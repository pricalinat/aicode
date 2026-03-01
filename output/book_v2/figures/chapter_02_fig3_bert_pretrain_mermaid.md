# 图2.3：BERT预训练流程

```mermaid
graph TD
    Input[输入: [CLS] the man went to [MASK] store [SEP]...]
    
    subgraph "Task 1: MLM"
        Input --> Mask[随机掩盖15%token]
        Mask --> Predict[预测[MASK]位置]
        Predict --> MLM[MLM Loss]
    end
    
    subgraph "Task 2: NSP"
        Input --> SentA[Sentence A]
        Input --> SentB[Sentence B]
        SentA --> IsNext[判断B是否为A的下一句]
        IsNext --> NSP[NSP Loss]
    end
    
    MLM --> Combine[MLM + NSP<br/>联合训练]
    NSP --> Combine
    Combine --> BERT[BERT Pre-trained Model]
```

标题: BERT预训练流程
说明: 展示BERT的MLM（掩码语言模型）和NSP（下一句预测）两个预训练任务
