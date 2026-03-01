# 图2.3：BERT预训练任务

```
输入: [CLS] the man went to [MASK] store [SEP] he bought a [MASK] of milk [SEP]

┌─────────────────────────────────────────────────────────────────────┐
│                      BERT Pre-training                              │
├─────────────────────────────────────────────────────────────────────┤
│  Task 1: Masked Language Model (MLM)                               │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ Input:  [CLS] the man went to [MASK] store [SEP] ...       │  │
│  │                   ↑                                         │  │
│  │              随机掩盖15%的token                              │  │
│  │                                                              │  │
│  │ 预测: [MASK] → "a" (80%) / "the" (10%) / "some"(10%)      │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  Task 2: Next Sentence Prediction (NSP)                           │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ Sentence A: the man went to the store                     │  │
│  │ Sentence B: he bought a gallon of milk                    │  │
│  │                            ↓                                │  │
│  │              Is B the next sentence of A?                  │  │
│  │              Label: IsNext (50%) / NotNext (50%)           │  │
│  └─────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```
