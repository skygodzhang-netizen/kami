# OpenClaw 桌面端安装指南

> 适用于 macOS / Linux / Windows，运行后只需填入 API 信息即可使用。

---

## 前置条件

- **Node.js 24**（推荐）或 Node 22.19+ — 安装脚本会自动处理
- 一个 AI 模型的 API Key（如 Anthropic、OpenAI、Google、MiniMax 等）

---

## 方法一：一键安装脚本（推荐，最快）

### macOS / Linux / WSL2

打开终端，运行：

```bash
curl -fsSL https://openclaw.ai/install.sh | bash
```

### Windows（PowerShell）

以**管理员身份**打开 PowerShell，运行：

```powershell
iwr -useb https://openclaw.ai/install.ps1 | iex
```

安装脚本会自动：
1. 检测操作系统
2. 安装 Node.js（如缺少）
3. 安装 OpenClaw
4. 启动引导配置向导（onboarding）

---

## 方法二：Windows Hub（图形化桌面应用）

适合想要 GUI 体验的 Windows 用户。

1. 从 GitHub Releases 下载：
   - x64: https://github.com/openclaw/openclaw/releases/latest/download/OpenClawCompanion-Setup-x64.exe
   - ARM64: https://github.com/openclaw/openclaw/releases/latest/download/OpenClawCompanion-Setup-arm64.exe
2. 运行安装程序（无需管理员权限）
3. 启动 **OpenClaw Companion**，按向导完成配置

功能包括：托盘状态、首次运行设置、聊天窗口、命令中心诊断、Windows 节点模式等。

---

## 方法三：npm 手动安装（已管理 Node 的用户）

如果你已经自己管理 Node.js：

```bash
npm install -g openclaw@latest
openclaw onboard --install-daemon
```

---

## 引导配置（onboarding）

安装完成后，运行以下命令进入交互式配置：

```bash
openclaw onboard --install-daemon
```

向导会引导你完成三步：

1. **选择模型提供商** — 选择你要用的 AI 服务（Anthropic / OpenAI / Google / MiniMax 等）
2. **输入 API Key** — 安全地存储在你的本地机器上，不会发送到 OpenClaw 服务器
3. **Gateway 设置** — 配置常驻后台的 Gateway 进程（自动开机启动）

> API Key 来源参考：
> - Anthropic (Claude): console.anthropic.com
> - OpenAI (GPT): platform.openai.com
> - Google (Gemini): aistudio.google.com
> - MiniMax: 你的 API 提供商控制台

---

## 验证安装

```bash
openclaw --version        # 确认 CLI 可用
openclaw doctor           # 检查配置问题
openclaw gateway status   # 确认 Gateway 正在运行
```

正常输出应显示 Gateway 在端口 18789 上监听。

---

## 常见问题

### `openclaw` 命令找不到

通常是 PATH 问题。运行：

```bash
echo "$PATH"
npm prefix -g
```

如果 `$(npm prefix -g)/bin` 不在 PATH 中，添加到 `~/.bashrc` 或 `~/.zshrc`：

```bash
export PATH="$(npm prefix -g)/bin:$PATH"
```

然后重启终端。

### Windows 上 Git 报错

如果看到 `npm error spawn git ENOENT`，重新运行安装脚本让它自动安装 MinGit，或安装 [Git for Windows](https://git-scm.com/download/win)。

### 跳过引导配置

如果想先安装再手动配置：

```bash
# macOS / Linux
curl -fsSL https://openclaw.ai/install.sh | bash -s -- --no-onboard

# Windows
& ([scriptblock]::Create((iwr -useb https://openclaw.ai/install.ps1))) -NoOnboard
```

然后手动运行 `openclaw onboard`。

---

## 卸载

```bash
openclaw uninstall
```

---

## 更新

```bash
openclaw update
```

或在 npm 安装下：

```bash
npm update -g openclaw
```

---

## 参考文档

- 完整文档：https://docs.openclaw.ai
- GitHub：https://github.com/openclaw/openclaw
