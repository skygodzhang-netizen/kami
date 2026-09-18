# 日报 2026-09-18（晚检 21:05 CST）

## 总览
整体正常，无告警。

## Ubuntu AI Server (192.168.100.108)
- 负载：1.36/0.50/0.23（正常）
- 内存：3.8G，used 1.5G，available 2.4G（正常）
- 磁盘：/ (sda2) 98G，used 20G，22%（正常）
- Docker：homeassistant Up 2 weeks（正常）
- Gateway：pid 215784 运行中，gateway 1d 1h（正常）
- 更新检查：未在本次晚检单独执行 apt 更新检查（常规项正常）

## iStoreOS 路由器 (192.168.100.1)
- 负载：2.14/1.58/1.36（正常）
- 分区：
  - overlay/sdb3: 73%（阈值 80%，正常）
  - sdb4: 8%（阈值 85%，正常）
  - sda1: 29%（阈值 85%，正常）
- OpenClash：clash pid 21600 / openclash_watch pid 21601 运行中（正常）
- Tailscale：istoreos-1 online；istoreos / zhanglihua offline（历史节点离线，未配置 serve）
- Tailscale serve：No serve config（正常，无提醒项）

## SSL 证书检查
- Gateway 证书：剩余 334 / 360 天（正常）
- 过期证书 4 个，全部为 Go module testdata 测试证书（非生产服务），无需处理

## 磁盘趋势
- disk-trend-analyze.sh 已执行，趋势数据更新至 21:05

## 安全邮件
- security-mail-check.sh 扫描完成，无异常

## 结论
无告警，无需人工干预。
