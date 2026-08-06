# scheduler — Cron Wrapper for Skills

## Purpose
给任何技能/pipeline 加定时触发能力。封装 OpenClaw 的 `cron` 工具，提供更友好的接口。

## When to use
- "每天早上 8 点运行 summarize"
- "每小时检查一次网页变化"
- 让 pipeline 无人值守地跑

## Usage

### 添加定时任务
```bash
# 每天 8:00 运行
scheduler add daily-summary --cron "0 8 * * *" --command "pipeline run daily-news"

# 每 1 小时
scheduler add hourly-check --every 1h --command "data-monitor check prices"

# 一次性任务（指定时间）
scheduler add one-time --at "2026-06-18T10:00:00Z" --command "notify send 'Meeting in 10min'"
```

### 列出所有任务
```bash
scheduler list
```

### 暂停/恢复/删除
```bash
scheduler pause daily-summary
scheduler resume daily-summary
scheduler remove daily-summary
```

### 查看执行历史
```bash
scheduler history daily-summary --limit 5
```

### 立即执行一次（测试用）
```bash
scheduler run daily-summary
```

## How it works

1. **输入层**：接收友好的时间表达式
   - `--cron "0 8 * * *"` → 标准 cron 表达式
   - `--every 1h` / `30m` / `1d` → 自动转为 everyMs
   - `--at "2026-06-18T10:00:00Z"` → ISO 时间戳

2. **转换层**：翻译成 OpenClaw cron 的 job 对象
3. **执行层**：调用 `cron(action=add)` 创建 job

## Integration points

- **pipeline**: `scheduler add daily-report --cron "0 9 * * *" --command "pipeline run daily-news"`
- **taskflow**: scheduler 创建的 job 里可以跑 taskflow

## Examples

### 每天早上 8 点推送新闻摘要
```bash
scheduler add morning-news \
  --cron "0 8 * * *" \
  --tz "Asia/Shanghai" \
  --command "pipeline run daily-news"
```

### 每 30 分钟检查价格变化
```bash
scheduler add price-watch \
  --every 30m \
  --command "data-monitor check https://example.com/price"
```

## Notes
- scheduler 只是 cron 的语法糖，底层完全用 OpenClaw cron
- 任务都跑在 isolated session，不污染主会话
- 时区默认 UTC，建议显式指定 `--tz "Asia/Shanghai"`
