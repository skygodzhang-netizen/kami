# Agnes AI Agent Compatibility

This file provides guidance for integrating Agnes AI with various agent frameworks.

## Supported Agents

### Codex

Codex can install the skill directly by referencing this directory:

```bash
python /path/to/install-skill-from-github.py \
  --repo AgnesAI-Labs/skills \
  --path agnes-ai-models
```

After installation, use the `agnes-ai-models` skill in your workflows.

### Hermes

Hermes can import the skill files as instructions and configure the Agnes endpoint as an OpenAI-compatible provider. Set the following parameters:

- Base URL: `https://apihub.agnes-ai.cn/v1`
- API Key: `AGNES_API_KEY` environment variable

### Manus

Import or reference the Markdown files as knowledge/instructions, then configure Agnes API access through a custom OpenAI-compatible provider if supported.

### Custom agents

Use the model catalog and troubleshooting references to configure calls against the Agnes API gateway.

## Provider Settings

Use these defaults unless the target agent requires different field names:

| Setting | Value |
| --- | --- |
| Provider type | OpenAI-compatible |
| Base URL | `https://apihub.agnes-ai.cn/v1` || API key | User-provided Agnes API key |
| API key environment variable | `AGNES_API_KEY` |
| Chat model | `agnes-2.0-flash` (use `agnes-2.5-flash` for new tasks) |
| Image models | `agnes-image-2.0-flash`, `agnes-image-2.1-flash` |
| Video model | `agnes-video-v2.0` |

## Recommended Agent Instruction

Use this instruction when adding Agnes AI to another agent:

```text
Use Agnes AI through the OpenAI-compatible API gateway.
Base URL: https://apihub.agnes-ai.cn/v1
Read the Agnes AI skill documentation from:
https://github.com/AgnesAI-Labs/skills/tree/main/agnes-ai-models
Before making requests, confirm the user has registered on Agnes Platform and has an API key.
Never expose API keys, bearer tokens, private logs, screenshots containing secrets, or customer data.
For model choices, use agnes-2.5-flash for chat, agnes-image-2.1-flash for image generation and editing, agnes-image-2.0-flash for fast image generation, and agnes-video-v2.0 for video generation.
```

## Notes

- Model availability, rate limits, context windows, and quota rules may change. Confirm production-critical values in the official docs or Agnes Platform console.
- For common errors and retry guidance, read `troubleshooting.md`.