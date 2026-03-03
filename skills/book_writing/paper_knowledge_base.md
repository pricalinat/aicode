# Paper Knowledge Base System - 论文知识库分析与检索系统

## 目标
构建一个结构化的论文知识库，用于：
1. 存储已下载的所有论文元信息和分析结果
2. 支持按主题、作者、年份、技术方法等维度检索
3. 为书籍写作提供精准的论文引用支撑
4. 支持批量分析和对比分析

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    论文知识库系统                              │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ 论文爬取  │  │ 元信息   │  │ 内容分析  │  │ 向量存储  │   │
│  │ 模块     │  │ 提取     │  │ 模块     │  │ 模块     │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│         │            │            │            │              │
│         └────────────┴────────────┴────────────┘              │
│                          │                                    │
│                    ┌─────┴─────┐                              │
│                    │  知识库    │                              │
│                    │ (SQLite/   │                              │
│                    │  JSON)     │                              │
│                    └─────┬─────┘                              │
│                          │                                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ 主题分类 │  │ 检索引擎  │  │ 对比分析  │  │ 引用生成 │   │
│  │ 模块     │  │ 模块     │  │ 模块     │  │ 模块     │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## 数据结构设计

### 1. 论文元信息表 (papers)
```python
{
    "paper_id": str,          # 唯一标识
    "title": str,             # 论文标题
    "authors": list,          # 作者列表
    "year": int,              # 发表年份
    "venue": str,             # 发表 venue (arXiv/Conference)
    "arxiv_id": str,          # arXiv ID (如果有)
    "file_path": str,         # PDF文件路径
    "category": str,          # 主题分类 (product_matching/llm_judge/...)
    "keywords": list,         # 关键词
    "abstract": str,          # 摘要
    "created_at": datetime,   # 添加时间
}
```

### 2. 论文分析表 (analysis)
```python
{
    "paper_id": str,
    "novelty": str,           # 核心创新点
    "method": str,            # 技术方法详细描述
    "architecture": str,       # 模型架构描述
    "experiments": {          # 实验相关
        "datasets": list,     # 使用的数据集
        "metrics": list,      # 评测指标
        "results": dict,      # 主要结果
        "baselines": list,    # 对比方法
    },
    "conclusions": str,       # 主要结论
    "limitations": str,       # 局限性（批判性分析）
    "related_work": list,     # 相关工作
    "citations": int,         # 引用数（如果可获取）
}
```

### 3. 技术主题表 (topics)
```python
{
    "topic_id": str,
    "topic_name": str,        # 技术主题名称
    "description": str,       # 主题描述
    "related_papers": list,   # 相关论文ID列表
    "evolution_timeline": list, # 发展时间线
}
```

### 4. 章节引用库 (chapter_references)
```python
{
    "chapter_id": int,
    "chapter_title": str,
    "citations": [
        {
            "paper_id": str,
            "usage": str,         # 如何引用（支持论点/对比/实验）
            "quote": str,         # 引用原文/核心结论
        }
    ]
}
```

## 核心功能模块

### 1. 论文导入模块
- 扫描论文目录
- 提取PDF元信息（标题、作者、年份）
- 自动分类到对应主题

### 2. 论文分析模块
使用LLM对每篇论文进行深度分析：
```
分析Prompt模板：
请分析以下论文，提取以下信息：

论文标题：{title}
论文摘要：{abstract}

请提取：
1. 核心创新点（Novelty）：
2. 技术方法（Method）：
3. 模型架构（Architecture）：
4. 实验设置：
   - 数据集：
   - 评测指标：
   - 主要结果：
5. 主要结论：
6. 局限性（请批判性分析）：
```

### 3. 主题分类模块
按章节主题自动分类论文：
- 技术演进类 → 第2章
- 知识图谱类 → 第3章
- 商品理解类 → 第4章
- 服务理解类 → 第5章
- 搜索推荐类 → 第6章
- LLM评测类 → 第7章
- 电商评测类 → 第8章

### 4. 检索查询模块
支持多种查询：
```python
# 按主题检索
query_by_topic("BERT 商品搜索")

# 按作者检索
query_by_author("Devlin")

# 按年份检索
query_by_year(2018, 2024)

# 按方法检索
query_by_method("对比学习")

# 组合检索
query_combine(topic="商品理解", method="预训练", year_range=(2020, 2024))
```

### 5. 对比分析模块
- 同类方法对比
- 不同年份发展对比
- 实验结果对比表格

### 6. 引用生成模块
为书籍写作自动生成引用：
```python
generate_citation(paper_id, style="academic")
# 输出: (Wang et al., 2019)

generate_reference_list(chapter_id)
# 输出: 该章节的完整参考文献列表
```

## 实施步骤

### Step 1: 创建知识库
```bash
mkdir -p /Users/rrp/Documents/aicode/knowledge_base/
cd /Users/rrp/Documents/aicode/knowledge_base/
```

### Step 2: 实现核心代码
创建以下文件：
- `kb_schema.py` - 数据库Schema
- `kb_importer.py` - 论文导入模块
- `kb_analyzer.py` - 论文分析模块
- `kb_query.py` - 检索查询模块
- `kb_analyzer.py` - 对比分析模块
- `kb_citation.py` - 引用生成模块

### Step 3: 运行论文分析
```bash
# 分析所有论文
python analyze_all_papers.py

# 按章节提取引用
python extract_chapter_references.py
```

### Step 4: 知识查询
```python
# 查询第2章需要的技术演进论文
chapter2_papers = query_chapter(2)

# 查询BERT相关论文及实验结果
bert_papers = query_by_method("BERT")

# 对比不同预训练模型的效果
comparison = compare_methods(["BERT", "RoBERTa", "ALBERT"])
```

## 输出格式

### 1. 论文分析结果 (JSON)
```json
{
  "paper_id": "arxiv_1908.08984",
  "title": "BERT: Pre-training of Deep Bidirectional Transformers",
  "analysis": {
    "novelty": "首次提出双向Transformer预训练+MLM任务",
    "method": "Transformer编码器+MLM+NSP",
    "experiments": {
      "datasets": ["GLUE", "SQuAD", "SNLI"],
      "metrics": ["Accuracy", "F1", "BLEU"],
      "results": {"GLUE": "78.3%", "SQuAD": "93.2%"}
    },
    "limitations": "参数量大，推理慢"
  }
}
```

### 2. 章节引用库 (Markdown)
```markdown
## 第2章引用

### 2.3.1 BERT及其变体

**核心论文：**
- (Devlin et al., 2019) BERT: Pre-training of Deep Bidirectional Transformers
  - 创新点：双向Transformer预训练
  - 实验：GLUE上达到78.3%

**对比实验：**
| 模型 | GLUE | 参数量 |
|------|------|--------|
| BERT | 78.3% | 110M |
| RoBERTa | 80.5% | 125M |
```

## 验收标准
- [ ] 所有600+篇论文都导入知识库
- [ ] 每篇论文都有完整分析结果
- [ ] 支持按章节检索相关论文
- [ ] 能生成规范的学术引用
- [ ] 能进行方法对比分析
