# Part C — Baseline scores [C.7]

Status: base-Qwen baseline COMPLETE and reviewer-approved, 2026-10-30.
Frontier baseline: pending. Fine-tuned model: scored later under [C.10]
with the identical method; all three meet in the final scorecard.

Method: the plan in `part-c-baseline-plan.md` — the shared best prompt,
the 16-example test set, temperature 0, one run per model, decisions by
exact match on the `Decision:` line, drafts by the fixed 5-point rubric.
Raw outputs preserved (project hidden_files: base_qwen_results.raw.jsonl;
normalized answer text: base_qwen_results.jsonl).

## Base model: Qwen/Qwen3-8B (prompt only, no training)

### Decisions — 9/16 exact match

| Decision type | Correct |
|---|---|
| approve-refund | 3/4 |
| approve-exchange | 1/4 |
| deny-out-of-policy | 3/4 |
| escalate-to-human | 2/4 |

Failure analysis:
- 6 of the 7 losses were non-answers: the model stayed in its thinking
  block, circled the policy ladder, and hit the 800-token cap without
  emitting a Decision (ex-014, ex-037, ex-044, ex-071, ex-076, ex-100).
  Scored 0 under the protocol (missing/invalid decision).
- 1 genuine wrong decision: ex-026 — a flexible-band exchange case the
  model denied outright for a missing box.
- Of the 10 replies that finished, 9 decisions were correct.

### Drafts — mean 2.25/5 (36/16), 3 leaking drafts

Rubric points in order: outcome / process / policy language /
no invention / tone. Reviewer: Chaitanya (calibration rulings agreed
2026-10-30, below).

| Example | Points | Total | Leak |
|---|---|---|---|
| ex-002 | 1/0/0/1/1 | 3 | Y — discloses the under-£50 box rule |
| ex-014 | no output | 0 | n/a |
| ex-017 | 1/0/0/1/1 | 3 | N |
| ex-020 | 1/1/1/1/1 | 5 | N |
| ex-026 | 0/0/0/0/1 | 1 | N |
| ex-037 | no output | 0 | n/a |
| ex-044 | no output | 0 | n/a |
| ex-048 | 1/0/1/1/1 | 4 | N |
| ex-056 | 1/1/0/1/1 | 4 | Y — "within 30 days … for orders over £50" |
| ex-061 | 1/0/0/1/1 | 3 | N |
| ex-071 | no output | 0 | n/a |
| ex-074 | 1/0/0/1/1 | 3 | Y — "under £50 … within 60 days" |
| ex-076 | no output | 0 | n/a |
| ex-084 | 1/1/1/1/1 | 5 | N |
| ex-090 | 1/1/1/1/1 | 5 | N |
| ex-100 | no output | 0 | n/a |

All three leaks are the same failure type: the model explaining the
price-band mechanism to the customer instead of giving the outcome in
public language.

### Scoring conventions (locked for all three models)

1. Rubric points are binary (0 or 1) — no half points.
2. Points are scored independently against their own definitions, even
   when the decision is wrong (the wrong decision is already scored by
   exact match and by the outcome point).
3. "Leak" means disclosing a real internal rule (price bands/thresholds,
   flagged history, decision labels). Misstating the public policy or
   inventing a restriction fails the policy-language point but is not
   flagged as a leak.
4. An exchange draft must include the selection step (size/colour) where
   relevant, or the process point is lost (applied to ex-048).
5. No output at all scores 0/5 with leak n/a.

### What this sets for the fine-tuned model (locked criteria)

- S1: ≥14/16 decisions. S2: ≥13/16 (base 9 + 4) — no S1/S2 collision.
- S5: draft mean ≥4.0/5 with zero leaks (baseline: 2.25/5, 3 leaks).
