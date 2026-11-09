"""Score the fine-tuned model: sample the epoch-3 sampler
weights on the same 16 test prompts, with the same settings as the
base-model baseline, and save the raw replies for scoring.

The model is chosen by the training log: validation loss fell
at every epoch (0.7235 -> 0.3025 -> 0.1354) and never turned up, so
the epoch-3 weights are the final model — no fallback to epoch 2.

Before running:
  pip install tinker tinker-cookbook
  export TINKER_API_KEY="..."        # your key, in this terminal session
  Put test_prompts.jsonl in the same folder as this script.

Run:
  python3 run_finetuned.py

Output: finetuned_results.jsonl — one {"id", "output"} line per test
example, the format the scoring harness expects. Scoring happens
afterwards, separately, by the same method as the baselines.
"""
import json

import tinker
from tinker_cookbook import renderers

# Epoch-3 sampler weights from the training run (see training_log.jsonl).
MODEL_PATH = (
    "tinker://db1fcb0d-2128-5761-98ce-5b5946f3996e"
    ":train:0/sampler_weights/epoch-3-sampler"
)


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


def main():
    service_client = tinker.ServiceClient()
    sampling_client = service_client.create_sampling_client(model_path=MODEL_PATH)
    tokenizer = sampling_client.get_tokenizer()
    renderer = renderers.get_renderer("qwen3", tokenizer)

    prompts = [json.loads(line) for line in open("test_prompts.jsonl")]
    with open("finetuned_results.jsonl", "w") as out:
        for p in prompts:
            messages = [
                {"role": "system", "content": p["system"]},
                {"role": "user", "content": p["user"]},
            ]
            prompt = renderer.build_generation_prompt(messages)
            params = tinker.SamplingParams(
                max_tokens=800,
                temperature=0.0,
                stop=renderer.get_stop_sequences(),
            )
            result = sampling_client.sample(
                prompt=prompt, num_samples=1, sampling_params=params
            ).result()
            message, _ok = renderer.parse_response(result.sequences[0].tokens)
            text = extract_text(message)
            out.write(json.dumps({"id": p["id"], "output": text}) + "\n")
            print(p["id"], "done")
    print("wrote finetuned_results.jsonl")


if __name__ == "__main__":
    main()
