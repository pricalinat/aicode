# 图1: 消息传递基本流程

```mermaid
flowchart LR
    subgraph "节点A的更新"
        M1[收集邻居消息]
        M2[聚合消息]
        M3[更新自身状态]
    end
    
    M1 --> M2 --> M3
    
    style M1 fill:#e3f2fd
    style M2 fill:#fff3e0
    style M3 fill:#c8e6c9
```

**说明**: 消息传递神经网络中，节点通过聚合邻居消息来更新自己的表示。

---

# 图2: 消息函数设计

```mermaid
flowchart LR
    subgraph "消息计算"
        MSG1[mᵢⱼ = f(hᵢ, hⱼ)]
    end
    
    MSG1 --> MSG2[基于节点特征]
    MSG1 --> MSG3[基于边特征eᵢⱼ]
    
    MSG2 --> MSG4[灵活的消息函数]
    
    style MSG1 fill:#fff3e0
    style MSG4 fill:#c8e6c9
```

**说明**: 消息函数可以设计为只考虑节点特征，或同时加入边特征，增强表达能力。

---

# 图3: 聚合函数类型

```mermaid
flowchart LR
    subgraph "聚合方式"
        A1[Mean: 平均]
        A2[Max: 最大]
        A3[Sum: 求和]
        A4[Attention: 加权]
    end
    
    A1 --> A5[不变序]
    A2 --> A5
    A3 --> A5
    A4 --> A5
    
    style A1 fill:#e3f2fd
    style A4 fill:#fff3e0
```

**说明**: 聚合函数应对节点顺序不变，常用的有Mean、Max、Sum和Attention。

---

# 图4: 多轮消息传递

```mermaid
flowchart LR
    subgraph "多层传播"
        L1[Layer 1: 1跳邻居]
        L2[Layer 2: 2跳邻居]
        L3[Layer 3: 3跳邻居]
    end
    
    L1 --> L2 --> L3
    L3 --> L4[感受野扩大]
    
    style L1 fill:#e3f2fd
    style L2 fill:#fff3e0
    style L3 fill:#f3e5f5
```

**说明**: 多层GNN堆叠使节点能够聚合更远距离的信息，扩大感受野。

---

# 图5: 消息传递效率优化

```mermaid
flowchart LR
    subgraph "优化方法"
        O1[采样邻居]
        O2[边采样]
        O3[小批量训练]
    end
    
    O1 --> O4[处理大图]
    O2 --> O4
    O3 --> O4
    
    style O1 fill:#e3f2fd
    style O4 fill:#c8e6c9
```

**说明**: 对大图进行邻居采样或边采样，使用小批量训练提高计算效率。
