#!/usr/bin/env bash
set -euo pipefail

OBSIGNA_COMMIT="77f36a22a6720deb4151970b047b0101a426f38d"
work="${RUNNER_TEMP:-/tmp}/channel-proof-obsigna"
rm -rf "$work"
mkdir -p "$work"

git clone --filter=blob:none https://github.com/agent-receipts/obsigna.git "$work/obsigna"
git -C "$work/obsigna" checkout --detach "$OBSIGNA_COMMIT"
(cd "$work/obsigna/mcp-proxy" && go build -o "$work/obsigna-mcp" ./cmd/obsigna-mcp)

cat >"$work/rules.yaml" <<'YAML'
rules:
  - name: prove_proxy_is_active
    description: Deterministically block the demo MCP tool call
    enabled: true
    tool_pattern: "demo_write"
    action: block
YAML

mediated="$work/mediated.txt"
bypass="$work/NON_MCP_BYPASS_MARKER.txt"
printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"demo_write","arguments":{"path":"'"$mediated"'"}}}' |
  "$work/obsigna-mcp" --socket= --http=none --name channel-proof --rules "$work/rules.yaml" \
  python3 demo/mcp_server.py >"$work/proxy.stdout" 2>"$work/proxy.stderr" || true

grep -q 'policy_event tool="demo_write"' "$work/proxy.stderr"
test ! -e "$mediated"

python3 demo/direct_bypass.py "$bypass" >"$work/bypass.stdout" 2>"$work/bypass.stderr"
grep -q 'NON_MCP_BYPASS_MARKER' "$bypass"
if grep -R -q 'NON_MCP_BYPASS_MARKER' "$work/proxy.stdout" "$work/proxy.stderr"; then
  echo "unexpected: Obsigna proxy log contains the non-MCP bypass marker" >&2
  exit 1
fi

python3 - <<'PY' "$work/result.json" "$OBSIGNA_COMMIT"
import json, sys
json.dump({
    "obsigna_commit": sys.argv[2],
    "mediated_mcp_call": "blocked_and_logged",
    "non_mcp_write": "completed",
    "non_mcp_marker_in_proxy_logs": False,
}, open(sys.argv[1], "w"), indent=2)
PY
cat "$work/result.json"
