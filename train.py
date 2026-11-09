"""Train the Returns Policy Assistant: LoRA fine-tune Qwen3-8B
on Tinker with the locked config (lora_config.yaml).

Before running:
  pip install tinker tinker-cookbook
  export TINKER_API_KEY="..."        # your key, in this terminal session
  Put these files in the same folder as this script:
    train_sft.jsonl          (68 training examples)
    train_sft_dryrun.jsonl   (8-example slice, for --dry-run)
    validation_sft.jsonl     (16 validation examples, loss only)

Run the dry run first:
  python3 train.py --dry-run
Then the full training:
  python3 train.py

What it does, in order:
  1. Loads the SFT files and turns each example into a training Datum
     (tokens + per-token weights; loss counts on the answer only).
  2. Creates a LoRA training client (base Qwen/Qwen3-8B, rank 16).
  3. For each epoch: shuffles, trains batch by batch (one
     forward_backward + one optim_step per batch), then measures the
     validation loss (forward only, no updates), then saves a
     checkpoint and sampler weights for that epoch.
  4. Writes training_log.jsonl — one line per epoch with the train
     loss, validation loss and checkpoint paths (evidence for the
     training record and the scorecard).

The dry run uses the 8-example slice for 3 steps (3 passes over the
slice as one batch of 8), then saves and samples the saved model once,
so all five dry-run checks can be seen in one short run.
"""
import argparse
import json
import random

import tinker
from tinker_cookbook import renderers
from tinker_cookbook.supervised.common import (
    compute_mean_nll,
    datum_from_model_input_weights,
)

# --- The locked config (lora_config.yaml) ---
BASE_MODEL = "Qwen/Qwen3-8B"
LORA_RANK = 16
LEARNING_RATE = 1e-4
EPOCHS = 3
BATCH_SIZE = 8
TRAIN_RATE_PER_M_TOKENS = 0.44  # USD, Tinker's published Qwen3-8B rate
COST_CAP_USD = 1.00

DRY_RUN_STEPS = 3  # passes over the 8-example slice (batch 8 = 1 step each)


def load_sft(path):
    return [json.loads(line) for line in open(path) if line.strip()]


def to_datums(rows, renderer):
    """Render each SFT row to a Datum. The renderer marks the prompt
    tokens with weight 0 and the assistant's answer tokens with
    weight 1, so the loss is counted on the answer only."""
    datums = []
    for row in rows:
        messages = [
            {"role": "system", "content": row["system"]},
            {"role": "user", "content": row["user"]},
            {"role": "assistant", "content": row["assistant"]},
        ]
        model_input, weights = renderer.build_supervised_example(messages)
        datums.append(datum_from_model_input_weights(model_input, weights))
    return datums


def batch_loss(result, datums):
    """Mean loss (negative log-likelihood) over the weighted tokens
    of one forward / forward_backward result."""
    logprobs = [x["logprobs"] for x in result.loss_fn_outputs]
    weights = [d.loss_fn_inputs["weights"] for d in datums]
    return compute_mean_nll(logprobs, weights)


def extract_text(message):
    """Same helper as run_baseline.py: the scoreable reply text out
    of a parsed response message."""
    content = message["content"] if isinstance(message, dict) else message
    if isinstance(content, list):
        return "\n".join(
            part.get("text", "")
            for part in content
            if isinstance(part, dict) and part.get("type") == "text"
        ).strip()
    text = str(content)
    if "</think>" in text:
        text = text.split("</think>", 1)[1]
    return text.strip()


def train_one_batch(training_client, batch, adam_params):
    result = training_client.forward_backward(batch, "cross_entropy").result()
    loss = batch_loss(result, batch)
    training_client.optim_step(adam_params).result()
    return loss


def mean_loss(training_client, datums):
    """Forward only — no gradients, no updates. Used for validation."""
    losses, token_counts = [], []
    for i in range(0, len(datums), BATCH_SIZE):
        batch = datums[i : i + BATCH_SIZE]
        result = training_client.forward(batch, "cross_entropy").result()
        losses.append(batch_loss(result, batch))
        token_counts.append(sum(sum(d.loss_fn_inputs["weights"].data) for d in batch))
    total = sum(token_counts)
    return sum(l * n for l, n in zip(losses, token_counts)) / total


def sample_check(training_client, renderer, row, name):
    """Save sampler weights and ask the saved model one question.
    Dry-run check 5: it must answer in normal English."""
    sampling_client = training_client.save_weights_and_get_sampling_client(name=name)
    messages = [
        {"role": "system", "content": row["system"]},
        {"role": "user", "content": row["user"]},
    ]
    prompt = renderer.build_generation_prompt(messages)
    params = tinker.SamplingParams(
        max_tokens=300, temperature=0.0, stop=renderer.get_stop_sequences()
    )
    result = sampling_client.sample(
        prompt=prompt, num_samples=1, sampling_params=params
    ).result()
    message, _ok = renderer.parse_response(result.sequences[0].tokens)
    print("--- sample from the saved model ---")
    print(extract_text(message))
    print("-----------------------------------")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    service_client = tinker.ServiceClient()
    # Note: Tinker's create call takes the rank only — there is no
    # alpha argument; the adapter scale is managed inside Tinker.
    # (Our config records alpha 32 as the design convention.)
    training_client = service_client.create_lora_training_client(
        base_model=BASE_MODEL, rank=LORA_RANK
    )
    tokenizer = training_client.get_tokenizer()
    renderer = renderers.get_renderer("qwen3", tokenizer)
    adam_params = tinker.AdamParams(
        learning_rate=LEARNING_RATE, beta1=0.9, beta2=0.95, eps=1e-8
    )

    if args.dry_run:
        rows = load_sft("train_sft_dryrun.jsonl")
        datums = to_datums(rows, renderer)
        print(f"dry run: {len(datums)} examples loaded, batch {BATCH_SIZE}")
        for step in range(1, DRY_RUN_STEPS + 1):
            loss = train_one_batch(training_client, datums, adam_params)
            print(f"step {step}: loss {loss:.4f}")
        saved = training_client.save_state("dry-run").result()
        print("checkpoint saved:", saved.path)
        sample_check(training_client, renderer, rows[0], "dry-run-sampler")
        print("dry run complete — check the five items in the plan")
        return

    train_rows = load_sft("train_sft.jsonl")
    val_rows = load_sft("validation_sft.jsonl")
    train_datums = to_datums(train_rows, renderer)
    val_datums = to_datums(val_rows, renderer)

    n_tokens = sum(d.model_input.length for d in train_datums)
    estimate = n_tokens * EPOCHS * TRAIN_RATE_PER_M_TOKENS / 1_000_000
    print(f"train tokens per epoch: {n_tokens}; estimated cost ${estimate:.3f}")
    assert estimate < COST_CAP_USD, "estimate exceeds the $1.00 cap — stop"

    with open("training_log.jsonl", "w") as log:
        for epoch in range(1, EPOCHS + 1):
            shuffled = train_datums[:]
            random.Random(1234 + epoch).shuffle(shuffled)
            step_losses = []
            for i in range(0, len(shuffled), BATCH_SIZE):
                batch = shuffled[i : i + BATCH_SIZE]
                loss = train_one_batch(training_client, batch, adam_params)
                step_losses.append(loss)
                print(f"epoch {epoch} step {i // BATCH_SIZE + 1}: loss {loss:.4f}")
            train_loss = sum(step_losses) / len(step_losses)
            val_loss = mean_loss(training_client, val_datums)
            state = training_client.save_state(f"epoch-{epoch}").result()
            sampler = training_client.save_weights_for_sampler(
                name=f"epoch-{epoch}-sampler"
            ).result()
            record = {
                "epoch": epoch,
                "train_loss": round(train_loss, 4),
                "val_loss": round(val_loss, 4),
                "checkpoint_path": state.path,
                "sampler_path": sampler.path,
            }
            log.write(json.dumps(record) + "\n")
            log.flush()
            print(
                f"epoch {epoch} done: train loss {train_loss:.4f}, "
                f"val loss {val_loss:.4f}"
            )
    print("training complete — see training_log.jsonl")


if __name__ == "__main__":
    main()
