#!/usr/bin/env bash
set -euo pipefail
if [[ $# -ne 1 || ! -f "$1" ]]; then
  echo "audio file required" >&2
  exit 2
fi
tmp_audio="$(mktemp --suffix=.wav)"
trap 'rm -f -- "$tmp_audio"' EXIT
ffmpeg -hide_banner -nostdin -loglevel error -y -i "$1" -ac 1 -ar 16000 "$tmp_audio"
/home/ubuntu/.openclaw/workspace/voice-v2/whisper.cpp/build/bin/whisper-cli \
  -m /home/ubuntu/.openclaw/workspace/voice-v2/whisper.cpp/models/ggml-base.bin \
  -f "$tmp_audio" -t 2 -np -nt -l zh
