# HakiOS / iOS 16.5 on Redmi Note 4 (`mido`) — handoff

Public contribution and verification rules are in [CONTRIBUTING.md](CONTRIBUTING.md). In particular, a fix must be verified on the intended target or with a documented substitute before it is committed and pushed.

Last updated: 2026-11-05

## Goal

Port HakiOS/iOS 16.5 to the Redmi Note 4/4X (`mido`, Snapdragon MSM8953, 3 GiB RAM), starting with a RAM-only boot. The long-term goal is to run Darwin from phone storage, but no persistent Darwin/iOS partition has been created yet.

This is a legacy Qualcomm phone. Its boot chain is:

```text
sbl1 -> aboot -> boot/recovery
```

It has no XBL, SBL2, UEFI, A/B slot layout, or `dtbo` partition. The phone’s normal boot image header is legacy Android header v0/v1-compatible with a 2 KiB page size and kernel address `0x80008000`.

## Safety state

- No phone partition has been flashed by this work.
- All phone tests used `fastboot boot`, which loads an image into RAM only.
- No Android system partition was formatted.
- The phone currently returns to LineageOS after failed RAM-only tests.
- Magisk root works; `com.android.shell` was approved and previously returned `uid=0(root)`.
- Do not run `fastboot flash`, `erase`, `format`, `repartition`, or `dd` unless a separate backup/rollback plan is agreed.

## Phone baseline

Current/working Android baseline:

- Device: Redmi Note 4 / 4X, codename `mido`
- ADB: use the device selected by `adb devices`; no device serial is stored in this repository
- ROM used for the authoritative capture: stable LineageOS 23.2, non-A/B dynamic build
- Kernel: 4.19.x; the latest reinstalled baseline reported `4.19.325-cip130-st14-Mi-Titanium-v2`
- RAM: 3 GiB
- Existing zram: approximately 2 GiB; no separate swap partition is needed for current bring-up
- Storage: raw system/super approximately 20 GiB (`mmcblk0p48`), userdata approximately 4.8 GiB, boot/recovery approximately 64 MiB each
- Display: OTM1911, 1080x1920
- Touch: FocalTech `fts_ts-mi8953`, I2C address `0x38`
- Boot storage: eMMC/SDHCI1, not UFS

The original 8 GiB system partition is no longer the current layout; it was expanded to approximately 20 GiB. The dynamic partition group itself is only about 4.09 GiB, so the whole raw 20 GiB is not automatically available as one Android/Darwin logical volume.

## Authoritative device tree

The current dynamic LineageOS DTB was pulled from the running phone and is stored at:

`evidence/mido-los23-dynamic/device-tree/live/mido-live.dtb`

SHA-256:

`bd8e6686c29fe17cb10d53ddb47daf5e6a97d42a9e9085b8a46ed96bb094098e`

Important facts from it:

- compatible: MSM8953 / Xiaomi mido
- `/memory` contains two banks: 1 GiB at `0x40000000` and 2 GiB at `0x80000000`
- USB DWC3 wrapper at approximately `0x070f8800`, DWC3 core at `0x07000000`
- QUSB2 PHY and the Android kernel’s USB path are known-good

The dynamic LOS23 capture is authoritative. The earlier non-dynamic/older DTBO capture was intentionally retired and must not be used as the source of truth.

## Source trees

Set `HAKIOS_ROOT` to the local HakiOS checkout path in your WSL environment.

Main HakiOS 2.3.4 checkout:

`$HAKIOS_ROOT`

Upstream HakiOS commit currently checked out:

`2631f5d7d4f9d7322aca60991b34ba465dec343b`

Relevant reference trees:

- `$WORK/ios-vince` — MSM8953/vince reference, especially eMMC PIO code
- `$WORK/hakios-uefi-234` — current HakiOS UEFI main checkout
- `$WORK/hakios-uefi-uboot` — HakiOS U-Boot branch checkout
- `$WORK/hakios-sm7325-uboot` — working redwood U-Boot reference
- `$WORK/linux-msm8953` — sparse Linux checkout containing MSM8953 GCC source

The HakiOS U-Boot source is materialized inside the main checkout at:

`$HAKIOS_ROOT/u-boot`

Its generated normal mido build is:

`$HAKIOS_ROOT/u-boot/build-mido`

## Completed HakiOS work

- Generated a mido device target from the live DTB.
- Added mido-specific `metal.args` (`fb_hz=60`, `fb_threads=3`).
- Disabled UFS for mido and enabled `CONFIG_HAKIOS_MIDO_EMMC=y`.
- Added a read-only Qualcomm SDHCI/eMMC PIO driver adapted from the vince MSM8953 implementation.
- Built the HakiOS kernel as Mach-O arm64.
- Built `xnuloader/loader.efi` and the HakiOS payload.
- Installed the AArch64 cross compiler and required WSL host dependencies.
- Added an MSM8953 GCC clock/reset/power-domain driver for the U-Boot USB/eMMC path.
- Added a mido U-Boot DTS with 3 GiB memory and USB peripheral/high-speed settings.
- Added a HakiOS U-Boot mido defconfig and RAM-only environment.

Kernel artifact:

`$HAKIOS_ROOT/hakios-kernel`

Kernel SHA-256:

`66f2bda10f1ef41806fda2c88a0c56e429a447e412f38e141bb94180686dc5e8`

## Current U-Boot implementation

Main mido U-Boot files:

- `devices/mido/u-boot/files/board/qualcomm/hakios-mido.env`
- `devices/mido/u-boot/files/configs/hakios_mido_defconfig`
- `devices/mido/u-boot/files/dts/upstream/src/arm64/qcom/msm8953-xiaomi-mido.dts`
- `devices/mido/drivers/storage/hakios.mido_mmc.c`
- `u-boot/drivers/clk/qcom/clock-msm8953.c`

The source DTS includes:

- 3 GiB RAM map
- HakiOS payload reserve at `0xf0000000`, size 64 MiB
- USB wrapper/core in peripheral mode at high speed
- `/delete-property/ usb-role-switch` for the U-Boot gadget path
- display clock/power-domain properties removed from simple framebuffer during early bring-up

The normal mido environment attempts HakiOS memory loading and otherwise enters U-Boot fastboot. A separate USB-only diagnostic environment was also built that skips HakiOS loading, EFI, display console, eMMC, and storage and immediately runs `fastboot usb 0`.

## Tests performed

### DTB placement

An image with the DTB in Android boot-image `--second` failed immediately:

```text
FAILED (remote: 'dtb not found')
```

This proves mido’s ABL expects the appended-DTB layout used by the other images. Do not switch to the `--second` layout.

### Appended-DTB U-Boot images

Multiple legacy header v0/v1 images were accepted by mido’s bootloader:

```text
Sending 'boot.img' ... OKAY
Booting ... OKAY
```

After the handoff, Windows loses the USB device. The phone eventually returns to LineageOS. This behavior is partly expected: `fastboot boot` resets the phone, so the original fastboot transport disappears. However, a working U-Boot USB gadget should re-enumerate as fastboot. It has not done so yet, so the remaining failure is inside early U-Boot/USB bring-up or an early U-Boot crash.

The USB-only diagnostic image behaved exactly the same as the HakiOS environment image, ruling out the HakiOS loader/payload parser as the first failure point.

### Live-DTB runtime test

The latest normal U-Boot build was changed so that, when ABL supplies an external DTB, U-Boot uses that live Android DTB as the runtime FDT rather than only using it for memory sizing. The image was tested and still disappeared from USB before exposing fastboot, then the phone returned to LineageOS.

The last tested image was:

`artifacts/hakios-mido-uboot-external-fdt-v0.img`

### USB reconnect behavior

After an Android-to-bootloader or boot-image reboot, Windows frequently does not re-enumerate the phone until the cable is physically unplugged and reconnected. Restarting the Windows ADB daemon with elevation restored ADB in LineageOS. `pnputil /scan-devices` was attempted but returned access denied.

This is a host transport issue layered on top of the U-Boot issue. Always check both transports after a test and physically reconnect once if both are empty.

## RAM-only image artifacts

All are in `artifacts/`. The important recent images are:

| Image | SHA-256 | Purpose |
|---|---|---|
| `hakios-mido-u-boot.img` | `86ad6ef30f8bd717b55517d6be75a5b3f9afc4d09bb2232869778f4fff933439` | First full HakiOS U-Boot image, appended live DTB, HKUB payload |
| `hakios-mido-uboot-only-v0-memory-live.img` | `ec50fca8a203c8ec23132603fe9570a8b6fddc1fe066e334a03247318fb25e36` | U-Boot only, legacy v0, appended live DTB, latest 3 GiB memory build before external-FDT change |
| `hakios-mido-uboot-fastboot-only-v0.img` | `b88a5bbd561ccc723a575e915fb25bc57e3b8b65f4fa03115c0ddcf2fd618866` | USB-only diagnostic U-Boot |
| `hakios-mido-uboot-external-fdt-v0.img` | `faaff0e0c54fd5c56ab3f052027ed68f4a0ec066cefa6a415da979648eac77a6` | Latest normal U-Boot using live Android DTB at runtime |
| `hakios-mido-uboot-only-second-v0.img` | `6085024ee6d6129694b02b95a10b72de176a5eb83d5a8159ac07d20b224728b5` | Negative test; `--second` layout, rejected by ABL with `dtb not found` |

Older experimental images are retained for comparison, but the appended-DTB images above are the useful set.

## Host commands

Run from the workspace root in PowerShell. The local `adb.exe` and `fastboot.exe` are already present.

Check Android/root:

```powershell
.\adb.exe devices -l
.\adb.exe shell su -c id
```

Enter bootloader from rooted LineageOS:

```powershell
.\adb.exe reboot bootloader
```

After the expected USB drop, unplug/reconnect the cable, then verify:

```powershell
.\fastboot.exe devices
```

Perform a RAM-only test:

```powershell
.\fastboot.exe boot .\artifacts\hakios-mido-uboot-external-fdt-v0.img
```

Do not use `fastboot flash` for the current phase. After the phone falls back to LineageOS, reconnect the cable again before using ADB. If ADB cannot start, restart the daemon from an elevated PowerShell:

```powershell
.\adb.exe kill-server
.\adb.exe start-server
.\adb.exe devices -l
```

## Next steps, in priority order

1. Obtain observable early-U-Boot output. The best options are a Qualcomm UART/test-point serial connection or a deliberately built U-Boot `pause`/video-console image that visibly holds instead of attempting HakiOS. Without a serial/display observation, repeated blind USB tests are low value.
2. Verify the live-DTB runtime patch on the phone with U-Boot console output. Check DWC3 wrapper probe, GCC clocks, QUSB2 PHY reset/power, and gadget initialization in that order.
3. Compare mido’s live USB node and clock/reset properties against the known-good Android 4.19 DT and the vince U-Boot/DT. Do not copy vince’s display, touch, memory, identity, or storage constants without mido evidence.
4. Once U-Boot itself re-enumerates, test the HakiOS protocol separately: `fastboot stage x.hkub`, `fastboot oem run:hakios load fastboot`, and `fastboot continue`/`hakios boot` as documented by HakiOS.
5. Only after the loader and kernel run from RAM should storage-backed Darwin be attempted. The read-only eMMC driver and GPT parsing must be validated before any write support.
6. Later, decide whether the compact Darwin/APFS root belongs in the expanded system/super area or another raw partition. Keep a recovery image and rollback path because userdata is only about 4.8 GiB.

## Disk-space notes

The Windows workspace has only about 47 GiB usable, with 3 GiB reserved for Windows stability. The current WSL normal U-Boot build is about 143 MiB; avoid full Android/AOSP rebuilds and duplicate kernel trees. Reuse existing build outputs, keep only one active diagnostic build directory, and do not download a complete Android source tree.

The phone’s existing approximately 2 GiB zram is already the efficient memory workaround. iOS/Darwin does not need its entire system image stored in RAM permanently; the eventual design can keep the root image on phone storage and page/cache through normal memory, but that stage is not yet reached.

## Handoff summary

The port is not at an iOS boot yet. The current verified milestone is: mido’s ABL accepts the legacy appended-DTB RAM image, but the custom U-Boot does not yet re-enumerate USB before the phone falls back to LineageOS. The next useful milestone is a visible/serial U-Boot startup trace and a working U-Boot fastboot gadget; only then should HakiOS loader/kernel debugging continue.

## Shim diagnostic update (2026-11-06)

Claude Code created and built a stripped-down diagnostic shim:

- Environment: `u-boot/board/qualcomm/hakios-mido-shim.env`
- Defconfig: `u-boot/configs/hakios_mido_shim_defconfig`
- WSL image: `$HAKIOS_ROOT/hakios-mido-uboot-shim-v0.img`
- Workspace copy: `artifacts/hakios-mido-uboot-shim-v0.img`
- SHA-256: `653f0b3e752fb80309dabc578294c0a0aef3fca56fcd27eea16108469f33479a`
- Size: 841,728 bytes
- Header: legacy v0, base `0x80000000`, kernel `0x80008000`, 2 KiB page, appended live DTB

The shim has a five-second boot delay, prints `--- HakiOS SHIM ACTIVE ---`, skips HakiOS loading/eMMC probing, and runs U-Boot fastboot directly. Volume Down still enters the U-Boot menu.

Test result: ABL accepted the shim and returned `Sending 'boot.img' ... OKAY` / `Booting ... OKAY`. After the reset, neither fastboot nor ADB re-enumerated within eight seconds. The phone then follows the usual fallback path back to LineageOS, with the known physical cable reconnect needed for Windows to see it again.

Interpretation: this further rules out the HakiOS loader/payload path as the first failure. The next useful test is the proposed shell-only/pause variant, ideally with a UART/test-point trace. If the shim banner or menu is visible on the phone, record that separately; the host-side tools cannot observe the panel during the USB transition.
