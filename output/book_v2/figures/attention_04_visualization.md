# 图1: 注意力热力图

```mermaid
flowchart LR
    subgraph "热力图表示"
        H1[行: Query词]
        H2[列: Key词]
        H3[颜色: 注意力权重]
    end
    
    H3 --> H4[深色=高权重]
    H4 --> H5[浅色=低权重]
    
    style H1 fill:#e3f2fd
    style H4 fill:#c8e6c9
```

**说明**: 注意力热力图直观展示词与词之间的关联强度，颜色越深表示关注度越高。

---

# 图2: 注意力权重分布

```mermaid
flowchart LR
    subgraph "稀疏注意力"
        S1[少数词高权重]
        S1 --> S2[聚焦关系]
    end
    
    subgraph "稠密注意力"
        D1[权重分散]
        D1 --> D2[广泛关联]
    end
    
    style S1 fill:#c8e6c9
    style D1 fill:#fff3e0
```

**说明**: 不同层的注意力分布不同，浅层更稀疏，深层更稠密。

---

# 图3: 多头注意力可视化对比

```mermaid
flowchart LR
    subgraph "头1: 语法结构"
        G1[关注位置关系]
    end
    
    subgraph "头2: 语义关联"
        S1[关注语义相似]
    end
    
    subgraph "头3: 指代消解"
        R1[关注指代词]
    end
    
    style G1 fill:#e3f2fd
    style S1 fill:#f3e5f5
    style R1 fill:#fff3e0
```

**说明**: 不同注意力头学习不同的模式，可视化可以观察头的分工。

---

# 图4: 层级间注意力变化

```mermaid
flowchart LR
    subgraph "低层"
        L1[局部关注<br/>相邻词关系]
    end
    
    subgraph "中层"
        L2[短语级别<br/>局部语法]
    end
    
    subgraph "高层"
        L3[全局语义<br/>句子级别]
    end
    
    L1 --> L4[注意力范围逐渐扩大]
    L2 --> L4
    L3 --> L4
    
    style L1 fill:#e3f2fd
    style L3 fill:#c8e6c9
```

**说明**: 从底层到高层，注意力从关注局部逐步扩展到全局上下文。

---

# 图5: 注意力模式类型

```mermaid
flowchart TD
    A[注意力模式] --> B[局部邻接]
    A --> C[全局]
    A --> D[对角线]
    A --> E[稀疏/块状]
    
    B --> B1[CNN类似<br/>局部关系]
    C --> C1[每个词关注所有词]
    D --> D1[位置关系<br/>位置编码效果]
    E --> E1[效率优化<br/>长序列]
    
    style A fill:#e1f5fe
    style C1 fill:#81d4fa
```

**说明**: Transformer展现出多种注意力模式，包括局部、全局、对角线和稀疏模式。
