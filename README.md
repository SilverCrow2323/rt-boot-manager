# Rt:BOOT MANAGER

**One H700. Multiple OSes. One boot path.**

Rt:BOOT MANAGER is an open multi-OS boot-management project for Allwinner H700 handhelds, beginning with the Anbernic RG35XX H. Its user-facing selector is **SGRUB** (SPDW Graphical Boot Selector).

The project aims to manage verified operating-system images, version-pinned releases, device-specific boot metadata, boot adapters and recovery workflows for:

- **Main systems:** muOS, ROCKNIX and KNULLI.
- **Additional systems:** Anbernic Stock OS, Stock OS MOD, GarlicOS 2 and MinUI.
- **Future profiles:** other H700 devices and compatible Linux environments after validation.

> **Status: early development.** The repository now includes a native SDL2 SGRUB profile-browser preview and read-only profile/device tooling. The preview is not a bootloader: it does not install bootloaders, rewrite partition tables, modify U-Boot environment data, flash images or boot alternate kernels.

## Project principles

See [the phased roadmap](docs/ROADMAP.md) for implementation milestones and the hardware-validation gates.

1. **Preserve the stock boot chain.** No Boot0, boot-package, U-Boot, environment or partition writes without a verified backup, explicit confirmation and a tested restore path.
2. **Detect before selecting.** Board revision, RAM variant, panel DTB, storage layout and image requirements must match before an OS is offered as bootable.
3. **Pin or follow.** Each OS can follow its latest compatible stable release or remain pinned to a specific older version.
4. **Different systems need different adapters.** A rootfs sharing the host kernel is not equivalent to a full firmware with its own kernel, DTB and initramfs.
5. **Recovery is a first-class feature.** A failed profile must never remove the user's ability to boot the known-good system.
6. **Read-only first.** Development begins with inventory, validation and dry-run plans. Destructive operations remain disabled until hardware tests prove the complete recovery cycle.

## Boot model

The Allwinner H700 boot chain is not a PC BIOS/UEFI + GRUB environment. The SoC BootROM loads the early boot stages, followed by the device's boot package/U-Boot and the selected kernel/ramdisk/device-tree path. Different H700 firmware families can use materially different layouts and boot artefacts.

SGRUB therefore has two distinct integration modes:

- **muOS user-init integration:** starts after the muOS Linux kernel is already running. muOS executes user init scripts asynchronously and in the background. It is suitable for diagnostics or a controlled reboot request after a separately validated native adapter, but it cannot pause the original kernel boot or load another kernel in-place. Starting a fullscreen SDL selector from that background hook can race the muOS frontend; the current SGRUB preview is therefore a manually launched muOS application.
- **Native pre-kernel integration:** a future U-Boot/boot-chain adapter that selects a complete boot profile before its kernel is launched. This is the route required for true kernel-level switching between firmware families such as ROCKNIX and KNULLI.

A separate **rootfs/chroot adapter** may support environments that share the currently running kernel. It must never be presented as a native firmware boot.

## Repository map

    .
    ├── catalog/os/            # Canonical OS profile manifests
    ├── catalog/releases/       # Release manifests and checksums
    ├── catalog/release-history/ # Archived provider/history indexes
    ├── config/                 # Example manager configuration
    ├── docs/                   # Architecture, safety, hardware and UI docs
    ├── schema/                 # Profile schema
    ├── src/rtbm/               # Read-only core and menu state
    ├── ui/sgrub/native/         # SDL2 640x480 graphical frontend
    ├── tests/                  # Host-side contract tests
    ├── tools/
    │   ├── rtbm.py             # Read-only CLI
    │   ├── generate_sgrub_profiles.py
    │   └── package_muos_sgrub.sh
    └── integrations/muos/
        ├── 99-rtbm-sgrub.sh    # Inert user-init bridge
        └── application/RTBM-SGRUB/mux_launch.sh

See docs/SGRUB_UI.md for native build, release browser, hardware diagnostics and muOS preview packaging instructions.

## First target

- Device: Anbernic RG35XX H
- SoC: Allwinner H700
- Firmware integration baseline: muOS 2606.0 Andromeda
- Primary OS profiles: muOS, ROCKNIX, KNULLI
- Additional profiles: Stock OS, Stock OS MOD, GarlicOS 2 and MinUI

H700 devices and even RG35XX H board revisions may differ in RAM and display panel details. The project will not infer a DTB or RAM variant from the product name alone.

## SGRUB graphical preview

The first native SDL2 profile-browser build and muOS application packaging
workflow are documented in [SGRUB UI](docs/SGRUB_UI.md). It is a preview only:
the boot hand-off is intentionally disconnected until the relevant adapter and
hardware recovery path have been validated.

## Release catalogue integrity

The release validator rejects ambiguous `asset`/`assets` declarations, duplicate or path-bearing asset filenames, credential-bearing/non-HTTPS source and asset URLs, malformed checksums, and invalid declared sizes. Historical provider indexes remain separate from installable manifests; a missing digest is accepted only with an explicit local-verification policy. This validates metadata only: it does not download or flash firmware.

## Read-only CLI

The initial CLI is deliberately non-destructive. The release browser and CLI
list release metadata only; they do not download or install operating systems:

```sh
python3 tools/rtbm.py list
python3 tools/rtbm.py probe
python3 tools/rtbm.py validate
python3 tools/rtbm.py releases
python3 tools/rtbm.py releases --os rocknix
python3 tools/rtbm.py plan rocknix --device rg35xx-h --ram unknown --dry-run
```

The exact device arguments and output are documented in the CLI help. No command in this phase writes to block devices or bootloader storage.

## Research references

- [muOS 2606.0 Andromeda release notes](https://muos.dev/release/current/2606_0)
- [MustardOS internal scripts](https://github.com/MustardOS/internal)
- [ROCKNIX H700 installation guide](https://rocknix.org/docs/configure/h700-installation/)
- [KNULLI H700 firmware extraction guide](https://knulli.org/guides/firmware-extraction/h700-firmware-extract/)
- [GarlicOS H700 bootloader](https://github.com/GarlicOS/bootloader_anbernic_rg35xxplus)
- [GarlicOS init template](https://github.com/GarlicOS/init_template)
- [MinUI](https://github.com/shauninman/MinUI)

## Naming

- Repository: `rt-boot-manager`
- Product: **Rt:BOOT MANAGER**
- Selector: **SGRUB — SPDW Graphical Boot Selector**
- Organisation/brand: **SPDW Factory**
