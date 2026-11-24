# Agent handoff: advancing the mido HakiOS port

This document is for the next coding agent. Treat it as an engineering log, not as permission to take destructive actions.

## Mission

Advance the legacy HakiOS 2.3.4 / iOS 16.5 port to the Redmi Note 4/4X (`mido`, MSM8953, 3 GiB RAM). Pin work to the legacy XNU `xnu-8796.121.2` line and its matching iPhoneOS 16.5 SDK. Do not use the newer Darwin 26/27 (`xnu-12377.121.6`) tree for this target.

The immediate technical milestone remains to reach an observable, stable RAM-loaded boot stage on mido, but first re-evaluate whether current upstream already supports the relevant boot and device-port workflow.

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

1. The earlier HakiOS 2.3.4 kernel built as Mach-O arm64. This is historical evidence, not validation against current upstream.
2. A read-only mido eMMC/SDHCI driver was added and compile-checked.
3. Mido-specific U-Boot source, GCC clock/reset/power support, memory map, and USB DTS were added.
4. ABL accepts several appended-DTB RAM-only images.
5. Putting the DTB in Android boot-image `--second` is wrong: ABL returns `dtb not found`.
6. Full HakiOS images, U-Boot-only images, a USB-only image, a live-DTB variant, and a five-second diagnostic shim all lose USB after the ABL handoff and eventually return to LineageOS.
7. The host often needs a physical cable unplug/replug after reboot before ADB/fastboot reappears. This is a Windows transport issue, separate from U-Boot USB initialization.

Historical diagnosis from our 2.3.4 experiments: U-Boot/USB/PHY failed before a visible diagnostic state. It is no longer a sufficient current diagnosis because the independent mido scaffold reports a later boot stage; compare its evidence and reproduce the smallest observable step before deciding which boot path to pursue.

## Current upstream re-evaluation (required first)

Read the legacy checkout's `README.md`, `CHANGELOG.md`, device-port guide, U-Boot guide, and build docs. Do not follow newer `make phone FROM=URL`, Darwin 26/27, or `common` branch instructions for this target. Confirm the source tags and exact commit against the 2.3.4 changelog before building.

Compare the old mido work in this repository against current upstream:

- Is there already a device-package model for mido?
- Does current kernel still accept the old `devices/mido` layout, or should the device be a separate repository with `board.dts` at its root?
- Which current Darwin release and loader contract does upstream target?
- Which existing board drivers and tests now replace the custom MSM8953 U-Boot work?
- Does the legacy mido `sbl1 -> aboot` chain fit current upstream's UEFI/phone workflow at all?

Write a short compatibility assessment and proposed migration map before transplanting the old code. Keep old code as a reference until each corresponding current-upstream implementation is built and tested.

### External mido scaffold reviewed

The [Caiyutaojing0721/mido-ios-xnu repository](https://github.com/Caiyutaojing0721/mido-ios-xnu) is now the most directly relevant mido reference. Its `docs/MIDO.md` is a long, active engineering log, and its conclusions need to be read at the relevant sections rather than relying on the repository README summary, which is internally stale: the README calls the mido scaffold unbooted, while the later MIDO log records a readable mido shim boot and an XNU handoff that hangs during early startup.

Key findings from that log:

- A mido diagnostic shim reportedly executed on hardware and showed a readable 1080x1920 console. A later custom XNU image reached `XNU jumping` but stopped before the first MMU-on progress mark. The log attributes that failure to an unmapped framebuffer and subsequently investigates early page-table/MMU setup. This is materially ahead of our historical U-Boot USB disappearance, but it is third-party evidence and has not been reproduced on this device.
- The scaffold reuses an iOS 16 era XNU 8796 / SWEET build pipeline, makes board-specific ADT and kernel patches, and packages a legacy Android boot image with a gzip `Image` plus appended stock DTB. The reported mido `fastboot boot` shim output and XNU-stage experiments are not proof of a complete iOS boot.
- It explicitly identifies the eMMC/SDHCI root backend as missing; the board files described there include a refusing/disabled eMMC gate, not a usable root filesystem driver. Touch, buttons, Adreno 506, and other phone functions are also incomplete.
- Its stated register/boot geometry came from a different mido boot image (crDroid 15) and is a valuable cross-check, not a replacement for our live dynamic LOS23 evidence. In particular, its RAM probe reports unresolved RAM sizing and the project says real installed RAM remains to be confirmed.
- The MIDO log lists later patch numbers through `0102` and says the immediate next step is to build/run its patched XNU with early boot tracing. Before using that prescription, inspect the actual commit, patch contents, scripts, provenance, and current upstream compatibility; do not copy generated images or any device dumps.

The legacy HakiOS 2.3.4 changelog identifies XNU `xnu-8796.121.2` (the Darwin 16.5 kernel), iPhoneOS 16.5 SDK tools, U-Boot `v2026.07`, and Mu-Silicium UEFI as its source line. Pin the exact legacy checkout commit before building. Do not follow the newer `common` branch or its Darwin 26/27 APIs for this work. The external mido scaffold is likewise an iOS 16-era reference and records the boot-image and early XNU lessons.

The mido phone's observed `sbl1 -> aboot` chain is still a key compatibility constraint. The old U-Boot tree and ABL RAM boot are the initial route; UEFI is not assumed. Therefore:

1. Treat the external `mido-ios-xnu` branch as the nearest implementation reference for the existing iOS 16.5-era port, especially its early XNU bring-up and boot-image lessons.
2. Use only the pinned legacy HakiOS 2.3.4 checkout for implementation. Reuse its U-Boot and loader contract, and adapt the existing mido configs/DTS and read-only MMC code there.
3. Keep the external iOS 16.5 mido scaffold and the independently captured dynamic LOS23 hardware baseline distinct; cross-check board constants before reuse.
4. First milestone: make the mido RAM-boot diagnostic shim reach a clear screen. Then advance through the scaffold's early XNU/MMU milestones. Keep every boot RAM-only until evidence supports a more permanent path.

## Rehydrate a development environment

Use a fresh WSL checkout; do not depend on deleted absolute paths or personal usernames. The legacy 2.3.4 code is the target; clone its documented public kernel repository shallowly and record the commit before building:

```bash
export WORK="$HOME/work"
export HAKIOS_ROOT="$WORK/hakios-234"
mkdir -p "$WORK"
git clone --depth=1 https://github.com/oosexgang/hakios-xnu-kernel "$HAKIOS_ROOT"
git -C "$HAKIOS_ROOT" rev-parse HEAD
```

The expected 2.3.4 line uses XNU `xnu-8796.121.2` and the iPhoneOS 16.5 SDK. Confirm the checked-out changelog says 2.3.4 and these source versions; if it does not, stop before applying mido changes. Keep the checkout shallow and avoid cloning a second large build tree.

Use the U-Boot and loader sources bundled/configured by that legacy checkout. The prior separate `hakios-uefi` repository is reference only; do not mix its independent current profile model into the legacy build without a demonstrated need.

Adapt the mido source under `porting/mido-u-boot/` directly to the legacy tree's expected device layout. Use the external mido scaffold for its iOS 16-era early XNU/MMU findings, but independently validate any constants or patches against our dynamic LOS23 device tree. The existing helper scripts require:

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

First inspect the legacy U-Boot phone workflow and the old shim/pause configs. Build a minimal diagnostic image that stops visibly before loading Darwin. Keep video output and USB paths independently testable.

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

Only use the legacy HakiOS phone test workflow after U-Boot and USB behavior are understood. Revalidate each command against the pinned checkout:

```text
fastboot stage x.hkub
fastboot oem run:hakios load fastboot
fastboot continue
```

Confirm the staged payload size/hash and obtain a loader-visible result. Keep this separate from the initial ABL `fastboot boot` image test.

### 5. Then test the current kernel and memory placement

The earlier QEMU result showed the old 2.3.4 profile needed 7 GiB and smaller profiles failed in that loader with `not enough contiguous RAM`. Recheck this limitation against the pinned legacy loader and its documented QEMU/host workflow. Do not assume swap/zram fixes early contiguous-memory allocation.

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
