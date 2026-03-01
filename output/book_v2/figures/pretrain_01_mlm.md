# 图1: MLM任务基本原理

```mermaid
flowchart LR
    subgraph "输入句子"
        I1[The [MASK] ate the fish]
    end
    
    subgraph "MLM任务"
        M1[随机遮盖15%词]
        M1 --> M2[预测遮盖词]
    end
    
    subgraph "训练目标"
        O1[最大化P(cat|I)]
    end
    
    I1 --> M1 --> O1
    
    style I1 fill:#e3f2fd
    style M1 fill:#fff3e0
    style O1 fill:#c8e6c9
```

**说明**: Masked Language Modeling随机遮盖输入中的词，让模型预测被遮盖的词。

---

# 图2: BERT中的MLM实现

```mermaid
flowchart LR
    subgraph "遮盖策略"
        B1[80%: [MASK]标记]
        B2[10%: 随机词替换]
        B3[10%: 保持原词]
    end
    
    B1 --> B4[训练目标]
    B2 --> B4
    B3 --> B4
    B4 --> B5[预测原始词
    
    style B1 fill:#ffcdd2
    style B4 fill:#c8e6c9
```

**说明**: BERT使用改进的MLM策略，80%用[MASK]替换，10%随机替换，10%保持不变，增加鲁棒性。

---

# 图3: MLM训练过程

```mermaid
flowchart LR
    subgraph "前向传播"
        F1[输入序列] --> F2[Transformer编码]
        F2 --> F3[MLM输出层]
    end
    
    subgraph "损失计算"
        L1[计算遮盖位置<br/>交叉熵损失]
    end
    
    subgraph "反向传播"
        R1[更新Transformer参数]
    end
    
    F3 --> L1 --> R1
    
    style F1 fill:#e3f2fd
    style L1 fill:#fff3e0
```

**说明**: MLM训练时只计算被遮盖位置的损失，通过反向传播更新模型参数。

---

# 图4: MLM的优缺点

```mermaid
flowchart LR
    subgraph "优点"
        A1[双向上下文建模]
        A1 --> A2[理解力强]
        A2 --> A3[适合理解任务]
    end
    
    subgraph "缺点"
        D1[预训练-微调差异]
        D1 --> D2[15%遮盖率限制]
        D2 --> D3[训练效率较低]
    end
    
    style A1 fill:#c8e6c9
    style D1 fill:#ffcdd2
```

**说明**: MLM的双向性是其核心优势，但预训练和微调阶段的不一致是需要注意的问题。

---

# 图5: MLM vs 其他预训练任务

```mermaid
flowchart TD
    A[预训练任务] --> B[MLM]
    A --> C[LM]
    A --> D[DAE]
    
    B --> B1[BERT<br/>双向]
    C --> C1[GPT<br/>自回归]
    D --> D2[降噪自编码<br/>部分损坏]
    
    B1 --> E[适合理解]
    C1 --> F[适合生成]
    
    style A fill:#e1f5fe
    style B1 fill:#81d4fa
    style C1 fill:#4fc3f7
```

**说明**: MLM与自回归语言建模不同，BERT采用MLM实现双向编码。
