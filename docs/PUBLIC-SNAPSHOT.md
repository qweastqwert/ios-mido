# Public snapshot policy

This repository is a sanitized handoff of the mido port. It contains source changes, reproducible helpers, device facts, status notes, and hashes of generated artifacts.

The following remain intentionally outside the public repository:

- raw phone partition and bootloader dumps;
- generated boot images and large build outputs;
- Windows ADB/fastboot/tool binaries;
- local Claude/Codex settings;
- device serials and host-specific paths;
- credentials, tokens, and personal data.

The upstream HakiOS repositories remain the source for the large kernel/UEFI trees. Recreate the local build checkout, set `HAKIOS_ROOT`, apply the mido-specific files in `porting/mido-u-boot`, and regenerate images rather than committing generated binaries.
