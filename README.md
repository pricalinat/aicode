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
