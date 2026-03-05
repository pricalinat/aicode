# MobilityBench 论文深度分析报告

**论文来源**: arXiv 2602.22638 (2026年2月26日)  
**作者**: Zhiheng Song, Jingshuai Zhang, Chuan Qin 等（高德地图 + 中科院）  
**GitHub**: https://github.com/AMAP-ML/MobilityBench

---

## 1. 论文概述

MobilityBench 是首个针对**基于大语言模型(LLM)的路径规划智能体**的系统化评测基准。该基准基于高德地图的大规模真实用户查询构建，覆盖全球350+城市、22个国家，包含10万个评测 episodes。

**核心问题**: 现有评测基准（如TravelBench、TravelPlanner）主要关注高级行程规划，缺乏对**日常出行场景中细粒度路径规划**的评测能力。

---

## 2. 核心贡献

### 2.1 基准构建

| 贡献点 | 具体描述 |
|--------|----------|
| **大规模真实数据** | 来自高德地图6个月的匿名用户语音查询（语音转文本） |
| **可扩展任务分类** | 4大意图家族、11种任务场景 |
| **确定性重放沙盒** | 消除实时地图API的随机性，确保可复现性 |
| **多维评测协议** | 涵盖指令理解、规划、工具使用、决策、效率5个维度 |

### 2.2 评测协议创新

论文提出将智能体行为分解为**5大核心能力**进行细粒度评测：

1. **Instruction Understanding** - 意图检测 + 信息提取
2. **Planning** - 任务分解
3. **Tool Use** - 工具选择 + 模式合规
4. **Decision Making** - 交付率 + 最终通过率
5. **Efficiency** - 输入/输出Token统计

---

## 3. 方法详解

### 3.1 任务分类体系

```
MobilityBench Task Taxonomy
├── Basic Information Retrieval (36.6%)
│   ├── POI Query
│   ├── Geolocation Query
│   ├── Nearby Query
│   ├── Weather Query
│   └── Traffic Info Query
├── Route-Dependent Information Retrieval (9.6%)
│   ├── Route Property Query
│   └── Arrival/Departure Time Query
├── Basic Route Planning (42.5%)
│   ├── Point-to-Point Planning
│   └── Multi-stop Planning
└── Preference-Constrained Route Planning (11.3%)
    ├── Option-Constrained (avoid tolls/highways, minimize transfers)
    └── Route-Constrained (via specific waypoints, avoid specific roads)
```

### 3.2 确定性重放沙盒设计

```
┌─────────────────────────────────────────────┐
│           Ground Truth Construction         │
│  (Capture API responses, freeze traffic)   │
└─────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────┐
│          Deterministic Replay Sandbox       │
│  • Pre-recorded API responses               │
│  • Canonicalized argument keys              │
│  • Fuzzy matching fallback                   │
│  • Strict schema validation                 │
└─────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────┐
│            Agent Evaluation                 │
│  • Identical inputs → Identical outputs    │
│  • No live API calls                        │
└─────────────────────────────────────────────┘
```

### 3.3 评测指标体系

| 维度 | 指标 | 公式/描述 |
|------|------|-----------|
| Instruction Understanding | Intent Detection (ID) | 意图标签相似度 ≥ α |
| | Information Extraction (IE) | 约束集合完全匹配 |
| Planning | DEC-P / DEC-R | 任务分解的精确率/召回率 |
| Tool Use | TS-P / TS-R | 工具选择的精确率/召回率 |
| | Schema Compliance (SC) | API参数格式/范围合规性 |
| Decision Making | Delivery Rate (DR) | 成功生成完整输出的比例 |
| | Final Pass Rate (FPR) | 满足所有显式/隐式约束的比例 |
| Efficiency | Input/Output Tokens | 上下文和处理开销 |

---

## 4. 实验发现

### 4.1 模型性能对比

| 框架 | 最佳模型 | Delivery Rate | Final Pass Rate |
|------|----------|---------------|-----------------|
| Plan-and-Execute | Claude-Opus-4.5 | **83.53%** | **65.77%** |
| ReAct | Gemini-3-Pro-Preview | 81.42% | **69.09%** |

### 4.2 关键发现

1. **基础任务表现良好**: Basic Information Retrieval 和 Basic Route Planning 任务表现优异

2. **偏好约束是难点**: Preference-Constrained Route Planning 是当前模型最容易出错的场景
   - Option-Constrained: 避免收费/高速、最少换乘
   - Route-Constrained: 途径特定地点、避开特定道路

3. **框架权衡**:
   - **ReAct**: 更好的最终通过率（动态调整策略），但Token消耗高35.38%
   - **Plan-and-Execute**: 更高效，但面对动态反馈时缺乏鲁棒性

4. **Scaling效应**: 模型规模增大带来一致的性能提升（4B→32B提升0.91%，MoE架构额外提升5.43%）

5. **Thinking模式**: 启用思考模式可提升约5-6%的FPR，但显著增加推理延迟

---

## 5. 与本书的关联评估

### 5.1 知识图谱（Knowledge Graph）

| 关联维度 | 分析 |
|----------|------|
| **实体类型** | POI（兴趣点）、地点、路线、交通方式、天气条件 |
| **关系建模** | 起点-终点路径、途径点顺序、偏好约束（如"避开高速"） |
| **时空属性** | 实时交通、天气、时间窗口、到达时间预测 |
| **KG应用机会** | 可将MobilityBench数据构建为出行领域知识图谱，用于意图理解、约束推理 |

### 5.2 供给理解（Supply Understanding）

| 关联维度 | 分析 |
|----------|------|
| **供给侧实体** | 道路网络、公共交通路线、POI服务能力 |
| **约束推理** | 偏好约束需要理解"高速"、"收费"、"换乘"等供给属性 |
| **多模态供给** | 支持驾车、步行、骑行、公交等多种出行方式 |
| **研究机会** | 如何利用KG进行跨供给选项的推理和推荐 |

### 5.3 评测体系（Benchmark/Evaluation）

| 关联维度 | 分析 |
|----------|------|
| **评测范式创新** | 多维分解评测（vs. 端到端黑盒评测） |
| **可复现性设计** | API重放沙盒消除环境随机性 |
| **任务难度梯度** | 从简单查询→多约束路径规划的渐进难度 |
| **对本书的借鉴** | 可参考其任务分类+多维评测思路构建垂直领域评测体系 |

---

## 6. 研究启示与机会

### 6.1 当前模型局限

1. **偏好约束处理能力不足** - 需要更强的约束满足推理
2. **多步规划幻觉** - 尤其在ReAct框架中可能偏离正确轨迹
3. **实时信息处理** - 对动态交通/天气信息的利用不充分

### 6.2 潜在改进方向

1. **知识图谱增强** - 将道路网络、POI关系编码为结构化知识
2. **混合架构** - LLM用于意图理解，传统算法用于路径优化
3. **强化学习微调** - 针对约束满足任务进行专项训练
4. **多智能体协作** - 意图理解、路径规划、偏好推理分工

---

## 7. 总结

MobilityBench 是路径规划智能体领域的重要里程碑：

- **数据质量**: 基于真实大规模用户查询，覆盖全球350+城市
- **评测创新**: 分解式多维评测 + 确定性沙盒确保可复现性
- **实践价值**: 揭示了当前LLM在偏好约束路径规划上的显著短板
- **生态贡献**: 开源基准数据和工具包，促进社区研究

对于从事**出行智能体、知识图谱、评测系统**研究的学者和工程师，MobilityBench 提供了重要的实验平台和参考框架。

---

*报告生成时间: 2026-03-05*  
*论文链接: https://arxiv.org/abs/2602.22638*  
*代码仓库: https://github.com/AMAP-ML/MobilityBench*
