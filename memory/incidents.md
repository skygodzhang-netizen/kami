# Incident History

## 2026-08-25

事件：
OpenClaw Gateway /health 端点空响应

现象：
- 服务进程运行正常（PID 24879）
- systemctl 显示 active (running)
- 但 /health 端点返回空响应

原因：
待排查

处理：
已记录，持续监控

状态：
待处理

---

## 2026-08-25

事件：
HA /health 端点返回空响应

现象：
- HA API /api/ 正常 (200)
- 但 /health 端点返回空响应

原因：
待排查

处理：
已记录，持续监控

状态：
待处理

---

## 2026-08-22

事件：
OpenClaw Gateway 服务未运行

现象：
- 健康检查返回 000
- 进程检查未找到 openclaw 进程

原因：
待排查

处理：
已修复，服务恢复运行

状态：
已解决
