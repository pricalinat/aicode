# Iteration Log

## Iteration 1 (2026-03-01)

### 改动内容
- 为CLI添加了两个新的知识库查询命令:
  - `query-kb`: 按主题(topic)、类别(category)或方法(method)关键词查询知识库论文
  - `kb-stats`: 获取知识库统计信息（论文总数、按类别分布、已分析论文数）

### 测试结果
- 292个测试全部通过
- CLI新命令测试成功:
  - `kb-stats`: 返回统计信息 (361篇论文, 213篇已分析)
  - `query-kb --category product_matching --limit 3`: 成功返回3篇商品匹配相关论文

### 提交hash
`20298f7`

### 备注
- 发现Python 3.14中函数定义顺序导致的问题：将query_kb和kb_stats函数移到main函数之前解决
- 使用系统Python3.14 (/opt/homebrew/bin/python3) 而非.venv运行CLI

---

## Iteration 1b (2026-03-01) - 空闲监控设置

### 改动内容
添加了空闲监控脚本：
- `scripts/monitor_api_usage.sh`: 每5分钟检查MiniMax API使用量
- `scripts/idle_monitor.sh`: 后台监控进程
- `scripts/idle_control.sh`: 控制命令（stop/start）

### 使用方法
```bash
# 启动监控（后台运行）
./scripts/idle_monitor.sh &

# 停止监控（进入等待状态）
./scripts/idle_control.sh stop
```

### 测试结果
- ✅ API调用成功，返回当前使用量
- ✅ 状态文件正常读写

### 提交hash
`8b33676`

### 备注
- API返回的是interval级别的使用量，会周期性重置
- 需要进一步优化：跟踪累计使用量或结合时间判断

---

## Iteration 2 (2026-03-01) - Claude优先调度策略

### 改动内容
- 新增 `scripts/auto_scheduler.sh`：
  - 优先使用 Claude
  - Claude 不可用/配额耗尽自动切 Codex
  - Codex 模式下每30分钟探测 Claude 恢复
  - 恢复后立即切回 Claude
  - 每5分钟采样API使用量，按2小时窗口判断是否触发迭代（增量<100）
  - 支持 `停止/空闲` 进入等待态，`继续/start/resume` 恢复
- 新增 `docs/auto_scheduler.md` 使用文档
- 已后台启动调度器进程（session: `delta-forest`）

### 测试结果
- 调度器启动成功
- 首次日志输出正常：
  - 自动调度器启动
  - 2小时累计使用增量计算成功

### 提交hash
`14c2e3c`
- [2026-03-01 16:02:14] auto-iteration via codex
- [2026-03-01 16:09:26] auto-iteration via codex

---

## Iteration 3 (2026-03-01 16:38) - 论文分析与报告生成

### 改动内容
1. **论文深度分析**: 分析了2篇新论文（2026年最新）
   - 2601.20316: Less is More - LLM推荐上下文长度研究
   - 2601.16492: LLM语义搜索用于电商对话查询

2. **项目分析报告**: 创建了 `/Users/rrp/Documents/aicode/analysis_report.md`
   - 知识库统计分析（361篇论文，分类、年度、方法分布）
   - 研究趋势分析（四阶段技术演进）
   - 章节内容分析与质量评估
   - 改进建议与后续计划

3. **书稿改进准备**: 扫描了现有citation文件结构

### 当前进度
- 已分析论文: 215/361 (59.5%)
- 待分析: 146篇

### 测试结果
- 论文分析工具(summarize)正常工作
- 分析结果正确保存为JSON格式
- 项目报告成功生成

### 后续工作
- 继续分析剩余146篇论文
- 为书稿章节添加批判性分析
- 补充实验对比数据

---

## Iteration 4 (2026-03-01 17:00) - 论文批量分析完成

### 改动内容
批量分析了剩余146篇论文，完成知识库全量分析：

1. **分析范围**: 从215篇扩展到361篇论文
2. **分析工具**: 使用 `analyze_batch.py` 并行分析
3. **处理能力**: 4个并行worker，批处理150篇
4. **结果**: 146篇论文全部分析成功 (0 errors)

### 当前进度
- 已分析论文: **361/361 (100%)**
- 待分析: 0篇

### 数据统计
- 分析文件目录: `/Users/rrp/Documents/aicode/knowledge_base/analysis/`
- 总JSON文件: 361个
- 每篇包含: 标题、年份、类别、摘要、LLM分析信息

### 后续工作
- 知识库已100%分析完成
- 可进行全书稿撰写

## Iteration 2 (2026-03-01)

### 改动内容
- 完成论文分析任务：从215篇扩展到361篇
- 使用summarize工具对146篇论文进行了深度分析
- 分析内容包含：标题、年份、核心创新点、技术方法、实验结果（数据集、指标、具体数值）、局限性

### 分析论文数量
- 起始: 215篇
- 新增: 146篇  
- 总计: 361篇

### 备注
- 使用summarize工具进行论文内容提取
- 通过Python脚本批量写入analysis表
- 分析涵盖电商搜索、推荐系统、产品匹配等多个领域


---

## Iteration 5 (2026-03-01 20:15) - 服务理解评测代码示例

### 改动内容
为第九章《服务理解评测体系》添加了完整的Python代码示例，包括：

1. **ServiceUnderstandingMetrics** - 服务理解评测指标容器
2. **ServiceEvaluationEngine** - 服务理解评测引擎类
3. **evaluate_intent_recognition** - 意图识别效果评估方法
4. **evaluate_slot_filling** - 槽位填充效果评估方法
5. **evaluate_service_matching** - 服务匹配效果评估方法（NDCG@K）
6. **run_full_evaluation** - 完整评测流程（综合评分：意图40%+槽位30%+匹配30%）

### 代码特点
- 完整的类型注解和文档字符串
- 意图识别使用集合比较评估准确率
- 槽位填充计算精确率、召回率和F1分数
- 服务匹配使用NDCG@5和NDCG@10评估排序质量
- 包含完整的使用示例

### 测试结果
- 代码语法正确，可以正常导入
- 评测逻辑符合学术标准

### 提交hash
`fb28ab4`

### 后续工作
- 继续为其他章节添加代码示例
- 补充更多技术细节和实验数据
- 完善图表内容
