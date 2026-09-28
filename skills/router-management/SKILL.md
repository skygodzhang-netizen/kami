---
name: router-management
description: Read iStoreOS router health and use the authoritative network mutation lock. Use only for owner-authorized router operations.
---

# Router management

Use the node-local wrapper. On Ubuntu call `scripts/routerctl-remote.sh ACTION`. On iStoreOS call `routerctl read ACTION`.

Allowed read actions: `identity`, `network`, `wan`, `lan`, `dhcp`, `dns`, `firewall`, `openclash`, `lucky`, `openclaw`, `storage`, `ubuntu-health`, `ubuntu-gateway`.

Before any network, firewall, DHCP, DNS, OpenClash, route, SSH, or management ACL mutation, acquire the iStoreOS authoritative lock with `routerctl lock-acquire OWNER SOURCE OPERATION TTL`. Back up the exact configuration, validate it, establish rollback, apply, verify WAN/LAN/DNS and management connectivity, then release with `routerctl lock-release OWNER`.

Never disable authentication or the firewall, create ANY-to-ANY rules, expose LuCI publicly, share node identities, or bypass the lock.
