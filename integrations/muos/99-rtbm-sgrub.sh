#!/bin/sh
# Rt:BOOT MANAGER / SGRUB — muOS user-init bridge.
# Post-kernel and asynchronous. This is NOT a pre-kernel bootloader.

set -u
LOG="/tmp/rtbm-muos-init.log"
printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S' 2>/dev/null || echo boot)" "SGRUB user-init hook entered" >> "$LOG"

find_root() {
    for candidate in \
        /mnt/mmc/MUOS/rt-boot-manager \
        /mnt/sdcard/MUOS/rt-boot-manager
    do
        if [ -d "$candidate" ]; then
            printf '%s\n' "$candidate"
            return 0
        fi
    done
    return 1
}

RTBM_HOME="$(find_root 2>/dev/null || true)"
if [ -z "$RTBM_HOME" ]; then
    printf '%s\n' "installation not found; no action taken" >> "$LOG"
    exit 0
fi

ENABLE_FILE="$RTBM_HOME/config/sgrub.enabled"
if [ ! -f "$ENABLE_FILE" ] || [ "$(cat "$ENABLE_FILE" 2>/dev/null || true)" != "1" ]; then
    printf '%s\n' "SGRUB autostart disabled; no action taken" >> "$LOG"
    exit 0
fi

SGRUB="$RTBM_HOME/bin/sgrub"
if [ ! -x "$SGRUB" ]; then
    printf '%s\n' "SGRUB frontend not installed; no action taken" >> "$LOG"
    exit 0
fi

# A future frontend must implement and test display/input hand-off before
# this optional launch path is enabled in a device package.
exec "$SGRUB" --mode muos-user-init --config "$RTBM_HOME/config/boot-manager.json" >> "$LOG" 2>&1
