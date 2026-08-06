# api-connector — External API Integration

## Purpose
统一封装外部 API（Slack、GitHub、邮件等），处理认证、限流、重试。

## When to use
- 需要调用第三方 API（GitHub 创建 issue、Slack 发消息、发邮件）
- 需要自动重试、限流保护

## Usage

### 配置凭证
```bash
api-connector config github --token "***"
api-connector list
```

### GitHub
```bash
# 创建 issue
api-connector github create-issue \
  --repo "owner/repo" \
  --title "Bug report" \
  --body "..." \
  --labels "bug,priority-high"

# 列出 issues
api-connector github list-issues --repo "owner/repo" --state open
```

### Slack
```bash
# 发送消息
api-connector slack send \
  --channel "#general" \
  --message "Deploy completed ✅"

# 上传文件
api-connector slack upload \
  --channel "#logs" \
  --file /var/log/app.log
```

### Email
```bash
# 发送邮件
api-connector email send \
  --to "user@example.com" \
  --subject "Report" \
  --body "..." \
  --attach /reports/weekly.pdf
```

## Integration points

- **pipeline**: 在流水线中调用外部 API
- **event-watcher**: webhook 触发后推送到 Slack

## Notes
- 凭证加密存储
- 自动重试、限流保护
- 支持批量调用
