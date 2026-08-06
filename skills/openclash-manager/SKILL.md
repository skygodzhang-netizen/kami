---
name: openclash-manager
description: Manage OpenClash on iStoreOS through SSH. Use for status, restart, logs, configuration and Mihomo diagnostics.
---

# OpenClash Manager

Always connect through SSH:

```bash
ssh root@192.168.100.1
```

## Status

```bash
/etc/init.d/openclash status
```

## Restart

```bash
/etc/init.d/openclash restart
```

## Stop

```bash
/etc/init.d/openclash stop
```

## Start

```bash
/etc/init.d/openclash start
```

## Logs

```bash
logread | grep OpenClash
```

## Mihomo

```bash
pgrep -a mihomo
```

## Config

```bash
ls /etc/openclash/
```

When the user asks anything about OpenClash, use these commands before answering.
