#!/usr/bin/env python3
"""Package a mido U-Boot binary as an Android v0 RAM-boot image."""

import argparse
import gzip
import os
import struct
import subprocess
import tempfile
from pathlib import Path


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("uboot", type=Path)
parser.add_argument("dtb", type=Path)
parser.add_argument("output", type=Path)
args = parser.parse_args()

root_value = os.environ.get("HAKIOS_ROOT")
if not root_value:
    raise SystemExit("set HAKIOS_ROOT to the legacy HakiOS checkout containing devices/mido/prebuilt/mkbootimg.py")
root = Path(root_value).expanduser().resolve()
mkbootimg = root / "devices/mido/prebuilt/mkbootimg.py"
if not mkbootimg.is_file():
    raise SystemExit(f"legacy mido mkbootimg.py not found: {mkbootimg}")
for source in (args.uboot, args.dtb):
    if not source.is_file():
        raise SystemExit(f"input file not found: {source}")

args.output.parent.mkdir(parents=True, exist_ok=True)
with tempfile.TemporaryDirectory(prefix="mido-boot-v0-") as temp_dir:
    temp = Path(temp_dir)
    kernel = temp / "kernel.gz-dtb"
    ramdisk = temp / "empty-ramdisk"
    kernel.write_bytes(gzip.compress(args.uboot.read_bytes(), compresslevel=6) + args.dtb.read_bytes())
    ramdisk.write_bytes(b"\0")
    subprocess.check_call([
        "python3", str(mkbootimg),
        "--kernel", str(kernel), "--ramdisk", str(ramdisk),
        "--header_version", "0", "--base", "0x80000000", "-o", str(args.output),
    ])

with args.output.open("rb") as image:
    header = image.read(64)
if len(header) < 44:
    raise SystemExit(f"mkbootimg produced an invalid short image: {args.output}")
print("image:", args.output)
print("kernel address:", hex(struct.unpack_from("<I", header, 12)[0]))
print("page size:", struct.unpack_from("<I", header, 36)[0])
print("header version:", struct.unpack_from("<I", header, 40)[0])
