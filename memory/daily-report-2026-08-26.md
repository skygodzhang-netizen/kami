# 2026-08-26 晚检报告

## Ubuntu AI Server (192.168.100.108)
- **负载**: 0.16 (1m), 0.09 (5m), 0.05 (15m) ✅
- **内存**: 1.2G / 3.8G (31%) ✅
- **磁盘 /**: 16G / 98G (17%) ✅
- **Docker**: homeassistant Up 6 days ✅
- **OpenClaw Gateway**: active ✅
- **安全日志**: 无异常登录 ✅
- **系统更新**: 5 个包可升级（byobu, console-setup, keyboard-configuration, open-vm-tools, snapd）⚠️ 非紧急
- **SSL 证书**: 全部正常，最近 93 天（Homebrew）✅
- **HA Camera**: bedroom_camera idle ✅

## iStoreOS 路由器 (192.168.100.1)
- **负载**: 1.00 (1m), 1.11 (5m), 1.14 (15m) ✅
- **内存**: 4.7G / 7.9G (60%) ✅
- **分区 overlay (sdb3)**: 1.4G / 1.9G (73%) ✅ 未超 80%
- **分区 sdb4**: 1.9G / 26.5G (8%) ✅
  - Docker: 726MB | OpenClaw: 513MB | Configs: 376MB
- **分区 sda1**: 24G / 109.5G (23%) ✅
  - ubuntu24.qcow2: ~21GB | iso: ~3.3GB
- **OpenClash**: running ✅
- **Tailscale**: 运行中，无 serve 配置 ✅
- **Docker**: 未运行 ✅

## 磁盘趋势
- 数据采集完成: 2026-08-26 21:00 CST ✅

## 安全邮件
- 无新邮件 ✅

## 异常摘要
- 无告警，所有指标正常
