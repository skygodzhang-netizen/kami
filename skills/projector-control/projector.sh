#!/bin/bash
# projector.sh — OpenClaw projector-control skill
# Device config: skills/projector-control/config.env
# Safety: auto-mode covers navigation/volume/screenshot/app-launch; power NOT exposed.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "$SCRIPT_DIR/config.env"
SERIAL="${PROJECTOR_SERIAL:-${PROJECTOR_HOST}:5555}"

adb_cmd() { adb -s "$SERIAL" "$@"; }

connect() {
  # 1) already connected?
  if adb devices 2>/dev/null | grep -q "^${SERIAL}[[:space:]]\+device$"; then
    return 0
  fi
  # 2) retry up to 3 times
  local attempt=1
  while [ $attempt -le 3 ]; do
    adb connect "$SERIAL" >/dev/null 2>&1
    sleep 2
    if adb devices 2>/dev/null | grep -q "^${SERIAL}[[:space:]]\+device$"; then
      return 0
    fi
    attempt=$((attempt+1))
  done
  echo "PROJECTOR_OFFLINE"
  return 1
}

cmd="${1:-}"
shift || true

case "$cmd" in
  connect)
    if connect; then echo "CONNECTED"; else exit 1; fi
    ;;
  status)
    if ! connect; then exit 1; fi
    echo "boot_completed=$(adb_cmd shell getprop sys.boot_completed)"
    echo "uptime=$(adb_cmd shell uptime)"
    echo "foreground=$(adb_cmd shell dumpsys window 2>/dev/null | grep mCurrentFocus | head -1 | sed 's/.*Window{[^}]* }u0 //')"
    ;;
  current-app)
    if ! connect; then exit 1; fi
    adb_cmd shell dumpsys window 2>/dev/null | grep mCurrentFocus | head -1
    ;;
  home)
    if ! connect; then exit 1; fi
    adb_cmd shell input keyevent KEYCODE_HOME && echo "HOME sent"
    ;;
  back)
    if ! connect; then exit 1; fi
    adb_cmd shell input keyevent KEYCODE_BACK && echo "BACK sent"
    ;;
  up|down|left|right)
    if ! connect; then exit 1; fi
    case "$cmd" in
      up) k=DPAD_UP;; down) k=DPAD_DOWN;; left) k=DPAD_LEFT;; right) k=DPAD_RIGHT;;
    esac
    adb_cmd shell input keyevent "KEYCODE_${k}" && echo "${cmd} sent"
    ;;
  ok)
    if ! connect; then exit 1; fi
    adb_cmd shell input keyevent KEYCODE_DPAD_CENTER && echo "OK sent"
    ;;
  volume-up)
    if ! connect; then exit 1; fi
    adb_cmd shell input keyevent KEYCODE_VOLUME_UP && echo "volume up sent"
    ;;
  volume-down)
    if ! connect; then exit 1; fi
    adb_cmd shell input keyevent KEYCODE_VOLUME_DOWN && echo "volume down sent"
    ;;
  play-pause)
    if ! connect; then exit 1; fi
    if adb_cmd shell dumpsys media_session 2>/dev/null | grep -qE 'active [1-9]|[1-9] Sessions'; then
      adb_cmd shell input keyevent KEYCODE_MEDIA_PLAY_PAUSE && echo "play-pause sent"
    else
      echo "SKIPPED: no active media session"
    fi
    ;;
  screenshot)
    if ! connect; then exit 1; fi
    out="${1:-/tmp/projector-shot.png}"
    adb_cmd shell screencap -p /sdcard/openclaw-proj-shot.png 2>/dev/null
    adb_cmd pull /sdcard/openclaw-proj-shot.png "$out" >/dev/null 2>&1
    adb_cmd shell rm /sdcard/openclaw-proj-shot.png 2>/dev/null
    echo "screenshot: $out ($(stat -c%s "$out" 2>/dev/null || echo 0) bytes)"
    ;;
  apps)
    if ! connect; then exit 1; fi
    adb_cmd shell pm list packages 2>/dev/null | grep -vE '^package:com\.android\.|^package:android\.|^package:com\.example\.|^package:com\.sohu\.' \
      | sed 's/^package://' | sort
    ;;
  launch-app)
    if ! connect; then exit 1; fi
    app="${1:-}"
    # Verified whitelist from 2026-09-25 inventory (package -> launch activity).
    # Add new entries ONLY after verifying with:
    #   adb -s $SERIAL shell pm dump <pkg> | grep -A2 MAIN
    case "$app" in
      launcher|当贝)  pkg="com.dangbei.mimir.lightos.launcher"; act="" ;;
      settings|设置)  pkg="com.android.tv.settings";            act="com.android.tv.settings.MainSettings" ;;
      网易云|netease|music) pkg="com.netease.cloudmusic.tv";    act="" ;;
      mxplayer|mx)   pkg="com.mxtech.videoplayer.pro";         act="pro.videoplayer.mx.VMActivity" ;;
      爱思影视|cibn)  pkg="com.cibn.tv";                        act="" ;;
      when|当贝桌面)  pkg="com.dangbei.mimir.lightos.launcher"; act="" ;;
      云视視極光|k_tcp|k_tcp|ktcp_tvvideo) pkg="com.ktcp.tvvideo"; act="com.ktcp.video.activity.MainActivity" ;;
      *) echo "APP_NOT_IN_WHITELIST: $app"; exit 2 ;;
    esac
    # Confirm installed
    if ! adb_cmd shell pm list packages 2>/dev/null | grep -q "^package:${pkg}$"; then
      echo "APP_NOT_INSTALLED: ${pkg}"; exit 3
    fi
    # Determine launch: explicit activity, or monkey with MAIN category
    if [ -n "$act" ]; then
      adb_cmd shell am start -n "${pkg}/${act}" 2>/dev/null && echo "launched: ${pkg}/${act}"
    else
      if adb_cmd shell monkey -p "$pkg" 1 >/dev/null 2>&1; then
        echo "launched: ${pkg} (monkey MAIN)"
      else
        echo "APP_NOT_LAUNCHABLE: ${pkg}"; exit 4
      fi
    fi
    ;;
  power)
    # Intentionally NOT available in auto mode.
    echo "POWER_NOT_ALLOWED: high-risk action not enabled. Requires explicit operator request; use smart-plug/HA for cold power, see SKILL.md."
    exit 5
    ;;
  *)
    echo "usage: projector.sh <connect|status|current-app|home|back|up|down|left|right|ok|volume-up|volume-down|play-pause|screenshot|apps|launch-app|power>"
    exit 64
    ;;
esac
