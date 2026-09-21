# 日报 2026-09-17（晚检 21:00 CST）

## Ubuntu AI Server
- 负载: 0.53 / 0.40 / 0.31（16d 12h uptime）
- 内存: 1437/3915MB 已用，Swap 296/2047MB
- 磁盘: / 22%（20G/98G）
- Docker: homeassistant 运行中（2周）
- Gateway (openclaw-gateway): active
- Home Assistant: API 可达（401 = 正常鉴权）
- 待更新: 包管理器有多个可升级包（base-files、docker-ce、krb5 等），未自动安装

## iStoreOS（192.168.100.1）
- 负载: 1.56 / 1.50 / 1.47
- 分区:
  - /overlay (sdb3): 73% ← 超过80%告警阈值，需关注
  - sdb4: 8% 正常
  - sda1: 29% 正常
- OpenClash: 未通过 systemctl 检测，CLI 不在 /usr/bin/openclash
- Tailscale: istoreos-1 online，istoreos/zhanglihua offline
- Tailscale serve: 无 serve 配置（正常）

## SSL 证书（ssl-cert-check.sh）
- Gateway 本地证书: 正常（335天/361天）
- 4 个过期证书: 均为 go module testdata / 无效测试证书，无实际业务影响

## 磁盘趋势（disk-trend-analyze.sh）
- 数据已更新: 2026-09-17 21:06

## 告警
- ⚠️ iStoreOS /overlay 73% 接近 80% 阈值，建议清理 sdb3 空间
