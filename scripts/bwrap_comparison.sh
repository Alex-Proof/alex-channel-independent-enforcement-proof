#!/usr/bin/env bash
set -euo pipefail

# --dev-bind would bind the host's REAL /dev into the sandbox, including raw block device nodes
# (e.g. /dev/sda) -- a write to the underlying block device would bypass the read-only bind-mount
# on the filesystem above it entirely. --dev instead gives a minimal, isolated devtmpfs (null,
# zero, random, urandom, tty, pts, shm -- no block devices). Verify that directly, don't just
# trust bwrap's documented behavior.
block_devices=$(bwrap --ro-bind / / --dev /dev --proc /proc --tmpfs /tmp --chdir "$PWD" \
  find /dev -type b 2>/dev/null || true)
if [ -n "$block_devices" ]; then
  echo "unexpected: sandboxed /dev exposes block devices: $block_devices" >&2
  exit 1
fi
echo "confirmed: sandboxed /dev exposes zero block devices"

target="$PWD/NON_MCP_BYPASS_MARKER.txt"
rm -f "$target"
set +e
bwrap \
  --ro-bind / / \
  --dev /dev \
  --proc /proc \
  --tmpfs /tmp \
  --chdir "$PWD" \
  python3 observer/deny_observer.py --require-denial -- \
  python3 demo/direct_bypass.py "$target" >"${RUNNER_TEMP:-/tmp}/bwrap-events.jsonl" 2>"${RUNNER_TEMP:-/tmp}/bwrap.stderr"
status=$?
set -e

test "$status" -ne 0
test ! -e "$target"
grep -Eq '"errno": "(EROFS|EACCES)"' "${RUNNER_TEMP:-/tmp}/bwrap-events.jsonl"
grep -q '"event": "kernel_write_denied"' "${RUNNER_TEMP:-/tmp}/bwrap-events.jsonl"
cat "${RUNNER_TEMP:-/tmp}/bwrap-events.jsonl"
