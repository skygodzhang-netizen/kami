# Procedural Memory — 操作经验
# 如何操作、常见问题解决方案、SOP

## Docker 管理
```bash
# 查看容器状态
docker ps -a

# 查看日志
docker logs <container>

# 重启服务
docker restart <container>
```

## OpenClaw 管理
```bash
# 查看状态
openclaw gateway status

# 重启服务
sudo systemctl restart openclaw-gateway

# 查看配置
cat ~/.openclaw/openclaw.json
```

## Caddy 证书管理
```bash
# 查看证书
openssl x509 -in /etc/caddy/certs/server.crt -noout -dates

# 重启 Caddy
sudo systemctl restart caddy
```

## 巡检脚本
- 脚本位置: `~/.openclaw/workspace/scripts/ssl-cert-check.sh`
- 调度: 早检 09:00 CST，晚检 21:00 CST
- 日志: `~/.openclaw/workspace/memory/YYYY-MM-DD.md`

## 故障处理模式
1. 检查服务状态
2. 查看日志定位问题
3. 尝试修复
4. 验证结果
5. 记录到 incidents.md

---

*最后更新: 2026-08-17*
