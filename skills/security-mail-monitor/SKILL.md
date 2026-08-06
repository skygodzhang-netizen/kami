# Security Mail Monitor

安全邮件监控技能。

## 用途
监控 Gmail 中指定服务商的安全通知邮件，按风险等级分类，高危事件即时 Telegram 通知。

## 监控服务商
Google, Bybit, PayPal, GitHub, Cloudflare, CloudCone, OpenAI, Anthropic

## 风险等级
- 🔴 高危：密码修改、API Key 创建/删除、提现、付款方式修改、关闭安全验证、异常登录成功 → 立即 Telegram 通知
- 🟡 警告：新设备登录、异地登录、安全设置变化 → Telegram 摘要通知
- 🟢 普通：安全建议、营销邮件 → 仅记录日志

## 使用方式

### 手动扫描
```bash
bash /home/ubuntu/.openclaw/workspace/scripts/security-mail-check.sh
```

### 规则文件
规则定义在 `/home/ubuntu/.openclaw/workspace/config/security-rules.json`

### 日志
扫描日志写入 `memory/security-mail-log.txt`

## 限制
- 只读取 Gmail，不修改/删除邮件
- 只分析和分类，不执行任何账号操作
- 不自动回复任何邮件
