# Pick one behavior

Status: written by Cooper at Chaitanya's request on 2026-10-29, from the policy
locked 2026-10-23/24, and approved by Chaitanya the same evening
("We are good now approve this version"). Final unless he revisits it.

## The behavior, in one sentence

Given an order and a return request at a clothing shop, the model decides what
the shop's returns policy allows — `approve-refund`, `approve-exchange`,
`deny-out-of-policy`, or `escalate-to-human` — and drafts the reply to the
customer.

## Why a prompt is not enough

This policy belongs to one shop, and no general model knows it. Its decisions
turn on exact numbers — a £50 boundary between a flexible 60-day window and a
strict 30-day one, a £150 line above which a human must review the case — plus
exceptions that have to be checked in a fixed order, such as a premium size or
colour problem reported within three days going straight to an exchange instead
of escalating. A prompt would have to carry all of these rules on every
request, and even then a general model applies them unevenly: it can be talked
into approving a return that fails the conditions by a sympathetic message, or
deny a faulty item that should have been escalated for verification. Those
mistakes are not just bad sentences — a wrong approval costs the shop money,
and a wrong denial costs it the customer's trust. What the shop actually needs
is the same rule applied the same way to every case, including cases it has
never seen before. Fine-tuning a small model on reviewed examples of this
policy bakes that behavior in, instead of re-explaining it in a long prompt on
every request and hoping it holds.

## Input and output

- **Input:** the item; the order value in pounds; days since delivery; the
  item's condition as six yes/no checks (used, has stains, has tears, was
  washed, has original tag, has original box); what the customer is requesting
  (refund or exchange); their reason; the customer's return history (good or
  flagged); a product flag (standard or rare-material); and the customer's
  message.
- **Output:** one decision — exactly one of `approve-refund` /
  `approve-exchange` / `deny-out-of-policy` / `escalate-to-human` — and a draft
  reply to the customer, written in the shop's public language, with the next
  step included where there is one.
