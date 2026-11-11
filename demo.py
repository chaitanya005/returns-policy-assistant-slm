"""Live demo: one return case, two models, side by side.

Shows the same return request to:
  1. the base model (Qwen3-8B, the shared best prompt, no training), and
  2. the fine-tuned model (LoRA, epoch-3 sampler weights),
then prints the correct decision from the test set, so the audience
can see what fine-tuning changed.

Both models get the exact prompts and settings used in the real
scoring runs (temperature 0, max 800 tokens) — nothing is reheated
for the demo.

Before running:
  pip install tinker tinker-cookbook
  export TINKER_API_KEY="..."        # your key, in this terminal session
  The test files live in the data/ folder — nothing to move.

Run:
  python3 demo.py            # menu: Enter = the 3 showcase cases,
                             # or type a test id (e.g. ex-014)
  python3 demo.py ex-014     # one case, straight away
  python3 demo.py --auto     # the 3 showcase cases with timed pauses
                             # (use this for a screen recording)

Cost: each case samples both models once — a fraction of a cent.

Presenter notes:
  The showcase three are cases the fine-tuned model gets right and
  the base model struggled with in the scored runs — it never
  answered any of them there. Live runs can differ: on 2026-11-09
  the base model answered ex-014 with a decision only, no draft.
  ex-084 is not in the showcase: both models get it right, so it is
  not a contrast (you can still run it by typing its id). The
  fine-tuned model's known misses (ex-056, ex-071, ex-076, ex-100 —
  the boundary lines) are NOT in the showcase set. Show one of them
  only if you want to present the failure analysis — it is a
  strength in an interview, a surprise in a sales demo.
"""
import json
import sys
import time
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"

import tinker
from tinker_cookbook import renderers

BASE_MODEL = "Qwen/Qwen3-8B"

# Epoch-3 sampler weights from the training run (see results/training_log.jsonl).
MODEL_PATH = (
    "tinker://db1fcb0d-2128-5761-98ce-5b5946f3996e"
    ":train:0/sampler_weights/epoch-3-sampler"
)

# The showcase set: (test id, one plain line for the presenter)
SHOWCASE = [
    ("ex-014", "£149 jacket, day 29 — just under the £150 line: refund"),
    ("ex-037", "Shop sent the wrong colour — the guarantee beats £150: exchange"),
    ("ex-044", "Rare-material blouse, refund asked — exchange only"),
]

CONDITION_WORDS = [
    ("used", "has been used"),
    ("has_stains", "has stains"),
    ("has_tears", "has tears"),
    ("was_washed", "has been washed"),
    ("has_original_tag", "missing the price tag"),
    ("has_original_box", "missing the box"),
]


def extract_text(message):
    """Same helper as run_baseline.py / run_finetuned.py: the
    scoreable reply text out of a parsed response message."""
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


def raw_text(message):
    """Everything the model produced, thinking included — used only
    to show a glimpse of a runaway thinking block when the base
    model never reaches an answer."""
    content = message["content"] if isinstance(message, dict) else message
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, dict):
                parts.append(part.get("text") or part.get("thinking") or "")
        return "\n".join(parts).strip()
    return str(content).strip()


def decision_of(text):
    """The label on the 'Decision:' line, or None if there is none."""
    for line in text.splitlines():
        if line.strip().lower().startswith("decision:"):
            return line.split(":", 1)[1].strip()
    return None


def case_summary(inp):
    """The case in plain words, for the screen (and the audience)."""
    lines = [
        f"Item: {inp['item']} — £{inp['order_value_gbp']}",
        f"Delivered {inp['days_since_delivery']} days ago",
        f"Customer asks for: {inp['customer_request']} (reason: {inp['reason']})",
    ]
    problems = [
        words for key, words in CONDITION_WORDS
        if (key.startswith("has_original") and not inp[key])
        or (not key.startswith("has_original") and inp[key])
    ]
    if problems:
        lines.append("Condition problems: " + ", ".join(problems))
    else:
        lines.append("Condition: all checks pass")
    if inp["customer_history"] != "good":
        lines.append(f"Customer history: {inp['customer_history']}")
    if inp["product_flag"] != "standard":
        lines.append(f"Product flag: {inp['product_flag']}")
    lines.append(f"Customer message: \"{inp['customer_message']}\"")
    return lines


def sample_once(sampling_client, renderer, prompt_record):
    """One sample with the scoring runs' settings. Returns
    (answer_text, raw_text)."""
    messages = [
        {"role": "system", "content": prompt_record["system"]},
        {"role": "user", "content": prompt_record["user"]},
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
    return extract_text(message), raw_text(message)


def pause(auto, text):
    if auto:
        print(f"\n(... {text} ...)")
        time.sleep(3)
    else:
        input(f"\nPress Enter {text}...")


def run_case(case_id, gold, prompts, base_client, ft_client, renderer, auto):
    record = gold[case_id]
    print("\n" + "=" * 64)
    print(f"CASE {case_id}")
    for line in case_summary(record["input"]):
        print("  " + line)

    pause(auto, "to show the base model")
    print("\n--- BASE MODEL (Qwen3-8B, prompt only) ---")
    answer, raw = sample_once(base_client, renderer, prompts[case_id])
    base_decision = decision_of(answer)
    if base_decision is None:
        print("No decision. The model kept thinking until the token")
        print("limit and never answered. A glimpse of the thinking:")
        print("  " + raw[:240].replace("\n", " ") + " ...")
    else:
        print(answer)

    pause(auto, "to show the fine-tuned model")
    print("\n--- FINE-TUNED MODEL (LoRA on Qwen3-8B) ---")
    answer, _raw = sample_once(ft_client, renderer, prompts[case_id])
    ft_decision = decision_of(answer)
    print(answer if answer else "(no answer)")

    gold_decision = record["decision"]
    print("\n--- RESULT ---")
    print(f"Correct decision: {gold_decision}")
    print("Base model:       "
          + ("no answer" if base_decision is None
             else f"{base_decision} " + ("✓" if base_decision == gold_decision else "✗")))
    print("Fine-tuned model: "
          + ("no answer" if ft_decision is None
             else f"{ft_decision} " + ("✓" if ft_decision == gold_decision else "✗")))


def main():
    args = [a for a in sys.argv[1:] if a != "--auto"]
    auto = "--auto" in sys.argv

    gold = {}
    for line in open(DATA / "test.jsonl"):
        d = json.loads(line)
        gold[d["id"]] = d
    prompts = {}
    for line in open(DATA / "test_prompts.jsonl"):
        d = json.loads(line)
        prompts[d["id"]] = d

    if args:
        case_ids = args
    elif auto:
        case_ids = [cid for cid, _note in SHOWCASE]
    else:
        print("Showcase cases:")
        for cid, note in SHOWCASE:
            print(f"  {cid} — {note}")
        choice = input(
            "\nPress Enter for all three, or type one test id: "
        ).strip()
        case_ids = [choice] if choice else [cid for cid, _note in SHOWCASE]

    for cid in case_ids:
        if cid not in gold:
            print(f"{cid} is not in the test set — skipped.")
            return

    service_client = tinker.ServiceClient()
    base_client = service_client.create_sampling_client(base_model=BASE_MODEL)
    ft_client = service_client.create_sampling_client(model_path=MODEL_PATH)
    renderer = renderers.get_renderer("qwen3", ft_client.get_tokenizer())

    for cid in case_ids:
        run_case(cid, gold, prompts, base_client, ft_client, renderer, auto)

    print("\n" + "=" * 64)
    print("Full test scores (16 cases): base 9/16 — fine-tuned 12/16 —")
    print("frontier model 15/16. Full detail in scorecard.md.")


if __name__ == "__main__":
    main()
