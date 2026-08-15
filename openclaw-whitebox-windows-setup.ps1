# OpenClaw Windows 白标安装脚本

> 客户拿到这个脚本，运行后就是一个功能完整的 OpenClaw 实例。
> 只需填自己的 AI API Key 和 Telegram Bot Token 即可开始使用。
> 无任何第三方 API Key 绑定，完全白标。

---

## 安装脚本（复制以下全部内容，以管理员 PowerShell 运行）

```powershell
# ============================================
# OpenClaw Windows 白标安装
# 运行环境: Windows 10 20H2+ / Windows 11
# 权限: 管理员 PowerShell
# ============================================

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "  OpenClaw 完整安装" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 安装 OpenClaw
Write-Host "[1/7] 安装 OpenClaw..." -ForegroundColor Yellow
iwr -useb https://openclaw.ai/install.ps1 | iex
Write-Host "  ✓ 完成" -ForegroundColor Green
Write-Host ""

# 2. 验证
Write-Host "[2/7] 验证安装..." -ForegroundColor Yellow
try {
    $ver = openclaw --version 2>&1
    Write-Host "  ✓ 版本: $ver" -ForegroundColor Green
} catch {
    Write-Host "  ⚠ 请关闭并重新打开 PowerShell 后重试" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 3. 创建工作区
Write-Host "[3/7] 创建工作区..." -ForegroundColor Yellow
$ws = "$env:USERPROFILE\.openclaw\workspace"
$mem = "$ws\memory"
if (!(Test-Path $mem)) { New-Item -ItemType Directory -Path $mem | Out-Null }
Write-Host "  ✓ $ws" -ForegroundColor Green
Write-Host ""

# 4. 创建人格文件
Write-Host "[4/7] 创建配置文件..." -ForegroundColor Yellow

@"
# SOUL.md

你是一个冷静直接的 AI 助手。

## 核心原则
1. 先给结论，再给细节
2. 少废话，但不冷冰冰
3. 能自己搞定的先搞定
4. 外部动作先确认

## 主动性
- 通过 HEARTBEAT.md 驱动周期性检查
- 安静时段 23:00-08:00 除非紧急
"@ | Out-File -Encoding utf8 "$ws\SOUL.md"

@"
# USER.md

- 称呼: 用户
- 语言: 中文
- 风格: 冷静、直接、靠谱
"@ | Out-File -Encoding utf8 "$ws\USER.md"

@"
# MEMORY.md

## 初始设置
- OpenClaw 桌面端实例建立
"@ | Out-File -Encoding utf8 "$ws\MEMORY.md"

@"
# AGENTS.md

## 每次会话
1. 读 SOUL.md
2. 读 USER.md
3. 读 memory/ 下的最近日记
4. 主会话额外读 MEMORY.md

## 安全
- 不泄露私人数据
- 用 trash 而非 rm
- 不确定就问
"@ | Out-File -Encoding utf8 "$ws\AGENTS.md"

@"
# HEARTBEAT.md

- 频率: 每天早晚各一次
- 安静时段: 23:00-08:00
"@ | Out-File -Encoding utf8 "$ws\HEARTBEAT.md"

@"
# TOOLS.md

## 本地路径
- 工作区: ~/.openclaw/workspace
- 配置: ~/.openclaw/openclaw.json
- 日志: /tmp/openclaw/
"@ | Out-File -Encoding utf8 "$ws\TOOLS.md"

@"
# 初始日

- OpenClaw 安装完成
"@ | Out-File -Encoding utf8 "$mem\初始日.md"

Write-Host "  ✓ 所有配置文件已创建" -ForegroundColor Green
Write-Host ""

# 5. 创建默认配置（白标，无 API Key）
Write-Host "[5/7] 创建默认配置..." -ForegroundColor Yellow
$configPath = "$env:USERPROFILE\.openclaw\openclaw.json"
if (!(Test-Path $configPath)) {
    @"
{
  // ================================================================
  //  OpenClaw 配置文件
  //  位置: ~/.openclaw/openclaw.json
  //  编辑此文件后 Gateway 会自动热加载
  // ================================================================

  // ========== Agent 配置 ==========
  agents: {
    defaults: {
      workspace: "$ws",

      // 模型配置 — 运行 openclaw onboard 后自动填充
      // model: {
      //   primary: "你的模型提供商/模型名",
      //   fallbacks: ["备用模型"]
      // }

      // 会话管理
      session: {
        dmScope: "per-channel-peer",
        reset: {
          mode: "daily",
          atHour: 4,
          idleMinutes: 120
        }
      },

      // 心跳检查
      heartbeat: {
        every: "30m",
        target: "last"
      }
    }
  },

  // ========== Gateway 配置 ==========
  gateway: {
    port: 18789,
    bind: "loopback",        // loopback=仅本机, lan=局域网可访问
    auth: {
      mode: "token",          // token | password | none
      // token: "你的网关密钥"  // openclaw onboard 会自动生成
    },
    controlUi: {
      enabled: true           // 浏览器管理界面
    }
  },

  // ========== 频道配置 ==========
  channels: {
    // ---- Telegram ----
    // 1. 在 Telegram 找 @BotFather 创建 Bot，拿到 Token
    // 2. 发消息给 Bot，运行 openclaw logs --follow 找到 from.id
    // 3. 取消下面注释，填入 Token 和 User ID
    /*
    telegram: {
      enabled: true,
      botToken: "你的BOT_TOKEN",
      dmPolicy: "allowlist",
      allowFrom: ["你的TELEGRAM_USER_ID"],
      groups: {
        "*": { requireMention: true }
      }
    }
    */

    // ---- Signal（可选）----
    /*
    signal: {
      enabled: true,
      // 按需配置
    }
    */

    // ---- Discord（可选）----
    /*
    discord: {
      enabled: true,
      // 按需配置
    }
    */
  },

  // ========== 浏览器 ==========
  browser: {
    enabled: true
  },

  // ========== 技能（Skills） ==========
  skills: {
    entries: {}
  },

  // ========== 插件（Plugins） ==========
  plugins: {
    enabled: true
  }
}
"@ | Out-File -Encoding utf8 $configPath
    Write-Host "  ✓ 默认配置已创建" -ForegroundColor Green
  } else {
    Write-Host "  ℹ 配置文件已存在" -ForegroundColor Yellow
  }
Write-Host ""

# 6. 安装 Gateway 服务
Write-Host "[6/7] 安装 Gateway 服务..." -ForegroundColor Yellow
try {
    openclaw gateway install 2>$null
    Write-Host "  ✓ 服务已安装" -ForegroundColor Green
} catch {
    Write-Host "  ⚠ 请手动运行: openclaw gateway install" -ForegroundColor Yellow
}
Write-Host ""

# 7. 防火墙
Write-Host "[7/7] 配置防火墙..." -ForegroundColor Yellow
try {
    $rule = Get-NetFirewallRule -DisplayName "OpenClaw Gateway" -ErrorAction SilentlyContinue
    if (!$rule) {
        New-NetFirewallRule -DisplayName "OpenClaw Gateway" -Direction Inbound -Protocol TCP -LocalPort 18789 -Action Allow 2>$null
        Write-Host "  ✓ 防火墙规则已添加" -ForegroundColor Green
    }
} catch {}
Write-Host ""

# ============================================
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  ✅ 安装完成！" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor White
Write-Host ""
Write-Host "  你的 OpenClaw 实例已就绪！" -ForegroundColor Cyan
Write-Host ""
Write-Host "  接下来只需要做 2 件事：" -ForegroundColor White
Write-Host ""
Write-Host "  ① 配置 AI 模型" -ForegroundColor Yellow
Write-Host "     运行: openclaw onboard --install-daemon" -ForegroundColor White
Write-Host "     → 选择模型提供商" -ForegroundColor Gray
Write-Host "     → 填入 API Key" -ForegroundColor Gray
Write-Host "     → 选择模型" -ForegroundColor Gray
Write-Host ""
Write-Host "  ② 配置 Telegram（可选）" -ForegroundColor Yellow
Write-Host "     编辑: ~/.openclaw/openclaw.json" -ForegroundColor White
Write-Host "     → 取消 telegram 部分的注释" -ForegroundColor Gray
Write-Host "     → 填入 botToken 和 allowFrom" -ForegroundColor Gray
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor White
Write-Host ""
Write-Host "常用命令：" -ForegroundColor White
Write-Host "  openclaw gateway start/stop/restart" -ForegroundColor Gray
Write-Host "  openclaw doctor" -ForegroundColor Gray
Write-Host "  openclaw logs --follow" -ForegroundColor Gray
Write-Host "  openclaw update" -ForegroundColor Gray
Write-Host ""
Write-Host "管理界面: http://127.0.0.1:18789" -ForegroundColor Cyan
Write-Host ""
```

---

## 客户使用流程

### 第1步：运行安装脚本

以管理员身份打开 PowerShell，粘贴上面脚本，回车。

### 第2步：配置 AI 模型

```powershell
openclaw onboard --install-daemon
```

向导引导：
1. 选择模型提供商（Anthropic / OpenAI / Google / OpenRouter / MiniMax 等）
2. 填入 API Key
3. 选择模型

### 第3步：配置 Telegram（可选）

1. 在 Telegram 找 @BotFather → `/newbot` → 拿到 Bot Token
2. 发消息给 Bot → 运行 `openclaw logs --follow` → 找到 `from.id`
3. 编辑 `~/.openclaw/openclaw.json` → 取消 `channels.telegram` 注释 → 填入 Token 和 User ID
4. 运行 `openclaw gateway restart`

### 第4步：验证

```powershell
openclaw doctor
openclaw gateway status
```

浏览器打开 http://127.0.0.1:18789 查看管理界面。

---

## 功能清单（安装后即具备）

| 功能 | 状态 |
|------|------|
| Gateway 常驻后台 | ✅ 开机自启 |
| Telegram 接入 | ✅ 配置后使用 |
| 浏览器控制 | ✅ 开箱即用 |
| Skills 系统 | ✅ 开箱即用 |
| Memory 记忆 | ✅ 开箱即用 |
| Cron 定时任务 | ✅ 开箱即用 |
| 多 Agent 路由 | ✅ 配置后使用 |
| Control UI 管理界面 | ✅ 开箱即用 |
| 会话自动重置 | ✅ 每日凌晨4点 |
| 心跳检查 | ✅ 每30分钟 |
| 安静时段 | ✅ 23:00-08:00 |
| 工作区文件 | ✅ SOUL/USER/MEMORY/AGENTS/HEARTBEAT/TOOLS |

---

## 销售/分发说明

- **无绑定**: 脚本不包含任何 API Key，客户用自己的
- **无授权**: 不依赖任何激活码或许可证
- **开源合规**: 基于 OpenClaw 官方安装脚本
- **可定制**: 修改脚本中的 SOUL.md 等文件即可定制人格
- **零成本**: 客户只需自备 AI 模型 API Key
