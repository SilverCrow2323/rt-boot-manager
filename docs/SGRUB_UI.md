# SGRUB graphical frontend

## Current implementation

The first graphical frontend is a native SDL2 application targeting the
RG35XX H's 640x480 display. It uses SDL2's software renderer and an embedded
bitmap font. It does not require X11, Wayland, SDL_ttf, SDL_image or a Python
runtime on the handheld.

The visible profile table is generated from the canonical catalog/os/*.json
manifests by tools/generate_sgrub_profiles.py. The native renderer must not
become a second source of truth for OS names, versions or boot modes.

The current build is deliberately a PROFILE-BROWSER PREVIEW:

- D-pad / arrow keys move between muOS, ROCKNIX and KNULLI.
- A / Enter opens the selected profile details.
- B / Escape returns or exits to the muOS application launcher.
- Y sets the default profile for the current application session only.
- A opens the release-history browser for the selected OS.
- The release browser reads the canonical release manifests and the separate muOS archive index.
- Release rows distinguish current baselines, stable history, legacy builds, checksum availability and hardware gates.
- A pins a release for the current SGRUB session; Y clears that pin and restores the current baseline.
- X opens the read-only hardware diagnostics screen from any SGRUB page; D does the same on a keyboard.
- Diagnostics report device-tree model/compatible strings, Linux-reported memory capacity, SDL output size and controller presence.
- DDR generation and panel/PCB revision are deliberately shown as unknown until positively identified.
- Session pins are memory-only: they are not written to the SD card or persisted after exit.
- muOS archive entries are shown as provider-link-only metadata until the exact device image and checksum are resolved.
- KNULLI legacy entries remain marked for checksum and hardware verification.
- No download, install, kernel switch, reboot, block-device scan or timeout-based autoboot is enabled.

The release browser is a read-only catalogue view. A session pin changes only
the version label shown by the preview; it does not download an image, install
a release, persist a pin or change the boot profile.

The status BOOT HANDOFF: NOT CONNECTED is intentional. Selecting a profile
does not start another kernel, request a reboot, alter the boot configuration
or write to storage. A boot adapter must be implemented and validated before
the UI can advertise a system as bootable.

## Build on a Linux development host

Install SDL2 development files and a C compiler, then run:

    python3 tools/generate_sgrub_profiles.py
    make -C ui/sgrub/native clean all
    ui/sgrub/native/build/sgrub --self-test

Run the preview window:

    ui/sgrub/native/build/sgrub

For a physical framebuffer/fullscreen test:

    ui/sgrub/native/build/sgrub --fullscreen

The optional --input-dump mode prints the controller name, GUID, SDL mapping,
button and axis counts, and incoming button/hat events. This helps collect a
mapping from the actual handheld without guessing its button order.

The SDL2 mapping-file loader is part of SDL since version 2.0.2. A device-verified SDL GameController database can be loaded explicitly:

    ui/sgrub/native/build/sgrub --input-dump --mapping-file ./gamecontrollerdb.txt

For the muOS app, place the verified file at
MUOS/application/RTBM-SGRUB/gamecontrollerdb.txt. The launcher detects it and
passes it to SDL automatically. The project does not enable an assumed H700
button mapping by default: controller GUIDs and SDL databases can vary between
firmware builds.

For a raw joystick that SDL does not recognize as a GameController, button
indices may be mapped explicitly with RTBM_RAW_A_BUTTON,
RTBM_RAW_B_BUTTON, RTBM_RAW_Y_BUTTON, RTBM_RAW_L1_BUTTON and
RTBM_RAW_R1_BUTTON. Leave them unset until the RG35XX H input report has
been collected. Raw joystick hats are used for D-pad navigation.

## Cross-compiling for muOS

muOS has no X11 or Wayland display server; handheld applications use the SDL2
library shipped by the firmware. Build against an ABI-compatible aarch64
toolchain and the device's SDL2 sysroot, rather than linking against a newer
desktop glibc and copying that binary onto the handheld.

Example, after preparing an aarch64 sysroot containing the firmware's SDL2
headers and library:

    make -C ui/sgrub/native clean all \
      CC=aarch64-linux-gnu-gcc \
      PKG_CONFIG_SYSROOT_DIR="$RTBM_SYSROOT" \
      PKG_CONFIG_LIBDIR="$RTBM_SYSROOT/usr/lib/pkgconfig:$RTBM_SYSROOT/usr/share/pkgconfig"

Toolchain and sysroot paths vary by host. Confirm the resulting executable's
ELF interpreter and required GLIBC symbol versions before deploying it.

## Build a muOS application archive

After building the binary against the target sysroot:

    sh tools/package_muos_sgrub.sh

The script creates dist/rtbm-sgrub.muxapp. Copy the archive to the ARCHIVE
folder at the root of SD1 and install it using muOS Archive Manager. It
installs as a normal application under MUOS/application/RTBM-SGRUB.

The launcher follows the official muOS application runner: it sources
/opt/muos/script/var/func.sh, calls SETUP_APP with the modern controller
profile, and uses MUOS_STORE_DIR for the SD1/SD2-neutral application path.
This gives muOS control of SDL environment setup, CPU governor, HOME/XDG and
foreground-process tracking. The launcher returns normally when SGRUB exits.

For the RG35XX H, muOS's own internal catalogue provides the
device-specific "muOS-Keys" SDL mapping and separate modern/retro layouts.
SGRUB requests the modern layout, so its SDL A/B actions follow the selected
muOS layout instead of relying on a hard-coded raw button order. The runtime
diagnostic mode can print the mapping actually seen by SDL on the device.

This application launcher is separate from the asynchronous muOS user-init
hook. Do not enable config/sgrub.enabled for this preview. The user-init
hook remains inert and is not a safe way to steal the framebuffer from an
already-running frontend.

## Device validation still required

- Confirm SDL2 opens the physical 640x480 display on the exact muOS build.
- Capture the H700 controller GUID and button/hat events with --input-dump.
- Verify A/B/Y mapping, hot-plug behaviour and clean return to muOS.
- Check CPU use, frame pacing and display restoration after exit.
- Confirm diagnostics match the actual board while RAM type and panel revision remain unclaimed until identified.
- Test only as a normal application; do not install it as an early boot hook.

Passing the host build and UI self-test does not certify the device runtime.

## muOS integration references

- [Application Runner FAQ](https://community.muos.dev/t/application-runner/1282)
- [muOS application setup helpers](https://github.com/MustardOS/internal/blob/main/script/var/retro.sh)
- [muOS SDL environment and modern/retro mapping selection](https://github.com/MustardOS/internal/blob/main/script/var/display.sh)
- [RG35XX H modern SDL controller map](https://github.com/MustardOS/internal/blob/main/device/rg35xx-h/control/gamecontrollerdb/modern.txt)
