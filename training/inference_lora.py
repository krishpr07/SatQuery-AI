import torch
import argparse
from PIL import Image
from transformers import PaliGemmaProcessor, PaliGemmaForConditionalGeneration
from peft import PeftModel

def generate_caption(image_path, model, processor, device="cuda"):
    """Runs inference using the fine-tuned LoRA model."""
    image = Image.open(image_path).convert("RGB")
    prompt = "caption: "
    
    inputs = processor(text=prompt, images=image, return_tensors="pt").to(device)
    
    with torch.no_grad():
        output = model.generate(**inputs, max_new_tokens=50)
        
    decoded = processor.decode(output[0], skip_special_tokens=True)
    return decoded.replace("caption: ", "").strip()

def main():
    parser = argparse.ArgumentParser(description="Run Inference with PaliGemma LoRA")
    parser.add_argument("--image", type=str, help="Path to input satellite image", required=True)
    args = parser.parse_args()

    model_id = "google/paligemma-3b-pt-224"
    adapter_path = "./models/paligemma_rs_lora/"
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    print(f"Loading base model {model_id} on {device}...")
    base_model = PaliGemmaForConditionalGeneration.from_pretrained(
        model_id,
        device_map="auto",
        torch_dtype=torch.float16 if device == "cuda" else torch.float32
    )
    
    print(f"Loading LoRA adapter from {adapter_path}...")
    try:
        model = PeftModel.from_pretrained(base_model, adapter_path)
    except Exception as e:
        print(f"Warning: Could not load LoRA weights. Ensure training was completed. {e}")
        model = base_model
        
    processor = PaliGemmaProcessor.from_pretrained(model_id)
    
    print(f"\nAnalyzing Image: {args.image}")
    result = generate_caption(args.image, model, processor, device=device)
    
    print("\n" + "="*50)
    print(f"🛰️ Generated Scene Description:\n{result}")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
