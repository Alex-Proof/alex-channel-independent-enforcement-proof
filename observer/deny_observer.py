#!/usr/bin/env python3
"""Run a command under strace and emit observed kernel write denials as JSONL."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

DENIED = {"EACCES", "EROFS"}
SYSCALL_RE = re.compile(
    r'^(?:\[pid\s+(?P<pid>\d+)\]\s+)?(?P<call>openat2?|creat|write|pwrite64)\((?P<args>.*)\)\s+=\s+-1\s+(?P<errno>EACCES|EROFS)\b'
)
QUOTED_RE = re.compile(r'"((?:[^"\\]|\\.)*)"')
FD_RE = re.compile(r"^(?P<fd>\d+),")


def redact_path(value: str) -> str:
    """Keep only a stable basename; never emit host directory structure."""
    if value.startswith("<fd:"):
        return value
    return f"<redacted>/{Path(value).name or '<root>'}"


def parse_denial(line: str, source: str = "strace") -> dict[str, object] | None:
    match = SYSCALL_RE.search(line.strip())
    if not match:
        return None
    syscall = match.group("call")
    arguments = match.group("args")
    quoted = QUOTED_RE.findall(arguments)
    if syscall in {"openat", "openat2"}:
        raw_path = quoted[0] if quoted else "<unknown>"
    elif syscall == "creat":
        raw_path = quoted[0] if quoted else "<unknown>"
    else:
        fd_match = FD_RE.match(arguments)
        raw_path = f"<fd:{fd_match.group('fd')}>" if fd_match else "<fd:unknown>"
    return {
        "event": "kernel_write_denied",
        "errno": match.group("errno"),
        "syscall": syscall,
        "path": redact_path(raw_path),
        "pid": int(match.group("pid")) if match.group("pid") else None,
        "source": source,
    }


def parse_trace_files(prefix: Path) -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    for trace in sorted(prefix.parent.glob(prefix.name + "*")):
        for line in trace.read_text(encoding="utf-8", errors="replace").splitlines():
            event = parse_denial(line, trace.name)
            if event:
                events.append(event)
    return events


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-denial", action="store_true")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("a command is required after --")

    with tempfile.TemporaryDirectory(prefix="deny-observer-") as directory:
        trace_prefix = Path(directory) / "trace"
        traced = [
            "strace", "-ff", "-qq", "-s", "4096",
            "-e", "trace=openat,openat2,creat,write,pwrite64",
            "-o", str(trace_prefix), "--", *command,
        ]
        completed = subprocess.run(traced, check=False)
        events = parse_trace_files(trace_prefix)
        for event in events:
            print(json.dumps(event, sort_keys=True), flush=True)
        if args.require_denial and not events:
            print("deny-observer: expected EROFS/EACCES but observed none", file=sys.stderr)
            return 65
        return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
