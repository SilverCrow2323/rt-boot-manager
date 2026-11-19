# Release baseline snapshot

Snapshot date: 2026-11-19. These are research baselines, not live "latest" claims. The release resolver must query upstream and re-check device compatibility before presenting an update.

| OS | Known stable / supported baseline | Device note |
|---|---|---|
| muOS | 2606.0 Andromeda | Stable baseline for RG35XX H. User-init integration is post-kernel and asynchronous. |
| ROCKNIX | 20261101 | Official H700 DDR3 and DDR4 image assets exist; exact RAM asset and DTB are hard requirements. |
| KNULLI | Scarab 20260511 | Official RG35XX H image; release notes include revised H700 RG XX support. |
| Anbernic Stock OS | V1.2.4-260526 | Official RG35XX H firmware. Keep as recovery reference. |
| Stock OS MOD | v4.0.4 (20261025) | Online update, not standalone image. Existing supported MOD base / update chain required. |
| GarlicOS 2 | v2.0.1 | Official release lists RG35XX H support; retain Stock TF1 dmenu bootloader and matching TF2 init/rootfs. |
| MinUI | Legacy device package | Repository is archived; resolve the exact RG35XX H package rather than using the generic latest tag. |
| MinOS | Unverified | No distinct H700 project and boot asset confirmed. Disabled. |

## Verified ROCKNIX 20261101 assets

The official release page publishes two H700 images with SHA-256:

- DDR3: ROCKNIX-H700.aarch64-20261101-DDR3.img.gz — 6c5567f5e29a041a1ae1a94c3737c640f5345b77fbaffa4010e8e8ebc6546af1
- DDR4: ROCKNIX-H700.aarch64-20261101-DDR4.img.gz — 46ec25c30be24fff5f154460f988e53c0311e115fd72ee7b861b55e59c553a07

The correct RG35XX H DTB must also be selected:

- Standard RG35XX H: sun50i-h700-anbernic-rg35xx-h.dtb
- RG35XX H rev6-panel: sun50i-h700-anbernic-rg35xx-h-rev6-panel.dtb

ROCKNIX's documented procedure copies the selected DTB from the device_trees directory to the system partition root as dtb.img. The board revision must be verified; it must not be guessed.

## Verified KNULLI Scarab 20260511 asset identity

The official release lists the RG35XX H image as:

knulli-h700-rg35xx-h-scarab-20260511.img.gz

The release page and image identity are recorded in catalog/releases/knulli/20260511.json. Since a published SHA-256 was not established in this snapshot, Rt:BOOT must calculate and store a local SHA-256 after download before the asset can pass verification.

## Stock OS MOD update chain

The 20261025 v4.0.4 release is an online upgrade. Upstream says its base images are v3.9.9 and documents upgrade paths from older MOD versions. The profile must detect a compatible base installation before any update is offered. It must never flash the v4.0.4 update archive as if it were a complete OS image.

## Official sources

- muOS 2606.0: https://muos.dev/release/current/2606_0
- ROCKNIX 20261101: https://github.com/ROCKNIX/distribution/releases
- ROCKNIX H700 DTB guide: https://rocknix.org/docs/configure/h700-installation/
- KNULLI Scarab: https://github.com/knulli-cfw/knulli-linux/releases/tag/20260511
- KNULLI H700 firmware extraction: https://knulli.org/guides/firmware-extraction/h700-firmware-extract/
- Anbernic Stock OS: https://anbernic.com/en-it/pages/system-update
- Stock OS MOD 20261025: https://github.com/cbepx-me/Anbernic-H700-RG-xx-StockOS-Modification/releases
- GarlicOS 2: https://github.com/GarlicOS/buildroot/releases
- MinUI: https://github.com/shauninman/MinUI
