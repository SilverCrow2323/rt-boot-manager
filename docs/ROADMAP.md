# Roadmap

This roadmap distinguishes implemented host-side foundations from unvalidated device boot work.

## M0 — Repository and safety foundation

- [x] Define Rt:BOOT MANAGER and SGRUB naming.
- [x] Establish profile schema and OS catalogue.
- [x] Document H700 boot-chain boundaries.
- [x] Document muOS user-init asynchronous behavior.
- [x] Make phase-0 CLI read-only.
- [x] Enforce that no profile can enable bootloader writes.
- [x] Add CI for catalogue validation, tests and shell syntax.

## M1 — Device inventory and release catalogue

- [x] Read device-tree model / compatible, CPU description and memory total.
- [x] Keep RAM technology and panel revision unknown unless positively identified.
- [x] Add initial muOS, ROCKNIX and KNULLI profiles.
- [x] Add Stock OS, Stock OS MOD, GarlicOS 2, MinUI and disabled MinOS research entry.
- [x] Add ROCKNIX 20261101 DDR3/DDR4 manifests, SHA-256 and DTB mapping.
- [x] Add KNULLI Scarab 20260511 H700 image manifest.
- [x] Add release-manifest validation.
- [x] Retain five earlier ROCKNIX H700 releases with release-specific asset checksums.
- [x] Retain four legacy KNULLI RG35XX H release records with explicit checksum-verification requirements.
- [x] Index the 15 archived muOS releases without inventing provider URLs, image filenames or checksums.
- [x] Generate one native release table from stable manifests and separate history indexes.
- [ ] Resolve and verify exact muOS archive downloads for RG35XX H.
- [ ] Verify KNULLI legacy checksum sidecars against downloaded images.
- [ ] Build upstream release resolver with signed-source / asset / checksum verification.
- [ ] Probe RG35XX H RAM variant and panel/PCB revision on physical hardware.

## M2 — SGRUB interface

- [x] Implement renderer-independent controller/menu state.
- [x] Put muOS, ROCKNIX and KNULLI first.
- [x] Implement selection, confirm, cancel, default profile and timeout state.
- [x] Build the first 640x480 SDL2 graphical profile-browser renderer.
- [x] Generate native SGRUB profile data from the canonical OS catalogue.
- [x] Add a muOS application archive builder for the profile-browser preview.
- [x] Add optional SDL controller database loading and input diagnostics.
- [x] Add a native read-only release-history/version screen for muOS, ROCKNIX and KNULLI.
- [x] Add session-only release pin selection and reset controls.
- [ ] Persist per-OS release pins and connect them to validated installation plans.
- [ ] Refine the SPDW visual system and release detail presentation.
- [ ] Add compatibility-aware update selection after physical hardware detection.
- [ ] Add status / diagnostics / recovery screens.
- [ ] Test framebuffer, controller mapping and clean return to muOS on RG35XX H.
- [ ] Implement and validate a real boot adapter before enabling any boot action.

## M3 — muOS integration

- [x] Add an inert, opt-in muOS user-init hook scaffold.
- [x] Require the user to enable muOS User Init Scripts and a separate SGRUB marker.
- [x] Provide a separate manually launched muOS SDL2 application preview.
- [ ] Implement tested display/input hand-off for a post-kernel selector.
- [ ] Implement controlled reboot request after a native boot entry has been separately validated.
- [ ] Package a reversible muOS integration installer and removal path.

## M4 — Shared-kernel and legacy adapters

- [ ] Inspect GarlicOS image, rootfs and matching init-template versions end-to-end.
- [ ] Inspect MinUI exact RG35XX H legacy payload and launcher chain.
- [ ] Implement read-only inventory and dry-run adapters.
- [ ] Verify Stock dmenu hand-off and Stock OS fallback without overwriting recovery files.

## M5 — Native pre-kernel multi-boot research

- [ ] Extract and compare exact Stock, muOS, ROCKNIX and KNULLI H700 images.
- [ ] Map Boot0, boot-package, U-Boot, env.img, kernel, initramfs and DTB per release.
- [ ] Determine whether a chain-loadable U-Boot menu is feasible on the exact RG35XX H board.
- [ ] Prototype only against a disposable test card.
- [ ] Design a verified byte-accurate backup and independent restore procedure.
- [ ] Test switching between ROCKNIX mainline and KNULLI BSP kernels.
- [ ] Test cold boot, warm reboot, sleep/wake, power-loss recovery and firmware update interactions.

## M6 — Installer and release

- [ ] Implement write operations only after M5 recovery validation.
- [ ] Keep Stock OS or a separately validated recovery entry available at all times.
- [ ] Add a signed installation plan, explicit target-card confirmation and post-write read-back verification.
- [ ] Publish installable packages, checksums, documentation and supported-device matrix.
- [ ] Certify each supported board/RAM/panel combination independently.

## Release gates

A profile is not “bootable” merely because an upstream image exists or a dry-run plan can be generated.

A profile may be marked **validated** only after:

1. correct hardware variant is positively established;
2. exact image and all boot artefacts are verified;
3. backup and recovery are tested;
4. cold boot and reboot are tested on a physical device;
5. return to the known-good system is verified.

Native multiboot remains experimental until the relevant release gates are complete.
