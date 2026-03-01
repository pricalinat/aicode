# 图1: Batch Normalization基本原理

```mermaid
flowchart LR
    subgraph "BN操作"
        BN1[输入: x] --> BN2[计算均值μ]
        BN2 --> BN3[计算方差σ²]
        BN3 --> BN4[标准化: x̂ = (x-μ)/√(σ²+ε)]
        BN4 --> BN5[缩放平移: y = γx̂ + β]
    end
    
    BN5 --> BN6[输出: y]
    BN6 --> BN7[可学习参数γ,β]
    
    style BN1 fill:#e3f2fd
    style BN4 fill:#ffcdd2
    style BN5 fill:#c8e6c9
```

**说明**: Batch Normalization将每层输入标准化到均值为0方差为1，再通过γ、β学习适合的分布。

---

# 图2: 训练与推理的BN

```mermaid
flowchart LR
    subgraph "训练阶段"
        T1[当前batch计算μ,σ] --> T2[移动平均更新全局统计量]
    end
    
    subgraph "推理阶段"
        I1[使用保存的全局统计量] --> I2[标准化]
    end
    
    T2 --> T3[E[x] ≈ μ, Var[x] ≈ σ²]
    I1 --> T3
    
    style T1 fill:#fff3e0
    style I1 fill:#e8f5e9
```

**说明**: 训练时使用batch统计量并更新移动平均，推理时使用预计算的全局统计量。

---

# 图3: BN的作用机制

```mermaid
flowchart TD
    A[内部协变量偏移] --> B[层输入分布变化]
    B --> C[需不断适应新分布]
    C --> D[训练困难收敛慢]
    
    E[Batch Normalization] --> F[稳定输入分布]
    F --> G[加速训练]
    G --> H[允许使用更高学习率]
    H --> I[正则化效果]
    
    style A fill:#ffcdd2
    style E fill:#c8e6c9
    style I fill:#a5d6a7
```

**说明**: BN通过稳定层间输入分布，解决内部协变量偏移问题，加速训练并有正则化效果。

---

# 图4: Layer Normalization

```mermaid
flowchart LR
    subgraph "Batch Norm"
        BN[同一个特征<br/>跨batch归一化]
    end
    
    subgraph "Layer Norm"
        LN[同一个样本<br/>跨特征归一化]
    end
    
    BN --> B1[需足够batch size]
    LN --> L1[RNN/Transformer<br/>常用]
    
    style BN fill:#e3f2fd
    style LN fill:#f3e5f5
```

**说明**: Layer Normalization对单个样本的特征进行归一化，不依赖batch大小，适合RNN和Transformer。

---

# 图5: 归一化方法对比

```mermaid
flowchart TD
    A[归一化方法] --> B[Batch Norm]
    A --> C[Layer Norm]
    A --> D[Instance Norm]
    A --> E[Group Norm]
    
    B --> B1[CV常用]
    C --> C1[NLP/RNN/Transformer]
    D --> D1[风格迁移]
    E --> E1[小batch友好]
    
    style A fill:#e1f5fe
    style B1 fill:#81d4fa
    style C1 fill:#4fc3f7
    style E1 fill:#29b6f6
```

**说明**: 不同归一化方法适用于不同场景，CV常用BN，NLP用LN，Group Norm折中处理batch依赖问题。
