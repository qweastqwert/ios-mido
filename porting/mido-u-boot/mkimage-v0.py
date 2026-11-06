#!/usr/bin/env python3
import gzip
import struct
import subprocess
import os
import sys

if len(sys.argv) != 4:
    raise SystemExit(f"usage: {sys.argv[0]} UBOOT.BIN DTB OUTPUT.IMG")

uboot, dtb, output = sys.argv[1:]
root = os.environ.get("HAKIOS_ROOT")
if not root:
    raise SystemExit("set HAKIOS_ROOT to the HakiOS checkout containing devices/mido/prebuilt/mkbootimg.py")
kernel = "/tmp/mido-uboot-custom-kernel-v0"
ramdisk = "/tmp/mido-empty-ramdisk-custom-v0"

with open(kernel, "wb") as out:
    out.write(gzip.compress(open(uboot, "rb").read(), 6))
    out.write(open(dtb, "rb").read())
with open(ramdisk, "wb") as out:
    out.write(b"\0")

subprocess.check_call([
    "python3", root + "/devices/mido/prebuilt/mkbootimg.py",
    "--kernel", kernel, "--ramdisk", ramdisk,
    "--header_version", "0", "--base", "0x80000000", "-o", output,
])

with open(output, "rb") as image:
    header = image.read(64)
    print("kernel address:", hex(struct.unpack_from("<I", header, 12)[0]))
    print("page size:", struct.unpack_from("<I", header, 36)[0])
    print("header version:", struct.unpack_from("<I", header, 40)[0])
