---
name: projector-control
version: 1.0.0
description: 控制当贝/RK3128 投影仪（192.168.100.199:5555）的 ADB 遥控 Skill：导航、音量、截图、App 启动、状态查询。冷开机不可用，需设备已通电并开启网络 ADB。
---

# projector-control

Control the living-room projector (Rockchip RK3128, Android 9) from Ubuntu OpenClaw over ADB-over-TCP.

## Device

Single source of truth: `/home/ubuntu/.openclaw/workspace/skills/projector-control/config.env`

```
PROJECTOR_HOST=192.168.100.199
PROJECTOR_PORT=5555
PROJECTOR_SERIAL=192.168.100.199:5555
```

Known device facts (verified 2026-09-25):
- model=PROJECTOR, manufacturer=rockchip, device=rk3128_box, Android 9.0 / SDK 25
- Launcher: `com.dangbei.mimir.lightos.launcher` (当贝 LightOS / LeRACD)
- ADB requires the projector to be powered on with "网络ADB" enabled; ADB CANNOT PROVIDE COLD POWER-ON
- After a projector power cycle, re-run `connect` before any command

## Commands

All commands run through `sh /home/ubuntu/.openclaw/workspace/skills/projector-control/projector.sh <cmd>`.

| Command | Effect | Safety |
|---|---|---|
| `status` | connection + boot state + foreground app | auto |
| `connect` | ensure ADB session (max 3 retries) | auto |
| `home` / `back` | KEYCODE_HOME / KEYCODE_BACK | auto |
| `up` `down` `left` `right` `ok` | DPAD_* / DPAD_CENTER | auto |
| `volume-up` `volume-down` | media volume | auto |
| `play-pause` | media toggle; SKIPPED if no active media session | auto |
| `current-app` | foreground window/activity | auto |
| `apps` | installed app inventory (key apps, no full system dump) | auto |
| `screenshot [out]` | screencap + pull to `/tmp` (default `/tmp/projector-shot.png`) | auto |
| `launch-app <name>` | launch by known app name from built-in whitelist | auto |
| `power` | intentionally NOT implemented in auto mode; requires explicit `--confirm-power` | HIGH RISK, never in tests |

## Connection recovery

Every command runs `connect` first:
1. check `adb devices` for `PROJECTOR_SERIAL` in state `device`
2. if missing/offline/unauthorized → `adb connect` once
3. retry up to 3 times, 2s apart
4. still failing → print `PROJECTOR_OFFLINE` and exit 1 (never loop forever, never change projector settings)

## App launch whitelist

`launch-app` resolves the target against a hardcoded whitelist (package + launch activity verified from `pm list packages` + `pm dump` on this device). No guessed package names.
- not installed → `APP_NOT_INSTALLED`
- installed but no launchable MAIN activity → `APP_NOT_LAUNCHABLE`

Never installs/uninstall APKs.

## Safety gates

Auto-executable: home, back, direction, ok, volume, play-pause, status, current-app, screenshot, launch known app.
Requires explicit operator confirmation (not wired into `projector.sh` auto mode): power off, reboot, install/uninstall APK, clear app data, system setting changes.
Forbidden: root, factory reset, system partition modification.

## Power note

KEYCODE_POWER can be identified but is NOT exposed in auto mode. Investigated: projector ADB is only reachable while the device is powered on (Wi-Fi/ADB stay up in on-state; cold power-off drops TCP). **ADB CANNOT PROVIDE COLD POWER-ON.** Recommended future method: keep a smart-plug/relay (HA controllable) for cold power, and use this ADB skill for everything else.
