# Solutions Library


## OpenClaw Gateway


问题:

Gateway异常


检查:

systemctl status openclaw-gateway


处理:

先检查日志

不要直接重装



---


## iStoreOS磁盘


规则:

overlay系统盘:

>80%

只通知


数据盘:

>85%

提供建议


禁止:

自动删除系统文件



---


## Docker


规则:

异常检测:

允许


自动恢复:

暂未开启


白名单:

等待Phase 2.2



---


## Tailscale


用途:

远程访问


注意:

不要使用serve代理OpenClaw


443:

由uhttpd管理
