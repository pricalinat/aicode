# Multi-Agent System with arXiv Retrieval Agent

This repository provides:

- A minimal multi-agent system architecture
- An implemented `arXiv` paper retrieval agent
- A CLI to run paper search quickly

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

在无线上真实流量/数据条件下，新增了可运行的“造数 → 特征聚合 → 双向匹配 → 离线A/B → 反馈回流”闭环：

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

### 4) 多模态输入降级方案

`src/multi_agent_system/ingestion/multimodal_ingest.py` 支持：
- 文本
- CSV/Markdown 表格
- 图片 OCR（可替换接口 + 默认可运行 stub）

### 边界说明（务实版）

- 当前为离线仿真，不包含真实线上流量分配、延迟反馈和高并发保障。
- OCR 默认是 stub；接入真实 OCR 需注入 `ocr_fn`。
- A/B 与归因为离线近似模型，用于框架验证，不等价于线上因果实验。
