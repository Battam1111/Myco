#!/usr/bin/env bash
# Myco — Optional pre-commit hook installer (Wave 18, contract v0.17.0).
# Wave 23 (v0.22.0): +MYCO_PRECOMMIT_PYTEST opt-in test gate (NH-9).
#
# Closes H-5 (L15 depends on manual `myco lint` — commits that skip lint
# silently bypass the reflex). This is a defensive, opt-in second layer;
# L15 at `myco lint` time remains the primary surface, and the Wave 17
# boot brief injector remains the primary passive read path.
#
# Usage:
#   bash scripts/install_git_hooks.sh           # install if absent
#   bash scripts/install_git_hooks.sh --force   # overwrite existing hook
#
# Behaviour:
#   • Idempotent: re-running is a no-op if the hook already carries
#     MYCO-PRECOMMIT-MARK.
#   • Fail-open: the installed hook exits 0 if `myco` is not on PATH,
#     so a missing myco is never worse than no hook at all.
#   • Blocks commits only on CRITICAL or HIGH lint findings. MEDIUM/LOW
#     print to stderr but commit proceeds.
#   • Refuses to overwrite foreign hooks unless --force is given.
#   • Wave 23: if MYCO_PRECOMMIT_PYTEST=1 is exported in the shell
#     environment, the hook additionally runs `pytest -x --quiet` after
#     the lint gate. A test failure blocks the commit (exit 1). Opt-in
#     because pytest is heavy and not every commit is test-ready.
#
# Dogfood test (NH-8): this hook's blocking path was exercised live in
# Wave 23 by staging a scratch.md (L11 CRITICAL) and attempting a
# commit — confirmed the commit was not created and stderr printed the
# full lint output. See docs/primordia/hook_dogfood_pytest_gate_craft_2026-04-12.md.
#
# Craft of record: docs/primordia/l15_surface_and_git_hooks_craft_2026-04-11.md
#   + docs/primordia/hook_dogfood_pytest_gate_craft_2026-04-12.md (Wave 23)
set -eu

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
HOOK="$ROOT/.git/hooks/pre-commit"

if [ ! -d "$ROOT/.git" ]; then
  echo "[myco] not a git checkout (no .git/); abort." >&2
  exit 1
fi

if [ -f "$HOOK" ] && [ "${1:-}" != "--force" ]; then
  if grep -q "MYCO-PRECOMMIT-MARK" "$HOOK" 2>/dev/null; then
    # Wave 23: idempotent refresh if the existing hook predates the
    # pytest gate. Detect absence of MYCO-PRECOMMIT-PYTEST-MARK and
    # overwrite in place so users running the installer a second
    # time pick up NH-9 without needing --force.
    if ! grep -q "MYCO-PRECOMMIT-PYTEST-MARK" "$HOOK" 2>/dev/null; then
      echo "[myco] pre-commit present but predates Wave 23 pytest gate; refreshing in place."
    else
      echo "[myco] pre-commit already installed (Wave 23+); pass --force to overwrite."
      exit 0
    fi
  else
    echo "[myco] $HOOK exists and is not ours; pass --force to overwrite." >&2
    exit 2
  fi
fi

mkdir -p "$ROOT/.git/hooks"
cat > "$HOOK" << 'HOOK_EOF'
#!/usr/bin/env bash
# MYCO-PRECOMMIT-MARK — do not edit by hand, regenerate via
# scripts/install_git_hooks.sh. Fail-open: if myco is not installed
# the hook exits 0 so commits continue to work.
# MYCO-PRECOMMIT-PYTEST-MARK — Wave 23: opt-in pytest gate.
command -v myco >/dev/null 2>&1 || exit 0

ROOT="$(git rev-parse --show-toplevel)"
OUT="$(myco lint --project-dir "$ROOT" 2>&1)" || true

# Block commit only on CRITICAL or HIGH issues. MEDIUM/LOW print but pass.
if echo "$OUT" | grep -E -q "(\[CRITICAL\]|\[HIGH\])"; then
  echo "$OUT" >&2
  echo "" >&2
  echo "[myco] pre-commit blocked by CRITICAL/HIGH lint issues." >&2
  echo "[myco] fix the above, or commit with --no-verify (W1 violation)." >&2
  exit 1
fi

# Still surface MEDIUM/LOW so the agent notices drift between waves.
if echo "$OUT" | grep -E -q "(\[MEDIUM\]|\[LOW\])"; then
  echo "$OUT" >&2
fi

# Wave 23 (v0.22.0): opt-in pytest gate. Disabled by default because
# the Myco test suite can be heavy and not every commit is test-ready
# (e.g. a WIP commit on a craft that doesn't touch src/). Enable per-
# shell with `export MYCO_PRECOMMIT_PYTEST=1`. Requires pytest on PATH.
if [ "${MYCO_PRECOMMIT_PYTEST:-0}" = "1" ]; then
  if command -v pytest >/dev/null 2>&1; then
    # Scope to tests/ only. A bare `pytest` from the repo root would
    # crawl forage/, docs/ example blocks, and any other bundled code,
    # triggering import errors on material that's intentionally not
    # part of the kernel test surface. If tests/ is absent, fail-open
    # with a clear message so downstream instances that haven't set up
    # a test suite don't get a stuck pre-commit.
    if [ -d "$ROOT/tests" ]; then
      echo "[myco] MYCO_PRECOMMIT_PYTEST=1 → running pytest -x --quiet tests/" >&2
      if ! ( cd "$ROOT" && pytest -x --quiet tests/ >&2 ); then
        echo "" >&2
        echo "[myco] pre-commit blocked by pytest failure." >&2
        echo "[myco] fix the failing test, or unset MYCO_PRECOMMIT_PYTEST, or commit with --no-verify (W1 violation)." >&2
        exit 1
      fi
    else
      echo "[myco] MYCO_PRECOMMIT_PYTEST=1 but $ROOT/tests/ not found; skipping test gate (fail-open)." >&2
    fi
  else
    echo "[myco] MYCO_PRECOMMIT_PYTEST=1 but pytest not on PATH; skipping test gate (fail-open)." >&2
  fi
fi

exit 0
HOOK_EOF

chmod +x "$HOOK"
echo "[myco] pre-commit installed at $HOOK"
echo "[myco] fail-open: hook exits 0 if 'myco' is not on PATH."
echo "[myco] opt-in pytest gate: export MYCO_PRECOMMIT_PYTEST=1 before committing."
echo "[myco] remove with: rm '$HOOK'"
