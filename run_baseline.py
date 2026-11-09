"""Run the base-model baseline: sample the base Qwen model on the
16 test prompts and save the raw replies for scoring.

Before running:
  pip install tinker tinker-cookbook
  export TINKER_API_KEY="..."        # your key, in this terminal session
  Put test_prompts.jsonl in the same folder as this script.

Run:
  python3 run_baseline.py

Output: base_qwen_results.jsonl — one {"id", "output"} line per test
example, in the format the scoring harness expects. Nothing in the
model's replies is edited; scoring happens afterwards, separately.
"""
import json

import tinker
from tinker_cookbook import renderers

BASE_MODEL = "Qwen/Qwen3-8B"  # must match the fine-tuning base in lora_config.yaml


def extract_text(message):
    """Pull the reply text out of a parsed response message.

    parse_response returns a message whose content is either a plain
    string (thinking left inline, wrapped in <think>...</think>) or a
    list of parts (a 'thinking' part and a 'text' part). Either way,
    the scoreable reply is the final answer text only.
    """
    content = message["content"] if isinstance(message, dict) else message
    if isinstance(content, list):
        return "\n".join(
            part.get("text", "")
            for part in content
            if isinstance(part, dict) and part.get("type") == "text"
        ).strip()
    text = str(content)
    if "</think>" in text:
        text = text.split("</think>", 1)[1]
    return text.strip()


def main():
    service_client = tinker.ServiceClient()
    sampling_client = service_client.create_sampling_client(base_model=BASE_MODEL)
    tokenizer = sampling_client.get_tokenizer()
    # The renderer wraps chat messages in Qwen3's chat format (special
    # tokens, turn markers) and knows the model's stop sequences.
    renderer = renderers.get_renderer("qwen3", tokenizer)

    prompts = [json.loads(line) for line in open("test_prompts.jsonl")]
    with open("base_qwen_results.jsonl", "w") as out:
        for p in prompts:
            messages = [
                {"role": "system", "content": p["system"]},
                {"role": "user", "content": p["user"]},
            ]
            prompt = renderer.build_generation_prompt(messages)
            params = tinker.SamplingParams(
                max_tokens=800,
                temperature=0.0,
                stop=renderer.get_stop_sequences(),
            )
            result = sampling_client.sample(
                prompt=prompt, num_samples=1, sampling_params=params
            ).result()
            message, _ok = renderer.parse_response(result.sequences[0].tokens)
            text = extract_text(message)
            out.write(json.dumps({"id": p["id"], "output": text}) + "\n")
            print(p["id"], "done")
    print("wrote base_qwen_results.jsonl")


if __name__ == "__main__":
    main()
