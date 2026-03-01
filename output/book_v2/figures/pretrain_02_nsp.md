# 图1: NSP任务原理

```mermaid
flowchart LR
    subgraph "输入"
        N1[句子A]
        N2[句子B]
    end
    
    subgraph "二分类任务"
        N3[IsNext?]
        N3 --> N4[是下一句]
        N3 --> N5[不是下一句]
    end
    
    N1 --> N3
    N2 --> N3
    
    style N1 fill:#e3f2fd
    style N4 fill:#c8e6c9
    style N5 fill:#ffcdd2
```

**说明**: Next Sentence Prediction让模型学习理解句子间的关系，对阅读理解等任务很重要。

---

# 图2: NSP数据构造

```mermaid
flowchart LR
    subgraph "正样本"
        P1[50%是连续句子]
    end
    
    subgraph "负样本"
        N1[50%随机句子]
    end
    
    P1 --> P2[训练数据]
    N1 --> P2
    
    style P1 fill:#c8e6c9
    style N1 fill:#ffcdd2
```

**说明**: 训练时50%使用真实的下一句，50%使用随机句子，让模型区分连续性。

---

# 图3: NSPBERT中的位置

在```mermaid
flowchart LR
    subgraph "BERT预训练"
        B1[Token级别<br/>MLM]
        B2[句子级别<br/>NSP]
    end
    
    B1 --> B3[联合训练]
    B2 --> B3
    
    style B1 fill:#e3f2fd
    style B2 fill:#fff3e0
```

**说明**: BERT同时训练MLM和NSP任务，MLM学习词级别表示，NSP学习句子级别表示。

---

# 图4: NSP任务的效果

```mermaid
flowchart LR
    subgraph "有NSP"
        Y1[句子关系理解]
        Y1 --> Y2[QA任务提升]
        Y2 --> Y3[NLI任务提升]
    end
    
    subgraph "无NSP"
        N1[仅词级别理解]
    end
    
    style Y1 fill:#c8e6c9
    style N1 fill:#fff3e0
```

**说明**: NSP对需要句子级别理解的任务如问答、自然语言推理有显著帮助。

---

# 图5: NSP的后续改进

```mermaid
flowchart LR
    subgraph "改进方法"
        I1[SOP<br/>Sentence Order Prediction]
    end
    
    I1 --> I2[正: 正确顺序AB]
    I2 --> I3[负: 错误顺序BA]
    
    I3 --> I4[更好学习<br/>句子顺序关系]
    
    style I1 fill:#e3f2fd
    style I4 fill:#c8e6c9
```

**说明**: 后来的模型如ALBERT用SOP替代NSP，预测句子顺序而非是否连续，效果更好。
