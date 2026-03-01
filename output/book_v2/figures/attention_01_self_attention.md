# 图1: Self-Attention计算流程概述

```mermaid
flowchart LR
    subgraph "输入"
        IN1[词嵌入向量<br/>x₁, x₂, ..., xₙ]
    end
    
    subgraph "计算"
        C1[计算Q、K、V矩阵]
        C2[计算注意力分数]
        C3[加权求和输出]
    end
    
    subgraph "输出"
        OUT1[上下文感知表示<br/>y₁, y₂, ..., yₙ]
    end
    
    IN1 --> C1 --> C2 --> C3 --> OUT1
    
    style IN1 fill:#e3f2fd
    style C2 fill:#fff3e0
    style OUT1 fill:#e8f5e9
```

**说明**: Self-Attention通过计算序列内部元素间的关联，学习上下文相关的表示。

---

# 图2: Q、K、V矩阵计算

```mermaid
flowchart LR
    subgraph "线性变换"
        Q1[x₁] --> Q2[W_Q × x₁]
        K1[x₁] --> K2[W_K × x₁]
        V1[x₁] --> V2[W_V × x₁]
    end
    
    Q2 --> Q3[Query向量]
    K2 --> K3[Key向量]
    V2 --> V4[Value向量]
    
    style Q1 fill:#e3f2fd
    style K1 fill:#f3e5f5
    style V1 fill:#fff3e0
```

**说明**: 输入向量通过三个独立的线性变换矩阵，生成Query、Key、Value向量。

---

# 图3: 注意力分数计算

```mermaid
flowchart LR
    subgraph "Scaled Dot-Product"
        S1[Q·Kᵀ] --> S2[除以√dₖ]
        S2 --> S3[Softmax]
    end
    
    S3 --> S4[注意力权重<br/>α₁, α₂, ..., αₙ]
    
    S4 --> S5[加权求和]
    S5 --> S6[Attention(Q,K,V) = ΣαᵢVᵢ]
    
    style S1 fill:#ffcdd2
    style S4 fill:#c8e6c9
```

**说明**: 计算Query与Key的相似度，经过缩放和Softmax得到注意力权重，再对Value加权求和。

---

# 图4: 多位置注意力示例

```mermaid
flowchart LR
    subgraph "例子: The cat sat on the mat"
        W1[The] --> A1[注意力分散]
        W2[cat] --> A2[注意力聚焦<br/>语义中心]
        W3[sat] --> A3[注意力转移]
        W4[on] --> A4[注意力较弱]
        W5[the] --> A5[注意力分散]
        W6[mat] --> A6[注意力聚焦<br/>位置相关]
    end
    
    style W2 fill:#c8e6c9
    style W6 fill:#c8e6c9
```

**说明**: Self-Attention可以同时关注序列中的多个位置，动态分配注意力权重。

---

# 图5: 自注意力计算复杂度

```mermaid
flowchart LR
    subgraph "计算复杂度"
        C1[序列长度n] --> C2[n × n 注意力矩阵]
    end
    
    C2 --> C3[O(n² × d)]
    
    subgraph "对比"
        C4[RNN: O(n × d²)]
        C5[CNN: O(n × k × d)]
    end
    
    C3 --> C6[长序列挑战]
    C4 --> C6
    C5 --> C6
    
    style C1 fill:#e3f2fd
    style C6 fill:#ffcdd2
```

**说明**: Self-Attention的计算复杂度是序列长度的平方，在处理长文本时面临计算挑战。
