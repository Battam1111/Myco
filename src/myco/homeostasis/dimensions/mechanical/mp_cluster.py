"""MP-cluster — merged dimensions (MP1, MP2, MP3).

v0.8.8 merged: this file consolidates the per-dim files that previously
lived as one file per dimension under ``homeostasis/dimensions/mechanical/``.
Class names and behaviour are byte-equivalent — only file locations
changed. Per L1 protocol.md: L3 organization choices are ordinary
code changes; no contract bump required. Original per-dim files are
preserved in git history at parent commits.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/homeostasis.md``
§ "Dimension enumeration".
"""

from __future__ import annotations

import ast
import re
from collections.abc import Iterable
from pathlib import Path
from typing import ClassVar

from myco.core.identity_cluster import MycoContext, MycoError, Severity
from myco.core.io_cluster import bounded_read_text, should_skip_dir
from myco.homeostasis.primitives_cluster import Category, Dimension, Finding

__all__ = [
    "MP1NoProviderImports",
    "MP2PluginProviderImports",
    "MP3PluginBytecodeAudit",
]


# =========================================================================
# MP1 — see module docstring + original git history at parent commits
# =========================================================================


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


# =========================================================================
# MP2 — see module docstring + original git history at parent commits
# =========================================================================


class MP2PluginProviderImports(Dimension):
    """Substrate-local plugins under ``.myco/plugins/`` import no LLM SDK."""

    id = "MP2"
    category = Category.MECHANICAL
    default_severity = Severity.MEDIUM
    fixable: ClassVar[bool] = False

    #: Reuse the MP1 blacklist verbatim — whatever the kernel isn't
    #: allowed to import, a plugin isn't allowed to import either.
    BLACKLIST: ClassVar[frozenset[str]] = MP1NoProviderImports.BLACKLIST

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        plugins_dir = ctx.substrate.root / ".myco" / "plugins"
        if not plugins_dir.is_dir():
            return
        system = ctx.substrate.canon.system or {}
        declared_no_llm = bool(system.get("no_llm_in_substrate", True))
        severity = Severity.MEDIUM if declared_no_llm else Severity.LOW
        for py_file in sorted(plugins_dir.rglob("*.py")):
            if self._should_skip(py_file):
                continue
            for rel_path, line, imported in self._scan_file(py_file, ctx):
                yield Finding(
                    dimension_id=self.id,
                    category=self.category,
                    severity=severity,
                    message=(
                        f"plugin file imports LLM provider SDK "
                        f"{imported!r} (L0 principle 1: agents call "
                        f"LLMs; the substrate — including its plugins "
                        f"— does not)."
                    ),
                    path=rel_path,
                    line=line,
                )

    @staticmethod
    def _should_skip(py_file: Path) -> bool:
        for part in py_file.parts:
            if part == "__pycache__":
                return True
            # Allow ``.myco`` itself; only reject other hidden dirs.
            if part.startswith(".") and part not in {".", "..", ".myco"}:
                return True
        return False

    def _scan_file(
        self, py_file: Path, ctx: MycoContext
    ) -> Iterable[tuple[str, int, str]]:
        try:
            source = bounded_read_text(py_file)
        except (OSError, UnicodeDecodeError, MycoError):
            return
        try:
            tree = ast.parse(source, filename=str(py_file))
        except SyntaxError:
            return
        try:
            rel_path = py_file.relative_to(ctx.substrate.root).as_posix()
        except ValueError:
            rel_path = py_file.as_posix()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if MP1NoProviderImports._matches_blacklist(alias.name):
                        yield (rel_path, node.lineno, alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.level and node.level > 0:
                    continue
                mod = node.module
                if mod is None:
                    continue
                if MP1NoProviderImports._matches_blacklist(mod):
                    yield (rel_path, node.lineno, mod)


# =========================================================================
# MP3 — see module docstring + original git history at parent commits
# =========================================================================

_SUSPICIOUS_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"importlib\.import_module\(\s*['\"](openai|anthropic|google\.generativeai|cohere|mistralai)"
    ),
    re.compile(
        r"__import__\(\s*['\"](openai|anthropic|google\.generativeai|cohere|mistralai)"
    ),
)


class MP3PluginBytecodeAudit(Dimension):
    """Plugin trees must not dynamically import LLM provider SDKs."""

    id = "MP3"
    category = Category.MECHANICAL
    default_severity = Severity.HIGH
    fixable: ClassVar[bool] = False

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        plugin_root = ctx.substrate.root / ".myco" / "plugins"
        if not plugin_root.is_dir():
            return
        for path in plugin_root.rglob("*.py"):
            if any(should_skip_dir(p.name) for p in path.parents):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            for pat in _SUSPICIOUS_PATTERNS:
                m = pat.search(text)
                if m:
                    rel = path.relative_to(ctx.substrate.root).as_posix()
                    yield Finding(
                        dimension_id=self.id,
                        category=self.category,
                        severity=self.default_severity,
                        message=(
                            f"plugin uses dynamic LLM-SDK import "
                            f"({m.group(0)[:60]}...); plugins must not "
                            f"call provider SDKs (L0 P1)"
                        ),
                        path=rel,
                    )
                    break
