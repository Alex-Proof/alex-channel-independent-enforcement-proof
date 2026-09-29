# Channel-independent write-deny proof

This repository tests one narrow claim:

> An MCP proxy can prevent a mediated MCP tool call, but it cannot prevent or witness an effect that bypasses that channel. A Linux mount-namespace boundary can prevent the same write independently of whether the caller used MCP.

It does **not** compare receipt signing, hash chains, fail-closed behavior, policy quality, or product maturity. Obsigna is a mature multi-language receipt system with formal-verification work and a separate signing daemon. The boundary shown here is explicit in its own documentation, not presented as a defect.

## Pinned comparison

The workflow builds Obsigna from commit [`77f36a22a6720deb4151970b047b0101a426f38d`](https://github.com/agent-receipts/obsigna/tree/77f36a22a6720deb4151970b047b0101a426f38d).

Its threat model says:

> “The audit trail can only witness traffic that passes through the proxy. Out of scope.”

Source: [Obsigna threat model, “Colluding MCP client that bypasses the proxy”](https://github.com/agent-receipts/obsigna/blob/77f36a22a6720deb4151970b047b0101a426f38d/docs/threat-model.md#colluding-mcp-client-that-bypasses-the-proxy).

Its runtime hook is broader than the MCP proxy but post-action by design:

> “It never pauses or modifies the tool call.”

Source: [Obsigna hook README](https://github.com/agent-receipts/obsigna/blob/77f36a22a6720deb4151970b047b0101a426f38d/hook/README.md).

The Obsigna daemon signs and stores emitter events. The cited threat model describes the proxy and hook as emitters and the daemon as the sole signer; it does not claim an independent effect-prevention boundary.

## What CI executes

On `ubuntu-22.04`, `ubuntu-24.04`, and `ubuntu-latest`, the workflow:

1. builds the real `obsigna-mcp` binary from the pinned commit;
2. sends a demo `tools/call` through it and verifies that the proxy blocks and logs that mediated call;
3. runs the same write directly, outside MCP, and verifies that it completes without appearing in the proxy logs;
4. runs that direct write under a read-only `bwrap` mount namespace;
5. captures the resulting kernel `EROFS` or `EACCES` with `strace`, emitting only a redacted JSONL event.

The observer is intentionally small and newly written for this public proof. It is not the private ALEX implementation and contains no customer policy, capability pack, or production integration.

## Local checks

Parser and redaction tests are portable:

```sh
python3 -m unittest discover -s tests -v
```

The two integration scripts require Linux, Python 3, Git, Go, `bubblewrap`, and `strace`:

```sh
bash scripts/obsigna_comparison.sh
bash scripts/bwrap_comparison.sh
```

## Interpretation

A green run proves only the tested write-denial property on the listed GitHub-hosted Ubuntu images and the pinned Obsigna revision. It does not prove that every Linux action is sandboxed, that the observer is tamper-proof, or that either project is universally more secure.

## Proposed license

Apache-2.0. The license file will be added only after the repository name, license, and this README are approved for public release.
