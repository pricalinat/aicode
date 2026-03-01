# 图1.3：BERT预训练模型架构

```
输入层:
[CLS] The [MASK] is [MASK] [SEP] A [MASK] example [SEP]

         ↓           ↓           ↓           ↓           ↓
      Token1    Token2      Token3      Token4     Token5

Transformer Encoder Stack (12 layers for BERT-Base):
┌─────────────────────────────────────────────────────┐
│  Layer 1: Multi-Head Self-Attention + FFN         │
│  Layer 2: Multi-Head Self-Attention + FFN         │
│  ...                                               │
│  Layer 12: Multi-Head Self-Attention + FFN        │
└─────────────────────────────────────────────────────┘
         ↓           ↓           ↓           ↓           ↓
      [C]         [T1]        [T2]        [T3]        [T4]

输出层:
- [C] 用于分类任务 (Next Sentence Prediction)
- [Ti] 用于 token 级别预测 (Masked LM)
```
