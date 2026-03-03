# Model Switcher Skill - 自动模型切换

## Purpose
Monitor MiniMax quota usage and automatically switch to Codex when usage exceeds threshold.

## Monitor Script
Location: `/Users/rrp/.openclaw/workspace/monitoring/minimax_monitor.sh`

## Usage Threshold
- **Trigger**: MiniMax quota usage > 80% (1200/1500)
- **Switch to**: Codex for code writing tasks
- **Restore**: When MiniMax usage drops < 60% (900/1500)

## Current Status
- Total: 1500
- Used: 801 (53%)
- Remaining: 699
- Time left: ~18446 minutes (~12 days)

## Check Usage Command
```bash
curl -s --location 'https://www.minimaxi.com/v1/api/openplatform/coding_plan/remains' \
  --header 'Authorization: Bearer sk-cp-mjBJmxDHEHvM8jYoUnpGfUS0bJLcS6Lc6lbIXseyS7j59dEEiy3iFV1R8SiwSuF23qS7H8_Ij8xKQuteDaNefFRlrPE4lhIUj5akR0RhUTcwDLH2DkEqQR0' \
  --header 'Content-Type: application/json'
```

## Decision Logic
```
IF Used/Total > 80% THEN
    Use Codex for code tasks
ELSE IF Used/Total < 60% THEN
    Restore MiniMax
END
```

## Priority
- Always prefer MiniMax (Claude)
- Only switch to Codex when quota is running low
