# 图9.2：对话评测流程

## 完整评测Pipeline

对话评测流程包含数据准备、评测执行、结果分析三个阶段：

```mermaid
flowchart TD
    subgraph 数据准备
        A[测试语料库] --> B[测试集划分]
        B --> C[基准问题集]
        C --> D[标注指南制定]
    end
    
    subgraph 评测执行
        D --> E[自动评测]
        D --> F[人工评测]
        E --> G[LLM-Judge评测]
        F --> H[专家评审]
        H --> I[用户调研]
    end
    
    subgraph 结果分析
        E --> J[指标计算]
        F --> J
        G --> J
        H --> J
        I --> J
        J --> K[统计分析]
        K --> L[可视化报告]
        L --> M[问题定位]
        M --> N[优化建议]
    end
```

## 多维度评测指标

```mermaid
flowchart LR
    subgraph 维度一：相关性
        A1[语义相关性] --> A2[主题一致性] --> A3[意图匹配度]
    end
    
    subgraph 维度二：流畅性
        B1[语法正确性] --> B2[表达自然度] --> B3[连贯性]
    end
    
    subgraph 维度三：信息量
        C1[内容完整性] --> C2[细节丰富度] --> C3[准确性]
    end
    
    subgraph 维度四：安全性
        D1[风险检测] --> D2[合规检查] --> D3[毒性过滤]
    end
```
