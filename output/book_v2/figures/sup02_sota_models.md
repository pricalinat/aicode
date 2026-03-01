# Supplementary: SOTA Model Performance Comparison

## Diagram 1: LLM Performance Evolution
```mermaid
graph TD
    Year[Year] --> 2020[2020 GPT-3]
    Year --> 2021[2021 Codex]
    Year --> 2022[2022 ChatGPT]
    Year --> 2023[2023 GPT-4]
    Year --> 2024[2024 GPT-4 Turbo]
```

## Diagram 2: Benchmark Categories
```mermaid
graph TD
    Benchmarks --> MMLU[MMLU]
    Benchmarks --> HumanEval[HumanEval]
    Benchmarks --> MBPP[MBPP]
    Benchmarks --> MATH[MATH]
    Benchmarks --> BBH[BBH]
```

## Diagram 3: Vision Models Timeline
```mermaid
graph TD
    ResNet[ResNet] --> EfficientNet[EfficientNet]
    EfficientNet --> ViT[ViT]
    ViT --> CLIP[CLIP]
    CLIP --> SAM[SAM]
    SAM --> DALL-E[DALL-E]
```

## Diagram 4: NLP Models
```mermaid
graph LR
    BERT[BERT] --> RoBERTa[RoBERTa]
    RoBERTa --> T5[T5]
    T5 --> GPT[GPT Series]
    GPT --> Claude[Claude]
    Claude --> Gemini[Gemini]
```

## Diagram 5: Multimodal Models
```mermaid
graph TD
    GPT4V[GPT-4V] --> ClaudeV[Claude V]
    ClaudeV --> GeminiPro[Gemini Pro]
    GeminiPro --> GPT4O[GPT-4O]
```

## Diagram 6: Code Generation
```mermaid
graph LR
    GPT3[GPT-3] --> Codex[Codex]
    Codex --> GPT4[GPT-4]
    GPT4 --> Claude3[Claude 3]
    Claude3 --> GPT4Turbo[GPT-4 Turbo]
```

## Diagram 7: Parameter Efficiency
```mermaid
graph TD
    Dense[Dense] --> 100[100% Params]
    MoE[MoE] --> 20[~20% Active]
    LoRA[LoRA] --> 1[~1% Params]
    Quant[Quantization] --> 25[~25% Size]
```

## Diagram 8: Training Compute
```mermaid
graph TD
    GPT2[GPT-2] --> Small[~1 M$]
    GPT3[GPT-3] --> Medium[~4 M$]
    GPT4[GPT-4] --> Large[~100 M$]
    GPT4O[GPT-4O] --> Huge[~100+ M$]
```

## Diagram 9: Context Length Evolution
```mermaid
graph TD
    GPT3[GPT-3] --> 2K[2K tokens]
    GPT3.5[GPT-3.5] --> 4K[4K tokens]
    GPT4[GPT-4] --> 32K[32K tokens]
    Claude2[Claude 2] --> 100K[100K tokens]
    Gemini[Gemini] --> 1M[1M tokens]
```

## Diagram 10: Inference Speed
```mermaid
graph LR
    Large[Large Model] --> Slow[~100 tok/s]
    Medium[Medium Model] --> Medium[~500 tok/s]
    Small[Small Model] --> Fast[~2000 tok/s]
    Quantized[Quantized] --> VeryFast[~4000 tok/s]
```

## Diagram 11: Cost per 1M Tokens
```mermaid
graph TD
    GPT4[GPT-4] --> 30[Input $30]
    GPT35[GPT-3.5] --> 2[Input $2]
    Claude[Claude 3] --> 15[Input $15]
    Gemini[Gemini Pro] --> 1.25[Input $1.25]
```

## Diagram 12: Accuracy vs Cost
```mermaid
graph TD
    HighAcc[High Accuracy] --> HighCost[High Cost]
    LowCost[Low Cost] --> LowerAcc[Lower Accuracy]
    Tradeoff[Trade-off Exists] --> Optimal[Find Optimal]
```

## Diagram 13: Open vs Closed Source
```mermaid
graph TD
    Open[LLaMA] --> Good[Good Performance]
    Open --> Control[Full Control]
    Closed[GPT-4] --> Best[Best Performance]
    Closed --> Convenience[Convenience]
```

## Diagram 14: Fine-tuning Methods
```mermaid
graph TD
    Full[Full Fine-tune] --> Best[Best Quality]
    LoRA[LoRA] --> Good[Good Quality]
    RLHF[RLHF] --> Aligned[Well Aligned]
    DPO[DPO] --> Simple[Simple]
```

## Diagram 15: Model Selection Guide
```mermaid
graph TD
    Need[Use Case] --> Quality{Quality Priority?}
    Quality -->|High| Closed[Closed Source]
    Quality -->|Medium| Open[Open Source]
    Need --> Cost{Cost Priority?}
    Cost -->|High| Small[Small Model]
    Cost -->|Low| Large[Large Model]
```
