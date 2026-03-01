# 图1: 全参数微调

```mermaid
flowchart LR
    subgraph "预训练模型"
        PT[BERT/GPT<br/>参数θ]
    end
    
    subgraph "微调阶段"
        FT1[下游数据]
        FT1 --> FT2[更新全部参数<br/>θ → θ']
    end
    
    PT --> FT2
    
    style PT fill:#e3f2fd
    style FT2 fill:#c8e6c9
```

**说明**: 全参数微调使用下游任务数据更新所有模型参数，效果最好但资源消耗大。

---

# 图2: LoRA微调

```mermaid
flowchart LR
    subgraph "核心思想"
        L1[冻结原参数]
        L1 --> L2[添加低秩适配器]
    end
    
    subgraph "参数更新"
        L3[W = W₀ + ΔW]
        L4[ΔW = A × B<br/>r << d]
    end
    
    L3 --> L5[大幅减少<br/>可训练参数]
    
    style L1 fill:#fff3e0
    style L5 fill:#c8e6c9
```

**说明**: LoRA通过添加低秩矩阵学习参数增量，显著减少可训练参数量和显存需求。

---

# 图3: Adapter微调

```mermaid
flowchart LR
    subgraph "Transformer层"
        T1[FFN] --> A1[Adapter]
        A1 --> T2[FFN]
    end
    
    subgraph "Adapter结构"
        A2[Down Project]
        A2 --> A3[激活函数]
        A3 --> A4[Up Project]
    end
    
    T1 --> A2
    
    style A1 fill:#ffcdd2
    style A4 fill:#c8e6c9
```

**说明**: Adapter在Transformer每层插入小的瓶颈网络，只训练Adapter参数，保持原模型不变。

---

# 图4: 提示微调(Prompt Tuning)

```mermaid
flowchart LR
    subgraph "连续提示"
        P1[可学习向量<br/>[P]₁, [P]₂, ..., [Pₖ]
    end
    
    subgraph "与输入拼接"
        P2[[P][P][P][The][cat]]
    end
    
    P2 --> P3[冻结模型<br/>只训练提示]
    
    style P1 fill:#e3f2fd
    style P3 fill:#c8e6c9
```

**说明**: Prompt Tuning使用可学习的连续提示向量，只需训练少量提示参数。

---

# 图5: 微调策略对比

```mermaid
flowchart TD
    A[微调策略] --> B[全参数]
    A --> C[LoRA]
    A --> D[Adapter]
    A --> E[Prefix Tuning]
    
    B --> B1[效果好<br/>资源需求高]
    C --> C1[效果接近<br/>资源需求低]
    D --> D2[效果稳定<br/>推理略慢]
    E --> E1[轻量<br/>适合少样本]
    
    style A fill:#e1f5fe
    style B1 fill:#81d4fa
```

**说明**: 不同微调策略在效果和效率间权衡，选择取决于任务规模和计算资源。
