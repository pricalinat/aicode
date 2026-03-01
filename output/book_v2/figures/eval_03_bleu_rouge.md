# 图1: BLEU评分原理

```mermaid
flowchart LR
    subgraph "BLEU"
        B1[n-gram匹配]
    end
    
    B1 --> B2[Precision计算]
    B2 --> B3[Brevity Penalty<br/>惩罚过短翻译]
    
    B1 --> B4[1-4 gram<br/>综合]
    
    style B1 fill:#e3f2fd
    style B3 fill:#c8e6c9
```

**说明**: BLEU通过n-gram精确率衡量生成文本与参考文本的相似度，加入BP惩罚短句。

---

# 图2: ROUGE评分

```mermaid
flowchart LR
    subgraph "ROUGE变体"
        R1[ROUGE-N: N-gram召回]
        R2[ROUGE-L: 最长公共子序列]
        R3[ROUGE-W: 加权LCS]
    end
    
    R1 --> R4[摘要任务常用]
    R2 --> R4
    R3 --> R4
    
    style R1 fill:#e3f2fd
    style R4 fill:#c8e6c9
```

**说明**: ROUGE是一系列召回率指标，BLEU是精确率，ROUGE更适合评估摘要任务。

---

# 图3: METEOR评分

```mermaid
flowchart LR
    subgraph "METEOR"
        M1[基于词匹配]
        M1 --> M2[考虑词形变化]
        M2 --> M3[同义词支持]
    end
    
    M3 --> M4[F分数计算]
    
    style M1 fill:#e3f2fd
    style M4 fill:#c8e6c9
```

**说明**: METEOR考虑词形变化和同义词，比BLEU更接近人工评估，但对生成文本较长时效果下降。

---

# 图4: BLEU vs ROUGE对比

```mermaid
flowchart LR
    subgraph "BLEU"
        B1[生成质量<br/>精确率导向]
    end
    
    subgraph "ROUGE"
        B2[信息覆盖<br/>召回率导向]
    end
    
    style B1 fill:#e3f2fd
    style B2 fill:#fff3e0
```

**说明**: BLEU适合评估翻译质量(精确率)，ROUGE适合评估摘要(召回率)。

---

# 图5: 生成指标选择

```mermaid
flowchart TD
    A[任务类型] --> B[机器翻译]
    A --> C[文本摘要]
    A --> D[对话生成]
    A --> E[创意写作]
    
    B --> B1[BLEU/METEOR]
    C --> C1[ROUGE]
    D --> D1[人工评估/困惑度]
    E --> E1[多样性/新颖性]
    
    style A fill:#e1f5fe
    style E1 fill:#81d4fa
```

**说明**: 根据任务类型选择合适指标，生成类任务常需结合多个指标和人工评估。
