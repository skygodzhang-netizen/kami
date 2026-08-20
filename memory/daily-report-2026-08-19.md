# 2026-08-19 日报

## 系统概览
| 设备 | 状态 | 备注 |
|------|------|------|
| Ubuntu AI Server | ✅ 正常 | 运行5天12小时 |
| iStoreOS 路由器 | ✅ 正常 | 运行5天12小时 |
| Home Assistant | ✅ 在线 | 19实体 |
| OpenClash | ✅ 运行中 | |
| Tailscale | ✅ 运行中 | zhanglihua offline |
| 摄像头 | ✅ 2/2 在线 | 卧室、客厅 |

## Ubuntu AI Server 详情
- 负载：0.37
- 内存：1.6Gi / 3.8Gi (42%)
- 磁盘 /：17% (78G free)
- Docker：homeassistant Up 40h
- OpenClaw Gateway：active (18h)
- 安全日志：无异常（3次失败尝试）
- 网络：DNS/互联网正常

## iStoreOS 路由器 详情
- 负载：1.09
- 内存：4.7Gi / 7.6Gi (62%)
- Overlay：72% (531MB free)
- 数据盘 sdb4：8% | sda1：23%
- OpenClash：running
- Tailscale：running ✅
- WAN：pppoe-wan 在线
- 内网设备：5台在线

## SSL 证书
- gateway.pem：剩余 364 天 ✅
- ⚠️ Caddy 中间证书：预计 8月22日到期（约4天）

## 安全邮件
- 无新增高危事件 ✅

## 磁盘趋势
- 数据采集正常，趋势文件已更新

## 待处理事项
1. 🟡 Caddy 中间证书到期预警（8月22日）
2. 🟡 7个系统包可升级
3. ℹ️ Tailscale zhanglihua 离线

## 结论
系统运行稳定，无紧急问题。Caddy 中间证书将在约4天后到期，建议届时检查是否需要手动续期。