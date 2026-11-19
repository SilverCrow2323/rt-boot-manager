# Safety and recovery policy

## Phase 0

All current commands are read-only. The CLI has no block-device write path.

Never infer a target device node from a hard-coded mmcblk value. Card ordering and device nodes can differ between firmware versions and boot contexts.

## Before any future boot-chain mutation

A future installer must positively identify the target card and slot, detect board/RAM/panel state, inspect the partition table, back up every region it may alter, verify backup sizes and SHA-256, record offsets and source versions, require a second confirmation showing the exact target, perform bounded writes, verify read-back hashes, preserve a known-good boot entry and provide a separately tested restore path.

No write operation may proceed if the backup is missing, incomplete or unverifiable.

## Explicitly forbidden in phase 0

- dd to a block device;
- writes to mmcblk, sd or raw MTD devices;
- fw_setenv / fw_printenv mutation;
- partition-table writes;
- unattended flashing;
- automatic deletion of the original firmware or recovery files.
