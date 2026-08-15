# OpenClaw 桌面端完整部署指南

> 目标：在你自己的电脑上跑出一个和我一样的 OpenClaw 实例——Gateway 常驻后台、Telegram 接入、skills、memory、cron、browser、nodes 全部就绪。

---

## 一、系统要求

| 项目 | 最低要求 | 推荐 |
|------|---------|------|
| 操作系统 | macOS 12+ / Ubuntu 20+ / Windows 10+ | macOS 14+ / Ubuntu 22+ / Windows 11 |
| Node.js | 22.19+ | 24（安装脚本自动处理） |
| 内存 | 4 GB | 8 GB+ |
| 磁盘 | 2 GB | 5 GB+ |
| 网络 | 需访问 AI 模型 API | 稳定连接 |

---

## 二、安装 OpenClaw

### macOS / Linux / WSL2

```bash
curl -fsSL https://openclaw.ai/install.sh | bash
```

### Windows（原生 PowerShell）

以管理员身份打开 PowerShell：

```powershell
iwr -useb https://openclaw.ai/install.ps1 | iex
```

### Windows（推荐 WSL2）

```powershell
# 1. 启用 WSL2
wsl --install -d Ubuntu-24.04

# 2. 启用 systemd
sudo tee /etc/wsl.conf >/dev/null <<'EOF'
[boot]
systemd=true
EOF

# 3. 重启 WSL
wsl --shutdown

# 4. 进入 WSL 安装
wsl
curl -fsSL https://openclaw.ai/install.sh | bash
```

---

## 三、引导配置（onboarding）

安装完成后运行：

```bash
openclaw onboard --install-daemon
```

交互式向导会引导你：

1. **选择模型提供商** — 输入你的 API Key
2. **选择模型** — 指定主模型和备用模型
3. **配置 Gateway** — 安装为系统服务（开机自启）

> 常用 API Key 来源：
> - Anthropic (Claude): https://console.anthropic.com
> - OpenAI (GPT): https://platform.openai.com
> - Google (Gemini): https://aistudio.google.com
> - OpenRouter (多模型): https://openrouter.ai
> - MiniMax: 你的提供商控制台

---

## 四、配置 Telegram 频道

### 1. 创建 Bot

在 Telegram 找 **@BotFather**，发送 `/newbot`，按提示设置名字和用户名，拿到 Bot Token。

### 2. 获取你的 Telegram User ID

发消息给你的 bot，然后运行：

```bash
openclaw logs --follow
```

在日志中找到 `from.id`（一串数字），这就是你的 Telegram 用户 ID。

### 3. 配置 Telegram

编辑 `~/.openclaw/openclaw.json`：

```json5
{
  channels: {
    telegram: {
      enabled: true,
      botToken: "你的BOT_TOKEN",
      dmPolicy: "allowlist",
      allowFrom: ["你的TELEGRAM_USER_ID"],
      groups: {
        "*": { requireMention: true }
      }
    }
  }
}
```

### 4. 重启 Gateway

```bash
openclaw gateway restart
```

---

## 五、完整配置文件模板

以下为 `~/.openclaw/openclaw.json` 的完整参考配置，包含所有核心功能模块。按需修改：

```json5
{
  // ========== 代理设置（中国网络环境可能需要） ==========
  // 如果无法直连 Telegram API 或模型 API，取消下面注释并填入代理地址
  // "http_proxy": "socks5://127.0.0.1:1080",
  // "https_proxy": "socks5://127.0.0.1:1080",

  // ========== 环境变量（API Keys） ==========
  env: {
    // 在这里填入你的模型 API Key
    // ANTHROPIC_API_KEY: "sk-ant-...",
    // OPENAI_API_KEY: "sk-...",
    // GOOGLE_GENERATIVE_AI_API_KEY: "AIza...",
    // OPENROUTER_API_KEY: "sk-or-...",
    // 或者用 SecretRef 引用环境变量
    // ANTHROPIC_API_KEY: { source: "env", provider: "default", id: "ANTHROPIC_API_KEY" }
  },

  // ========== Gateway 配置 ==========
  gateway: {
    port: 18789,
    bind: "loopback",       // 仅本机访问；如需局域网访问改为 "lan"
    auth: {
      mode: "token",        // token / password / none
      token: "你的网关密钥"   // 用于 Control UI 和 API 认证
    },
    controlUi: {
      enabled: true         // 浏览器访问 http://127.0.0.1:18789 的管理界面
    }
  },

  // ========== Agent 配置 ==========
  agents: {
    defaults: {
      workspace: "~/.openclaw/workspace",

      // 主模型
      model: {
        primary: "anthropic/claude-sonnet-4-6",
        // fallbacks: ["openai/gpt-5.4", "google/gemini-2.5-pro"]
      },

      // 会话管理
      session: {
        dmScope: "per-channel-peer",
        reset: {
          mode: "daily",    // 每天重置会话
          atHour: 4,        // 凌晨4点
          idleMinutes: 120  // 空闲2小时后也重置
        }
      },

      // 心跳检查（定期自检）
      heartbeat: {
        every: "30m",
        target: "last"
      },

      // 消息设置
      messages: {
        visibleReplies: "automatic",
        groupChat: {
          visibleReplies: "message_tool",
          unmentionedInbound: "room_event"
        }
      }
    }
  },

  // ========== 频道配置 ==========
  channels: {
    // Telegram
    telegram: {
      enabled: true,
      botToken: "你的BOT_TOKEN",
      dmPolicy: "allowlist",
      allowFrom: ["你的TELEGRAM_USER_ID"],
      groups: {
        "*": { requireMention: true }
      }
    }
    // 其他频道按需添加（Signal / Discord / WhatsApp 等）
    // signal: {
    //   enabled: true,
    //   accounts: { ... }
    // }
  },

  // ========== 技能（Skills） ==========
  skills: {
    entries: {
      // 按需启用内置技能
      // peekaboo: { enabled: true }  // UI 自动化
      // gemini: { enabled: true }    // Gemini 图像分析
    }
  },

  // ========== 插件（Plugins） ==========
  plugins: {
    enabled: true,
    entries: {
      // 内置插件默认启用
    }
  },

  // ========== 浏览器控制 ==========
  browser: {
    enabled: true,
    evaluateEnabled: true
  },

  // ========== MCP 服务器（可选） ==========
  // mcp: {
  //   servers: {
  //     docs: {
  //       command: "npx",
  //       args: ["-y", "@modelcontextprotocol/server-fetch"]
  //     }
  //   }
  // }
}
```

---

## 六、工作区初始化

安装脚本会自动创建工作区 `~/.openclaw/workspace/`，但你还需要创建核心文件：

```bash
mkdir -p ~/.openclaw/workspace/memory

# 创建 SOUL.md — Agent 人格定义
cat > ~/.openclaw/workspace/SOUL.md << 'EOF'
# SOUL.md

你是一个冷静直接的 AI 助手。
- 先给结论，再给细节
- 少废话，用短句、动词开头
- 允许轻微幽默，但不油不尬
- 能自己搞定的先搞定，卡住再问
- 外部动作（发消息/删除/对外）先确认
EOF

# 创建 USER.md — 关于你的信息
cat > ~/.openclaw/workspace/USER.md << 'EOF'
# USER.md

- 称呼: kami
- 语言: 中文
- 风格: 冷静、直接、靠谱
- 偏好: 先结论后细节，需要时可执行步骤/清单
EOF

# 创建 MEMORY.md — 长期记忆
cat > ~/.openclaw/workspace/MEMORY.md << 'EOF'
# MEMORY.md

## 初始设置 (2026-06-29)
- 桌面端 OpenClaw 实例建立
- 主要使用 Telegram 频道
- 模型: 按需配置
EOF

# 创建 AGENTS.md — Agent 行为规范
cat > ~/.openclaw/workspace/AGENTS.md << 'EOF'
# AGENTS.md

## 每次会话
1. 读 SOUL.md
2. 读 USER.md
3. 读 memory/ 下的最近日记
4. 主会话额外读 MEMORY.md

## 安全
- 不泄露私人数据
- 删除用 trash 而非 rm
- 不确定就问
EOF

# 创建 HEARTBEAT.md — 主动检查清单
cat > ~/.openclaw/workspace/HEARTBEAT.md << 'EOF'
# HEARTBEAT.md

- 频率: 每天早晚各一次
- 日程: 未来24-48小时事件
- 待办: 对话中提到的事项整理成清单
- 项目: 工作区 git 状态检查
- 安静时段: 23:00-08:00
EOF

# 创建 TOOLS.md — 本地工具笔记
cat > ~/.openclaw/workspace/TOOLS.md << 'EOF'
# TOOLS.md

## 本地路径
- 工作区: /root/.openclaw/workspace
- 配置: ~/.openclaw/openclaw.json
- 日志: /tmp/openclaw/
EOF
```

---

## 七、启动和验证

```bash
# 1. 检查版本
openclaw --version

# 2. 健康检查
openclaw doctor

# 3. 启动/查看 Gateway
openclaw gateway start
openclaw gateway status

# 4. 查看日志
openclaw logs --follow

# 5. 浏览器打开 Control UI
#    http://127.0.0.1:18789
```

预期输出：
- `openclaw doctor` 无红色错误
- `openclaw gateway status` 显示 Gateway 运行中，端口 18789
- 浏览器访问 Control UI 能看到管理面板
- Telegram 发消息给 Bot 能收到回复

---

## 八、Windows 特殊注意事项

### 8.1 防火墙

确保 18789 端口未被 Windows 防火墙拦截：

```powershell
# 以管理员 PowerShell 运行
New-NetFirewallRule -DisplayName "OpenClaw Gateway" -Direction Inbound -Protocol TCP -LocalPort 18789 -Action Allow
```

### 8.2 开机自启

```powershell
# 安装 Gateway 服务
openclaw gateway install
```

### 8.3 PATH 问题

如果 `openclaw` 命令找不到：

```powershell
# 查看全局 npm 路径
npm config get prefix

# 将该路径的 bin 目录加入系统 PATH
# 例如: C:\Users\<你>\AppData\Roaming\npm
```

---

## 九、常用运维命令

```bash
# 更新 OpenClaw
openclaw update

# 重新配置
openclaw configure

# 重启 Gateway
openclaw gateway restart

# 查看日志
openclaw logs --follow

# 修复配置问题
openclaw doctor --fix

# 查看当前配置
openclaw config get

# 修改单个配置项
openclaw config set agents.defaults.model.primary "anthropic/claude-sonnet-4-6"

# 停止 Gateway
openclaw gateway stop

# 完全卸载
openclaw uninstall
```

---

## 十、网络代理（中国大陆环境）

如果你的网络需要代理才能访问 Telegram API 或模型 API：

### 方法1：环境变量

在 `~/.openclaw/.env` 文件中添加：

```bash
HTTP_PROXY=http://127.0.0.1:7890
HTTPS_PROXY=http://127.0.0.1:7890
ALL_PROXY=socks5://127.0.0.1:1080
```

### 方法2：Gateway 配置

在 `openclaw.json` 中：

```json5
{
  channels: {
    telegram: {
      proxy: "socks5://127.0.0.1:1080"
    }
  }
}
```

### 方法3：系统级代理

```bash
# 在 ~/.bashrc 或 ~/.zshrc 中添加
export http_proxy=http://127.0.0.1:7890
export https_proxy=http://127.0.0.1:7890
export ALL_PROXY=socks5://127.0.0.1:1080
```

---

## 十一、快速一键脚本

如果你想一步到位，可以把以下内容保存为 `setup-openclaw.sh` 并运行：

```bash
#!/bin/bash
set -e

echo "=== OpenClaw 桌面端安装 ==="
echo ""

# 1. 安装 OpenClaw
echo "[1/6] 安装 OpenClaw..."
curl -fsSL https://openclaw.ai/install.sh | bash

# 2. 创建工作区
echo "[2/6] 创建工作区..."
mkdir -p ~/.openclaw/workspace/memory

# 3. 创建基础配置文件
echo "[3/6] 创建基础配置文件..."

cat > ~/.openclaw/workspace/SOUL.md << 'SKILL_EOF'
# SOUL.md
你是一个冷静直接的 AI 助手。先给结论，再给细节。少废话，允许轻微幽默。
SKILL_EOF

cat > ~/.openclaw/workspace/USER.md << 'SKILL_EOF'
# USER.md
- 称呼: kami
- 语言: 中文
- 风格: 冷静、直接、靠谱
SKILL_EOF

cat > ~/.openclaw/workspace/MEMORY.md << 'SKILL_EOF'
# MEMORY.md
## 初始设置
- 桌面端 OpenClaw 实例建立
SKILL_EOF

cat > ~/.openclaw/workspace/AGENTS.md << 'SKILL_EOF'
# AGENTS.md
## 每次会话
1. 读 SOUL.md, USER.md, memory/ 日记
2. 主会话额外读 MEMORY.md
## 安全
- 不泄露私人数据，用 trash 而非 rm
SKILL_EOF

cat > ~/.openclaw/workspace/HEARTBEAT.md << 'SKILL_EOF'
# HEARTBEAT.md
- 频率: 每天早晚各一次
- 安静时段: 23:00-08:00
SKILL_EOF

# 4. 启动引导
echo "[4/6] 启动引导配置..."
echo "   请运行: openclaw onboard --install-daemon"
echo ""
echo "   向导会要求你输入:"
echo "   - AI 模型 API Key"
echo "   - 选择的模型"
echo ""

# 5. 配置 Telegram
echo "[5/6] Telegram 配置..."
echo "   请编辑 ~/.openclaw/openclaw.json，在 channels.telegram 中填入:"
echo "   - botToken: 从 @BotFather 获取的 Token"
echo "   - allowFrom: 你的 Telegram User ID"
echo ""

# 6. 验证
echo "[6/6] 验证安装..."
openclaw --version
openclaw doctor

echo ""
echo "=== 安装完成！ ==="
echo ""
echo "下一步："
echo "1. openclaw onboard --install-daemon  （配置 API Key 和模型）"
echo "2. 编辑 ~/.openclaw/openclaw.json 配置 Telegram"
echo "3. openclaw gateway start"
echo "4. 在 Telegram 给你的 Bot 发消息测试"
echo "5. 浏览器访问 http://127.0.0.1:18789 打开 Control UI"
```

---

## 十二、完整流程总结

```
┌─────────────────────────────────────────────────┐
│  1. 运行安装脚本                                  │
│     curl -fsSL https://openclaw.ai/install.sh | bash │
├─────────────────────────────────────────────────┤
│  2. 运行引导配置                                  │
│     openclaw onboard --install-daemon            │
│     → 填入 AI 模型 API Key                       │
│     → 选择模型                                    │
│     → 安装为系统服务                              │
├─────────────────────────────────────────────────┤
│  3. 创建工作区文件                                │
│     SOUL.md / USER.md / MEMORY.md / AGENTS.md   │
│     HEARTBEAT.md / TOOLS.md / memory/           │
├─────────────────────────────────────────────────┤
│  4. 配置 Telegram                                │
│     → BotFather 创建 Bot → 拿 Token              │
│     → 发消息给 Bot → 拿 User ID                  │
│     → 编辑 openclaw.json 填入 Token 和 ID        │
├─────────────────────────────────────────────────┤
│  5. 启动 & 验证                                  │
│     openclaw gateway start                       │
│     openclaw doctor                              │
│     Telegram 发消息测试                            │
│     http://127.0.0.1:18789 打开 Control UI       │
└─────────────────────────────────────────────────┘
```

---

## 参考

- 完整文档：https://docs.openclaw.ai
- GitHub：https://github.com/openclaw/openclaw
- 配置参考：https://docs.openclaw.ai/gateway/configuration-reference
