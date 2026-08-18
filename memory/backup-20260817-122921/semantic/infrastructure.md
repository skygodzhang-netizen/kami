# Semantic Memory — 事实记忆
# 持久化知识、技术架构、配置信息

## 基础设施

### Ubuntu AI Server (192.168.100.108)
- **系统**: Ubuntu 24.04
- **用途**: OpenClaw AI 运维中心
- **主要服务**: OpenClaw Gateway, Docker, Home Assistant, Caddy
- **内存基线**: ~3.8GB
- **磁盘规则**:
  - 系统盘 (overlay): 只监控，不自动清理
  - 数据盘 (sdb4): >85% 提醒，>90% 紧急
  - 数据盘 (sda1): 只监控

### iStoreOS 路由器 (192.168.100.1)
- **硬件**: Intel J4205
- **用途**: 软路由
- **主要服务**: OpenClash, Docker, Tailscale
- **分区**:
  - sdb3 (overlay): 系统盘
  - sdb4: Docker + OpenClaw 数据
  - sda1: 数据盘

### Home Assistant
- **位置**: Docker 容器 (homeassistant)
- **访问**: http://192.168.100.108:8123

### OpenClash
- **位置**: iStoreOS 路由器
- **功能**: 代理管理
- **特点**: 台湾节点，DNS 策略独立

## 技术栈
- **OpenClaw**: 2026.6.5
- **Docker**: 容器化管理
- **Caddy**: HTTPS 反向代理
- **Tailscale**: 远程访问

---

*最后更新: 2026-08-17*
