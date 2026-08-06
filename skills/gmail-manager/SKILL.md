# Gmail Manager Skill

## Purpose

管理 Gmail 邮件。

运行环境：
Ubuntu AI Server

功能：

- 查询邮件
- 获取未读邮件
- 邮件摘要
- 重要邮件提醒
- 每日邮件报告


## Gmail API

使用 OAuth2.

认证文件：

~/.openclaw/secrets/gmail/


## Commands


查看今日邮件：

gmail_today


查看未读：

gmail_unread


生成日报：

gmail_daily_report


## Rules

不要删除邮件。

不要发送邮件。

涉及外部发送必须确认。
