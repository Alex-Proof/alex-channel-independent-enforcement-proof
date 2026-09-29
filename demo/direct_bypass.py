#!/usr/bin/env python3
"""A deliberate write path that does not use MCP."""

import errno
from pathlib import Path
import sys

target = Path(sys.argv[1])
try:
    target.write_text("NON_MCP_BYPASS_MARKER\n", encoding="utf-8")
except OSError as error:
    name = errno.errorcode.get(error.errno, "OS_ERROR")
    print(f"direct write denied: {name}", file=sys.stderr)
    raise SystemExit(1)
print(f"direct write completed: {target.name}")
