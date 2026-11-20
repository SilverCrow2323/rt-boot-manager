#!/bin/sh
# Assemble a muOS .muxapp archive from the native SDL2 build.

set -eu

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
BINARY="$ROOT/ui/sgrub/native/build/sgrub"
LAUNCHER="$ROOT/integrations/muos/application/RTBM-SGRUB/mux_launch.sh"
DIST="$ROOT/dist"
STAGE="$(mktemp -d)"

cleanup() {
    rm -rf "$STAGE"
}
trap cleanup EXIT HUP INT TERM

if [ ! -x "$BINARY" ]; then
    printf '%s\n' "SGRUB binary not found. Build it first with make -C ui/sgrub/native." >&2
    exit 1
fi
if ! command -v zip >/dev/null 2>&1; then
    printf '%s\n' "The zip utility is required to create a .muxapp archive." >&2
    exit 1
fi

APP="$STAGE/RTBM-SGRUB"
mkdir -p "$APP"
install -m 0755 "$BINARY" "$APP/sgrub"
install -m 0755 "$LAUNCHER" "$APP/mux_launch.sh"

cat > "$APP/README.txt" <<'EOF'
Rt:BOOT MANAGER - SGRUB preview

This package is an SDL2 profile-browser preview for the Anbernic RG35XX H.
It displays the muOS, ROCKNIX and KNULLI profile catalogue.

IMPORTANT:
- This preview does not boot another operating system.
- It does not reboot the device.
- It does not write partitions, bootloader regions or U-Boot variables.
- The BOOT HANDOFF status is intentionally shown as NOT CONNECTED.

Controls:
- D-pad: move through profiles
- A: open profile details
- B: return / exit
- Y: set the session default

Install the .muxapp with muOS Archive Manager. Remove the RTBM-SGRUB
application folder from MUOS/application to uninstall this preview.
EOF

mkdir -p "$DIST"
rm -f "$DIST/rtbm-sgrub.muxapp"
(cd "$STAGE" && zip -qr "$DIST/rtbm-sgrub.muxapp" RTBM-SGRUB)
printf 'Created %s\n' "$DIST/rtbm-sgrub.muxapp"
