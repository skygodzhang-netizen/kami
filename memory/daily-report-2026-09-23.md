# Daily Report 2026-09-23

## Ubuntu AI Server (host: ubuntu-ai, 192.168.100.108)
- Uptime: 22 days, load 0.04/0.08/0.12 (low).
- Memory: 1.6Gi/3.8Gi used, 2.3Gi available. Swap 293Mi/2Gi.
- Disk /dev/sda2: 21G/98G (23%) — OK.
- Docker: homeassistant Up 3 weeks; docker service active.
- OpenClaw Gateway: port 18789 listening (pid 360732), OpenClaw 2026.9.4.
- Home Assistant: :8123 HTTP 401 (auth required = up); recent errors are external API connectivity (met.no, analytics, alerts.home-assistant.io), no container issues.
- Upgradable packages: docker-ce 5:29.7.2→29.8.1, containerd.io 2.3.3→2.3.5, base-files/byobu/console-setup patch levels. Non-critical; no action taken.

## iStoreOS (192.168.100.1)
- Load avg: 1.53/1.44/1.38 (normal for this box).
- /overlay: 73% of 1.9G (<80% threshold) OK.
- sdb4: 8% (OK, <85%); sda1: 32% (OK, <85%).
- OpenClash: API on port 9090 responding (401 unauthorized = running).
- Tailscale: istoreos-1 online (100.123.106.24); istoreos, zhanglihua offline (historical, no change).
- Tailscale serve: `No serve config` — normal, no reminder needed.

## SSL certs
- 16 scanned; gateway certs valid 329/355 days.
- 4 expired certs all inside /home/ubuntu/go/pkg/mod test fixtures — no production impact.

## Disk trend
- disk-trend-analyze.sh ran OK, data updated 2026-09-23 21:02 CST.

## Security mail
- security-mail-check.sh: scan complete, no findings.

## Anomalies / decisions needed
- None. All within thresholds. No notification required.
