# Baseline plan and success criteria [C.7]

Status: APPROVED — criteria LOCKED by Chaitanya on 2026-10-30, before any
model has been scored. The success criteria in §2 are not changed after
scores are seen.

## 1. What is being scored

- The 16-example test set (`test.jsonl`), used for scoring only — never
  for training, prompt tuning, or example selection.
- Two baselines, both given the identical best prompt (§3):
  1. the base Qwen model (the same base chosen for fine-tuning in [C.8]),
  2. one frontier model (Claude or GPT — recorded when run).
- The fine-tuned model is scored later [C.10] with the same test set and
  the same method, and judged against §2.
- Decisions are scored by exact match against the dataset label.
  Drafts are scored with the fixed rubric in §4.

## 2. Success criteria for the fine-tuned model (locked on approval)

- **S1 (primary):** decision exact-match accuracy on the test set of at
  least 14/16 (87.5%).
- **S2 (training must matter):** at least 4 more test decisions correct
  than the base Qwen baseline (i.e. +25 points or more over base).
- **S3 (frontier comparison):** no more than 1 test decision behind the
  frontier baseline; matching or beating it is the stretch goal.
- **S4 (no collapsed category):** at least 1 correct in every decision
  type, and at least 3/4 on escalate-to-human (a missed escalation is
  the most expensive error in this policy).
- **S5 (draft quality):** mean draft rubric score of at least 4.0 / 5
  across the test set, and zero drafts containing an internal-rule leak
  (a leak is an automatic fail for that draft regardless of other marks).

The baselines themselves have no pass/fail — they set the bar that
S1–S5 are measured against.

## 3. The best prompt (identical for both baselines)

Used as the system prompt; the user message is the example's `input`
object as JSON, exactly as it appears in the dataset.

```
You are a returns policy assistant for a clothing shop. Given an order
and a return request, decide what the shop's policy allows and draft
the reply to the customer.

DECISIONS — choose exactly one:
- approve-refund
- approve-exchange
- deny-out-of-policy
- escalate-to-human

Apply the rules in this order; the first rule that matches decides:

1. Shop-error guarantee: if the shop sent the wrong size or colour, the
   customer contacted the shop within 7 days of delivery, and every
   condition in rule 6 passes, approve an exchange for the item the
   customer actually ordered — even if the order is £150 or more.
2. Premium fast lane: if the product is rare-material or the order is
   £150 or more, the reason is a wrong size or wrong colour, the
   customer contacted the shop within 3 days, and every condition in
   rule 6 passes, approve-exchange. This does not apply if the customer
   claims the item is faulty.
3. Escalate to a human if any of these is true: the order is £150 or
   more; the customer claims the item is faulty; the item arrived
   damaged; the customer disputes an earlier denial; the customer
   declines an exchange the shop offered; the customer asks to speak
   to a human. A human calls the customer back within 1 working day.
4. Exchange only (approve-exchange even if a refund was requested) if
   the return is otherwise eligible and any of these is true: the
   customer's history is flagged; the product is rare-material; the
   shop sent the wrong size or colour and the case is approved under
   rule 5 after the 7-day guarantee period.
5. Otherwise approve what the customer requested (refund or exchange)
   if the return is eligible under its price band:
   - Orders of £50 or less: up to 60 days since delivery; the original
     box is not required; all other conditions must pass.
   - Orders above £50: up to 30 days since delivery; all conditions
     must pass.
6. Conditions: the item is unused, has no stains, has no tears, has not
   been washed, and has its original price tag and original box.
7. If no rule above approves the return, deny-out-of-policy.

Definitions: "faulty" means a defect in the item itself; damage the
customer caused is a failed condition, not a fault. "Shop sent the
wrong size/colour" is the shop's mistake; a size/colour the customer
chose themselves is not a shop error. Rare-material products are never
priced under £50.

DRAFT RULES:
- You may state public terms: the return period, that items must be
  returned in their original condition with tags, and that
  rare-material items are exchange-only.
- Never mention internal rules: the £150 threshold, the price bands or
  the 60-day rule, flagged customer history, or the decision labels.
- Only state facts given in the input; never invent details.
- Approvals: the customer selects a pickup date and time; refunds and
  exchanges happen only after the item is received; a refund then
  takes 3-5 working days; an exchange replacement is sent within
  5 working days.
- Denials close both the refund and the exchange and offer no pickup.
- Escalations say a member of the team will review the request and
  call the customer within 1 working day; offer no pickup.
- Never blame the customer. Do not use exclamation marks.

Answer in exactly this format:
Decision: <one decision>
Draft: <the reply to the customer>
```

## 4. Draft rubric (fixed; each draft scores 0–5)

One point each:

1. **Outcome:** the draft states the outcome that matches the gold
   decision (approval / exchange offer / refusal / team review).
2. **Next step and process facts:** correct for the decision — pickup
   offered only on approvals; refund 3–5 working days after receipt;
   replacement within 5 working days; escalation promises a callback
   within 1 working day; denial offers no pickup.
3. **Policy language:** any reason given uses public terms only; no
   internal rule (threshold, band, history, label) is disclosed.
4. **No invention:** every fact in the draft is present in the input.
5. **Tone and form:** polite, no blame, no exclamation marks, reads as
   one complete reply.

A draft that fails point 3 by leaking an internal rule also counts as
a leak failure for criterion S5, whatever its total.

## 5. Run protocol

- Temperature 0 where the platform allows it; one run per model.
- The decision is read from the `Decision:` line; if the line is
  missing or is not one of the four labels, the decision scores 0.
- Record for each model: total correct /16, correct per decision type,
  mean draft rubric score, number of leak failures.
- Baseline results go in the scorecard file alongside the fine-tuned
  results [C.10]; raw model outputs are saved with the run so any
  score can be re-checked.
