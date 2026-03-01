# 论文引用库

本目录包含按章节分类的论文引用库。

## 论文统计

| 章节 | 论文数量 | 状态 |
|------|---------|------|
| 第1章 - 基础概念 | 45篇 | 已分析 |
| 第2章 - 深度学习 | 22篇 | 已分析 |
| 第3章 - 知识图谱 | 27篇 | 已分析 |
| 第4章 - 商品理解 | 275篇 | 已分析 |
| 第5章 - 服务理解 | 26篇 | 已分析 |
| 第6章 - 双向匹配 | 5篇 | 已分析 |
| 第7章 - 评测体系 | 10篇 | 已分析 |
| 第8章 - LLM评测 | 9篇 | 已分析 |
| 第9章 - Benchmark | 3篇 | 已分析 |
| 第10章 - 评测指标 | 1篇 | 已分析 |

**总计**: 423篇论文

## 目录结构

```
references/
├── ch01_foundation/      # 第1章 - 供给的概念基础
│   └── papers.json
├── ch02_deep_learning/   # 第2章 - 深度学习技术
│   └── papers.json
├── ch03_knowledge_graph/ # 第3章 - 知识图谱
│   └── papers.json
├── ch04_product/        # 第4章 - 商品理解
│   └── papers.json
├── ch05_service/        # 第5章 - 服务理解
│   └── papers.json
├── ch06_matching/       # 第6章 - 双向匹配
│   └── papers.json
├── ch07_evaluation/     # 第7章 - 评测体系
│   └── papers.json
├── ch08_llm_judge/      # 第8章 - LLM评测
│   └── papers.json
├── ch09_benchmark/      # 第9章 - Benchmark
│   └── papers.json
├── ch10_metrics/        # 第10章 - 评测指标
│   └── papers.json
├── ch11_application/    # 第11章 - 应用实践
│   └── papers.json
└── ch12_future/         # 第12章 - 未来展望
    └── papers.json
```

## 论文分类依据

分类基于论文文件名中的关键词自动识别，包括：
- embedding, representation → 基础概念
- transformer, bert, neural → 深度学习
- knowledge graph, entity, graph → 知识图谱
- product, ecommerce, search, recommendation → 商品理解
- service, chatbot, dialog, intent → 服务理解
- matching, alignment, similarity → 双向匹配
- evaluation, benchmark, metric → 评测相关

---
生成时间: 2026-03-01
