# 图1: 集成学习概述

```mermaid
flowchart LR
    subgraph "集成思想"
        E1[多个模型]
    end
    
    E1 --> E2[各自预测]
    E2 --> E3[投票/平均]
    E3 --> E4[最终结果<br/>优于单模型]
    
    style E1 fill:#e3f2fd
    style E4 fill:#c8e6c9
```

**说明**: 集成学习通过组合多个模型提升整体性能，是Kaggle等竞赛的常用技巧。

---

# 图2: Bagging

```mermaid
flowchart LR
    subgraph "Bagging"
        B1[Bootstrap采样]
    end
    
    B1 --> B2[训练多个模型]
    B2 --> B3[独立预测]
    B3 --> B4[投票/平均]
    
    style B1 fill:#fff3e0
    style B4 fill:#c8e6c9
```

**说明**: Bagging通过Bootstrap有放回采样训练多个模型，降低方差，适合不稳定模型如决策树。

---

# 图3: Random Forest

```mermaid
flowchart LR
    subgraph "随机森林"
        RF1[Bagging + 特征随机]
    end
    
    RF1 --> RF2[每棵树只看到<br/>部分特征]
    RF2 --> RF3[高度多样化]
    
    style RF1 fill:#e3f2fd
    style RF3 fill:#c8e6c9
```

**说明**: Random Forest是Bagging的扩展，随机选择特征子集，增加模型多样性。

---

# 图4: Boosting

```mermaid
flowchart LR
    subgraph "Boosting"
        BO1[串行训练]
    end
    
    BO1 --> BO2[每个模型<br/>纠正前一个错误]
    BO2 --> BO3[加权组合]
    
    style BO1 fill:#fff3e0
    style BO3 fill:#c8e6c9
```

**说明**: Boosting串行训练模型，每个模型关注前一个的错误，最终加权组合，降低偏差。

---

# 图5: Stacking

```mermaid
flowchart LR
    subgraph "Stacking"
        S1[基模型预测]
    end
    
    S1 --> S2[元特征]
    S2 --> S3[元学习器]
    S3 --> S4[最终预测]
    
    style S1 fill:#e3f2fd
    style S4 fill:#c8e6c9
```

**说明**: Stacking使用基模型预测作为元特征，训练元学习器组合，是更高级的集成方法。
