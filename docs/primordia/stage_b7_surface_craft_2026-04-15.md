# Stage B.7 — Surface Craft

> **Date**: 2026-04-15.
> **Governs**: `src/myco/surface/` + `tests/unit/surface/` + `src/myco/__main__.py`.
> **Upward**: L3 `command_manifest.md`, L1 `protocol.md` + `exit_codes.md`.

---

## Round 1 — 主张

Layout:

```
src/myco/surface/
├── __init__.py
├── manifest.py        # load + validate manifest.yaml; dispatcher
├── manifest.yaml      # SSoT for 11 verbs
├── cli.py             # argparse tree generated from manifest
└── mcp.py             # FastMCP tools generated from manifest
```

Eleven verbs per L3: genesis, hunger, eat, sense, forage, reflect,
digest, distill, perfuse, propagate, immune. Plus the `session-end`
meta-verb (orchestrates reflect + immune --fix).

Manifest loader responsibilities:

- Parse `manifest.yaml` (bundled inside `src/myco/surface/`).
- Validate against a tiny schema (commands[].name/handler/args[]).
- Import each `module:function` handler and cache the callable.
- Provide a `dispatch(name, args, ctx)` method returning `Result`.
- Argument coercion: `str / bool / int / path / list[str]`.

CLI responsibilities:

- Build an argparse tree: one subparser per verb.
- Global flags: `--project-dir`, `--exit-on`, `--json`.
- Invoke handler; print either human-readable or JSON payload.
- Exit with `Result.exit_code`; map `MycoError` → `exc.exit_code`
  (≥3).

MCP responsibilities:

- Use `FastMCP` to register one tool per manifest verb.
- Each tool invokes the same dispatch path as the CLI.
- Tool return is the `Result.payload` (plus `exit_code`).

## Round 1.5 — 自我反驳

T1. **Genesis handler shape.** Genesis predates the substrate — it has
no `ctx`. Its API is `bootstrap(project_dir, substrate_id, ...)`. The
manifest norm is `run(args, *, ctx)`. Options: (a) add a genesis
`run(args)` that ignores `ctx`; (b) let the manifest declare the
handler as "pre-substrate" and skip substrate loading for that verb.

T2. **Where does project-dir resolution happen?** Two places want it:
`core.substrate.discover(start)` walks up from cwd; genesis wants to
create a substrate at a specific directory. The CLI must route
`--project-dir` correctly for both.

T3. **Manifest YAML packaged as a resource.** Hatchling wheel config
has `packages = ["src/myco"]`. That's fine for `.yaml` files sitting
alongside `.py` files — but we should confirm Hatchling includes them.
If not, add explicit `[tool.hatch.build.targets.wheel.force-include]`
(or just rely on `src/myco/surface/manifest.yaml` being under the
package — it will be).

T4. **Return-schema validation.** L3 specifies a `returns:` section
in the manifest. For B.7, we'll land a skeleton — handlers return
payload dicts, and the manifest declares the shape, but we don't
enforce the shape at dispatch time. Enforcement comes as a homeostasis
dimension in B.8.

T5. **`--exit-on` plumbing.** Exit-on is a homeostasis concept. Only
`immune` currently respects it. Other handlers compute their own exit
codes (0 or ≥1). Don't pretend other verbs honor `--exit-on`; keep it
immune-specific but surface it as a global flag (ignored elsewhere).

T6. **MCP tool arg naming.** CLI uses `--project-dir`; MCP is JSON and
typically uses `project_dir`. The manifest lists arg names in dash-case
(per L3 sample: `project-dir`). Coerce dash-case → snake_case for the
handler dict, and flag-case (`--project-dir`) for argparse. MCP tool
input schema uses snake_case.

T7. **`session-end` meta-verb.** This is a composition of `reflect` +
`immune --fix`, not a single subsystem handler. Options: (a) a dedicated
handler under `surface/meta.py` that calls both; (b) declare it as a
sequence in the manifest and have the dispatcher run them in order.
(a) is simpler and more type-safe. Go with (a).

T8. **Where does the `Substrate` load happen?** Pre-B.7 tests built
`MycoContext` manually via `for_testing`. The CLI needs to build one
from the real environment: discover substrate root from cwd (or
`--project-dir`), load canon, populate now/env/stdio. Put this in
`surface/manifest.py::build_ctx`.

T9. **Genesis skips substrate discovery.** Since genesis creates a
substrate, the CLI must NOT try to discover one first. Mark genesis in
the manifest as `pre_substrate: true` and route accordingly.

T10. **Argparse `list[str]` handling.** Typical argparse uses `nargs="*"`
or repeated `--tag x --tag y`. Pick the latter — `nargs="+"` with
`action="append"` on a single flag — so the CLI reads `--tag foo --tag bar`.
MCP accepts JSON arrays directly.

T11. **CLI error mapping.** `MycoError` subclasses carry `exit_code`
(≥3). Catch at the top level, print the error message to stderr, exit
with `exc.exit_code`. Unhandled exceptions propagate (crash with stack
trace — a bug, not a user error).

## Round 2 — 修正

R1 (T1, T9). Manifest entries may declare `pre_substrate: true`. The
dispatcher skips substrate loading for such verbs. Genesis's handler
is `myco.genesis.genesis:run_cli`, a thin wrapper added in B.7 that
reads `args` and calls `bootstrap(...)`.

R2 (T2). `build_ctx(project_dir=None)` runs `find_substrate_root` on
`project_dir or Path.cwd()`. If `SubstrateNotFound`, re-raise as
`UsageError` with a helpful message (suggest `myco genesis`).

R3 (T3). Relying on Hatchling's default package-inclusion. Tests
confirm the YAML is importable via `importlib.resources.files`.

R4 (T5). `--exit-on` is a global CLI flag, defaults to the L1 ladder
default (`critical`). Only `immune` passes it through; other handlers
ignore it. Not a bug — manifest docstring notes this.

R5 (T6). Manifest args are YAML dash-case on the wire; the loader
normalizes to snake_case in the runtime dict it hands the handler.
CLI parser uses `--dash-case` flags; MCP schema exposes
`snake_case`. Internal dict always snake_case.

R6 (T7). `surface/meta.py::session_end_run(args, *, ctx)` orchestrates
reflect + immune+fix. Registered as a manifest entry whose handler is
`myco.surface.meta:session_end_run`.

R7 (T10). Argparse uses `nargs="*"` for list args; MCP accepts JSON
arrays. Consistent behavior: empty list if absent.

R8 (T11). Top-level CLI entry:

```python
def main(argv: list[str] | None = None) -> int:
    try:
        # parse → build_ctx (unless pre-substrate) → dispatch
        result = dispatch(...)
    except MycoError as exc:
        print(exc, file=sys.stderr)
        return exc.exit_code
    # print result.payload (or human-readable)
    return result.exit_code
```

## Round 2.5 — 再驳

T12. R6 puts `session_end_run` in `surface/meta.py`. But "surface is
pure adaptation" (L3 invariant 4). `session_end` is business logic (a
composition), not adaptation. Fix: put it in `src/myco/meta.py` (a new
cross-cutting module alongside `core/`), not under `surface/`. Keeps
invariant 4 intact. Alternatively: put it inside the first subsystem
that contains both — but it spans digestion (reflect) and homeostasis
(immune). Standalone module is cleanest.

T13. R2 raises `UsageError` for `SubstrateNotFound`. But pre_substrate
verbs (genesis) shouldn't discover at all. Split: dispatcher inspects
manifest entry → if `pre_substrate`, skip discovery entirely; else,
discover and re-raise cleanly on failure.

T14. CLI's JSON output — do we emit `{"payload": ..., "exit_code": ...}`
or just the payload? MCP callers want the full structure. CLI `--json`
should match MCP for parity. Go with structured form.

T15. MCP output exit_code: MCP tools don't natively "exit code". We
include `exit_code` in the tool return payload, so callers can branch.
The process itself continues running.

## Round 3 — 反思

F12. `session-end` lives at `src/myco/meta.py`. Single function,
small.
F13. Dispatcher branches on `pre_substrate`; never discovers for
genesis.
F14. `--json` output: `{"exit_code": N, "payload": {...}}`. Same
shape MCP returns.
F15. MCP includes `exit_code` in payload; no process-level exit.

### What this craft revealed

- The shared manifest is the narrow waist. CLI and MCP are both thin.
- Genesis's pre-substrate shape is a real asymmetry — the manifest
  carries a flag for it rather than faking a context.
- `--exit-on` is a specialty of immune, not a universal flag. Document
  it as such; don't pretend.
- `session-end` is legitimate cross-cutting composition; `src/myco/meta.py`
  is its home, keeping the `surface/` package "pure adaptation".

## Deliverables

```
src/myco/surface/
├── __init__.py
├── manifest.py
├── manifest.yaml
├── cli.py
└── mcp.py

src/myco/meta.py          # session_end composition
src/myco/__main__.py      # rewired to surface.cli:main

tests/unit/surface/
├── __init__.py
├── test_manifest.py
├── test_cli.py
└── test_mcp.py

tests/unit/test_meta.py
```

## Acceptance

- `pytest tests/` green (previous 230 + additions).
- `python -m myco --help` lists all 11 verbs (+ session-end).
- `python -m myco hunger --execute --project-dir <tmp>` runs end-to-end
  and exits 0.
- `python -m myco genesis --project-dir <new-dir> --substrate-id foo`
  creates a substrate.
- Manifest dispatcher resolves every handler at startup.
- MCP server builds (no protocol interaction test at B.7 — dimension
  in B.8 may add one).
