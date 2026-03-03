# Model Routing Policy (2026-03-01)

- Primary: Claude (MiniMax-M2.5)
- Fallback: Codex
- Check interval: every 30 minutes
- Rule:
  1) Try Claude first
  2) If Claude quota/availability is exhausted, route coding tasks to Codex
  3) Every 30 minutes, probe Claude availability
  4) If Claude is back, switch routing back to Claude

- OpenClaw role:
  - Mainly orchestrate Claude/Codex workers
  - Direct tool execution mainly for Brave web access and lightweight coordination
