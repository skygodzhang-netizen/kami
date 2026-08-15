#!/bin/bash
# OpenClaw 桌面端一键安装脚本
# 运行: bash setup-openclaw.sh
set -e

echo "=========================================="
echo "  OpenClaw 桌面端完整安装"
echo "=========================================="
echo ""

# 1. 安装 OpenClaw
echo "[1/5] 安装 OpenClaw..."
curl -fsSL https://openclaw.ai/install.sh | bash
echo ""

# 2. 创建工作区
echo "[2/5] 创建工作区..."
mkdir -p ~/.openclaw/workspace/memory

# 3. 创建基础配置文件
echo "[3/5] 创建配置文件..."

cat > ~/.openclaw/workspace/SOUL.md << 'EOF'
# SOUL.md

你是小维，一个冷静直接的 AI 助手。

## 核心原则
1. 先给结论，再给细节
2. 少废话，但不冷冰冰
3. 能自己搞定的先搞定
4. 外部动作先确认

## 主动性
- 通过 HEARTBEAT.md 驱动周期性检查
- 安静时段 23:00-08:00 除非紧急
EOF

cat > ~/.openclaw/workspace/USER.md << 'EOF'
# USER.md

- 称呼: kami
- 语言: 中文
- 风格: 冷静、直接、靠谱
- 偏好: 先结论后细节，需要时可执行步骤/清单
EOF

cat > ~/.openclaw/workspace/MEMORY.md << 'EOF'
# MEMORY.md

## 初始设置 (2026-06-29)
- 桌面端 OpenClaw 实例建立
- 主要使用 Telegram 频道
EOF

cat > ~/.openclaw/workspace/AGENTS.md << 'EOF'
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
EOF

cat > ~/.openclaw/workspace/HEARTBEAT.md << 'EOF'
# HEARTBEAT.md

- 频率: 每天早晚各一次
- 安静时段: 23:00-08:00
EOF

cat > ~/.openclaw/workspace/TOOLS.md << 'EOF'
# TOOLS.md

## 本地路径
- 工作区: ~/.openclaw/workspace
- 配置: ~/.openclaw/openclaw.json
- 日志: /tmp/openclaw/
EOF

echo ""

# 4. 验证安装
echo "[4/5] 验证安装..."
openclaw --version
openclaw doctor
echo ""

# 5. 安装 Gateway 服务
echo "[5/5] 安装 Gateway 服务..."
openclaw gateway install 2>/dev/null || echo "   (Gateway 服务安装可能需要 sudo)"
echo ""

echo "=========================================="
echo "  ✅ 安装完成！"
echo "=========================================="
echo ""
echo "接下来你需要做三件事："
echo ""
echo "1️⃣  运行引导配置（填入 API Key）："
echo "   openclaw onboard --install-daemon"
echo ""
echo "2️⃣  配置 Telegram（编辑 ~/.openclaw/openclaw.json）："
echo "   - botToken: 从 @BotFather 获取"
echo "   - allowFrom: 你的 Telegram User ID"
echo ""
echo "3️⃣  启动 Gateway："
echo "   openclaw gateway start"
echo ""
echo "💡 浏览器访问 http://127.0.0.1:18789 打开管理界面"
echo ""
