# Gmail 使用规则

当前 Gmail 状态：

账号：
skygodzhang@gmail.com

认证方式：
Google OAuth + gog

状态：
正常


规则：

1. 不要要求用户重复 OAuth 授权。
2. 不要要求重新上传 client_secret.json。
3. 判断 Gmail 是否可用时，优先执行：

gog gmail search "newer_than:7d"

4. 只有 gog 命令明确返回认证错误时，才提示重新授权。


当前已验证：

2026-07-21

gog gmail search:
成功返回邮件列表。
