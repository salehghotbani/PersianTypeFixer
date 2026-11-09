#!/bin/bash
set -eu

export XDG_RUNTIME_DIR="$(mktemp -d)"
export XDG_CONFIG_HOME="$XDG_RUNTIME_DIR/config"
export WAYLAND_DISPLAY=wayland-smoke
export XDG_SESSION_TYPE=wayland
unset DISPLAY QT_QPA_PLATFORM

weston --backend="$1" --socket="$WAYLAND_DISPLAY" --idle-time=0 --no-config >"$XDG_RUNTIME_DIR/weston.log" 2>&1 &
compositor=$!
trap 'kill "$compositor" 2>/dev/null || true; rm -rf -- "$XDG_RUNTIME_DIR"' EXIT
for i in {1..50}; do
    test ! -S "$XDG_RUNTIME_DIR/$WAYLAND_DISPLAY" || break
    sleep 0.1
done
test -S "$XDG_RUNTIME_DIR/$WAYLAND_DISPLAY" || { cat "$XDG_RUNTIME_DIR/weston.log"; exit 1; }

result=0
timeout 4s /opt/persiantypefixer/PersianTypoFixer || result=$?
test "$result" -eq 124
