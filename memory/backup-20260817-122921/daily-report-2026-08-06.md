# 日报 2026-08-06

## 巡检汇总

### Ubuntu AI Server (192.168.100.108) ✅
- 运行时间: 15 days, 21:35
- 负载: 0.28 0.21 0.13 (晚检)
- 内存: 1.5G/3.8G (39%)
- 磁盘 /: 16% (79G 可用)
- Docker: homeassistant Up 5 days
- 服务: docker ✅, openclaw-gateway ✅
- 系统更新: 7 个包可升级 (docker-ce 29.7.1, nodejs 22.23.2)
- SSL 证书: 全部正常，最短 113 天
- OpenClaw Gateway 日志: 10:08 UTC 有一次 model-fetch abort error（临时网络问题，已恢复）

### iStoreOS 路由器 (192.168.100.1) ✅
- 运行时间: 15 days, 21:36
- 负载: 0.69 0.41 0.31 (晚检)
- 分区:
  - [系统盘 overlay] sdb3: 67% (638MB 可用)
  - [数据盘 sdb4] /mnt/sata2-4: 8% (23.2G 可用)
  - [数据盘 sda1] /mnt/data_sda1: 21% (82.5G 可用)
- OpenClash: running ✅
- Tailscale: running ✅ (PID 8782)
- Tailscale serve 配置: 存在 (_serve/e416)，已记录不操作

### 磁盘趋势
- 采集完成，共 52 条记录

### Docker 容器
- homeassistant: Up 5 days，正常

### SSL 证书
- 全部正常，最短 113 天

### 异常汇总
- 无严重异常
- 10:08 UTC OpenClaw Gateway 临时网络波动，已自动恢复

### 待处理
- 7 个系统包可升级（非紧急，下次晚检处理）

---
_生成时间: 2026-08-06 20:02 CST_
