# Mermaid diagrams

Two diagrams for the repo README. Diagram 1 shows how one example moves
through every file in the project. Diagram 2 shows the training script,
step by step.

## Diagram 1 — one example through every file

```mermaid
flowchart TD
    A["dataset.jsonl<br/>100 reviewed examples, 25 per decision"] --> B["validate_dataset.py<br/>re-derives every label from the policy ladder;<br/>checks leaks and structure"]
    B --> C["split_dataset.py<br/>fixed, explicit ID selection"]
    C --> D["train.jsonl — 68 examples"]
    C --> E["validation.jsonl — 16 examples"]
    C --> F["test.jsonl — 16 examples"]
    D --> G["prepare_training_data.py<br/>prompt + input + gold Decision and Draft"]
    G --> H["train_sft.jsonl"]
    E --> I["prepare_training_data.py"]
    I --> J["validation_sft.jsonl<br/>loss measurement only — never trained on"]
    H --> K["train.py"]
    J --> K
    L["lora_config.yaml<br/>base model, rank, alpha, LR, epochs"] --> K
    K --> M["Tinker — LoRA training run"]
    M --> N["training_log.jsonl<br/>train and validation loss per epoch"]
    M --> O["sampler weights<br/>one checkpoint per epoch; epoch 3 is final"]
    F --> P["score_baseline.py — prepare"]
    P --> Q["test_prompts.jsonl<br/>shared best prompt + the 16 test inputs"]
    Q --> R["run_baseline.py<br/>base Qwen3-8B"]
    Q --> S["run_finetuned.py<br/>fine-tuned sampler weights"]
    Q --> T["run_frontier_gemini.py<br/>frontier model, same prompt"]
    O --> S
    R --> U["results files, one per model"]
    S --> U
    T --> U
    U --> V["score_baseline.py — score<br/>decisions by exact match;<br/>rubric worksheet for the drafts"]
    V --> W["scorecard<br/>all three models, per-type scores,<br/>verdicts against S1–S5"]
```

## Diagram 2 — the training script, step by step

```mermaid
flowchart TD
    A["start: python train.py<br/>(--dry-run for the 8-example check)"] --> B["read the locked values from lora_config.yaml<br/>Qwen3-8B, rank 16, alpha 32, LR 1e-4, batch 8"]
    B --> C["load the training data<br/>full run: train_sft.jsonl, 68 examples<br/>dry run: 8-example slice"]
    C --> D["pre-flight check<br/>tokenise everything, count tokens,<br/>estimate cost, assert under the $1 cap"]
    D --> E["create the LoRA training client on Tinker<br/>create_lora_training_client, rank 16"]
    E --> F{"dry run?"}
    F -- yes --> G["3 steps on the single batch of 8<br/>forward_backward + optim_step each step"]
    G --> H["save the checkpoint, then sample one<br/>training prompt to check the answer format"]
    H --> Z["end"]
    F -- no --> I["epoch loop: epochs 1 to 3"]
    I --> J["shuffle the 68 examples<br/>seed 1234 + epoch, so each epoch differs"]
    J --> K["split into batches of 8 — 9 batches"]
    K --> L["for each batch: build supervised examples<br/>renderer puts loss on the assistant turn only"]
    L --> M["forward_backward<br/>compute the loss and gradients"]
    M --> N["optim_step<br/>one Adam update — one batch, one step"]
    N --> O{"more batches?"}
    O -- yes --> L
    O -- no --> P["validation pass<br/>forward only over validation_sft.jsonl;<br/>mean loss — the model never trains on it"]
    P --> Q["append the epoch's train and<br/>validation loss to training_log.jsonl"]
    Q --> R["save_state: resumable checkpoint<br/>save_weights_for_sampler: sampling weights"]
    R --> S{"more epochs?"}
    S -- yes --> I
    S -- no --> T["report the final sampler path<br/>epoch-3 weights — validation loss fell<br/>at every epoch, so no earlier checkpoint is used"]
    T --> Z
```
