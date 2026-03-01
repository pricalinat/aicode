# 图11.1：电商搜索实践架构

## 端到端服务架构

本章以电商搜索为案例，展示完整的LLM服务落地实践：

```mermaid
flowchart TD
    subgraph 接入层
        A[用户查询] --> B[流量网关]
        B --> C[请求路由]
    end
    
    subgraph 理解层
        C --> D[意图识别]
        D --> E[实体抽取]
        E --> F[类目预测]
        F --> G[语义编码]
    end
    
    subgraph 召回层
        G --> H[关键词召回]
        G --> I[向量召回]
        G --> J[知识图谱召回]
        H --> K[候选合并]
        I --> K
        J --> K
    end
    
    subgraph 排序层
        K --> L[粗排]
        L --> M[精排]
        M --> N[重排]
    end
    
    subgraph 结果层
        N --> O[结果展示]
        O --> P[效果追踪]
        P --> Q[反馈优化]
    end
```

## 核心模块技术选型

| 模块 | 技术选型 | 核心能力 |
|------|---------|----------|
| 语义编码 | BERT/ERNIE | 深度语义理解 |
| 向量召回 | Faiss/HNSW | 高效相似检索 |
| 知识图谱 | Neo4j | 结构化知识 |
| 模型排序 | LightGBM/DNN | 智能排序 |
