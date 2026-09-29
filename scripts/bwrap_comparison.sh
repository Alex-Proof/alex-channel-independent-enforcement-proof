#!/usr/bin/env bash
set -euo pipefail

target="$PWD/NON_MCP_BYPASS_MARKER.txt"
rm -f "$target"
set +e
bwrap \
  --ro-bind / / \
  --dev-bind /dev /dev \
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
