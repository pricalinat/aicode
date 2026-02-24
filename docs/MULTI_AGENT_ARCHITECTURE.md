# 多 Agent 系统架构设计

## 1. 目标

构建一个可扩展的多 Agent 系统，满足：

- 任务统一建模：不同 Agent 使用同一任务消息格式
- 可扩展：新增 Agent 不修改核心编排逻辑
- 可观测：每次调度都有追踪标识
- 低耦合：业务 Agent 与编排器职责分离

## 2. 核心组件

### 2.1 Message（任务消息）

用于封装用户/系统任务：

- `task_type`: 任务类型（如 `search_arxiv`）
- `content`: 任务参数（JSON-like 字典）
- `trace_id`: 追踪 ID（默认自动生成）

### 2.2 BaseAgent（Agent 抽象）

定义所有 Agent 的统一协议：

- `name`: Agent 标识
- `capabilities`: 支持的任务类型集合
- `can_handle(message)`: 判断是否能处理任务
- `handle(message)`: 处理任务并返回结构化响应

### 2.3 Orchestrator（编排器）

职责：

- 注册 Agent
- 按 `can_handle` 路由任务
- 统一返回 `AgentResponse`

当前采用简单策略：按注册顺序匹配第一个可处理 Agent。
后续可扩展为：优先级路由、多路并发、投票融合。

### 2.4 AgentResponse（统一响应）

- `agent`: 响应来源 Agent
- `success`: 是否成功
- `data`: 成功数据
- `error`: 失败原因
- `trace_id`: 调度追踪 ID

## 3. 任务流程

1. 上层系统构造 `Message`
2. `Orchestrator` 遍历已注册 Agent
3. 命中可处理 Agent 后调用 `handle`
4. Agent 执行业务逻辑并返回 `AgentResponse`
5. 上层消费结果（展示/存储/后处理）

## 4. arXiv 检索 Agent 设计

### 4.1 职责边界

- 接收论文检索参数
- 生成 arXiv 查询表达式
- 调用 arXiv Atom API
- 解析 XML 并返回结构化论文列表

### 4.2 输入参数

- `query`（必填）
- `category`（可选，如 `cs.CL`）
- `start_year` / `end_year`（可选）
- `max_results`（可选，默认 10，最大 100）
- `sort_by`（`relevance | lastUpdatedDate | submittedDate`）
- `sort_order`（`ascending | descending`）

### 4.3 输出结构（每篇论文）

- `id`
- `title`
- `summary`
- `authors`
- `published`
- `updated`
- `pdf_url`
- `categories`
- `primary_category`

## 5. 扩展方案

新增 Agent（例如 `CodeSearchAgent`）仅需：

1. 继承 `BaseAgent`
2. 定义 `name` 与 `capabilities`
3. 实现 `handle`
4. 在启动时注册到 `Orchestrator`

无需修改现有 Agent 与编排器核心逻辑。
