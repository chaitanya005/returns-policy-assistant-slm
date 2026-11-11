# Baseline scores

Status: base-Qwen baseline COMPLETE and reviewer-approved, 2026-10-30.
Frontier baseline: COMPLETE 2026-11-06 — 15/16 decisions on
gemini-3.5-flash-lite, after the original choice (gemini-3.8-flash)
was abandoned for documented unavailability; frontier draft scores
frontier drafts scored 74/80 (mean 4.63/5, 2 leaks). See the frontier section below. Fine-tuned model: scored
with the identical method; all three meet in the final
scorecard.

Method: the plan in `baseline-plan.md` — the shared best prompt,
the 16-example test set, temperature 0, one run per model, decisions by
exact match on the `Decision:` line, drafts by the fixed 5-point rubric.
Raw outputs preserved outside this repo (base_qwen_results.raw.jsonl);
normalized answer text: results/base_qwen_results.jsonl.

## Base model: Qwen/Qwen3-8B (prompt only, no training)

### Decisions — 9/16 exact match

| Decision type      | Correct |
| ------------------ | ------- |
| approve-refund     | 3/4     |
| approve-exchange   | 1/4     |
| deny-out-of-policy | 3/4     |
| escalate-to-human  | 2/4     |

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

| Example | Points    | Total | Leak                                       |
| ------- | --------- | ----- | ------------------------------------------ |
| ex-002  | 1/0/0/1/1 | 3     | Y — discloses the under-£50 box rule       |
| ex-014  | no output | 0     | n/a                                        |
| ex-017  | 1/0/0/1/1 | 3     | N                                          |
| ex-020  | 1/1/1/1/1 | 5     | N                                          |
| ex-026  | 0/0/0/0/1 | 1     | N                                          |
| ex-037  | no output | 0     | n/a                                        |
| ex-044  | no output | 0     | n/a                                        |
| ex-048  | 1/0/1/1/1 | 4     | N                                          |
| ex-056  | 1/1/0/1/1 | 4     | Y — "within 30 days … for orders over £50" |
| ex-061  | 1/0/0/1/1 | 3     | N                                          |
| ex-071  | no output | 0     | n/a                                        |
| ex-074  | 1/0/0/1/1 | 3     | Y — "under £50 … within 60 days"           |
| ex-076  | no output | 0     | n/a                                        |
| ex-084  | 1/1/1/1/1 | 5     | N                                          |
| ex-090  | 1/1/1/1/1 | 5     | N                                          |
| ex-100  | no output | 0     | n/a                                        |

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

## Frontier model: Gemini via Google AI Studio (free tier)

Model change, recorded openly (decided 2026-11-06): the original
frontier choice was **gemini-3.8-flash**. Its free tier allows only
20 requests/day, and its API capacity was unavailable across
2026-11-03–05 — three straight days of HTTP 503 failures from the
first attempt, after a 429-dominated week (peak daily usage 24 against
the 20 cap). The run stopped at 9/16 saved answers. Those 9 were never
a baseline of record — on a preliminary decision check all 9 were
correct — and the partial set is preserved unmixed
(`frontier_gemini_results.jsonl`) as the record of the attempt.

The frontier baseline is therefore completed on **gemini-3.5-flash-lite**
(free tier: 500 requests/day) instead: one clean run of all 16 test
prompts, same shared prompt, temperature 0.0,
`reasoning_effort="low"`, identical scoring. Results file:
`frontier_gemini_35flashlite_results.jsonl`. The reason for the change
is availability, recorded here in advance of the score; it is noted
that a lighter frontier model may score lower than 3.8 Flash would
have, which affects S3 (fine-tuned 12/16; S3 passes if the frontier
finishes ≤13/16).

### Frontier decisions — 15/16 exact match (run completed 2026-11-06)

| Decision type      | Correct |
| ------------------ | ------- |
| approve-refund     | 4/4     |
| approve-exchange   | 3/4     |
| deny-out-of-policy | 4/4     |
| escalate-to-human  | 4/4     |

The only miss: ex-048 — a Step 0 premium fast-lane case (£150+,
colour/size, within 3 days, all conditions pass) that the model
escalated on the £150 trigger instead of approving the exchange; its
draft also states the £150 threshold to the customer (the reviewer's
leak ruling sits with the draft scores). Notably, the frontier model
answered correctly on all four cases the fine-tuned model missed
(ex-056, ex-071, ex-076, ex-100).

Draft scores (reviewer's rubric pass, completed 2026-11-06):
**74/80 — mean 4.63/5 — 2 leaks** (ex-017: the draft explains the
£50 band and the 60-day window; ex-048: the draft states the £150
threshold). Two calibration fixes were applied under the locked
conventions (ex-017 and ex-037 process points restored; as first
scored the total was 72/80).
This settles S3: fine-tuned 12/16 finishes 3 behind the frontier's
15/16, so **S3 FAILS** (bar: no more than 1 behind).
