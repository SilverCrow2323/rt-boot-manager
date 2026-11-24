# SGRUB preview package verification

The muOS preview package is intentionally not a bootloader installer. CI validates the ZIP structure, the exact three-file package surface, safe member paths, symlink rejection, CRC integrity, executable permissions, the muOS launcher contract and the preview-only safety notice.

The ELF check inspects the actual ELF64 program-header entries as well as the header. It requires a little-endian AArch64 executable/PIE, a complete program-header table, at least one PT_LOAD segment, p_filesz no larger than p_memsz, and file-backed segment ranges contained within the binary. It also verifies that the entry point falls inside an executable PT_LOAD segment, that the load address range does not overflow the ELF64 address space, and that non-trivial PT_LOAD alignment is a power of two with congruent file and virtual offsets.

These checks reject structurally incomplete or non-loadable placeholders before artifact upload. They do not certify the AArch64 ABI beyond the inspected ELF fields, runtime library availability, display/controller mapping, or a physical RG35XX H launch.

A successful CI package proves that an ARM64 preview artifact was built and structurally checked. It does not prove that the application launches on an RG35XX H or that any boot-chain hand-off works. SGRUB remains read-only and BOOT HANDOFF remains NOT CONNECTED until separate native boot/recovery milestones and physical device acceptance are complete.
