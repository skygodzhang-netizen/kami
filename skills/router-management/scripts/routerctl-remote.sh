#!/bin/sh
set -eu
case "${1:-}" in
 identity) cmd='cat /proc/sys/kernel/hostname; ubus call system board';;
 network) cmd='ip -br addr; ip route';;
 wan) cmd='ubus call network.interface.wan status';;
 lan) cmd='ubus call network.interface.lan status';;
 dhcp) cmd='pgrep -a dnsmasq; uci show dhcp';;
 dns) cmd='pgrep -a dnsmasq; cat /tmp/resolv.conf.d/resolv.conf.auto 2>/dev/null || true';;
 firewall) cmd='uci show firewall.@defaults[0]; nft list ruleset | sed -n "1,80p"';;
 openclash) cmd='/etc/init.d/openclash status; pgrep -a clash';;
 lucky) cmd='/etc/init.d/lucky status; pgrep -a lucky; netstat -lntp 2>/dev/null | grep lucky';;
 openclaw) cmd='docker inspect --format "{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{end}} {{.HostConfig.RestartPolicy.Name}}" openclaw-vps-istoreos';;
 storage) cmd='mount | grep /mnt/sata2-4; df -h /overlay /mnt/sata2-4';;
 *) echo 'denied: action is not in the router read allowlist' >&2; exit 77;;
esac
exec ssh -i /home/ubuntu/.ssh/id_ed25519 -o IdentitiesOnly=yes -o BatchMode=yes -o ConnectTimeout=8 root@192.168.100.1 "$cmd"
