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
 "video_model": "agnes-video-v2.0",
 "api_key": "sk-oCwMPTJpZc9uWLlZeimvbcXPsSiZUg5ZWTjjlJjxzPrYLS42"
}
⚠️ API key 是完整值，实际 curl 请求中直接使用，不要脱敏。
```

## 图片生成
当用户要求生成图片时，使用以下步骤：

### 步骤 1：生成图片
```bash
curl -s --connect-timeout 15 --max-time 120 -X POST https://apihub.agnes-ai.cn/v1/images/generations \
  -H "Authorization: Bearer sk-oCwMPTJpZc9uWLlZeimvbcXPsSiZUg5ZWTjjlJjxzPrYLS42" \
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
当用户要求生成视频时，使用 Agnes-Video-V2.0 模型。

### 步骤 1：创建视频任务
```bash
curl -s -X POST https://apihub.agnes-ai.cn/v1/videos \
  -H "Authorization: Bearer sk-oCwMPTJpZc9uWLlZeimvbcXPsSiZUg5ZWTjjlJjxzPrYLS42" \
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
返回结果中包含 `video_id`。

### 步骤 2：查询视频结果（长轮询 + 重试）
```bash
curl -s -X GET "https://apihub.agnes-ai.cn/agnesapi?video_id=<VIDEO_ID>" \
  -H "Authorization: Bearer sk-oCwMPTJpZc9uWLlZeimvbcXPsSiZUg5ZWTjjlJjxzPrYLS42"
```
**长轮询机制：** 视频生成需要较长时间。每 30 秒轮询一次状态，最多轮询 120 次（约 1 小时）。检查返回状态直到完成。

### 参数说明
- **model**: `agnes-video-v2.0`
- **prompt**: 视频内容描述
- **height/width**: 分辨率，默认 768x1152（竖屏），可选 16:9/9:16/1:1/4:3/3:4
- **num_frames**: 帧数，≤441，满足 8n+1
- **frame_rate**: FPS，1-60
- **image**: 可选，图生视频用
- **extra_body.image**: 可选，多图视频用
- **extra_body.mode**: `keyframes` 关键帧模式

### 支持模式
- 文生视频（text-to-video）
- 图生视频（image-to-video）
- 多图视频生成
- 关键帧动画

### 步骤 3：下载视频到工作区并发送
视频完成后下载到工作区：
curl -sL "<视频URL>" -o /root/.openclaw/workspace/<文件名>.mp4
使用 message 工具的 attachments 参数发送视频，media 路径必须是 /root/.openclaw/workspace/ 下的文件。

### 步骤 4：清理（必须执行）
发送成功后立即删除：
rm /root/.openclaw/workspace/<文件名>.mp4
发完务必清理，不要在工作区残留视频文件。

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
