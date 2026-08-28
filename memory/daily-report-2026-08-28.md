# 2026-08-28 日报

## 巡检总结

### Ubuntu AI Server ✅
- 系统运行 8 天 7 小时，load 0.30
- 内存 1.3G / 3.8G (~34%)
- 磁盘 / 17% (可用 78G)
- Docker: homeassistant Up 8 days
- Gateway active, Caddy active
- fail2ban active，无安全事件
- 23 个包可升级（非紧急）
- **HA token 过期**（连续多日未处理）⚠️

### iStoreOS 路由器 🔴
- 系统运行 14 天 10 小时，load 1.14
- 磁盘 overlay 73% / sdb4 8% / sda1 23%
- OpenClash 服务 running，但 **mihomo 进程未运行**
- 代理端口返回 407，代理流量全部失败
- Tailscale running
- WAN 123.155.8.238，外网连通正常（0% 丢包）
- **代理失效需处理** 🔴

### 网络状态
- Ubuntu → google.com: 200 ✅
- iStoreOS → 8.8.8.8: 0% 丢包 ✅
- iStoreOS → baidu.com: 0% 丢包 ✅

### 今日关键问题
1. **HA token 过期** — 连续多日未处理
2. **OpenClash 代理失效** — mihomo 进程未运行，上游节点不可达
3. **Telegram bot 被踢出频道** — 通知持续失败
4. 23 个包可升级（非紧急）

---
*生成时间：2026-08-28 20:00 UTC (04:00 CST)*
