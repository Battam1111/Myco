# IOU — v0.7.10 examples/ smoke-test coverage gap (dry-run only)

> **Status**: OPEN. Surfaced 2026-05-10 by the v0.7.10 examples-smoke
> work that landed `tests/integration/examples/test_examples_smoke.py`.
> **Layer**: L3 (gap log against the v0.6.0 8-demo subtree commitment).
> **Scope**: the 8 framework demos under `examples/` are now smoke-
> covered in CI, but only along the `--dry` happy path. The real-
> framework MCP-stdio integration path is uncovered.

---

## What v0.7.10 closed

`tests/integration/examples/test_examples_smoke.py` proves, for each
of the 8 demos under `examples/`:

1. The demo's `main.py` loads via `importlib` and exposes a
   `main(dry: bool = False) -> int` callable (skipped per-demo when
   the framework dep isn't installed in the active venv).
2. The demo runs `main(dry=True)` against a freshly-germinated tmp
   Myco substrate, exits `0`, prints its dry-run token, and the
   substrate's `_canon.yaml` carries `contract_version` (the "expected
   shape" a Myco-aware integration would consume).

The pre-existing CI gap ("never E2E tested") is closed for the dry-run
surface. The 8 demos covered:

| Demo dir | Framework probe | Dry-run test status |
|---|---|---|
| `agno-myco-demo` | `agno` | PASS (dry); SKIP (framework absent) |
| `claude-sdk-myco-demo` | `claude_agent_sdk` | PASS (dry); SKIP |
| `crewai-myco-demo` | `crewai` | PASS (dry); SKIP |
| `dspy-myco-demo` | `dspy` | PASS (dry); SKIP |
| `langgraph-myco-demo` | `langchain_mcp_adapters` | PASS (dry); SKIP |
| `microsoft-agent-framework-myco-demo` | `agent_framework` | PASS (dry); SKIP |
| `praisonai-myco-demo` | `praisonaiagents` | PASS (dry); SKIP |
| `smolagents-myco-demo` | `smolagents` | PASS (dry); SKIP |

---

## What's still uncovered

### 1 — Non-dry path: real framework + real `mcp-server-myco` stdio

Each demo's `main(dry=False)` imports its framework (e.g. `agno.Agent`,
`langchain_mcp_adapters.client.MultiServerMCPClient`,
`crewai_tools.MCPServerAdapter`) and connects it to `mcp-server-myco`
over stdio. None of this is exercised in CI today because:

- The 8 frameworks together pull in a transitive closure that is
  expensive to install + version-conflict-prone (e.g. CrewAI pulls
  pydantic; LangGraph pulls langchain-core; Agno is its own ecosystem).
- Several frameworks require an LLM API key at construction time
  (Anthropic/OpenAI), which CI cannot supply without a secret-bearing
  matrix cell.
- `mcp-server-myco`'s stdio stream needs a child-process harness that
  the demos themselves don't expose as a programmatic API.

### 2 — No assertion that demos actually exercise `myco_*` verbs

The dry path prints a static token (`"[<demo>] dry-run OK"`), not the
list of tools the demo would invoke if the framework were live. The
"`myco_*` tool invocations" half of the v0.7.10 spec is satisfied by
the substrate's `contract_version` reference rather than a recorded
verb call, because the dry path doesn't make verb calls.

### 3 — No version-pin floors in the `[examples]` extras

`pyproject.toml`'s new `[project.optional-dependencies].examples`
list (added by v0.7.10) carries no `>=X` floors. Framework releases
move fast; a future LangGraph 1.0 that breaks the `MultiServerMCPClient`
constructor would silently flip the `langgraph-myco-demo` from PASS
to FAIL on the next `pip install -U`. This is intentional debt for
v0.7.10 (we don't want every patch release to bump 8 floors), but
should be revisited at the v0.8 boundary.

---

## Concrete next steps (when budget allows)

1. **Add a `[ci-examples]` matrix cell** that runs
   `pip install 'myco[examples]'` + the 8 framework deps, then exercises
   the import-cleanly suite with the framework present (those tests
   currently SKIP on every run). Even without LLM credentials, the
   import side-effect coverage triples.
2. **Add per-demo non-dry tests gated behind `MYCO_RUN_FRAMEWORK_E2E=1`**
   that mock the framework's LLM client at the boundary (e.g. monkey-
   patch `langchain_anthropic.ChatAnthropic` to return a canned
   response) and run the full pipeline, asserting at least one
   `myco_*` tool call is recorded.
3. **Add MF6** (or extend MF3) to lint that every demo under
   `examples/<framework>-myco-demo/` carries both `main.py` AND
   `README.md` AND a corresponding entry in `tests/integration/examples/
   test_examples_smoke.py::DEMOS`. The
   `test_demos_registry_matches_examples_dir` test enforces this at
   pytest time, but a homeostasis dim would catch it at `myco immune`
   time too.

---

## Closure criteria

This IOU is closed when:

1. CI has a matrix cell that installs `myco[examples]` and runs
   `tests/integration/examples/test_examples_smoke.py` with
   `pytest.importorskip` inverted (i.e. the import-cleanly tests
   transition from SKIP to PASS).
2. At least one demo per framework has a non-dry test that asserts a
   recorded `myco_*` tool invocation against a mocked LLM.
3. The `[examples]` extras list either pins floors or carries an
   automated upgrade-watch (Dependabot constraint file) so silent
   framework drift becomes loud.

Until then, the v0.6.0 §V claim "8-framework demo subtree, working
end-to-end" is **CI-verified for the harness only**, not the framework
adapter integration.

---

## Cross-references

- **Test file**: [`tests/integration/examples/test_examples_smoke.py`](../../tests/integration/examples/test_examples_smoke.py)
- **Demo subtree**: [`examples/`](../../examples/)
- **Extras target**: `pyproject.toml::[project.optional-dependencies].examples`
- **Sibling IOU**: [`docs/iou/v0_7_10_streamable_http_gaps.md`](v0_7_10_streamable_http_gaps.md)
- **L0 reference**: `docs/architecture/L0_VISION.md` § 8-framework
  subtree (the original commitment v0.7.10 partially redeems).

---

## v0.8.0 update — adjacent multimedia gap closed

v0.8.0 closes the multimedia gap via `myco[multimedia]` extras (3
adapters, opt-in): `audio.py` (Whisper segment transcription),
`image_ocr.py` (pytesseract single-image OCR), `video_frames.py`
(OpenCV frame sampling + per-frame OCR). Total adapter count moves
from 10 (v0.7.10) → **13** (v0.8.0). The same `[examples]` opt-in
discipline applies: heavy deps live behind a single extras flag,
the default install stays lean, and the adapters cleanly emit
install-extras failed-stubs when the extras are absent (per the
v0.7.3 AD1 closure). This IOU's *examples-dry-only* concern is
orthogonal — it remains OPEN for the `[examples]` extras row, with
the v0.8.0 multimedia work providing a fresh template for the
"opt-in heavy-dep modality" pattern future bumps may follow.
