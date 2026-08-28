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
- OpenClash 服务 running，clash 进程 PID 12168
- **代理端口正常**：7890/7891/7893 监听中
- **但无可用节点**：
  - proxylite 订阅源返回 404 Not Found
  - 所有代理请求失败（返回 000）
  - 直连正常
- Tailscale running
- WAN 123.155.8.238，外网连通正常（0% 丢包）
- **需更新订阅链接或重新配置节点** 🔴

### 网络状态
- Ubuntu → google.com: 200 ✅
- iStoreOS → 8.8.8.8: 0% 丢包 ✅
- iStoreOS → baidu.com: 0% 丢包 ✅

### 今日关键问题
1. **HA token 过期** — 连续多日未处理
2. **OpenClash 代理失效** — proxylite 订阅 404，无可用节点
3. **Telegram bot 被踢出频道** — 通知持续失败
4. 23 个包可升级（非紧急）

---
*生成时间：2026-08-28 20:00 UTC (04:00 CST)*
