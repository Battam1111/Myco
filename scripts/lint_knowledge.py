#!/usr/bin/env python3
"""
Myco Knowledge System — Automated Lint
=======================================
Check project documents for consistency against _canon.yaml.

Usage:
    python scripts/lint_knowledge.py              # Full lint (all dimensions)
    python scripts/lint_knowledge.py --quick       # Quick mode (L0-L3 only)
    python scripts/lint_knowledge.py --fix-report  # Output fix suggestions

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
    L11 Write Surface — agent write-target whitelist enforcement (v1.2.0)
"""

import os
import re
import sys
import glob
import yaml
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent

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

def load_canon():
    canon_path = ROOT / "_canon.yaml"
    if not canon_path.exists():
        print(red("FATAL: _canon.yaml not found at project root!"))
        sys.exit(1)
    with open(canon_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def get_entry_point():
    """Get entry point filename from _canon.yaml or default to MYCO.md"""
    canon = load_canon()
    system = canon.get("system", {})
    entry_point = system.get("entry_point", "MYCO.md")
    return entry_point

def read_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None

def find_files(pattern, root=ROOT):
    return sorted(glob.glob(str(root / pattern), recursive=True))

# ---------------------------------------------------------------------------
# L0: Canon Self-Check
# ---------------------------------------------------------------------------

def lint_canon_schema(canon):
    """Verify _canon.yaml contains universal required keys."""
    issues = []

    universal_required = {
        "system.principles_count": ["system", "principles_count"],
        "architecture.layers": ["architecture", "layers"],
        "architecture.wiki_pages": ["architecture", "wiki_pages"],
    }

    # Dynamically check project-specific keys if they exist
    # (projects define their own required keys — we only check universal ones)

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

def lint_references(canon):
    """Check all files referenced in entry point document exist."""
    issues = []
    entry_point = get_entry_point()
    entry_file = read_file(ROOT / entry_point)
    if not entry_file:
        issues.append(("L1", "CRITICAL", entry_point, f"Cannot read {entry_point}"))
        return issues

    refs = re.findall(
        r"`([a-zA-Z_/][a-zA-Z0-9_/\-.*]+\.(?:md|py|sh|yaml|txt))`", entry_file
    )

    for ref in refs:
        if "*" in ref or ref.startswith("/"):
            continue
        path = ROOT / ref
        if not path.exists():
            issues.append(("L1", "HIGH", entry_point,
                           f"Referenced file missing: {ref}"))

    # Cross-references within wiki pages
    for wiki_file in find_files("wiki/*.md"):
        content = read_file(wiki_file)
        if not content:
            continue
        links = re.findall(r"\[.*?\]\((\.\.?/[^)]+)\)", content)
        for link in links:
            target = (Path(wiki_file).parent / link).resolve()
            if not target.exists():
                rel = str(Path(wiki_file).relative_to(ROOT))
                issues.append(("L1", "HIGH", rel,
                               f"Broken cross-reference: {link}"))

    return issues

# ---------------------------------------------------------------------------
# L2: Number Consistency (Stale Patterns from _canon.yaml)
# ---------------------------------------------------------------------------

def lint_numbers(canon):
    """Check stale patterns defined in _canon.yaml."""
    issues = []

    # Get stale patterns from canon
    stale_patterns = []
    system = canon.get("system", {})
    if isinstance(system.get("stale_patterns"), list):
        stale_patterns = system["stale_patterns"]

    if not stale_patterns:
        return issues

    # Collect active documents
    entry_point = get_entry_point()
    active_files = []
    for pattern in [entry_point, "docs/WORKFLOW.md", "wiki/*.md"]:
        active_files.extend(find_files(pattern))

    for filepath in active_files:
        content = read_file(filepath)
        if not content:
            continue
        rel = str(Path(filepath).relative_to(ROOT))

        for sp in stale_patterns:
            for match in re.finditer(re.escape(sp), content):
                start = max(0, match.start() - 40)
                end = min(len(content), match.end() + 40)
                ctx = content[start:end].replace("\n", " ").strip()
                # Skip if in known-exception context
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

def lint_stale_patterns(canon):
    """Scan for outdated entry point section references."""
    issues = []

    # By default, §0-§5 are valid in the standard entry point template
    # Projects can override by setting system.valid_sections in _canon.yaml
    valid_sections = set(canon.get("system", {}).get("valid_sections", [0, 1, 2, 3, 4, 5]))
    entry_point = get_entry_point()
    entry_point_safe = entry_point.replace(".", r"\.")
    stale_section_pattern = fr"{entry_point_safe}\s*§(\d+)"

    active_files = []
    for pattern in ["docs/WORKFLOW.md", "wiki/*.md"]:
        active_files.extend(find_files(pattern))

    for filepath in active_files:
        content = read_file(filepath)
        if not content:
            continue
        rel = str(Path(filepath).relative_to(ROOT))

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

def lint_orphans(canon):
    """Check for wiki pages not referenced in entry point."""
    issues = []
    entry_point = get_entry_point()
    entry_content = read_file(ROOT / entry_point) or ""

    for wiki_file in find_files("wiki/*.md"):
        rel = str(Path(wiki_file).relative_to(ROOT))
        name = Path(wiki_file).name
        if rel not in entry_content and name not in entry_content:
            issues.append(("L4", "MEDIUM", rel,
                           f"Wiki page not referenced in {entry_point}"))

    return issues

# ---------------------------------------------------------------------------
# L5: log.md Coverage
# ---------------------------------------------------------------------------

def lint_log(canon):
    """Validate log.md format and entry types."""
    issues = []
    log_content = read_file(ROOT / "log.md")
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

def lint_dates(canon):
    """Check header dates in key files."""
    issues = []
    entry_point = get_entry_point()
    for rel_path in [entry_point, "docs/WORKFLOW.md"]:
        filepath = ROOT / rel_path
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

def lint_wiki_format(canon):
    """Verify wiki pages follow W8 template (header + footer)."""
    issues = []
    valid_types = set(canon.get("system", {}).get("wiki_page_types",
                      ["entity", "concept", "operations", "analysis", "craft"]))

    for wiki_file in find_files("wiki/*.md"):
        content = read_file(wiki_file)
        if not content:
            continue
        rel = str(Path(wiki_file).relative_to(ROOT))
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

def lint_original_sync(canon):
    """Check .original.md timestamp consistency."""
    issues = []
    for orig_path in ROOT.rglob("*.original.md"):
        rel_orig = str(orig_path.relative_to(ROOT))
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
            rel_comp = str(compressed.relative_to(ROOT))
            issues.append(("L8", "LOW", rel_comp,
                           "Compressed file missing auto-compressed marker"))
    return issues

# ---------------------------------------------------------------------------
# L9: Vision Anchor Check
# ---------------------------------------------------------------------------

def lint_vision_anchors(canon):
    """Ensure public-facing files contain lexical anchors for every
    identity element declared in _canon.yaml → system.vision_anchors.

    This converts the 2026-04-10 vision-drift recovery into a permanent
    structural safeguard. Authoritative source:
        docs/current/vision_recovery_craft_2026-04-10.md §7
    """
    issues = []
    va = canon.get("system", {}).get("vision_anchors")
    if not va:
        return issues  # feature not configured; skip silently

    targets = va.get("targets", [])
    groups = va.get("groups", [])
    min_hits = int(va.get("min_hits_per_file", 1))
    if not targets or not groups:
        return issues

    for rel_path in targets:
        content = read_file(ROOT / rel_path)
        if content is None:
            issues.append(("L9", "HIGH", rel_path,
                           "Vision-anchor target file not found"))
            continue

        missing_groups = []
        for group in groups:
            name = group.get("name", "?")
            variants = group.get("any_of", []) or []
            hits = sum(content.count(v) for v in variants)
            if hits < min_hits:
                missing_groups.append((name, variants))

        for name, variants in missing_groups:
            sample = " | ".join(variants[:4])
            issues.append(("L9", "CRITICAL", rel_path,
                           f"Vision anchor missing: group '{name}' "
                           f"(none of: {sample})"))

    return issues

# ---------------------------------------------------------------------------
# L10: Notes Schema — validate frontmatter on every notes/*.md
# ---------------------------------------------------------------------------

_FRONTMATTER_RE = re.compile(
    r"^---\s*\n(?P<fm>.*?\n)---\s*\n(?P<body>.*)$",
    re.DOTALL,
)


def lint_notes_schema(canon):
    """Validate that every notes/*.md has a well-formed frontmatter block
    matching the schema declared in _canon.yaml → system.notes_schema.

    Authoritative runtime is src/myco/notes.py::validate_frontmatter. This
    standalone check mirrors that logic so projects without the myco
    package installed can still lint their notes.
    """
    issues = []
    schema = canon.get("system", {}).get("notes_schema")
    if not schema:
        return issues  # feature not configured; skip silently

    notes_dir = ROOT / schema.get("dir", "notes")
    if not notes_dir.exists():
        return issues  # no notes yet; not a failure

    required_fields = schema.get("required_fields", []) or []
    valid_statuses = set(schema.get("valid_statuses", []) or [])
    valid_sources = set(schema.get("valid_sources", []) or [])
    filename_re = re.compile(schema.get("filename_pattern", r".*\.md$"))
    id_re = re.compile(r"^n_\d{8}T\d{6}_[0-9a-f]{4}$")

    for path in sorted(notes_dir.glob("*.md")):
        rel = str(path.relative_to(ROOT))
        name = path.name

        # Skip non-note files (e.g. README.md) silently — only files
        # starting with 'n_' are subject to schema validation.
        if not name.startswith("n_"):
            continue

        if not filename_re.match(name):
            issues.append(("L10", "MEDIUM", rel,
                           f"Filename does not match schema pattern"))
            continue

        content = read_file(path)
        if content is None:
            issues.append(("L10", "HIGH", rel, "Cannot read notes file"))
            continue

        m = _FRONTMATTER_RE.match(content)
        if not m:
            issues.append(("L10", "CRITICAL", rel,
                           "Missing YAML frontmatter block (--- ... ---)"))
            continue

        try:
            meta = yaml.safe_load(m.group("fm")) or {}
        except yaml.YAMLError as e:
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
                           f"Invalid status {status!r}; expected one of {sorted(valid_statuses)}"))

        source = meta.get("source")
        if valid_sources and source is not None and source not in valid_sources:
            issues.append(("L10", "MEDIUM", rel,
                           f"Invalid source {source!r}; expected one of {sorted(valid_sources)}"))

        tags = meta.get("tags")
        if tags is not None and not isinstance(tags, list):
            issues.append(("L10", "MEDIUM", rel, "tags must be a list"))

        dc = meta.get("digest_count")
        if dc is not None and not isinstance(dc, int):
            issues.append(("L10", "MEDIUM", rel, "digest_count must be integer"))

        pc = meta.get("promote_candidate")
        if pc is not None and not isinstance(pc, bool):
            issues.append(("L10", "MEDIUM", rel, "promote_candidate must be boolean"))

        nid = meta.get("id")
        if nid is not None and not id_re.match(str(nid)):
            issues.append(("L10", "MEDIUM", rel,
                           f"id {nid!r} does not match n_YYYYMMDDTHHMMSS_xxxx"))

        # Status-conditioned checks
        if status == "excreted" and not meta.get("excrete_reason"):
            issues.append(("L10", "HIGH", rel,
                           "excreted notes must have a non-empty excrete_reason"))

        # Filename/id coherence
        stem = path.stem
        if nid and stem != nid:
            issues.append(("L10", "MEDIUM", rel,
                           f"filename stem {stem!r} does not match id {nid!r}"))

    return issues


# ---------------------------------------------------------------------------
# L11: Write Surface — enforce agent write-target whitelist
# ---------------------------------------------------------------------------
# Authoritative contract: docs/agent_protocol.md §1.
# The write_surface.allowed list declares every legal top-level entry.
# Anything else (except dotfiles) triggers HIGH. Anything in
# write_surface.forbidden_top_level triggers CRITICAL, regardless.

def _allowed_match(name, allowed):
    """Return True if top-level name matches any allowed pattern.

    Allowed patterns are either exact filenames (README.md, pyproject.toml)
    or directory names with a trailing slash (notes/, src/). A bare dir
    name (no slash) is also accepted for leniency.
    """
    for pat in allowed:
        pat = pat.rstrip("/")
        if name == pat:
            return True
    return False


def _load_gitignore_names(root):
    """Return a set of literal path/file names appearing in .gitignore.

    Intentionally simple: we only want to suppress L11 HIGH warnings for
    entries the user has explicitly marked as local/ignored. Does NOT
    implement full gitignore glob semantics.
    """
    names = set()
    gi = root / ".gitignore"
    if not gi.exists():
        return names
    try:
        for line in gi.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Strip leading './' and trailing '/'
            if line.startswith("./"):
                line = line[2:]
            if line.endswith("/"):
                line = line[:-1]
            # Only care about top-level names (no nested patterns)
            if "/" in line or "*" in line or "?" in line or "[" in line:
                continue
            names.add(line)
    except OSError:
        pass
    return names


def lint_write_surface(canon):
    issues = []
    ws = canon.get("system", {}).get("write_surface")
    if not ws:
        return issues  # feature not configured; skip silently

    allowed = ws.get("allowed", []) or []
    forbidden = set(ws.get("forbidden_top_level", []) or [])
    gitignored = _load_gitignore_names(ROOT)

    # --- Pass 1: top-level entries ---
    try:
        top_entries = sorted(os.listdir(ROOT))
    except OSError:
        return issues

    for name in top_entries:
        # Skip hidden dotfiles/dotdirs (.git, .github, .gitignore, .venv, ...)
        if name.startswith("."):
            continue
        # Skip common build / cache directories that are gitignored.
        if name in {"__pycache__", "build", "node_modules", "venv", "env"}:
            continue
        # Skip egg-info build artifacts.
        if name.endswith(".egg-info"):
            continue

        # Forbidden anti-patterns override everything (even gitignore).
        if name in forbidden or (name + "/") in forbidden:
            issues.append(("L11", "CRITICAL", name,
                           "Forbidden top-level entry (anti-pattern). "
                           "See docs/agent_protocol.md §1."))
            continue

        # Skip entries explicitly gitignored — they are acknowledged
        # local / internal files, not agent contract violations.
        if name in gitignored:
            continue

        if not _allowed_match(name, allowed):
            issues.append(("L11", "HIGH", name,
                           "Top-level entry not in write_surface.allowed. "
                           "If legitimate, add to _canon.yaml; otherwise "
                           "remove or move into an allowed location."))

    # --- Pass 2: notes/ must contain only n_*.md (or README.md) ---
    notes_dir = ROOT / "notes"
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

    # --- Pass 3: wiki/ must be markdown only (v1.2 rule) ---
    wiki_dir = ROOT / "wiki"
    if wiki_dir.exists() and wiki_dir.is_dir():
        for path in sorted(wiki_dir.rglob("*")):
            if path.is_file() and path.suffix not in {".md", ""}:
                rel = path.relative_to(ROOT)
                issues.append(("L11", "MEDIUM", str(rel),
                               "wiki/ should contain markdown only"))

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    quick_mode = "--quick" in sys.argv
    fix_report = "--fix-report" in sys.argv

    print(bold(f"\n{'='*60}"))
    print(bold(f"  Myco Knowledge System Lint"))
    print(bold(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"))
    print(bold(f"{'='*60}\n"))

    canon = load_canon()

    checks = [
        ("L0 Canon 自检", lint_canon_schema),
        ("L1 引用完整性", lint_references),
        ("L2 数字一致性", lint_numbers),
        ("L3 过时模式扫描", lint_stale_patterns),
    ]
    if not quick_mode:
        checks.extend([
            ("L4 孤儿文档检测", lint_orphans),
            ("L5 log.md 覆盖度", lint_log),
            ("L6 日期一致性", lint_dates),
            ("L7 Wiki 格式一致性", lint_wiki_format),
            ("L8 .original 同步检查", lint_original_sync),
            ("L9 愿景锚点检查", lint_vision_anchors),
            ("L10 Notes 结构检查", lint_notes_schema),
            ("L11 写入面白名单", lint_write_surface),
        ])

    all_issues = []
    for name, checker in checks:
        print(cyan(f"  Checking {name}..."))
        issues = checker(canon)
        all_issues.extend(issues)
        if issues:
            print(yellow(f"    → {len(issues)} issue(s) found"))
        else:
            print(green(f"    → PASS"))

    if quick_mode:
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


if __name__ == "__main__":
    sys.exit(main())
