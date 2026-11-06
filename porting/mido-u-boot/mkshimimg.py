#!/usr/bin/env python3
import gzip, os, struct, subprocess, sys
root = os.environ.get("HAKIOS_ROOT")
if not root:
    raise SystemExit("set HAKIOS_ROOT to the HakiOS checkout containing devices/mido/prebuilt/mkbootimg.py")
build = sys.argv[1] if len(sys.argv) > 1 else "build-mido-shim"
hdr = sys.argv[2] if len(sys.argv) > 2 else "0"
out = sys.argv[3] if len(sys.argv) > 3 else root + "/hakios-mido-uboot-shim-v0.img"
kernel = "/tmp/mido-uboot-shim-kernel"
ramdisk = "/tmp/mido-uboot-shim-ramdisk"
with open(kernel, "wb") as f:
    f.write(gzip.compress(open(root + "/u-boot/" + build + "/u-boot.bin", "rb").read(), 6))
    f.write(open(root + "/devices/mido/prebuilt/device-tree.dtb", "rb").read())
with open(ramdisk, "wb") as f:
    f.write(b"\0")
subprocess.check_call([
    "python3", root + "/devices/mido/prebuilt/mkbootimg.py",
    "--kernel", kernel, "--ramdisk", ramdisk,
    "--header_version", hdr, "--base", "0x80000000", "-o", out,
])
with open(out, "rb") as image:
    h = image.read(64)
    print("image:", out)
    print("kernel address:", hex(struct.unpack_from("<I", h, 12)[0]))
    print("page size:", struct.unpack_from("<I", h, 36)[0])
    print("header version:", struct.unpack_from("<I", h, 40)[0])
