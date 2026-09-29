#!/usr/bin/env python3
"""Minimal newline-delimited JSON-RPC MCP-shaped demo server."""

import json
import sys
from pathlib import Path

for line in sys.stdin:
    request = json.loads(line)
    request_id = request.get("id")
    method = request.get("method")
    if method == "initialize":
        result = {"protocolVersion": "2025-06-18", "capabilities": {"tools": {}}, "serverInfo": {"name": "channel-proof", "version": "1.0.0"}}
    elif method == "tools/list":
        result = {"tools": [{"name": "demo_write", "description": "Write a marker", "inputSchema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}]}
    elif method == "tools/call":
        target = Path(request["params"]["arguments"]["path"])
        target.write_text("MCP_MARKER\n", encoding="utf-8")
        result = {"content": [{"type": "text", "text": "written"}]}
    else:
        result = {}
    if request_id is not None:
        print(json.dumps({"jsonrpc": "2.0", "id": request_id, "result": result}), flush=True)
