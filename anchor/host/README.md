# anchor-surface-host

> The substrate's signing endpoint, held outside the operator process.
> Closes Phase γ.5's "operator-IS-anchor honor-system collapse" finding.

## What this is

Myco's owner Ed25519 private key signs every CI-class mutation
(`l0_revision_attest`, `schema_evolution`, `cost_budget_set`,
`owner_objective_declaration`, `dag_tip_cosign`). Pre-M-anchor-1, the
operator process held that key in its own memory — meaning any agent
that could read operator memory could forge owner signatures, collapsing
the entire trust model into an honor system.

**anchor-surface-host** is the fix: a separate Rust daemon that holds the
owner Ed25519 key and serves sign / get_pubkey requests over local TCP.
The operator (e.g. `operators/claude`) becomes a thin client; the key
never enters operator memory.

```text
┌────────────────────────────┐  local TCP   ┌─────────────────────────────┐
│  operators/claude          │ ◄──────────► │  anchor-surface-host        │
│  (or any operator runtime) │ 127.0.0.1:R  │  (THIS binary)              │
│                            │              │                             │
│  • talks to substrate      │              │  • holds owner Ed25519 key  │
│  • drives Cultivar via     │              │  • NEVER ships key to       │
│    AnchorSurfaceClient     │              │    operator process         │
└────────────────────────────┘              └─────────────────────────────┘
```

## Quick start

```bash
# 1. Build
cargo build --release -p anchor-surface-host

# 2. Run (host writes its TCP port to anchor_surface_dir/port.txt)
target/release/anchor-surface-host
# Single line on success: "anchor-surface-host listening on 127.0.0.1:<port>"

# 3. Operator client reads port.txt and connects via AnchorSurfaceClient
#    (see operators/claude/src/anchor_surface_client.ts)
```

## Storage

The host owns these files under `$HOME/.myco/anchor_surface/` (Unix)
or `%USERPROFILE%\.myco\anchor_surface\` (Windows):

| File          | Contents                                              | Permissions |
|---------------|-------------------------------------------------------|-------------|
| `owner_key.cb`| Owner Ed25519 signing seed (32 bytes, canonical-bytes)| 0600        |
| `port.txt`    | Resolved TCP port the host is listening on            | 0600        |

On first boot: generates a fresh Ed25519 keypair, persists the seed to
`owner_key.cb`, writes the port. On subsequent boots: loads the seed
from `owner_key.cb` — substrate-ID's pinned owner pubkey stays stable.

## Environment variables

| Variable                              | Purpose                                                              |
|---------------------------------------|----------------------------------------------------------------------|
| `MYCO_ANCHOR_SURFACE_DIR`             | Override storage directory (test/multi-tenant scenarios)             |
| `MYCO_ANCHOR_SURFACE_BIND_ADDR`       | Override bind (default `127.0.0.1:0` — OS picks port)                |
| `MYCO_ANCHOR_SURFACE_OWNER_SEED_HEX`  | **Testing only**: inject a fixed 64-char hex seed instead of load-or-create |

## Protocol

Three message types, all canonical-bytes-encoded over length-prefixed
TCP frames (same shape as the bridge protocol):

- **`ping`** — round-trip health check
- **`get_pubkey`** — returns the 32-byte owner public key (always safe)
- **`sign`** — signs an arbitrary byte payload; returns 64-byte Ed25519 signature

See `protocol.rs` for the exact canonical-bytes shape.

## Hard rules

1. Owner Ed25519 **private key NEVER appears in operator process memory**.
2. The host is a **separate binary**; operator talks over local TCP.
3. The owner key file is `~/.myco/anchor_surface/owner_key.cb` with
   `chmod 0600` on Unix.
4. `OperatorIdentity` on the operator side is a **thin TCP client**.
5. The host process is **single-tenant** — one host per cultivator. Sharing
   a host across cultivators would conflate identities.

## What's deferred (M-anchor-1.5 follow-up)

- **OS-sealing** of `owner_key.cb` (TPM, Secure Enclave, Linux keyring,
  Windows DPAPI). The interim defense layer is `chmod 0600` +
  localhost-only TCP bind.
- **Cross-process authentication** on the local socket (HMAC shared
  secret). Currently relies on filesystem permissions and same-user
  process model.
- **TLS** on the socket. Localhost binding is the current trust boundary.

## Operating the daemon long-running

For production cultivar deployment, the host should run as a
user-scoped daemon (systemd user service on Linux, launchd plist on
macOS, Windows Service on Windows). Sample systemd unit:

```ini
[Unit]
Description=Myco anchor-surface-host
After=network.target

[Service]
ExecStart=%h/.cargo/bin/anchor-surface-host
Restart=on-failure
RestartSec=2

[Install]
WantedBy=default.target
```

Save to `~/.config/systemd/user/myco-anchor-surface.service` and
`systemctl --user enable --now myco-anchor-surface`.

## Doctrine traceability

- L0/cards/AS_anchor_surface.md — anchor surface decomposition; owner
  key custody outside substrate AND operator.
- L1/GOVERNANCE §2.1 — owner private key never enters substrate memory;
  M-anchor-1 extends to: never enters operator memory either.
- L1/HARD_RULES C4 substrate_secret_unsealed (analogue) — operator
  never sees owner seed bytes; only signature bytes return over TCP.
- Phase γ.5 audit finding "operator-IS-anchor honor-system collapse" —
  this binary is the substantive resolution.

## Tests

```bash
cargo test --release -p anchor-surface-host
# Currently 8 tests covering identity load/create, persistence
# round-trip, protocol envelope encode/decode, and signing correctness.
```
