# 图1: 提示工程概述

```mermaid
flowchart LR
    subgraph "核心要素"
        P1[任务描述]
        P2[输入格式]
        P3[输出格式]
        P4[示例]
    end
    
    P1 --> P5[优化提示<br/>提升效果]
    P2 --> P5
    P3 --> P5
    P4 --> P5
    
    style P1 fill:#e3f2fd
    style P5 fill:#c8e6c9
```

**说明**: 提示工程通过设计合适的指令、格式和示例，引导模型产生期望的输出。

---

# 图2: 零样本提示

```mermaid
flowchart LR
    subgraph "Zero-Shot"
        Z1[无示例]
        Z1 --> Z2[直接指令]
    end
    
    subgraph "示例"
        Z3[情感分析:<br/>"这个产品很棒"→?]
        Z4[输出: Positive]
    end
    
    Z2 --> Z4
    
    style Z1 fill:#e3f2fd
    style Z4 fill:#c8e6c9
```

**说明**: 零样本提示不提供示例，仅通过指令引导模型完成任务，考验模型泛化能力。

---

# 图3: 少样本提示

```mermaid
flowchart LR
    subgraph "Few-Shot"
        F1[提供K个示例]
    end
    
    F1 --> F2[示例1: Great→Positive]
    F1 --> F3[示例2: Terrible→Negative]
    F1 --> F4[示例3: Okay→Neutral]
    F2 --> F5[测试: So-so→?]
    F3 --> F5
    F4 --> F5
    
    style F1 fill:#e3f2fd
    style F5 fill:#fff3e0
```

**说明**: 少样本提示通过示例帮助模型理解任务格式和意图，提升few-shot性能。

---

# 图4: 思维链提示(CoT)

```mermaid
flowchart LR
    subgraph "CoT提示"
        C1[问题+让我们<br/>一步步思考]
        C1 --> C2[中间推理步骤]
        C2 --> C3[最终答案]
    end
    
    C1 --> C4[复杂推理任务<br/>数学/逻辑]
    
    style C1 fill:#fff3e0
    style C4 fill:#c8e6c9
```

**说明**: Chain-of-Thought提示引导模型展示推理过程，显著提升复杂推理任务效果。

---

# 图5: 自洽性提示

```mermaid
flowchart LR
    subgraph "Self-Consistency"
        S1[多次采样<br/>不同路径]
    end
    
    S1 --> S2[生成多个<br/>推理结果]
    S2 --> S3[投票选择<br/>最一致答案]
    
    style S1 fill:#e3f2fd
    style S3 fill:#c8e6c9
```

**说明**: 自洽性通过多路径推理和投票机制，提高推理结果的可靠性。

---

# 图6: 角色提示

```mermaid
flowchart LR
    subgraph "Role Prompting"
        R1[设定角色]
        R2[你是一位资深<br/>产品经理]
    end
    
    R2 --> R3[符合角色的<br/>视角和风格]
    
    style R1 fill:#e3f2fd
    style R3 fill:#c8e6c9
```

**说明**: 角色提示设定模型扮演特定角色，获得更符合特定场景的输出。

---

# 图7: 结构化输出提示

```mermaid
flowchart LR
    subgraph "Output Formatting"
        F1[JSON格式]
        F1 --> F2[{字段1, 字段2}]
    end
    
    F1 --> F3[markdown表格]
    F1 --> F4[列表/编号]
    
    style F1 fill:#e3f2fd
```

**说明**: 指定输出格式便于后续程序解析，提高模型输出可用性。

---

# 图8: 知识提示

```mermaid
flowchart LR
    subgraph "Knowledge Prompting"
        K1[先提供相关知识]
        K2[基于知识回答]
    end
    
    K1 --> K3[减少幻觉<br/>提高准确性]
    K2 --> K3
    
    style K1 fill:#fff3e0
    style K3 fill:#c8e6c9
```

**说明**: 在提示中先提供相关背景知识，引导模型基于给定知识而非记忆回答。

---

# 图9: 迭代优化提示

```mermaid
flowchart LR
    subgraph "Iterative"
        I1[生成初稿] --> I2[评估]
        I2 --> I3[改进指令]
        I3 --> I1
    end
    
    I2 --> I4[多轮优化<br/>直到满意]
    
    style I1 fill:#e3f2fd
    style I4 fill:#c8e6c9
```

**说明**: 通过迭代方式不断优化提示，基于前轮结果调整指令提高输出质量。

---

# 图10: 提示工程最佳实践

```mermaid
flowchart TD
    A[提示设计] --> B[清晰明确]
    A --> C[具体示例]
    A --> D[适当限制]
    A --> E[迭代优化]
    
    B --> B1[减少歧义]
    C --> C1[帮助理解]
    D --> D1[控制格式]
    E --> E1[持续改进]
    
    style A fill:#e1f5fe
    style E1 fill:#81d4fa
```

**说明**: 好的提示应清晰具体，包含示例，适当限制输出格式，并持续迭代优化。
