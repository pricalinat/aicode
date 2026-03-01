# 图1: 网格搜索

```mermaid
flowchart LR
    subgraph "Grid Search"
        G1[穷举所有组合]
    end
    
    G1 --> G2[学习率: 0.01, 0.1, 1.0]
    G2 --> G3[批大小: 16, 32, 64]
    G2 --> G4[隐藏层: 64, 128, 256]
    
    G4 --> G5[共27种组合]
    
    style G1 fill:#e3f2fd
    style G5 fill:#c8e6c9
```

**说明**: 网格搜索穷举所有参数组合，简单全面但计算成本高，适合参数空间不大时。

---

# 图2: 随机搜索

```mermaid
flowchart LR
    subgraph "Random Search"
        R1[随机采样组合]
    end
    
    R1 --> R2[高效发现<br/>重要参数]
    R2 --> R3[收敛快]
    
    style R1 fill:#e3f2fd
    style R3 fill:#c8e6c9
```

**说明**: 随机搜索在参数空间随机采样，往往比网格搜索更高效，尤其是高维空间。

---

# 图3: 贝叶斯优化

```mermaid
flowchart LR
    subgraph "Bayesian Optimization"
        B1[建立代理模型]
        B1 --> B2[预测参数效果]
        B2 --> B3[采集函数<br/>选择下一个点]
    end
    
    B3 --> B4[更少迭代<br/>找到最优]
    
    style B1 fill:#fff3e0
    style B4 fill:#c8e6c9
```

**说明**: 贝叶斯优化利用历史结果建模参数-效果关系，智能选择下一个评估点，效率最高。

---

# 图4: 学习率调度

```mermaid
flowchart LR
    subgraph "LR Schedule"
        L1[Step Decay]
        L2[Cosine Annealing]
        L3[Reduce on Plateau]
    end
    
    L1 --> L4[固定间隔衰减]
    L2 --> L5[余弦曲线变化]
    L3 --> L6[验证集不提升时]
    
    style L1 fill:#e3f2fd
    style L5 fill:#fff3e0
```

**说明**: 学习率调度动态调整学习率，常用方法有按步衰减、余弦退火和早停策略。

---

# 图5: 超参数搜索策略选择

```mermaid
flowchart TD
    A[参数空间] --> B[小]
    A --> C[大/复杂]
    
    B --> D[网格搜索<br/>全面]
    C --> E[随机搜索<br/>高效]
    C --> F[贝叶斯优化<br/>智能]
    
    style A fill:#e1f5fe
    style D fill:#81d4fa
    style F fill:#4fc3f7
```

**说明**: 根据参数空间大小选择搜索策略，网格搜索全面，随机搜索高效，贝叶斯最智能。
