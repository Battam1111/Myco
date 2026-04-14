#!/usr/bin/env bash
# Myco — Optional pre-commit hook installer (Wave 18, contract v0.17.0).
# Wave 23 (v0.22.0): +MYCO_PRECOMMIT_PYTEST opt-in test gate (NH-9).
#
# Closes H-5 (L15 depends on manual `myco immune` — commits that skip lint
# silently bypass the reflex). This is a defensive, opt-in second layer;
# L15 at `myco immune` time remains the primary surface, and the Wave 17
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
    # Wave 25: same mechanism for the canon-driven test_dir change —
    # detect absence of MYCO-PRECOMMIT-CANON-MARK and refresh.
    if ! grep -q "MYCO-PRECOMMIT-PYTEST-MARK" "$HOOK" 2>/dev/null; then
      echo "[myco] pre-commit present but predates Wave 23 pytest gate; refreshing in place."
    elif ! grep -q "MYCO-PRECOMMIT-CANON-MARK" "$HOOK" 2>/dev/null; then
      echo "[myco] pre-commit present but predates Wave 25 canon-driven test_dir; refreshing in place."
    else
      echo "[myco] pre-commit already installed (Wave 25+); pass --force to overwrite."
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
# MYCO-PRECOMMIT-CANON-MARK  — Wave 25: test_dir resolved from canon.
command -v myco >/dev/null 2>&1 || exit 0

ROOT="$(git rev-parse --show-toplevel)"
OUT="$(myco immune --project-dir "$ROOT" 2>&1)" || true

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
#
# Wave 25 (v0.24.0): test_dir now reads from
# _canon.yaml::system.tests.test_dir via inline Python (PyYAML is
# already a Myco runtime dep). Falls back to hardcoded "tests/" on any
# read error so downstream instances without the new canon section
# still work. Single-source-of-truth discipline per
# docs/primordia/hermes_absorption_craft_2026-04-12.md §4.2 step 9.
if [ "${MYCO_PRECOMMIT_PYTEST:-0}" = "1" ]; then
  if command -v pytest >/dev/null 2>&1; then
    # Resolve test_dir from canon (fail-open to "tests" on any error).
    TEST_DIR=$(python -c "
import sys
try:
    import yaml
    with open('$ROOT/_canon.yaml', encoding='utf-8') as f:
        c = yaml.safe_load(f) or {}
    td = (c.get('system') or {}).get('tests', {}).get('test_dir') or 'tests/'
    print(td.rstrip('/'))
except Exception:
    print('tests')
" 2>/dev/null || echo "tests")
    if [ -z "$TEST_DIR" ]; then
      TEST_DIR="tests"
    fi

    # Scope to the canon-declared test_dir. A bare `pytest` from the
    # repo root would crawl forage/, docs/ example blocks, and any
    # other bundled code, triggering import errors on material that's
    # intentionally not part of the kernel test surface. If test_dir
    # is absent, fail-open with a clear message so downstream instances
    # that haven't set up a test suite don't get a stuck pre-commit.
    if [ -d "$ROOT/$TEST_DIR" ]; then
      echo "[myco] MYCO_PRECOMMIT_PYTEST=1 → running pytest -x --quiet $TEST_DIR/" >&2
      if ! ( cd "$ROOT" && pytest -x --quiet "$TEST_DIR" >&2 ); then
        echo "" >&2
        echo "[myco] pre-commit blocked by pytest failure." >&2
        echo "[myco] fix the failing test, or unset MYCO_PRECOMMIT_PYTEST, or commit with --no-verify (W1 violation)." >&2
        exit 1
      fi
    else
      echo "[myco] MYCO_PRECOMMIT_PYTEST=1 but $ROOT/$TEST_DIR/ not found; skipping test gate (fail-open)." >&2
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
