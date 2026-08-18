# Incident History


## 2026-07-19

事件:
iStoreOS tailscale 443冲突提示


现象:

巡检发现tailscale相关443问题


原因:

旧 tailscale serve 配置


排查:

确认443实际占用:

uhttpd


结果:

正常


处理:

清理tailscale serve配置


最终状态:

已解决


规则:

以后只检查tailscale服务状态
不检查443占用


---


## 2026-07-18

事件:

Phase 2 自动化上线


内容:

- 安全邮件监控
- SSL检测
- 磁盘趋势
- Docker健康检查


结果:

稳定运行
