# Stage B.1 Core — Implementation Craft

> **Status**: DRAFT 2026-04-15, awaiting execution.
> **Depth**: three rounds — B.1 has real tensions (context shape, canon
> strictness, severity representation, substrate discovery semantics).
> **Governing docs**:
> - `docs/architecture/L0_VISION.md`
> - `docs/architecture/L1_CONTRACT/protocol.md`
> - `docs/architecture/L1_CONTRACT/versioning.md`
> - `docs/architecture/L1_CONTRACT/exit_codes.md`
> - `docs/architecture/L1_CONTRACT/canon_schema.md`
> - `docs/architecture/L3_IMPLEMENTATION/package_map.md`
> - `docs/architecture/L3_IMPLEMENTATION/command_manifest.md`

---

## Intent

Land `myco.core` — the L1 primitives shared by every subsystem. No
business logic, no I/O beyond canon-read. Every module below is small
and self-contained.

Scope (per `package_map.md`):

- `errors` — exception hierarchy + exit-code classifier (rank ≥ 3).
- `severity` — four-level `Severity` + ordering + downgrade primitive.
- `paths` — canonical paths within a substrate root.
- `substrate` — substrate-root discovery (walk-up from cwd).
- `canon` — load + validate `_canon.yaml` against L1 schema.
- `version` — SemVer + contract-version parse + compare.
- `context` — the `MycoContext` passed into every handler (new module,
  see Round 1.5 below; was implicit in L3 manifest doc).

Out of scope (explicitly deferred): exit-policy grammar evaluation
(Stage B.2 — belongs with the immune kernel that actually produces
findings), actual lint dimensions (B.2 + B.8), any command handler.

---

## Round 1 — 主张 (initial claim)

### Proposed module surface

```
src/myco/core/
├── __init__.py              re-exports the stable public surface
├── errors.py                MycoError hierarchy; exit_code_for()
├── severity.py              Severity enum + downgrade()
├── paths.py                 SubstratePaths dataclass
├── substrate.py             find_substrate_root(), Substrate dataclass
├── canon.py                 load_canon(), CanonSchemaError
├── version.py               parse_semver(), compare_contract_versions()
└── context.py               MycoContext dataclass
```

### Key types (first pass)

```python
# severity.py
class Severity(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

# errors.py
class MycoError(Exception):          # exit 3
    exit_code = 3
class ContractError(MycoError):      # exit 3 per exit_codes.md
    pass
class SubstrateNotFound(MycoError):  # exit 3
    pass
class CanonSchemaError(ContractError):
    pass

# substrate.py
@dataclass(frozen=True)
class Substrate:
    root: Path
    canon: Canon         # parsed canon
    paths: SubstratePaths

# context.py
@dataclass(frozen=True)
class MycoContext:
    substrate: Substrate
    now: datetime        # injected for determinism in tests
    stdout, stderr: TextIO
```

### Canon validation strategy

Strict, but with one affordance: **missing fields that have a schema
default are filled in** (e.g. `schema_version` defaults to `"1"` if
absent on a fresh genesis canon — genesis itself writes it, but we
accept the absence on read too). Unknown fields at known levels are a
WARNING, not an error (agents may extend). Unknown `schema_version` is
a fatal `ContractError` per canon_schema.md rule 4.

### Substrate discovery

`find_substrate_root(start: Path) -> Path` walks from `start` upward
looking for a directory that contains `_canon.yaml`. First hit wins.
If none found by filesystem root, raise `SubstrateNotFound`. During
Stage B tests this is bypassed via `Substrate.from_root(tmp_path)`.

---

## Round 1.5 — 自我反驳 (attack the claim)

**R1.5-A. Does `MycoContext` belong in core or surface?**
Claim puts it in core. But `MycoContext` is the handler-facing
construct (per command_manifest.md: `def run(args, *, ctx) -> Result`).
Surface imports core, not vice versa. If ctx lives in core, who
*constructs* it? A context builder would want to live near CLI main.
→ **Resolution**: ctx *type* lives in core (every subsystem imports
it); ctx *builder* lives in surface. Handlers receive it, never build
it. This matches the dependency direction and is cleanly testable.

**R1.5-B. Severity IntEnum vs. dataclass.**
IntEnum allows `severity >= Severity.HIGH` to "just work", but it also
lets `3 + severity.HIGH == 6` which is meaningless. A plain Enum with
a `rank` property is safer but forces `a.rank >= b.rank` at every
comparison.
→ **Resolution**: keep IntEnum but add `__add__ = None`-style guards
is overkill. Accept the int arithmetic affordance; the comparisons are
what matter, and tests cover the ordering.

**R1.5-C. Canon warnings — where do they surface?**
Claim says unknown fields emit WARNING. But B.1 has no warning bus yet
(the immune kernel lands in B.2). Returning warnings alongside the
parsed canon mixes concerns.
→ **Resolution**: `load_canon()` returns `Canon` only; strict-mode and
warning collection land in B.2 as part of the mechanical lint
category. In B.1, unknown top-level fields are silently preserved as
`Canon.extras: dict`; unknown fields at known typed levels are
dropped with no complaint. The immune kernel will pick them up later.

**R1.5-D. Substrate walk-up — false positives?**
If a parent directory unrelated to Myco happens to contain
`_canon.yaml` (e.g. a symbiont's parent), walk-up finds the wrong
substrate.
→ **Resolution**: match on *presence of valid canon*, not just
filename. `find_substrate_root()` tries to parse `_canon.yaml` at each
candidate; only a canon that parses and whose `schema_version` is
known counts as a match. Corrupt canons propagate as `ContractError`
(user sees a clear message).

**R1.5-E. `version.py` scope creep.**
Parsing SemVer is easy but opinionated: PEP 440 (`0.4.0.dev`) vs. pure
SemVer (`0.4.0-dev`). Package version today is `0.4.0.dev` (PEP 440)
and contract version is `v0.4.0-alpha.1` (SemVer-ish prefix). Two
different grammars.
→ **Resolution**: core/version.py exposes two parsers: `PackageVersion`
for PEP 440 (delegates to `packaging.version.Version` — add
`packaging` as a runtime dep? No — re-implement the subset we need to
avoid adding a dep) and `ContractVersion` for the `vMAJOR.MINOR.PATCH
[-pre]` form. Keep both minimal; don't try to be a SemVer library.
Tests cover the exact cases we use.

**R1.5-F. Handler return shape — `Result` is undefined.**
The manifest doc says handlers return `Result`. Where does `Result`
live? It's cross-subsystem, so core/. But it's also a surface concern
(how to render output). Split or unified?
→ **Resolution**: `Result` is a tiny dataclass in `core.context` (same
module as `MycoContext`) with `exit_code: int`, `findings: list`,
`payload: dict`. Rendering happens in surface. This keeps handlers
pure.

---

## Round 2 — 修正 (revised claim)

### Updated module surface

```
src/myco/core/
├── __init__.py              re-exports Severity, MycoError family,
│                            Substrate, Canon, MycoContext, Result
├── errors.py                MycoError hierarchy (no exit_code_for;
│                            each exception carries .exit_code)
├── severity.py              class Severity(IntEnum); downgrade()
├── paths.py                 SubstratePaths (pure functions of root)
├── substrate.py             find_substrate_root(); Substrate dataclass
├── canon.py                 Canon dataclass + load_canon();
│                            preserves unknown top-level keys in .extras
├── version.py               PackageVersion, ContractVersion (parse + cmp)
└── context.py               MycoContext, Result
```

### Revised validation contract

- `load_canon(path)` returns `Canon` or raises `ContractError`.
- Known top-level keys are parsed into typed slots.
- Unknown top-level keys land in `Canon.extras: dict[str, Any]`.
- Unknown nested keys at known sections are dropped silently in B.1;
  the immune kernel (B.2) will re-scan the raw YAML for "unknown key
  at known section" as a `mechanical:HIGH` finding.
- Unknown `schema_version` → `ContractError`, exit 3.
- Missing required top-level keys (`schema_version`, `contract_version`,
  `identity`, `system`, `subsystems`) → `ContractError`, exit 3.

### Revised severity + errors

- `Severity` is `IntEnum` with values 1/2/3/4.
- `Severity.downgrade(from_, to)` is a static helper used by the
  skeleton-mode downgrade (B.2 consumes it).
- `MycoError.exit_code` defaults to 3. Subclasses override:
  `ContractError.exit_code = 3`, `SubstrateNotFound.exit_code = 3`,
  `UsageError.exit_code = 3`. No subclass uses 1 or 2 — those are
  reserved for finding-driven exits computed by the exit-policy layer
  (B.2), not raised.

### Version module — minimal re-impl

- `PackageVersion`: parses `MAJOR.MINOR.PATCH[.devN]`. No epoch, no
  local, no rc. If future needs expand, we'll widen then.
- `ContractVersion`: parses `v?MAJOR.MINOR.PATCH[-<tag>]`. Leading `v`
  optional on read, normalized off. Tag is a free-form string compared
  lexicographically (`alpha.1 < alpha.2 < beta.1` happens to work; if
  it ever doesn't, we add a cmp override).
- No `packaging` dep. All parse logic is `re.fullmatch` + tuple cmp.

### Context + Result

```python
# context.py
@dataclass(frozen=True)
class MycoContext:
    substrate: Substrate
    now: datetime
    env: Mapping[str, str]    # env vars snapshot, for deterministic tests

@dataclass(frozen=True)
class Result:
    exit_code: int
    findings: tuple[Finding, ...] = ()     # Finding imported later (B.2)
    payload: Mapping[str, Any] = field(default_factory=dict)
```

`Finding` is forward-declared as `TYPE_CHECKING`-only in B.1 — the
concrete class lands in B.2. `Result.findings` default is empty, so
B.1 tests don't need it.

---

## Round 2.5 — 再驳 (attack the revision)

**R2.5-A. Forward-declared `Finding` is an import-time landmine.**
If `Result.findings` is typed as `tuple[Finding, ...]` but `Finding`
only exists under `TYPE_CHECKING`, the runtime class has no clue what
to validate. It works until the first time someone uses
`isinstance(r.findings[0], Finding)` inside core.
→ **Response**: the simpler fix is to type `findings` as
`tuple[Any, ...]` in B.1 and tighten the type when B.2 lands `Finding`.
Runtime is unchanged; type checking is loose until B.2. Accept the
looseness; it's one line to upgrade. **Applied.**

**R2.5-B. `env: Mapping[str, str]` on context — YAGNI?**
No handler in the planned inventory reads env. Why carry it?
→ **Response**: `myco hunger` needs `CLAUDE_PROJECT_DIR` to disambiguate
substrate roots under nested mounts (pre-rewrite behavior we carry
forward per Chesterton's-fence reasoning). Cheaper to plumb env now
than to retrofit context shape at B.4.
→ **Resolution**: keep env in context.

**R2.5-C. `find_substrate_root` parsing every `_canon.yaml` it passes
is expensive.**
Walk-up could touch many `_canon.yaml` files in large-monorepo setups.
Parsing each one is wasteful.
→ **Response**: in practice walk-up terminates at the first hit (we
want the innermost substrate anyway). The parse is ~300 lines of YAML
max, sub-millisecond. Don't optimize pre-emptively.

**R2.5-D. PackageVersion without `packaging` — parity risk.**
`pip` uses `packaging.version` to compare versions. If our parser
disagrees with pip's (e.g. on `0.4.0.dev` vs `0.4.0.dev0`), CI will
silently diverge.
→ **Response**: we only *compare* package versions inside Myco (lint
dim "version monotonicity"); pip does its own comparison for install.
As long as Myco's comparisons are internally consistent, parity with
pip isn't required. Document this explicitly in version.py docstring
and accept the limited scope.

**R2.5-E. Round 1.5-A claimed ctx-builder in surface, but Stage B.1
ships no surface code.**
Surface lands in B.7. How do B.2–B.6 tests construct a `MycoContext`?
→ **Response**: B.1 provides `MycoContext.for_testing(root=...)`
classmethod that constructs a minimal context from a substrate root
using `datetime.now()` and `os.environ`. This is a test helper, not a
production builder. The production builder lands in B.7.
→ **Applied.**

---

## Round 3 — 反思 (reflection)

**What the debate revealed.**

1. The context/result types are a cross-cutting concern that naturally
   lives in core — but the *builder* belongs at the seam where the
   real world meets the pure logic (surface). Pulling `for_testing`
   out as a classmethod keeps that seam honest.

2. The canon parser is split in two: strict-parse (B.1, raises on
   structural breaks) and lint-scan (B.2, complains about soft
   issues). This split is the concrete realization of L1's four-
   category stratification: `mechanical:critical` = "won't parse",
   `mechanical:high` = "parses but violates rule". Good.

3. Version parsing deliberately does not reach for `packaging`. That
   saves a runtime dep but accepts a narrow scope. If Myco ever needs
   to compare against PyPI-published versions, that's a contract
   change and gets its own craft.

4. B.1 ships no handlers and no findings. The temptation is strong to
   "just add a small severity→finding helper now". Resist — B.2 owns
   that, and keeping B.1 handler-free makes the layering legible.

**Escalation to user.** None. All Round 1.5 and 2.5 concerns resolve
locally; no L0/L1/L2 change surfaced. Proceed.

---

## File inventory

### Source (`src/myco/core/`)

| File | LoC budget | Contents |
|------|-----------|----------|
| `__init__.py` | ~20 | public re-exports only |
| `errors.py` | ~50 | MycoError, ContractError, SubstrateNotFound, CanonSchemaError, UsageError |
| `severity.py` | ~35 | `Severity(IntEnum)` + `downgrade(sev, floor)` helper |
| `paths.py` | ~40 | `SubstratePaths` dataclass: canon, notes, docs, state, entry_point |
| `substrate.py` | ~80 | `Substrate` dataclass, `find_substrate_root`, `Substrate.load` |
| `canon.py` | ~180 | `Canon` dataclass mirroring `canon_schema.md`; `load_canon` |
| `version.py` | ~100 | `PackageVersion`, `ContractVersion`, parse + cmp |
| `context.py` | ~60 | `MycoContext`, `Result`, `MycoContext.for_testing` |

Total ~565 LoC, well under the package-wide 800 megafile cap (no single
file is close).

### Tests (`tests/unit/core/`)

| File | What it covers |
|------|----------------|
| `test_severity.py` | ordering, IntEnum values, `downgrade` semantics, CRITICAL→HIGH under skeleton |
| `test_errors.py` | each exception's `exit_code`, inheritance tree, re-raise preserves type |
| `test_paths.py` | canonical path construction; immutability |
| `test_substrate.py` | walk-up hit; walk-up miss → SubstrateNotFound; corrupt canon → ContractError; nested-substrate innermost-wins |
| `test_canon.py` | minimal-valid parses; missing required → ContractError; unknown schema_version → ContractError; unknown top-level → preserved in .extras; extras round-trip |
| `test_version.py` | PackageVersion parses `0.4.0`, `0.4.0.dev`; ContractVersion parses `v0.4.0`, `v0.4.0-alpha.1`; ordering across pre-release; invalid → ValueError |
| `test_context.py` | `for_testing` constructs valid ctx; frozen dataclass rejects mutation; Result defaults |

### Fixtures (`tests/conftest.py` — augmented)

Add `minimal_canon_text` fixture (valid YAML string) and
`seeded_substrate(tmp_substrate_root)` fixture that writes
`_canon.yaml` + creates `notes/` + `docs/` dirs.

## Verification contract

```bash
pytest tests/unit/core/ -v
pytest --collect-only                              # still green at 13+~40
python -c "from myco.core import (Severity, MycoError, ContractError, \
    SubstrateNotFound, CanonSchemaError, Substrate, Canon, MycoContext, \
    Result); print('ok')"
python -c "from myco.core.version import PackageVersion, ContractVersion; \
    assert PackageVersion.parse('0.4.0.dev') < PackageVersion.parse('0.4.0')"
```

All must pass. Then commit with subject
`Stage B.1: myco.core primitives (severity, errors, substrate, canon, context)`.
