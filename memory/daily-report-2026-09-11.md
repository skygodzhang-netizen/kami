# 日报 2026-09-11（周五）晚检

## 总览
全部正常 ✅，无紧急异常，无需自动修复。

---

## Ubuntu AI Server
- 系统：up 10 天 12 小时 ✅
- 负载：0.22 / 0.13 / 0.10（正常）
- 内存：3.8G total，used 1.4G，available 2.4G ✅
- 磁盘 /：16% used (16G/98G，78G free) ✅
- Docker：homeassistant Up 10 days ✅
- HA：v2026.7.2，camera.bedroom_camera idle ✅
- Gateway：active ✅
- 更新可升级：21 个包（docker/containerd/base-files 等），未自动升级
- 安全日志：无异常登录，无 fail2ban 记录

---

## iStoreOS 路由器
- 系统：up 10 天 12 小时，负载 1.22/1.27/1.26 ✅
- 温度：45°C（thermal_zone0）/ 54°C（thermal_zone1）✅
- 内存：8G total，used 4.7G，available 3.1G ✅
- 磁盘：
  - overlay (sdb3)：73% (1.4G/1.9G，525M free) — 低于 80% 阈值 ✅
  - sdb4：8% (1.9G/26.5G) ✅
  - sda1：25% (25.5G/109.5G) ✅
- OpenClash：running ✅
- Docker：无容器 ✅
- Tailscale：not running（无 serve 配置，无需提醒）
- WAN：br-lan / docker0 / br-aa687e4ea3e7 正常

---

## SSL 证书
- gateway 证书：341 天 ✅
- 共检测 9 个证书，全部正常

---

## 磁盘趋势
- 已采集 2026-09-11 21:00 CST 数据点 → config/disk-trend.json

---

## 安全邮件
- 最近扫描：2026-09-10 13:05 CST ✅
- 无高危事件

---

## 异常记录
- 09:30 早检 HA API 报"supervisor" 命令缺失（路径问题，不影响服务，HA 容器正常运行）
- Gateway 日志 12:21 UTC 有 2 条 telegram transport unhealthy 记录（自动恢复，非持续故障）
- 无其他异常

---

## 待处理事项
1. apt 21 个包可升级（含 docker/containerd），建议在适当窗口执行
2. iStoreOS overlay 73%（525M free），持续观察，暂不清理
