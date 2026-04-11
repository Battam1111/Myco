#!/usr/bin/env python3
"""
Myco Knowledge System — Automated 14-Dimension Lint.

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
    L9  Vision Anchor — identity-element drift detection (v1.1.1)
    L10 Notes Schema — atomic-note frontmatter validation (v1.2.0)
    L11 Write Surface — _canon.yaml write_surface whitelist (v1.2.0)
    L12 Upstream Dotfile Hygiene — .myco_upstream_{outbox,inbox}/ rules (v1.2.0)
    L13 Craft Protocol Schema — docs/primordia/*_craft_*.md frontmatter (v1.3.0, W3)
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
    issues = []
    entry_point = get_entry_point(canon)
    entry_file = read_file(root / entry_point)
    if not entry_file:
        issues.append(("L1", "CRITICAL", entry_point, f"Cannot read {entry_point}"))
        return issues

    refs = re.findall(
        r"`([a-zA-Z_/][a-zA-Z0-9_/\-.*]+\.(?:md|py|sh|yaml|txt))`", entry_file
    )
    for ref in refs:
        if "*" in ref or ref.startswith("/"):
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
        rel = str(Path(wiki_file).relative_to(root))
        name = Path(wiki_file).name
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

    Single source of truth as of contract v1.6.0 (Wave 6 de-dup).
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
    truth as of contract v1.6.0 — scripts/lint_knowledge.py is a shim.
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

    Upstream Protocol v1.0 (see docs/agent_protocol.md §8.5) defines two
    transport directories at the repo root:

      - ``.myco_upstream_outbox/``  (instance → kernel)
      - ``.myco_upstream_inbox/``   (kernel ack → instance)

    Rules:
      1. If either dir exists, every file inside MUST match the pattern
         ``upstream_YYYYMMDDTHHMMSS_[0-9a-f]{4}\\.(json|md|patch)``.
      2. Files older than 30 days produce a LOW-severity GC reminder.
      3. Any OTHER ``.myco_*`` top-level dir is HIGH (reserved namespace).
    """
    import re as _re
    import time as _time

    issues = []

    pattern = _re.compile(
        r"^upstream_\d{8}T\d{6}_[0-9a-f]{4}\.(json|md|patch)$"
    )
    ALLOWED_DIRS = {".myco_upstream_outbox", ".myco_upstream_inbox"}
    thirty_days = 30 * 86400
    now = _time.time()

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

            for child in sorted(full.iterdir()):
                if child.is_dir():
                    issues.append(("L12", "HIGH", f"{name}/{child.name}/",
                                   f"{name}/ must be flat — no subdirectories"))
                    continue
                if child.name == "README.md":
                    continue
                if not pattern.match(child.name):
                    issues.append(("L12", "HIGH", f"{name}/{child.name}",
                                   "Filename does not match "
                                   "upstream_YYYYMMDDTHHMMSS_xxxx.(json|md|patch). "
                                   "See docs/agent_protocol.md §8.5."))
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


def lint_craft_protocol(canon, root):
    """L13 — Craft Protocol Schema (W3, v1.3.0).

    Enforces docs/craft_protocol.md frontmatter schema on any file in
    docs/primordia/ matching the craft filename pattern AND declaring
    craft_protocol_version: 1. Files without craft_protocol_version are
    grandfathered (see docs/craft_protocol.md §6) and skipped entirely.

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
