# 自动调度策略（立即生效）

## 规则
1. 优先使用 Claude
2. Claude 不可用/配额耗尽时，切换到 Codex 执行编码迭代
3. 每 30 分钟检查一次 Claude 是否恢复
4. 一旦恢复，立即切回 Claude
5. 继续做明确增量（功能/修复/测试/文档），并记录日志

## 启动
```bash
cd /Users/rrp/Documents/aicode
./scripts/auto_scheduler.sh
```

## 控制（等待/恢复）
通过控制文件（供上层消息路由写入）：
- `停止` / `空闲` / `stop` / `idle` -> 进入等待状态
- `继续` / `start` / `resume` -> 恢复运行

文件路径：`/Users/rrp/Documents/aicode/logs/idle_monitor_control`

## 日志
- 调度日志：`logs/auto_scheduler.log`
- 迭代记录：`iteration_log.md`
- 状态文件：`logs/auto_scheduler_state.json`
