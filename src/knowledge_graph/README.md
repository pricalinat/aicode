# 双向知识图谱系统架构文档

## 1. 系统概述

本系统实现了一个**双向知识图谱驱动的供给匹配系统**，用于支持"人找供给"和"供给找人"两种场景。

### 1.1 核心能力

| 能力 | 描述 | 场景 |
|------|------|------|
| 用户意图图谱 | 建模用户需求、偏好、行为模式 | 人找供给 |
| 供给能力图谱 | 建模商品/服务能力、库存、状态 | 供给找人 |
| 双向匹配引擎 | 双向推荐和召回 | 精准匹配 |

### 1.2 引用论文

| 论文 | 技术点 | 应用 |
|------|--------|------|
| KGAT (arXiv:1905.07854) | 知识图谱注意力网络，高阶关系建模 | 用户-商品-属性路径嵌入 |
| KGIN (arXiv:2102.07057) | 学习交互意图，细粒度关系建模 | 多意图解耦 |
| LGCF (arXiv:2108.04475) | 局部图协同过滤，稀疏场景 | 冷启动场景 |
| User-item Fairness (arXiv:2412.04466) | 双侧公平性优化 | 曝光公平性 |

## 2. 模块架构

```
knowledge_graph/
├── data/                    # 数据层
│   ├── __init__.py
│   ├── dataset.py           # 数据集加载与预处理
│   ├── entities.py          # 实体定义
│   └── relations.py         # 关系定义
│
├── models/                  # 模型层
│   ├── __init__.py
│   ├── graph_builder.py      # 图谱构建器
│   ├── embeddings.py        # 嵌入学习 (KGAT/KGIN/LGCF)
│   └── encoder.py           # 特征编码器
│
├── matching/                # 匹配层
│   ├── __init__.py
│   ├── engine.py            # 双向匹配引擎
│   ├── recall.py            # 召回模块
│   ├── rank.py              # 排序模块
│   └── fairness.py          # 公平性模块
│
├── evaluation/             # 评估层
│   ├── __init__.py
│   ├── metrics.py           # 评估指标
│   └── evaluator.py         # 评估器
│
└── utils/                   # 工具层
    ├── __init__.py
    ├── config.py            # 配置管理
    ├── logger.py            # 日志工具
    └── helpers.py           # 辅助函数
```

## 3. 核心数据模型

### 3.1 实体类型

**用户侧 (User Intent Graph):**
- `User`: 用户实体
- `Intent`: 意图（搜索、购买、对比等）
- `Preference`: 偏好（品牌、价格、材质等）
- `Behavior`: 行为（浏览、点击、购买等）

**供给侧 (Supply Capability Graph):**
- `Product`: 商品/服务
- `Category`: 品类
- `Attribute`: 属性（颜色、尺寸、材质等）
- `SupplyStatus`: 供给状态（库存、上新等）

### 3.2 关系类型

| 关系 | 起点 | 终点 | 说明 |
|------|------|------|------|
| has_intent | User | Intent | 用户具有某意图 |
| prefers | User | Preference | 用户偏好 |
| exhibits | User | Behavior | 用户行为 |
| belongs_to | Product | Category | 商品属于品类 |
| has_attr | Product | Attribute | 商品具有属性 |
| matches_intent | Product | Intent | 商品匹配意图 |
| similar_to | Product | Product | 商品相似 |

## 4. 图谱构建流程

### 4.1 用户意图图谱构建

```
用户查询 → 意图识别 → 实体抽取 → 偏好提取 → 图谱构建
```

1. **意图识别**: 从查询中识别用户意图（商品检索、价格约束、对比决策等）
2. **实体抽取**: 抽取品类、品牌、价格范围等实体
3. **偏好提取**: 从标签中提取用户偏好
4. **图谱构建**: 构建用户-意图-偏好-行为异构图

### 4.2 供给能力图谱构建

```
商品/服务 → 品类分类 → 属性提取 → 状态标注 → 图谱构建
```

1. **品类分类**: 识别商品/服务所属品类
2. **属性提取**: 提取商品属性（颜色、尺寸、材质等）
3. **状态标注**: 标注供给状态（库存、价格区间等）
4. **图谱构建**: 构建商品-品类-属性-供给状态异构图

## 5. 嵌入学习模型

### 5.1 KGAT (Knowledge Graph Attention Network)

- **核心思想**: 使用注意力机制建模高阶关系路径
- **实现**: `models/embeddings/kgat.py`
- **特点**: 可学习的关系注意力权重

### 5.2 KGIN (Knowledge Graph Intent Network)

- **核心思想**: 学习交互意图的细粒度表示
- **实现**: `models/embeddings/kgin.py`
- **特点**: 意图感知的嵌入学习

### 5.3 LGCF (Local Graph Collaborative Filtering)

- **核心思想**: 利用局部图结构进行协同过滤
- **实现**: `models/embeddings/lgcf.py`
- **特点**: 适合稀疏场景

## 6. 双向匹配引擎

### 6.1 人找供给 (User → Supply)

```
用户查询 → 意图解析 → 嵌入计算 → 向量召回 → 排序 → 结果
```

### 6.2 供给找人 (Supply → User)

```
商品/服务 → 能力解析 → 嵌入计算 → 用户召回 → 排序 → 推送
```

### 6.3 匹配策略

| 阶段 | 人找供给 | 供给找人 |
|------|----------|----------|
| 召回 | ANN向量召回 | 用户群画像召回 |
| 粗排 | 规则过滤 | 需求匹配度过滤 |
| 精排 | CTR/CVR排序 | 转化概率排序 |
| 策略 | 多样性重排 | 公平性打散 |

## 7. 公平性模块

### 7.1 双侧公平性

参考 User-item Fairness (arXiv:2412.04466)：

- **供给侧公平**: 避免头部商品过度曝光
- **用户侧公平**: 避免特定用户群体被忽视
- **实现**: `matching/fairness.py`

### 7.2 公平性指标

- **曝光公平性**: 基尼系数衡量曝光分布
- **质量公平性**: 供需匹配质量保证
- **多样性**: 推荐结果多样性衡量

## 8. 数据流转

```
goldset_v0_1
     │
     ▼
┌─────────────────────────────────────────┐
│           data/dataset.py              │
│  (加载 & 预处理 gold_ecom & gold_miniapp) │
└─────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────┐
│        models/graph_builder.py          │
│  (构建用户意图图谱 & 供给能力图谱)        │
└─────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────┐
│         models/embeddings.py            │
│    (KGAT/KGIN/LGCF 嵌入学习)             │
└─────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────┐
│         matching/engine.py              │
│      (双向匹配引擎: 召回 + 排序)          │
└─────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────┐
│        matching/fairness.py             │
│         (公平性优化)                     │
└─────────────────────────────────────────┘
```

## 9. 使用示例

```python
from src.knowledge_graph.data.dataset import KnowledgeGraphDataset
from src.knowledge_graph.models.graph_builder import GraphBuilder
from src.knowledge_graph.models.embeddings import KGATEmbedding
from src.knowledge_graph.matching.engine import MatchingEngine

# 1. 加载数据
dataset = KnowledgeGraphDataset("./goldset_v0_1")
user_graph, supply_graph = dataset.build()

# 2. 构建图谱
builder = GraphBuilder()
user_kg = builder.build_user_intent_graph(dataset)
supply_kg = builder.build_supply_capability_graph(dataset)

# 3. 学习嵌入
model = KGATEmbedding(user_kg, supply_kg)
user_emb, supply_emb = model.train(epochs=100)

# 4. 双向匹配
engine = MatchingEngine(user_emb, supply_emb)

# 人找供给
results = engine.user_to_supply(user_query="想买蓝牙耳机")

# 供给找人
users = engine.supply_to_user(product={"category": "蓝牙耳机", "price": 500})
```

## 10. 评估指标

| 指标 | 说明 |
|------|------|
| Recall@K | Top-K 召回率 |
| NDCG@K | 归一化折扣增益 |
| MRR | 平均倒数排名 |
| Coverage | 覆盖率 |
| Fairness | 公平性指标 |

## 11. 依赖

```txt
numpy>=1.21.0
pandas>=1.3.0
torch>=2.0.0
scikit-learn>=1.0.0
tqdm>=4.60.0
```

## 12. 扩展性

- 可扩展的嵌入模型接口
- 可插拔的匹配策略
- 可配置的公平性约束
- 支持多数据源接入
