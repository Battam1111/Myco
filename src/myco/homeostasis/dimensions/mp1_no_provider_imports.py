"""MP1 — kernel imports no LLM provider SDK (L0 principle 1 enforcement).

v0.5.6 promotes Myco's **first-class mycelium-purity invariant** from
doctrine-by-convention to mechanical enforcement. L0 principle 1 states:

    *Agents call LLMs; the substrate does not embed provider calls in
     its own logic.*

Before v0.5.6, this was a sentence in ``docs/architecture/L2_DOCTRINE/
digestion.md`` and a habit the maintainers honored by convention.
Nothing mechanical stopped a future refactor from sneaking an
``import openai`` into, say, the ingestion pipeline — which would break
the agent-first boundary that makes Myco a substrate rather than a
product wrapper.

MP1 walks every ``.py`` file under ``<substrate_root>/src/myco/`` —
the kernel surface — and cross-checks its imports against a curated
blacklist of LLM provider SDKs. Finding any blacklisted top-level
module means the kernel has started reaching for an LLM directly; that
is a contract violation of the L0 trust boundary.

Governing doctrine:
``docs/architecture/L2_DOCTRINE/digestion.md`` (agent-first boundary).
Governing craft:
``docs/primordia/v0_5_6_mp1_mycelium_purity_craft_2026-04-18.md``.

Scope (what MP1 does NOT scan):

- ``src/myco/providers/`` — the declared opt-in escape hatch. Empty at
  v0.5.6 by design; adding a real provider bridge there requires (a)
  flipping ``canon.system.no_llm_in_substrate`` to ``false``, (b) a
  contract-bumping ``molt``, and (c) craft approval.
- ``.myco/plugins/`` — substrate-local extensions. MF2 governs this
  axis; reusing MP1 for plugins would cross subsystem boundaries.
- ``tests/`` — test fixtures import provider SDKs legitimately (e.g.
  to *prove* the boundary holds). MP1 is a kernel check, not a test
  check.
- Anything under a directory whose name starts with ``.`` (e.g.
  ``.venv``, ``.git``) or ``__pycache__``.

Severity logic:

- ``canon.system.no_llm_in_substrate: true`` (the default) + scan
  finds a violation → :attr:`Severity.HIGH` finding per import,
  message names each imported module. CI gates this by default.
- ``canon.system.no_llm_in_substrate: false`` + scan finds a violation
  → :attr:`Severity.LOW` finding per import, message surfaces that
  the substrate has opted out. The agent still sees the import so it
  knows the LLM boundary is not enforced here.
- Either canon value + scan clean → no finding.

Fixable: **False**. Removing an import is too destructive to automate
— it changes the meaning of the surrounding code. MP1 detects only;
repairing is human/agent work.
"""

from __future__ import annotations

import ast
from collections.abc import Iterable
from pathlib import Path
from typing import ClassVar

from myco.core.context import MycoContext
from myco.core.severity import Severity

from ..dimension import Dimension
from ..finding import Category, Finding

__all__ = ["MP1NoProviderImports"]


class MP1NoProviderImports(Dimension):
    """Kernel imports no LLM provider SDK (L0 principle 1 enforcement).

    Scans every ``.py`` file under the substrate's ``src/myco/``
    directory — excluding ``src/myco/providers/`` (the declared
    opt-in escape hatch) — for imports matching the provider
    blacklist. Cross-checks the finding severity against
    ``canon.system.no_llm_in_substrate``:

    - canon declares ``true`` (default) + scan finds violation →
      HIGH finding (contract violation; CI gates by default)
    - canon declares ``false`` + scan finds violation → LOW
      finding (opt-out declared, so technically valid, but
      immune surfaces it so the agent knows the LLM-boundary
      invariant is off for this substrate)
    - canon declares ``true`` + scan clean → no finding (healthy)
    - canon declares ``false`` + scan clean → no finding (opt-out
      declared but honored; also healthy)

    The blacklist covers the major Python LLM SDKs as of 2026-04.
    New provider shapes are added by editing :attr:`BLACKLIST` and
    bumping the governing craft; a blacklist miss is an honest gap
    (not a bug), because MP1 can only check what it knows to look
    for. The canon field ``no_llm_in_substrate`` is the policy knob;
    this dimension is the enforcement mechanism.
    """

    id = "MP1"
    category = Category.MECHANICAL
    default_severity = Severity.HIGH
    #: Removing an import mutates semantics of surrounding code; MP1
    #: detects, humans/agents repair.
    fixable = False

    #: Top-level dotted paths of known LLM provider SDKs. A match is
    #: either an exact equality or a dotted-prefix equality (so
    #: ``langchain_openai.chat_models`` matches the ``langchain_openai``
    #: entry). Curated 2026-04 per the v0.5.6 craft; extended 2026-04-21
    #: (v0.5.8 Phase 16c audit) to cover the provider ecosystem that has
    #: landed since v0.5.6. Extending the blacklist requires a craft
    #: entry + a contract-version bump.
    #:
    #: Note: this is a blacklist (fail-open on unknown SDKs). The
    #: bitter-lesson alternative — an allowlist + "everything else
    #: is kernel-internal" — was considered in the v0.5.6 craft and
    #: rejected as too strict for a substrate that imports stdlib +
    #: pyyaml + httpx + pypdf + bs4 widely. A future v0.6.x
    #: MP-series dim may invert the polarity; MP1 stays blacklist.
    BLACKLIST: ClassVar[frozenset[str]] = frozenset(
        {
            # v0.5.6 baseline — first-party provider SDKs
            "openai",
            "anthropic",
            "mistralai",
            "cohere",
            "voyageai",
            "google.generativeai",
            "google.genai",
            # LangChain ecosystem
            "langchain",
            "langchain_core",
            "langchain_openai",
            "langchain_anthropic",
            # v0.5.8 extension — LangChain provider integrations
            "langchain_google_genai",
            "langchain_mistralai",
            "langchain_cohere",
            "langchain_community",
            # LlamaIndex + llama.cpp
            "llama_index",
            "llama_cpp",
            "llama_cpp_python",
            # Local-first runtimes
            "ollama",
            # v0.5.8 extension — cloud provider SDKs
            "together",
            "fireworks",
            "groq",
            "deepseek",
            "zhipuai",
            "replicate",
            "huggingface_hub",
            # v0.5.8 extension — aggregator / router SDKs
            "litellm",
            "aisuite",
            "portkey_ai",
            "instructor",
            # v0.5.8 extension — orchestration frameworks that
            # themselves dispatch to providers
            "guidance",
            "dspy",
        }
    )

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        root = ctx.substrate.root
        kernel_dir = root / "src" / "myco"
        if not kernel_dir.is_dir():
            # Substrate does not ship a kernel tree under the canonical
            # path (e.g. a documentation-only substrate). Nothing to
            # check; silent exit.
            return

        system = ctx.substrate.canon.system or {}
        declared_no_llm = bool(system.get("no_llm_in_substrate", True))

        providers_dir = kernel_dir / "providers"

        for py_file in sorted(kernel_dir.rglob("*.py")):
            if self._should_skip(py_file, providers_dir):
                continue
            for violation in self._scan_file(py_file):
                rel_path, line, imported = violation
                if declared_no_llm:
                    yield Finding(
                        dimension_id=self.id,
                        category=self.category,
                        severity=Severity.HIGH,
                        message=(
                            f"kernel file imports LLM provider SDK "
                            f"{imported!r} (L0 principle 1 violation: "
                            f"agents call LLMs; the substrate does not). "
                            f"Either route through the agent surface or "
                            f"move the bridge under src/myco/providers/ "
                            f"and set canon.system.no_llm_in_substrate: "
                            f"false."
                        ),
                        path=rel_path,
                        line=line,
                    )
                else:
                    yield Finding(
                        dimension_id=self.id,
                        category=self.category,
                        severity=Severity.LOW,
                        message=(
                            f"kernel file imports LLM provider SDK "
                            f"{imported!r}; substrate opted out "
                            f"(canon.system.no_llm_in_substrate: false), "
                            f"so the LLM boundary is not enforced here."
                        ),
                        path=rel_path,
                        line=line,
                    )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _should_skip(self, py_file: Path, providers_dir: Path) -> bool:
        """True iff ``py_file`` is outside MP1's scan scope.

        Skips:

        - anything under ``src/myco/providers/`` (the declared opt-in
          escape hatch; ``canon.system.no_llm_in_substrate: false``
          governs this axis);
        - any ``__pycache__`` directory;
        - any directory whose name begins with ``.`` (``.venv``,
          ``.git``, …) — a source checkout may contain these even
          though git-ignored; rglob still descends into them.
        """
        try:
            rel = py_file.relative_to(providers_dir)
            # If we reach here, py_file is inside providers_dir.
            _ = rel
            return True
        except ValueError:
            pass

        for part in py_file.parts:
            if part == "__pycache__":
                return True
            # Hidden directories (``.venv``, ``.git``, etc). A leading
            # dot on the filename itself (``.__init__.py``) is not a
            # real Python module, so skipping is safe.
            if part.startswith(".") and part not in {".", ".."}:
                return True
        return False

    def _scan_file(self, py_file: Path) -> Iterable[tuple[str, int, str]]:
        """Yield ``(rel_path_posix, line, imported_name)`` for each violation.

        Returns an empty iterator when the file cannot be parsed —
        syntax errors are not MP1's concern (defer to MF2 or a future
        MF-series dimension that pins kernel parseability).
        """
        try:
            source = py_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return
        try:
            tree = ast.parse(source, filename=str(py_file))
        except SyntaxError:
            return

        rel_posix = py_file.as_posix()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name
                    if self._matches_blacklist(top):
                        yield (rel_posix, node.lineno, top)
            elif isinstance(node, ast.ImportFrom):
                # Relative imports (``from .x import y``) have
                # ``module`` either None or the dotted suffix only.
                # ``level`` > 0 marks them; they cannot pull in a
                # top-level provider SDK by definition.
                if node.level and node.level > 0:
                    continue
                mod = node.module
                if mod is None:
                    continue
                if self._matches_blacklist(mod):
                    yield (rel_posix, node.lineno, mod)

    @classmethod
    def _matches_blacklist(cls, dotted: str) -> bool:
        """True iff ``dotted`` is (or is nested under) a blacklist entry.

        Exact-match catches ``import openai``; dotted-prefix match
        catches ``from langchain_openai.chat_models import ChatOpenAI``
        (the top-level ``langchain_openai`` is the blacklisted root).
        """
        if dotted in cls.BLACKLIST:
            return True
        for entry in cls.BLACKLIST:
            if dotted.startswith(entry + "."):
                return True
        return False
