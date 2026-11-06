# HakiOS mido phase 3 status

## Completed

- ADB root access is confirmed through Magisk (`uid=0`, Magisk SELinux domain).
- Captured and decompiled the live DTB from the current LineageOS 23.2 / 4.19 system.
- Confirmed 3 GiB RAM, active ~2 GiB zram, Qualcomm MSM8953, SDHCI/eMMC boot storage,
  OTM1911 1080x1920 display, and FocalTech `fts_ts-mi8953` touch input.
- Generated and validated `devices/mido` for the current HakiOS tree.
- Disabled the generated mido UFS selection because this phone boots from eMMC.
- Installed the Linux/WSL HakiOS build prerequisites and Theos with the iPhoneOS 16.5 SDK.
- Built `hakios-kernel` as a Mach-O arm64 kernel (15 MiB stripped artifact).
- Added `hakios.mido_mmc.c`, a read-only Qualcomm SDHCI/eMMC PIO driver adapted from the
  vince MSM8953 implementation.
- Added the `MIDO_EMMC` configuration; `drivers-check` passes and the driver compiles into
  the HakiOS kernel. It has no write commands.

## Reinstalled-system baseline (2026-11-05)

- ADB root re-approved and confirmed through Magisk.
- Current kernel: `4.19.325-cip130-st14-Mi-Titanium-v2`.
- Current DTB: 249,035 bytes; it identifies MSM8953/PMI8950, 3 GiB RAM, SDHCI/eMMC,
  OTM1911 1080x1920, and FocalTech at I2C address `0x38`.
- This DTB does not include the earlier `xiaomi,mido` compatible string, so the port must
  use the hardware facts plus the board's boot properties rather than matching only that
  string.
- This installation is non-A/B: no slot properties are set, and it has separate 64 MiB
  `boot` and `recovery` partitions.
- The phone's current raw partitions are approximately: system 20 GiB, userdata 4.8 GiB,
  boot 64 MiB, recovery 64 MiB, persist 32 MiB.

## Dynamic LOS23 comparison capture (2026-11-05)

- Root was re-approved and confirmed.
- This ROM exposes the fuller 280,107-byte DTB, including `xiaomi,mido`, and uses the
  earlier cip136 kernel.
- It reports `androidboot.super_partition=system`; `/dev/block/mmcblk0p48` is the raw
  20-GiB super container.
- `lpdump` reports a two-slot metadata table, a `mido_dynamic_partitions` group capped at
  4,089,446,400 bytes, and logical `system`, `vendor`, `product`, `odm`, and `system_ext`.
- Dynamic partitioning is useful for the richer DTB/kernel, but it does not make all 20 GiB
  available to Android logical partitions. The remaining raw space is not automatically
  a Darwin volume.

## HakiOS 2.3.4 checkpoint

- Upstream was force-rewritten, so the old checkout was preserved and a fresh shallow
  checkout was created at commit `2631f5d7d4f9d7322aca60991b34ba465dec343b`.
- The mido target was regenerated from `evidence/mido-los23-dynamic` and includes the new
  per-device `metal.args` file.
- UFS is explicitly disabled; `MIDO_EMMC` is enabled; `drivers-check` and device checks pass.
- The 2.3.4 kernel builds with the read-only eMMC driver. SHA-256:
  `66f2bda10f1ef41806fda2c88a0c56e429a447e412f38e141bb94180686dc5e8`.
- The open loader test artifacts also build: `xnuloader/loader.efi` and a RAM payload
  containing this kernel. A phone-side test is still gated on a mido-specific UEFI/U-Boot
  platform; the legacy mido `aboot` cannot consume the Mach-O kernel directly.
- The old capture's unavailable DTBO marker was removed; the dynamic-ROM capture is now
  authoritative. The phone itself was not modified.

## Current blocker before any phone boot attempt

The UFS driver is not usable on this hardware. The storage bring-up is now present, but
the vince port is only a reference: its display, touch, memory-map, and identity constants
must not be copied unchanged.

The first implementation will be read-only and will expose only a selected GPT partition
for a ramdisk/root experiment. Write support and flashing remain disabled until reads,
GPT parsing, and bootloader handoff are independently verified.

## Next implementation order

1. Adapt the vince SDCC1/SDHCI PIO initialization to mido's live addresses and clock/power
   facts; add it as a mido storage driver and compile-test it.
2. Add mido ADT/device-tree data for MSM8953, 3 GiB split memory, OTM1911 1080x1920, and
   FocalTech 0x38. Keep vince's Synaptics/1080x2160 data separate.
3. Port the minimal display/input bring-up needed for a diagnostic loader.
4. Build the mido UEFI/loader path and test only with a temporary RAM-loaded payload before
   considering any persistent partition changes.

The current `make mido_defconfig`, `make config`, `tools/drivers-check.py`, and
`make kernel JOBS=4` checkpoint completes. The remaining XNU symbol-set diagnostics are
the expected omitted-Apple-kext checks accepted by HakiOS's build wrapper.

## Storage constraint (updated after repartition)

The phone now reports `mmcblk0p48` (system) at 20,971,520 KiB, approximately 20 GiB raw,
and userdata at about 4.8 GiB raw. This is enough room for a compact Darwin system image
on the system partition, but leaves little room for rollback or Android. The existing zram
is already enabled, so creating a swap partition is not currently useful.

The system partition is now large enough for a compact Darwin image, but formatting it
would erase the current ROM. No image has been formatted or flashed.

