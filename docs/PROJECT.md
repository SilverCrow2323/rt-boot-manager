# Project: Rt:BOOT MANAGER / SGRUB

## Purpose
Provide a hardware-aware, read-only-first multi-OS profile manager for Allwinner H700 handhelds, beginning with the Anbernic RG35XX H. SGRUB is the graphical selector preview; Rt:BOOT CORE owns inventory, profile validation and boot-plan policy.

## Users and use cases
- H700 owners comparing supported firmware profiles and release requirements.
- Maintainers validating OS image metadata, RAM variants, panel/PCB revisions and device compatibility.
- Developers building a future recovery-capable boot adapter after hardware evidence exists.

## Scope and boundaries
In scope: device inventory, versioned OS profiles, upstream release catalogues, checksum/DTB requirements, controller-driven profile browsing, dry-run planning and recovery design.

Out of scope in the current phase: flashing images, repartitioning storage, Boot0/boot-package writes, U-Boot environment mutation, kernel switching, or presenting a profile as bootable solely from the product name. muOS user-init runs after the kernel and is not a pre-kernel multi-boot mechanism.

## Target
- Reference: Anbernic RG35XX H, Allwinner H700, AArch64, 640×480.
- Initial OS profiles: muOS, ROCKNIX and KNULLI; additional systems remain research/disabled until evidence is sufficient.
- Host development: Python 3.11+, SDL2 native preview and shell packaging checks.

## Architecture
- Catalog/schema: versioned OS profiles and release manifests.
- Device probe: model/compatible, memory and storage observations; unknown RAM/panel remain unknown.
- Compatibility planner: typed status and dry-run plan, never privileged execution.
- SGRUB: SDL2 profile browser and controller state.
- Integrations/recovery: muOS user-init and future firmware-specific adapters, with restore design before any mutation.

## Dependencies and provenance
OS releases and firmware artefacts remain upstream-owned. Every downloadable asset requires a verified source, exact device/RAM/DTB match and checksum. The tool must not invent missing URLs or checksums.

## Safety and quality
No profile may enable writes in the current phase. Unknown hardware facts must block native boot selection. Validate untrusted catalogue URLs/paths, keep network and image handling bounded, and preserve a known-good boot path. UI text must be legible at 640×480 and fully navigable by controller. Documentation is English.

## Verified baseline
The repository contains profile/release catalogues, a read-only planner, device probe, SDL2 SGRUB preview, muOS packaging and host tests. CI can validate software and packaging syntax; no physical H700 boot/recovery qualification is claimed.
