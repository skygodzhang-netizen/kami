# Daily Report 2026-09-22

## Ubuntu AI Server (host: ubuntu-ai, 192.168.100.108)
- Uptime: 21 days, load 0.06/0.09/0.09 (low).
- Memory: 1.4Gi/3.8Gi used, 2.5Gi available. Swap 295Mi/2Gi.
- Disk /dev/sda2: 21G/98G (23%) — OK.
- Docker: homeassistant Up 3 weeks; docker active.
- OpenClaw Gateway: port 18789 listening, service active.
- Home Assistant: :8123 HTTP 200, service inactive as systemd unit (runs under Docker).
- Security mail check: no findings.

## iStoreOS (192.168.100.1)
- Load avg: 1.56/1.50/1.42 (1.9G/1.4G RAM busy but ~3G available).
- /overlay: 73% of 1.9G (<80% threshold) OK; /: 73%.
- sdb4: 8% (OK, <85%); sda1: 31% (OK, <85%).
- OpenClash: config enable=1, mode fake-ip-mix; running under uci.
- Tailscale: istoreos-1 online (100.123.106.24); istoreos and zhanglihua offline.
- Tailscale serve: no config — normal.

## SSL certs
- 16 scanned, 4 problem certs all inside /home/ubuntu/go/pkg/mod (test fixtures / dev-only). No production cert issues.

## Disk trend
- Trend data updated at 2026-09-22 21:01 CST.

## Anomalies / decisions needed
- None. All within thresholds. Router Tailscale peers offline (historical, not new).
