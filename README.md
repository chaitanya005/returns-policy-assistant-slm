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

| Step                                       | State                                                                                    |
| ------------------------------------------ | ---------------------------------------------------------------------------------------- |
| [C.3] Behavior definition                  | Done — `behavior.md`                                                                     |
| Policy (v5)                                | Done — `policy-reference.md`                                                             |
| [C.5] Review SOP                           | Done — `review-sop.md`                                                                   |
| [C.4]/[C.6] Dataset: 100 reviewed examples | Done — `dataset.jsonl`, splits below                                                     |
| [C.7] Baselines                            | Base Qwen3-8B scored (see Results); frontier run 9/16, completing under free-tier limits |
| [C.8] LoRA config                          | Done — `lora_config.yaml`                                                                |
| [C.9] Training on Tinker                   | Done — 3 epochs, validation loss 0.72 → 0.30 → 0.14 (`training_log.jsonl`)               |
| [C.10] Scorecard                           | Done except the frontier column — `scorecard.md`                                         |
| [C.11] This repo                           | In progress — diagrams in `diagrams.md`; final checks pending the frontier results       |

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
- `base_qwen_results.jsonl` — the base model's 16 raw replies from
  that run (the scored copy of record).
- `run_frontier_gemini.py` — the frontier baseline (Gemini via Google
  AI Studio's free tier, same prompt and scoring).
- `lora_config.yaml` — [C.8]: the LoRA config, every value justified.
- `prepare_training_data.py` — builds the SFT files from the splits.
- `train_sft.jsonl` / `train_sft_dryrun.jsonl` / `validation_sft.jsonl`
  — the training data (prompt + gold Decision/Draft per example).
- `train.py` — [C.9]: the training script (`--dry-run` first).
- `training_log.jsonl` — [C.9]: train and validation loss, one line
  per epoch.
- `run_finetuned.py` — samples the fine-tuned model (epoch-3 sampler
  weights) on the same 16 test prompts.
- `finetuned_results.jsonl` — the fine-tuned model's 16 raw replies.
- `scorecard.md` — [C.10]: the three-model scorecard — decision and
  draft scores, per-type detail, criteria verdicts, failure analysis,
  and what data to change next.
- `diagrams.md` — [C.11]: two Mermaid diagrams — one example through
  every file, and the training script step by step.

## How to run

```
pip install tinker tinker-cookbook
export TINKER_API_KEY="..."   # never committed; see .env.example

python3 run_baseline.py       # base-model baseline [C.7]
python3 train.py --dry-run    # dry run: 8 examples, 3 steps [C.8]
python3 train.py              # full training: 68 examples, 3 epochs [C.9]
```

## Results

All models: same 16 test prompts, same shared prompt, decisions by
exact match, drafts on the fixed 5-point rubric. Full detail, failure
analysis and criteria verdicts in `scorecard.md`.

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
  data-change plan in `scorecard.md`.
- **Frontier model** (Gemini, same prompt): run in progress under
  free-tier rate limits — 9 of 16 answers saved so far, all 9
  decisions correct. Final column lands in `scorecard.md` when the
  run completes.
