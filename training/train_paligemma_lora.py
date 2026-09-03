import os
import torch
import matplotlib.pyplot as plt
from datasets import load_dataset
from transformers import (
    PaliGemmaProcessor,
    PaliGemmaForConditionalGeneration,
    BitsAndBytesConfig,
    TrainingArguments,
    Trainer,
)
from peft import get_peft_model, LoraConfig, prepare_model_for_kbit_training

def main():
    print("Initializing PaliGemma QLoRA Fine-Tuning Pipeline...")
    model_id = "google/paligemma-3b-pt-224"
    adapter_path = "./models/paligemma_rs_lora/"
    os.makedirs(os.path.dirname(adapter_path), exist_ok=True)

    print("1. Loading Processor...")
    processor = PaliGemmaProcessor.from_pretrained(model_id)

    print("2. Configuring 4-bit NF4 Quantization...")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    print(f"3. Loading Base Model: {model_id}...")
    model = PaliGemmaForConditionalGeneration.from_pretrained(
        model_id,
        quantization_config=bnb_config,
        device_map="auto"
    )
    model = prepare_model_for_kbit_training(model)

    print("4. Applying LoRA Adapters...")
    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "v_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM"
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    print("5. Loading Remote Sensing Dataset (arampacha/rsicd)...")
    dataset = load_dataset("arampacha/rsicd", split="train[:10%]")

    def collate_fn(examples):
        images = [example["image"].convert("RGB") for example in examples]
        texts = ["caption: " + example["captions"][0] for example in examples]
        tokens = processor(text=texts, images=images, return_tensors="pt", padding="longest", truncation=True)
        labels = tokens["input_ids"].clone()
        labels[labels == processor.tokenizer.pad_token_id] = -100
        tokens["labels"] = labels
        return tokens

    print("6. Initializing Trainer...")
    training_args = TrainingArguments(
        output_dir="./paligemma_results",
        per_device_train_batch_size=2,
        gradient_accumulation_steps=8,
        learning_rate=2e-4,
        warmup_ratio=0.05,
        max_steps=300,
        logging_steps=10,
        save_steps=100,
        optim="paged_adamw_8bit",
        fp16=True,
        remove_unused_columns=False,
        report_to="none"
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        data_collator=collate_fn,
    )

    print("7. Starting Training Loop...")
    trainer.train()

    print(f"8. Saving trained PEFT adapter to {adapter_path}...")
    model.save_pretrained(adapter_path)
    processor.save_pretrained(adapter_path)

    print("9. Generating Training Convergence Plot...")
    history = trainer.state.log_history
    steps = [h["step"] for h in history if "loss" in h]
    loss = [h["loss"] for h in history if "loss" in h]
    
    if loss:
        plt.figure(figsize=(8, 5))
        plt.plot(steps, loss, label="Training Loss", color="#2563EB", linewidth=2)
        plt.title("QLoRA Convergence on Remote Sensing Dataset")
        plt.xlabel("Steps")
        plt.ylabel("Loss")
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.legend()
        plt.savefig("training_loss.png", dpi=300, bbox_inches="tight")
        print("Saved training_loss.png successfully.")

if __name__ == "__main__":
    main()
