---
name: home-assistant
description: Home Assistant 深度集成 — 环境感知、状态查询、设备控制、Camera 联动
---

# Home Assistant Integration Skill

## 架构

```
Home Assistant
    ↓ (API/Webhook)
ha-api.sh — 安全 API 封装
    ↓
ha-integration.sh — 状态变化检测 → Memory
    ↓
ha-query.sh — 自然语言查询
ha-control.sh — 自然语言控制 (带安全确认)
    ↓
ha-camera.sh — Camera 快照 (预留 Vision 接口)
camera-vision.sh — Camera Vision 分析
    ↓
Environment Memory (状态记录)
Episodes (事件记录)
Notifications (通知队列)
```

## 核心脚本 (12个)

| 脚本 | 功能 | 安全级别 |
|------|------|----------|
| `ha-api.sh` | 安全 API 封装 (速率限制 30s) | - |
| `ha-integration.sh` | 状态变化检测 → Memory | 只读 |
| `ha-query.sh` | 自然语言查询 HA 状态 | 只读 |
| `ha-control.sh` | 自然语言控制 (带安全级别) | 低/高 |
| `ha-camera.sh` | Camera 快照 + Vision 预留 | 只读 |
| `camera-vision.sh` | Camera Vision 分析 | 只读 |
| `ha-camera-integration.sh` | Camera 集成到 HA | 配置 |
| `camera-monitor.sh` | Camera 离线监控 | 保护 |
| `ha-loop-prevention.sh` | 防循环机制 (5分钟冷却) | 保护 |
| `ha-webhook.sh` | Webhook 事件处理 | 只读 |
| `ha-config.sh` | 配置向导 | 配置 |
| `heartbeat-ha.sh` | Heartbeat 巡检集成 | 只读 |

## Heartbeat 集成

`scripts/heartbeat-ha.sh` — 在 Heartbeat 中自动调用：
- 检测 HA 在线状态
- 记录实体数量变化
- 监控关键实体 (person/motion/alarm)
- 输出摘要到 Heartbeat 报告

## Camera 集成

### 添加摄像头
```bash
# 添加摄像头到 HA
bash scripts/ha/ha-camera-integration.sh <IP> <名称>

# 示例
bash scripts/ha/ha-camera-integration.sh 192.168.100.152 客厅
```

### Camera 操作
```bash
# 列出摄像头
bash scripts/ha/camera-vision.sh list

# 拍摄快照
bash scripts/ha/camera-vision.sh <名称> snapshot

# 分析图片
bash scripts/ha/camera-vision.sh <名称> analyze
```

## 安全规则

### 低风险操作 (自动执行)
- 灯光开关
- 插座开关
- 空调温度设置
- 窗帘控制

### 高风险操作 (必须确认)
- 门锁控制
- 安防系统
- 摄像头录制
- 删除/重置操作

### 防循环机制
- 5分钟冷却期: 防止 HA → Memory → Agent → HA 死循环
- 同一实体最多每 30 秒查询一次
- 状态变化记录到日志，不高频写入 Memory
- 重要事件才写入 Episode

## 使用示例

### 查询状态
```bash
bash scripts/ha/ha-query.sh "客厅灯"
bash scripts/ha/ha-query.sh "家里有人吗"
bash scripts/ha/ha-query.sh "传感器状态"
```

### 控制设备
```bash
# 低风险 (直接执行)
bash scripts/ha/ha-control.sh "打开" "客厅灯"
bash scripts/ha/ha-control.sh "设置温度" "空调" "26度"

# 高风险 (需要确认)
bash scripts/ha/ha-control.sh "开锁" "前门"
```

### Camera
```bash
# 列出 Camera
bash scripts/ha/camera-vision.sh list

# 拍摄快照
bash scripts/ha/camera-vision.sh 客厅 snapshot

# 获取最新快照
bash scripts/ha/ha-camera.sh latest camera.living_room
```

### Heartbeat
```bash
# 手动执行 HA 巡检
bash scripts/heartbeat-ha.sh
```

## 环境变量

```bash
HA_URL=http://192.168.100.108:8123
HA_TOKEN_FILE=/home/ubuntu/.openclaw/workspace/config/ha-token
```

## Memory 集成

| 目标 | 路径 | 内容 |
|------|------|------|
| 状态快照 | `memory/ha-states/last.json` | 当前所有实体状态 |
| 变化日志 | `memory/episodes/ha-changes.log` | 状态变化历史 |
| 历史数据 | `memory/ha-state-history.jsonl` | JSONL 格式历史 |
| 通知队列 | `memory/ha-notifications/queue.txt` | 待处理通知 |
| Camera 快照 | `memory/camera/` | 图片文件 |
| Camera 配置 | `memory/camera/*.json` | 摄像头配置信息 |
| Heartbeat 日志 | `memory/ha-status.log` | 巡检记录 |

---
*Home Assistant Integration v3.0*
