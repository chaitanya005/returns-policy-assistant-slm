"""Prepare SFT training data from the locked splits.

Reads files/train.jsonl ONLY (never test.jsonl, never validation.jsonl
for training). For each train example it emits one line:
  {"id", "system", "user", "assistant"}
where:
  - "system" is the shared best prompt (hidden_files/baseline_prompt.txt,
    identical to the baseline prompt),
  - "user" is the example's input object as JSON, exactly as in the dataset,
  - "assistant" is "Decision: <label>\nDraft: <gold draft_reply>".

Also writes a dry-run slice (the first 8 train lines) for the
dry run: a few steps on a small slice to verify data loading, loss
computation and checkpoint saving before the full run.

Run from the project folder:
  python3 hidden_files/prepare_training_data.py

Outputs (hidden_files, not files/ — these are derived, not source data):
  hidden_files/train_sft.jsonl
  hidden_files/train_sft_dryrun.jsonl

No model, API key, or Tinker call is involved here; this is data prep
only. The training script itself is still to be walked through
step by step before training, so this file can be diagrammed
honestly.
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
FILES = ROOT
HIDDEN = ROOT
VALID_DECISIONS = {
    "approve-refund",
    "approve-exchange",
    "deny-out-of-policy",
    "escalate-to-human",
}
DRY_RUN_SIZE = 8


def main():
    system = (HIDDEN / "baseline_prompt.txt").read_text().strip()
    rows = [json.loads(line) for line in open(FILES / "train.jsonl") if line.strip()]
    assert len(rows) == 68, f"expected 68 train examples, got {len(rows)}"
    out = []
    for r in rows:
        assert r["decision"] in VALID_DECISIONS, r["id"]
        assert r["draft_reply"] and "!" not in r["draft_reply"], r["id"]
        out.append({
            "id": r["id"],
            "system": system,
            "user": json.dumps(r["input"], sort_keys=True),
            "assistant": f"Decision: {r['decision']}\nDraft: {r['draft_reply']}",
        })
    # Guard: no test/validation id may leak into training data.
    for split in ("test.jsonl", "validation.jsonl"):
        seen = {json.loads(l)["id"] for l in open(FILES / split) if l.strip()}
        assert not (seen & {o["id"] for o in out}), split
    with open(HIDDEN / "train_sft.jsonl", "w") as f:
        for o in out:
            f.write(json.dumps(o) + "\n")
    with open(HIDDEN / "train_sft_dryrun.jsonl", "w") as f:
        for o in out[:DRY_RUN_SIZE]:
            f.write(json.dumps(o) + "\n")
    print(f"wrote {len(out)} lines to train_sft.jsonl")
    print(f"wrote {DRY_RUN_SIZE} lines to train_sft_dryrun.jsonl")

    # Validation in the same SFT shape — used ONLY to measure loss at
    # each epoch; never trained on, never part of the train outputs.
    vrows = [json.loads(line) for line in open(FILES / "validation.jsonl") if line.strip()]
    assert len(vrows) == 16, f"expected 16 validation examples, got {len(vrows)}"
    vout = []
    for r in vrows:
        assert r["decision"] in VALID_DECISIONS, r["id"]
        vout.append({
            "id": r["id"],
            "system": system,
            "user": json.dumps(r["input"], sort_keys=True),
            "assistant": f"Decision: {r['decision']}\nDraft: {r['draft_reply']}",
        })
    assert not ({o["id"] for o in vout} & {o["id"] for o in out})
    with open(HIDDEN / "validation_sft.jsonl", "w") as f:
        for o in vout:
            f.write(json.dumps(o) + "\n")
    print(f"wrote {len(vout)} lines to validation_sft.jsonl")


if __name__ == "__main__":
    main()
