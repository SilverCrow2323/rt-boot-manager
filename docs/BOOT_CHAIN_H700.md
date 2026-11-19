# H700 boot chain research

## Not a PC BIOS/UEFI environment

The Allwinner H700 path starts at SoC BootROM and continues through board/vendor-specific early boot stages. KNULLI documents the relevant BSP firmware building blocks as Boot0, boot-package (including U-Boot and board-specific components), boot.img (kernel and ramdisk in the documented image) and env.img (U-Boot environment).

This is a model, not a universal partition recipe. Offsets and layouts must be extracted from the exact firmware image. Never copy raw offsets from another device or release.

## Kernel families

- ROCKNIX uses mainline-based H700 support and requires the correct device-tree file for the exact device / panel revision.
- KNULLI uses an H700 BSP boot stack with its own boot artefacts and environment assumptions.
- muOS and Stock OS have their own image and update conventions.
- GarlicOS 2 uses a Stock TF1 bootloader hand-off to a TF2 init script and rootfs.
- MinUI is a legacy launcher/rootfs path, not an interchangeable native H700 image.

## Device identity is not inferred

The RG35XX H product name alone does not prove PCB revision, panel revision, RAM technology or RAM capacity. Unknown values stay unknown. A profile requiring a verified DTB or RAM variant is blocked until those values are known.

## Required research for each release

Record official URL and tag, asset filename and size, upstream SHA-256, image format, partition table, Boot0 / boot-package / U-Boot changes, kernel and initramfs, DTB name, RAM/panel requirements, update mechanism and documented restore procedure.

## References

- KNULLI H700 firmware extraction: https://knulli.org/guides/firmware-extraction/h700-firmware-extract/
- ROCKNIX H700 installation: https://rocknix.org/docs/configure/h700-installation/
- GarlicOS H700 bootloader: https://github.com/GarlicOS/bootloader_anbernic_rg35xxplus
