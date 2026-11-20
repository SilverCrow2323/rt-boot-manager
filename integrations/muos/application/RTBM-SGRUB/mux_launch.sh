#!/bin/sh
# HELP: SPDW Factory multi-OS profile browser preview
# GRID: SGRUB

set -eu

# Use the official muOS application lifecycle: SDL environment, governor,
# HOME/XDG setup, foreground tracking and clean return to the frontend.
. /opt/muos/script/var/func.sh

APP_BIN="sgrub"
SETUP_APP "$APP_BIN" "modern"

# Applications must use the SD1/SD2-neutral runtime bind mount.
APP_DIR="/run/muos/storage/application/RTBM-SGRUB"
cd "$APP_DIR"

export SDL_VIDEO_CENTERED=1
export SDL_RENDER_SCALE_QUALITY=1

# Optional SDL GameController database: users can place a device-verified
# gamecontrollerdb.txt beside the binary without modifying the launcher.
if [ -f "$APP_DIR/gamecontrollerdb.txt" ]; then
    exec "./$APP_BIN" --fullscreen --mapping-file "$APP_DIR/gamecontrollerdb.txt" "$@"
fi

exec "./$APP_BIN" --fullscreen "$@"
