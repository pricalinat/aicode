# 自动调度策略（立即生效）

## 概述

自动调度器（Auto Scheduler）是一个后台运行的智能调度系统，用于在 Codex 审计模式下持续自动地改进项目。它监控 API 使用量，根据预设策略在 Claude 和 Codex 之间自动切换，并执行代码迭代任务。

## 规则

1. **优先使用 Claude**：默认情况下，调度器优先使用 Claude 模型进行代码迭代
2. **自动切换**：当 Claude 不可用或配额耗尽时，自动切换到 Codex 执行编码迭代
3. **恢复检测**：每 30 分钟检查一次 Claude 是否已恢复
4. **立即恢复**：一旦检测到 Claude 恢复，立即切回 Claude 模式
5. **增量工作**：继续做明确增量（功能/修复/测试/文档），并记录日志

## 工作流程

```
┌─────────────────────────────────────────────────────────┐
│                    调度器主循环                          │
├─────────────────────────────────────────────────────────┤
│  1. 检查 API 使用量                                     │
│     ↓                                                   │
│  2. 判断是否触发迭代（2小时窗口增量<100）              │
│     ↓                                                   │
│  3. 如果触发：                                          │
│     ├─ Claude 可用 → 执行 Claude 迭代                   │
│     └─ Claude 不可用 → 切换到 Codex                     │
│     ↓                                                   │
│  4. 执行改进任务                                        │
│     ├─ 代码质量提升                                      │
│     ├─ 文档完善                                          │
│     ├─ 属性库扩展                                        │
│     └─ 书籍优化                                          │
│     ↓                                                   │
│  5. git add → commit → push                            │
│     ↓                                                   │
│  6. 等待 5 分钟                                         │
│     ↓                                                   │
│  7. 继续循环                                            │
└─────────────────────────────────────────────────────────┘
```

## 启动

```bash
cd /Users/rrp/Documents/aicode
./scripts/auto_scheduler.sh &
```

查看日志：
```bash
tail -f logs/auto_scheduler.log
```

## 控制（等待/恢复）

通过控制文件（供上层消息路由写入）：
- `停止` / `空闲` / `stop` / `idle` → 进入等待状态
- `继续` / `start` / `resume` → 恢复运行

文件路径：`/Users/rrp/Documents/aicode/logs/idle_monitor_control`

```bash
# 停止调度器
echo "停止" > /Users/rrp/Documents/aicode/logs/idle_monitor_control

# 恢复调度器
echo "继续" > /Users/rrp/Documents/aicode/logs/idle_monitor_control
```

## 日志

- **调度日志**：`logs/auto_scheduler.log` - 详细调度信息
- **迭代记录**：`iteration_log.md` - 每次迭代的改动内容
- **状态文件**：`logs/auto_scheduler_state.json` - 当前状态

## 状态文件格式

```json
{
  "last_mode": "claude",
  "current_mode": "codex",
  "last_check": "2026-03-02T23:30:00",
  "usage_2h": 150,
  "idle_triggered": false
}
```

## 改进方向

调度器会优先处理以下方向的改进：

1. **书籍深度优化** - 添加实验数据、完善章节内容
2. **属性库扩展** - 补充缺失的业务属性
3. **代码质量提升** - 改进测试覆盖、优化代码结构
4. **文档完善** - 补充技术文档、使用说明

## 故障排查

### 调度器不启动
```bash
# 检查脚本权限
ls -la scripts/auto_scheduler.sh

# 手动启动
bash scripts/auto_scheduler.sh
```

### 状态文件错误
```bash
# 查看状态文件
cat logs/auto_scheduler_state.json

# 重置状态
echo '{"last_mode":"claude","current_mode":"claude"}' > logs/auto_scheduler_state.json
```

### 日志无输出
```bash
# 检查日志文件
ls -la logs/auto_scheduler.log

# 手动创建日志目录
mkdir -p logs
```
