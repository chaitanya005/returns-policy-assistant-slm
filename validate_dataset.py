#!/usr/bin/env python3
"""Validate dataset.jsonl against the locked v5 policy + SOP draft rules.

Checks:
- JSON validity, exact field sets, types
- label re-derived from the v5 ladder (field-driven + controlled message triggers)
- label balance counts
- contradictions: same input signature with different labels; exact duplicates
- rare-material => price >= 50
- draft rules: internal-rule leak scan, pickup/timeline structure per label,
  no exclamation marks, no decision labels inside drafts
Exit code 1 if any error.
"""
import json, sys, collections

PATH = sys.argv[1] if len(sys.argv) > 1 else \
    "dataset.jsonl"

LABELS = {"approve-refund", "approve-exchange", "deny-out-of-policy", "escalate-to-human"}
INPUT_FIELDS = {"item", "order_value_gbp", "days_since_delivery", "used", "has_stains",
                "has_tears", "was_washed", "has_original_tag", "has_original_box",
                "customer_request", "reason", "customer_history", "product_flag",
                "customer_message"}
BOOLS = ["used", "has_stains", "has_tears", "was_washed", "has_original_tag", "has_original_box"]

def triggers(msg):
    m = msg.lower()
    return {
        "faulty": any(k in m for k in ["faulty", "fault", "defect"]),
        "damaged": "arrived damaged" in m or "damaged on arrival" in m or "damaged when it arrived" in m,
        "dispute": "dispute" in m or "appeal" in m,
        "declines": any(k in m for k in ["don't want an exchange", "do not want an exchange",
                                         "refuse the exchange", "won't accept an exchange",
                                         "not accept an exchange"]),
        "human": any(k in m for k in ["speak to a human", "talk to a human", "real person",
                                      "speak to someone from", "human being"]),
    }

def derive(i):
    price, days = i["order_value_gbp"], i["days_since_delivery"]
    t = triggers(i["customer_message"])
    shop_error = i["reason"].startswith("shop sent wrong")
    all_strict = (not i["used"] and not i["has_stains"] and not i["has_tears"]
                  and not i["was_washed"] and i["has_original_tag"] and i["has_original_box"])
    flex_ok = (not i["used"] and not i["has_stains"] and not i["has_tears"]
               and not i["was_washed"] and i["has_original_tag"])  # box waived
    # shop-error guarantee (<=7d, all conditions pass) beats the £150+ trigger only
    if shop_error and days <= 7 and all_strict and not any(t.values()):
        return "approve-exchange"
    if any(t.values()):
        return "escalate-to-human"
    premium = i["product_flag"] == "rare-material" or price >= 150
    if premium and i["reason"] in ("wrong size", "wrong colour") and days <= 3 and all_strict:
        return "approve-exchange"  # Step 0 (faulty already escalated above)
    if price >= 150:
        return "escalate-to-human"
    if price <= 50:
        eligible = days <= 60 and flex_ok
    else:
        eligible = days <= 30 and all_strict
    if not eligible:
        return "deny-out-of-policy"
    if i["customer_history"] == "flagged" or i["product_flag"] == "rare-material" or shop_error:
        return "approve-exchange"  # exchange-only (shop-error here = post-guarantee)
    return "approve-refund" if i["customer_request"] == "refund" else "approve-exchange"

LEAKS = ["£150", "150", "60-day", "60 day", "flagged", "high-value", "high value",
         "price band", "threshold", "approve-refund", "approve-exchange",
         "deny-out-of-policy", "escalate-to-human", "escalat"]

errors, warnings = [], []
rows = []
with open(PATH) as f:
    for n, line in enumerate(f, 1):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except Exception as e:
            errors.append(f"line {n}: invalid JSON: {e}")

counts = collections.Counter()
sig = {}
for r in rows:
    rid = r.get("id", "?")
    if set(r.keys()) != {"id", "input", "decision", "draft_reply", "review"}:
        errors.append(f"{rid}: top-level keys {sorted(r.keys())}")
        continue
    i = r["input"]
    if set(i.keys()) != INPUT_FIELDS:
        errors.append(f"{rid}: input fields mismatch: {sorted(set(i.keys()) ^ INPUT_FIELDS)}")
        continue
    for b in BOOLS:
        if not isinstance(i[b], bool):
            errors.append(f"{rid}: {b} not boolean")
    if r["decision"] not in LABELS:
        errors.append(f"{rid}: bad label {r['decision']}")
    counts[r["decision"]] += 1
    if i["product_flag"] == "rare-material" and i["order_value_gbp"] < 50:
        errors.append(f"{rid}: rare-material under £50")
    exp = derive(i)
    if exp != r["decision"]:
        errors.append(f"{rid}: label {r['decision']} != ladder-derived {exp}")
    key = json.dumps(i, sort_keys=True)
    if key in sig and sig[key] != r["decision"]:
        errors.append(f"{rid}: CONTRADICTION with earlier example (same input, label {sig[key]})")
    elif key in sig:
        warnings.append(f"{rid}: exact duplicate input of an earlier example")
    sig[key] = r["decision"]
    d = r["draft_reply"]
    dl = d.lower()
    for leak in LEAKS:
        if leak in dl:
            errors.append(f"{rid}: draft leaks internal term '{leak}'")
    if "!" in d:
        errors.append(f"{rid}: draft contains '!'")
    lab = r["decision"]
    if lab.startswith("approve"):
        if "pickup" not in dl:
            errors.append(f"{rid}: approved draft missing pickup line")
    else:
        if "pickup" in dl:
            errors.append(f"{rid}: {lab} draft must not offer pickup")
    if lab == "approve-refund" and "3-5 working days" not in d:
        errors.append(f"{rid}: refund draft missing '3-5 working days'")
    if lab == "approve-exchange" and "within 5 working days" not in d:
        errors.append(f"{rid}: exchange draft missing 'within 5 working days'")
    if lab == "escalate-to-human":
        if "1 working day" not in d:
            errors.append(f"{rid}: escalate draft missing 1-working-day callback")
        if "review" not in dl:
            errors.append(f"{rid}: escalate draft missing team-review framing")
    if lab == "deny-out-of-policy":
        if "refund" not in dl or "exchange" not in dl:
            errors.append(f"{rid}: deny draft must close both refund and exchange")
        if "original condition" not in dl and "return period" not in dl:
            errors.append(f"{rid}: deny draft missing public-term link "
                          f"('original condition' or 'return period')")

print(f"examples: {len(rows)}")
print("label counts:", dict(counts))
for w in warnings:
    print("WARN:", w)
for e in errors:
    print("ERROR:", e)
print("RESULT:", "FAIL" if errors else "PASS")
sys.exit(1 if errors else 0)
