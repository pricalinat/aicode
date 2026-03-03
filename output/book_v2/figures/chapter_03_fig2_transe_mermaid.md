# 图3.2：TransE模型原理

```mermaid
graph LR
    subgraph "TransE核心思想"
        H[头实体 h] --> Plus[+]
        R[关系 r] --> Plus
        Plus --> Approx[≈]
        Approx --> T[尾实体 t]
    end
    
    subgraph "得分函数"
        Score[f(h,r,t) = -||h + r - t||₂]
    end
    
    subgraph "示例"
        Ex1[(iPhone15, is_a, 智能手机)]
        Ex1 --> Vec[向量学习]
    end
    
    subgraph "局限性"
        Lim1[1-1关系: 良好]
        Lim2[1-N关系: 可能有问题]
        Lim3[N-1关系: 可能有问题]
    end
```

标题: TransE模型原理
说明: 展示TransE的核心思想h+r≈t，以及得分函数和局限性
