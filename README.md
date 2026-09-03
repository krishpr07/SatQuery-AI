
### Remote-Sensing Domain Adaptation (PEFT / QLoRA)

To satisfy the mandatory hackathon requirement for domain adaptation on visual/vision-language models, we have included a complete PEFT (Parameter-Efficient Fine-Tuning) pipeline in the /training directory.

- **Base Architecture**: PaliGemma-3B (google/paligemma-3b-pt-224)
- **Quantization**: 4-bit NormalFloat (NF4) via itsandbytes
- **LoRA Configuration**: Rank =16, lpha=32, applied to q_proj and _proj attention modules.
- **Target Dataset**: Remote Sensing Image Captioning Dataset (rampacha/rsicd).
- **Optimization**: Paged AdamW 8-bit, lr=2e-4, effective batch size = 16.

#### How to run the adaptation pipeline:
1. **Local Pipeline**: Run python training/train_paligemma_lora.py (Requires 12GB+ VRAM).
2. **Cloud Environment**: Import 	raining/fine_tune_colab.ipynb into Google Colab (Optimized for Free T4 GPU instances).
3. **Inference**: Use python training/inference_lora.py --image sample.jpg to evaluate the adapted LoRA weights against raw satellite imagery.
