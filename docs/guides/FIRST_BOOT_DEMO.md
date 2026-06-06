# First boot demo

> **SUPERSEDED / archival.** This document records the Sprint 7.C first-boot
> (2026-05-19), which ran the **pre-keyless** architecture: a separate
> `anchor-surface-host` process holding an owner Ed25519 key. The v0.9 keyless
> transition **removed the entire anchor surface and the owner key**. The boot
> recorded below no longer reflects how Myco starts. For the current keyless
> procedure, see [`GETTING_STARTED.md`](./GETTING_STARTED.md). The keyless
> first real cultivation is the next milestone (it has not happened yet).

## What it proved (historical)

Before Sprint 7.C, all evidence of substrate functionality came from test suites.
Sprint 7.C ran the actual production binaries against a real filesystem on the
cultivator's host and captured the result: the binaries booted, bound their
ports, and wrote their state files in real OS processes (not just test
harnesses). That conditions-of-possibility result still holds for the substrate
itself.

What is now **obsolete** in that record: the `anchor-surface-host` process,
`MYCO_ANCHOR_SURFACE_OWNER_SEED_HEX`, the owner-key sign step, and the
`owner_keys.cb` state file. None of these exist in the keyless architecture.

## What first boot looks like now (keyless)

The keyless boot has no anchor process and no key step. One runtime starts
everything:

```bash
cd operators/claude && npm start
# spawns myco-substrate (Rust), which spawns python -m myco_kernel_bridge,
# and exposes the MCP surface for Claude.
```

Full procedure: [`GETTING_STARTED.md`](./GETTING_STARTED.md).

## Confirmation procedure (when the cultivator runs the first real session)

After Step 4 of `GETTING_STARTED.md`, verify:

```bash
# 1. Substrate state files exist (keyless: no owner_keys.cb)
ls ~/.myco/substrate/state/
# Expected: dag.cb, snapshot.cb, gradient.cb, substrate_signing_key.cb (some after first cycle)

# 2. DAG contains genesis + early events
#    (MCP tool query_recent_nodes in the Claude conversation)

# 3. Substrate emits no C-row immune events for legitimate ops
#    (MCP tool query_immune_events; expect empty unless a real C-row fires)

# 4. After some normal operation, take a backup
#    (MCP tool export_backup_to_dir, to encrypted external media)
```

## Status

- **Substrate boot (binaries run, state writes)**: proven in vitro on real OS
  processes by the test suite, and once in vivo at Sprint 7.C (pre-keyless).
- **Keyless first boot**: procedure documented in `GETTING_STARTED.md`; a fresh
  keyless in-vivo record will replace this file when the first real cultivation
  begins.
- **First real cultivation** (a human conversing through MCP over a meaningful
  duration, the Cultivar accumulating its life): **pending**. This is the
  threshold Myco now stands at.
