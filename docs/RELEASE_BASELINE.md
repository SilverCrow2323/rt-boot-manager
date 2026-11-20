# Release baseline and retained history

Snapshot date: 2026-11-20. These are upstream release records, not a claim that every image is bootable on every RG35XX H board. The resolver must re-check exact device, RAM, panel/PCB, image checksum and boot artefacts before presenting an install action.

## Main systems

| OS | Latest stable baseline in this snapshot | Retained history |
|---|---|---|
| muOS | 2606.0 Andromeda | 15 archived release pages indexed; external download asset and checksum resolution remains manual |
| ROCKNIX | 20261101 | 20261001, 20260901, 20260801, 20260701, 20260601 |
| KNULLI | Scarab 20260511 | Gladiator II 20250813, Gladiator 20250505, Firefly 20241204, 40 20240721 |

The history catalog is intentionally honest about verification state:

- ROCKNIX 20260601–20261001 image assets have release-specific SHA-256 digests from GitHub release metadata. Releases from 202607 onward publish separate DDR3 and DDR4 images; 20260601 has one generic H700 asset and is marked as not RAM-variant-specific.
- KNULLI legacy entries preserve the exact RG35XX H asset filename and upstream checksum-sidecar filename, but the image digest is not yet locally verified. They require a sidecar comparison or locally calculated SHA-256 before trust.
- muOS archive pages are indexed separately because downloads are delivered through external provider links. No guessed filenames, direct URLs or checksums are recorded. The archive page is not itself an installable image manifest.

## ROCKNIX 20261101 assets

The official release publishes two H700 images:

- DDR3: ROCKNIX-H700.aarch64-20261101-DDR3.img.gz — 6c5567f5e29a041a1ae1a94c3737c640f5345b77fbaffa4010e8e8ebc6546af1
- DDR4: ROCKNIX-H700.aarch64-20261101-DDR4.img.gz — 46ec25c30be24fff5f154460f988e53c0311e115fd72ee7b861b55e59c553a07

Resolve the DTB from the same release and match the exact board/panel:

- Standard RG35XX H: sun50i-h700-anbernic-rg35xx-h.dtb
- RG35XX H rev6-panel: sun50i-h700-anbernic-rg35xx-h-rev6-panel.dtb

Never reuse a DTB across releases without verifying its identity.

## KNULLI boot-chain isolation

Scarab and the older Gladiator/Firefly releases use a KNULLI-specific BSP boot stack. Boot0, boot-package, boot.img, env.img and DTB are release-specific. Never mix these with ROCKNIX or another KNULLI release.

## Official sources

- muOS current: https://muos.dev/release/current/2606_0
- muOS archive: https://muos.dev/release/archive
- ROCKNIX releases: https://github.com/ROCKNIX/distribution/releases
- ROCKNIX H700 installation / DTB guide: https://rocknix.org/docs/configure/h700-installation/
- KNULLI current releases: https://github.com/knulli-cfw/knulli-linux/releases
- KNULLI legacy releases: https://github.com/knulli-cfw/distribution/releases
- KNULLI H700 firmware extraction: https://knulli.org/guides/firmware-extraction/h700-firmware-extract/
