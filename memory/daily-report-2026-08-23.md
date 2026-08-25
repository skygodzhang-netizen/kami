# 日报 — 2026-08-23（周日）

## 晚检 (21:00 CST)

### Ubuntu AI Server ✅
- **运行时间**: 2天23小时
- **负载**: 0.19 (idle 95%)
- **内存**: 1.6Gi / 3.8Gi (42%) | 空闲 2.2Gi
- **磁盘 /**: 17% (78G free) ✅
- **Docker**: homeassistant Up 3 days ✅
- **服务**: openclaw-gateway ✅, caddy ✅, docker ✅

### iStoreOS 路由器 ✅
- **运行时间**: 9天3小时
- **负载**: 1.35
- **内存**: 4.5Gi / 7.6Gi (62%) | 空闲 3.1Gi
- **分区**:
  - overlay: 72% ✅
  - sdb4: 8% ✅
  - sda1: 23% ✅
- **OpenClash**: running ✅
- **Tailscale**: running ✅ (无 serve 配置)

### SSL 证书 ✅
- gateway.pem: 剩余 360 天
- 所有 9 个证书正常

### 安全邮件 ✅
- 扫描完成，无新增异常

### 磁盘趋势 ✅
- 数据已采集，趋势稳定

### 异常记录
- ⚠️ openclaw-gateway 日志中有 memory sync 失败警告（node-llama-cpp 缺失）
- ⚠️ update_goal 调用失败（goal 不存在）

---

## 总结
系统整体运行稳定 ✅，无紧急事项，无需处理。
