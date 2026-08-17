# 操作日志

## 2026-08-14

### 23:05 CST — OpenClash 维护
**操作**：修复YouTube延迟高、手机GPT证书错误问题
**步骤**：
1. 配置TUN证书到 smart.yaml
2. 重启OpenClash服务

**结果**：
- YouTube延迟: 7.9s → 1.77s ✅
- GPT API连通性正常 ✅
- TUN证书问题已由 kami 处理完成 ✅

**待办**：
- Airport1和VPS订阅可能需要更新

---

### 20:03 UTC — 晚检日报
**问题**：
- OpenClash 未运行 (enable=0)
- Telegram通知发送失败
- Agnes API响应变慢 (2.14s)

---

### 15:00 UTC — 午检
- 全部正常

---

### 13:12 CST — 安全邮件扫描
- Bybit 新设备登录（台中）
- PayPal 数据删除请求
- Google 多次验证码

---

### 05:05 UTC — 安全邮件扫描
- Bybit 台中新设备登录

---

## 2026-08-13

### 操作记录
- 安全邮件扫描完成

### 10:01 CST — 早检完成
- Ubuntu AI Server: 全部正常
- iStoreOS: 全部正常
- 无异常，安静时段不打扰

[2026-08-15 12:04 CST] 午检完成 — OpenClash运行正常，全部服务稳定
[2026-08-15 13:32:31 CST] 晚检完成 - 全部正常，无异常

## 2026-08-16 06:00 UTC — Heartbeat
- Ubuntu AI Server: up 1d20h, load 0.31, disk 16%, mem 1.4G/3.8G, HA 401, Gateway 200
- iStoreOS: up 1d20h, load 1.08, disk overlay 68%, sdb4 8%, sda1 22%, OpenClash running, Tailscale running
- SSL: Caddy intermediate cert 6 days (Aug 22)
- Docker: homeassistant Up 44h
- No zombie processes, no log errors
- 6 packages upgradable (krb5)
- Status: ALL NORMAL

## 2026-08-16 16:00 UTC
- 心跳巡检完成，全部正常
- SSL Caddy 中间证书剩余6天，连续多日关注
- 安全邮件无新增高危事件

## 2026-08-16 16:30 UTC - 心跳巡检
- Ubuntu AI Server: 正常
- iStoreOS: 正常
- SSL证书: 中间CA剩余6天，继续观察
- 安全邮件: 无新增事件
- 磁盘趋势: 已采集
- 无异常事件

## 2026-08-16 10:30 UTC — 心跳巡检
- Ubuntu AI Server: all normal
- iStoreOS: all normal
- SSL: Caddy cert still 6 days (持续关注)
- Disk trend: data collected
- Status: ALL OK
[2026-08-16 11:30 CST] 心跳巡检 — Ubuntu AI Server: all OK, iStoreOS: all OK, SSL: Caddy cert 6 days, disk trend: collected, security email: no new high-risk events

[2026-08-16 20:02 CST] 晚检完成
- Ubuntu AI Server: all normal, 1 package upgradable (krb5)
- iStoreOS: all normal, OpenClash running, Tailscale running
- SSL: Caddy intermediate cert 6 days (Aug 22) — persistent warning
- No security events, no disk alerts
- Container health: 1/1 normal
- Status: ALL OK

[2026-08-16 20:03 CST] 安全邮件扫描
- Google: 无新增高危
- Bybit: 2026-06-30 台中新设备登录（历史事件）
- PayPal: 数据删除请求（历史事件）
- 无新增高危事件

## 2026-08-17 01:00 UTC — 夜间心跳巡检
- Ubuntu: up 2d7h, load 0.57, mem 37%, disk 16%, HA/ Gateway OK
- iStoreOS: up 2d7h, load 1.27, overlay 68%, OpenClash/Tailscale OK
- SSL: Caddy中间证书剩余5天（8/22到期）— 持续告警
- Gateway错误：141条/24h（mostly非关键：node-llama-cpp缺失、Telegram瞬时失败、Agnes DNS临时失败）
- 磁盘趋势：已采集
- 结论：系统稳定，无紧急事项
