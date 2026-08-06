# Agnes AI Models Skill

## Overview

This skill provides instructions for integrating Agnes AI text, image, video, and agent models through the OpenAI-compatible API gateway.

## Models

### Text Models

| Model | Endpoint | Use Cases |
|-------|----------|-----------|
| `agnes-2.0-flash` | `/v1/chat/completions` | Chat, coding, reasoning, tools, streaming, image understanding, agent workflows |
| `agnes-2.5-flash` | `/v1/chat/completions` | Advanced reasoning, coding, complex tasks (recommended for new text tasks) |

### Image Models

| Model | Endpoint | Use Cases |
|-------|----------|-----------|
| `agnes-image-2.0-flash` | `/v1/images/generations` | Fast text-to-image, image-to-image generation |
| `agnes-image-2.1-flash` | `/v1/images/generations` | Higher quality image generation and editing |

### Video Models

| Model | Endpoint | Use Cases |
|-------|----------|-----------|
| `agnes-video-v2.0` | `/v1/videos` | Text-to-video, image-to-video, multi-image video, keyframe animation |

## Base URLs

- OpenAI-compatible API: `https://apihub.agnes-ai.cn/v1`
- Video result polling: `https://apihub.agnes-ai.cn/agnesapi?video_id=<VIDEO_ID>`

## Integration Requirements

1. Register an Agnes Platform account: https://platform.agnes-ai.com/
2. Obtain an Agnes API key from the platform
3. Store the key as environment variable: `export AGNES_API_KEY="***"`

## Integration Workflow

### Using OpenAI SDK (Recommended for Text/Image)

```python
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.env…Y"],
    base_url="https://apihub.agnes-ai.cn/v1",
)

# Text completion with agnes-2.5-flash (recommended)
response = client.chat.completions.create(
    model="agnes-2.5-flash",
    messages=[{"role": "user", "content": "Write a short intro to Agnes AI."}],
    stream=True,
)

# Image generation
response = client.images.generate(
    model="agnes-image-2.1-flash",
    prompt="A cute fluffy puppy",
    n=1,
    size="1024x1024"
)
```

### Direct HTTP Requests (Video)

For video generation and polling, use direct HTTP calls:

```bash
# Generate video
curl -X POST https://apihub.agnes-ai.cn/v1/videos \
  -H "Authorization: Bearer $AGNES_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "agnes-video-v2.0",
    "prompt": "A sunny park with dogs playing",
    "width": 1152,
    "height": 768,
    "num_frames": 60,
    "frame_rate": 24
  }'

# Poll for video result
curl -s "https://apihub.agnes-ai.cn/agnesapi?video_id=<VIDEO_ID>" \
  -H "Authorization: Bearer $AGNES_API_KEY"
```

## Debugging

For common errors, read `references/troubleshooting.md`.

## References

- See `references/model_catalog.md` for detailed model information and limits
- See `references/agent_compatibility.md` for agent setup guidance

## Testing

Run smoke test to verify API key configuration:

```bash
python scripts/smoke_chat.py