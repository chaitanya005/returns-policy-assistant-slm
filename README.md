# Returns Policy Assistant

Antern Cohort 3 — Part C (the SLM project). A small language model,
fine-tuned with LoRA on Tinker, that applies one clothing shop's
returns policy.

**The behavior, in one sentence:** given an order and a return request
at a clothing shop, the model decides what the shop's returns policy
allows — `approve-refund`, `approve-exchange`, `deny-out-of-policy`,
or `escalate-to-human` — and drafts the reply to the customer.

A prompt alone is not enough for this: the policy is specific to one
shop (exact £50 / £150 cut-offs, a fixed order of exceptions), a
prompted model bends rules it should apply exactly, and a wrong
approve or deny costs the shop money or trust. The full argument is in
`behavior.md`.

## Status

| Step | State |
|---|---|
| [C.3] Behavior definition | Done — `behavior.md` |
| Policy (v5) | Done — `policy-reference.md` |
| [C.5] Review SOP | Done — `review-sop.md` |
| [C.4]/[C.6] Dataset: 100 reviewed examples | Done — `dataset.jsonl`, splits below |
| [C.7] Baselines | Base Qwen3-8B scored (see Results); frontier run in progress |
| [C.8] LoRA config | Done — `lora_config.yaml` |
| [C.9] Training on Tinker | Dry run next |
| [C.10] Scorecard | After training |
| [C.11] This repo | In progress |

## Files

- `policy-reference.md` — the shop's returns policy (v5), the decision
  ladder every label comes from.
- `behavior.md` — [C.3]: the behavior, why a prompt is not enough,
  input/output definitions.
- `review-sop.md` — [C.5]: the review SOP used to label the dataset.
- `dataset.jsonl` — the full 100-example dataset (25 per decision),
  each example reviewed and kept.
- `train.jsonl` / `validation.jsonl` / `test.jsonl` — the split
  (68 / 16 / 16). The test set is used only for scoring.
- `validate_dataset.py` — re-derives every label from the policy and
  checks the dataset (contradictions, balance, draft leaks).
- `split_dataset.py` — the explicit, auditable split selection.
- `baseline-plan.md` — [C.7]: success criteria (written before any
  scores), the shared best prompt, the draft rubric, the run protocol.
- `baseline-scores.md` — baseline results so far.
- `baseline_prompt.txt` / `test_prompts.jsonl` — the shared prompt and
  the 16 prepared test prompts.
- `score_baseline.py` — decision scoring (exact match) + rubric
  worksheet generator.
- `run_baseline.py` — samples the base Qwen3-8B on the test prompts
  via Tinker.
- `run_frontier_gemini.py` — the frontier baseline (Gemini via Google
  AI Studio's free tier, same prompt and scoring).
- `lora_config.yaml` — [C.8]: the LoRA config, every value justified.
- `prepare_training_data.py` — builds the SFT files from the splits.
- `train_sft.jsonl` / `train_sft_dryrun.jsonl` / `validation_sft.jsonl`
  — the training data (prompt + gold Decision/Draft per example).
- `train.py` — [C.9]: the training script (`--dry-run` first).

## How to run

```
pip install tinker tinker-cookbook
export TINKER_API_KEY="..."   # never committed; see .env.example

python3 run_baseline.py       # base-model baseline [C.7]
python3 train.py --dry-run    # dry run: 8 examples, 3 steps [C.8]
python3 train.py              # full training: 68 examples, 3 epochs [C.9]
```

## Results

Base model (Qwen3-8B, best prompt, test set of 16): **9/16 decisions**
exact match; draft rubric mean **2.25/5**; 3 drafts leaked internal
policy rules. Per-decision detail in `baseline-scores.md`.

Frontier baseline and fine-tuned results: to be added in the [C.10]
scorecard.
