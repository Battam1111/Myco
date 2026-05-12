# Stage B.2 Homeostasis Kernel — Implementation Craft

> **Status**: DRAFT 2026-04-15, awaiting execution.
> **Depth**: three rounds — B.2 is the most load-bearing subsystem and
> has real tensions around Dimension API shape, registry mechanics,
> exit-policy grammar, and skeleton downgrade sequencing.
> **Governing docs**:
> - `docs/architecture/L1_CONTRACT/exit_codes.md` (exit ladder, `--exit-on` grammar, skeleton downgrade)
> - `docs/architecture/L2_DOCTRINE/homeostasis.md` (responsibility + boundary; ≤ 1500 LoC kernel budget excluding dimensions)
> - `docs/architecture/L3_IMPLEMENTATION/package_map.md` (kernel / exit_policy / skeleton / dimensions layout)
> - `docs/architecture/L1_CONTRACT/canon_schema.md` (`lint.dimensions` map, `lint.categories`, skeleton marker)

---

## Intent

Land the homeostasis infrastructure — enough to:

1. Register a dimension, look it up by id, list all, explain one.
2. Run selected dimensions against a substrate and collect findings.
3. Apply skeleton-mode downgrade.
4. Parse an `--exit-on` spec and compute the exit code from the
   findings.
5. Offer a kernel entry point that a future `myco immune` handler
   (B.7) invokes with a single call.

Zero concrete lint dimensions. B.8 lands those. B.2 ships a single
*smoke* dimension (`L0_kernel_alive`) used only to prove the registry
works end-to-end in tests.

---

## Round 1 — 主张

### Proposed module surface

```
src/myco/homeostasis/
├── __init__.py              re-export public surface
├── finding.py               Finding dataclass + Category enum
├── dimension.py             Dimension base class / protocol
├── registry.py              DimensionRegistry
├── skeleton.py              apply_skeleton_downgrade()
├── exit_policy.py           parse_exit_policy() + ExitPolicy.compute()
├── kernel.py                run_immune() — orchestrator entry point
└── dimensions/
    ├── __init__.py
    └── l0_kernel_alive.py   smoke dim; always emits LOW "alive"
```

### Types (first pass)

```python
class Category(str, Enum):
    MECHANICAL = "mechanical"
    SHIPPED    = "shipped"
    METABOLIC  = "metabolic"
    SEMANTIC   = "semantic"

@dataclass(frozen=True)
class Finding:
    dimension_id: str
    category: Category
    severity: Severity
    message: str
    path: Path | None = None
    line: int | None = None
    fixable: bool = False

class Dimension(Protocol):
    id: str
    category: Category
    default_severity: Severity
    def run(self, ctx: MycoContext) -> Iterable[Finding]: ...
```

### Registry

```python
class DimensionRegistry:
    def register(self, dim: Dimension) -> None: ...
    def get(self, dim_id: str) -> Dimension: ...
    def all(self) -> tuple[Dimension, ...]: ...
```

Registration happens at import time in `dimensions/__init__.py`.

### `--exit-on` grammar

Grammar (restated from `exit_codes.md`):

```
<spec>         ::= <global> | <per-cat-list>
<global>       ::= "never" | "critical" | "high"
<per-cat-list> ::= <cat-rule> ("," <cat-rule>)*
<cat-rule>     ::= <cat> ":" <threshold>
<threshold>    ::= "never" | "critical" | "high"
```

Per-category lists default *unnamed* categories to `critical`. Unknown
categories or thresholds → `ContractError` (exit 3).

### Kernel flow

```
run_immune(ctx, registry, *, selected=None, exit_on="critical", fix=False):
    1. collect dims (all, or restricted by `selected`)
    2. for each dim: run, flatten findings
    3. apply skeleton downgrade to all findings (if ctx.substrate.is_skeleton)
    4. exit_code = ExitPolicy.parse(exit_on).compute(findings)
    5. return Result(exit_code, findings, payload={...})
```

---

## Round 1.5 — 自我反驳

**R1.5-A. Protocol vs. ABC for `Dimension`.**
Protocol is duck-typed; ABC gives explicit inheritance. Pro-protocol:
lightweight, doesn't force subclassing. Pro-ABC: registry can type-
check `isinstance(dim, Dimension)` at registration.
→ **Resolution**: use a concrete ABC `Dimension`. The registry's
`register` asserts `isinstance(dim, Dimension)`, which catches typos
before tests run. B.8 dimensions subclass `Dimension` and override
`run`. This is worth ~10 LoC for clarity. **Applied.**

**R1.5-B. Where does category come from — code or canon?**
`canon_schema.md` shows `lint.dimensions: { L0: mechanical, … }` — the
map is in canon. But dimensions also declare their category in code.
Two sources → drift.
→ **Resolution**: code is SSoT for the category. Canon's
`lint.dimensions` is a *reflection* that gets lint-checked against code
in a later dimension (add it to the B.8 dimension set). At B.2 the
kernel reads `dim.category` directly. If canon carries a conflicting
mapping, the kernel logs a `mechanical:HIGH` finding (not handled by
B.2, noted as TODO for B.8). **Applied.**

**R1.5-C. Skeleton downgrade scope.**
`exit_codes.md` says skeleton-mode downgrades L0 and L1 CRITICAL→HIGH.
But the "affected_dimensions" list is canon-driven (`lint.skeleton_
downgrade.affected_dimensions`). B.2 must read that list from canon,
not hard-code `[L0, L1]`.
→ **Resolution**: `apply_skeleton_downgrade(findings, ctx)` reads
`ctx.substrate.canon.lint.get("skeleton_downgrade", {}).get("affected_
dimensions", [])` and caps those dimensions' findings at HIGH. Empty
list or missing section → no-op. **Applied.**

**R1.5-D. Finding equality & hashing.**
`@dataclass(frozen=True)` gives value-equality. But `Path` objects are
hashable only as `PurePath`; mixing `None` and `Path` in
`tuple[Finding, ...]` sometimes bites on Windows paths.
→ **Resolution**: store `path` as `str | None`, not `Path`. Keep
construction ergonomic: `Finding.from_path(path, ...)` classmethod
converts a `Path` to its `str()` form. This avoids a hashing bug class
and works the same everywhere.

**R1.5-E. Registry as module-global singleton vs. per-kernel-call.**
Pre-rewrite Myco used a module-level `_REGISTRY`. That breaks tests
(dimension registration leaks between tests).
→ **Resolution**: registry is a plain object that the caller
constructs. There's a `default_registry()` factory that returns a
fresh, populated registry (registers all dims in `dimensions/`). Tests
build their own empty registries and register only the smoke dim they
care about. **Applied.**

**R1.5-F. Exit-policy grammar ambiguity.**
The grammar allows both `critical` (global) and `mechanical:critical`
(per-cat). How do we tell apart `critical` (global) from a
typo-per-cat like `critical:critical`? And what if someone passes
`mechanical`?
→ **Resolution**: parsing is two-pass. If the raw string contains no
`:`, it must match one of the three globals. If it contains `:`, every
comma-separated piece must be `<cat>:<threshold>`. `mechanical` alone
(no colon) is a parse error. `critical:critical` errors because
`critical` is not a known category.

**R1.5-G. What does "auto-fix" mean at B.2?**
Homeostasis doc says Homeostasis auto-fixes when `--fix` is passed and
the dimension declares itself fixable. B.2 has no fixable dimension.
→ **Resolution**: the `fix: bool` kwarg is plumbed through `run_
immune` but does nothing at B.2 (returns findings unchanged). The
`fixable` flag on `Finding` is declared but unused. Actual auto-fix
lands with the first fixable dimension in B.8. Document the TODO in
the kernel docstring.

---

## Round 2 — 修正 (after R1.5)

### Locked module surface

```
src/myco/homeostasis/
├── __init__.py              public: Finding, Category, Dimension,
│                            DimensionRegistry, default_registry,
│                            parse_exit_policy, ExitPolicy,
│                            apply_skeleton_downgrade, run_immune
├── finding.py               Finding + Category
├── dimension.py             Dimension ABC
├── registry.py              DimensionRegistry + default_registry()
├── skeleton.py              apply_skeleton_downgrade()
├── exit_policy.py           parse_exit_policy() + ExitPolicy
├── kernel.py                run_immune()
└── dimensions/
    ├── __init__.py          imports l0_kernel_alive; registers on load
    └── l0_kernel_alive.py   smoke dimension — LOW severity, always fires
```

### Locked types

```python
class Category(str, Enum):
    MECHANICAL = "mechanical"
    SHIPPED    = "shipped"
    METABOLIC  = "metabolic"
    SEMANTIC   = "semantic"

@dataclass(frozen=True)
class Finding:
    dimension_id: str
    category: Category
    severity: Severity
    message: str
    path: str | None = None
    line: int | None = None
    fixable: bool = False

    @classmethod
    def from_path(cls, *, dimension_id, category, severity, message,
                  path: Path | None = None, line=None, fixable=False) -> Finding:
        return cls(dimension_id, category, severity, message,
                   str(path) if path else None, line, fixable)

class Dimension(ABC):
    id: ClassVar[str]
    category: ClassVar[Category]
    default_severity: ClassVar[Severity]

    @abstractmethod
    def run(self, ctx: MycoContext) -> Iterable[Finding]: ...

    @property
    def explain(self) -> str:
        """Default: the class docstring. Override for dynamic explain."""
        return (self.__class__.__doc__ or "").strip()
```

### Exit-policy evaluator

```python
@dataclass(frozen=True)
class ExitPolicy:
    # dict: Category → Threshold
    thresholds: Mapping[Category, Threshold]

    def compute(self, findings: Iterable[Finding]) -> int:
        worst = 0
        for f in findings:
            t = self.thresholds[f.category]
            if t == Threshold.NEVER: continue
            if f.severity == Severity.CRITICAL: worst = max(worst, 2)
            elif f.severity == Severity.HIGH and t == Threshold.HIGH:
                worst = max(worst, 1)
            # MEDIUM and LOW never trip exit regardless of threshold
        return worst
```

`Threshold` is a small enum: `NEVER | CRITICAL | HIGH`.

### Skeleton downgrade

```python
def apply_skeleton_downgrade(
    findings: Iterable[Finding],
    *,
    ctx: MycoContext,
) -> tuple[Finding, ...]:
    if not ctx.substrate.is_skeleton:
        return tuple(findings)
    affected = set(
        ctx.substrate.canon.lint.get("skeleton_downgrade", {})
        .get("affected_dimensions", [])
    )
    out = []
    for f in findings:
        if f.dimension_id in affected and f.severity == Severity.CRITICAL:
            out.append(replace(f, severity=Severity.HIGH))
        else:
            out.append(f)
    return tuple(out)
```

### Kernel orchestrator

```python
def run_immune(
    ctx: MycoContext,
    registry: DimensionRegistry,
    *,
    selected: Sequence[str] | None = None,
    exit_on: str = "critical",
    fix: bool = False,     # B.2: plumbed but no-op
) -> Result:
    dims = [registry.get(i) for i in selected] if selected else registry.all()
    findings: list[Finding] = []
    for dim in dims:
        findings.extend(dim.run(ctx))
    findings = apply_skeleton_downgrade(findings, ctx=ctx)
    policy = parse_exit_policy(exit_on)
    exit_code = policy.compute(findings)
    return Result(
        exit_code=exit_code,
        findings=tuple(findings),
        payload={"dimensions_run": [d.id for d in dims]},
    )
```

---

## Round 2.5 — 再驳

**R2.5-A. `run_immune` swallows exceptions from dimensions.**
As written, a dimension that raises kills the whole run.
→ **Response**: for B.2 this is correct — a crashing dimension is a
bug, not a finding, and should surface immediately. B.8 may opt-in to
per-dimension exception handling if we find a need. Document the
choice in the kernel docstring.

**R2.5-B. Threshold enum vs. string literal.**
The grammar keywords are strings (`"never"`, `"critical"`, `"high"`).
Converting to enum adds a layer. Why not just compare strings?
→ **Response**: enums catch typos at *parse* time (before any finding
is evaluated). Tests are cleaner. Keep the enum.

**R2.5-C. `parse_exit_policy("never")` vs. `parse_exit_policy("foo:never")`.**
The first is a global keyword; the second is a per-cat rule whose cat
happens to be invalid. Need distinct error messages.
→ **Response**: error messages explicitly say "unknown global
keyword" vs. "unknown category in per-cat rule". **Applied.**

**R2.5-D. HIGH-finding on a category with threshold `critical` — silent.**
Policy is: threshold `critical` means "only CRITICAL trips". So HIGH
findings in a `critical`-threshold category produce no exit bump but
are still *reported*. Confirm.
→ **Response**: Correct. They appear in `Result.findings` so the
surface layer can print them; they just don't affect exit code. Add a
test for this case.

**R2.5-E. `Finding.fixable` unused at B.2 — YAGNI?**
Nothing in B.2 reads `fixable`. Should it wait for B.8?
→ **Response**: the field is declared by contract (per homeostasis
doc: "dimension declares itself fixable"). Defining it now at the
type level is free and keeps B.8's dimension files from having to
invent it. Keep.

**R2.5-F. `selected: Sequence[str]` — what if a selected id is unknown?**
`registry.get(missing_id)` raises `KeyError`. Run crashes, user sees
stack trace.
→ **Response**: map `KeyError` to `UsageError("unknown dimension:
{id}")` at the kernel boundary. exit 3 + clean message. **Applied.**

---

## Round 3 — 反思

1. The big decision pair was **ABC vs. Protocol** for `Dimension` and
   **enum vs. str** for `Threshold`. Both land on the "more typing
   structure" side. For a kernel that third-party symbiont substrates
   will subclass / extend, that costs ~20 LoC and pays back every time
   a typo is caught before runtime.

2. B.2's hardest temptation is **writing real dimensions early**. The
   kernel is useless without dimensions, and writing one real
   dimension "just to make immune do something" would be cheap.
   Resist — B.8 is the doctrinal home, and pre-populating the 30
   v0.3 dimensions now would recreate the ported-not-rewritten
   failure mode explicitly banned by §9. The smoke `L0_kernel_alive`
   dimension stays deliberately trivial: it proves the wiring works
   and nothing more.

3. Skeleton-downgrade semantics are canon-driven, not hard-coded.
   That means the B.2 code has zero knowledge of *which* dimensions
   get downgraded — it just respects the canon's declaration. This is
   exactly the layer discipline L0/L1/L2 demands.

4. **Escalation to user.** None. All R1.5/R2.5 questions resolve
   locally without contract changes. Proceed.

---

## File inventory

| File | LoC budget | Contents |
|------|-----------|----------|
| `__init__.py` | ~30 | re-exports |
| `finding.py` | ~60 | `Category`, `Finding`, `from_path` |
| `dimension.py` | ~50 | `Dimension` ABC |
| `registry.py` | ~80 | `DimensionRegistry`, `default_registry()` |
| `skeleton.py` | ~45 | `apply_skeleton_downgrade` |
| `exit_policy.py` | ~130 | `Threshold`, `ExitPolicy`, `parse_exit_policy` |
| `kernel.py` | ~90 | `run_immune` |
| `dimensions/__init__.py` | ~15 | loader |
| `dimensions/l0_kernel_alive.py` | ~30 | smoke dim |

Total ~530 LoC kernel, under the 1500-LoC budget with substantial
headroom for B.2 bugfixes before B.8 dimension files add their own LoC.

### Tests (`tests/unit/homeostasis/`)

| File | What it covers |
|------|----------------|
| `test_finding.py` | Finding construction, Category enum, `from_path` |
| `test_dimension.py` | abstract cannot instantiate; subclass works |
| `test_registry.py` | register, get, all, duplicate id error, default_registry has smoke dim |
| `test_skeleton.py` | no-op when not skeleton; L0 CRITICAL→HIGH when skeleton; non-affected unchanged |
| `test_exit_policy.py` | each global; per-cat list; defaults unnamed to critical; unknown cat/threshold raise ContractError; compute examples from exit_codes.md |
| `test_kernel.py` | run all; run selected; unknown selected→UsageError; skeleton downgrade applied before policy; exit_code 0/1/2 end-to-end |
| `test_l0_kernel_alive.py` | smoke dim always emits, category mechanical, severity LOW |

## Verification contract

```bash
pytest tests/unit/core/ tests/unit/homeostasis/ -v
pytest --collect-only                 # still all green
python -c "from myco.homeostasis import (
    Finding, Category, Dimension, DimensionRegistry, default_registry,
    parse_exit_policy, ExitPolicy, apply_skeleton_downgrade, run_immune)"
python -c "
from myco.homeostasis import parse_exit_policy
p = parse_exit_policy('mechanical:critical,shipped:critical,metabolic:never,semantic:never')
print({k.value: v.name for k, v in p.thresholds.items()})
"
```

All green → commit:
`Stage B.2: homeostasis kernel (Finding / Dimension / Registry / ExitPolicy / skeleton downgrade / run_immune)`.
