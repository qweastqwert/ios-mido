# Dynamic-partition LOS23 capture

Captured read-only from the newly booted Redmi Note 4 (`mido`) on 2026-11-05.
Magisk root was confirmed for the ADB shell.

## Identity

- Android 16, build `BP4A.251205.006 release-keys`
- Kernel: `4.19.325-cip136-st20-perf-g4a43f94c363c`
- SoC: Qualcomm MSM8953 / PMI8950
- RAM: approximately 3 GiB
- zram: 2,211,086,336 bytes (approximately 2 GiB)

## DTB facts

- DTB size: 280,107 bytes
- Compatible includes `qcom,msm8953-qrd-sku3`, `qcom,msm8953`, and `xiaomi,mido`
- Boot storage: Qualcomm SDHCI/eMMC at `7824900.sdhci`
- Display: OTM1911 FHD video, 1080x1920, single DSI
- Touch: FocalTech `fts_ts-mi8953`, address `0x38`

## Dynamic partition facts

- `androidboot.super_partition=system`
- Raw super container: `/dev/block/mmcblk0p48`, 20,971,520 KiB / 20 GiB
- `lpdump` metadata version: 10.0; metadata slot count: 2
- Logical group: `mido_dynamic_partitions`, maximum 4,089,446,400 bytes
- Logical partitions: `system`, `vendor`, `product`, `odm`, `system_ext`
- The logical partitions are read-only and occupy the first approximately 5,891,464 sectors
  of the raw system container; the remaining raw space is not automatically a Darwin volume.
- No `dtbo` by-name node was present.

## Safety

This capture contains reference data only. No HakiOS image was flashed and no partition
was formatted or modified.
