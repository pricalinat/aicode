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
