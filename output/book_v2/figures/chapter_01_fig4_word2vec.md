# 图1.4：Word2Vec模型架构对比

CBOW (Continuous Bag-of-Words):
```
上下文: [The, cat, over, the, river]
         ↓    ↓    ↓    ↓    ↓
      投影层 (求平均)
         ↓
    中间层 (隐层)
         ↓
    输出层 → 预测中心词: "jumped"
```

Skip-gram:
```
中心词: "jumped"
         ↓
    中间层 (隐层)
         ↓
    输出层 → 预测上下文: [The, cat, over, the, river]
```

数学目标:
- CBOW: J(θ) = (1/T) Σ log P(w_t | w_{t-k}, ..., w_{t+k})
- Skip-gram: J(θ) = (1/T) Σ Σ log P(w_{t+j} | w_t)
