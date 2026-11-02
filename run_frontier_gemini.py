"""Run the frontier-model baseline [C.7] on Google's Gemini flagship via
the free Google AI Studio tier, using Gemini's OpenAI-compatible
endpoint — so this is the OpenAI SDK with a different base URL, key,
and model id. Same 16 test prompts, same scoring as both other models.

Before running:
  Get a free API key at aistudio.google.com (Get API key — no card,
  no billing setup for the free tier).
  pip install openai
  export GEMINI_API_KEY="..."        # your key, in this terminal session
  Put test_prompts.jsonl in the same folder as this script.

Run:
  python3 run_frontier_gemini.py

Output: frontier_gemini_results.jsonl — one {"id", "output"} line per
test example, flushed to disk as each reply arrives, so partial
progress survives an interruption. The script RESUMES: on start it
reads any results already saved, skips those prompts, and appends the
rest — a crashed or rate-limited run never has to start over. Replies
are raw and unedited; scoring happens afterwards, separately.

Notes:
- temperature=0.0 is sent as the protocol requires — Gemini accepts it,
  so unlike the GPT-5 route there is no temperature deviation to record.
- reasoning_effort="low" caps how long the model thinks before
  answering. At the default effort, each call on the free tier took
  over 3 minutes (the model deliberating over the long policy prompt);
  the model, prompt, and scoring are unchanged — only its thinking
  budget. This parameter is recorded on the scorecard.
- Progress is printed before and after each call, with a running
  count of saved answers. If Google answers 429 (rate limit) or 503
  (temporarily overloaded) — both common on the free tier — the script
  waits 60 seconds and tries that same prompt again, up to 8 attempts.
  If all 8 attempts fail, that prompt is SKIPPED for this run (it is
  not written to the results file) and the script moves on to the
  next one — one stubborn prompt can no longer kill the whole run,
  which is what happened on 2026-10-31. Rerunning the script later
  picks skipped prompts up automatically via the resume logic. One
  exception:
  if the DAILY request quota for the model is exhausted, no waiting
  helps until it resets at midnight Pacific (~07:00 UK). Check which
  quota is full at aistudio.google.com/rate-limit.
- Responses are not streamed: each reply appears only when the model
  has finished thinking and writing.
- Free-tier traffic may be used by Google to improve its models. The
  prompts contain only the synthetic shop policy and fictional orders —
  no personal data, per the dataset rules in [C.4].
"""
import json
import os
import time

from openai import OpenAI

MODEL = "gemini-3.8-flash"  # current Gemini flagship on the free tier


def main():
    client = OpenAI(
        api_key=os.environ["GEMINI_API_KEY"],
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        timeout=600,
        max_retries=0,
    )
    prompts = [json.loads(line) for line in open("test_prompts.jsonl")]
    done_ids = set()
    if os.path.exists("frontier_gemini_results.jsonl"):
        for line in open("frontier_gemini_results.jsonl"):
            done_ids.add(json.loads(line)["id"])
    if done_ids:
        print("resuming — already saved:", ", ".join(sorted(done_ids)),
              flush=True)
    skipped = []
    saved = len(done_ids)
    with open("frontier_gemini_results.jsonl", "a") as out:
        for i, p in enumerate(prompts):
            if p["id"] in done_ids:
                continue
            if i:
                time.sleep(15)  # stay inside the free tier's per-minute limit
            print(p["id"], "asking...", flush=True)
            response = None
            for attempt in range(8):
                try:
                    response = client.chat.completions.create(
                        model=MODEL,
                        messages=[
                            {"role": "system", "content": p["system"]},
                            {"role": "user", "content": p["user"]},
                        ],
                        temperature=0.0,
                        max_tokens=4000,
                        reasoning_effort="low",
                    )
                    break
                except Exception as e:
                    status = getattr(e, "status_code", None)
                    retryable = status is None or status == 429 or status >= 500
                    if not retryable:
                        raise
                    if attempt == 7:
                        print(p["id"], "failed after 8 attempts — skipping"
                              " it for this run; a rerun will retry it",
                              flush=True)
                        break
                    print(p["id"], "rate limited or server busy — waiting 60s,"
                          " then retrying", flush=True)
                    time.sleep(60)
            if response is None:
                skipped.append(p["id"])
                continue
            text = response.choices[0].message.content or ""
            out.write(json.dumps({"id": p["id"], "output": text}) + "\n")
            out.flush()
            saved += 1
            print(p["id"], "done", f"({saved}/{len(prompts)} saved)",
                  flush=True)
    if skipped:
        print("finished with gaps — skipped:", ", ".join(skipped),
              "— rerun this script to fill them in", flush=True)
    else:
        print("all answers saved in frontier_gemini_results.jsonl",
              flush=True)


if __name__ == "__main__":
    main()
