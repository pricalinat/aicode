# 图1.4：BERT预训练模型架构与电商应用

## 核心参数（基于423篇论文分析）

- BERT-Base: L=12, H=768, A=12, 110M参数
- BERT-Large: L=24, H=1024, A=16, 340M参数
- 电商场景常用: BERT-Base（效率与效果平衡）

## 预训练任务

```
输入层:
[CLS] the man went to [MASK] store [SEP] he bought a [MASK] of milk [SEP]

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

## 电商搜索应用（引用论文）

| 论文 | 应用场景 | 方法 |
|------|---------|------|
| 1901.04085 | Passage Re-ranking | BERT微调 |
| 1904.07531 | 电商排序 | BERT排序 |
| 1908.10084 | 语义匹配 | Sentence-BERT |
| 2008.09689 | 电商搜索 | BERT |
| 2010.10442 | BERT+DNN | 模型融合 |
