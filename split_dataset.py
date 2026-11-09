#!/usr/bin/env python3
"""Split dataset.jsonl into train / validation / test (68 / 16 / 16).

Selection is explicit (not random) so the small validation and test sets
stay balanced (4 per decision) and the test set carries the sharpest
boundary cases:
  - GBP 149 approve-refund (ex-014) vs GBP 150 escalate (ex-100)
  - day 60 approve (ex-017) vs day 61 deny (ex-074); day 30 (ex-020)
  - GBP 51 no-box deny (ex-071) vs the GBP 50-or-less no-box approvals
  - Step 0 day-3 boundary (ex-048), shop-error guarantee beating the
    high-value escalate trigger (ex-037), faulty claim blocking Step 0
    (ex-084)
The test file is set aside for scoring and must not be used
while building or tuning. Re-run after any review-pass changes.
"""
import json
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent
SRC = BASE / "dataset.jsonl"

TEST = {
    # approve-refund
    "ex-002", "ex-014", "ex-017", "ex-020",
    # approve-exchange
    "ex-026", "ex-037", "ex-044", "ex-048",
    # deny-out-of-policy
    "ex-056", "ex-061", "ex-071", "ex-074",
    # escalate-to-human
    "ex-076", "ex-084", "ex-090", "ex-100",
}
VALIDATION = {
    # approve-refund
    "ex-005", "ex-010", "ex-021", "ex-024",
    # approve-exchange (Step 0, flagged-history, post-guarantee shop-error, strict)
    "ex-029", "ex-032", "ex-040", "ex-049",
    # deny-out-of-policy
    "ex-052", "ex-064", "ex-068", "ex-075",
    # escalate-to-human (faulty, arrived damaged, declines exchange, asks for human)
    "ex-082", "ex-086", "ex-094", "ex-097",
}


def main():
    rows = [json.loads(line) for line in SRC.read_text().splitlines() if line.strip()]
    ids = [r["id"] for r in rows]
    assert len(ids) == len(set(ids)) == 100, f"expected 100 unique examples, got {len(ids)}"
    assert not (TEST & VALIDATION), "test/validation overlap in selection"
    assert (TEST | VALIDATION) <= set(ids), "selection contains unknown ids"

    splits = {"train": [], "validation": [], "test": []}
    for r in rows:
        if r["id"] in TEST:
            splits["test"].append(r)
        elif r["id"] in VALIDATION:
            splits["validation"].append(r)
        else:
            splits["train"].append(r)

    for name, part in splits.items():
        out = BASE / f"{name}.jsonl"
        out.write_text("".join(json.dumps(r) + "\n" for r in part))
        counts = dict(Counter(r["decision"] for r in part))
        print(f"{name}: {len(part)} examples, labels {counts}")

    total = sum(len(p) for p in splits.values())
    seen = [r["id"] for p in splits.values() for r in p]
    assert total == 100 and len(set(seen)) == 100, "splits must partition the 100 examples"
    print("partition check: OK (100 examples, no overlap)")


if __name__ == "__main__":
    main()
