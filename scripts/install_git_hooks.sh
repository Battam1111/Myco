#!/usr/bin/env bash
# Myco — Optional pre-commit hook installer (Wave 18, contract v0.17.0).
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
#
# Craft of record: docs/primordia/l15_surface_and_git_hooks_craft_2026-04-11.md
set -eu

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
HOOK="$ROOT/.git/hooks/pre-commit"

if [ ! -d "$ROOT/.git" ]; then
  echo "[myco] not a git checkout (no .git/); abort." >&2
  exit 1
fi

if [ -f "$HOOK" ] && [ "${1:-}" != "--force" ]; then
  if grep -q "MYCO-PRECOMMIT-MARK" "$HOOK" 2>/dev/null; then
    echo "[myco] pre-commit already installed; pass --force to overwrite."
    exit 0
  fi
  echo "[myco] $HOOK exists and is not ours; pass --force to overwrite." >&2
  exit 2
fi

mkdir -p "$ROOT/.git/hooks"
cat > "$HOOK" << 'HOOK_EOF'
#!/usr/bin/env bash
# MYCO-PRECOMMIT-MARK — do not edit by hand, regenerate via
# scripts/install_git_hooks.sh. Fail-open: if myco is not installed
# the hook exits 0 so commits continue to work.
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

exit 0
HOOK_EOF

chmod +x "$HOOK"
echo "[myco] pre-commit installed at $HOOK"
echo "[myco] fail-open: hook exits 0 if 'myco' is not on PATH."
echo "[myco] remove with: rm '$HOOK'"
