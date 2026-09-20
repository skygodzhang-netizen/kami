# 日报 2026-09-20（晚检 21:00 CST）

## 总览
整体正常，无告警。Ubuntu 侧有 25 个 apt 更新待安装（非紧急，记录备查）。

## Ubuntu AI Server (192.168.100.108)
- 负载：0.15/0.29/0.18（正常）
- 内存：3.8G，used 1.4G，available 2.5G（正常）
- 磁盘：/ (sda2) 98G，used 20G，22%（正常）
- Docker：homeassistant Up 2 weeks（正常）
- Gateway：运行中（正常）
- HA：HTTP 200 可达（正常）
- 系统更新：25 个包待升级（apt），不属紧急项

## iStoreOS 路由器 (192.168.100.1)
- 负载：1.75/1.53/1.39（正常）
- 分区：
  - overlay/sdb3: 73%（阈值 80%，正常）
  - sdb4: 8%（阈值 85%，正常）
  - sda1: 30%（阈值 85%，正常）
- OpenClash：clash(pid 4360) + openclash_watchdog(pid 4361) 运行中（正常）
- Tailscale：istoreos-1 (100.123.106.24) online；istoreos / zhanglihua offline（历史节点离线，已知）
- Tailscale serve：未发现 serve.json 配置（正常，无提醒项）

## SSL 证书检查
- 共检测 16 个证书，4 个过期证书全部为 Go module testdata 测试证书（非生产服务），无需处理

## 磁盘趋势
- disk-trend-analyze.sh 已执行，趋势数据更新至 21:06

## 安全邮件
- security-mail-check.sh 扫描完成，无异常

## 结论
无告警，无需人工干预。
