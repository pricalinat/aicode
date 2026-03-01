# 图1: Multi-Head Attention架构

```mermaid
flowchart LR
    subgraph "输入X"
        X1[h₀]
    end
    
    subgraph "多头注意力"
        H1[Head₁]
        H2[Head₂]
        H3[Headₕ]
    end
    
    subgraph "输出"
        Y1[拼接<br/>Concat]
        Y2[线性变换<br/>W⁰]
    end
    
    X1 --> H1
    X1 --> H2
    X1 --> H3
    
    H1 --> Y1
    H2 --> Y1
    H3 --> Y1
    
    Y1 --> Y2
    
    style X1 fill:#e3f2fd
    style Y2 fill:#c8e6c9
```

**说明**: Multi-Head Attention并行运行多个注意力头，捕捉不同类型的语义关系。

---

# 图2: 单头注意力计算

```mermaid
flowchart LR
    subgraph "第i个头"
        HI1[Qᵢ = XWᵢᴼ] --> HI2[Kᵢ = XWᵢᴷ]
        HI2 --> HI3[Vᵢ = XWᵢⱽ]
        HI3 --> HI4[Attention(Qᵢ,Kᵢ,Vᵢ)]
    end
    
    HI4 --> HI5[输出Zᵢ]
    
    style HI1 fill:#fff3e0
    style HI4 fill:#c8e6c9
```

**说明**: 每个头使用独立的W_Q、W_K、W_V参数，学习不同的注意力模式。

---

# 图3: 多头注意力的优势

```mermaid
flowchart LR
    subgraph "不同头捕获"
        A1[头1: 语法关系<br/>主语-谓语]
        A2[头2: 语义关系<br/>同义词]
        A3[头3: 位置关系<br/>邻近词]
        A4[头4: 指代关系<br/>代词消解]
    end
    
    A1 --> A5[多样化特征表示]
    A2 --> A5
    A3 --> A5
    A4 --> A5
    
    style A1 fill:#e3f2fd
    style A5 fill:#c8e6c9
```

**说明**: 不同注意力头可以学习捕获不同类型的语义关系，提升模型表达能力。

---

# 图4: 头数选择与性能

```mermaid
flowchart TD
    A[选择头数h] --> B{任务需求}
    B -->|小数据集| C[h=4~8]
    B -->|标准设置| D[h=8~12]
    B -->|大模型| E[h=16~32]
    
    C --> F[计算效率]
    D --> F
    E --> F
    
    F --> G[Attention(Q,K,V) = Concat(head₁...headₕ)W⁰]
    
    style A fill:#e1f5fe
    style G fill:#81d4fa
```

**说明**: 头数根据任务复杂度和计算资源选择，通常8-12个头是较好的平衡点。

---

# 图5: 多头注意力在Transformer中的应用

```mermaid
flowchart LR
    subgraph "Encoder"
        EN1[Multi-Head Attention<br/>自注意力]
    end
    
    subgraph "Decoder"
        DE1[Masked Multi-Head<br/>自注意力]
        DE2[Cross-Attention<br/>编码器-解码器]
    end
    
    EN1 --> DE2
    
    style EN1 fill:#e3f2fd
    style DE1 fill:#f3e5f5
    style DE2 fill:#fff3e0
```

**说明**: Transformer中Encoder使用自注意力，Decoder同时使用自注意力和交叉注意力。
