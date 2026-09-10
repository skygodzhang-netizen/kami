## Ubuntu AI Server Runtime (OpenClaw)

- This agent runs on Ubuntu AI Server.
- Hostname: ubuntu-ai
- IP: 192.168.100.108
- OpenClaw Gateway port: 18789

## iStoreOS Router Management

- Host: iStoreOS router
- IP: 192.168.100.1
- SSH access:

`ssh root@192.168.100.1`

- Management:
  - System status
  - OpenClash
  - Docker
  - Logs
  - Service restart

## Available Skills

- `summarize`: Summarize URLs/files (web/PDF/images/audio/YouTube).
- `healthcheck`: Host security hardening/exposure review/risk posture.
- `oracle`: Second-model review/debug with bundled prompt+files.
- `mcporter`: Manage/auth/call MCP servers/tools (HTTP or stdio).

## 图片和视频配置
```json
{
 "api_base_url": "https://apihub.agnes-ai.cn/v1",
 "image_model": "agnes-image-2.1-flash",
 "video_model": "agnes-video-2.5-flash",
 "video_fallback": "agnes-video-v2.0",
 "api_key": "sk-dV4Ek64MnTqVL8YwKc8VXeiGonIDVYXE30LVoSIxKKu8SMQ8"
}
⚠️ API key 是完整值，实际 curl 请求中直接使用，不要脱敏。
```

### 可用模型（2026-09-09 已验证）
- 图片: `agnes-image-2.0-flash` / `agnes-image-2.1-flash` / `agnes-image-2.5-flash`（POST /v1/images/generations，参数规范相同，换 model 即可）
- 视频: `agnes-video-2.5-flash`（新规范，优先）/ `agnes-video-v2.0`（经典规范，fallback）
- 免费层连续请求易触发 429，务必串行 + 间隔 ≥12s

## 图片生成
**重要（2026-09-10 验证）：不要用内置 `image_generate` 工具出 Agnes 图。**
OpenClaw 的 OpenAI 兼容 parser 解析 Agnes 图片响应会报 `response malformed`（key/网络都正常，是 OpenClaw 侧适配问题）。一律按下面步骤 **curl 直连 Agnes API** 出图。
默认模型用 `agnes-image-2.5-flash`（可换 2.0/2.1，参数规范相同）。

当用户要求生成图片时，使用以下步骤：

### 步骤 1：生成图片
```bash
curl -s --connect-timeout 15 --max-time 120 -X POST https://apihub.agnes-ai.cn/v1/images/generations \
  -H "Authorization: Bearer sk-dV4Ek64MnTqVL8YwKc8VXeiGonIDVYXE30LVoSIxKKu8SMQ8" \
  -H "content-type: application/json" \
  -d '{"model":"agnes-image-2.1-flash","prompt":"用户的描述","size":"1024x1024","extra_body":{"response_format":"url"}}'
```
**重试机制：** 如果返回 503 (服务繁忙) 或其他非 content_policy_violation 错误，等待 30 秒后重试，最多重试 3 次。超时增加到 120 秒（图片生成可能较慢）。

从返回结果中提取 `data[0].url`。

### 步骤 2：下载图片到工作区
```bash
curl -sL "<图片URL>" -o /root/.openclaw/workspace/<文件名>.png
```

### 步骤 3：通过 message 工具发送
使用 `message` 工具的 `attachments` 参数发送图片，media 路径必须是 `/root/.openclaw/workspace/` 下的文件。

### 步骤 4：清理
发送成功后立即删除：
```bash
rm /root/.openclaw/workspace/<文件名>.png
```

⚠️ 注意：
- 图片内容必须符合安全规范（不能包含成人/裸露/暴力等违规内容），否则 API 会返回 `content_policy_violation` 错误
- 文件必须放在 `/root/.openclaw/workspace/` 才能通过 message 工具发送
- 发完务必清理，不要在工作区残留图片文件

## 视频生成
当用户要求生成视频时，优先使用 `agnes-video-2.5-flash`（按新规范，下方"2.5-flash 调用规范"），不可用时回退 `agnes-video-v2.0`（经典规范，下方"v2.0 调用规范"）。

### 查询端点（重要）
- 提交任务: POST /v1/videos
- 查询状态: GET /v1/videos/{video_id}  （注意：是 /v1/videos/ 不是 /agnesapi）
- 视频下载: 从返回的 `metadata.url` 字段获取（2.5-flash 顶层无 url 字段；v2.0 经典查询以实际返回为准）
- 成功判据: 顶层 `status=completed`（2.5-flash 下载地址在 `metadata.url`，不要依赖 internal_status）

### API Key
⚠️ 使用完整 API Key，不要脱敏。

---

### 2.5-flash 调用规范（优先）
**已验证参数（2026-09-09，勿再自行猜测）：**
- `mode`: **必填**，只接受 `text` / `keyframe` / `reference`（不要用 i2v）
- `size`: 只能用 `"720P"`
- `seconds`: 字符串，范围 `"4"`–`"12"`
- `aspect_ratio`: 宽高比（替代 height/width）
- **禁止发送**: `height`、`width`、`num_frames`、`frame_rate`

#### 步骤 1：创建任务
```bash
curl -s -X POST https://apihub.agnes-ai.cn/v1/videos \
  -H "Authorization: Bearer <API_KEY>" \
  -H "content-type: application/json" \
  -d '{
    "model": "agnes-video-2.5-flash",
    "mode": "text",
    "prompt": "视频描述",
    "size": "720P",
    "seconds": "6",
    "aspect_ratio": "9:16"
  }'
```
返回中包含 `video_id`。keyframe/reference 模式附加 `image` 字段（参考图）。

#### 步骤 2：轮询（必须带 model_name）
```bash
curl -s -X GET "https://apihub.agnes-ai.cn/v1/videos/<VIDEO_ID>?model_name=agnes-video-2.5-flash" \
  -H "Authorization: Bearer <API_KEY>"
```
- 每 30 秒轮询一次，实际完成约 90 秒
- 成功 = 顶层 `status=completed`；下载地址在 **`metadata.url`**（顶层**没有** `url` 字段，不要读顶层 url）
- 429（免费层限流）→ 等 30s+ 重试，**不算配置错误**

---

### v2.0 调用规范（fallback，经典参数）

#### 步骤 1：创建任务
```bash
curl -s -X POST https://apihub.agnes-ai.cn/v1/videos \
  -H "Authorization: Bearer <API_KEY>" \
  -H "content-type: application/json" \
  -d '{
    "model": "agnes-video-v2.0",
    "prompt": "视频描述",
    "height": 768,
    "width": 1152,
    "num_frames": 121,
    "frame_rate": 24
  }'
```
返回中包含 `video_id`。

#### 步骤 2：轮询
```bash
curl -s -X GET "https://apihub.agnes-ai.cn/agnesapi?video_id=<VIDEO_ID>" \
  -H "Authorization: Bearer <API_KEY>"
```
- 实际完成约 60 秒；成功 = 顶层 `status=completed` 且存在 `url`

#### v2.0 参数说明
- **prompt**: 视频内容描述
- **height/width**: 分辨率，默认 768x1152（竖屏），可选 16:9/9:16/1:1/4:3/3:4
- **num_frames**: 帧数，≤441，满足 8n+1
- **frame_rate**: FPS，1-60
- **image**: 可选，图生视频用

### 支持模式（v2.0）
- 文生视频（text-to-video）
- 图生视频（image-to-video）
- 多图视频生成
- 关键帧动画

### 通用：下载与发送

### 步骤 3：下载视频到工作区
视频完成后下载到工作区：
curl -sL "<视频URL>" -o /root/.openclaw/workspace/<文件名>.mp4
⚠️ 必须先下载再发送，不要先发送。

### 步骤 4：通过 message 工具发送
使用 `message` 工具的 `attachments` 参数发送视频：
```json
{
  "media": "/root/.openclaw/workspace/<文件名>.mp4",
  "mimeType": "video/mp4",
  "name": "<文件名>.mp4"
}
```
⚠️ media 路径必须是 `/root/.openclaw/workspace/` 下的文件。

### 步骤 5：清理（必须执行）
**只有确认 message 发送成功后**才能删除：
```bash
rm /root/.openclaw/workspace/<文件名>.mp4
```
⚠️ 如果发送失败，不要删除视频文件，保留供重试。

## ElevenLabs TTS 配置

API Key 存储在 `config/elevenlabs.json`

### 使用方式
```bash
curl -s -X POST "https://api.elevenlabs.io/v1/text-to-speech/<voice_id>" \
  -H "xi-api-key: <API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"text":"文本内容"}' -o <output_file> -w "%{http_code}"
```

### 常用声音 ID
- Adam (男, 坚定): pNInz6obpgDQGcFmaJgB
- Bella (女, 专业明亮): hpp4J3VqNfWAUOO0d1Us
- Sarah (女, 成熟稳重): EXAVITQu4vr4xnSDxMaL
- Brian (男, 深沉): nPczCjzI2devNBz1zQrb

声音列表: curl -s "https://api.elevenlabs.io/v1/voices" -H "xi-api-key: <API_KEY>"

### 当前账户状态
- 订阅: 免费版 (10,000 字符/月)
- 当前已用: ~256 字符
