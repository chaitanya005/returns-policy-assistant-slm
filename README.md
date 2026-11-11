# Returns Policy Assistant

A small language model,
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
`docs/behavior.md`.

## Status

| Step                           | State                                                                           |
| ------------------------------ | ------------------------------------------------------------------------------- |
| Behavior definition            | Done — `docs/behavior.md`                                                       |
| Policy (v5)                    | Done — `docs/policy-reference.md`                                               |
| Review SOP                     | Done — `docs/review-sop.md`                                                     |
| Dataset: 100 reviewed examples | Done — `data/dataset.jsonl`, splits below                                       |
| Baselines                      | Done — base and frontier both scored (see Results)                              |
| LoRA config                    | Done — `lora_config.yaml`                                                       |
| Training on Tinker             | Done — 3 epochs, validation loss 0.72 → 0.30 → 0.14 (`results/training_log.jsonl`) |
| Scorecard                      | Done — `docs/scorecard.md`                                                      |
| This repo                      | Done — diagrams in `docs/diagrams.md`                                           |

## Files

### `docs/` — the written record

- `docs/policy-reference.md` — the shop's returns policy (v5), the
  decision ladder every label comes from.
- `docs/behavior.md` — the behavior, why a prompt is not enough,
  input/output definitions.
- `docs/review-sop.md` — the review SOP used to label the dataset.
- `docs/baseline-plan.md` — success criteria (written before any
  scores), the shared best prompt, the draft rubric, the run protocol.
- `docs/baseline-scores.md` — baseline results so far.
- `docs/scorecard.md` — the three-model scorecard — decision and
  draft scores, per-type detail, criteria verdicts, failure analysis,
  and what data to change next.
- `docs/diagrams.md` — two Mermaid diagrams — one example through
  every file, and the training script step by step.

### `data/` — dataset, splits and training files

- `data/dataset.jsonl` — the full 100-example dataset (25 per
  decision), each example reviewed and kept.
- `data/train.jsonl` / `data/validation.jsonl` / `data/test.jsonl` —
  the split (68 / 16 / 16). The test set is used only for scoring.
- `data/baseline_prompt.txt` / `data/test_prompts.jsonl` — the shared
  prompt and the 16 prepared test prompts.
- `data/train_sft.jsonl` / `data/train_sft_dryrun.jsonl` /
  `data/validation_sft.jsonl` — the training data (prompt + gold
  Decision/Draft per example).

### `results/` — raw model outputs and the training log

- `results/base_qwen_results.jsonl` — the base model's 16 raw replies
  (the scored copy of record).
- `results/frontier_gemini_35flashlite_results.jsonl` — the frontier
  model's 16 raw replies (the baseline of record).
- `results/finetuned_results.jsonl` — the fine-tuned model's 16 raw
  replies.
- `results/training_log.jsonl` — train and validation loss, one line
  per epoch.

### `scripts/` — the code

- `scripts/validate_dataset.py` — re-derives every label from the
  policy and checks the dataset (contradictions, balance, draft
  leaks).
- `scripts/split_dataset.py` — the explicit, auditable split
  selection.
- `scripts/score_baseline.py` — decision scoring (exact match) +
  rubric worksheet generator.
- `scripts/run_baseline.py` — samples the base Qwen3-8B on the test
  prompts via Tinker.
- `scripts/run_frontier_gemini.py` — the frontier runner as first
  built for gemini-3.8-flash (abandoned at 9/16 — free-tier
  unavailability, recorded in `docs/baseline-scores.md`).
- `scripts/run_frontier_gemini_35flashlite.py` — the frontier runner
  as run: gemini-3.5-flash-lite, clean full-16 run, new results file.
- `scripts/prepare_training_data.py` — builds the SFT files from the
  splits.
- `scripts/train.py` — the training script (`--dry-run` first).
- `scripts/run_finetuned.py` — samples the fine-tuned model (epoch-3
  sampler weights) on the same 16 test prompts.
- `scripts/smoke.py` — a 10-line Tinker connection check.

### Repo root

- `demo.py` — the live demo (see Demo below).
- `lora_config.yaml` — the LoRA config, every value justified.

## How to run

```
pip install tinker tinker-cookbook
export TINKER_API_KEY="..."   # never committed; see .env.example

python3 scripts/run_baseline.py   # base-model baseline
python3 scripts/train.py --dry-run    # dry run: 8 examples, 3 steps
python3 scripts/train.py              # full training: 68 examples, 3 epochs
```

## Demo

`demo.py` (in the repo root) runs one return case through both
models, live, side by side. The base model and the fine-tuned model
get the exact prompts and settings used in the scoring runs
(temperature 0, max 800 tokens). It then prints the correct decision
from the test set, so you can see what fine-tuning changed.

```
python3 demo.py            # menu: Enter runs the 3 showcase cases,
                           # or type any test id (e.g. ex-014)
python3 demo.py ex-014     # one case, straight away
python3 demo.py --auto     # the 3 showcase cases with timed pauses
                           # (for a screen recording)
```

It needs a Tinker API key (see `.env.example`). Each case samples
both models once — a fraction of a cent.

The showcase three (ex-014, ex-037, ex-044) are cases the fine-tuned
model gets right and the base model never answered in the scored
runs. Live runs can differ — sampling varies — so treat the demo as
a live illustration, not a replay of the scored runs. The fine-tuned
model's four known misses (ex-056, ex-071, ex-076, ex-100) can also
be run by typing their ids.

## Results

All models: same 16 test prompts, same shared prompt, decisions by
exact match, drafts on the fixed 5-point rubric. Full detail, failure
analysis and criteria verdicts in `docs/scorecard.md`.

- **Base model** (Qwen3-8B, best prompt): **9/16 decisions**; draft
  rubric mean **2.25/5**; 3 drafts leaked internal policy rules. Six
  of its 16 replies never finished (runaway thinking) — of the 10 that
  finished, 9 decisions were correct.
- **Fine-tuned model** (LoRA on Qwen3-8B, 68 training examples, 3
  epochs): **12/16 decisions** (approve-refund 4/4, approve-exchange
  4/4, deny 2/4, escalate 2/4); draft rubric mean **3.75/5**; 1 leak.
  All 16 replies in the exact format. The four wrong decisions all sit
  on policy boundary lines (the £150 escalate line; the strict band's
  £50/box and day-30 edges) — see the failure analysis and the
  data-change plan in `docs/scorecard.md`.
- **Frontier model** (Gemini 3.5 Flash-Lite, same prompt):
  **15/16 decisions** (approve-refund 4/4, approve-exchange 3/4,
  deny 4/4, escalate 4/4). The original frontier choice,
  gemini-3.8-flash, was abandoned at 9/16 after its free tier
  (20 requests/day) proved unavailable across three days; the swap
  and its reason are recorded in `docs/scorecard.md` and
  `docs/baseline-scores.md`. Draft rubric mean **4.63/5**; 2 drafts leaked
  internal rules (both by explaining the mechanism — the £50 band /
  60-day window, and the £150 threshold).
