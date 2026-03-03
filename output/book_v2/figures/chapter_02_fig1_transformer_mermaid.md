# 图2.1：Transformer架构图

```mermaid
graph TD
    Input[Input Embedding<br/>+ Positional Encoding] --> Encoder[Encoder Stack<br/>N=6 layers]
    Encoder --> Decoder[Decoder Stack<br/>N=6 layers]
    Decoder --> Output[Linear<br/>+ Softmax Output]
    
    subgraph "Encoder Layer"
        MHA[Multi-Head Attention] --> AddNorm1[Add & Norm]
        AddNorm1 --> FFN[Feed Forward Network]
        FFN --> AddNorm2[Add & Norm]
    end
    
    subgraph "Decoder Layer"
        MaskMHA[Masked Multi-Head Attention] --> AddNorm3[Add & Norm]
        AddNorm3 --> CrossAttn[Cross Attention]
        CrossAttn --> AddNorm4[Add & Norm]
        AddNorm4 --> FFN2[Feed Forward Network]
        FFN2 --> AddNorm5[Add & Norm]
    end
    
    Encoder -.-> "×6" 
    Decoder -.-> "×6"
```

标题: Transformer架构图
说明: 展示Transformer的Encoder-Decoder结构，包括输入嵌入、多头注意力、前馈网络等核心组件
