---
type: craft
status: ACTIVE
created: 2026-04-11
target_confidence: 0.85
current_confidence: 0.93
rounds: 2
craft_protocol_version: 1
decision_class: instance_contract
---

# Lint SSoT Craft — collapse dual-write to single source

> **Decision class**: `instance_contract` (floor 0.85)
> **Terminal confidence**: 0.93
> **Rounds**: 2
> **Debate of record for**: Wave 6 — consolidate
> `scripts/lint_knowledge.py` and `src/myco/lint.py` into a single source
> of truth.

## §0 Why a craft at all

The dual-write is not in the kernel contract's strictest ring — no
protocol text is changing, no new lint dimension is being added, no new
canon fields. But it **does** touch two class_z contract files
(`scripts/lint_knowledge.py` and `src/myco/lint.py`, per
`_canon.yaml::upstream_channels.class_z`), so by Upstream Protocol §8.3
it is an `instance_contract` class decision at minimum. Floor 0.85.

## §1 Claim

**C1**: `scripts/lint_knowledge.py` (940 lines) and `src/myco/lint.py`
(869 lines) will be collapsed into a single source of truth. The
authoritative implementation lives in `src/myco/lint.py`.
`scripts/lint_knowledge.py` becomes a ~90-line shim that (a) prepends
`src/` to `sys.path` and (b) delegates to `myco.lint.main` with parsed
arguments.

**C2**: The shim preserves three backwards-compatibility guarantees:
the CLI path (`python scripts/lint_knowledge.py`), the documented flags
(`--project-dir`, `--quick`, `--fix-report`), and the canon class_z
reference.

**C3**: The `synced_contract_version` tag bumps from `v1.5.0` to
`v1.6.0` because this is a contract-level structural change (two
contract files become one authoritative file). No new lint dimension,
no new hunger signal — contract minor.

## §2 Round 1 — 5 attacks

**A1 "Shim still drifts"**: the shim still has a copy of the script
filename, the docstring may go stale, and a future developer might fork
the logic back into the shim. — *Defense*: the shim is 90 lines and
contains **zero lint logic** — it only parses args and delegates. L11
write-surface + class_z review gate prevent re-forking without an
explicit contract bump.

**A2 "Loss of offline invocability"**: the old script was entirely
self-contained — you could copy `scripts/lint_knowledge.py` to any
Myco checkout and run it. The shim requires `src/myco/lint.py` to be
present. — *Defense*: the shim is invoked from **inside** the repo
(the path `scripts/lint_knowledge.py` implies repo presence), and the
shim explicitly prepends `src/` to sys.path so `pip install -e .` is
not required. Outside-repo copy-paste was never a supported use case
(not documented anywhere).

**A3 "Import path fragility"**: if `src/myco/__init__.py` changes or
the package is renamed, the shim breaks silently. — *Defense*:
`src/myco` is in class_z; any rename is already a contract-level action
requiring craft + changelog. The fragility is **desired coupling** —
if myco package is renamed, the shim breaking is correct signal.

**A4 "Historical invocation mismatch"**: the old script uses Chinese
dimension names (`L0 Canon 自检`), the new `src/myco/lint.py` uses
English (`L0 Canon Self-Check`). Users who grep logs for the old names
will have dead links. — *Defense*: cosmetic only. Dimension numbers
(L0-L13) are the machine identifiers. Chinese/English is display text.
log.md historical entries referring to Chinese names are archival and
should not be retroactively rewritten. Future log entries use English.
Accept this drift.

**A5 "L8 .original sync semantics"**: L8 checks `.original.md`
compression markers. Does collapsing the dual-write break L8? —
*Defense*: No. L8 has nothing to do with lint file parity; it checks
`auto-compressed from .original.md` markers in wiki files. Verified by
reading `lint_original_sync` source. Unrelated.

Round 1 end confidence: **0.88** — all 5 attacks deflected without
Claim revision.

## §3 Round 2 — 2 residual attacks

**R2.1 "CI doesn't use editable install"**: some hypothetical CI/CD
setup that runs `python scripts/lint_knowledge.py` without having done
`pip install -e .` will fail because `myco` is not importable. —
*Defense*: the shim prepends `REPO_ROOT / "src"` to `sys.path` **before**
the `from myco.lint import main` line, so the import works whether or
not the package is installed. Verified by running
`python scripts/lint_knowledge.py --project-dir .` in a shell without
any editable install — 14/14 PASS.

**R2.2 "Python version sensitivity"**: `pathlib` behavior and `sys.path`
ordering vary across Python versions. — *Defense*: Myco targets
Python 3.10+ per `pyproject.toml` (inherited from the bootstrap doc).
`Path(__file__).resolve().parent.parent` is stable behavior since 3.6.
`sys.path.insert(0, ...)` is stable since 2.x. No version sensitivity.

Round 2 end confidence: **0.93** — above `instance_contract` floor
0.85 by 0.08. Claim stable. Execute.

## §4 Execution

1. Replace `scripts/lint_knowledge.py` with shim (~90 lines).
2. Update two "Runtime parity with scripts/..." docstrings in
   `src/myco/lint.py::lint_notes_schema` and `::lint_write_surface` to
   say "single source of truth as of v1.6.0".
3. Bump `_canon.yaml::system.contract_version` v1.5.0 → v1.6.0.
4. Bump `src/myco/templates/_canon.yaml::synced_contract_version`
   v1.5.0 → v1.6.0.
5. Append `docs/contract_changelog.md` v1.6.0 entry.
6. Append `log.md` Wave 6 milestone entry.
7. Update `MYCO.md` kernel contract version banner.
8. 14/14 lint dual-path PASS.
9. Single `[contract:minor]` commit.

## §5 Known non-goals

- **No new lint dimension**. L14 is reserved; L15+ will be for Wave 7
  forage hygiene.
- **No behavior change**. Every lint check produces the same issues
  on the same repo state. The only difference is that both CLI
  invocations now share one code path.
- **No templates de-dup**. `_canon.yaml` vs `src/myco/templates/_canon.yaml`
  remain dual-maintained. Templates duplication is a different problem
  (templates are meant to be copies distributed to new instances, the
  `synced_contract_version` mechanism is the chosen solution). Out of
  scope.
- **No removal of `scripts/lint_knowledge.py`**. The file remains
  because class_z canon references it and CLI docs reference it.

## §6 Success criteria

- `python scripts/lint_knowledge.py --project-dir .` → 14/14 PASS
- `python -c "from myco.lint import main; main(Path('.'))"` → 14/14 PASS
- `wc -l scripts/lint_knowledge.py` < 100 (down from 940)
- `grep -c "def lint_" scripts/lint_knowledge.py` == 0 (no lint logic)
- contract_version advanced to v1.6.0 consistently across canon + templates

All six criteria hit before commit.

## §7 Philosophical note

This is a small craft that does a big thing. The substrate spent
Waves 1-5 **adding** structure; Wave 6 is the first wave that **removes**
structure (two copies → one copy, ~850 lines deleted). The
compression-as-intelligence doctrine (v1.5.0 biomimetic_map §4) is
applied to **code itself**, not just documentation. Fungal autolysis on
a dead duplicate.

If Myco cannot compress its own lint implementation, it cannot
credibly claim compression as a core value. Wave 6 closes that
credibility gap.
