# HEARTBEAT.md - 自动化巡检与提醒

# 巡检频率
- **早检：09:00 CST** — 每日全面巡检
- **晚检：21:00 CST** — 每日全面巡检 + 日报
- **安静时段：23:00-08:00 CST** — 不主动打扰（紧急异常除外）

# 全面巡检清单

## Ubuntu AI Server (192.168.100.108)
- [ ] 系统负载（CPU/内存/磁盘IO）
- [ ] 磁盘空间（/ 和 /home，阈值 >85% 告警）
- [ ] Docker 容器状态（名称、运行时间、端口映射）
- [ ] Home Assistant 状态（是否在线、版本、长时间运行异常）
- [ ] HA 环境快照（运行 scripts/ha/ha-integration.sh）
- [ ] HA Camera 状态（运行 scripts/ha/ha-camera.sh list）
- [ ] OpenClaw Gateway 状态（进程、连接、日志错误）
- [ ] 系统更新可用（apt upgrade 检查）
- [ ] 安全日志（fail2ban、登录异常）
- [ ] 证书到期（Caddy local / Let's Encrypt，<30天告警）
- [ ] SSL 证书检测（运行 ssl-cert-check.sh）
- [ ] 磁盘趋势采集（运行 disk-trend-analyze.sh）

## iStoreOS 路由器 (192.168.100.1)
- [ ] 系统负载与温度
- [ ] 磁盘空间（分区分别显示）
- [ ] OpenClash 状态（运行中/异常）
- [ ] Docker 容器状态
- [ ] WAN 连接状态
- [ ] 内网设备在线情况
- [ ] Tailscale 服务状态（仅检查运行状态，不检测 443 占用）
  - 如检测到 tailscale serve 配置存在 → 提醒 kami

## 安全邮件监控（独立 cron，非巡检触发）
- [ ] 扫描 Google/Bybit/PayPal/GitHub/Cloudflare/CloudCone/OpenAI/Anthropic 安全邮件
- [ ] 风险等级分类（🔴高危/🟡警告/🟢普通）
- [ ] 高危事件立即 Telegram 通知
- [ ] 普通事件仅记录日志

## 网络与服务
- [ ] 内外网连通性
- [ ] DNS 解析正常
- [ ] 关键端口可达性

# 巡检报告格式

## Ubuntu AI Server
```
[磁盘] / : 16% (98G, 可用79G)
[Docker] homeassistant: Up 2 days
[服务] docker: OK, openclaw-gateway: OK
[更新] 1 个包可升级
```

## iStoreOS 路由器 — 分区独立显示
```
[系统盘 overlay] sdb3: 67% (1.9G, 可用644MB) ← 只监控
[数据盘 sdb4] /mnt/sata2-4: 8% (26.5G, 可用23.2G)
  ├─ Docker: 726MB
  ├─ OpenClaw: 513MB
  └─ 其他: ...
[数据盘 sda1] /mnt/data_sda1: 19% (109.5G, 可用83.8G)
  └─ iso: 3.2GB
[服务] OpenClash: running
[网络] WAN: IPv6 2408:8340:5427:18e0::1
```

# 磁盘告警规则

## 系统盘 (overlay)
- **>80%**: 通知 kami，分析占用原因，**不自动清理**
- **>90%**: 紧急通知，建议方案

## 数据盘 (sdb4, sda1)
- **>85%**: 通知 kami，提供清理建议，**执行删除前确认**
- **>90%**: 紧急通知，建议方案

## Docker 存储
- 监控 /mnt/sata2-4/docker 占用
- 异常增长时分析 volume 大小

# 日报内容
每次晚检生成日报，包含：
- 所有设备/服务的健康状态汇总
- 发现的异常及处理结果
- 磁盘/内存趋势
- SSL 证书状态
- Docker 容器状态
- 安全邮件扫描摘要
- 待处理事项

# 独立监控任务（非巡检触发）
## 安全邮件监控
- 脚本: scripts/security-mail-check.sh
- 规则: config/security-rules.json
- 日志: memory/security-mail-log.txt
- 调度: 通过 cron 独立定时执行

## Docker 容器健康（观察模式）
- 脚本: scripts/container-health-check.sh
- 日志: memory/container-health-log.txt
- 模式: 仅检测+通知，不自动恢复
- 调度: 通过 cron 独立定时执行

## SSL 证书检测
- 脚本: scripts/ssl-cert-check.sh
- 合并到早检/晚检执行
- 阈值: <7天 🔴紧急, <30天 🟡警告, <90天 记录

## 磁盘趋势分析
- 脚本: scripts/disk-trend-analyze.sh
- 数据: config/disk-trend.json
- 合并到晚检执行
- 保留最近90天数据

# 异常自动修复策略
- Docker 容器异常停止 → 尝试重启
- OpenClaw Gateway 异常 → 尝试重启
- OpenClash 异常 → 尝试重启
- 磁盘空间不足 → 清理旧日志/临时文件
- 以上操作完成后记录日志，通知 kami

# 日程与提醒
- 检查未来 24-48 小时日程/事件
- 提前 1 天提醒即将发生的事件
- 对话中提到的待办自动整理记录

# 工作区
- 定期检查 git 状态，有未提交改动时提醒
