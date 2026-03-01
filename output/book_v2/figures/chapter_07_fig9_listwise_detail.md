# 图7.9：Listwise评估方法详解

## Listwise流程

```mermaid
flowchart LR
    subgraph 输入
        A[查询Q] --> D[候选列表L]
        B[所有候选] --> D
    end
    
    subgraph 列表级学习
        D --> E[列表评分]
        E --> F[排列概率]
    end
    
    subgraph 输出
        F --> G[最优排列]
        G --> H[排序结果]
    end
```

## ListNet算法

```mermaid
flowchart TD
    A[ListNet] --> B[列表评分]
    A --> C[概率计算]
    A --> D[损失优化]
    
    B --> B1[每个候选打分]
    
    C --> C1[计算排列概率]
    C --> C2[Top-K概率]
    
    D --> D1[交叉熵损失]
    D --> D2[NDCG优化]
```

## 与其他方法对比

```mermaid
flowchart LR
    subgraph 复杂度
        A[Pointwise] --> D[O(n)]
        B[Pairwise] --> D
        C[Listwise] --> E[O(n!)]
    end
    
    subgraph 精度
        A --> F[较低]
        B --> G[中等]
        C --> H[最高]
    end
```
