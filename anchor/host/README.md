# anchor-surface-host

> The substrate's signing endpoint, held outside the operator process.
> Closes Phase γ.5's "operator-IS-anchor honor-system collapse" finding.

## What this is

Myco's owner Ed25519 private key signs every CI-class mutation. Pre-M-anchor-1, the operator process held that key in its own memory: meaning any agent that could read operator memory could forge owner signatures, collapsing the entire trust model into an honor system.

**anchor-surface-host** is the fix: a separate Rust daemon holds the owner Ed25519 key and serves `sign` / `get_pubkey` requests over local TCP. The operator becomes a thin client; the key never enters operator memory.

```
operator  ◄── 127.0.0.1:R ──►  anchor-surface-host
(thin client)                  (holds owner Ed25519, never ships it)
```

## Quick start

```bash
cargo build --release -p anchor-surface-host
target/release/anchor-surface-host
# anchor-surface-host listening on 127.0.0.1:<port>
```

Storage at `~/.myco/anchor_surface/` (Unix) or `%USERPROFILE%\.myco\anchor_surface\` (Windows):

- `owner_key.cb`: Ed25519 seed, 32 bytes, mode 0600
- `port.txt`: resolved TCP port, mode 0600

First boot generates a fresh keypair; subsequent boots load it. **Back up `owner_key.cb` to encrypted external media immediately. Losing it ends the Cultivar's identity.**

## Hard rules

1. Owner private key NEVER appears in operator memory.
2. Separate binary; operator talks over local TCP.
3. `owner_key.cb` is mode 0600 on Unix.
4. `OperatorIdentity` on the operator side is a thin TCP client.
5. Single-tenant: one host per cultivator.

## Protocol

`ping` · `get_pubkey` · `sign`. Canonical-bytes frames, same shape as bridge protocol. See `protocol.rs`.

## Environment overrides

`MYCO_ANCHOR_SURFACE_DIR` (test / multi-tenant) · `MYCO_ANCHOR_SURFACE_BIND_ADDR` (default `127.0.0.1:0`) · `MYCO_ANCHOR_SURFACE_OWNER_SEED_HEX` (testing only)

## Deferred (M-anchor-1.5)

OS-sealing (TPM / Secure Enclave / kernel keyring / DPAPI), cross-process auth, TLS. Interim defense: chmod 0600 + localhost-only TCP bind. For long-running daemons, use systemd user service / launchd plist / Windows Service.

## Doctrine traceability

[`AS_anchor_surface`](../../docs/architecture/L0/cards/AS_anchor_surface.md) · L1/GOVERNANCE §2.1 · L1/HARD_RULES C4 (analogue) · Phase γ.5 audit resolution.
