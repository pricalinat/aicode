# 图1: K折交叉验证流程

```mermaid
flowchart LR
    subgraph "数据划分"
        D1[全部数据]
    end
    
    D1 --> K1[分成K份]
    K1 --> K2[训练K次]
    K2 --> K3[每次用K-1份训练<br/>1份验证]
    K3 --> K4[取平均结果]
    
    style D1 fill:#e3f2fd
    style K2 fill:#fff3e0
    style K4 fill:#c8e6c9
```

**说明**: K折交叉验证将数据分成K份，轮流作为验证集，得到更稳定可靠的性能评估。

---

# 图2: 5折交叉验证示例

```mermaid
flowchart LR
    subgraph "5-Fold CV"
        F1[Fold1: 训练4份验证1份]
        F2[Fold2: 训练4份验证1份]
        F3[Fold3: 训练4份验证1份]
        F4[Fold4: 训练4份验证1份]
        F5[Fold5: 训练4份验证1份]
    end
    
    F1 --> AVG[平均5次结果]
    F2 --> AVG
    F3 --> AVG
    F4 --> AVG
    F5 --> AVG
    
    style F1 fill:#e3f2fd
    style AVG fill:#c8e6c9
```

**说明**: 5折交叉验证是常用选择，数据量小时可用10折，数据量大时可减少折数。

---

# 图3: 留一法交叉验证

```mermaid
flowchart LR
    subgraph "Leave-One-Out"
        L1[N个样本]
        L1 --> L2[每次留1个验证]
        L2 --> L3[训练N次]
    end
    
    L3 --> L4[适合小数据集]
    
    style L1 fill:#e3f2fd
    style L4 fill:#c8e6c9
```

**说明**: 留一法每次只留一个样本做验证，训练N次，适合小数据但计算成本高。

---

# 图4: 分层K折

```mermaid
flowchart LR
    subgraph "Stratified K-Fold"
        S1[保持类别比例]
    end
    
    S1 --> S2[每折类别分布<br/>与整体一致]
    S2 --> S3[分类任务推荐]
    
    style S1 fill:#fff3e0
    style S3 fill:#c8e6c9
```

**说明**: 分层K折保证每折中各类别比例与整体一致，适合不平衡分类问题。

---

# 图5: 交叉验证注意事项

```mermaid
flowchart LR
    subgraph "注意事项"
        C1[数据泄露]
        C2[时间序列]
        C3[组别因素]
    end
    
    C1 --> C4[避免验证集<br/>信息泄露]
    C2 --> C5[使用时间序列<br/>划分方法]
    C3 --> C6[按组划分<br/>如用户/患者]
    
    style C1 fill:#ffcdd2
    style C2 fill:#fff3e0
    style C5 fill:#c8e6c9
```

**说明**: 注意数据泄露问题，时间序列和分组数据需要特殊划分方法。
