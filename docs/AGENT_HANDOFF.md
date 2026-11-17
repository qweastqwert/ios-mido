# Agent handoff: advancing the mido HakiOS port

This document is for the next coding agent. Treat it as an engineering log, not as permission to take destructive actions.

## Mission

Advance the HakiOS/iOS 16.5 port to the Redmi Note 4/4X (`mido`, MSM8953, 3 GiB RAM). The immediate milestone is not “boot iOS”; it is to make a RAM-loaded mido U-Boot image visibly reach a stable diagnostic state and re-enumerate USB fastboot.

Do not claim a feature works because it compiles, because ABL accepts `fastboot boot`, or because a phone returns to Android. A result is verified only when the target behavior is observed and recorded.

## Ground truth

- Boot chain: `sbl1 -> aboot -> boot/recovery`.
- No XBL, no SBL2, no UEFI firmware path, no A/B slots, and no `dtbo` by-name partition were observed.
- Legacy Android boot image is accepted with 2 KiB pages, base `0x80000000`, kernel address `0x80008000`.
- RAM layout from the authoritative dynamic LOS23 DTB: 1 GiB at `0x40000000` plus 2 GiB at `0x80000000`.
- Storage is eMMC through MSM8953 SDHCI1, not UFS.
- USB hardware: MSM8953 DWC3 wrapper near `0x070f8800`, DWC3 core near `0x07000000`, QUSB2 PHY.
- Display: OTM1911 1080x1920. Touch: FocalTech `fts_ts-mi8953` at I2C `0x38`.
- Android has roughly 2 GiB zram, but zram cannot solve the loader’s early physically-contiguous-memory requirement.

The authoritative DT documentation is under `evidence/mido-los23-dynamic/`. Do not revive the older non-dynamic capture as the source of truth.

## What has already been proven

1. HakiOS 2.3.4 kernel builds as Mach-O arm64.
2. A read-only mido eMMC/SDHCI driver was added and compile-checked.
3. Mido-specific U-Boot source, GCC clock/reset/power support, memory map, and USB DTS were added.
4. ABL accepts several appended-DTB RAM-only images.
5. Putting the DTB in Android boot-image `--second` is wrong: ABL returns `dtb not found`.
6. Full HakiOS images, U-Boot-only images, a USB-only image, a live-DTB variant, and a five-second diagnostic shim all lose USB after the ABL handoff and eventually return to LineageOS.
7. The host often needs a physical cable unplug/replug after reboot before ADB/fastboot reappears. This is a Windows transport issue, separate from U-Boot USB initialization.

Therefore, the current blocker is early U-Boot/USB/PHY bring-up, not the HakiOS loader payload. Do not spend the next iteration rewriting the payload until U-Boot itself is observable.

## Rehydrate a development environment

Use a fresh WSL checkout; do not depend on deleted absolute paths or personal usernames:

```bash
export WORK="$HOME/work"
export HAKIOS_ROOT="$WORK/hakios-234"
mkdir -p "$WORK"
git clone --depth=1 https://github.com/oosexgang/hakios-xnu-kernel "$HAKIOS_ROOT"
```

The exact HakiOS commit used for the previous checkpoint is documented in the root README. Check upstream history before assuming branch names or repository layout; HakiOS repositories have been force-rewritten before.

Obtain the current U-Boot/UEFI sources using the current HakiOS instructions and inspect the repository’s own scripts before cloning extra trees. Keep the checkout shallow and avoid a full Android/AOSP tree because host storage is limited.

Copy or regenerate the mido-specific source from this repository’s `porting/mido-u-boot/` into the HakiOS checkout. The helper scripts require:

```bash
export HAKIOS_ROOT="$HOME/work/hakios-234"
```

Never hard-code another person’s `/home/...` or Windows path into a committed helper.

## Required test discipline

For every experiment, record:

- source commit and changed files;
- generated image SHA-256;
- boot header version/base/page/kernel address;
- exact command used;
- whether the image was RAM-only or flashed;
- fastboot/ADB state before handoff, immediately after, and after cable reconnect;
- visible phone/UART output if available;
- the honest result: passed, failed, inconclusive, or not tested.

Keep a failed experiment as a failed experiment. Do not overwrite logs or edit a status document to make a failed boot look successful.

## Next work sequence

### 1. Build an observable shell/pause image

Use the existing shim and pause configurations as references. Make the earliest boot path stop in a diagnostic state rather than trying HakiOS. Keep video output and USB paths independently selectable.

If possible, attach a 1.8 V Qualcomm UART/test point. A UART trace is much more useful than guessing from USB disappearance. If no UART is available, use the panel and a long `pause`/menu delay, then record exactly what is visible.

### 2. Prove the U-Boot FDT choice

Compare the internal compiled mido DTB and the external DTB handed over by ABL. Instrument or print:

- chosen FDT address;
- parsed RAM banks;
- DWC3 wrapper/core nodes and `dr_mode`;
- clock and reset phandles;
- QUSB2 PHY compatible, clocks, supplies, and reset;
- reserved-memory regions.

The external Android DT is hardware evidence, but using it wholesale may carry Android-only nodes that U-Boot cannot probe. Test a minimal, explicitly constructed U-Boot DT against the live DT rather than assuming either is correct.

### 3. Diagnose USB in dependency order

Do not randomly change ten registers. Verify in this order:

1. GCC provider binds for MSM8953.
2. Required USB branch clocks enable without timeout.
3. USB30 power domain and resets transition correctly.
4. QUSB2 PHY reset, supplies, reference clock, and power-on complete.
5. DWC3 wrapper probes and enters peripheral mode.
6. U-Boot gadget initializes.
7. `fastboot usb 0` remains alive long enough for Windows to enumerate it.

Compare every custom register offset/rate with the Linux MSM8953 GCC and PHY drivers and the Android DT. A successful compile is not evidence that a register sequence is correct.

### 4. Only after U-Boot fastboot works, test HakiOS protocol

Use a host-side sequence such as:

```text
fastboot stage x.hkub
fastboot oem run:hakios load fastboot
fastboot continue
```

Confirm the staged payload size/hash and obtain a loader-visible result. Keep this separate from the initial ABL `fastboot boot` image test.

### 5. Then test the kernel and memory placement

The earlier QEMU result showed the standard profile needs 7 GiB and smaller profiles fail in the loader with `not enough contiguous RAM`. A 3 GiB mido port therefore needs a smaller/repacked image or segmented/demand-paged placement. Do not assume swap/zram fixes that early loader allocation.

Measure the actual reserved regions and available contiguous ranges from the mido DTB before changing the loader contract. Keep the 64 MiB HakiOS payload reservation below the relevant RAM limit and verify that it does not collide with ABL/Android reservations.

### 6. Storage-backed Darwin comes last

The expanded raw system/super area is not automatically a Darwin filesystem. Before any storage write:

- validate read-only eMMC initialization;
- parse GPT read-only;
- expose one selected partition read-only;
- test mounting/reading from a RAM-loaded loader;
- make and verify complete recovery images;
- document rollback.

Do not add write commands or flashing instructions merely because storage reads work.

## Safety rules

- Default to `fastboot boot`, never `fastboot flash`.
- Never run `erase`, `format`, `dd`, repartitioning, or raw partition writes without explicit review and a recovery plan.
- Never use `rm -rf` on a broad workspace path; resolve and print the exact target first.
- Do not commit raw `persist`, `sbl1`, `aboot`, `boot`, recovery, IMEI, MAC, serial, or user-data captures.
- Do not commit credentials, tokens, personal paths, local settings, or generated binaries.
- If a test returns to Android, that means recovery succeeded—not that the experimental image worked.

## Definition of done for a contribution

A contribution is ready only when its PR states:

1. what changed;
2. why the change is expected to help mido;
3. what was actually tested;
4. exact observed output;
5. image/source hashes;
6. remaining uncertainty;
7. whether any phone partition was written.

If hardware testing is unavailable, label the change compile-only or static-analysis-only. Never call it working.
