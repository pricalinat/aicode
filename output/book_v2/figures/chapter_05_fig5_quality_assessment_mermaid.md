```mermaid
flowchart LR
    subgraph 数据源
        A[服务元数据] ::: data
        B[用户行为日志] ::: data
        C[用户评价数据] ::: data
        D[违规记录数据] ::: data
    end
    
    subgraph 评估维度
        E[功能完备性] ::: dim
        F[性能稳定性] ::: dim
        G[用户口碑] ::: dim
        H[安全保障] ::: dim
        I[合规性] ::: dim
    end
    
    subgraph 评估方法
        J[规则检查] ::: method
        K[统计分析] ::: method
        L[机器学习] ::: method
    end
    
    subgraph 输出
        M[质量分数] ::: output
        N[质量报告] ::: output
    end
    
    A --> E
    B --> F
    C --> G
    D --> H
    D --> I
    
    E --> J
    F --> K
    G --> K
    H --> J
    I --> J
    
    J --> L
    K --> L
    
    L --> M
    L --> N
    
Def data fill:#e3f2fd,    classstroke:#1976d2
    classDef dim fill:#fff3e0,stroke:#f57c00
    classDef method fill:#e8f5e9,stroke:#388e3c
    classDef output fill:#fce4ec,stroke:#c2185b
```
