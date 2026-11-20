#!/bin/sh
# HELP: SPDW Factory multi-OS profile browser preview
# GRID: SGRUB

set -eu

# Official muOS application lifecycle: CPU governor, HOME/XDG, SDL input
# mapping, foreground-process tracking and application control profile.
. /opt/muos/script/var/func.sh

APP_BIN="sgrub"
SETUP_APP "$APP_BIN" "modern"

# MUOS_STORE_DIR is the SD1/SD2-neutral runtime storage bind mount.
APP_DIRECTORY="$MUOS_STORE_DIR/application/RTBM-SGRUB"
cd "$APP_DIRECTORY" || exit 1

export SDL_VIDEO_CENTERED=1
export SDL_RENDER_SCALE_QUALITY=1

# Optional device-verified SDL mapping. The stock muOS mapping remains the
# default when no per-app override is installed.
if [ -f "$APP_DIRECTORY/gamecontrollerdb.txt" ]; then
    "./$APP_BIN" --fullscreen --mapping-file "$APP_DIRECTORY/gamecontrollerdb.txt" "$@"
else
    "./$APP_BIN" --fullscreen "$@"
fi
