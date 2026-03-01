# 图S.5：供需匹配完整流程图

## 端到端匹配Pipeline

本书详细介绍了从用户需求到商品供给的完整匹配流程：

```mermaid
flowchart TD
    subgraph 需求侧
        A[用户Query] --> B[Query理解]
        B --> C[意图识别]
        C --> D[实体抽取]
        D --> E[类目预测]
        E --> F[语义编码]
    end
    
    subgraph 供给侧
        G[商品库] --> H[商品理解]
        H --> I[实体识别]
        I --> J[属性抽取]
        J --> K[类目映射]
        K --> L[向量编码]
    end
    
    subgraph 匹配层
        F --> M[向量检索]
        L --> M
        M --> N[候选召回]
        N --> O[粗排]
        O --> P[精排]
        P --> Q[重排]
    end
    
    subgraph 业务层
        Q --> R[业务规则]
        R --> S[多样性处理]
        S --> T[结果展示]
        T --> U[效果追踪]
        U --> V[反馈优化]
    end
    
    V --> B
    V --> H
```

## 多通道召回策略

```mermaid
flowchart LR
    subgraph 召回通道
        A[关键词召回] --> D[召回合并]
        B[向量召回] --> D
        C[知识图谱召回] --> D
        E[规则召回] --> D
    end
    
    subgraph 排序阶段
        D --> F[粗排模型]
        F --> G[精排模型]
        G --> H[重排模型]
    end
    
    subgraph 输出
        H --> I[最终结果]
    end
```

## 核心算法组件

| 阶段 | 核心组件 | 技术选型 |
|------|---------|----------|
| 需求理解 | 意图识别 | BERT+分类器 |
| 需求理解 | 实体抽取 | BERT+NER |
| 供给理解 | 商品编码 | BERT+属性模型 |
| 匹配召回 | 向量检索 | Faiss/HNSW |
| 排序 | 粗排/精排 | DNN/LightGBM |
| 重排 | 多样性 | MMR/DPP |
