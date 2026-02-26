# Multi-Agent System with arXiv Retrieval Agent

This repository provides:

- A minimal multi-agent system architecture
- An implemented `arXiv` paper retrieval agent
- A CLI to run paper search quickly
- V2 Supply Knowledge Graph capabilities

## Quick Start

```bash
cd /Users/rrp/Documents/aicode
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python -m multi_agent_system.cli --query "large language model" --category cs.CL --max-results 5
```

## Architecture Overview

- `Message`: unified task envelope (`task_type + content`)
- `BaseAgent`: common interface for all agents
- `Orchestrator`: registers agents and routes tasks to a suitable agent
- `ArxivAgent`: handles `search_arxiv` style tasks via arXiv API

See detailed design: [docs/MULTI_AGENT_ARCHITECTURE.md](docs/MULTI_AGENT_ARCHITECTURE.md)

## CLI Example

```bash
python -m multi_agent_system.cli \
  --query "graph neural network" \
  --category cs.LG \
  --start-year 2023 \
  --end-year 2025 \
  --max-results 3 \
  --sort-by submittedDate \
  --sort-order descending
```

## Task Contract for `search_arxiv`

The `ArxivAgent` expects message content keys:

- `query` (required): search text
- `category` (optional): e.g. `cs.CL`
- `start_year` (optional): integer
- `end_year` (optional): integer
- `max_results` (optional): default `10`, max `100`
- `sort_by` (optional): `relevance | lastUpdatedDate | submittedDate`
- `sort_order` (optional): `ascending | descending`

## Run Tests

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

## AliCoCo差距补齐（离线可运行版）

在无线上真实流量/数据条件下，新增了可运行的"造数 → 特征聚合 → 双向匹配 → 离线A/B → 反馈回流"闭环：

### 1) 构建闭环样例数据

```bash
python -m multi_agent_system.cli build-closed-loop-demo --seed 42 --supplies 16 --users 10
```

输出到 `data/`：
- `synthetic_supply.json`
- `synthetic_users.json`
- `synthetic_events.json`
- `feature_store_snapshot.json`
- `feature_store_after_feedback.json`（执行 offline AB 后）

### 2) 运行双向匹配 Demo

```bash
python -m multi_agent_system.cli run-dual-matching-demo --top-k 5
```

包含：
- 人找供给：`match_supply_for_user`
- 供给找人：`match_users_for_supply`
- 组合了 KG 候选召回 + 特征打分 + 风险/策略约束

### 3) 运行离线 A/B 实验

```bash
python -m multi_agent_system.cli run-offline-ab --report-name offline_ab_report.json
```

输出到 `data/experiments/*.json`，包含：
- Recall@K / NDCG@K
- 覆盖率
- 转化代理指标
- 简化收益归因

### 4) 多模态输入 V2（增强版）

`src/multi_agent_system/ingestion/multimodal_ingest.py` 支持：
- 文本（带行级源跨度）
- CSV/Markdown 表格（带置信度）
- 图片 OCR（可替换接口 + 默认可运行 stub）
- PDF 文档解析（可替换接口 + 默认可运行 stub）
- 文档分块（按大小/按句子）

```python
from multi_agent_system.ingestion import MultiModalIngestor, KnowledgeChunk

# 基础用法
ing = MultiModalIngestor()
chunks = ing.ingest(text="Hello world", csv_text="a,b\n1,2", pdf_bytes=b"...")

# 自定义 OCR
def my_ocr(image_bytes):
    return "提取的文字"
chunks = ing.ingest(image_bytes=b"...", ocr_fn=my_ocr)

# 文档分块
from multi_agent_system.ingestion import DocumentChunker
chunks = DocumentChunker.chunk_by_size(text, chunk_size=500, overlap=50)
```

### 5) LLM-Judge 评估（V2 新增）

`src/multi_agent_system/experiments/llm_judge_eval.py` 提供：

- 基于规则的评分标准（Relevance, Quality, Safety, Diversity, Freshness）
- 校准钩子（线性/Z分数/百分位）
- LLM 可消费的输出格式

```python
from multi_agent_system.experiments import LlmJudgeEvaluator, LlmJudgeRubric

# 使用默认评分标准
evaluator = LlmJudgeEvaluator()

# 评估单个结果
result = evaluator.evaluate(
    query="I want electronics",
    result={"id": "s1", "category": "electronics", "quality_score": 0.8, "risk_level": "low"}
)

print(result.overall_score)  # 0-1 分数
print(result.overall_level)  # EXCELLENT/GOOD/FAIR/POOR/VERY_POOR

# 获取校准统计
stats = evaluator.calibrate(method="zscore")
```

### 6) 成本与安全控制（V2 新增）

`src/multi_agent_system/cost_safety.py` 提供：

- 模型路由（基于复杂度、成本、能力）
- 审计日志（合规与调试）
- 预算控制（每日/每月限额）
- 安全过滤器（内容审查）

```python
from multi_agent_system.cost_safety import ModelRouter, AuditLogger, CostBudget

# 模型路由
router = ModelRouter()
decision = router.route({"text": "分析这段代码", "prompt": "解释"})

# 审计日志
logger = AuditLogger(log_dir="data/audit")
logger.log(operation="query", model="sonnet", input_tokens=100, output_tokens=50,
           latency_ms=150, success=True)

# 预算控制
budget = CostBudget(daily_limit=10.0, monthly_limit=100)
allowed, reason = budget.check_budget("user123", 0.5)
```

### 边界说明（务实版）

- 当前为离线仿真，不包含真实线上流量分配、延迟反馈和高并发保障。
- OCR/PDF 解析默认是 stub；接入真实服务需注入对应函数。
- A/B 与归因为离线近似模型，用于框架验证，不等价于线上因果实验。
