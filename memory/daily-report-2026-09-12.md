# 📊 每日巡检报告 — 2026-09-12

## Ubuntu AI Server (192.168.100.108)
- [系统] up 11d | 负载 0.05-0.54（正常）；12:36-21:33 间 2 次瞬时高负载（libdxfrwx 编译，峰值 5.67，编译完成后回落）
- [磁盘] / : 18% (98G, 可用 77G)（较 17% 微升，编译产物写入）
- [内存] ~1.3-1.6Gi / 3.8Gi
- [Docker] homeassistant: Up 11 days
- [服务] Gateway: running

## iStoreOS 路由器 (192.168.100.1)
- [系统] up 11d | 负载 1.17-1.86（正常区间）；21:33 曾冲高至 15m 3.39（与 Ubuntu 编译时间重叠），已回落
- [磁盘] overlay /dev/sdb3: 73% (1.9G, 可用 525.4M) ← 只监控
- [服务] OpenClash: running | Tailscale: running
- [Tailscale serve] 配置存在于 _serve/e416（仅记录）

## SSL 证书
- 🟢 gateway.pem/crt: 剩余 340 天
- 共 9 个证书全部正常

## 安全邮件扫描
- 无高危事件

## 磁盘趋势
- 已采集（注意：脚本内部时间戳显示 05:01 CST 9/13，为脚本时区问题，数据正常）

## 可升级包（常规更新，非紧急）
- base-files、byobu、console-setup 系列
- containerd.io、docker-buildx-plugin、docker-ce-cli（Docker 相关）
- 建议下轮更新窗口统一处理

## 异常与处理
- 12:36 发现 Ubuntu 高负载 → 定位为用户发起的 libdxfrwx C 编译（cc1 并行），编译完成后自行回落，无需干预
- 21:33 路由器负载瞬时偏高（15m 3.39）→ 30 分钟后回落至 1.96，观察项关闭

## 巡检记录
- 本日（CST 09-12）共 5 条去重巡检条目（含晚检），全部正常
