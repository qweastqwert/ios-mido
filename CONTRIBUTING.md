# Contributing

## Verify before committing or pushing

Do not blindly commit or push an unverified fix or feature. Every contribution must be tested on the intended mido hardware, in QEMU when applicable, or with a clearly documented compile/static check when hardware is unavailable.

For each change, include:

- the exact command or test procedure;
- the target device/build and relevant toolchain commit;
- the observed result, including failures;
- hashes for generated images when an image is involved;
- a statement that no partition was written, or an explicit explanation and recovery plan if a write was required.

“Builds successfully” is not equivalent to “works on mido.” A fastboot-accepted image is not equivalent to a booted HakiOS system.

## Safety and privacy

- Do not commit passwords, access tokens, ADB serials, IMEIs, MAC addresses, raw user data, or host-specific absolute paths.
- Do not commit raw `persist`, `sbl1`, `aboot`, `boot`, or other phone partition dumps unless there is a documented legal and technical reason.
- Keep tests RAM-only until the boot path has been independently verified.
- Never add `fastboot flash`, `erase`, `format`, repartitioning, or storage-write code without an explicit review and rollback procedure.
- Keep failed experiments documented as failed; do not rewrite them into apparent successes.

Before opening a pull request, run a local secret/path scan and review `git diff --check`.
