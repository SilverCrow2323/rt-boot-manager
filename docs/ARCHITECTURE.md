# Architecture

## Goals

Rt:BOOT MANAGER manages bootable system profiles, not just downloaded images. A profile describes device matching, release policy, boot artefacts, adapter, persistence model and recovery requirements.

SGRUB is the selector UI. Rt:BOOT CORE is the inventory and policy layer. OS-specific boot logic lives behind adapters; profile data must never contain executable shell commands.

## Execution layers

1. SGRUB UI — controller navigation, system cards, version picker, timeout, default selection, diagnostics and recovery entry.
2. Profile engine — schema validation, release resolution, hardware compatibility and installation-state inventory.
3. Boot planner — converts a selected profile into a typed plan. The planner does not execute privileged operations.
4. Boot adapters — U-Boot/native firmware, muOS user-init hand-off, Stock dmenu hand-off and shared-kernel rootfs/chroot.
5. Recovery engine — verified backups, boot-chain snapshot metadata, restore plans and rollback state.

## Adapter contract

Every adapter must expose supported device families, required artefacts, hardware requirements, unknown-state policy, read-only inspection and dry-run planning. Any later mutation capability must be explicitly declared and separately reviewed.

## Boot modes

| Mode | Meaning | Initial state |
|---|---|---|
| native_firmware | Own kernel and boot artefacts | Research / dry-run only |
| uboot_profile | U-Boot chooses a complete boot entry | Not implemented |
| muos_user_init | Linux is already running; asynchronous user script | Hook scaffold |
| stock_dmenu_handoff | Existing Stock OS dmenu hand-off | Research / no mutation |
| shared_kernel_rootfs | Root filesystem reuses host kernel | Inventory only |
| legacy_rootfs | Existing launcher/chroot model | Inventory only |

## Phase 0 non-goals

No flashing, repartitioning, Boot0 writes, boot-package writes, U-Boot environment changes, boot.img repacking or automatic kexec. An init script must never be described as a pre-kernel bootloader.

## Version model

A profile can follow the latest compatible stable release, remain pinned to an older release, or use a manually supplied image. Latest upstream and latest compatible for the exact board are different concepts.
