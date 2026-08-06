# event-watcher — Event-Driven Automation

## Purpose
监听文件变化、webhook 到来等事件,自动触发后续流程。

## When to use
- "有新文件上传就自动处理"
- "配置文件改了就重启服务"
- "收到 webhook 就跑 pipeline"

## Usage

### 监听文件夹变化
```bash
# 监听新文件
event-watcher add watch-uploads \
  --path /uploads \
  --on create \
  --command "pipeline run process-file --input '{{event.path}}'"

# 监听文件修改
event-watcher add watch-config \
  --path /etc/myapp/config.yml \
  --on modify \
  --command "exec systemctl reload myapp"
```

### 创建 webhook 端点
```bash
event-watcher add github-webhook \
  --webhook /hooks/github \
  --command "pipeline run ci-build --input '{{event.payload}}'"
```

### 列出所有 watcher
```bash
event-watcher list
```

## Integration points

- **pipeline**: `event-watcher add ... --command "pipeline run process-file"`
- **taskflow**: 触发的 command 里可以创建 taskflow job

## Examples

### 自动处理上传文件
```bash
event-watcher add auto-process \
  --path /uploads \
  --on create \
  --filter "*.pdf" \
  --command "pipeline run extract-and-classify --input '{{event.path}}'"
```

### 配置变化自动重载
```bash
event-watcher add reload-nginx \
  --path /etc/nginx/nginx.conf \
  --on modify \
  --command "exec sudo nginx -s reload"
```

## Notes
- 文件监听依赖系统工具（inotifywait/fswatch）
- 触发频率限制：同一事件 1 秒内只触发一次
- 支持模板变量 `{{event.path}}`、`{{event.payload}}`
