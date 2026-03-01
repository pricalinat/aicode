# 图1: 图神经网络概述

```mermaid
flowchart LR
    subgraph "输入"
        I1[图结构]
        I2[节点特征]
    end
    
    subgraph "GNN层"
        G1[聚合邻居信息]
        G2[更新节点表示]
    end
    
    I1 --> G1
    I2 --> G1
    G1 --> G2
    
    G2 --> O1[输出<br/>节点/边/图表示]
    
    style I1 fill:#e3f2fd
    style G1 fill:#fff3e0
    style O1 fill:#c8e6c9
```

**说明**: 图神经网络通过聚合邻居节点信息来更新节点表示，学习图结构中的模式。

---

# 图2: GCN卷积操作

```mermaid
flowchart LR
    subgraph "GCN公式"
        GC1[H⁽ˡ⁺¹⁾ = σ(D̃⁻¹/²ÃD̃⁻¹/² H⁽ˡ⁾ W⁽ˣ⁾]
    end
    
    GC1 --> GC2[邻接矩阵归一化]
    GC2 --> GC3[特征变换]
    GC3 --> GC4[非线性激活]
    
    style GC1 fill:#e3f2fd
    style GC4 fill:#c8e6c9
```

**说明**: 图卷积网络GCN通过归一化邻接矩阵实现卷积操作，结合特征变换和非线性激活。

---

# 图3: GCN层间传播

```mermaid
flowchart LR
    subgraph "单层传播"
        P1[节点i的特征hᵢ⁽ˡ⁾]
        P2[聚合邻居特征]
        P3[拼接并变换]
        P4[得到hᵢ⁽ˡ⁺¹⁾]
    end
    
    P1 --> P2 --> P3 --> P4
    
    style P1 fill:#e3f2fd
    style P2 fill:#fff3e0
```

**说明**: GCN每层将节点自身特征与邻居特征聚合，经过变换得到新的节点表示。

---

# 图4: 图注意力网络(GAT)

```mermaid
flowchart LR
    subgraph "注意力机制"
        A1[计算注意力系数]
        A1 --> A2[αᵢⱼ = softmax(LeakyReLU(aᵀ[Whᵢ||Whⱼ]))]
    end
    
    A2 --> A3[加权聚合]
    A3 --> A4[hᵢ⁽ˡ⁺¹⁾ = σ(ΣⱼαᵢⱼWhⱽ⁽ˡ⁾)]
    
    style A1 fill:#fff3e0
    style A4 fill:#c8e6c9
```

**说明**: GAT引入注意力机制，让节点自适应地决定对不同邻居的注意力权重。

---

# 图5: 多头注意力GAT

```mermaid
flowchart LR
    subgraph "K个注意力头"
        H1[Head₁]
        H2[Head₂]
        H3[Headₖ]
    end
    
    H1 --> H4[拼接]
    H2 --> H4
    H3 --> H4
    H4 --> H5[或平均]
    
    style H1 fill:#e3f2fd
    style H4 fill:#fff3e0
```

**说明**: GAT使用多头注意力增加模型稳定性，类似Multi-Head Attention。

---

# 图6: GraphSAGE采样聚合

```mermaid
flowchart LR
    subgraph "采样"
        S1[随机采样<br/>固定数量邻居]
    end
    
    subgraph "聚合"
        S2[Mean聚合]
        S3[LSTM聚合]
        S4[Pooling聚合]
    end
    
    S1 --> S2
    S2 --> S5[生成新表示]
    
    style S1 fill:#e3f2fd
    style S5 fill:#c8e6c9
```

**说明**: GraphSAGE通过采样和多种聚合函数，支持归纳学习，能够处理新节点。

---

# 图7: GCN vs GAT对比

```mermaid
flowchart LR
    subgraph "GCN"
        G1[固定权重]
        G1 --> G2[确定性聚合]
    end
    
    subgraph "GAT"
        G3[自适应权重]
        G3 --> G4[注意力聚合]
    end
    
    style G1 fill:#e3f2fd
    style G3 fill:#fff3e0
```

**说明**: GCN使用固定的图结构权重，GAT学习动态的注意力权重，更灵活。

---

# 图8: 消息传递神经网络

```mermaid
flowchart LR
    subgraph "消息传递"
        M1[节点发送消息<br/>mᵢⱼ = f(hᵢ, hⱼ, eᵢⱼ)]
    end
    
    M1 --> M2[消息聚合]
    M2 --> M3[节点更新<br/>hᵢ' = g(hᵢ, Σmᵢⱼ)]
    
    style M1 fill:#fff3e0
    style M3 fill:#c8e6c9
```

**说明**: 消息传递网络框架包含消息生成、聚合和更新三个步骤，是GNN的通用框架。

---

# 图9: 图 pooling 操作

```mermaid
flowchart LR
    subgraph "节点→图"
        PL1[Readout函数]
        PL1 --> PL2[全局平均池化]
        PL1 --> PL3[全局最大池化]
        PL1 --> PL4[注意力池化]
    end
    
    PL2 --> PL5[图级别表示]
    PL3 --> PL5
    PL4 --> PL5
    
    style PL1 fill:#fff3e0
    style PL5 fill:#c8e6c9
```

**说明**: 图Pooling将节点级别表示聚合成图级别表示，用于图分类任务。

---

# 图10: GNN应用场景

```mermaid
flowchart TD
    A[GNN应用] --> B[节点分类]
    A --> C[边预测]
    A --> D[图分类]
    A --> E[知识图谱]
    
    B --> B1[社交网络<br/>推荐系统]
    C --> C1[药物分子<br/>相互作用]
    D --> D1[蛋白质功能<br/>材料分类]
    
    style A fill:#e1f5fe
    style E fill:#81d4fa
```

**说明**: GNN广泛用于节点分类、边预测、图分类和知识图谱等任务。
