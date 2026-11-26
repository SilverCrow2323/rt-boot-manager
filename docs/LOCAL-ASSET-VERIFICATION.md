# Local release-image verification (M1 extension)

The release catalogue now has a read-only verifier for images that the user has already downloaded. It does not fetch files or write to block devices.

```sh
python3 tools/rtbm.py verify-asset rocknix 20261101 ./rocknix-rg35xx-h-ddr4.img.gz
```

The filename must match a declared asset in the selected OS/tag manifest. The verifier checks the local file is regular (not a symlink), verifies its size when the manifest pins one, and streams SHA-256 before reporting `verified: true`.

Legacy records whose provider checksum is not verified fail closed. The tool will not invent or substitute a checksum, and it will not mark an asset verified from a release-page URL alone.

This is still a local-file verification step: it does not download, extract, flash, mount or install an operating system. Hardware compatibility and boot recovery gates remain unchanged.
