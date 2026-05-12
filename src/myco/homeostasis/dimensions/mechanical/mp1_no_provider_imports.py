"""MP1 — kernel imports no LLM provider SDK + craft host signature (L0 P1 enforcement).

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

**v0.6.14 extension — craft host signature:** MP1 also walks every
``docs/primordia/*.md`` craft proposal and verifies frontmatter carries
``authored_by:`` naming a host from
``canon.governance.recognized_authoring_hosts`` (default list:
``claude-code-agent``, ``cursor-agent``, ``claude-desktop-agent``,
``cowork-agent``, ``human``). A craft missing the field — or naming an
unrecognized host — emits a HIGH finding. This is the **mechanical
guard** that "no craft was authored inside the substrate process": even
if a future bug let substrate-side code generate a craft markdown file,
MP1 would refuse it without a recognized host signature, and ``myco
winnow`` (which now requires immune-clean for high-risk crafts) would
gate it.

Governing doctrine:
``docs/architecture/L2_DOCTRINE/digestion.md`` (agent-first boundary)
+ ``docs/architecture/L2_DOCTRINE/cycle.md`` § "Cycle 自起 fruit—winnow—
molt 闭环 (v0.6.14+)".
Governing crafts:
``docs/contract_changelog.md`` § v0.5.6 (origin)
+ ``docs/primordia/v0_6_14_cycle_autostart_fruit_winnow_molt_loop_craft_2026-04-29.md``
(host-signature extension).

Scope (what MP1 does NOT scan):

- ``.myco/plugins/`` — substrate-local extensions. MF2 governs this
  axis; reusing MP1 for plugins would cross subsystem boundaries.
- ``tests/`` — test fixtures import provider SDKs legitimately (e.g.
  to *prove* the boundary holds). MP1 is a kernel check, not a test
  check.
- Anything under a directory whose name starts with ``.`` (e.g.
  ``.venv``, ``.git``) or ``__pycache__``.

**Removed at v0.6.14**: the ``src/myco/providers/`` path-skip. v0.6.14
excretes the directory entirely (per the v0.6.14 craft Round 2 §T17 —
"providers/ was reserved at v0.5.6 as escape hatch; v0.6.14 excretes
as never-populated through 7 minor releases"). The directory's
nonexistence is the stronger guard than a path-skip; if a synthetic
substrate (e.g. a downstream test fixture) recreates the directory,
MP1 now scans it like any other kernel path.

Severity logic (provider import scan):

- ``canon.system.llm_policy: "forbidden"`` (the default) + scan
  finds a violation → :attr:`Severity.HIGH` finding per import,
  message names each imported module. CI gates this by default.
- ``canon.system.llm_policy: "opt-in"`` + scan finds a violation
  → :attr:`Severity.LOW` finding per import, message surfaces that
  the substrate has opted out. The agent still sees the import so it
  knows the LLM boundary is not enforced here.
- Either canon value + scan clean → no finding.

Severity logic (craft host signature, v0.6.14+):

- Craft missing ``authored_by:`` frontmatter key → HIGH finding.
- Craft with ``authored_by: <not-in-recognized-list>`` → HIGH finding.
- Craft with ``authored_by: <recognized-host>`` → no finding.

The recognized-hosts list is read fresh from
``canon.governance.recognized_authoring_hosts`` on each run. Crafts in
the special directory ``docs/primordia/_excreted/`` are skipped (MB6's
auto-excretion path produces these from stale DRAFTs; they're not live
governance artifacts).

Fixable: **False**. Removing an import is too destructive to automate
— it changes the meaning of the surrounding code. Adding a missing
``authored_by:`` field is also not auto-fixable — the substrate cannot
know whether a craft was authored by a human or by claude-code-agent;
that's the human's call. MP1 detects only; repairing is human/agent work.
"""

from __future__ import annotations

import ast
from collections.abc import Iterable
from pathlib import Path
from typing import ClassVar

from myco.core.context import MycoContext
from myco.core.errors import MycoError
from myco.core.io_atomic import bounded_read_text
from myco.core.severity import Severity
from myco.homeostasis.dimension import Dimension
from myco.homeostasis.finding import Category, Finding

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

        system = ctx.substrate.canon.system or {}
        # v0.6.0: schema v2 replaces ``no_llm_in_substrate: bool`` with
        # ``llm_policy: "forbidden" | "opt-in"``.
        # v0.6.14: ``providers-declared`` enum option dropped (providers/
        # excreted; never-populated through 7 minor releases). Read the v2
        # enum first; fall back to v1 bool for substrates that somehow
        # bypass the upgrader chain.
        llm_policy = system.get("llm_policy")
        if llm_policy is not None:
            declared_no_llm = str(llm_policy) == "forbidden"
        else:
            declared_no_llm = bool(system.get("no_llm_in_substrate", True))

        # ----- Part 1: provider-import scan (v0.5.6+) -----
        if kernel_dir.is_dir():
            for py_file in sorted(kernel_dir.rglob("*.py")):
                if self._should_skip(py_file):
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
                                f"Route through the agent surface (host-mediated "
                                f"MCP sampling or Claude Code Agent tool sub-agent "
                                f"per cycle.md L0 P1 exception #2)."
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
                                f"(canon.system.llm_policy: opt-in), "
                                f"so the LLM boundary is not enforced here."
                            ),
                            path=rel_path,
                            line=line,
                        )

        # ----- Part 2: craft host-signature scan (v0.6.14+) -----
        # v0.8.5 — canon-configurable docs_dir (Myco-self uses .docs/).
        primordia_dir = ctx.substrate.paths.docs / "primordia"
        if primordia_dir.is_dir():
            governance = system.get("governance", {}) or {}
            recognized_hosts = frozenset(
                governance.get(
                    "recognized_authoring_hosts",
                    # Fallback default for substrates without v0.6.14 governance
                    # block. Mirrors the canon default exactly.
                    [
                        "claude-code-agent",
                        "cursor-agent",
                        "claude-desktop-agent",
                        "cowork-agent",
                        "human",
                    ],
                )
            )
            for craft_path in sorted(primordia_dir.glob("*.md")):
                yield from self._scan_craft_authorship(
                    craft_path, root, recognized_hosts
                )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _should_skip(self, py_file: Path) -> bool:
        """True iff ``py_file`` is outside MP1's scan scope.

        Skips:

        - any ``__pycache__`` directory;
        - any directory whose name begins with ``.`` (``.venv``,
          ``.git``, …) — a source checkout may contain these even
          though git-ignored; rglob still descends into them.

        v0.6.14: removed the ``src/myco/providers/`` path-skip — the
        directory was excreted (never populated through 7 minor releases).
        Its nonexistence is the stronger guard. If a synthetic substrate
        recreates the directory, MP1 now scans it like any other kernel
        path; declared opt-in via ``llm_policy: opt-in`` flips findings
        to LOW severity.
        """
        for part in py_file.parts:
            if part == "__pycache__":
                return True
            # Hidden directories (``.venv``, ``.git``, etc). A leading
            # dot on the filename itself (``.__init__.py``) is not a
            # real Python module, so skipping is safe.
            if part.startswith(".") and part not in {".", ".."}:
                return True
        return False

    def _scan_craft_authorship(
        self, craft_path: Path, root: Path, recognized_hosts: frozenset[str]
    ) -> Iterable[Finding]:
        """Yield host-signature findings for a single craft markdown file.

        v0.6.14+ scan path. Scope: files under ``docs/primordia/*.md`` whose
        frontmatter declares ``type: craft``. Other primordia files
        (historical agent-handoff notes, old release-notes, audit reports)
        are exempt — the host-signature requirement is craft-specific
        because crafts are governance proposals that mutate doctrine, while
        non-craft primordia are records of decisions already made.

        Skips files under ``docs/primordia/_excreted/`` (auto-excreted stale
        DRAFTs from MB6 are no longer live governance artifacts).
        """
        import re

        try:
            rel = craft_path.relative_to(root).as_posix()
        except ValueError:
            return
        if "_excreted/" in rel or "/_excreted/" in rel:
            return

        try:
            text = bounded_read_text(craft_path)
        except (OSError, UnicodeDecodeError, MycoError):
            return

        # Files without frontmatter are non-craft primordia (e.g. handoff
        # notes, raw transcripts). Exempt — not governance proposals.
        if not text.startswith("---\n") and not text.startswith("---\r\n"):
            return

        # Find the closing `---` delimiter.
        match = re.search(r"^---\s*$", text[4:], re.MULTILINE)
        if match is None:
            return  # malformed frontmatter — exempt (non-craft)
        fm_text = text[4 : 4 + match.start()]

        # Scope-restrict to type: craft. Other types (audit, design-note,
        # handoff, etc.) are exempt from host-signature requirement.
        type_match = re.search(
            r"^\s*type\s*:\s*['\"]?([^'\"\n#]+?)['\"]?\s*(?:#.*)?$",
            fm_text,
            re.MULTILINE,
        )
        if type_match is None or type_match.group(1).strip() != "craft":
            return  # not a craft — exempt

        # This is a craft. authored_by: is required.
        host_match = re.search(
            r"^\s*authored_by\s*:\s*['\"]?([^'\"\n#]+?)['\"]?\s*(?:#.*)?$",
            fm_text,
            re.MULTILINE,
        )
        if host_match is None:
            yield Finding(
                dimension_id=self.id,
                category=self.category,
                severity=Severity.HIGH,
                message=(
                    f"craft {rel} (type: craft) frontmatter is missing required "
                    f"authored_by: field (v0.6.14+). Add "
                    f"`authored_by: <recognized-host>` where host is one of "
                    f"{sorted(recognized_hosts)}. This is the mechanical "
                    f"guard that no craft was authored inside the substrate "
                    f'process; see L2_DOCTRINE/cycle.md § "Cycle 自起 闭环".'
                ),
                path=rel,
                line=1,
            )
            return

        host = host_match.group(1).strip()
        if host not in recognized_hosts:
            yield Finding(
                dimension_id=self.id,
                category=self.category,
                severity=Severity.HIGH,
                message=(
                    f"craft {rel} declares unrecognized authored_by: {host!r}. "
                    f"Recognized hosts (from canon.governance.recognized_authoring_hosts): "
                    f"{sorted(recognized_hosts)}. To add a host, edit "
                    f"_canon.yaml::system.governance.recognized_authoring_hosts."
                ),
                path=rel,
                line=1,
            )
            return
        # host is recognized: no finding.

    def _scan_file(self, py_file: Path) -> Iterable[tuple[str, int, str]]:
        """Yield ``(rel_path_posix, line, imported_name)`` for each violation.

        Returns an empty iterator when the file cannot be parsed —
        syntax errors are not MP1's concern (defer to MF2 or a future
        MF-series dimension that pins kernel parseability).
        """
        try:
            source = bounded_read_text(py_file)
        except (OSError, UnicodeDecodeError, MycoError):
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
