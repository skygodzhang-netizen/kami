# 2026-08-10 安全审计日志

## 审计时间
2026-08-10 09:02 CST

## 审计结果摘要
- 高风险: 1项 (Home Assistant 暴露)
- 中风险: 2项 (SSH 无 fail2ban, OpenClaw Gateway 全接口监听)
- 低风险: 2项 (无磁盘加密, 无防火墙规则)
- 建议: 2项 (node-llama-cpp, Git未提交)

## 详细发现

### 🔴 高风险
1. **Home Assistant 暴露在所有接口**
   - `0.0.0.0:8123` 监听所有接口，无防火墙保护
   - 若服务器有公网IP (61.218.136.115)，HA 直接暴露在公网
   - **建议**: 限制HA只监听127.0.0.1或通过Caddy反向代理+认证

### 🟡 中风险
2. **SSH 无 fail2ban**
   - SSH 监听 0.0.0.0:22 和 [::]:22
   - PermitRootLogin=prohibit-password (仅允许密钥)
   - 但无 fail2ban 防护暴力破解
   - **建议**: 安装 fail2ban + 限制SSH来源IP

3. **OpenClaw Gateway 全接口监听**
   - 18789 端口监听 0.0.0.0
   - 当前 auth.mode=token，已启用token认证
   - **建议**: 通过Caddy反向代理+认证访问，或限制来源IP

### 🟢 低风险
4. **无磁盘加密**
   - 系统盘 sda2 ext4，无LUKS加密
   - **建议**: 如有敏感数据，考虑启用LUKS

5. **无防火墙规则**
   - ufw/firewalld/nftables 均未配置
   - **建议**: 配置基础防火墙规则

### 💡 建议
6. **node-llama-cpp 缺失**
   - OpenClaw memory sync 失败
   - **建议**: 安装或切换remote embedding provider

7. **Git 工作区有未提交改动**
   - 10+ 文件未提交 (disk-trend, memory等)
   - **建议**: 定期commit或确认是否需保留

## 审计命令
```
openclaw security audit --deep
openclaw gateway status --deep
```

## 下次审计建议
- 配置 ufw 基础规则
- 安装 fail2ban
- 限制 HA 暴露范围
