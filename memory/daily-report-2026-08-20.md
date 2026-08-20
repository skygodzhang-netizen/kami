# 2026-08-20 日报

## 系统概览：🟢 正常
全天运行稳定，无异常事件。

---

## Ubuntu AI Server
- 运行时间：6天3小时 | 负载：0.30
- 内存：45%（1.7Gi/3.8Gi）
- 磁盘 /：17%（78G free）
- Docker：homeassistant Up 2 days
- OpenClaw Gateway：active
- Caddy：active
- HA API：200 OK
- SSL：gateway.pem 剩余363天
- 系统更新：16个包可升级（非紧急）

## iStoreOS 路由器
- 运行时间：6天3小时 | 负载：0.83
- 内存：62%（4.7Gi/7.6Gi）
- 系统盘 overlay：72%（稳定）
- 数据盘 sdb4：8%
- 数据盘 sda1：23%
- OpenClash：running
- Tailscale：running（istoreos-1 online，zhanglihua offline）
- WAN：pppoe-wan 在线
- Tailscale serve：无配置

## SSL 证书
- 9个证书全部正常
- gateway.pem 剩余363天

## 安全邮件
- 今日多次扫描，无新增高危事件

## 磁盘趋势
- 数据采集正常，无异常增长

## 异常记录
- event_loop_delay 轻微（P99=188ms，max=1369ms），继续观察

## 待处理
- 🟡 16个系统包可升级（非紧急）
- ℹ️ Tailscale zhanglihua 设备离线
