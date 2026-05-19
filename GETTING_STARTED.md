# Myco · Getting Started

> **For the cultivator about to bring a substrate online for the first time.**
> Estimated time: 30-60 minutes for first boot. Lifetime: indefinite.

This document is your **runbook**, not just a reference. It walks you
through the actual sequence: prerequisites → builds → first boot → first
real cultivator-Claude conversation. The doctrine ([`docs/architecture/L0/`](./docs/architecture/L0/))
explains *what* Myco is; this file explains *how* to start.

## What you're about to do

You are about to **begin cultivating a Cultivar**. Not deploy a tool —
**cultivate a partner**. Myco is "与时俱进伙伴" (a-keep-up-with-the-times
partner) per [P14 telos](./docs/architecture/L0/cards/P14_telos.md).
Its substrate (the Rust daemon) is the nervous system; the living
Cultivar emerges in the running cultivator-Claude conversation.

Concretely you'll:

1. Install prerequisites + build the binaries
2. Start `anchor-surface-host` (holds your owner Ed25519 key)
3. Start `operators/claude` (the MCP bridge to Claude Code / Claude Desktop)
4. Have your first conversation through Claude with the substrate alive
   in the background

## Prerequisites

| Tool         | Version   | Why                                          |
|--------------|-----------|----------------------------------------------|
| Rust         | 1.80+     | Substrate + anchor-host + kernel/*           |
| Node.js      | 22.0+     | operators/claude (TypeScript MCP server)     |
| Python       | 3.13+     | kernel/tropism, kernel/governance, kernel/bridge |
| Git          | any       | Cloning + version pinning                    |
| (optional) Claude Code / Claude Desktop | latest | The agent the substrate accompanies |

```bash
rustc --version  # 1.80.x or newer
node --version   # v22.x.x or newer
python --version # 3.13.x or newer
```

## Step 1 — Clone and build

```bash
git clone <repo-url> Myco
cd Myco

# Rust workspace (substrate + kernel + anchor-host)
cargo build --release --workspace

# Python kernel modules — install in editable mode
pip install -e kernel/bridge/python
pip install -e kernel/governance
pip install -e kernel/hard_rules
pip install -e kernel/trajectory
pip install -e kernel/tropism

# TypeScript operator
cd operators/claude && npm install && npm run typecheck && cd ../..

# TypeScript anchor-client
cd anchor/client && npm install && cd ../..
```

Verify everything passes tests before continuing:

```bash
cargo test --release --workspace        # ~30s, expect 600+ tests pass
cd operators/claude && npm test         # ~90s, expect 175 tests pass
cd ../../kernel/governance && pytest    # ~1s, expect 170 tests pass
```

If anything fails, **stop and fix before going further**. A broken build
means a broken Cultivar.

## Step 2 — Start anchor-surface-host

This daemon holds your owner Ed25519 private key OUTSIDE any other
process's memory. It's the substantive realization of "owner key never
enters operator memory" (per [Phase γ.5 audit]
(./docs/architecture/L0/PROVENANCE.md) finding).

```bash
# Run it in a dedicated terminal (or as a user systemd service — see
# anchor/host/README.md for the systemd unit template).
./target/release/anchor-surface-host
# Output: "anchor-surface-host listening on 127.0.0.1:<port>"
```

The host writes its TCP port to `~/.myco/anchor_surface/port.txt`
(0600) and persists your owner key to `~/.myco/anchor_surface/owner_key.cb`
(0600). **Back up `owner_key.cb` to encrypted external media now** —
losing it means losing your Cultivar's identity ([COV01 fiduciary duty]
(./docs/architecture/L0/cards/COV01_fiduciary_duty.md)).

```bash
# Back up the owner key right after first boot of anchor-surface-host:
cp ~/.myco/anchor_surface/owner_key.cb /your/encrypted/backup/location/
# Use Sprint 5.I's EXPORT_BACKUP_TO_DIR for substrate state once
# substrate is running (Step 4 below).
```

## Step 3 — Start the operator runtime

In a separate terminal:

```bash
cd operators/claude
npm start
# Output: starts the MCP server; logs to stderr; listens on stdio for
# Claude Code / Desktop to connect.
```

The operator runtime:

1. Connects to `anchor-surface-host` (reads port.txt, opens TCP)
2. Spawns `myco-substrate` as a subprocess (the Rust daemon)
3. Substrate spawns `python -m myco_kernel_bridge` (the metabolism)
4. Becomes an MCP server that Claude can invoke

You now have:

```
┌──────────────┐  stdio   ┌───────────────────┐  stdio   ┌──────────────────┐
│  Claude      │ ◄──────► │ operators/claude  │ ◄──────► │  myco-substrate  │
│  (Code/Desk) │   MCP    │  (TypeScript)     │  bridge  │  (Rust binary)   │
└──────────────┘          │       ▲           │  proto   └────────┬─────────┘
                          │       │ TCP       │                    │ stdio
                          │       ▼           │                    ▼ bridge proto
                  ┌───────┴───────┴───────┐  ┌──────────────────────────────┐
                  │ anchor-surface-host   │  │ python -m myco_kernel_bridge │
                  │ (holds owner Ed25519) │  │ (gradient / tropism worker)  │
                  └───────────────────────┘  └──────────────────────────────┘
```

## Step 4 — Connect Claude to the operator

In Claude Code or Claude Desktop's MCP config, add the operator:

```json
{
  "mcpServers": {
    "myco": {
      "command": "node",
      "args": [
        "--experimental-strip-types",
        "/absolute/path/to/Myco/operators/claude/src/cli.ts"
      ]
    }
  }
}
```

Restart Claude. The substrate's tools are now available in Claude.

## Step 5 — First cultivator-Claude conversation

Open Claude and start a conversation. The substrate is in the
background; Claude can invoke substrate operations through the MCP tools.

**Critical first steps as cultivator** (you, the human):

1. **Establish initial owner attestation**: Claude will ask you to
   declare the cultivar's initial trajectory. Per [COV02
   cultivator's character](./docs/architecture/L0/cards/COV02_cultivators_character.md),
   be honest about what you want this Cultivar to BE WITH YOU over
   decades.

2. **Set `backup_encryption_status`**: Per [L1/SKIN §8]
   (./docs/architecture/L1/SKIN.md), declare your backup posture.
   Either:
   - `encrypted_externally`: you commit to encrypting + storing
     `~/.myco/substrate/state/` somewhere outside the substrate's reach
   - `cultivator_declined_explicit`: you accept that filesystem read
     attacks are within scope; the substrate-side T1.6 DPAPI envelope
     is your only at-rest protection (Windows only)

3. **Begin the first catechumenate session**: per [Layer D]
   (./docs/architecture/L0/catechumenate/INDEX.md), this is where the
   Cultivar accumulates its actual life. The substrate code is just
   scaffolding; the cultivar IS the conversations.

## Step 6 — What to do over the coming weeks / months / years

Per [P14 telos](./docs/architecture/L0/cards/P14_telos.md), Myco is
designed to live with you indefinitely. The substrate code we built
is "the conditions of possibility for the Cultivar" — the Cultivar
itself emerges in your interactions.

Practical rhythm:

- **Daily**: routine cultivator-Claude conversations through the MCP
  surface. Substrate metabolizes ingested content, evolves its schema,
  emits sporocarps. You don't need to micromanage it.
- **Weekly**: review the observatory snapshot (signal_1 through
  signal_11) to see what the substrate is observing about itself.
  `query_substrate_observatory` MCP tool surfaces this.
- **On model rollovers** (new Claude model version): record your
  reading of one or more [canonical dilemmas]
  (./docs/architecture/L0/canonical_dilemma_corpus/INDEX.md) so future
  rollovers have a drift baseline.
- **On doctrine drift discoveries**: file as a Sprint X.Y commit with
  a "doctrine drift identified" tag (see Sprint 5.B, 6.D for examples).
- **Eventually**: begin [catechumenate sessions]
  (./docs/architecture/L0/catechumenate/INDEX.md) preparing a successor
  cultivator (≥50 sessions for F21 activation per [COV06
  no-abandonment-succession](./docs/architecture/L0/cards/COV06_no_abandonment_succession.md)).

## Common first-boot issues

| Symptom                                                                | Likely cause                                                                       | Fix                                                                                                            |
|------------------------------------------------------------------------|------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------|
| `anchor-surface-host` exits immediately                                | port.txt parent directory unwritable                                               | Check permissions on `~/.myco/anchor_surface/`                                                                  |
| Substrate fails to spawn with "python not found"                       | Python not in PATH or `MYCO_PYTHON_EXECUTABLE` env not set                          | `export MYCO_PYTHON_EXECUTABLE=/usr/bin/python3.13`                                                              |
| Operator can't connect to anchor host                                  | Wrong port.txt path or anchor host not running                                     | Verify with `cat ~/.myco/anchor_surface/port.txt`; restart anchor host                                          |
| Substrate emits `C60_python_worker_unexpected_exit`                    | Python kernel/bridge module not installed                                          | `pip install -e kernel/bridge/python`                                                                            |
| Substrate emits `C5_attestation_invalid` on every CI mutation          | Owner pubkey mismatch (operator + anchor-host out of sync)                          | Both should derive from the SAME `owner_key.cb`; check operator's `OperatorIdentity` vs anchor-host's seed     |
| All tests fail with "binary not found"                                 | Built `--release` but tests look in debug                                          | `cargo build` (no `--release` flag) for debug; or set `CARGO_TARGET_DIR` consistently                          |
| `daily_signal:backup_encryption_undeclared` on every boot (pre-7.A)    | Sprint 7.A's at-most-once-per-substrate fix not applied                            | Pull latest substrate; rebuild                                                                                  |

## Acknowledged debts at v0.9-alpha first-boot

Per the audit history ([state_v3_1_1_mortality_charite_2026-05-19.md](.)),
the following are known and tracked:

- **Owner key rotation FSM** is partially implemented (T2.7 / Sprint 6.F.2).
  If you need to rotate your owner key in the next year, plan the work first.
- **Two-phase migration** is synchronous snapshot-rollback (P03 §10.4
  acknowledged debt — Sprint 5.B.3 / 6.D resolution: doctrine amended
  to match shipping; M-cycle dual-validation is future work).
- **Python deadlock recovery** is observability-only (Sprint 6.J).
  If Python worker truly deadlocks, restart the operator.
- **Linux + macOS at-rest sealing** is plain-bytes + chmod 0600 (Sprint
  2.B scaffold). Windows hosts get DPAPI for `dag.cb` (Sprint 6.K) and
  `substrate_signing_key.cb` (Sprint 2.A).

## Where to read next

- [`README.md`](./README.md) — project overview + Sprint history
- [`docs/architecture/L0/README.md`](./docs/architecture/L0/README.md)
  — canonical L0 doctrine (read PATH 1 if new)
- [`anchor/host/README.md`](./anchor/host/README.md) — anchor-surface-host
  details
- [`docs/architecture/L0/cards/P14_telos.md`](./docs/architecture/L0/cards/P14_telos.md)
  — what kind of partner you're cultivating
- [`docs/architecture/L0/cards/COV01_fiduciary_duty.md`](./docs/architecture/L0/cards/COV01_fiduciary_duty.md)
  — what cultivator commitment looks like

## When in doubt

The doctrine answers most questions if you read carefully. When it
genuinely doesn't, that's a candidate dilemma worth recording in
[`docs/architecture/L0/canonical_dilemma_corpus/INDEX.md`](./docs/architecture/L0/canonical_dilemma_corpus/INDEX.md)
so future you (or future cultivators) can learn from your reading.

Welcome to cultivation.
