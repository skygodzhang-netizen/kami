# notify — Unified Notification Layer

## Purpose
统一的通知出口。让所有流程都能推送结果。

## When to use
- Pipeline 完成后推送结果
- 监控触发后发警报
- 定时任务结束后通知

## Usage

### 发送通知
```bash
# 当前会话
notify send "Build completed ✅"

# 指定渠道
notify send "Alert!" --channel telegram --to "@vpskamibot"
notify send "Deploy done" --channel slack --to "#deploys"
notify send "Report" --channel email --to "team@example.com"

# 带附件
notify send "Log" --attach /var/log/app.log

# 批量通知
notify send "Update" --to "telegram:@user1,slack:#team,email:admin@example.com"
```

### 配置
```bash
# 默认渠道
notify config --default "telegram:@vpskamibot"

# 回退渠道
notify config --fallback "email:admin@example.com"

# 静默时段
notify config --quiet-hours "23:00-08:00"
```

## Integration points

所有技能都应该用 `notify` 推送结果：
- **pipeline**: 最后一步用 `notify send`
- **scheduler**: 定时任务完成后调 `notify`
- **data-monitor**: 检测到变化用 `notify`

## Examples

### Pipeline 完成通知
```json
{
  "name": "daily-report",
  "steps": [
    {"name":"fetch","skill":"web_fetch","input":"..."},
    {"name":"summarize","skill":"summarize","input":"{{fetch.output}}"},
    {"name":"notify","skill":"notify","action":"send","params":{"message":"📊 {{summarize.output}}"}}
  ]
}
```

## Notes
- 默认用当前会话渠道
- 失败自动尝试 fallback
- 支持静默时段配置
