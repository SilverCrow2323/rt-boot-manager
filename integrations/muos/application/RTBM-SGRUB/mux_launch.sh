#!/bin/sh
# muOS application entry point for the SGRUB profile-browser preview.
# This is launched by the normal Applications frontend, not by user-init.

set -eu

APP_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
if [ ! -x "$APP_DIR/sgrub" ]; then
    printf '%s\n' "SGRUB executable is missing: $APP_DIR/sgrub" >&2
    exit 1
fi

export SDL_VIDEO_CENTERED=1
export SDL_RENDER_SCALE_QUALITY=1

# Optional SDL GameController database: users can place a device-verified
# gamecontrollerdb.txt beside the binary without modifying the launcher.
if [ -f "$APP_DIR/gamecontrollerdb.txt" ]; then
    exec "$APP_DIR/sgrub" --fullscreen --mapping-file "$APP_DIR/gamecontrollerdb.txt" "$@"
fi

exec "$APP_DIR/sgrub" --fullscreen "$@"
