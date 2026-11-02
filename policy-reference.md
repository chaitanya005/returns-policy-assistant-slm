# Part C — Returns Policy Assistant: locked v4 reference

**Purpose:** a checkable reference for Chaitanya's own review SOP [C.5] and dataset work.
This is NOT the SOP itself, and NOT dataset examples. He writes those; this only
consolidates decisions already locked in conversation (2026-10-23 to 2026-10-24)
so the SOP session does not have to re-derive them from chat.

**Status check:** policy is at v4 (v3 ladder + Step 0 + shop-error rule). No dataset
file, repo or training files have been created yet; the 5 practice examples exist
only in conversation. The QKV LinkedIn post and the Monday LinkedIn invite check
are separate threads and are not covered here.

## 1. Decision ladder — first match wins, top to bottom

### Step 0 — premium colour/size fast lane (checked BEFORE escalate)
All four must hold:
- premium product: rare-material OR £150+
- reason is colour/size
- within 3 days of delivery
- all conditions strictly pass

→ **approve-exchange** (skips the £150+ escalate step).

Note: practice Example 4 (£175 coat, changed-mind reason) still escalates — its
reason is not colour/size, so Step 0 does not apply.

### Step 1 — escalate-to-human (closed trigger list, never an "unsure" bucket)
- order £150+
- faulty claim (escalate to verify fault vs customer damage)
- item arrived damaged
- customer disputes a denial
- customer declines / refuses an exchange offer
- customer asks for a human

Escalate drafts: presented as a deliberate team review ("a member of our team
will review this"), never as a system failure. Promise a phone callback within
1 working day. No pickup offered. No £150 / high-value threshold disclosed.

### Step 2 — exchange-only
Otherwise eligible, but either:
- `customer_history: flagged` (bad return history / suspected non-genuine refunds), or
- `product_flag: rare-material`

### Step 3 — approve as requested
- Flexible band, £50 or less: up to 60 days; original box NOT required; all
  other conditions must pass.
- Strict band, above £50 to £149.99: up to 30 days; ALL conditions must pass:
  unused, no stains, no tears, not washed, original price tag AND original box.

### Step 4 — deny-out-of-policy
Past the window for its band, or any (applicable) condition fails.

## 2. Shop-error rule (shop sent the wrong size/colour)
- Within 7 days + all other conditions pass → guaranteed correction exchange
  for the correct size/colour actually ordered. The 7 days is a priority
  correction window for the shop's own mistake.
- After 7 days → the special guarantee expires and the normal ladder applies
  (price band, conditions, customer request). This was a correction in chat:
  Chaitanya first tapped "deny", then immediately corrected it in text to
  "normal return windows apply" — the text version is authoritative.
- This is distinct from customer-chosen wrong size/colour, which follows the
  normal colour/size rules, and from a faulty item.

## 3. Dataset constraints already locked
- Rare-material products are never priced under £50
  (`product_flag: rare-material` ⇒ price ≥ £50). This removes the clash with
  the flexible-band box waiver.
- Format: one JSONL line per example with `input` / `decision` / `draft_reply`,
  plus a separate `review` metadata block (reviewer, kept) that is NOT training
  input/output, per brief [C.5].
- Input fields: `item`; `order_value_gbp` and `days_since_delivery` as numbers;
  condition as six booleans (`used`, `has_stains`, `has_tears`, `was_washed`,
  `has_original_tag`, `has_original_box`); `customer_request`; `reason`;
  `customer_history`; `product_flag`; free-text `customer_message` where
  faulty / arrived-damaged / disputed-denial / human-request / declines-exchange
  triggers are visible.
- Target: at least 100 reviewed examples, roughly balanced across the 4 decisions
  (~25 each), split train/validation/test with the test set untouched until scoring.
- No personal data (names, emails, phone numbers) in examples, per brief [C.4].

## 4. Draft-reply rules already settled (public vs internal)
Public terms that MAY be cited in customer language: return window,
unused / original-condition requirement, and (to be added to the public terms)
"rare-material items are exchange-only".
Internal rules that must NOT be disclosed in a draft: flagged history /
suspicion of non-genuine refunds, the £150 escalation threshold, the
price-band ladder, and the flexible 60-day / £50-or-less mechanism. Internal
reasoning belongs in the dataset/reviewer record, not the customer reply.

Other settled draft mechanics:
- Refund/exchange is initiated only after the product is received; refund then
  takes 3–5 working days to reflect; exchange replacement within 5 working days.
- Returns use a pickup the customer selects; do NOT invent pickup time slots.
- Deny drafts tie the refusal to "original condition", close both refund and
  exchange, offer no pickup, and invent no detail beyond the input fields
  (e.g. do not write "a few stains" when the input only says `has_stains: yes`).
- Naming the material in a rare-material exchange draft is acceptable because it
  is a visible product fact — but only once the exchange-only line is in the
  public terms, and the draft must still include the exchange next-step flow
  (pickup, then replacement), not just the refund refusal.

## 5. SOP checklist — what brief [C.5] / [C.6] require the SOP to cover
Chaitanya writes the SOP; this is only the coverage checklist drawn from the brief:
- [ ] One-sentence behaviour [C.3] + paragraph on why a prompt is not enough
  (still to be written by Chaitanya — a separate pending item, not in this file).
- [ ] Each label defined so two reviewers following the SOP give the same label
  to the same example.
- [ ] The full ladder above, in order, including Step 0 and the shop-error rule.
- [ ] For each example, record: label, reviewer, kept/rejected. Reject examples
  that do not teach the behaviour.
- [ ] Contradiction check: same situation, different labels ([C.6]).
- [ ] Label-balance check ([C.6]) — target ~25 per decision.
- [ ] Read a random sample of 20 examples; fix the data, then update the SOP so
  the same problem does not come back ([C.6]).
- [ ] The public-terms list (including rare-material exchange-only) vs the
  internal-rules list in §4, so reviewers can check drafts for leaks.

## 6. Open edge questions — NOT yet decided, flag for the SOP session
Do not assume answers to these; they need Chaitanya's call:
1. Shop-error vs escalate for high-value items: a £150+ shop-error case at
   day 4–7 is inside the 7-day shop-error guarantee (exchange) but outside
   Step 0's 3 days — does the shop-error guarantee override the £150+
   escalate step, or does it escalate? (Days 0–3 both rules agree: exchange.)
2. Faulty claim + premium colour/size within 3 days: Step 0 requires all
   conditions to strictly pass — does a faulty claim count as failing that
   gate, so the case escalates to verify, rather than taking the Step 0 exchange?
3. Shop-error after 7 days, approved under the normal ladder: if the customer
   requested a refund rather than an exchange, is the normal "approve as
   requested" outcome a refund, or does a shop-error case stay exchange-only
   for the correction?

## 7. Still pending after this reference (from conversation, 2026-10-24)
- 2 Step 0 practice examples (premium colour/size within 3 days, and after 3 days).
- One draft style/grammar pass over the 5 practice examples (neutral opening,
  Example 5 exchange next-step flow, Example 2 box reassurance, no invented details).
- Chaitanya's [C.3] paragraph.
- The review SOP [C.5] itself.
- Scaling from 5 practice examples to the full 100-example balanced dataset.

## 8. v5 amendments — the three §6 edge questions, decided 2026-10-29

The policy is now v5: the v4 ladder above plus these three decisions by
Chaitanya (from the edge-questions decision pack):

- **Q1 = A (shop-error beats escalate inside the guarantee):** a shop-error
  case within 7 days with all conditions passing is `approve-exchange` even
  when the order is £150+ — i.e. at days 4–7 the guaranteed correction
  exchange overrides the £150+ escalate trigger. In ladder terms, the
  shop-error guarantee is checked before the £150+ escalate step. (Days 0–3
  both rules already agreed: exchange.)
- **Q2 = A (faulty blocks Step 0):** a faulty claim means Step 0's "all
  conditions strictly pass" gate is not met, so a premium colour/size case
  within 3 days that also claims a fault is `escalate-to-human` (verify fault
  vs customer damage). "Faulty = escalate to verify" has no exceptions.
- **Q3 = B (shop-error stays exchange-only):** a shop-error case approved
  under the normal ladder after day 7 is `approve-exchange` even if the
  customer requested a refund — shop-error is effectively a third
  exchange-only trigger (alongside flagged history and rare-material),
  applying whenever the case is otherwise eligible. It does not rescue
  ineligible cases: past the band window or a failed condition still denies
  (e.g. practice Example 10: £60 shop-error at day 40 = `deny-out-of-policy`).
  After day 7 the guarantee no longer overrides escalate, so a £150+
  shop-error case after day 7 escalates at Step 1 as usual.

Consolidated shop-error rule (v5): wrong item sent by the shop → within
7 days + all conditions pass = guaranteed correction exchange (beats £150+
escalate); after 7 days = normal ladder, but if approved the remedy is
exchange-only; window/condition failures still deny.
