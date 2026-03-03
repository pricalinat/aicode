# Agent Autopilot Skill - 持续自动运行

## 功能
让 OpenClaw Agent 持续自动运行任务

## 核心机制

### 1. Heartbeat (心跳)
OpenClaw 内置的心跳机制，可以定期触发任务：
```bash
# 设置心跳触发
openclaw cron add --name "my-task" --pattern "*/5 * * * *" --task "do something"
```

### 2. Wake Mode
- `wakeMode: "next-heartbeat"` - 下次心跳时唤醒
- `wakeMode: "now"` - 立即执行

### 3. 自循环模式
Agent 完成任务后自动启动下一轮：
```
Loop:
  1. 执行任务
  2. 报告进度
  3. 等待心跳/定时
  4. 继续循环
```

## 使用方法

### 配置心跳任务
```bash
# 每5分钟运行一次
openclaw cron add --name "auto-task" --pattern "*/5 * * * *" --message "执行任务"

# 每小时运行一次  
openclaw cron add --name "hourly-task" --pattern "0 * * * *" --message "执行任务"
```

### 在 Skill 中使用
```python
async def run():
    while True:
        # 执行任务
        await do_work()
        
        # 报告进度
        report_progress()
        
        # 等待下一次触发
        await heartbeat.wait()
```

## 监控
- 查看运行状态：`openclaw cron list`
- 查看日志：`openclaw logs`
- 停止任务：`openclaw cron remove <name>`

## Source
- https://github.com/openclaw/skills/tree/main/skills/edoserbia/agent-autopilot
- https://docs.openclaw.ai/automation/cron-vs-heartbeat
