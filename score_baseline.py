#!/usr/bin/env python3
"""Baseline scoring harness for Part C [C.7]/[C.10].

Usage:
  score_baseline.py prepare
      Write hidden_files/test_prompts.jsonl: one line per test example
      with the shared system prompt (hidden_files/baseline_prompt.txt)
      and the user message (the example input as JSON).

  score_baseline.py score RESULTS.jsonl
      RESULTS.jsonl lines: {"id": "ex-001", "output": "<raw model reply>"}
      Parses the "Decision:" line, exact-matches against the gold label
      in files/test.jsonl, prints total + per-label accuracy and every
      mismatch, and writes a draft-rubric worksheet next to the results
      file (<name>.rubric.md) for the human rubric scoring.
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent
TEST = BASE / "test.jsonl"
PROMPT = Path(__file__).resolve().parent / "baseline_prompt.txt"
PROMPTS_OUT = Path(__file__).resolve().parent / "test_prompts.jsonl"
LABELS = ["approve-refund", "approve-exchange",
          "deny-out-of-policy", "escalate-to-human"]


def load_test():
    return [json.loads(l) for l in TEST.read_text().splitlines() if l.strip()]


def prepare():
    system = PROMPT.read_text().strip()
    rows = load_test()
    with PROMPTS_OUT.open("w") as f:
        for r in rows:
            f.write(json.dumps({
                "id": r["id"],
                "system": system,
                "user": json.dumps(r["input"], indent=2),
            }) + "\n")
    print(f"wrote {len(rows)} prompts to {PROMPTS_OUT.name}")


def parse_decision(output):
    m = re.search(r"Decision:\s*(\S+)", output or "")
    return m.group(1) if m else None


def parse_draft(output):
    m = re.search(r"Draft:\s*(.*)", output or "", re.S)
    return m.group(1).strip() if m else ""


def score(path):
    gold = {r["id"]: r for r in load_test()}
    results = {}
    for line in Path(path).read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            results[r["id"]] = r.get("output", "")

    total = correct = 0
    per = defaultdict(lambda: [0, 0])
    misses = []
    worksheet = ["# Draft rubric worksheet",
                 "Score each draft 0-5 with the rubric in "
                 "files/part-c-baseline-plan.md §4.\n"]
    for rid in sorted(gold):
        g = gold[rid]
        out = results.get(rid)
        pred = parse_decision(out) if out is not None else None
        ok = pred == g["decision"]
        total += 1
        correct += ok
        per[g["decision"]][1] += 1
        per[g["decision"]][0] += ok
        if not ok:
            misses.append(f"{rid}: gold={g['decision']} predicted={pred!r}")
        worksheet.append(f"## {rid} — gold: {g['decision']} | model: {pred}")
        worksheet.append(f"Gold draft: {g['draft_reply']}")
        worksheet.append(f"Model draft: {parse_draft(out) if out else '(no output)'}")
        worksheet.append("Rubric (outcome / process / policy language / "
                         "no invention / tone): __ / 5   Leak: Y/N\n")

    print(f"decision accuracy: {correct}/{total}")
    for lab in LABELS:
        c, t = per[lab]
        print(f"  {lab}: {c}/{t}")
    if misses:
        print("mismatches:")
        for m in misses:
            print(" ", m)
    ws = Path(path).with_suffix(".rubric.md")
    ws.write_text("\n".join(worksheet))
    print(f"rubric worksheet: {ws}")


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "prepare":
        prepare()
    elif len(sys.argv) >= 3 and sys.argv[1] == "score":
        score(sys.argv[2])
    else:
        print(__doc__)
        sys.exit(1)
