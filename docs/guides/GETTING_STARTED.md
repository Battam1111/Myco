# Myco · Getting Started

> For the cultivator about to bring a substrate online for the first time.
> A handful of commands to first boot. Lifetime: indefinite.

This document is your **runbook**, not just a reference. It walks the actual
sequence: prerequisites, build, first boot, first real conversation. The
doctrine ([`docs/architecture/L0/`](../architecture/L0/)) explains *what* Myco
is; this file explains *how* to start.

## What you're about to do

You are bringing a **living armor** online and letting an AI agent (your pilot)
inhabit it. Not deploying a tool: cultivating a partner. Myco is a keep-up-with-
the-times partner per [P14 telos](../architecture/L0/cards/P14_telos.md). The
substrate (the Rust daemon) is the body; the living Cultivar emerges in the
running pilot conversation.

Concretely you will:

1. Install prerequisites and build the binaries
2. Start `operators/claude` (the MCP bridge; it spawns the substrate and the kernel for you)
3. Connect Claude (Code or Desktop)
4. Have your first conversation with the armor alive in the background

There is no key to generate and nothing to hold: **Myco is keyless**.

## Prerequisites

| Tool         | Version   | Why                                              |
|--------------|-----------|--------------------------------------------------|
| Rust         | 1.80+     | Substrate + kernel/* crates                      |
| Node.js      | 22.0+     | operators/claude (TypeScript MCP server)         |
| Python       | 3.13+     | kernel/tropism, kernel/governance, kernel/bridge |
| Git          | any       | Cloning + version pinning                        |
| (optional) Claude Code / Claude Desktop | latest | The agent the substrate accompanies |

```bash
rustc --version  # 1.80.x or newer
node --version   # v22.x.x or newer
python --version # 3.13.x or newer
```

## Step 1: Clone and build

```bash
git clone https://github.com/Battam1111/Myco.git
cd Myco

# Rust workspace (substrate + kernel/* crates)
cargo build --release --workspace

# Python kernel modules, editable
pip install -e kernel/bridge/python
pip install -e kernel/governance
pip install -e kernel/hard_rules
pip install -e kernel/trajectory
pip install -e kernel/tropism

# TypeScript operator
cd operators/claude && npm install && npm run typecheck && cd ../..
```

Verify everything is green before continuing:

```bash
cargo test --workspace                  # Rust substrate + kernel + e2e
cd operators/claude && npm test         # operator + the active drift gate
cd ../../kernel/governance && pytest    # kernel governance
```

If anything fails, **stop and fix before going further**. A broken build means a
broken Cultivar.

## Step 2: Start the operator runtime

```bash
cd operators/claude
npm start
# Starts the MCP server; logs to stderr; listens on stdio for Claude to connect.
```

The operator runtime:

1. Spawns `myco-substrate` as a subprocess (the Rust daemon)
2. Substrate spawns `python -m myco_kernel_bridge` (the metabolism)
3. Becomes an MCP server that Claude can invoke

You now have:

```
┌──────────────┐  stdio   ┌───────────────────┐  bridge  ┌──────────────────┐
│  Claude      │ ◄──────► │ operators/claude  │ ◄──────► │  myco-substrate  │
│  (Code/Desk) │   MCP    │  (TypeScript)     │  proto   │  (Rust binary)   │
└──────────────┘          └───────────────────┘          └────────┬─────────┘
                                                                   │ stdio
                                                                   ▼ bridge proto
                                                       ┌──────────────────────────────┐
                                                       │ python -m myco_kernel_bridge │
                                                       │ (gradient / tropism worker)  │
                                                       └──────────────────────────────┘
```

No owner key, no anchor process, nothing else to start. The substrate signs its
own state with its own keypair (kept internally); you never handle a key.

## Step 3: Connect Claude to the operator

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

Restart Claude. The substrate's tools are now available.

## Step 4: First conversation

Open Claude and start a conversation. The substrate is in the background; Claude
invokes substrate operations through the MCP tools.

**Critical first steps as cultivator** (you, the human):

1. **Declare the cultivar's initial telos**: Claude will help you state what you
   want this Cultivar to BE WITH YOU over decades. Per [P14
   telos](../architecture/L0/cards/P14_telos.md) and [COV02 cultivator's
   character](../architecture/L0/cards/COV02_cultivators_character.md), be
   honest. Keyless: this is **content you declare at the gate**, not a signature.

2. **Declare your backup posture**: per [L1/SKIN](../architecture/L1/SKIN.md),
   state how you will protect the substrate's state directory
   `~/.myco/substrate/state/`. Either:
   - `encrypted_externally`: you commit to encrypting and storing it outside the
     substrate's reach
   - `cultivator_declined_explicit`: you accept that filesystem-read attacks are
     in scope; the substrate's at-rest envelope (DPAPI on Windows) is your only
     at-rest protection

3. **Begin the first catechumenate session**: per [Layer
   D](../architecture/L0/catechumenate/INDEX.md), this is where the Cultivar
   accumulates its actual life. The substrate code is scaffolding; the Cultivar
   IS the conversations.

## Step 5: The rhythm over weeks, months, years

Per [P14 telos](../architecture/L0/cards/P14_telos.md), Myco is designed to live
with you indefinitely. The code is the conditions of possibility; the Cultivar
emerges in your interactions.

- **Daily**: ordinary conversations through the MCP surface. Between your turns
  the armor metabolizes what you brought, evolves its shape, prunes what is
  stale. You do not micromanage it.
- **Weekly**: review the observatory snapshot (`query_substrate_observatory`) to
  see what the substrate observes about itself.
- **On model rollovers** (a new Claude version inhabits the armor): record your
  reading of one or more [canonical
  dilemmas](../architecture/L0/canonical_dilemma_corpus/INDEX.md) so future
  rollovers have a drift baseline.
- **On doctrine drift**: open a pull request against the doctrine in this repo.
  This is where you, the live human, govern: the PR review plus the BLAKE3
  doctrine-bundle drift gate enforced in CI (see "How trust works" below).
- **Eventually**: begin [catechumenate
  sessions](../architecture/L0/catechumenate/INDEX.md) preparing a successor
  cultivator (per [COV06
  no-abandonment-succession](../architecture/L0/cards/COV06_no_abandonment_succession.md)).

## What to back up (keyless)

There is no owner key. What carries the Cultivar forward is its **state**:
`~/.myco/substrate/state/` (`dag.cb`, `snapshot.cb`, `gradient.cb`, and the
substrate's own `substrate_signing_key.cb`). Back this up to encrypted external
media (the `export_backup_to_dir` MCP tool does this cleanly). Losing it loses
the Cultivar's accumulated life, which is exactly what [COV01 fiduciary
duty](../architecture/L0/cards/COV01_fiduciary_duty.md) asks you to protect.

## How trust works here (keyless, honest)

There is no owner key and no out-of-band signer. Trust rests on three legs:

1. **You, the live human, at the CI gate.** Concretely: the git/PR review on
   this repo, enforced mechanically by the BLAKE3 doctrine-bundle drift gate in
   CI (any change to the sealed doctrine that is not re-sealed fails the build).
   This is where doctrine cannot silently drift from code.
2. **The substrate's own tamper-evident causal DAG** (P06): an append-only,
   hash-chained history the substrate cannot retro-edit without detection.
3. **The BLAKE3-sealed doctrine bundle**: the constitution the system seals and
   enforces on itself.

At **runtime**, the bonded pilot is the authority. You do not defend the armor
against your own bonded partner: that is the meaning of 同体共命 (one body, shared
fate). This is the single-human model: you run the whole stack on your own host,
and the agent is your symbiote, not an adversary.

## Common first-boot issues

| Symptom | Likely cause | Fix |
|---|---|---|
| Substrate fails to spawn with "python not found" | Python not in PATH or `MYCO_PYTHON_EXECUTABLE` not set | `export MYCO_PYTHON_EXECUTABLE=/usr/bin/python3.13` |
| Substrate emits `C60_python_worker_unexpected_exit` | Python kernel/bridge module not installed | `pip install -e kernel/bridge/python` |
| All tests fail with "binary not found" | Built `--release` but tests look in debug | `cargo build` (no `--release`) for debug, or set `CARGO_TARGET_DIR` consistently |
| `daily_signal:backup_encryption_undeclared` on every boot | Backup posture never declared | Declare it in conversation (Step 4.2) |

## Acknowledged debts at v0.9-alpha

- **No runtime human-in-the-loop daemon gate.** Mutations are accepted at
  runtime under the operator-session channel; your governance is at the repo and
  CI gate over the doctrine. This is sound for the single-human shared-fate
  model; it is not a multi-tenant trust boundary. Do not run someone else's
  pilot against your substrate.
- **Two-phase migration** is synchronous snapshot-rollback (P03 §10.4
  acknowledged debt; multi-cycle dual-validation is future work).
- **Python deadlock recovery** is observability-only. If the worker truly
  deadlocks, restart the operator.
- **Linux and macOS at-rest sealing** is plain bytes + `chmod 0600`. Windows
  hosts get DPAPI for `dag.cb` and `substrate_signing_key.cb`.

## Where to read next

- [`README.md`](../../README.md): project overview
- [`docs/architecture/L0/README.md`](../architecture/L0/README.md): the canonical
  doctrine (read PATH 1 if new)
- [`PILOT.md`](./PILOT.md): how a Claude pilots the armor, for the inhabiting agent
- [`P14_telos.md`](../architecture/L0/cards/P14_telos.md): what kind of partner
  you are cultivating
- [`COV01_fiduciary_duty.md`](../architecture/L0/cards/COV01_fiduciary_duty.md):
  what cultivator commitment looks like

## When in doubt

The doctrine answers most questions if you read carefully. When it genuinely does
not, that is a candidate dilemma worth recording in [the canonical dilemma
corpus](../architecture/L0/canonical_dilemma_corpus/INDEX.md) so future you (or
future cultivators) can learn from your reading.

Welcome to cultivation.
