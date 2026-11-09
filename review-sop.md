# Review SOP: Returns Policy Assistant

**Status:** v1 — written by Cooper at Chaitanya's request on 2026-10-29 from
the locked policy (v5) and the approved [C.3] text, and **approved by
Chaitanya on 2026-10-29**. This is the current SOP; any change goes through
the version note at the end of this document.

**Purpose (brief [C.5]):** this document tells a reviewer how to decide the
label for any returns example, and how to check its draft reply. Two
reviewers following this SOP should give the same label to the same example.
If a case is not covered here, do not improvise a label — flag it, and the
policy owner (Chaitanya) decides; the decision is then added to this SOP.

---

## 1. The behavior

Given an order and a return request at a clothing shop, the model decides
what the shop's returns policy allows — `approve-refund`, `approve-exchange`,
`deny-out-of-policy`, or `escalate-to-human` — and drafts the reply to the
customer.

Every example is one JSON line with three parts:

- **input** — the facts of the case (see §2)
- **decision** — exactly one of the four labels above, spelled exactly that
  way (scoring is exact-match; near-enough labels are wrong)
- **draft_reply** — the customer-facing reply (rules in §5)

Plus a separate review record (§6) that is **not** part of the training data.

## 2. The input fields — and the checks before labelling

Fields: `item`; `order_value_gbp` (number); `days_since_delivery` (number);
six condition booleans — `used`, `has_stains`, `has_tears`, `was_washed`,
`has_original_tag`, `has_original_box`; `customer_request` (`refund` or
`exchange`); `reason`; `customer_history` (`good` or `flagged`);
`product_flag` (`standard` or `rare-material`); `customer_message` (free
text).

Before labelling, reject or fix the example if any of these fail:

1. **A decision-changing fact is missing.** Anything that can change the
   label must be visible in the input. Escalation triggers that are not
   order facts (faulty claim, arrived damaged, disputes a denial, declines
   an exchange offer, asks for a human) must be stated in `customer_message`.
   A reviewer must never have to guess or infer a trigger.
2. **Rare-material priced under £50.** `product_flag: rare-material`
   requires `order_value_gbp` >= 50. Violations are data errors — reject.
3. **Personal data present.** No names, emails, phone numbers or addresses
   anywhere in the example (brief [C.4]). Remove or reject.
4. **The reason and the message disagree** (e.g. `reason: wrong size` but the
   message describes a fault). Fix the fields so they tell one story.

## 3. Definitions a reviewer needs

- **Condition checks.** "All conditions pass" means: `used` = no, no stains,
  no tears, not washed, original tag present, original box present — except
  where a band rule waives the box (§4, Step 3).
- **Faulty** means the defect is in the item itself — present on arrival, or
  appearing after proper use (a seam splitting, a zip failing). Damage the
  customer caused (stains, tears, washing damage) is **not** faulty; it is a
  failed condition check.
- **Shop-error** means the shop sent the wrong size or colour — the shop's
  mistake. A customer choosing the wrong size or colour is not shop-error.
- **Premium** means `product_flag: rare-material` **or** order value £150+.
- **Flagged history** means the customer has a record of repeated refund
  requests suspected to be non-genuine. "Good" history is the default state;
  it waives nothing and changes nothing.
- **Second-turn cases.** "Disputes a denial" and "declines an exchange
  offer" can only be labelled when the earlier turn is visible in the
  example's input (in `customer_message`). Without that context, the trigger
  does not exist.

## 4. How to decide the label — walk the ladder, first match wins

Check the steps **in this order**. Stop at the first step that matches.
Falling out of a step never sends a case straight to deny — it drops to the
next step. Deny is only the last step.

### Step 0 — premium colour/size fast lane → `approve-exchange`

All four must hold: premium product · reason is colour/size · within 3 days
of delivery · all conditions strictly pass.
**Exception (v5):** a faulty claim blocks Step 0 — if the message claims a
fault, skip this step and go to Step 1 (faults are verified, never
fast-laned).

### Shop-error rule — checked alongside Steps 0–2

The shop sent the wrong size/colour:

- **Within 7 days and all conditions pass → `approve-exchange`** for the
  correct size/colour actually ordered. This guarantee is checked before
  the £150+ escalate trigger: a £150+ shop-error case at days 4–7 is still
  `approve-exchange`. (It does **not** override the other Step 1 triggers —
  a faulty claim, arrived-damaged claim, dispute, declined exchange, or a
  request for a human still escalates.)
- **After 7 days** the guarantee has expired: run the normal ladder. If the
  case is approved, the remedy is exchange-only (see Step 2) — never a
  refund. If the case is not eligible under the normal ladder, it denies
  like any other case.

### Step 1 — escalate → `escalate-to-human`

Any one of these triggers escalates. This list is closed — escalate is
never a label for "unsure" or "unusual":

- Order value **£150 or more** (unless the shop-error guarantee above or
  Step 0 already caught the case)
- **Faulty claim** — escalate to verify fault vs customer damage
- Item **arrived damaged**
- Customer **disputes a denial**
- Customer **declines / refuses an exchange offer**
- Customer **asks for a human** — the shop's promise is a phone callback
  within 1 working day

High value never denies on its own, and good history never cancels an
escalation. Escalate means a human reviews and decides; the human may still
approve the refund or exchange afterwards.

### Step 2 — exchange-only → `approve-exchange`

The case is otherwise eligible (it would pass Step 3), but the customer
asked for a refund and one of these applies:

- `customer_history: flagged`
- `product_flag: rare-material`
- The case is a **shop-error** case past its 7-day guarantee (v5)

Label `approve-exchange`. The draft offers the exchange instead of the
refund (§5).

### Step 3 — approve as requested

Eligible, and none of the steps above matched → approve what the customer
asked for (`approve-refund` or `approve-exchange`):

- **Flexible band — £50 or less:** up to 60 days; the original box is **not**
  required; all other conditions must pass.
- **Strict band — above £50 to £149.99:** up to 30 days; **all six**
  conditions must pass, including tag and box.
  Boundaries are exact: £50.00 is flexible; £150.00 is Step 1 (subject to
  Step 0 and the shop-error guarantee).

### Step 4 — deny → `deny-out-of-policy`

Reached only when nothing above matched **and** the case is outside its
band's window or a condition it needs has failed.

## 5. How to check the draft reply

### 5.1 Public vs internal — the rule a draft must never break

Drafts may only use **public** language — the terms a customer could be
shown at purchase:

- the return period ("within our 30-day return period")
- items returned unused / in their **original condition**, with tags
- "rare-material items are exchange-only" (a published term of this shop)
- a team review and a callback within 1 working day

Drafts must **never** reveal internal rules:

- flagged history, or any hint of suspicion about the customer
- the £150 escalation threshold, or that a case is "high-value"
- the price bands, the ladder, or the flexible 60-day / £50-or-less
  mechanism
- the decision labels themselves

For internal-trigger cases, state only the outcome in neutral words:
exchange-only → "we can offer an exchange instead of a refund"; escalation →
a team member will review it and call within 1 working day. The internal
reason belongs in the review record, not the customer's copy.

### 5.2 Process facts every draft must respect

- Returns are collected by **pickup**. Approved drafts include one generic
  line asking the customer to select a pickup date and time. Never invent
  specific time slots.
- A refund or exchange starts only **after the item is received**: refunds
  then take **3–5 working days** to reflect; exchange replacements are sent
  **within 5 working days** of receipt, to the customer's address.
- Exchange drafts confirm the replacement the customer asked for (e.g. the
  size selected at the pickup step).
- Escalations promise a **phone callback within 1 working day**. No slot
  selection. Deny and escalate drafts offer **no pickup**.

### 5.3 Structure per decision

- **approve-refund:** decision → public reason → pickup line → "once we've
  received it" → 3–5 working days.
- **approve-exchange (as requested):** decision → answer any worry stated in
  the customer's message in public words (e.g. "You don't need the original
  box for this return") → pickup + selection step → replacement within 5
  working days.
- **approve-exchange (exchange-only):** decline the refund plainly → give
  the public reason where one exists (rare-material) or a neutral outcome
  line (flagged history) → then the full exchange flow, as above. Never
  stop at the refusal.
- **deny-out-of-policy:** "Sorry" → the failing fact in the input's own
  words → tie it to the public term "original condition" → close **both**
  refund and exchange → no pickup, no next step.
- **escalate-to-human:** frame as a deliberate team review ("a member of
  our team will review this"), never as the shop being unable to decide →
  callback within 1 working day → no reason, no threshold, no pickup.

### 5.4 Style rules (apply to every draft)

- Open with the decision. Do not use "After analyzing the product
  condition…" or any stock opening.
- **Invent nothing.** Use only details present in the input — if the input
  says `has_stains: yes`, the draft says "stains", never "a few stains".
  Never blame the customer ("the item has stains", not "you stained it").
- Consistent grammar and punctuation: full stops, no exclamation marks;
  "Once we've received" (not "Once after"); "within 5 working days" (not
  "with the next"); "your", not "you're".

## 6. The review record — what to save for every example

A model may produce a first-pass label and draft; a person reviews every
example before it is kept. For each example record, outside the training
fields: the **label**, the **reviewer**, and **kept or rejected**.

Reject an example when any of these holds:

- the label disagrees with the ladder in §4 (relabel it correctly instead,
  if the input is sound)
- a decision-changing fact is missing from the input (§2)
- the draft leaks an internal rule, invents a detail or a time slot, or
  breaks a process fact in §5.2
- personal data is present and cannot be cleanly removed
- the example duplicates an existing one, or contradicts an existing
  example's label for the same situation

## 7. Before training — consistency checks (brief [C.6])

- **Contradiction check:** search for the same situation carrying two
  labels. Fix the data first, then update this SOP so the same problem does
  not come back.
- **Label balance:** aim for roughly 25 examples per decision (~100 total
  to start). A set that is mostly one label teaches the model to always
  answer that label.
- **Read 20 at random yourself** (the policy owner), checking labels and
  drafts against §§4–5.

## 8. Calibration cases (decided; use them to test a reviewer's walk)

1. £180 coat, day 2, all pass, wrong size, exchange → **approve-exchange**
   (Step 0 — premium + size + within 3 days).
2. £175 coat, day 5, all pass, wrong size, exchange →
   **escalate-to-human** (Step 0 fails on days; Step 1 catches £150+).
3. £160 coat, day 2, changed mind, refund → **escalate-to-human** (Step 0
   fails on the reason; Step 1 catches £150+).
4. £180 coat, day 5, shop sent the wrong colour, all pass, wants the
   correct colour → **approve-exchange** (shop-error guarantee beats the
   £150+ trigger inside 7 days).
5. £160 coat, day 2, all booleans pass, wants a different size, message
   also says "the zip is faulty" → **escalate-to-human** (faulty blocks
   Step 0; verify the fault).
6. £80 shirt, day 10, shop sent the wrong size, all pass, refund requested
   → **approve-exchange** (guarantee expired, but shop-error stays
   exchange-only when approved under the normal ladder).
7. £60 shirt, day 40, shop sent the wrong size, all conditions pass →
   **deny-out-of-policy** (normal ladder: strict band, 30 days, day 40 is
   past it — exchange-only never rescues an ineligible case).
8. £70 rare-material blouse, day 15, all pass, refund requested →
   **approve-exchange** (Step 2 — rare-material is exchange-only).

---

_SOP version: v1 (approved 2026-10-29), written against policy v5. When a
labelling decision changes the policy, update this SOP and the policy
reference together, and re-check any examples already labelled under the
old rule._
