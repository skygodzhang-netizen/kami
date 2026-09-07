# 每日报告 — 2026-09-07（周一）

## 概览

| 设备 | 状态 | 备注 |
|------|------|------|
| Ubuntu AI Server | ✅ 正常 | 运行 5 天，负载低，磁盘 17% |
| iStoreOS 路由器 | ✅ 正常 | 运行 5 天，负载正常，overlay 73% |
| Home Assistant | ✅ 正常 | Up 5 days |
| OpenClaw Gateway | ✅ 正常 | 运行中 |
| OpenClash | ✅ 正常 | running |
| Tailscale | ✅ 正常 | running |

## SSL 证书状态

- `gateway.pem` — 剩余 **346 天**（2027-08-19 过期）✅

## 磁盘状态

### Ubuntu AI Server
- `/dev/sda2` (/) — **17%**（98G 总量，78G 可用）✅

### iStoreOS 路由器
- `/dev/sdb3` (overlay) — **73%**（1.9G 总量，525M 可用）✅ 只监控
- `/dev/sdb4` — 数据盘，约 8% 使用 ✅
- `/dev/sda1` — 数据盘，约 19% 使用 ✅

## 巡检统计

- 今日巡检次数：20 次（完整）
- 异常事件：0 次
- 安静时段：23:00–08:00 CST（本日为首次完整安静时段）

## 结论

✅ 全部系统正常运行，无异常。

---
*报告生成时间：2026-09-07 05:01 CST*

## 09:00 CST 巡检 (01:00 UTC)

| 设备 | 状态 | 备注 |
|------|------|------|
| Ubuntu AI Server | ✅ 正常 | 运行 6 天，负载 0.19，磁盘 17% |
| iStoreOS 路由器 | ✅ 正常 | 运行 6 天，负载 1.39，overlay 73% |
| Home Assistant | ✅ 正常 | Up 6 days |
| OpenClaw Gateway | ✅ 正常 | 运行中 |
| OpenClash | ✅ 正常 | running |
| Tailscale | ✅ 正常 | running |
| SSL 证书 | ✅ 正常 | 剩余 346 天 |
| 安全邮件 | ✅ 无异常 | 无新增高危/警告 |

**结论：** 全部正常 ✅
