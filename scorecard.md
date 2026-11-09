# Scorecard [C.10] — Returns Policy Assistant

**Status: FINAL — all three models scored, all criteria verdicts settled.**

Three models, one test set (16 examples, 4 per decision), one shared prompt,
one scoring method. Decisions are scored by exact match against the gold
label. Drafts are scored by the reviewer on the fixed 5-point rubric from the
baseline plan (1 point each: outcome matches the gold decision; correct next
step and process facts; public policy language only, no internal leak; no
invented facts; tone and form). Success criteria S1–S5 were written and
locked on 2026-10-30, before any model was scored, and have not been edited
since.

## Decision accuracy (exact match, out of 16)

| Model                            | Total     | approve-refund | approve-exchange | deny-out-of-policy | escalate-to-human |
| -------------------------------- | --------- | -------------- | ---------------- | ------------------ | ----------------- |
| Base Qwen3-8B (best prompt)      | 9/16      | 3/4            | 1/4              | 3/4                | 2/4               |
| Frontier — Gemini 3.5 Flash-Lite | **15/16** | 4/4            | 3/4              | 4/4                | 4/4               |
| Fine-tuned Qwen3-8B (LoRA)       | **12/16** | 4/4            | 4/4              | 2/4                | 2/4               |

Frontier note: the original frontier choice, gemini-3.8-flash, was
abandoned at 9/16 saved answers after its free-tier capacity proved
unavailable across 2026-11-03–05 (20 requests/day cap; documented
429/503 pattern). Those 9 answers were never a baseline of record (a
preliminary check found all 9 decisions correct) and are preserved
unmixed. The frontier baseline was completed on gemini-3.5-flash-lite
(500 requests/day on the free tier) with the same prompt and scoring —
see the protocol notes.

The comparison is sharp: the frontier model answered correctly on all
four cases the fine-tuned model missed (ex-056, ex-071, ex-076,
ex-100 — the strict-band edges and the £150 line). Its single miss was
ex-048, the Step 0 premium fast lane, which it escalated on the £150
trigger instead — a case both Qwen models answered correctly. A
prompted frontier model still reasons through the policy's boundary
lines more reliably than the fine-tuned model; what fine-tuning bought
was format discipline and draft quality on a 68-example dataset, not
frontier-level boundary reasoning.

## Draft quality (reviewer rubric, mean out of 5)

| Model                            | Mean         | Total   | Drafts with an internal leak                                                              |
| -------------------------------- | ------------ | ------- | ----------------------------------------------------------------------------------------- |
| Base Qwen3-8B                    | 2.25 / 5     | 36 / 80 | 3 (ex-002, ex-056, ex-074 — price bands disclosed)                                        |
| Frontier — Gemini 3.5 Flash-Lite | **4.63 / 5** | 74 / 80 | 2 (ex-017 — the £50 band and 60-day window explained; ex-048 — the £150 threshold stated) |
| Fine-tuned Qwen3-8B (LoRA)       | **3.75 / 5** | 60 / 80 | 1 (ex-017 — "60-day return period" disclosed)                                             |

## Success criteria — verdicts

| Criterion | Bar (locked 2026-10-30)                      | Result                       | Verdict              |
| --------- | -------------------------------------------- | ---------------------------- | -------------------- |
| S1        | Fine-tuned decisions ≥ 14/16                 | 12/16                        | FAIL                 |
| S2        | Fine-tuned ≥ 4 more than base (≥ 13/16)      | 12 vs base 9 (+3)            | FAIL — by one        |
| S3        | Fine-tuned no more than 1 behind frontier    | 12 vs frontier 15 (3 behind) | FAIL                 |
| S4        | ≥ 1 correct in every type AND escalate ≥ 3/4 | every type ≥ 1; escalate 2/4 | FAIL                 |
| S5        | Draft mean ≥ 4.0/5 AND zero leaks            | 3.75/5; 1 leak               | FAIL — on both parts |

## Failure examples — what went wrong, and why

Fine-tuned model, wrong decisions:

1. **ex-056** (£85 jacket, day 45). Gold: deny — strict band, the 30-day
   window has passed. Model: approve-refund, and the draft claims the return
   is "within our 30-day return period", which is false at day 45. The
   strict-band window edge was not learned.
2. **ex-071** (£51 item, day 20, no original box). Gold: deny — above £50
   the box is required. Model: approve-refund; the draft says "You don't
   need the original box". The flexible-band rule was applied £1 over the
   line — the £50 boundary was not learned as a hard line.
3. **ex-076** (£175, day 10, all conditions pass). Gold: escalate — orders
   of £150+ go to a human. Model: deny, citing the return period — at day
   10, inside every window. A memorised deny template fired where the
   escalate trigger should have.
4. **ex-100** (exactly £150, day 18, all conditions pass). Gold: escalate —
   the £150 line is inclusive. Model: deny, the same template as ex-076.
   Both high-value test cases were pulled toward deny instead of escalate.

Fine-tuned model, right decision, failed draft:

5. **ex-026** (jeans, exchange). Decision correct: approve-exchange. The
   draft then refuses the return, citing the missing box — it contradicts
   its own decision. The decision was learned; the draft fell back to a
   deny pattern.
6. **ex-061** (stained item, day 18). Decision correct: deny. The draft
   cites the return period — the wrong reason. Day 18 is inside the window;
   the refusal rests on the stains (original condition). Right answer,
   wrong justification.

Base model, the failure class fine-tuning removed:

7. **Six non-answers.** In 6 of 16 base outputs (ex-014, 037, 044, 071,
   076, 100) the model produced a runaway thinking block that hit the
   800-token cap and never emitted a Decision — scored 0 under the
   protocol. Of the 10 replies that finished, 9 decisions were correct:
   the base model's problem was answer discipline, not policy knowledge.
   The fine-tuned model answered all 16 in the exact format.
8. **Three leaking drafts** (ex-002, ex-056, ex-074) disclosed the internal
   price bands to the customer. Fine-tuning cut leaks from 3 to 1.

## What data to change next

The four wrong decisions all sit on two seams — the £150 escalate line and
the strict band's edges (£50/box, day-30 window). The next dataset iteration
should add matched boundary pairs, where a pair differs in exactly one
number so that number is the only signal:

- **£145–£160 escalate pairs:** the same order at £149 (approve) and £150 /
  £155 (escalate). Targets ex-076 and ex-100.
- **£50/£51 box pairs:** the same item and day at £50 with no box (approve —
  flexible) and £51 with no box (deny — strict). Targets ex-071.
- **Day-30/31 window pairs:** strict-band items at day 30 (approve) and day
  31+ (deny), with deny drafts that state the window truthfully. Targets
  ex-056.
- **More escalate variety overall:** escalate is the weakest type for both
  Qwen models (2/4 and 2/4). Add examples across all six triggers — £150+,
  faulty, arrived damaged, disputed denial, declined exchange, asks for a
  human.
- **Deny-reason alignment pairs:** condition-failure denies inside the
  window whose drafts cite "original condition" (never the return period),
  beside window denies that cite the return period — so the reason and the
  wording stay welded together. Targets ex-061.
- **Exchange drafts that follow the decision:** more approve-exchange
  examples where a condition is relaxed under the flexible band, with
  drafts completing the full flow (pickup, selection step, replacement
  within 5 working days). Targets ex-026.

## Protocol notes

- Criteria, prompt, rubric and test set were all fixed before scoring;
  nothing was re-run and no checkpoint was chosen using test scores. The
  epoch-3 model is the final model because validation loss fell at every
  epoch (0.72 → 0.30 → 0.14), not because of its test result.
- All three models received the same system prompt and the same 16 test
  inputs, at temperature 0.
- Frontier run parameter on record: `reasoning_effort="low"` (caps the
  model's thinking time on the free tier; prompt and scoring unchanged).
- Frontier model change, recorded openly (decided 2026-11-06, before
  the replacement run was scored): original choice gemini-3.8-flash;
  free-tier capacity unavailable across 2026-11-03–05 (documented
  429/503 pattern, 20 requests/day cap); frontier baseline completed
  on gemini-3.5-flash-lite instead. The reason for the change is
  availability. It is noted that a lighter frontier model may score
  lower than 3.8 Flash would have, which affects S3.
