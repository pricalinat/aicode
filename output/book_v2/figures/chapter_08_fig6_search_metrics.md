# 图8.6：搜索评测指标——NDCG/DCGM原理

## NDCG原理

```mermaid
flowchart LR
    subgraph DCG计算
        A[相关性分数] --> D[折现累计增益]
    end
    
    subgraph IDCG
        B[理想排序] --> E[理想DCG]
    end
    
    subgraph NDCG
        D --> F[NDCG]
        E --> F
    end
```

## 计算公式

```mermaid
flowchart LR
    subgraph DCG
        A[rel₁/log₂(i+1)] --> D[Σ]
    end
    
    subgraph NDCG
        B[DCG/IDCG] --> E[0-1标准化]
    end
```
