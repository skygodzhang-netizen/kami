---
name: docker-manager
description: Manage Docker containers on Ubuntu AI Server and iStoreOS. Use for container status, logs, restart, images, volumes, networks, compose and cleanup.
---

# Docker Manager

Use this skill whenever the user asks about Docker.

## Ubuntu

Use local docker commands:

```bash
docker ps
docker ps -a
docker images
docker logs <container>
docker restart <container>
docker stop <container>
docker start <container>
docker exec -it <container> sh
docker system df
docker system prune
```

## iStoreOS

Use SSH:

```bash
ssh root@192.168.100.1 "docker ps"
ssh root@192.168.100.1 "docker images"
ssh root@192.168.100.1 "docker logs <container>"
ssh root@192.168.100.1 "docker restart <container>"
```

Always determine whether the user refers to Ubuntu or iStoreOS before executing commands.
