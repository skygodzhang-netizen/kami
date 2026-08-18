# Environment Memory — 环境状态
# 技术环境、网络状态、运行状态

## 技术环境

### VPS (Ubuntu AI Server)
- **状态**: ✅ 运行中
- **OpenClaw Gateway**: running (pid 54878)
- **Caddy**: active
- **Docker**: 运行中
- **Home Assistant**: 运行中

### 网络
- **WAN**: pppoe-wan 在线
- **内网**: 192.168.100.x
- **代理**: OpenClash (台湾节点)
- **DNS**: 独立策略

### 服务状态
| 服务 | 状态 | 备注 |
|------|------|------|
| OpenClaw | ✅ | Gateway + main agent |
| Caddy | ✅ | HTTPS proxy |
| Docker | ✅ | 多容器运行 |
| HA | ⚠️ | 状态待确认 |
| OpenClash | ✅ | 代理管理 |
| Tailscale | ✅ | VPN 覆盖 |

## 历史故障记录
- **2026-08-04/05**: Google 账户安全警报（用户本人操作，非异常）
- **2026-08-17**: Caddy 证书过期 → 已修复，迁移到手动管理
- **2026-08-17**: OpenAI API Key 401 → 已更换新 Key，但 quota 不足

## 经验总结
- Caddy `tls internal` 模式只签发 12 小时证书，不适合生产
- 手动证书应放在 `/etc/caddy/certs/` 并由 root:caddy 组管理
- OpenClaw 配置修改后需要 `systemctl restart openclaw-gateway`

---

*最后更新: 2026-08-17*
