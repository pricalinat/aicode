# Multi-Agent System 项目文档

## 1. 项目概述

**项目名称**: Multi-Agent arXiv System
**版本**: 0.1.0
**描述**: 基于多智能体架构的论文检索与管理系统，支持语义搜索、意图分类、实体提取等功能
**编程语言**: Python 3.9+

## 2. 项目结构

```
aicode/
├── src/multi_agent_system/     # 主源码目录
│   ├── agents/                # Agent 实现
│   │   ├── arxiv_agent.py         # arXiv 论文检索
│   │   ├── intent_classification_agent.py  # 意图分类
│   │   ├── entity_extraction_agent.py      # 实体提取
│   │   ├── semantic_search_agent.py        # 语义搜索
│   │   ├── paper_search_agent.py           # 论文库搜索
│   │   ├── matching_agent.py               # 匹配推荐
│   │   ├── recommendation_agent.py         # 推荐系统
│   │   └── user_profile_agent.py           # 用户画像
│   │
│   ├── core/                 # 核心框架
│   │   ├── agent.py              # Agent 基类
│   │   ├── orchestrator.py      # 任务编排器
│   │   ├── message.py           # 消息格式
│   │   ├── registry.py          # Agent 注册
│   │   ├── plugin.py            # 插件系统
│   │   ├── cache.py             # 缓存
│   │   └── tracing.py           # 追踪
│   │
│   ├── enterprise/            # 企业级扩展
│   │   ├── planner.py               # 任务规划 (Routine)
│   │   ├── memory.py                 # 记忆系统
│   │   ├── evaluator.py              # 评测系统 (IntellAgent)
│   │   ├── rag.py                    # RAG 知识增强
│   │   ├── proactive.py              # 主动感知 (ProAgent)
│   │   ├── consensus.py              # 共识决策
│   │   ├── continual.py              # 持续学习 (GenCNER)
│   │   ├── self_optimizing.py        # 自优化系统 (AccelOpt)
│   │   ├── brainstorming.py         # 头脑风暴系统
│   │   ├── domain_qa.py             # 领域问答系统
│   │   └── orchestrator_enhanced.py  # 增强编排器
│   │
│   ├── knowledge/            # 知识管理
│   │   ├── graph.py              # 知识图谱
│   │   └── paper.py              # 论文模型
│   │
│   ├── adapters/             # 外部适配器
│   ├── cli.py                # CLI 入口
│   └── ...
│
├── data/                     # 数据目录
│   └── papers.json           # 论文库 (136篇)
│
├── tests/                    # 测试
│   └── test_arxiv_agent.py
│
├── docs/                     # 文档
│   ├── MULTI_AGENT_ARCHITECTURE.md
│   └── ENTERPRISE_AGENT_ARCHITECTURE.md
│
└── pyproject.toml           # 项目配置
```

## 3. 核心模块说明

### 3.1 Agent 体系

| Agent | 功能 | 核心能力 |
|-------|------|----------|
| ArxivAgent | arXiv论文检索 | search_arxiv |
| IntentClassificationAgent | 意图分类 | classify_intent |
| EntityExtractionAgent | 实体提取 | extract_entity |
| SemanticSearchAgent | 语义搜索 | semantic_search |
| PaperSearchAgent | 本地论文搜索 | search_papers |
| MatchingAgent | 匹配推荐 | match, recommend |
| RecommendationAgent | 个性化推荐 | recommend |

### 3.2 企业级扩展

| 模块 | 功能 | 参考论文 |
|------|------|----------|
| Planner | 结构化任务规划 | Routine |
| Memory | 短期/长期记忆 | Multi-Agent Memory |
| Evaluator | 多维质量评测 | IntellAgent |
| RAG | 知识检索增强 | Multi-Agent RAG |
| Proactive | 主动服务预测 | ProAgent |
| Consensus | 多Agent共识 | Silence is Not Consensus |
| Continual | 持续学习 | GenCNER |
| SelfOptimizing | 自优化系统 | AccelOpt |
| Brainstorming | 头脑风暴系统 | Multi-Agent Research Ideation |
| DomainQA | 领域问答系统 | RAG-Based Multi-Agent |
| Security | 安全防护 | Agents Under Siege |
| Monitoring | 行为监控 | Multi-Agent Observability |
| CostControl | 成本控制 | Controlling Performance and Budget |

## 4. 数据资源

### 4.1 论文库

- **位置**: `data/papers.json`
- **数量**: 136 篇
- **时间范围**: 2023-2025
- **主要分类**: cs.CL, cs.AI, cs.LG, cs.IR

### 4.2 论文主题分布

| 主题 | 数量 |
|------|------|
| LLM | 45 |
| entity/NER | 36 |
| retrieval/search | 37 |
| multi-agent | 32 |
| graph | 24 |
| RAG | 19 |
| conversational | 17 |
| intent | 16 |
| semantic | 15 |

## 5. CLI 命令

### 5.1 论文搜索

```bash
# 搜索 arXiv 论文
python -m multi_agent_system.cli search-arxiv --query "LLM agent" --category cs.CL --max-results 10

# 保存论文到本地
python -m multi_agent_system.cli save --query "multi-agent LLM" --category cs.CL --max-results 25

# 列出已保存论文
python -m multi_agent_system.cli list --category cs.LG --year 2025

# 语义搜索
python -m multi_agent_system.cli semantic-search "graph neural network" --top-k 5

# 统计论文数量
python -m multi_agent_system.cli count
```

## 6. 架构分层

```
┌─────────────────────────────────────────────┐
│            CLI / API 入口层                  │
├─────────────────────────────────────────────┤
│            任务入口 (解析 + 路由)              │
├─────────────────────────────────────────────┤
│     EnhancedOrchestrator (增强编排器)         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │ Planner  │ │Proactive │ │ Consensus │   │
│  │ 任务规划 │ │ 主动感知 │ │ 共识决策 │   │
│  └──────────┘ └──────────┘ └──────────┘   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │  Memory  │ │   RAG   │ │Evaluator │   │
│  │ 记忆系统 │ │ 知识增强 │ │ 评测系统 │   │
│  └──────────┘ └──────────┘ └──────────┘   │
├─────────────────────────────────────────────┤
│            基础 Agent 层                      │
│  ArxivAgent | IntentAgent | EntityAgent ...  │
├─────────────────────────────────────────────┤
│            知识存储层                        │
│  papers.json | entities.json | memory/        │
└─────────────────────────────────────────────┘
```

## 7. 使用示例

### 7.1 基本使用

```python
from multi_agent_system.core import Orchestrator, Message
from multi_agent_system.agents import ArxivAgent, IntentClassificationAgent

# 创建编排器
orchestrator = Orchestrator([
    ArxivAgent(),
    IntentClassificationAgent(),
])

# 发送任务
message = Message(
    task_type="search_arxiv",
    content={"query": "LLM agent", "max_results": 10}
)

response = orchestrator.dispatch(message)
print(response.data)
```

### 7.2 企业级使用

```python
from multi_agent_system.enterprise import EnhancedOrchestrator, ExecutionStrategy

# 创建增强编排器
orchestrator = EnhancedOrchestrator(
    agents=[ArxivAgent(), IntentClassificationAgent()],
    config=ExecutionConfig(
        strategy=ExecutionStrategy.CONSENSUS,
        enable_evaluation=True,
        enable_rag=True,
    )
)

# 执行任务
response = orchestrator.dispatch(message, user_id="user123")
```

## 8. 扩展开发

### 8.1 新增 Agent

```python
from multi_agent_system.core import BaseAgent, AgentResponse, Message

class MyAgent(BaseAgent):
    name = "my-agent"
    capabilities = {"my_task"}

    def handle(self, message: Message) -> AgentResponse:
        # 实现逻辑
        return AgentResponse(agent=self.name, success=True, data={})
```

### 8.2 新增知识源

```python
from multi_agent_system.enterprise.rag import KnowledgeSource, RetrievedChunk

class MyKnowledgeSource(KnowledgeSource):
    def retrieve(self, query: str, top_k: int = 5):
        # 实现检索逻辑
        return []
```

## 9. 依赖

- Python >= 3.9
- loguru >= 0.7.0
- typing-extensions >= 4.5

## 10. 后续规划

### Phase 1: 基础能力
- [x] 多Agent架构
- [x] 论文检索 (ArxivAgent)
- [x] 本地论文库 + 向量搜索

### Phase 2: 企业级扩展 (已完成)
- [x] 任务规划 (Planner)
- [x] 记忆系统 (Memory)
- [x] 评测系统 (Evaluator)
- [x] RAG 知识增强
- [x] ProActive 主动服务
- [x] Multi-Agent 共识决策
- [x] Continual Learning 持续学习
- [x] Self-Optimizing 自优化
- [x] Brainstorming 头脑风暴
- [x] DomainQA 领域问答
- [x] Security 安全防护
- [x] Monitoring 行为监控
- [x] CostControl 成本控制

### Phase 3: LLM 集成
- [ ] 接入 Claude API
- [ ] 接入 OpenAI API
- [ ] 接入本地模型

## 11. 相关论文

### 已落地方向
1. **Routine** - 结构化任务规划
2. **ProAgent** - 主动式LLM Agent
3. **IntellAgent** - 对话系统评测
4. **GenCNER** - 持续学习NER

### RAG 方向
- Multi-Agent GraphRAG
- RAG-Based Multi-Agent LLM System

### Multi-Agent 方向
- CORE: Measuring Multi-Agent LLM Interaction
- Controlling Performance and Budget of Multi-Agent LLM

---

*最后更新: 2025-02-24*
