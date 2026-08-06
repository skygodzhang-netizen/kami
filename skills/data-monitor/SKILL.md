# data-monitor — Change Detection & Monitoring

## Purpose
定期抓取网页/API/文件,对比上次结果,有变化才触发后续动作。

## When to use
- 监控价格变化
- 跟踪网页更新
- API 数据变化通知
- 配置文件漂移检测

## Usage

### 添加监控
```bash
# 监控网页
data-monitor add price-watch \
  --url "https://example.com/product" \
  --selector ".price" \
  --on-change "notify send 'Price: {{change.old}} → {{change.new}}'"

# 监控 API
data-monitor add api-watch \
  --url "https://api.example.com/status" \
  --jsonpath "$.status" \
  --on-change "notify send 'Status: {{change.new}}'"

# 监控文件
data-monitor add config-watch \
  --file /etc/myapp/config.yml \
  --on-change "exec systemctl reload myapp"
```

### 手动检查
```bash
data-monitor check price-watch
```

### 查看历史
```bash
data-monitor history price-watch --limit 10
```

## Integration points

- **scheduler**: `scheduler add price-check --every 10m --command "data-monitor check price-watch"`
- **pipeline**: 在流水线中检查变化并决定后续步骤

## Examples

### 监控价格+定时检查
```bash
data-monitor add laptop-price \
  --url "https://shop.example.com/laptop" \
  --selector ".price-current" \
  --on-change "notify send '💰 Price: {{change.old}} → {{change.new}}'"

scheduler add laptop-check --every 1h --command "data-monitor check laptop-price"
```

## Notes
- 抓取频率建议 ≥5 分钟
- 历史记录默认保留 90 天
- 支持容错（忽略空格、大小写）
