# SGRUB preview package verification

The muOS preview package is intentionally not a bootloader installer. CI validates the ZIP structure, the exact three-file package surface, safe member paths, symlink rejection, CRC integrity, executable permissions, the muOS launcher contract and the preview-only safety notice.

The ELF check now inspects the actual ELF64 program-header entries as well as the header. It requires a little-endian AArch64 executable/PIE, a complete program-header table, at least one PT_LOAD segment, p_filesz no larger than p_memsz, and file-backed segment ranges contained within the binary. This prevents a header-only or non-loadable placeholder from passing the architecture gate.

A successful CI package proves that an ARM64 preview artifact was built and structurally checked. It does not prove that the application launches on an RG35XX H, that the display/controller mapping is correct, or that any boot-chain hand-off works. SGRUB remains read-only and BOOT HANDOFF remains NOT CONNECTED until separate native boot/recovery milestones and physical device acceptance are complete.
