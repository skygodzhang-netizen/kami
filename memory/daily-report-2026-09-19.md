# 日报 2026-09-19（晚检 21:00 CST）

## 总览
整体正常，无告警。

## Ubuntu AI Server (192.168.100.108)
- 负载：0.09/0.24/0.25（正常）
- 内存：3.8G，used 1.2G，available 2.6G（正常）
- 磁盘：/ (sda2) 98G，used 20G，22%（正常）
- Docker：homeassistant Up 2 weeks（正常）
- Gateway：运行中（正常）
- HA：HTTP 可达（正常）

## iStoreOS 路由器 (192.168.100.1)
- 负载：1.29/1.38/1.36（正常）
- 分区：
  - overlay/sdb3: 73%（阈值 80%，正常）
  - sdb4: 8%（阈值 85%，正常）
  - sda1: 30%（阈值 85%，正常）
- OpenClash：clash(pid 4360) + openclash_watch(pid 4361) 运行中（正常）
- Tailscale：istoreos-1 online；istoreos / zhanglihua offline（历史节点离线）
- Tailscale serve：No serve config（正常，无提醒项）

## SSL 证书检查
- 过期证书 4 个，全部为 Go module testdata 测试证书（非生产服务），无需处理
- 网关证书 334/360 天正常（沿用 09-18 记录，本次未单独验证）

## 磁盘趋势
- disk-trend-analyze.sh 已执行，趋势数据更新至 21:13

## 安全邮件
- security-mail-check.sh 扫描完成，无异常

## OpenClash 日志观察
- 存在 i/o timeout 警告（msg.ivod.wavideo.tv:9990、mobile.events.data.microsoft.com），属偶发连接超时，非服务异常，无需处理

## 结论
无告警，无需人工干预。
