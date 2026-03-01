# 第1章：供给理解基础

## 1. 供给概念演进图

### 图1.1 供给概念的历史演进
```mermaid
mindmap
  root((供给概念演进))
    古典经济学
      亚当·斯密
        劳动价值论
        看不见的手
      李嘉图
        相对优势理论
    新古典经济学
      边际革命
        边际效用递减
        供需均衡
      瓦尔拉斯
        一般均衡理论
    现代经济学
      信息经济学
        信息不对称
        信号传递
      制度经济学
        交易成本
        产权理论
    数字经济时代
      平台经济
        网络效应
        双边市场
      数据要素
        数据成为新生产要素
        数字资产
```

### 图1.2 供给定义的演变
```mermaid
flowchart LR
    A[传统供给<br/>有形商品] --> B[工业供给<br/>规模化生产]
    B --> C[服务供给<br/>无形体验]
    C --> D[数字供给<br/>信息内容]
    D --> E[智能供给<br/>AI能力]
    
    style A fill:#e1f5fe
    style B fill:#b3e5fc
    style C fill:#81d4fa
    style D fill:#4fc3f7
    style E fill:#29b6f6
```

### 图1.3 供给侧改革演进
```mermaid
flowchart TD
    A[供给侧结构性改革] --> B[去产能]
    A --> C[去库存]
    A --> D[去杠杆]
    A --> E[降成本]
    A --> F[补短板]
    
    B --> B1[淘汰落后产能]
    B --> B2[优化产业结构]
    C --> C1[房地产去库存]
    C --> C2[库存周转率提升]
    D --> D1[企业债务重组]
    D --> D2[金融风险防控]
    E --> E1[税制改革]
    E --> E2[简政放权]
    F --> F1[基础设施]
    F --> F2[科技创新]
```

### 图1.4 供给能力的层次
```mermaid
flowchart TB
    A[供给能力] --> B[基础层]
    A --> C[能力层]
    A --> D[创新层]
    
    B --> B1[资源禀赋]
    B --> B2[劳动力]
    B --> B3[资本]
    B --> B4[土地]
    
    C --> C1[生产能力]
    C --> C2[技术能力]
    C --> C3[组织能力]
    
    D --> D1[创新能力]
    D --> D2[学习能力]
    D --> D3[适应能力]
```

### 图1.5 供给与需求关系演变
```mermaid
flowchart LR
    subgraph 古典时期
        A1[供给创造需求<br/>Say定律]
    end
    
    subgraph 凯恩斯时期
        A2[需求创造供给<br/>有效需求不足]
    end
    
    subgraph 现代时期
        A3[供需动态平衡<br/>新古典综合]
    end
    
    subgraph 数字时期
        A4[智能匹配供给<br/>实时个性化]
    end
    
    A1 --> A2 --> A3 --> A4
```

---

## 2. 经济学视角图

### 图1.6 供给的经济学框架
```mermaid
flowchart TB
    subgraph 供给经济学
        A[供给] --> B[生产理论]
        A --> C[成本理论]
        A --> D[市场结构]
        
        B --> B1[生产函数]
        B --> B2[规模经济]
        
        C --> C1[边际成本]
        C --> C2[机会成本]
        
        D --> D1[完全竞争]
        D --> D2[垄断]
        D --> D3[寡头]
    end
```

### 图1.7 供给曲线移动
```mermaid
flowchart LR
    subgraph 供给曲线移动
        A[供给曲线S] -->|技术进步| B[右移S']
        A -->|成本上升| C[左移S'']
        A -->|政策扶持| D[右移S''']
    end
```

### 图1.8 供需均衡模型
```mermaid
flowchart TD
    A[供需均衡] --> B[需求曲线D]
    A --> C[供给曲线S]
    B --> D[均衡点E]
    C --> D
    D --> E[均衡价格Pe]
    D --> F[均衡数量Qe]
    
    B -->|需求增加| G[D右移]
    C -->|供给减少| H[S左移]
    G --> I[新均衡E']
    H --> I
```

---

## 3. 数字化表示方法对比

### 图1.9 向量表示方法演进
```mermaid
flowchart LR
    A[One-Hot] --> B[Bag of Words]
    B --> C[TF-IDF]
    C --> D[Word2Vec]
    D --> E[ELMo]
    E --> F[BERT]
    
    style A fill:#ffcdd2
    style B fill:#ffcdd2
    style C fill:#ffcdd2
    style D fill:#c8e6c9
    style E fill:#c8e6c9
    style F fill:#c8e6c9
```

### 图1.10 离散 vs 连续表示
```mermaid
flowchart TB
    subgraph 离散表示
        A[One-Hot] --> A1[稀疏向量]
        A1 --> A2[无语义相似性]
        A2 --> A3[词汇鸿沟]
    end
    
    subgraph 连续表示
        B[分布式表示] --> B1[密集向量]
        B1 --> B2[语义相似性]
        B2 --> B3[可计算相似度]
    end
```

### 图1.11 文本表示方法对比
```mermaid
flowchart LR
    A[表示方法] --> B[维度]
    A --> C[稀疏/密集]
    A --> D[语义]
    
    B --> B1[高/低]
    C --> C1[稀疏/密集]
    D --> D1[无/有]
```

### 图1.12 嵌入空间可视化
```mermaid
flowchart TB
    A[嵌入空间] --> B[语义相似词聚集]
    A --> C[语义关系可计算]
    A --> D[维度约简可视化]
```

### 图1.13 数字表示的信息密度
```mermaid
flowchart LR
    A[One-Hot<br/>N维度] --> B[TF-IDF<br/>N维度]
    B --> C[Word2Vec<br/>300-500维]
    C --> D[BERT<br/>768-4096维]
```

---

## 4. TF-IDF原理图

### 图1.14 TF-IDF计算流程
```mermaid
flowchart TD
    A[文档集合] --> B[词频TF计算]
    B --> C[逆文档频率IDF计算]
    C --> D[TF-IDF = TF × IDF]
    D --> E[特征向量]
    
    B --> B1[词出现次数<br/>÷ 文档总词数]
    C --> C1[log(文档数<br/>/ 包含词文档数)]
```

### 图1.15 TF-IDF权重分布
```mermaid
flowchart LR
    subgraph TF权重
        A[高频词] -->|高TF| A1[重要词]
    end
    
    subgraph IDF权重
        B[稀有词] -->|高IDF| B1[重要词]
    end
    
    subgraph 综合
        C[常见词] -->|低TF×IDF| C1[低权重]
        D[稀有专业词] -->|高TF×IDF| D1[高权重]
    end
```

### 图1.16 TF-IDF的局限性
```mermaid
flowchart TB
    A[TF-IDF局限性] --> B[语义缺失]
    A --> C[词序丢失]
    A --> D[长文档偏差]
    A --> E[同义词问题]
    
    B --> B1[无法捕捉上下文]
    C --> C1[词袋模型]
    D --> D1[词频天然偏长]
    E --> E1[horse和pony视为不同]
```

---

## 5. Word2Vec原理图

### 图1.17 Skip-gram模型架构
```mermaid
flowchart LR
    subgraph 输入层
        A[中心词]
    end
    
    subgraph 隐藏层
        B[投影]
    end
    
    subgraph 输出层
        C[上下文词]
    end
    
    A --> B --> C
    
    A -->|embedding| B
    B -->|softmax| C
```

### 图1.18 CBOW模型架构
```mermaid
flowchart LR
    subgraph 输入层
        A[上下文词<br/>w1,w2,w3,w4]
    end
    
    subgraph 隐藏层
        B[求和平均]
    end
    
    subgraph 输出层
        C[中心词预测]
    end
    
    A --> B --> C
```

### 图1.19 词向量空间语义关系
```mermaid
flowchart TB
    A[词向量空间] --> B[语义相似词相近]
    A --> C[类比关系可计算]
    
    B --> B1[king - queen ≈ man - woman]
    B --> B2[Paris - France ≈ Tokyo - Japan]
    
    C --> C1[vec(king) - vec(man) + vec(woman) ≈ vec(queen)]
```

---

## 6. BERT vs GPT对比图

### 图1.20 BERT vs GPT架构对比
```mermaid
flowchart TB
    subgraph BERT
        A[BERT Base] --> A1[12层Transformer]
        A --> A2[768隐藏维度]
        A --> A3[双向注意力]
        
        B[BERT Large] --> B1[24层Transformer]
        B --> B2[1024隐藏维度]
        B --> B3[双向注意力]
    end
    
    subgraph GPT
        C[GPT-1] --> C1[12层Transformer]
        C --> C2[768隐藏维度]
        C --> C3[单向注意力]
        
        D[GPT-2] --> D1[48层Transformer]
        D --> D2[1024隐藏维度]
        D --> D3[单向注意力]
        
        E[GPT-3] --> E1[96层Transformer]
        E --> E2[12288隐藏维度]
        E --> E3[单向注意力]
    end
```

### 图1.21 预训练任务对比
```mermaid
flowchart LR
    subgraph BERT预训练
        A[MLM<br/>掩码语言模型] --> A1[随机掩码15%词]
        A1 --> A2[预测被掩码词]
        
        B[NSP<br/>下一句预测] --> B1[判断两句是否相连]
    end
    
    subgraph GPT预训练
        C[CLM<br/>因果语言模型] --> C1[预测下一个词]
        C1 --> C2[自回归生成]
    end
```

### 图1.22 BERT与GPT注意力模式
```mermaid
flowchart TB
    subgraph BERT双向注意力
        A[所有词<br/>互相关注]
        A --> A1[每个词<br/>看到左右所有词]
    end
    
    subgraph GPT单向注意力
        B[每个词<br/>只看左侧]
        B --> B1[从左到右<br/>自回归生成]
    end
```

### 图1.23 应用场景对比
```mermaid
flowchart TB
    subgraph BERT擅长
        A[理解任务] --> A1[文本分类]
        A --> A2[命名实体识别]
        A --> A3[问答系统]
        A --> A4[句子对关系]
    end
    
    subgraph GPT擅长
        B[生成任务] --> B1[文本续写]
        B --> B2[对话生成]
        B --> B3[代码生成]
        B --> B4[创意写作]
    end
```

---

## 7. CLIP多模态图

### 图1.24 CLIP双塔架构
```mermaid
flowchart TB
    A[CLIP双塔模型] --> B[图像编码器]
    A --> C[文本编码器]
    
    B --> B1[ViT-B/32]
    B --> B2[ResNet-50]
    
    C --> C1[Transformer]
    
    B --> D[对比学习]
    C --> D
    D --> E[图文匹配]
```

### 图1.25 CLIP预训练流程
```mermaid
flowchart TD
    A[大规模图文对] --> B[图像编码器]
    A --> C[文本编码器]
    
    B --> D[图像向量I]
    C --> E[文本向量T]
    
    D --> F[对比损失]
    E --> F
    
    F --> G[优化使I·T匹配对相似度最大化]
```

### 图1.26 CLIP零样本分类
```mermaid
flowchart LR
    A[输入图像] --> B[图像编码器]
    
    C[类别文本<br/>"a photo of a cat"] --> D[文本编码器]
    C1[类别文本<br/>"a photo of a dog"] --> D
    C2[类别文本<br/>"a photo of a bird"] --> D
    
    B --> E[计算相似度]
    D --> E
    
    E --> F[选择最高相似度<br/>作为预测类别]
```

---

## 8. 三层理解细节图

### 图1.27 理解的三层模型
```mermaid
flowchart TB
    A[机器理解三层模型] --> B[表层理解<br/>字面意思]
    A --> C[语义理解<br/>意图含义]
    A --> D[语用理解<br/>隐含意图]
    
    B --> B1[词汇识别]
    B --> B2[语法解析]
    B --> B3[句法结构]
    
    C --> C1[语义角色]
    C --> C2[指代消解]
    C --> C3[逻辑推理]
    
    D --> D1[语境推断]
    D --> D2[隐喻理解]
    D --> D3[意图识别]
```

### 图1.28 语义理解层次
```mermaid
flowchart LR
    A[词义] --> B[句义]
    B --> C[段义]
    C --> D[篇义]
    
    A -->|词汇层面| A1[词向量]
    B -->|句子层面| B1[句向量]
    C -->|段落层面| C1[注意力]
    D -->|篇章层面| D1[长距离依赖]
```

### 图1.29 上下文理解机制
```mermaid
flowchart TD
    A[输入文本] --> B[词级别编码]
    B --> C[句子级别编码]
    C --> D[上下文集成]
    
    D --> E[注意力机制]
    E --> F[上下文向量]
    F --> G[理解输出]
```

### 图1.30 语境建模方法
```mermaid
flowchart TB
    A[语境建模] --> B[局部语境<br/>窗口内]
    A --> C[全局语境<br/>全文]
    A --> D[外部语境<br/>知识库]
    
    B --> B1[滑动窗口]
    C --> C1[Transformer]
    D --> D1[知识增强]
```

### 图1.31 理解评估维度
```mermaid
flowchart TB
    A[理解评估] --> B[准确性]
    A --> C[一致性]
    A --> D[推理能力]
    A --> E[鲁棒性]
    
    B --> B1[答案正确]
    C --> C1[不自相矛盾]
    D --> D1[逻辑推理]
    E --> E1[抗干扰能力]
```

---

## 9. 补充图表

### 图1.32 供给弹性类型
```mermaid
flowchart LR
    E[供给弹性] --> P[点弹性]
    E --> A[弧弹性]
    P --> P1[es = ΔQ/Q ÷ ΔP/P]
```

### 图1.33 生产函数类型
```mermaid
flowchart LR
    PF[生产函数] --> L[线性]
    PF --> C[柯布-道格拉斯]
    PF --> F[固定比例]
```

### 图1.34 成本曲线关系
```mermaid
flowchart LR
    TC[总成本] --> AVC[平均可变成本]
    TC --> AFC[平均固定成本]
    AVC --> MC[边际成本]
```

### 图1.35 市场结构类型
```mermaid
flowchart TB
    MS[市场结构] --> PC[完全竞争]
    MS --> MC[垄断]
    MS --> OL[寡头]
    MS --> MC1[垄断竞争]
```

---

## 11. 更多补充图表

### 图1.36 预训练语言模型对比
```mermaid
flowchart LR
    PLM[预训练模型] --> E[编码器]
    PLM --> D[解码器]
    PLM --> ED[编码器-解码器]
    
    E --> BERT
    D --> GPT
    ED --> T5
```

### 图1.37 提示工程方法
```mermaid
flowchart LR
    PE[提示工程] --> Zero[零样本]
    PE --> Few[少样本]
    PE --> CoT[思维链]
    PE --> ReAct[ReAct]
```

### 图1.38 模型评估指标
```mermaid
flowchart TB
    Eval[评估] --> Acc[准确率]
    Eval --> F1[F1分数]
    Eval --> Rouge[ROUGE]
    Eval --> Bleu[BLEU]
```

### 图1.39 对齐技术发展
```mermaid
flowchart LR
    Align[对齐] --> RLHF
    RLHF --> DPO
    RLHF --> KTO
    RLHF --> ORPO
```

### 图1.40 长上下文技术
```mermaid
flowchart LR
    LC[长上下文] --> Sparse[稀疏注意力]
    LC --> Extend[位置编码扩展]
    LC --> Chunk[分块处理]
```
