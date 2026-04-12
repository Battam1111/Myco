#!/usr/bin/env python3
"""
Myco Knowledge System — Automated 23-Dimension Substrate Immune System.

The canonical dimension count is `len(FULL_CHECKS)` (computed at module load
time, see bottom of this file). This docstring's dimension table below is a
maintainer-facing index, not the source of truth — when a new dimension
lands, FULL_CHECKS auto-updates and L19 enforces that every downstream cache
(README badges, MYCO.md headlines, mcp_server.py tool
description, cli.py help strings, etc.) tracks it.

Dimensions:
    L0  Canon Self-Check — _canon.yaml contains all required keys
    L1  Reference Integrity — indexed files exist, cross-references valid
    L2  Number Consistency — key numbers match _canon.yaml, stale patterns detected
    L3  Stale Pattern Scan — search for known outdated phrases
    L4  Orphan Detection — wiki pages not referenced in any index
    L5  log.md Coverage — format and entry type validation
    L6  Date Consistency — header dates vs file modification times
    L7  Wiki W8 Format — header (type + date) + footer (Back to) template compliance
    L8  .original Sync — compressed file timestamp consistency (v2.5)
    L9  Vision Anchor — identity-element drift detection (v0.1.1)
    L10 Notes Schema — atomic-note frontmatter validation (v0.2.0)
    L11 Write Surface — _canon.yaml write_surface whitelist (v0.2.0)
    L12 Upstream Dotfile Hygiene — .myco_upstream_{outbox,inbox}/ rules (v0.2.0)
    L13 Craft Protocol Schema — docs/primordia/*_craft_*.md frontmatter (v0.3.0, W3)
    L14 Forage Hygiene — forage/_index.yaml manifest + files (v0.7.0)
    L15 Craft Reflex — trigger-surface touches must cite craft evidence (v0.10.0, W3)
    L16 Boot Brief Freshness — .myco_state/boot_brief.md mtime sanity (Wave 21, v0.20.0)
    L17 Contract Drift — synced_contract_version vs kernel contract_version (Wave 24, v0.23.0)
    L18 Compression Integrity — forward-compression bidirectional link audit (Wave 30, v0.26.0)
    L19 Lint Dimension Count Consistency — downstream-cache drift detection (Wave 38, v0.29.0)
    L20 Translation Mirror Consistency — locale README skeleton parity (Wave 39, v0.30.0)
    L21 Contract Version Inline Consistency — forward-looking inline contract version SSoT (Wave 40, v0.31.0)
    L22 Wave-Seed Lifecycle — raw wave-seed orphan detection (seven-step pipeline post-condition, Wave 41, v0.32.0)
"""

import os
import re
import sys
import glob
from pathlib import Path
from datetime import datetime
from collections import defaultdict

try:
    import yaml
except ImportError:
    yaml = None


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

class C:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    END = "\033[0m"


def red(s):    return f"{C.RED}{s}{C.END}"
def green(s):  return f"{C.GREEN}{s}{C.END}"
def yellow(s): return f"{C.YELLOW}{s}{C.END}"
def cyan(s):   return f"{C.CYAN}{s}{C.END}"
def bold(s):   return f"{C.BOLD}{s}{C.END}"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_canon(root: Path):
    if yaml is None:
        print(red("FATAL: PyYAML not installed. Run: pip install pyyaml"))
        sys.exit(1)
    canon_path = root / "_canon.yaml"
    if not canon_path.exists():
        print(red("FATAL: _canon.yaml not found at project root!"))
        sys.exit(1)
    with open(canon_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_entry_point(canon):
    """Get entry point filename from _canon.yaml or default to MYCO.md"""
    system = canon.get("system", {})
    return system.get("entry_point", "MYCO.md")


def read_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None


def find_files(pattern, root):
    return sorted(glob.glob(str(root / pattern), recursive=True))


# ---------------------------------------------------------------------------
# L0: Canon Self-Check
# ---------------------------------------------------------------------------

def lint_canon_schema(canon, root):
    issues = []
    universal_required = {
        "system.principles_count": ["system", "principles_count"],
        "architecture.layers": ["architecture", "layers"],
        "architecture.wiki_pages": ["architecture", "wiki_pages"],
    }
    for key_path, path_parts in universal_required.items():
        val = canon
        for part in path_parts:
            if isinstance(val, dict):
                val = val.get(part)
            else:
                val = None
                break
        if val is None:
            issues.append(("L0", "CRITICAL", "_canon.yaml",
                           f"Missing required key: {key_path}"))
    return issues


# ---------------------------------------------------------------------------
# L1: Reference Integrity
# ---------------------------------------------------------------------------

def lint_references(canon, root):
    """L1 Reference Integrity.

    v0.9.0 (ASCC 3356 friction): skip backtick-enclosed paths that
    appear in explicit *negative* or *example* context — these are
    documentation references to files the agent must NOT create, or
    external kernel paths being cited for explanation. The previous
    scanner only skipped glob/absolute paths, producing false HIGH
    errors when the entry document included a "forbidden list" of
    paths. Context-aware skip rules:

      1. Path appears within a fenced code block (```...```) whose
         opening fence line contains "example" or "anti-pattern" or "bad"
      2. Same-line negative context within ~40 chars before the backtick:
         one of {"forbid", "must not", "do not", "don't", "never create",
                 "anti-pattern", "example of", "external", "kernel path"}
      3. Path matches canon ``system.l1_exclude_paths`` (explicit allowlist)

    The first two are prose-sniffing heuristics; the third is the
    explicit escape hatch. Authors with edge cases should prefer (3).
    """
    issues = []
    entry_point = get_entry_point(canon)
    entry_file = read_file(root / entry_point)
    if not entry_file:
        issues.append(("L1", "CRITICAL", entry_point, f"Cannot read {entry_point}"))
        return issues

    # Canon-level explicit exclude list (3356 option c — escape hatch)
    l1_exclude_paths = set(
        (canon.get("system", {}) or {}).get("l1_exclude_paths", []) or []
    )

    # Precompute "safe-context" line starts: within an example/anti-pattern
    # fenced code block.
    lines = entry_file.split("\n")
    in_example_fence = False
    example_fence_lines = set()
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith("```"):
            fence_label = stripped[3:].lower()
            if not in_example_fence and any(
                kw in fence_label for kw in ("example", "anti-pattern", "bad")
            ):
                in_example_fence = True
            elif in_example_fence:
                in_example_fence = False
            continue
        if in_example_fence:
            example_fence_lines.add(i)

    # Negative-context keywords (lowercased substring match in preceding window)
    NEG_KEYWORDS = (
        "forbid", "must not", "do not", "don't", "never create",
        "anti-pattern", "example of", "external", "kernel path",
        "do NOT", "MUST NOT",
    )

    # Iterate with match positions so we can inspect surrounding context.
    ref_re = re.compile(
        r"`([a-zA-Z_/][a-zA-Z0-9_/\-.*]+\.(?:md|py|sh|yaml|txt))`"
    )
    for match in ref_re.finditer(entry_file):
        ref = match.group(1)
        if "*" in ref or ref.startswith("/"):
            continue
        if ref in l1_exclude_paths:
            continue

        # Fenced-example skip
        line_idx = entry_file[:match.start()].count("\n")
        if line_idx in example_fence_lines:
            continue

        # Same-line negative-context skip (window of 40 chars before backtick)
        line_start = entry_file.rfind("\n", 0, match.start()) + 1
        preceding = entry_file[line_start:match.start()].lower()
        if any(kw.lower() in preceding for kw in NEG_KEYWORDS):
            continue

        path = root / ref
        if not path.exists():
            issues.append(("L1", "HIGH", entry_point,
                           f"Referenced file missing: {ref}"))

    for wiki_file in find_files("wiki/*.md", root):
        content = read_file(wiki_file)
        if not content:
            continue
        links = re.findall(r"\[.*?\]\((\.\.?/[^)]+)\)", content)
        for link in links:
            target = (Path(wiki_file).parent / link).resolve()
            if not target.exists():
                rel = str(Path(wiki_file).relative_to(root))
                issues.append(("L1", "HIGH", rel,
                               f"Broken cross-reference: {link}"))
    return issues


# ---------------------------------------------------------------------------
# L2: Number Consistency
# ---------------------------------------------------------------------------

def lint_numbers(canon, root):
    issues = []
    stale_patterns = []
    system = canon.get("system", {})
    if isinstance(system.get("stale_patterns"), list):
        stale_patterns = system["stale_patterns"]
    if not stale_patterns:
        return issues

    entry_point = get_entry_point(canon)
    active_files = []
    for pattern in [entry_point, "docs/WORKFLOW.md", "wiki/*.md"]:
        active_files.extend(find_files(pattern, root))

    for filepath in active_files:
        content = read_file(filepath)
        if not content:
            continue
        rel = str(Path(filepath).relative_to(root))
        for sp in stale_patterns:
            for match in re.finditer(re.escape(sp), content):
                start = max(0, match.start() - 40)
                end = min(len(content), match.end() + 40)
                ctx = content[start:end].replace("\n", " ").strip()
                if any(kw in ctx for kw in ["→", "改为", "stale", "过时",
                                             "exception", "pattern", "已知"]):
                    continue
                line_num = content[:match.start()].count("\n") + 1
                issues.append(("L2", "MEDIUM", f"{rel}:{line_num}",
                               f"Stale pattern '{sp}': ...{ctx}..."))
    return issues


# ---------------------------------------------------------------------------
# L3: Stale Section References
# ---------------------------------------------------------------------------

def lint_stale_patterns(canon, root):
    issues = []
    valid_sections = set(canon.get("system", {}).get("valid_sections", [0, 1, 2, 3, 4, 5]))
    entry_point = get_entry_point(canon)
    entry_point_safe = entry_point.replace(".", r"\.")
    stale_section_pattern = fr"{entry_point_safe}\s*§(\d+)"

    active_files = []
    for pattern in ["docs/WORKFLOW.md", "wiki/*.md"]:
        active_files.extend(find_files(pattern, root))

    for filepath in active_files:
        content = read_file(filepath)
        if not content:
            continue
        rel = str(Path(filepath).relative_to(root))
        for match in re.finditer(stale_section_pattern, content):
            section_num = int(match.group(1))
            if section_num not in valid_sections:
                start = max(0, match.start() - 10)
                end = min(len(content), match.end() + 30)
                ctx = content[start:end].replace("\n", " ").strip()
                line_num = content[:match.start()].count("\n") + 1
                issues.append(("L3", "HIGH", f"{rel}:{line_num}",
                               f"Stale section ref '{entry_point} §{section_num}': ...{ctx}..."))
    return issues


# ---------------------------------------------------------------------------
# L4: Orphan Detection
# ---------------------------------------------------------------------------

def lint_orphans(canon, root):
    issues = []
    entry_point = get_entry_point(canon)
    entry_content = read_file(root / entry_point) or ""
    for wiki_file in find_files("wiki/*.md", root):
        name = Path(wiki_file).name
        # README.md in wiki/ is a directory charter, not a wiki page — skip.
        if name.lower() == "readme.md":
            continue
        rel = str(Path(wiki_file).relative_to(root))
        if rel not in entry_content and name not in entry_content:
            issues.append(("L4", "MEDIUM", rel,
                           f"Wiki page not referenced in {entry_point}"))
    return issues


# ---------------------------------------------------------------------------
# L5: log.md Coverage
# ---------------------------------------------------------------------------

def lint_log(canon, root):
    issues = []
    log_content = read_file(root / "log.md")
    if not log_content:
        issues.append(("L5", "HIGH", "log.md", "log.md not found or empty"))
        return issues

    entry_pattern = re.compile(r"^## \[(\d{4}-\d{2}-\d{2})\] (\w+) \| (.+)$")
    valid_types = {"milestone", "decision", "debug", "deploy", "debate", "system",
                   "friction", "meta", "contradiction", "validation", "script",
                   "document", "analysis", "progress"}

    prev_date = None
    entry_count = 0
    for i, line in enumerate(log_content.split("\n"), 1):
        if line.startswith("## ["):
            m = entry_pattern.match(line)
            if not m:
                issues.append(("L5", "MEDIUM", "log.md",
                               f"Line {i}: malformed entry: {line[:60]}..."))
                continue
            date_str, entry_type, _ = m.groups()
            entry_count += 1
            if entry_type not in valid_types:
                issues.append(("L5", "LOW", "log.md",
                               f"Line {i}: unknown type '{entry_type}'"))
            if prev_date and date_str < prev_date:
                issues.append(("L5", "MEDIUM", "log.md",
                               f"Line {i}: date {date_str} before previous {prev_date}"))
            prev_date = date_str

    if entry_count == 0:
        issues.append(("L5", "HIGH", "log.md", "No entries found"))
    return issues


# ---------------------------------------------------------------------------
# L6: Date Consistency
# ---------------------------------------------------------------------------

def lint_dates(canon, root):
    issues = []
    entry_point = get_entry_point(canon)
    for rel_path in [entry_point, "docs/WORKFLOW.md"]:
        filepath = root / rel_path
        content = read_file(filepath)
        if not content:
            continue
        m = re.search(r"最后更新[：:]\s*(\d{4}-\d{2}-\d{2})", content)
        if not m:
            issues.append(("L6", "LOW", rel_path, "No date header found"))
    return issues


# ---------------------------------------------------------------------------
# L7: Wiki W8 Format
# ---------------------------------------------------------------------------

def lint_wiki_format(canon, root):
    issues = []
    valid_types = set(canon.get("system", {}).get("wiki_page_types",
                      ["entity", "concept", "operations", "analysis", "craft"]))
    for wiki_file in find_files("wiki/*.md", root):
        # README.md in wiki/ is a directory charter, not a W8 page — skip.
        if Path(wiki_file).name.lower() == "readme.md":
            continue
        content = read_file(wiki_file)
        if not content:
            continue
        rel = str(Path(wiki_file).relative_to(root))
        lines = content.split("\n")
        header = "\n".join(lines[:15])

        type_match = re.search(r"\*\*类型\*\*[：:]\s*(\w+)", header)
        if not type_match:
            issues.append(("L7", "MEDIUM", rel, "Missing W8 header: **类型**"))
        elif type_match.group(1) not in valid_types:
            issues.append(("L7", "LOW", rel,
                           f"Unknown wiki type '{type_match.group(1)}'"))

        if not re.search(r"\*\*最后更新\*\*[：:]", header):
            issues.append(("L7", "MEDIUM", rel, "Missing W8 header: **最后更新**"))

        footer = "\n".join(lines[-10:])
        if "**Back to**" not in footer:
            issues.append(("L7", "MEDIUM", rel, "Missing W8 footer: **Back to**"))
    return issues


# ---------------------------------------------------------------------------
# L8: .original Sync (v2.5)
# ---------------------------------------------------------------------------

_FRONTMATTER_RE = re.compile(
    r"^---\s*\n(?P<fm>.*?\n)---\s*\n(?P<body>.*)$",
    re.DOTALL,
)


def lint_vision_anchors(canon, root):
    """L9 — ensure public-facing files contain lexical anchors for every
    identity element declared in _canon.yaml → system.vision_anchors.

    Converts the 2026-04-10 vision-drift recovery into a permanent
    structural safeguard. Authoritative source:
        docs/primordia/vision_recovery_craft_2026-04-10.md §7
    """
    issues = []
    va = canon.get("system", {}).get("vision_anchors")
    if not va:
        return issues

    targets = va.get("targets", []) or []
    groups = va.get("groups", []) or []
    min_hits = int(va.get("min_hits_per_file", 1))
    if not targets or not groups:
        return issues

    for rel_path in targets:
        content = read_file(root / rel_path)
        if content is None:
            issues.append(("L9", "HIGH", rel_path,
                           "Vision-anchor target file not found"))
            continue
        for group in groups:
            name = group.get("name", "?")
            variants = group.get("any_of", []) or []
            hits = sum(content.count(v) for v in variants)
            if hits < min_hits:
                sample = " | ".join(variants[:4])
                issues.append(("L9", "CRITICAL", rel_path,
                               f"Vision anchor missing: group '{name}' "
                               f"(none of: {sample})"))
    return issues


def lint_notes_schema(canon, root):
    """L10 — validate every notes/*.md against the schema in _canon.yaml.

    Single source of truth as of contract v0.6.0 (Wave 6 de-dup).
    scripts/lint_knowledge.py is a shim that delegates to this module.
    """
    issues = []
    schema = canon.get("system", {}).get("notes_schema")
    if not schema:
        return issues

    notes_dir = root / schema.get("dir", "notes")
    if not notes_dir.exists():
        return issues

    required_fields = schema.get("required_fields", []) or []
    valid_statuses = set(schema.get("valid_statuses", []) or [])
    valid_sources = set(schema.get("valid_sources", []) or [])
    filename_re = re.compile(schema.get("filename_pattern", r".*\.md$"))
    id_re = re.compile(r"^n_\d{8}T\d{6}_[0-9a-f]{4}$")

    for path in sorted(notes_dir.glob("*.md")):
        rel = str(path.relative_to(root))
        name = path.name

        # Skip non-note files (e.g. README.md) — only n_* files count.
        if not name.startswith("n_"):
            continue

        if not filename_re.match(name):
            issues.append(("L10", "MEDIUM", rel,
                           "Filename does not match schema pattern"))
            continue

        content = read_file(path)
        if content is None:
            issues.append(("L10", "HIGH", rel, "Cannot read notes file"))
            continue

        m = _FRONTMATTER_RE.match(content)
        if not m:
            issues.append(("L10", "CRITICAL", rel,
                           "Missing YAML frontmatter block"))
            continue

        try:
            meta = yaml.safe_load(m.group("fm")) or {}
        except Exception as e:
            issues.append(("L10", "CRITICAL", rel,
                           f"Malformed frontmatter YAML: {e}"))
            continue
        if not isinstance(meta, dict):
            issues.append(("L10", "CRITICAL", rel,
                           "Frontmatter is not a mapping"))
            continue

        for field in required_fields:
            if field not in meta:
                issues.append(("L10", "HIGH", rel,
                               f"Missing required field: {field}"))

        status = meta.get("status")
        if valid_statuses and status is not None and status not in valid_statuses:
            issues.append(("L10", "HIGH", rel,
                           f"Invalid status {status!r}"))

        source = meta.get("source")
        if valid_sources and source is not None and source not in valid_sources:
            issues.append(("L10", "MEDIUM", rel,
                           f"Invalid source {source!r}"))

        if meta.get("tags") is not None and not isinstance(meta.get("tags"), list):
            issues.append(("L10", "MEDIUM", rel, "tags must be a list"))
        if meta.get("digest_count") is not None and not isinstance(meta.get("digest_count"), int):
            issues.append(("L10", "MEDIUM", rel, "digest_count must be integer"))
        if meta.get("promote_candidate") is not None and not isinstance(meta.get("promote_candidate"), bool):
            issues.append(("L10", "MEDIUM", rel, "promote_candidate must be boolean"))

        nid = meta.get("id")
        if nid is not None and not id_re.match(str(nid)):
            issues.append(("L10", "MEDIUM", rel,
                           f"id {nid!r} does not match n_YYYYMMDDTHHMMSS_xxxx"))

        if status == "excreted" and not meta.get("excrete_reason"):
            issues.append(("L10", "HIGH", rel,
                           "excreted notes must have a non-empty excrete_reason"))

        if nid and path.stem != nid:
            issues.append(("L10", "MEDIUM", rel,
                           f"filename stem {path.stem!r} != id {nid!r}"))

        # Wave 35 (v0.27.0) — soft inlet provenance check.
        # When source=='inlet', the 4 inlet_* fields SHOULD be present.
        # Severity LOW (warn, not error) so existing notes that get
        # retroactively retagged source=inlet aren't broken; the lint
        # surfaces the gap without blocking the substrate.
        if source == "inlet":
            for fld in (
                "inlet_origin",
                "inlet_method",
                "inlet_fetched_at",
                "inlet_content_hash",
            ):
                if fld not in meta or meta.get(fld) in (None, ""):
                    issues.append(("L10", "LOW", rel,
                                   f"source=inlet missing provenance field: {fld}"))

    return issues


def lint_original_sync(canon, root):
    issues = []
    for orig_path in root.rglob("*.original.md"):
        rel_orig = str(orig_path.relative_to(root))
        compressed = Path(str(orig_path).replace(".original.md", ".md"))
        if not compressed.exists():
            issues.append(("L8", "HIGH", rel_orig,
                           "No compressed version found"))
            continue
        if orig_path.stat().st_mtime > compressed.stat().st_mtime:
            issues.append(("L8", "MEDIUM", rel_orig,
                           "Original newer than compressed — run compress_original.py"))
        comp_content = read_file(compressed)
        if comp_content and "auto-compressed from .original.md" not in comp_content:
            rel_comp = str(compressed.relative_to(root))
            issues.append(("L8", "LOW", rel_comp,
                           "Compressed file missing auto-compressed marker"))
    return issues


# ---------------------------------------------------------------------------
# L11: Write Surface — enforce agent write-target whitelist
# ---------------------------------------------------------------------------

def _ws_allowed_match(name, allowed):
    for pat in allowed:
        pat = pat.rstrip("/")
        if name == pat:
            return True
    return False


def _ws_gitignored_names(root):
    names = set()
    gi = root / ".gitignore"
    if not gi.exists():
        return names
    try:
        for line in gi.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("./"):
                line = line[2:]
            if line.endswith("/"):
                line = line[:-1]
            if "/" in line or "*" in line or "?" in line or "[" in line:
                continue
            names.add(line)
    except OSError:
        pass
    return names


def lint_write_surface(canon, root):
    """Enforce _canon.yaml → system.write_surface.

    Authoritative contract: docs/agent_protocol.md §1. Single source of
    truth as of contract v0.6.0 — scripts/lint_knowledge.py is a shim.
    """
    issues = []
    ws = canon.get("system", {}).get("write_surface")
    if not ws:
        return issues

    allowed = ws.get("allowed", []) or []
    forbidden = set(ws.get("forbidden_top_level", []) or [])
    gitignored = _ws_gitignored_names(root)

    try:
        top_entries = sorted(os.listdir(root))
    except OSError:
        return issues

    for name in top_entries:
        if name.startswith("."):
            continue
        if name in {"__pycache__", "build", "node_modules", "venv", "env"}:
            continue
        if name.endswith(".egg-info"):
            continue

        if name in forbidden or (name + "/") in forbidden:
            issues.append(("L11", "CRITICAL", name,
                           "Forbidden top-level entry (anti-pattern). "
                           "See docs/agent_protocol.md §1."))
            continue

        if name in gitignored:
            continue

        if not _ws_allowed_match(name, allowed):
            issues.append(("L11", "HIGH", name,
                           "Top-level entry not in write_surface.allowed. "
                           "If legitimate, add to _canon.yaml; otherwise "
                           "remove or move into an allowed location."))

    notes_dir = root / "notes"
    if notes_dir.exists() and notes_dir.is_dir():
        for path in sorted(notes_dir.iterdir()):
            if path.is_dir():
                issues.append(("L11", "HIGH", f"notes/{path.name}/",
                               "notes/ must be flat — no subdirectories"))
                continue
            nm = path.name
            if nm == "README.md":
                continue
            if not (nm.startswith("n_") and nm.endswith(".md")):
                issues.append(("L11", "HIGH", f"notes/{nm}",
                               "Non-note file in notes/ — use `myco eat` "
                               "instead of hand-writing files here."))

    wiki_dir = root / "wiki"
    if wiki_dir.exists() and wiki_dir.is_dir():
        for path in sorted(wiki_dir.rglob("*")):
            if path.is_file() and path.suffix not in {".md", ""}:
                rel = path.relative_to(root)
                issues.append(("L11", "MEDIUM", str(rel),
                               "wiki/ should contain markdown only"))

    return issues


def lint_dotfile_hygiene(canon, root):
    """L12 — Upstream transport dotfile dir hygiene.

    Upstream Protocol v1.0 (docs/agent_protocol.md §8.5) defines two
    transport directories at the repo root:

      - ``.myco_upstream_outbox/``  (instance → kernel)
      - ``.myco_upstream_inbox/``   (kernel side; receives absorbed bundles)

    Contract v0.9.0 (Wave 9, docs/primordia/upstream_absorb_craft_2026-04-11.md)
    adds the kernel-side ``absorbed/`` subdirectory under
    ``.myco_upstream_inbox/`` as the canonical evidence archive written by
    ``myco upstream ingest``.

    Rules:
      1. If either outer dir exists, every *file* inside MUST match one of
         the two accepted bundle-filename patterns:
           - outbox side:  ``n_YYYYMMDDTHHMMSS_<hex>.bundle.(yaml|yml|json)``
           - inbox side:   ``<absorb_ts>_n_YYYYMMDDTHHMMSS_<hex>.bundle.(yaml|yml|json)``
         ``README.md`` in either dir is always allowed.
      2. Only one subdirectory is allowed, and only on the inbox side:
         ``.myco_upstream_inbox/absorbed/`` — files inside it must match
         the inbox-side bundle pattern.
      3. Files older than 30 days produce a LOW-severity GC reminder
         (inbox side: only for items still in the root, not in absorbed/).
      4. Any OTHER ``.myco_*`` top-level dir is HIGH (reserved namespace).
    """
    import re as _re
    import time as _time

    issues = []

    OUTBOX_BUNDLE_RE = _re.compile(
        r"^n_\d{8}T\d{6}_[0-9a-f]+\.bundle\.(yaml|yml|json)$"
    )
    INBOX_BUNDLE_RE = _re.compile(
        r"^\d{8}T\d{6}_n_\d{8}T\d{6}_[0-9a-f]+\.bundle\.(yaml|yml|json)$"
    )
    # Wave 17 (contract v0.16.0): .myco_state/ added as boot brief
    # cache dir. See docs/primordia/boot_brief_injector_craft_2026-04-11.md.
    ALLOWED_DIRS = {
        ".myco_upstream_outbox",
        ".myco_upstream_inbox",
        ".myco_state",
    }
    ALLOWED_SUBDIRS = {
        ".myco_upstream_inbox": {"absorbed"},
        ".myco_upstream_outbox": set(),
        ".myco_state": set(),
    }
    # Wave 17: .myco_state/ files match any .md or .json name — no
    # bundle-pattern constraint. We validate extension only.
    STATE_ALLOWED_EXTS = {".md", ".json", ".db"}  # .db added Wave 52 (sessions.db)
    thirty_days = 30 * 86400
    now = _time.time()

    def _choose_pattern(top_dir_name: str):
        if top_dir_name == ".myco_upstream_outbox":
            return OUTBOX_BUNDLE_RE, ("n_YYYYMMDDTHHMMSS_<hex>"
                                       ".bundle.(yaml|yml|json)")
        return INBOX_BUNDLE_RE, ("<absorb_ts>_n_YYYYMMDDTHHMMSS_<hex>"
                                  ".bundle.(yaml|yml|json)")

    try:
        for name in sorted(os.listdir(root)):
            if not name.startswith(".myco_"):
                continue
            full = root / name
            if not full.is_dir():
                continue
            if name not in ALLOWED_DIRS:
                issues.append(("L12", "HIGH", name + "/",
                               "Unknown .myco_* top-level dir. "
                               "Only .myco_upstream_outbox/, "
                               ".myco_upstream_inbox/, and "
                               ".myco_state/ are reserved. "
                               "See docs/agent_protocol.md §8.5."))
                continue

            # Wave 17 (v0.16.0): .myco_state/ has its own validation
            # path — any .md/.json file allowed, no nested dirs.
            if name == ".myco_state":
                for child in sorted(full.iterdir()):
                    if child.is_dir():
                        issues.append((
                            "L12", "HIGH",
                            f"{name}/{child.name}/",
                            f"{name}/ must be flat — no subdirectories "
                            "(Wave 17 boot brief cache)."))
                        continue
                    if child.name == "README.md":
                        continue
                    if child.suffix not in STATE_ALLOWED_EXTS:
                        issues.append((
                            "L12", "MEDIUM",
                            f"{name}/{child.name}",
                            f"{name}/ allows only "
                            f"{sorted(STATE_ALLOWED_EXTS)} files — "
                            f"found {child.suffix or '<no ext>'}."))
                continue

            pattern, pattern_hint = _choose_pattern(name)
            allowed_subdirs = ALLOWED_SUBDIRS.get(name, set())

            for child in sorted(full.iterdir()):
                if child.is_dir():
                    if child.name in allowed_subdirs:
                        # Validate inbox/absorbed/ contents with the
                        # inbox-side bundle pattern.
                        for grandchild in sorted(child.iterdir()):
                            if grandchild.is_dir():
                                issues.append((
                                    "L12", "HIGH",
                                    f"{name}/{child.name}/{grandchild.name}/",
                                    f"{name}/{child.name}/ must be flat — "
                                    "no nested directories"))
                                continue
                            if grandchild.name == "README.md":
                                continue
                            if not INBOX_BUNDLE_RE.match(grandchild.name):
                                issues.append((
                                    "L12", "HIGH",
                                    f"{name}/{child.name}/{grandchild.name}",
                                    "Archived bundle filename does not "
                                    "match <absorb_ts>_n_YYYYMMDDTHHMMSS_"
                                    "<hex>.bundle.(yaml|yml|json). "
                                    "See docs/agent_protocol.md §8.5.1."))
                        continue
                    issues.append(("L12", "HIGH", f"{name}/{child.name}/",
                                   f"{name}/ allows only these subdirs: "
                                   f"{sorted(allowed_subdirs) or '(none)'}"))
                    continue
                if child.name == "README.md":
                    continue
                if not pattern.match(child.name):
                    issues.append(("L12", "HIGH", f"{name}/{child.name}",
                                   f"Filename does not match {pattern_hint}. "
                                   "See docs/agent_protocol.md §8.5.1."))
                    continue
                try:
                    age = now - child.stat().st_mtime
                    if age > thirty_days:
                        days = int(age // 86400)
                        issues.append(("L12", "LOW", f"{name}/{child.name}",
                                       f"Upstream transport file is {days} days "
                                       "old — consider GC or promotion."))
                except OSError:
                    pass
    except OSError:
        return issues

    return issues


def _l13_body_metrics(content, round_markers):
    """L13 body metrics helper — Wave 15 (contract v0.14.0).

    Parse a craft body and return
    (body_chars, unique_round_numbers, per_round_chars) where:
        body_chars           — non-whitespace char count of body after frontmatter
        unique_round_numbers — list of unique round numbers detected across
                               round_marker regexes on top-level `^## ` headings
        per_round_chars      — dict {round_number: char_count} measuring
                               non-whitespace chars from each round heading
                               to the next top-level heading. Duplicate
                               anchors for the same round number sum.

    Called from lint_craft_protocol. Standalone for testability.
    See docs/primordia/l13_body_schema_craft_2026-04-11.md.
    """
    # Strip frontmatter if present
    m = _FRONTMATTER_RE.match(content)
    body = m.group("body") if m else content

    # Compile marker regexes (ignore invalid ones silently)
    compiled = []
    for pat in round_markers or []:
        try:
            compiled.append(re.compile(pat))
        except re.error:
            continue

    # Chinese numeral → int (best-effort; falls back to int(str))
    _cn_map = {
        "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
        "六": 6, "七": 7, "八": 8, "九": 9, "十": 10,
    }

    def _parse_num(raw: str):
        s = raw.strip()
        if s.isdigit():
            return int(s)
        if len(s) == 1 and s in _cn_map:
            return _cn_map[s]
        if s == "十":
            return 10
        # e.g. "十一" = 11, "二十" = 20 — simple two-char combinations
        if len(s) == 2:
            a, b = s[0], s[1]
            if a == "十" and b in _cn_map:
                return 10 + _cn_map[b]
            if a in _cn_map and b == "十":
                return _cn_map[a] * 10
            if a in _cn_map and b in _cn_map:
                return _cn_map[a] * 10 + _cn_map[b] if a != "十" else 10 + _cn_map[b]
        return None

    lines = body.splitlines()
    round_anchors = []  # list of (line_idx, round_number)
    for i, line in enumerate(lines):
        if not line.startswith("## "):
            continue
        for cre in compiled:
            m2 = cre.search(line)
            if m2:
                raw = m2.group(1) if m2.groups() else ""
                num = _parse_num(raw)
                if num is not None:
                    round_anchors.append((i, num))
                    break  # first pattern wins for this line

    unique_rounds = sorted({n for _, n in round_anchors})

    # Per-round slice: for each anchor, count non-whitespace chars from
    # its line to the next top-level `## ` heading (exclusive).
    per_round_chars = {}
    # Top-level heading positions for slice boundaries
    h2_positions = [i for i, l in enumerate(lines) if l.startswith("## ")]
    for idx, rnum in round_anchors:
        try:
            next_h = next(p for p in h2_positions if p > idx)
        except StopIteration:
            next_h = len(lines)
        slice_text = "\n".join(lines[idx:next_h])
        chars = len("".join(slice_text.split()))
        # For duplicate round numbers across anchors, sum
        per_round_chars[rnum] = per_round_chars.get(rnum, 0) + chars

    body_chars = len("".join(body.split()))
    return body_chars, unique_rounds, per_round_chars


def lint_craft_protocol(canon, root):
    """L13 — Craft Protocol Schema (W3, v0.3.0 + Wave 15 body schema).

    Enforces docs/craft_protocol.md frontmatter schema on any file in
    docs/primordia/ matching the craft filename pattern AND declaring
    craft_protocol_version: 1. Files without craft_protocol_version are
    grandfathered (see docs/craft_protocol.md §6) and skipped entirely.

    Wave 15 (contract v0.14.0) adds body-schema checks (partial closure
    of craft_protocol.md §7 #3):
        HIGH  — body_chars < declared * min_body_chars_per_round
        HIGH  — 0 < body_rounds < declared  (declaration lie)
        MEDIUM — body_rounds == 0 and declared > 0  (style nudge)
        MEDIUM — per-round slice chars < min_round_body_chars
    See docs/primordia/l13_body_schema_craft_2026-04-11.md.

    Authoritative schema: _canon.yaml → system.craft_protocol.
    """
    import time as _time

    issues = []
    schema = canon.get("system", {}).get("craft_protocol")
    if not schema:
        return issues  # feature not configured; skip silently

    craft_dir = root / schema.get("dir", "docs/primordia")
    if not craft_dir.exists():
        return issues

    filename_re = re.compile(schema.get("filename_pattern", r".*_craft_.*\.md$"))
    required_fields = schema.get("required_frontmatter", []) or []
    valid_statuses = set(schema.get("valid_statuses", []) or [])
    min_rounds = int(schema.get("min_rounds", 2))
    targets_by_class = schema.get("confidence_targets_by_class", {}) or {}
    stale_days = int(schema.get("stale_active_threshold_days", 30))
    now = _time.time()

    # Wave 15 (contract v0.14.0) — body schema config
    body_schema = schema.get("body_schema") or {}
    body_schema_enabled = bool(body_schema.get("enabled", False))
    body_min_per_round = int(body_schema.get("min_body_chars_per_round", 200))
    body_min_per_round_slice = int(body_schema.get("min_round_body_chars", 150))
    body_round_markers = list(body_schema.get("round_markers") or [])
    body_exempt = set(body_schema.get("exempt_files") or [])

    for path in sorted(craft_dir.glob("*_craft_*.md")):
        rel = str(path.relative_to(root))
        name = path.name

        content = read_file(path)
        if content is None:
            continue

        m = _FRONTMATTER_RE.match(content)
        if not m:
            # No frontmatter → fully grandfathered (see §6). Skip entirely.
            continue

        try:
            meta = yaml.safe_load(m.group("fm")) or {}
        except yaml.YAMLError as e:
            issues.append(("L13", "HIGH", rel,
                           f"Malformed frontmatter YAML: {e}"))
            continue

        if not isinstance(meta, dict):
            continue

        cpv = meta.get("craft_protocol_version")
        if cpv is None:
            continue  # grandfathered
        if cpv != 1:
            continue  # future version unknown to current L13

        if not filename_re.match(name):
            issues.append(("L13", "MEDIUM", rel,
                           "Filename does not match craft pattern"))

        for field in required_fields:
            if field not in meta:
                issues.append(("L13", "HIGH", rel,
                               f"Missing required frontmatter field: {field}"))

        if meta.get("type") not in (None, "craft"):
            issues.append(("L13", "HIGH", rel,
                           f"type must be 'craft', got {meta.get('type')!r}"))

        status = meta.get("status")
        if valid_statuses and status is not None and status not in valid_statuses:
            issues.append(("L13", "HIGH", rel,
                           f"Invalid status {status!r}; expected one of "
                           f"{sorted(valid_statuses)}"))

        rounds = meta.get("rounds")
        if isinstance(rounds, int) and rounds < min_rounds:
            issues.append(("L13", "HIGH", rel,
                           f"rounds={rounds} < min_rounds={min_rounds}"))

        dclass = meta.get("decision_class")
        if dclass is not None and dclass not in targets_by_class:
            issues.append(("L13", "HIGH", rel,
                           f"Unknown decision_class {dclass!r}; "
                           f"expected one of {sorted(targets_by_class)}"))

        target_c = meta.get("target_confidence")
        current_c = meta.get("current_confidence")

        if dclass in targets_by_class and isinstance(target_c, (int, float)):
            floor = float(targets_by_class[dclass])
            if float(target_c) < floor:
                issues.append(("L13", "HIGH", rel,
                               f"target_confidence={target_c} < floor "
                               f"{floor} for decision_class={dclass}"))

        if status in ("ACTIVE", "COMPILED"):
            if isinstance(target_c, (int, float)) and isinstance(current_c, (int, float)):
                if float(current_c) < float(target_c):
                    issues.append(("L13", "HIGH", rel,
                                   f"current_confidence={current_c} < "
                                   f"target_confidence={target_c} "
                                   f"(status={status})"))

        if status == "ACTIVE":
            try:
                age = now - path.stat().st_mtime
                if age > stale_days * 86400:
                    d = int(age // 86400)
                    issues.append(("L13", "LOW", rel,
                                   f"ACTIVE for {d} days — consider COMPILED "
                                   "or SUPERSEDED"))
            except OSError:
                pass

        # --- Wave 15 body schema checks (partial closure of §7 #3) ---
        if (
            body_schema_enabled
            and isinstance(rounds, int)
            and rounds > 0
            and path.name not in body_exempt
        ):
            try:
                body_chars, body_rounds, per_round_chars = _l13_body_metrics(
                    content, body_round_markers
                )
            except Exception as e:
                issues.append(("L13", "LOW", rel,
                               f"body metrics unavailable: {e}"))
            else:
                # HIGH: total body chars below hollow-craft floor
                min_total = rounds * body_min_per_round
                if body_chars < min_total:
                    issues.append(("L13", "HIGH", rel,
                                   f"body_chars={body_chars} < "
                                   f"rounds*min_body_chars_per_round={min_total} "
                                   f"(hollow craft — §7 #3 body floor, Wave 15)"))

                # HIGH: declaration lie (body has detectable rounds but
                # fewer than declared)
                n_body_rounds = len(body_rounds)
                if 0 < n_body_rounds < rounds:
                    issues.append(("L13", "HIGH", rel,
                                   f"body_rounds={n_body_rounds} "
                                   f"({body_rounds}) < declared rounds={rounds} "
                                   f"(frontmatter overstates actual round count)"))

                # MEDIUM: style nudge — declared but no Round headings
                if n_body_rounds == 0 and rounds > 0:
                    issues.append(("L13", "MEDIUM", rel,
                                   f"declared rounds={rounds} but no `Round N` "
                                   f"headings detected in body — consider adding "
                                   f"explicit `## Round N` anchors so L13 body "
                                   f"schema can verify structure (Wave 15)"))

                # MEDIUM: per-round slice below per-round floor
                for rnum, pchars in sorted(per_round_chars.items()):
                    if pchars < body_min_per_round_slice:
                        issues.append(("L13", "MEDIUM", rel,
                                       f"Round {rnum} body_chars={pchars} < "
                                       f"min_round_body_chars="
                                       f"{body_min_per_round_slice} "
                                       f"(thin round — consider expanding attacks)"))

    return issues


def lint_forage_hygiene(canon, root):
    """L14 — Forage Hygiene (v0.7.0).

    Validates the forage/_index.yaml manifest and the filesystem
    layout of the forage/ substrate. Authoritative schema:
    _canon.yaml → system.forage_schema.
    Debate of record: docs/primordia/forage_substrate_craft_2026-04-11.md.

    Checks (per item unless noted):
        - Manifest must be readable YAML (HIGH if malformed).
        - Each item passes forage.validate_item (required fields,
          id pattern, valid status/source_type, digested/absorbed
          imply non-empty digest_target, license present, etc).
        - Per-item size_bytes within max_item_size_bytes (HIGH if over).
        - Total footprint within hard_budget_bytes (HIGH if over;
          total_budget_bytes is a HUNGER soft signal, not a lint error).
        - Orphan local_path: item references a file that does not
          exist under the project root (MEDIUM).
        - Orphan file: file exists under forage/{papers,repos,articles}/
          but no manifest entry references it (LOW).
        - Stale license_checked_at older than license_recheck_days (LOW).
    """
    import time as _time

    issues = []
    schema = canon.get("system", {}).get("forage_schema")
    if not schema:
        return issues  # feature not yet enabled; silent skip

    forage_dir = root / schema.get("dir", "forage")
    if not forage_dir.exists():
        return issues  # nothing to lint

    index_rel = schema.get("index_file", "forage/_index.yaml")
    index_path = root / index_rel
    if not index_path.exists():
        issues.append(("L14", "HIGH", index_rel,
                       "forage/ exists but manifest _index.yaml is missing"))
        return issues

    try:
        raw = yaml.safe_load(index_path.read_text(encoding="utf-8"))
    except Exception as e:
        issues.append(("L14", "HIGH", index_rel,
                       f"Manifest YAML unreadable: {e}"))
        return issues

    if raw is None:
        raw = {"items": []}
    if not isinstance(raw, dict):
        issues.append(("L14", "HIGH", index_rel,
                       "Manifest root must be a mapping"))
        return issues

    items = raw.get("items") or []
    if not isinstance(items, list):
        issues.append(("L14", "HIGH", index_rel,
                       "Manifest 'items' must be a list"))
        return issues

    # Import validator lazily to avoid hard dependency during
    # grandfathered/contractless scenarios.
    try:
        from myco.forage import validate_item as _validate_item
    except Exception:
        _validate_item = None

    max_item = int(schema.get("max_item_size_bytes",
                              DEFAULT := 10 * 1024 * 1024))
    hard_budget = int(schema.get("hard_budget_bytes", 1024 * 1024 * 1024))
    recheck_days = int(schema.get("license_recheck_days", 90))
    now_ts = _time.time()

    total_size = 0
    referenced_paths = set()

    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            issues.append(("L14", "HIGH", index_rel,
                           f"item[{idx}] is not a mapping"))
            continue

        item_id = item.get("id") or f"<item[{idx}]>"
        tag = f"{index_rel}::{item_id}"

        if _validate_item is not None:
            errs = _validate_item(item, schema)
            for e in errs:
                sev = "HIGH"
                # License+quarantine mismatch is HIGH; missing fields HIGH.
                issues.append(("L14", sev, tag, e))

        # Size sanity
        sz = item.get("size_bytes")
        try:
            sz_int = int(sz) if sz is not None else 0
        except (TypeError, ValueError):
            sz_int = 0
        total_size += sz_int
        if sz_int > max_item:
            issues.append(("L14", "HIGH", tag,
                           f"size_bytes={sz_int} > max_item_size_bytes="
                           f"{max_item}"))

        # Orphan local_path
        lp = item.get("local_path") or ""
        if lp:
            abs_lp = (root / lp).resolve()
            if not abs_lp.exists():
                issues.append(("L14", "MEDIUM", tag,
                               f"local_path {lp!r} does not exist on disk"))
            else:
                try:
                    referenced_paths.add(abs_lp)
                except Exception:
                    pass

        # Stale license check
        lcat = item.get("license_checked_at")
        if lcat:
            try:
                from datetime import datetime as _dt
                t = _dt.strptime(str(lcat), "%Y-%m-%dT%H:%M:%S").timestamp()
                if now_ts - t > recheck_days * 86400:
                    d = int((now_ts - t) // 86400)
                    issues.append(("L14", "LOW", tag,
                                   f"license_checked_at is {d} days old "
                                   f"(> {recheck_days}); re-verify license"))
            except Exception:
                pass

    # Total budget — hard cap only
    if total_size > hard_budget:
        issues.append(("L14", "HIGH", index_rel,
                       f"total forage footprint {total_size} bytes > "
                       f"hard_budget_bytes={hard_budget}"))

    # Orphan files on disk (LOW) — a file is covered if it IS a
    # referenced path, OR any of its ancestors is a referenced directory
    # path (this handles the common case where a manifest item points at
    # a cloned repo or extracted paper bundle, not an individual file).
    # Surface: Wave 9 first live multi-repo forage (2026-04-11, f_…_c7ab+).
    referenced_dirs = {p for p in referenced_paths if p.is_dir()}
    for sub in ("papers", "repos", "articles"):
        sub_dir = forage_dir / sub
        if not sub_dir.exists():
            continue
        for p in sub_dir.rglob("*"):
            if not p.is_file():
                continue
            if p.name in (".gitkeep", ".gitignore"):
                continue
            try:
                rp = p.resolve()
                if rp in referenced_paths:
                    continue
                # Covered by an ancestor directory entry in the manifest?
                if any(d in rp.parents for d in referenced_dirs):
                    continue
            except Exception:
                continue
            rel_p = str(p.relative_to(root))
            issues.append(("L14", "LOW", rel_p,
                           "forage file not referenced by manifest — "
                           "orphan; add to _index.yaml or remove"))

    return issues


def lint_craft_reflex(canon, root):
    """L15 — Craft Reflex (W3, v0.10.0).

    Active discovery surface for the craft protocol. Converts passive
    trigger conditions (kernel contract change / public-claim rewrite)
    into an emitted LOW signal when a listed surface was touched inside
    the lookback window AND no craft evidence appears in log.md in the
    same window.

    Motivating failure: Wave 10 README rewrite (a Trigger #4 event per
    craft_protocol.md §3) walked past craft entirely because the
    discovery surface was purely documentation — the agent had to
    remember craft exists. L15 removes that requirement: if you touched
    a trigger surface recently and did not leave craft evidence, the
    linter says so.

    Detection strategy (Round 3 of the meta-craft, mtime primary):
        1. Primary: `path.stat().st_mtime` for each file in
           reflex.trigger_surfaces.{kernel_contract, public_claim}.
           Files not modified in the last `lookback_days` are ignored.
        2. Auxiliary: scan log.md within the same window for
           `evidence_pattern`. If a matching line references a craft
           file OR uses `craft_reference: <id>`, the window is
           considered "covered" — no issue emitted for any surface
           touched in the same window.
        3. Respect `reflex.enabled: false` — emit zero issues and
           return silently (opt-out for downstream instances that have
           not yet imported craft protocol).

    Authoritative schema: _canon.yaml → system.craft_protocol.reflex.
    Craft of record: docs/primordia/craft_reflex_craft_2026-04-11.md.
    """
    import time as _time

    issues = []
    schema = canon.get("system", {}).get("craft_protocol") or {}
    reflex = schema.get("reflex") or {}
    if not reflex or not reflex.get("enabled", False):
        return issues

    lookback_days = int(reflex.get("lookback_days", 3))
    severity = str(reflex.get("severity", "HIGH")).upper()
    if severity not in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
        severity = "HIGH"
    trivial_exempt_lines = int(reflex.get("trivial_exempt_lines", 0) or 0)

    surfaces = reflex.get("trigger_surfaces") or {}
    kernel_surfaces = list(surfaces.get("kernel_contract") or [])
    public_surfaces = list(surfaces.get("public_claim") or [])

    evidence_pattern = reflex.get(
        "evidence_pattern",
        r"(docs/primordia/[a-z0-9_]+_craft_\d{4}-\d{2}-\d{2}(_[0-9a-f]{4})?\.md|craft_reference\s*:)",
    )
    try:
        evidence_re = re.compile(evidence_pattern)
    except re.error as e:
        issues.append(("L15", "HIGH", "_canon.yaml",
                       f"craft_protocol.reflex.evidence_pattern invalid: {e}"))
        return issues

    now = _time.time()
    window = lookback_days * 86400

    # --- Step 1: collect recently-touched surfaces ----------------------
    recent_touches = []   # list of (class_name, rel_path, mtime)
    for cls_name, paths in (("kernel_contract", kernel_surfaces),
                            ("public_claim", public_surfaces)):
        for rel in paths:
            p = root / rel
            if not p.exists():
                # Surface listed but absent — configuration drift.
                # Emit LOW so the reflex block itself stays honest.
                issues.append(("L15", "LOW", rel,
                               f"craft_protocol.reflex surface ({cls_name}) "
                               "declared but file does not exist"))
                continue
            try:
                mt = p.stat().st_mtime
            except OSError:
                continue
            if now - mt < window:
                recent_touches.append((cls_name, rel, mt))

    if not recent_touches:
        return issues  # nothing to check

    # --- Step 2: scan log.md for craft evidence in the same window ------
    # Evidence is considered present if ANY recent log entry references
    # a craft file or uses craft_reference. The log may not exist yet
    # in a fresh clone — in that case we conservatively treat the window
    # as uncovered and emit the reflex signal.
    log_path = root / "log.md"
    evidence_present = False
    if log_path.exists():
        try:
            log_text = log_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            log_text = ""
        # Also consider the primordia/ directory itself — any craft file
        # authored within the lookback window counts as evidence even if
        # log.md has not yet been updated (mtime-based robustness).
        if evidence_re.search(log_text):
            evidence_present = True
        if not evidence_present:
            primordia = root / schema.get("dir", "docs/primordia")
            if primordia.exists():
                for cp in primordia.glob("*_craft_*.md"):
                    try:
                        if now - cp.stat().st_mtime < window:
                            evidence_present = True
                            break
                    except OSError:
                        continue
    else:
        # Fresh clone grace: no log.md — also check primordia/ directly.
        primordia = root / schema.get("dir", "docs/primordia")
        if primordia.exists():
            for cp in primordia.glob("*_craft_*.md"):
                try:
                    if now - cp.stat().st_mtime < window:
                        evidence_present = True
                        break
                except OSError:
                    continue

    if evidence_present:
        return issues

    # --- Step 3: trivial-edit exemption (Wave 12, v0.11.0) ---------------
    # A surface touch whose `git diff` stat is <= trivial_exempt_lines AND
    # introduces no new identifiers is exempt. Wrapped in try/except so
    # non-git environments or untracked files fall back to "not exempt"
    # (fail-closed — fire the reflex when in doubt).
    def _is_trivial_edit(rel_path: str) -> bool:
        if trivial_exempt_lines <= 0:
            return False
        import subprocess
        try:
            # Diff since HEAD — captures all unstaged + staged changes
            # relative to last commit. Untracked files return non-zero
            # and we fall back to not-exempt.
            proc = subprocess.run(
                ["git", "-C", str(root), "diff", "--numstat", "HEAD", "--", rel_path],
                capture_output=True, text=True, timeout=5,
            )
            if proc.returncode != 0:
                return False  # git error / untracked — fail-closed
            out = (proc.stdout or "").strip()
            if not out:
                return True   # file committed but unchanged vs HEAD
            # numstat: "<added>\t<deleted>\t<path>"
            first_line = out.splitlines()[0]
            parts = first_line.split("\t")
            if len(parts) < 2:
                return False
            try:
                added = int(parts[0]) if parts[0] != "-" else 0
                deleted = int(parts[1]) if parts[1] != "-" else 0
            except ValueError:
                return False
            if added + deleted > trivial_exempt_lines:
                return False
            # Check for new identifiers (def, class, function name,
            # YAML key at top-level). Conservative heuristic: any added
            # line that introduces a new keyword-like token.
            diff_proc = subprocess.run(
                ["git", "-C", str(root), "diff", "HEAD", "--", rel_path],
                capture_output=True, text=True, timeout=5,
            )
            if diff_proc.returncode != 0:
                return False
            id_re = re.compile(
                r"^\+\s*(def |class |function |async def |[a-z_][a-z0-9_]*:)"
            )
            for line in diff_proc.stdout.splitlines():
                if id_re.match(line):
                    return False  # new identifier → not trivial
            return True
        except (OSError, subprocess.TimeoutExpired, FileNotFoundError):
            return False  # git missing or timeout — fail-closed

    # --- Step 4: emit per-touched-surface signal ------------------------
    # Group by class to keep output scannable.
    for cls_name, rel, mt in recent_touches:
        if _is_trivial_edit(rel):
            continue
        age_h = int((now - mt) // 3600)
        issues.append(("L15", severity, rel,
                       f"craft trigger surface ({cls_name}) modified "
                       f"{age_h}h ago with no craft evidence in the last "
                       f"{lookback_days}d window — write the missing "
                       f"craft NOW as docs/primordia/<topic>_craft_"
                       f"{datetime.now().strftime('%Y-%m-%d')}.md before "
                       f"resuming the task (W3 reflex arc, contract v0.11.0)"))

    return issues


def lint_boot_brief_freshness(canon, root):
    """L16 (Wave 21, contract v0.20.0) — Boot Brief Freshness.

    The Wave 17 Boot Brief Injector writes `.myco_state/boot_brief.md`
    as a side effect of `myco hunger`, and the brief is injected into
    the entry-point file's MYCO-BOOT-SIGNALS sentinel block. If canon
    or the contract changelog changes without a subsequent hunger run,
    the brief becomes stale but continues to display as if authoritative.

    This lint surfaces staleness as MEDIUM. It does not block; the
    severity-vs-noise tradeoff is per the Wave 21 craft R2.2.

    Authoritative craft:
        docs/primordia/observability_integrity_craft_2026-04-12.md

    Logic:
      1. Read `system.boot_brief.enabled` — if false/missing, PASS.
      2. Resolve brief path from `system.boot_brief.brief_path`.
      3. Brief missing → MEDIUM "missing, run myco hunger".
      4. Compute reference mtime = max(_canon.yaml, contract_changelog.md).
      5. If brief mtime < reference → MEDIUM "stale, run myco hunger".
    """
    from datetime import datetime as _dt

    issues = []
    system = canon.get("system") or {}
    cfg = system.get("boot_brief") or {}
    if not cfg.get("enabled", False):
        return issues  # injector off → nothing to keep fresh

    brief_rel = cfg.get("brief_path", ".myco_state/boot_brief.md")
    brief = Path(root) / brief_rel
    canon_path = Path(root) / "_canon.yaml"
    changelog = Path(root) / "docs" / "contract_changelog.md"

    if not brief.exists():
        issues.append((
            "L16", "MEDIUM", str(brief.relative_to(root)) if brief.is_absolute() and brief.is_relative_to(root) else str(brief),
            "boot brief is missing but boot_brief.enabled=true. "
            "Run `myco hunger` to regenerate; the entry-point signal "
            "block will show absent or stale data until you do."
        ))
        return issues

    try:
        brief_mtime = brief.stat().st_mtime
    except OSError:
        return issues  # permission issue — don't block lint

    ref_mtime = 0.0
    ref_source = None
    if canon_path.exists():
        try:
            ref_mtime = canon_path.stat().st_mtime
            ref_source = "_canon.yaml"
        except OSError:
            pass
    if changelog.exists():
        try:
            cl_mtime = changelog.stat().st_mtime
            if cl_mtime > ref_mtime:
                ref_mtime = cl_mtime
                ref_source = "docs/contract_changelog.md"
        except OSError:
            pass

    if ref_mtime == 0.0:
        return issues  # nothing to compare against

    if brief_mtime < ref_mtime:
        issues.append((
            "L16", "MEDIUM",
            str(brief.relative_to(root)) if brief.is_absolute() and brief.is_relative_to(root) else str(brief),
            f"boot brief is stale: brief mtime "
            f"{_dt.fromtimestamp(brief_mtime).strftime('%Y-%m-%d %H:%M:%S')} "
            f"is older than {ref_source} mtime "
            f"{_dt.fromtimestamp(ref_mtime).strftime('%Y-%m-%d %H:%M:%S')}. "
            f"Run `myco hunger` to regenerate so the entry-point signal "
            f"block reflects current contract state."
        ))
    return issues


def lint_contract_drift(canon, root):
    """L17 (Wave 24, contract v0.23.0) — Contract Drift Surfacing in Lint.

    Closes panorama-#3 hole NH-10: `myco hunger` correctly reports
    `[REFLEX HIGH] contract_drift` when an instance's
    `synced_contract_version` lags the kernel (and when grandfather
    ceiling is exceeded, escalates appropriately), but `myco lint` had
    no equivalent surfacing. Agents running only `myco lint` — which is
    the surface invoked by the Wave 18 pre-commit hook — would see
    "ALL CHECKS PASSED" while the system was screaming drift. Same
    silent-fail pathology class as NH-1 (grandfather ceiling).

    This check re-uses `detect_contract_drift` from `myco.notes` (the
    authoritative drift detector) so there is exactly one truth-
    definition of contract drift across both sensory surfaces.

    Severity mapping (straight from the detector's prefix):
      • `[REFLEX HIGH]` → HIGH   (grandfather expired or drift + enabled reflex)
      • `[REFLEX MEDIUM]` → MEDIUM (version parse error)
      • No signal → PASS
      • Signal without a `[REFLEX ...]` prefix → MEDIUM (defensive default)

    HIGH severity means the Wave 18 pre-commit hook will block commits
    until the instance updates its synced_contract_version — this is
    deliberate: you don't want a downstream to keep committing against
    a stale contract interpretation.

    Authoritative craft:
        docs/primordia/contract_drift_lint_craft_2026-04-12.md
    """
    issues = []
    try:
        from myco.notes import detect_contract_drift
    except Exception as exc:
        # detect_contract_drift lives in the same package as this lint;
        # import failure is itself a catastrophic signal (partial install
        # or broken PYTHONPATH). Wave 24 craft §R3.2: fail-LOUD, not
        # fail-advisory. HIGH blocks the pre-commit hook until install
        # integrity is restored.
        issues.append((
            "L17", "HIGH", "_canon.yaml",
            f"contract drift detector unavailable: {type(exc).__name__}: {exc}. "
            f"Install integrity is compromised. Re-install myco "
            f"(`pip install -e .` or equivalent) before committing."
        ))
        return issues

    try:
        signal = detect_contract_drift(Path(root))
    except Exception as exc:
        issues.append((
            "L17", "HIGH", "_canon.yaml",
            f"contract drift detector raised {type(exc).__name__}: {exc}. "
            f"Re-install myco or file a bug — this should not happen."
        ))
        return issues

    if not signal:
        return issues

    if "[REFLEX HIGH]" in signal:
        severity = "HIGH"
    elif "[REFLEX MEDIUM]" in signal:
        severity = "MEDIUM"
    else:
        # Wave 24 craft §R2.2: unknown reflex prefix must NOT silently
        # degrade. A future contract renaming the prefix would become
        # invisible. Fail-LOUD so the contract author gets a blink
        # during their own dogfood.
        severity = "HIGH"

    # Strip the `[REFLEX ...]` prefix so the lint message reads as a
    # lint message, not as a hunger reflex echo. Keep the rest verbatim.
    msg = signal
    for prefix in ("[REFLEX HIGH] ", "[REFLEX MEDIUM] ", "[REFLEX LOW] "):
        if msg.startswith(prefix):
            msg = msg[len(prefix):]
            break

    issues.append((
        "L17", severity, "_canon.yaml",
        f"{msg} This is the same signal surfaced by `myco hunger`; "
        f"both sensors now agree. Fix by updating "
        f"`system.synced_contract_version` in `_canon.yaml` after "
        f"reading the relevant `docs/contract_changelog.md` entries."
    ))
    return issues


# ---------------------------------------------------------------------------
# L18: Compression Integrity (Wave 30, v0.26.0)
# ---------------------------------------------------------------------------

def lint_compression_integrity(canon, root):
    """L18 (Wave 30, contract v0.26.0) — forward-compression audit-trail integrity.

    Closes Wave 27 D4 + Wave 27 §2.1 defense #4: forward compression's
    bidirectional link integrity is enforced at lint time, not at
    runtime, because (a) the substrate's notes layer cannot detect
    after-the-fact tampering with frontmatter and (b) hallucination
    risk in `myco compress` is bounded by structural rules, not by
    semantic checks. L18 is the structural enforcement.

    Three checks (each issue is HIGH severity):

      1. **Output integrity**: every note with `compressed_from` (i.e. an
         output of compression) must
         (a) have status `extracted` (Wave 27 D3 — never `integrated`
             directly; integration is a separate downstream decision)
         (b) have source `compress`
         (c) have `compression_method` and `compression_rationale` set
         (d) have every id in `compressed_from` exist in notes/

      2. **Input back-link integrity**: every note in any output's
         `compressed_from` list must
         (a) exist in notes/
         (b) have its own `compressed_into` field pointing back to that output
         (c) have status `excreted`

      3. **Cascade prevention**: no note in any output's `compressed_from`
         may itself have a `compressed_from` field. Compressing already-
         compressed notes amplifies hallucination risk and is structurally
         forbidden (Wave 27 §2.1 defense #4).

    L18 is HIGH severity because a broken compression audit chain
    invalidates the reversibility property (Wave 27 D5) — without it
    the user cannot audit what was preserved vs dropped, and Wave 27
    Attack F (hallucination) is unbounded.

    Authoritative craft:
        docs/primordia/compression_primitive_craft_2026-04-12.md (Wave 27)
        docs/primordia/compress_mvp_craft_2026-04-12.md (Wave 30)
    """
    issues = []
    schema = canon.get("system", {}).get("notes_schema") or {}
    notes_dir = root / schema.get("dir", "notes")
    if not notes_dir.exists():
        return issues

    # First pass: build an index of {note_id → (status, compressed_from, compressed_into, source, method, rationale)}
    index = {}
    for path in sorted(notes_dir.glob("n_*.md")):
        rel = str(path.relative_to(root))
        content = read_file(path)
        if content is None:
            continue
        m = _FRONTMATTER_RE.match(content)
        if not m:
            continue
        try:
            meta = yaml.safe_load(m.group("fm")) or {}
        except Exception:
            continue
        if not isinstance(meta, dict):
            continue
        nid = meta.get("id")
        if not nid:
            continue
        index[str(nid)] = {
            "rel": rel,
            "status": meta.get("status"),
            "source": meta.get("source"),
            "compressed_from": meta.get("compressed_from") or [],
            "compressed_into": meta.get("compressed_into"),
            "compression_method": meta.get("compression_method"),
            "compression_rationale": meta.get("compression_rationale"),
        }

    # Check 1: output integrity (notes with compressed_from)
    for nid, info in index.items():
        cf = info["compressed_from"]
        if not cf:
            continue
        rel = info["rel"]
        if not isinstance(cf, list):
            issues.append(("L18", "HIGH", rel,
                           f"compressed_from must be a list, got {type(cf).__name__}"))
            continue
        if info["status"] != "extracted":
            issues.append(("L18", "HIGH", rel,
                           f"output of compression must have status `extracted` "
                           f"(Wave 27 D3), got {info['status']!r}"))
        if info["source"] != "compress":
            issues.append(("L18", "HIGH", rel,
                           f"output of compression must have source `compress` "
                           f"(Wave 27 D4), got {info['source']!r}"))
        if not info["compression_method"]:
            issues.append(("L18", "HIGH", rel,
                           "output of compression missing compression_method "
                           "(Wave 27 D4 audit field)"))
        if not info["compression_rationale"]:
            issues.append(("L18", "HIGH", rel,
                           "output of compression missing compression_rationale "
                           "(Wave 27 D4 audit field — required prose)"))
        # Each input id must exist
        for in_id in cf:
            in_id_str = str(in_id)
            if in_id_str not in index:
                issues.append(("L18", "HIGH", rel,
                               f"compressed_from references unknown note "
                               f"{in_id_str!r} — broken audit chain"))
                continue
            in_info = index[in_id_str]
            # Check 2: input back-link integrity
            if in_info["compressed_into"] != nid:
                issues.append(("L18", "HIGH", in_info["rel"],
                               f"input note must have compressed_into="
                               f"{nid!r}, got {in_info['compressed_into']!r} "
                               f"— bidirectional link integrity broken"))
            if in_info["status"] != "excreted":
                issues.append(("L18", "HIGH", in_info["rel"],
                               f"input note must have status `excreted` after "
                               f"compression into {nid!r}, got "
                               f"{in_info['status']!r}"))
            # Check 3: cascade prevention
            if in_info["compressed_from"]:
                issues.append(("L18", "HIGH", rel,
                               f"compressed_from cascade rejected: input "
                               f"{in_id_str!r} is itself a compression output. "
                               f"Wave 27 §2.1 defense #4 — compression-on-"
                               f"compression amplifies hallucination risk."))

    # Check 2 (continued): orphan compressed_into pointing nowhere
    for nid, info in index.items():
        ci = info["compressed_into"]
        if not ci:
            continue
        ci_str = str(ci)
        if ci_str not in index:
            issues.append(("L18", "HIGH", info["rel"],
                           f"compressed_into references unknown output "
                           f"{ci_str!r} — broken audit chain"))
            continue
        target = index[ci_str]
        if nid not in [str(x) for x in (target["compressed_from"] or [])]:
            issues.append(("L18", "HIGH", info["rel"],
                           f"compressed_into points to {ci_str!r} but that "
                           f"note's compressed_from does not list this id "
                           f"({nid!r}) — bidirectional link integrity broken"))

    return issues


# ---------------------------------------------------------------------------
# L19: Lint Dimension Count Consistency  (Wave 38, contract v0.29.0)
# ---------------------------------------------------------------------------

# Surface lists for L19 — hardcoded per Wave 38 D4. NOT in canon.yaml because
# the list is implementation detail (which downstream caches the substrate
# tracks), not contract surface (which invariants the substrate enforces).
#
# HIGH = user-facing first-impression surfaces (silent damage if drifted)
# MEDIUM = maintainer-facing source/docs (maintainer friction if drifted)
#
# NOT scanned (per Wave 38 D5):
#   - log.md, contract_changelog.md, docs/primordia/*, notes/*, examples/ascc/*
#     (pinned by Hard Contract #2 — historical claims correctly preserved)
#   - src/myco/lint.py itself (own-file self-reference loophole, Wave 38 L1)
_L19_HIGH_SURFACES = (
    "README.md",
    "README_zh.md",
    "README_ja.md",
    "MYCO.md",
)
_L19_MEDIUM_SURFACES = (
    "CONTRIBUTING.md",
    "wiki/README.md",
    "src/myco/cli.py",
    "src/myco/mcp_server.py",
    "src/myco/migrate.py",
    "src/myco/init_cmd.py",
    "scripts/myco_init.py",
    "scripts/myco_migrate.py",
    "docs/reusable_system_design.md",
    "docs/adapters/README.md",
)

# 5 regex patterns (per Wave 38 D6). Each requires domain keywords to
# minimize false positives on unrelated numeric strings.
_L19_PAT_BADGE = re.compile(r"\bLint-(\d+)%2F(\d+)\b")
_L19_PAT_DIM_EN = re.compile(r"\b(\d+)[- ]dimension(?:al)?\s+(?:lint|health|consistency)", re.IGNORECASE)
# CJK count claim: matches both 中文 `维` and 日本語 `次元`. Trailing keyword
# is `lint`, `L0`, `次元の`, or 中文 quantifier patterns to minimize false
# positives.
_L19_PAT_DIM_CJK = re.compile(r"\b(\d+)\s*(?:维|次元)\s*(?:lint|L0|の|的)?")
_L19_PAT_L_RANGE = re.compile(r"\bL0[-–](?:L)?(\d+)\b")
_L19_PAT_RATIO = re.compile(r"\b(\d+)/(\d+)\s+(?:green|绿|PASS|pass)")


def lint_dimension_count_consistency(canon, root):
    """L19 (Wave 38, contract v0.29.0) — LINT_DIMENSION_COUNT downstream-cache integrity.

    Closes Wave 37 D7 candidate #1 + enforces Wave 37 D1 ("SSoT for
    LINT_DIMENSION_COUNT is `len(FULL_CHECKS)`; every other surface is a
    downstream cache that must be bumped in lockstep").

    Background: between Wave 30 (when L18 landed) and Wave 37 (when the
    manual sweep caught it), the substrate silently rotted for ~7 waves —
    README badges, MYCO.md headlines, mcp_server.py docstrings, and 12+
    other surfaces all claimed "15-dimension / L0-L14" while the actual
    substrate was at 19 dimensions / L0-L18. The drift was invisible
    because no automated check enforced consistency between the structural
    truth (`len(FULL_CHECKS)`) and the labels that referenced it.

    L19 makes that class of rot structurally impossible: any future wave
    that adds a lint dimension and forgets to bump downstream caches will
    trip L19 at the next lint run. The Wave 38 craft §2 Attack A defends
    permanence over a one-time script: a structural check is the substrate-
    native way to encode any consistency invariant.

    What L19 scans (per Wave 38 D4 + D5):
      - HIGH surfaces (4): README.md, README_zh.md, README_ja.md, MYCO.md
      - MEDIUM surfaces (10): CONTRIBUTING.md, wiki/README.md,
        src/myco/{cli,mcp_server,migrate,init_cmd}.py,
        scripts/myco_{init,migrate}.py, docs/reusable_system_design.md,
        docs/adapters/README.md
      - NOT scanned: pinned surfaces (log.md, contract_changelog.md,
        primordia/*, notes/*, examples/ascc/*) and lint.py itself
        (own-file self-reference loophole, Wave 38 L1)

    What L19 detects (per Wave 38 D6 — 5 regex patterns):
      1. README badge `Lint-(\\d+)%2F(\\d+)\\s+green`
      2. English count `\\b(\\d+)[- ]dimension(?:al)?\\s+(?:lint|health|consistency)`
      3. Chinese count `\\b(\\d+)\\s*维\\s*(?:lint|L0)`
      4. L range `\\bL0[-–](?:L)?(\\d+)\\b`
      5. Pass ratio `\\b(\\d+)/(\\d+)\\s+(?:green|绿|PASS|pass)`

    Patterns 1, 2, 3, 5 expect the integer == LINT_DIMENSION_COUNT.
    Pattern 4 expects the integer == LINT_DIMENSION_COUNT - 1 (the L-max).

    Severity (per Wave 38 D1 + D4):
      - HIGH for surfaces in _L19_HIGH_SURFACES (user-facing damage)
      - MEDIUM for surfaces in _L19_MEDIUM_SURFACES (maintainer damage)

    Authoritative craft:
        docs/primordia/lint_dimension_count_consistency_craft_2026-04-12.md
    """
    issues = []
    expected = len(FULL_CHECKS)
    expected_l_max = expected - 1
    # Quick-mode subset is a legitimate sub-range claim (e.g. `L0-L3` in
    # `myco lint --quick` help text and the MCP `quick: L0-L3` arg description).
    # Pattern 4 must NOT flag L0-L<quick_max> as drift because it's the
    # documented sub-range, not a current full-range claim.
    quick_l_max = len(QUICK_CHECKS) - 1
    legitimate_l_max = {expected_l_max, quick_l_max}

    def _scan(rel: str, severity: str):
        path = root / rel
        if not path.exists():
            return
        content = read_file(path)
        if content is None:
            return
        for line_no, line in enumerate(content.splitlines(), 1):
            # Pattern 1 — README badge
            for m in _L19_PAT_BADGE.finditer(line):
                n1, n2 = int(m.group(1)), int(m.group(2))
                if n1 != expected or n2 != expected:
                    issues.append((
                        "L19", severity, rel,
                        f"line {line_no}: badge `Lint-{n1}/{n2}` drifted "
                        f"from current LINT_DIMENSION_COUNT={expected} "
                        f"(SSoT is len(FULL_CHECKS) in src/myco/lint.py — "
                        f"Wave 37 D1)",
                    ))
            # Pattern 2 — English count
            for m in _L19_PAT_DIM_EN.finditer(line):
                n = int(m.group(1))
                if n != expected:
                    issues.append((
                        "L19", severity, rel,
                        f"line {line_no}: dimension count `{n}-dimension` "
                        f"drifted from current LINT_DIMENSION_COUNT={expected}",
                    ))
            # Pattern 3 — CJK count (中文 `维` / 日本語 `次元`)
            for m in _L19_PAT_DIM_CJK.finditer(line):
                n = int(m.group(1))
                if n != expected:
                    issues.append((
                        "L19", severity, rel,
                        f"line {line_no}: CJK 维度计数 `{m.group(0).strip()}` "
                        f"与当前 LINT_DIMENSION_COUNT={expected} 不一致",
                    ))
            # Pattern 4 — L range. Exempt the quick-mode subset claim
            # (L0-L<quick_max>) per the legitimate_l_max set above.
            for m in _L19_PAT_L_RANGE.finditer(line):
                n = int(m.group(1))
                if n in legitimate_l_max:
                    continue
                issues.append((
                    "L19", severity, rel,
                    f"line {line_no}: lint range `L0-L{n}` drifted "
                    f"from current `L0-L{expected_l_max}`",
                ))
            # Pattern 5 — Pass ratio
            for m in _L19_PAT_RATIO.finditer(line):
                n1, n2 = int(m.group(1)), int(m.group(2))
                if n1 != expected or n2 != expected:
                    issues.append((
                        "L19", severity, rel,
                        f"line {line_no}: pass ratio `{n1}/{n2}` drifted "
                        f"from current `{expected}/{expected}`",
                    ))

    for rel in _L19_HIGH_SURFACES:
        _scan(rel, "HIGH")
    for rel in _L19_MEDIUM_SURFACES:
        _scan(rel, "MEDIUM")

    return issues


# ---------------------------------------------------------------------------
# L20 — Translation Mirror Consistency (Wave 39, contract v0.30.0)
# ---------------------------------------------------------------------------

# The three locale-mirror READMEs that L20 enforces. README.md is the
# reference (Wave 39 D2 — English first because it is updated first in
# practice and every contributor reads English; only some read CJK).
_L20_LOCALE_READMES = ("README.md", "README_zh.md", "README_ja.md")

# Skip-marker pattern (Wave 39 D5). A section preceded by `<!-- l20-skip -->`
# on the previous non-blank line is excluded from all skeleton counts.
_L20_SKIP_MARKER = "<!-- l20-skip -->"


def _count_skeleton(content: str) -> tuple:
    """Compute the 5-tuple structural skeleton of a README file.

    Returns ``(h2_count, h3_count, code_count, table_rows, badge_count)``.

    The parser is fence-aware (Wave 39 D6): H2/H3 lines INSIDE fenced
    code blocks are NOT counted. The l20-skip marker (Wave 39 D5) on
    the previous non-blank line excludes the immediately following H2/H3
    from the count.

    Components:
        h2_count    — number of `^## ` lines outside code fences
        h3_count    — number of `^### ` lines outside code fences
        code_count  — number of fenced code block opens
        table_rows  — number of `^|` lines outside code fences (any table)
        badge_count — number of `Lint-N%2FN` badge lines (URL-encoded)
    """
    if content is None:
        return (0, 0, 0, 0, 0)

    h2 = 0
    h3 = 0
    code = 0
    table_rows = 0
    badge = 0
    in_fence = False
    skip_next_heading = False
    prev_nonblank_was_skip = False

    badge_re = re.compile(r"\bLint-\d+%2F\d+\b")

    for raw_line in content.splitlines():
        line = raw_line.rstrip()

        # Fence toggle (matches both ``` and ```language)
        if line.startswith("```"):
            code += 1 if not in_fence else 0  # count opens only
            in_fence = not in_fence
            prev_nonblank_was_skip = False
            continue

        if in_fence:
            # Inside a code fence: nothing structural counts.
            # (Skip marker tracking pauses inside fences too.)
            continue

        # Track the skip marker on the previous non-blank line.
        stripped = line.strip()
        if stripped == _L20_SKIP_MARKER:
            prev_nonblank_was_skip = True
            continue

        if stripped == "":
            # Blank line — does NOT reset prev_nonblank_was_skip
            # (the marker is allowed to be 1+ blank lines above the heading).
            continue

        if line.startswith("### "):
            if prev_nonblank_was_skip:
                prev_nonblank_was_skip = False
            else:
                h3 += 1
        elif line.startswith("## "):
            if prev_nonblank_was_skip:
                prev_nonblank_was_skip = False
            else:
                h2 += 1
        elif line.startswith("|"):
            # Markdown table row (header rows + body rows + separator).
            # We count all `^|` lines uniformly; this is a single proxy
            # for "table density" and is sufficient for skeleton parity.
            table_rows += 1
            prev_nonblank_was_skip = False
        elif badge_re.search(line):
            badge += 1
            prev_nonblank_was_skip = False
        else:
            # Any non-blank, non-fence, non-heading, non-table, non-badge
            # line resets the skip flag (the marker only applies to the
            # very next structural element).
            prev_nonblank_was_skip = False

    return (h2, h3, code, table_rows, badge)


def lint_translation_mirror_consistency(canon, root):
    """L20 (Wave 39, contract v0.30.0) — locale README skeleton parity.

    Closes Wave 37 D7 followup #2 + Wave 38 forward path. Enforces that
    `README_zh.md` and `README_ja.md` mirror `README.md`'s structural
    skeleton tuple-for-tuple. The three READMEs are the substrate's
    user-facing first impression in three languages; if their structural
    skeletons drift apart (one section dropped from one locale but not
    from another), non-English users see a degraded substrate while
    English readers see a healthy one.

    What L20 enforces (Wave 39 D1):
      The 5-tuple ``skeleton(README.md) ==
      skeleton(README_zh.md) == skeleton(README_ja.md)``,
      where skeleton is ``(h2, h3, code, table_rows, badge)``.

    What L20 does NOT enforce (Wave 39 §0.3):
      - Heading text (translation is precisely why these files exist)
      - Paragraph content or word count (translation length varies)
      - Specific line numbers (length differences shift positions)
      - Files outside _L20_LOCALE_READMES (explicit allowlist)

    Severity (Wave 39 D4): HIGH for any drift in any locale README.

    Edge case handling (Wave 39 §3.1):
      - C1: README.md missing → silent pass (no reference to compare)
      - C2: 2 of 3 present → compare just those two
      - C3: empty README → loud drift report
      - C5: CRLF line endings → splitlines() handles all styles
      - C6: trailing whitespace → rstrip() before prefix check
      - C7: code-fence-aware (D6 + see _count_skeleton)

    Authoritative craft:
        docs/primordia/translation_mirror_lint_craft_2026-04-12.md
    """
    issues = []

    # Read all 3 locale files (or as many as exist).
    skeletons = {}
    for rel in _L20_LOCALE_READMES:
        path = root / rel
        if not path.exists():
            continue
        content = read_file(path)
        if content is None:
            continue
        skeletons[rel] = _count_skeleton(content)

    if len(skeletons) < 2:
        # C1: < 2 locale READMEs exist; nothing to mirror against. Silent pass.
        return issues

    # Pick the reference: README.md if present (D2), else the longest file
    # (C2 fallback for projects that haven't yet created the English copy).
    if "README.md" in skeletons:
        reference_file = "README.md"
    else:
        # Fallback: the file with the highest h2_count is the most-developed.
        reference_file = max(skeletons, key=lambda r: skeletons[r][0])
    reference_skeleton = skeletons[reference_file]

    # Compare each non-reference file's skeleton to the reference.
    component_names = ("h2", "h3", "code", "table_rows", "badge")
    for rel, skel in skeletons.items():
        if rel == reference_file:
            continue
        if skel == reference_skeleton:
            continue
        # Mismatch — emit one issue per drifted component for granular triage.
        for i, name in enumerate(component_names):
            if skel[i] != reference_skeleton[i]:
                issues.append((
                    "L20", "HIGH", rel,
                    f"skeleton {name}={skel[i]} drifted from "
                    f"{reference_file} {name}={reference_skeleton[i]} "
                    f"(translation mirror parity broken — Wave 39 D1)",
                ))

    return issues


# ---------------------------------------------------------------------------
# L21 Contract Version Inline Consistency (Wave 40, v0.31.0)
# ---------------------------------------------------------------------------
# Forward-looking inline contract version claims (e.g. "kernel contract
# v0.X.Y") in narrative surfaces must match `_canon.yaml::system.contract_version`.
# Catches the scar class where Wave 38 + Wave 39 both swept narrative
# surfaces but missed inline `kernel contract v0.28.0` claims in MYCO.md
# lines 4 / 22 / 159 — proving manual sweeps cannot replace ground-truth
# lint. Sister to L19 (count drift) and L20 (skeleton drift). Together
# the three close the substrate's top three silent-rot scar classes.
#
# Authoritative craft:
#     docs/primordia/contract_version_inline_craft_2026-04-12.md

_L21_HIGH_FILES = (
    "MYCO.md",
    "README.md",
    "README_zh.md",
    "README_ja.md",
)

_L21_MEDIUM_FILES = (
    "docs/adapters/README.md",
    "CONTRIBUTING.md",
    "docs/architecture.md",
    "docs/vision.md",
    "docs/theory.md",
)

_L21_SKIP_MARKER = "<!-- l21-skip -->"

# Forward-looking pattern (Wave 40 D1): catches "kernel contract v0.X.Y",
# "当前 contract v0.X.Y", "current contract: v0.X.Y" with optional colon
# (ASCII or full-width) and optional `v` prefix. Case-insensitive.
_L21_FORWARD_RE = re.compile(
    r"(?i)(kernel contract|当前\s*contract|current contract)\s*[:：]?\s*(v?\d+\.\d+\.\d+)"
)

# Date-in-parens marker for historical context, e.g. (2026-04-11).
_L21_DATE_RE = re.compile(r"\(20\d\d-\d\d-\d\d")

# Two-version transition arrow, e.g. "v0.29.0 → v0.30.0" (describes a bump).
_L21_TRANSITION_RE = re.compile(r"v?\d+\.\d+\.\d+\s*[→\-]>?\s*v?\d+\.\d+\.\d+")

# Historical-event verbs adjacent to a version (within 30 chars).
_L21_HISTORICAL_VERBS = ("landed", "landing", "落地", "已完成", "完成", "post-rebase",
                         "supersedes", "succeeded", "✅")


def _l21_is_historical(line, prev_nonblank_line):
    """Apply Wave 40 §1.2 historical-marker filter to a matched line.

    Returns True if the line should be treated as a historical reference
    (skip) and False if it is a current claim (check). The filter is
    deliberately biased toward false negatives (skip on ambiguity) — the
    cost of a false positive (noisy lint that operators learn to ignore)
    is higher than the cost of a false negative (one missed drift caught
    on the next wave).
    """
    # 1. Operator skip-marker on previous non-blank line.
    if prev_nonblank_line is not None and prev_nonblank_line.strip() == _L21_SKIP_MARKER:
        return True

    # 2. Date in parens — strong historical timestamp signal.
    if _L21_DATE_RE.search(line):
        return True

    # 3. Two-version transition arrow — describes a bump action, not a state.
    if _L21_TRANSITION_RE.search(line):
        return True

    # 4. Historical-event verbs anywhere in the line.
    for verb in _L21_HISTORICAL_VERBS:
        if verb in line:
            return True

    # 5. Markdown table row — Phase tracker shape (`|` or `· …` bullet rows
    # are not table rows but have similar historical semantics).
    # We treat actual table rows (`^\s*\|`) as historical because the Phase
    # tracker uses tables for landing records.
    stripped = line.lstrip()
    if stripped.startswith("|"):
        return True

    return False


def lint_contract_version_inline(canon, root):
    """L21 (Wave 40, contract v0.31.0) — inline contract version SSoT enforcement.

    Closes Wave 37 D7 followup #3, the third + final candidate from the
    Wave 37 manual sweep. Sister to Wave 38 L19 (dimension count) and
    Wave 39 L20 (translation mirror skeleton). The three together close
    the substrate's top three silent-rot scar classes.

    What L21 enforces (Wave 40 D1):
        Every line matching the forward-looking pattern
        ``(kernel contract|当前 contract|current contract)\\s*[:：]?\\s*v?\\d+\\.\\d+\\.\\d+``
        in an allowlisted file (Wave 40 D2) must use the canonical
        contract version from ``_canon.yaml::system.contract_version``,
        UNLESS the line is identified as historical by the §1.2 filter
        set (date in parens, transition arrow, landed verb, code fence,
        table row, post-rebase keyword, or l21-skip marker).

    What L21 does NOT enforce (Wave 40 §0.3):
        - Package version `__version__` / pyproject.toml (independent SemVer
          line per Wave 8 re-baseline)
        - Append-only history surfaces (log.md, contract_changelog.md,
          docs/primordia/, notes/, examples/ascc/)
        - Source code, tests, scripts (not narrative surfaces)
        - Semantic alignment between contract version and prose description

    Severity (Wave 40 D4):
        - HIGH for entry point (MYCO.md) + 3 locale READMEs
        - MEDIUM for adapter/contrib/doctrinal docs

    Edge cases (Wave 40 §3.1):
        - C1: multiple version claims per line — first match used
        - C2: optional `v` prefix
        - C3: ASCII or full-width colon
        - C4: missing allowlist file → silent skip
        - C5: missing canon → silent pass (L0 enforces canon presence)
        - C6: code-fence aware
        - C7: src/myco/lint.py itself is not in the allowlist

    Authoritative craft:
        docs/primordia/contract_version_inline_craft_2026-04-12.md
    """
    issues = []

    # Read canon contract version (D1 SSoT).
    canon_version = (canon.get("system") or {}).get("contract_version")
    if not canon_version:
        # C5: no canon version → can't compare, silent pass.
        return issues

    # Normalize: canon may store with or without leading `v`. Compare
    # both forms to be tolerant.
    canon_normalized = canon_version.lstrip("v")

    # Walk the file allowlist.
    for severity, files in (("HIGH", _L21_HIGH_FILES), ("MEDIUM", _L21_MEDIUM_FILES)):
        for rel in files:
            path = root / rel
            if not path.exists():
                continue  # C4
            content = read_file(path)
            if content is None:
                continue

            # Walk lines with code-fence state and previous-line tracking.
            in_fence = False
            prev_nonblank_line = None

            for raw_line in content.splitlines():
                line = raw_line.rstrip()

                # C6: code-fence aware.
                if line.startswith("```"):
                    in_fence = not in_fence
                    if line.strip() != "":
                        prev_nonblank_line = line
                    continue

                if in_fence:
                    if line.strip() != "":
                        prev_nonblank_line = line
                    continue

                # Try to match the forward-looking pattern.
                match = _L21_FORWARD_RE.search(line)
                if match is None:
                    if line.strip() != "":
                        prev_nonblank_line = line
                    continue

                # Apply historical-marker filter.
                if _l21_is_historical(line, prev_nonblank_line):
                    if line.strip() != "":
                        prev_nonblank_line = line
                    continue

                # Forward-looking match: extract version, compare to canon.
                matched_version = match.group(2).lstrip("v")
                if matched_version != canon_normalized:
                    issues.append((
                        "L21", severity, rel,
                        f"inline contract version `v{matched_version}` "
                        f"drifted from canon `v{canon_normalized}` "
                        f"(forward-looking claim must mirror "
                        f"_canon.yaml::system.contract_version — "
                        f"Wave 40 D1)",
                    ))

                if line.strip() != "":
                    prev_nonblank_line = line

    return issues


# ---------------------------------------------------------------------------
# L22 Wave-Seed Lifecycle (Wave 41, v0.32.0)
# ---------------------------------------------------------------------------
# Wave-seed orphan detection: a raw note tagged `wave{N}-seed` where wave N
# has already landed (its milestone exists in `log.md`) is a structural
# post-condition violation of the seven-step pipeline (anchor #3). The seed
# was captured during the wave as evidence input but never advanced past
# `raw` after the wave closed. L22 catches each such orphan as a HIGH
# issue, naming the canonical advancement command.
#
# Sister to L19/L20/L21: each is a structural drift detector for a
# different scar class. Together they form the substrate's silent-rot
# fence around its most fragile referential surfaces.
#
# Authoritative craft:
#     docs/primordia/wave_seed_lifecycle_craft_2026-04-12.md

# Tag pattern (Wave 41 D6): exact `wave\d+-seed`. No loose variations.
_L22_WAVE_SEED_RE = re.compile(r"^wave(\d+)-seed$")

# log.md milestone pattern (Wave 41 D3): bold `**Wave N landed**` with
# optional trailing parenthetical context inside the bold. Stable across
# 40+ waves of log.md history.
_L22_MILESTONE_RE = re.compile(
    r"\*\*Wave\s+(\d+)\s+landed[^*]*\*\*",
    re.IGNORECASE,
)


def _l22_parse_closed_waves(root):
    """Parse log.md and return the set of closed wave numbers (Wave 41 D2).

    Returns an empty set if log.md is missing or unreadable. The set is
    composed of integers parsed from `**Wave N landed**` milestone bold
    headers anywhere in the file.
    """
    log_path = root / "log.md"
    if not log_path.exists():
        return set()
    try:
        content = log_path.read_text(encoding="utf-8")
    except Exception:
        return set()

    closed = set()
    for match in _L22_MILESTONE_RE.finditer(content):
        try:
            closed.add(int(match.group(1)))
        except (ValueError, TypeError):
            continue
    return closed


def lint_wave_seed_orphan(canon, root):
    """L22 (Wave 41, contract v0.32.0) — wave-seed orphan detection.

    Catches the structural post-condition violation where a raw note
    tagged `wave{N}-seed` exists for a wave N whose `**Wave N landed**`
    milestone is already in `log.md`. The seed was captured as evidence
    input to the wave's craft but was never advanced past `raw` after
    the wave's closing commit. This violates anchor #3 (the seven-step
    metabolic pipeline: raw must advance).

    Detection (Wave 41 D1):
        A note is an orphan iff ALL of:
        1. status == "raw"
        2. some tag matches `wave\\d+-seed`
        3. the parsed wave number has a milestone in log.md

    What L22 does NOT enforce (Wave 41 §0.2):
        - That every wave MUST create a seed bundle
        - That seeds must reach a specific terminal state
        - That non-wave-tagged raw notes must advance
        - Seeds tagged for waves not yet landed (allowed to stay raw
          while wave is in progress)
        - Seeds in `digesting` (advanced once, then forgotten — separate
          dimension if needed)

    Severity: HIGH for each orphan (no tier system per Wave 41 D4).

    Authoritative craft:
        docs/primordia/wave_seed_lifecycle_craft_2026-04-12.md
    """
    issues = []

    # Determine notes/ directory (mirror L10 logic for schema-driven dir).
    schema = (canon.get("system") or {}).get("notes_schema") or {}
    notes_dir = root / schema.get("dir", "notes")
    if not notes_dir.exists():
        return issues

    closed_waves = _l22_parse_closed_waves(root)
    if not closed_waves:
        # C8: empty/missing log.md or no landed waves → nothing to enforce.
        return issues

    for path in sorted(notes_dir.glob("*.md")):
        name = path.name
        if not name.startswith("n_"):
            continue  # skip README and similar

        content = read_file(path)
        if content is None:
            continue

        m = _FRONTMATTER_RE.match(content)
        if not m:
            continue  # L10 will catch the missing frontmatter

        try:
            meta = yaml.safe_load(m.group("fm")) or {}
        except Exception:
            continue  # L10 will catch the malformed frontmatter
        if not isinstance(meta, dict):
            continue

        if meta.get("status") != "raw":
            continue

        tags = meta.get("tags") or []
        if not isinstance(tags, list):
            continue

        # Find the first wave-seed tag whose wave is closed (D2 — first
        # match wins to bound noise; one issue per orphan, not per tag).
        rel = str(path.relative_to(root)).replace("\\", "/")
        note_id = meta.get("id") or path.stem
        for tag in tags:
            if not isinstance(tag, str):
                continue
            tm = _L22_WAVE_SEED_RE.match(tag)
            if tm is None:
                continue
            try:
                wave_n = int(tm.group(1))
            except (ValueError, TypeError):
                continue
            if wave_n in closed_waves:
                issues.append((
                    "L22", "HIGH", rel,
                    f"wave-seed orphan: tag `wave{wave_n}-seed` references "
                    f"a closed wave but note status is still `raw`. "
                    f"Advance via `myco digest --to extracted {note_id}` "
                    f"(seven-step pipeline post-condition — Wave 41 D1). "
                    f"Authoritative craft: "
                    f"docs/primordia/wave_seed_lifecycle_craft_2026-04-12.md"
                ))
                break  # one issue per orphan note

    return issues


# ---------------------------------------------------------------------------
# Module-level checks lists (Wave 38 D2 — SSoT for LINT_DIMENSION_COUNT)
# ---------------------------------------------------------------------------

# QUICK_CHECKS = the L0-L3 fast subset run when `myco lint --quick`.
# FULL_CHECKS  = the full L0-L22 sequence (default). `len(FULL_CHECKS)` is
# the canonical lint dimension count — see L19 docstring for the rot story.
QUICK_CHECKS = (
    ("L0 Canon Self-Check", lint_canon_schema),
    ("L1 Reference Integrity", lint_references),
    ("L2 Number Consistency", lint_numbers),
    ("L3 Stale Pattern Scan", lint_stale_patterns),
)

FULL_CHECKS = QUICK_CHECKS + (
    ("L4 Orphan Detection", lint_orphans),
    ("L5 log.md Coverage", lint_log),
    ("L6 Date Consistency", lint_dates),
    ("L7 Wiki W8 Format", lint_wiki_format),
    ("L8 .original Sync", lint_original_sync),
    ("L9 Vision Anchor", lint_vision_anchors),
    ("L10 Notes Schema", lint_notes_schema),
    ("L11 Write Surface", lint_write_surface),
    ("L12 Upstream Dotfile Hygiene", lint_dotfile_hygiene),
    ("L13 Craft Protocol Schema", lint_craft_protocol),
    ("L14 Forage Hygiene", lint_forage_hygiene),
    ("L15 Craft Reflex", lint_craft_reflex),
    ("L16 Boot Brief Freshness", lint_boot_brief_freshness),
    ("L17 Contract Drift", lint_contract_drift),
    ("L18 Compression Integrity", lint_compression_integrity),
    ("L19 Lint Dimension Count Consistency", lint_dimension_count_consistency),
    ("L20 Translation Mirror Consistency", lint_translation_mirror_consistency),
    ("L21 Contract Version Inline Consistency", lint_contract_version_inline),
    ("L22 Wave-Seed Lifecycle", lint_wave_seed_orphan),
)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(root: Path = None, quick: bool = False, fix_report: bool = False) -> int:
    """Run lint checks. Can be called programmatically or from CLI."""
    if root is None:
        root = Path.cwd()

    print(bold(f"\n{'='*60}"))
    print(bold(f"  Myco Knowledge System Lint"))
    print(bold(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"))
    print(bold(f"  Project: {root}"))
    print(bold(f"{'='*60}\n"))

    canon = load_canon(root)

    checks = list(QUICK_CHECKS) if quick else list(FULL_CHECKS)

    all_issues = []
    for name, checker in checks:
        print(cyan(f"  Checking {name}..."))
        issues = checker(canon, root)
        all_issues.extend(issues)
        if issues:
            print(yellow(f"    → {len(issues)} issue(s) found"))
        else:
            print(green(f"    → PASS"))

    if quick:
        print(cyan(f"  (quick mode: L4-L8 skipped)"))

    print(bold(f"\n{'='*60}"))

    if not all_issues:
        print(green(bold("  ✅ ALL CHECKS PASSED — 0 issues found")))
        print(bold(f"{'='*60}\n"))
        return 0

    by_severity = defaultdict(list)
    for lint_id, severity, filepath, msg in all_issues:
        by_severity[severity].append((lint_id, filepath, msg))

    total = len(all_issues)
    critical = len(by_severity.get("CRITICAL", []))
    high = len(by_severity.get("HIGH", []))
    medium = len(by_severity.get("MEDIUM", []))
    low = len(by_severity.get("LOW", []))

    print(red(bold(f"  ⚠️  {total} issue(s): "
                   f"{critical} CRITICAL, {high} HIGH, {medium} MEDIUM, {low} LOW")))
    print(bold(f"{'='*60}\n"))

    for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        items = by_severity.get(severity, [])
        if not items:
            continue
        color = red if severity in ("CRITICAL", "HIGH") else yellow
        print(color(bold(f"  [{severity}]")))
        for lint_id, filepath, msg in items:
            print(f"    {lint_id} | {filepath}")
            print(f"         {msg}")
        print()

    return 2 if critical else (1 if high else 0)


def run_lint(args) -> int:
    """Entry point called from CLI dispatcher."""
    root = Path(args.project_dir).resolve()
    return main(root=root, quick=args.quick, fix_report=args.fix_report)
