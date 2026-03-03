# 图2.2：自注意力机制计算流程

```mermaid
graph TD
    subgraph "Step 1: Q K V生成"
        Token[Token: "cat"] --> Q[Query q_cat]
        Token --> K[Key k_cat]
        Token --> V[Value v_cat]
    end
    
    subgraph "Step 2: 注意力分数"
        Q --> Attn[Attention Score<br/>Q × K^T / √d_k]
        K --> Attn
    end
    
    subgraph "Step 3: Softmax归一化"
        Attn --> Softmax[Softmax<br/>注意力权重]
    end
    
    subgraph "Step 4: 加权求和"
        Softmax --> Output[Output<br/>Σ Attention × V]
    end
```

标题: 自注意力机制计算流程
说明: 展示自注意力的四步计算过程：QKV生成、注意力分数计算、Softmax归一化、加权求和输出
