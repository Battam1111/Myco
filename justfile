# Myco — local build + test orchestration.
#
# A single entry point mirroring .github/workflows/ci.yml and the
# GETTING_STARTED runbook, so "build everything / test everything" is one
# command instead of four hand-run toolchains.
#
# Requires `just` (https://just.systems). Recipes assume an sh-compatible
# shell (git-bash / WSL / macOS / Linux). Run `just` with no args to list.

default:
    @just --list

# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

# Rust workspace (substrate + kernel/* crates).
build-rust:
    cargo build --workspace

# Python kernel packages, editable, in dependency order.
build-python:
    pip install -e kernel/governance -e kernel/tropism -e kernel/trajectory -e kernel/hard_rules -e kernel/bridge/python

# TypeScript package (the operator).
build-ts:
    cd operators/claude && npm install

# Everything.
build-all: build-rust build-python build-ts

# ---------------------------------------------------------------------------
# Test
# ---------------------------------------------------------------------------

# Rust: substrate + kernel unit + e2e + Layer-C witnesses.
test-rust:
    cargo test --workspace

# Python: all five kernel packages.
test-python:
    python -m pytest kernel/governance kernel/tropism kernel/trajectory kernel/hard_rules kernel/bridge/python

# TypeScript: operator (typecheck + tests, incl. the active ceremony
# verify_hashes drift gate). The operator e2e spawns the
# real substrate + Python bridge, so build those first.
test-ts: build-rust build-python
    cd operators/claude && npm run test:all

# Everything (matches CI).
test-all: test-rust test-python test-ts

# ---------------------------------------------------------------------------
# Ceremony
# ---------------------------------------------------------------------------

# Verify the active L0 doctrine seal still reproduces from the bundle
# (the drift gate; fails if any L0 file changed without re-sealing).
ceremony-verify:
    cd operators/claude && node --experimental-strip-types --no-warnings --test ceremonies/v3_1_5_keyless_anchor_retirement/verify_hashes.test.ts
