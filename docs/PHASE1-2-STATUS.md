# HackiOS mido port — phases 1 and 2

Completed in an Ubuntu WSL2 checkout of HakiOS.

## Completed

- Installed the minimal QEMU/image-build toolchain.
- Shallow-cloned `oosexgang/hackios-xnu-kernel`.
- Downloaded and extracted the iOS 16.5 (20F66) inputs with `sysimage/fetch.sh`.
- Built `userland/root.apfs` and `userland/system.apfs`.
- Booted the stock HackiOS QEMU target with the repository prebuilt kernel/loader.
- Confirmed launchd, SpringBoard, wifid, and HackiOS injected services reached userspace.
- Timed QEMU session exited cleanly.

## Important memory result

The standard 7 GiB QEMU profile boots. 3 GiB, 4 GiB, and 5 GiB profiles all fail in `xnuloader` before XNU starts with:

```text
not enough contiguous RAM
```

Therefore zram or swap cannot solve the immediate mido constraint. The loader needs a physically contiguous region before the kernel and VM are running. A 3 GiB mido port will require reducing/repacking the memory layout or changing the loader to support segmented/demand-paged image placement.

## Useful commands

```bash
cd "$HAKIOS_ROOT"
QEMU_EFI=/usr/share/AAVMF/AAVMF_CODE.fd \
QEMU_VARS=/usr/share/AAVMF/AAVMF_VARS.fd \
QEMU_RAM_GB=7 qemu/run-ios.sh 180 -display none > logs/qemu.log 2>&1
```

The 3 GiB failure is in `logs/qemu-3gb.log`; the successful run is in `logs/qemu.log`.
