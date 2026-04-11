#!/usr/bin/env python3
"""
Myco Knowledge System — Automated 16-Dimension Lint.

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
    ALLOWED_DIRS = {".myco_upstream_outbox", ".myco_upstream_inbox"}
    ALLOWED_SUBDIRS = {
        ".myco_upstream_inbox": {"absorbed"},
        ".myco_upstream_outbox": set(),
    }
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
                               "Only .myco_upstream_outbox/ and "
                               ".myco_upstream_inbox/ are reserved. "
                               "See docs/agent_protocol.md §8.5."))
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

    checks = [
        ("L0 Canon Self-Check", lint_canon_schema),
        ("L1 Reference Integrity", lint_references),
        ("L2 Number Consistency", lint_numbers),
        ("L3 Stale Pattern Scan", lint_stale_patterns),
    ]
    if not quick:
        checks.extend([
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
        ])

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
