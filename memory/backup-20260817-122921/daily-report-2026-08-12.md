# 2026-08-12 日报

## 系统总览

### Ubuntu AI Server ✅
- 运行时间: 21天22小时
- CPU负载: 0.12–0.73 (低，全天稳定)
- 内存: 1.5–1.6G/3.8G (可用 2.2–2.3G) ✓
- 磁盘 /: 17% (78G 可用) ✓
- Docker: homeassistant Up 35h ✓
- OpenClaw Gateway: 200 OK ✓
- Home Assistant: 200 OK ✓
- fail2ban: ✅ 已修复并运行（上午检发现未运行，现已 active）

### iStoreOS 路由器 ✅
- 运行时间: 21天22小时
- CPU负载: 0.23–1.09 (低，全天稳定)
- 内存: ~4.7G/7.9G (可用 ~3.2G) ✓
- 磁盘 overlay: 67% ✓
- /mnt/sata2-4: 8% ✓
- /mnt/data_sda1: 21% → 22% ⚠️ (夜间增长1%，建议关注)
- OpenClash: running ✓
- Tailscale: running ✓ (istoreos online, zhanglihua offline)
- Tailscale serve: 无配置 ✓

## SSL 证书
- 全部正常，最短有效期 **107 天**（至 2026-10-25）✅

## 磁盘趋势
- Ubuntu /: 稳定 17%，无异常增长 ✓
- iStoreOS overlay: 67%（稳定）✓
- iStoreOS sata2-4: 8%（稳定）✓
- iStoreOS data_sda1: 21% → 22%（夜间+1%，需关注后续趋势）

## Docker 状态
- homeassistant: Up 35h，Web 服务正常 ✓
- 容器健康：0 异常

## 安全邮件摘要
- 上次扫描: 2026-08-11 22:03 CST
- 无新增高危事件 ✅
- 历史遗留提醒（非紧急）:
  - PayPal: 数据删除请求跟踪（7月22日）
  - Bybit: 6/30 台湾新设备登录
  - GitHub: 设备验证（5–7月）

## AI 安全分析
- 风险等级: **低** (score: 0)
- 温度: 51°C

## 异常处理记录
| 时间 | 项目 | 问题 | 处理 |
|------|------|------|------|
| 21:00 CST | Ubuntu AI Server | fail2ban 未运行 | 已修复，当前 active ✅ |

## 待处理事项
- ⚠️ **iStoreOS /mnt/data_sda1 磁盘使用率增长**：从21%升至22%，建议持续监控未来2-3天趋势
- ℹ️ fail2ban 已于今日修复，确认其持续运行

---
**生成时间**: 2026-08-12 16:00 UTC (00:00 CST 次日)
**生成方式**: 自动巡检日报

---

## 安全邮件扫描 (18:03 CST)

| 等级 | 数量 | 说明 |
|------|------|------|
| 🔴 高危 | 10封 | Google 支付/订阅通知、Bybit 登录安全 |
| 🟡 警告 | 10封 | 验证码、安全快讯 |
| 🟢 普通 | 1封 | 账号恢复请求 |

**需关注事项:**
- Bybit 6/30 新设备登录（台中台湾）
- Google 5/30 重大安全性快讯
- Google 5/31 账号恢复请求

大部分为订阅/支付/验证码等常规通知。如上述异常登录或恢复请求非本人操作，建议立即检查相关账户安全设置。

**Telegram 通知**: 已发送 ✅
