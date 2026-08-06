# pipeline — Workflow Orchestration

## Purpose
串联多个技能/命令成一条流水线，前一步的输出自动传给下一步。底层用 taskflow 存储状态。

## When to use
- 需要"做完 A → 拿结果 → 做 B → 再传给 C"
- 手动串联太繁琐，想定义一次、复用多次
- 配合 scheduler/event-watcher 实现无人值守流程

## Usage

### 定义一条 pipeline
```bash
pipeline define <name> --steps '[
  {"name":"fetch","skill":"web_fetch","input":"{{trigger.url}}"},
  {"name":"summarize","skill":"summarize","input":"{{fetch.output}}"},
  {"name":"notify","tool":"message","params":{"action":"send","message":"{{summarize.output}}"}}
]'
```

### 执行 pipeline
```bash
pipeline run <name> --input '{"url":"https://example.com"}'
```

### 列出所有 pipeline
```bash
pipeline list
```

### 查看执行历史
```bash
pipeline history <name> --limit 10
```

## How it works

1. **定义阶段**：
   - 每个 step 可以是 `skill`（调用已有技能）、`tool`（直接调工具）、或 `exec`（跑命令）
   - 支持模板变量 `{{step_name.output}}` 引用前序步骤结果
   - 定义存在 `~/.openclaw/workspace/pipelines/<name>.json`

2. **执行阶段**：
   - 创建一个 taskflow job，每个 step 是一个 child task
   - 按顺序执行，传递上下文
   - 失败时可配置重试/跳过/中止策略

3. **状态管理**：
   - taskflow 负责持久化、断点续跑
   - pipeline 只是定义层，不自己存储运行时状态

## Implementation

### 文件结构
```
~/.openclaw/workspace/skills/pipeline/
├── SKILL.md          # 本文件
├── define.js         # 定义/验证 pipeline
├── run.js            # 执行 pipeline（调 taskflow）
├── list.js           # 列出所有 pipeline
└── history.js        # 查看执行历史
```

### 核心逻辑（run.js 伪代码）
```javascript
// 1. 加载 pipeline 定义
const def = JSON.parse(fs.readFileSync(`pipelines/${name}.json`));

// 2. 创建 taskflow job
const job = await taskflow.create({
  name: `pipeline:${name}`,
  context: input
});

// 3. 为每个 step 创建 child task
for (const step of def.steps) {
  const task = await job.addChild({
    name: step.name,
    action: step.skill || step.tool || step.exec,
    input: resolveTemplate(step.input, job.context)
  });
  
  // 等待完成，更新 context
  await task.wait();
  job.context[step.name] = { output: task.result };
}

// 4. 返回最终结果
return job.context;
```

## Integration points

- **scheduler**: `cron add --command "pipeline run daily-report"`
- **event-watcher**: `watch /data --on-change "pipeline run process-new-files"`
- **taskflow**: 所有运行时状态存在 taskflow jobs 里，可用 `taskflow list` 查看

## Error handling
- Step 失败时，默认中止整条 pipeline
- 可配置 `continueOnError: true` 跳过失败步骤
- 支持 `retryCount` 和 `retryDelayMs`

## Examples

### 示例1：每日新闻摘要
```json
{
  "name": "daily-news",
  "steps": [
    {"name":"fetch","skill":"web_fetch","input":"https://news.ycombinator.com"},
    {"name":"summarize","skill":"summarize","input":"{{fetch.output}}"},
    {"name":"send","tool":"message","params":{"action":"send","message":"📰 Today's HN summary:\n{{summarize.output}}"}}
  ]
}
```

### 示例2：文件处理流水线
```json
{
  "name": "process-uploads",
  "steps": [
    {"name":"list","exec":"ls /uploads/*.pdf"},
    {"name":"extract","skill":"pdf","input":"{{list.output}}"},
    {"name":"classify","skill":"oracle","input":"Classify these documents:\n{{extract.output}}"},
    {"name":"move","exec":"mv {{list.output}} /processed/"}
  ]
}
```

## Notes
- Pipeline 定义是纯数据（JSON），不是代码，便于版本控制和分享
- 复杂逻辑用 taskflow 直接写更灵活；pipeline 适合简单串联
- 未来可扩展：条件分支、并行执行、子 pipeline 调用
