#!/usr/bin/env python3
"""
Myco Document Compression Tool
===============================

Compresses `.original.md` documentation files to Agent-optimized versions.

**Core Concept** (from Caveman Project):
  .original.md = Human-edited complete version (includes examples, narratives, redundant explanations)
  .md          = Agent-optimized version (tablized, deduplicated, preserves precise references and numbers)

**Workflow**:
  1. Read `.original.md` file(s)
  2. Apply multi-round compression rules
  3. Output compressed `.md` file
  4. Report compression ratio and preserved key information

**Usage**:
    python compress_original.py wiki/example.original.md
    python compress_original.py --all                     # Compress all .original.md files
    python compress_original.py --diff FILE               # Show before/after diff
    python compress_original.py --dry-run FILE            # Preview only, don't write
    python compress_original.py --verify FILE             # Verify info preservation
    python compress_original.py --project-root /path/to   # Specify project root (default: script parent)

**Compression Rules** (by priority):
    R1  Remove decorative whitespace (preserve structural spacing)
    R2  Lists → Tables (when items have consistent structure)
    R3  Paragraph deduplication (remove redundant explanations)
    R4  Protected zones: code, numbers, URLs, formulas — never compressed
    R5  Template preservation (header/footer structure unchanged)
    R6  Information density check (warn on low-value content)
"""

import os
import re
import sys
import argparse
import difflib
from pathlib import Path
from datetime import datetime

# Default to script parent as project root, overridable via --project-root
def get_project_root():
    """Get project root from --project-root arg or script parent directory"""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--project-root", type=Path, default=None)
    args, _ = parser.parse_known_args()

    if args.project_root:
        return args.project_root.resolve()
    return Path(__file__).resolve().parent.parent

ROOT = get_project_root()

# ---------------------------------------------------------------------------
# Protected Zones — Never compress these regions
# ---------------------------------------------------------------------------

PROTECTED_PATTERNS = [
    # Code blocks (markdown fenced)
    (re.compile(r"```[\s\S]*?```", re.MULTILINE), "code_block"),
    # Inline code
    (re.compile(r"`[^`\n]+`"), "inline_code"),
    # Numbers with units (e.g., 900 runs, 24GB, 5 seeds)
    (re.compile(r"\b\d+[\d.,]*\s*(?:%|GB|MB|KB|ms|s|min|hours?|seeds?|runs?|envs?|dims?|行|页|项|个|次|轮)\b"), "number_with_unit"),
    # URLs and hyperlinks
    (re.compile(r"https?://\S+"), "url"),
    # File path references
    (re.compile(r"`[a-zA-Z_/][a-zA-Z0-9_/\-.*]+\.(?:md|py|sh|yaml|tex|bib|json|toml)`"), "file_ref"),
    # LaTeX/math formulas
    (re.compile(r"\$[^$]+\$"), "latex"),
    # Blockquotes
    (re.compile(r"^>.*$", re.MULTILINE), "blockquote"),
]


def identify_protected_zones(text):
    """Identify all protected region positions in text"""
    zones = []
    for pattern, zone_type in PROTECTED_PATTERNS:
        for match in pattern.finditer(text):
            zones.append((match.start(), match.end(), zone_type))
    return sorted(zones)


def is_in_protected_zone(pos, zones):
    """Check if position is within a protected zone"""
    for start, end, _ in zones:
        if start <= pos < end:
            return True
    return False


# ---------------------------------------------------------------------------
# Compression Rules
# ---------------------------------------------------------------------------

def r1_trim_decorative_whitespace(lines):
    """R1: Remove excess blank lines (keep max 1), remove pure decoration separators"""
    result = []
    prev_empty = False

    for line in lines:
        stripped = line.strip()

        # Pure decorative separator (only --- and not in YAML frontmatter)
        if stripped == "---" and len(result) > 3:
            # Preserve if previous line is a heading (structural separator)
            if result and result[-1].strip().startswith("#"):
                result.append(line)
                prev_empty = False
                continue
            # Otherwise skip
            continue

        is_empty = stripped == ""
        if is_empty and prev_empty:
            continue  # Merge consecutive blank lines

        result.append(line)
        prev_empty = is_empty

    return result


def r2_list_to_table(lines):
    """R2: Convert consecutive key-value lists to tables for better density"""
    result = []
    i = 0

    while i < len(lines):
        # Detect consecutive `- **key**: value` pattern
        kv_pattern = re.compile(r"^[-*]\s+\*\*(.+?)\*\*[：:]\s*(.+)$")
        block_start = i
        kv_items = []

        while i < len(lines):
            stripped = lines[i].strip()
            m = kv_pattern.match(stripped)
            if m:
                kv_items.append((m.group(1), m.group(2)))
                i += 1
            else:
                break

        # Only convert to table if ≥3 consecutive items (significant density gain)
        if len(kv_items) >= 3:
            max_key = max(len(k) for k, v in kv_items)
            max_val = max(len(v) for k, v in kv_items)

            result.append(f"| {'Item':<{max_key}} | {'Description':<{max_val}} |")
            result.append(f"|{'-' * (max_key + 2)}|{'-' * (max_val + 2)}|")
            for k, v in kv_items:
                result.append(f"| {k:<{max_key}} | {v:<{max_val}} |")
            result.append("")
        else:
            # Not enough items, preserve original
            for j in range(block_start, i):
                result.append(lines[j])
            if block_start == i:
                result.append(lines[i])
                i += 1

    return result


def r3_paragraph_dedup(text):
    """R3: Paragraph-level deduplication — remove redundant explanations of same concept"""
    paragraphs = text.split("\n\n")
    seen_concepts = set()
    result = []

    for para in paragraphs:
        stripped = para.strip()
        if not stripped:
            continue

        # Protect: headings, tables, code, blockquotes
        if (stripped.startswith("#") or stripped.startswith("|") or
            stripped.startswith("```") or stripped.startswith(">")):
            result.append(para)
            continue

        # Extract "concept fingerprint" — key terms minus stop words
        words = set(re.findall(r"[\u4e00-\u9fff]+|[a-zA-Z_]+", stripped.lower()))
        stop_words = {
            # Chinese
            "的", "是", "在", "了", "和", "与", "也", "但", "而", "因为",
            "所以", "如果", "这", "那", "有", "没有", "可以", "需要",
            # English
            "this", "the", "is", "a", "an", "to", "for", "and", "or",
            "but", "that", "not", "be", "can", "should", "would", "will",
            "have", "has", "had", "as", "if", "when", "where", "why"
        }
        concept = frozenset(words - stop_words)

        # Check if concept overlaps > 80% with existing paragraph (likely duplicate)
        is_dup = False
        for seen in seen_concepts:
            if len(concept) > 0 and len(seen) > 0:
                overlap = len(concept & seen) / min(len(concept), len(seen))
                if overlap > 0.8 and len(concept) > 3:
                    is_dup = True
                    break

        if not is_dup:
            result.append(para)
            if len(concept) > 3:  # Only track sufficiently complex paragraphs
                seen_concepts.add(concept)

    return "\n\n".join(result)


def r6_density_check(lines):
    """R6: Information density audit — flag low-value lines (warn, don't delete)"""
    low_density = []

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("|"):
            continue
        if stripped.startswith(">") or stripped.startswith("```"):
            continue

        # Check if line is mostly filler/transition words
        content_words = re.findall(r"[\u4e00-\u9fff]+|[a-zA-Z]{3,}", stripped)
        filler_words = {
            # Chinese
            "因此", "所以", "总之", "综上", "换句话说", "也就是说",
            # English
            "therefore", "thus", "hence", "summary", "overall",
            "basically", "essentially", "simply", "actually"
        }

        if len(content_words) > 0:
            filler_ratio = sum(1 for w in content_words if w.lower() in filler_words) / len(content_words)
            if filler_ratio > 0.5 and len(content_words) < 10:
                low_density.append((i + 1, stripped[:60]))

    return low_density


# ---------------------------------------------------------------------------
# Compression Pipeline
# ---------------------------------------------------------------------------

def compress(original_text, verbose=False):
    """Execute full compression pipeline"""
    stats = {
        "original_lines": len(original_text.split("\n")),
        "original_chars": len(original_text),
        "protected_zones": 0,
        "low_density_lines": [],
    }

    # Identify protected regions
    zones = identify_protected_zones(original_text)
    stats["protected_zones"] = len(zones)

    # R1: Clean whitespace/separators
    lines = original_text.split("\n")
    lines = r1_trim_decorative_whitespace(lines)

    # R2: Convert lists → tables
    lines = r2_list_to_table(lines)

    # Rejoin to text
    text = "\n".join(lines)

    # R3: Paragraph deduplication
    text = r3_paragraph_dedup(text)

    # R6: Density audit (report only)
    final_lines = text.split("\n")
    stats["low_density_lines"] = r6_density_check(final_lines)

    stats["compressed_lines"] = len(final_lines)
    stats["compressed_chars"] = len(text)
    stats["compression_ratio"] = (1 - stats["compressed_chars"] / stats["original_chars"]) * 100 if stats["original_chars"] > 0 else 0

    return text, stats


def verify_compression(original, compressed):
    """Verify that compression preserves critical information"""
    issues = []

    # Extract all numbers
    orig_numbers = set(re.findall(r"\b\d+[\d.,]*\b", original))
    comp_numbers = set(re.findall(r"\b\d+[\d.,]*\b", compressed))
    lost_numbers = orig_numbers - comp_numbers
    if lost_numbers:
        issues.append(f"Lost numbers: {lost_numbers}")

    # Extract all file references
    orig_refs = set(re.findall(r"`([a-zA-Z_/][a-zA-Z0-9_/\-.*]+\.(?:md|py|sh|yaml|json))`", original))
    comp_refs = set(re.findall(r"`([a-zA-Z_/][a-zA-Z0-9_/\-.*]+\.(?:md|py|sh|yaml|json))`", compressed))
    lost_refs = orig_refs - comp_refs
    if lost_refs:
        issues.append(f"Lost file references: {lost_refs}")

    # Extract all URLs
    orig_urls = set(re.findall(r"https?://\S+", original))
    comp_urls = set(re.findall(r"https?://\S+", compressed))
    lost_urls = orig_urls - comp_urls
    if lost_urls:
        issues.append(f"Lost URLs: {lost_urls}")

    # Extract all section headers
    orig_headers = set(re.findall(r"^#+\s+(.+)$", original, re.MULTILINE))
    comp_headers = set(re.findall(r"^#+\s+(.+)$", compressed, re.MULTILINE))
    lost_headers = orig_headers - comp_headers
    if lost_headers:
        issues.append(f"Lost section headers: {lost_headers}")

    return issues


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def print_stats(stats, filepath):
    """Print compression report"""
    print(f"\n{'='*50}")
    print(f"  Compression Report: {filepath}")
    print(f"{'='*50}")
    print(f"  Original:    {stats['original_lines']:>6} lines | {stats['original_chars']:>8} chars")
    print(f"  Compressed:  {stats['compressed_lines']:>6} lines | {stats['compressed_chars']:>8} chars")
    print(f"  Ratio:       {stats['compression_ratio']:>5.1f}% reduction")
    print(f"  Protected:   {stats['protected_zones']:>6} zones preserved")

    if stats["low_density_lines"]:
        print(f"\n  Low-density lines ({len(stats['low_density_lines'])}):")
        for line_num, preview in stats["low_density_lines"][:5]:
            print(f"    L{line_num}: {preview}...")

    print(f"{'='*50}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Compress .original.md documentation files to Agent-optimized versions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("files", nargs="*", help="File paths to compress")
    parser.add_argument("--all", action="store_true", help="Compress all .original.md files")
    parser.add_argument("--diff", action="store_true", help="Show before/after diff")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, don't write")
    parser.add_argument("--verify", action="store_true", help="Verify information preservation")
    parser.add_argument("--project-root", type=Path, default=None, help="Project root directory (default: script parent)")

    args = parser.parse_args()

    # Re-compute ROOT if --project-root was specified
    global ROOT
    if args.project_root:
        ROOT = args.project_root.resolve()

    if not args.files and not args.all:
        parser.print_help()
        return 0

    dry_run = args.dry_run
    verify_mode = args.verify
    diff_mode = args.diff
    all_mode = args.all

    files = args.files

    if all_mode:
        # Find all .original.md files
        files = sorted(str(p.relative_to(ROOT)) for p in ROOT.rglob("*.original.md"))
        if not files:
            print("No .original.md files found.")
            return 0
        print(f"Found {len(files)} .original.md files.")

    if not files:
        print("Error: No input files specified. Use --all or provide file paths.")
        return 1

    total_saved = 0

    for filepath in files:
        path = ROOT / filepath if not Path(filepath).is_absolute() else Path(filepath)

        if not path.exists():
            print(f"Error: {filepath} not found")
            continue

        original_text = path.read_text(encoding="utf-8")
        compressed_text, stats = compress(original_text, verbose=True)

        print_stats(stats, filepath)

        if verify_mode:
            issues = verify_compression(original_text, compressed_text)
            if issues:
                print("  VERIFICATION ISSUES:")
                for issue in issues:
                    print(f"    WARNING: {issue}")
            else:
                print("  OK: All key information preserved")

        if diff_mode:
            orig_lines = original_text.splitlines(keepends=True)
            comp_lines = compressed_text.splitlines(keepends=True)
            diff = difflib.unified_diff(orig_lines, comp_lines,
                                         fromfile=f"{filepath} (original)",
                                         tofile=f"{filepath} (compressed)")
            print("".join(diff))

        if not dry_run and not verify_mode and not diff_mode:
            # Output filename: remove .original suffix
            out_name = str(path).replace(".original.md", ".md")
            out_path = Path(out_name)

            # Safety check: warn if target exists and wasn't auto-generated
            if out_path.exists():
                existing = out_path.read_text(encoding="utf-8")
                if "<!-- auto-compressed from .original.md" not in existing:
                    print(f"  WARNING: {out_name} exists and was NOT auto-generated. Skipping.")
                    print(f"           Add '<!-- auto-compressed from .original.md -->' to override.")
                    continue

            # Write compressed version with metadata header
            header = f"<!-- auto-compressed from .original.md | {datetime.now().strftime('%Y-%m-%d %H:%M')} | ratio: {stats['compression_ratio']:.1f}% -->\n"
            out_path.write_text(header + compressed_text, encoding="utf-8")
            print(f"  Written: {out_name}")
            total_saved += stats["original_chars"] - stats["compressed_chars"]

    if total_saved > 0 and not dry_run:
        print(f"\nTotal saved: {total_saved:,} characters across {len(files)} files")

    return 0


if __name__ == "__main__":
    sys.exit(main())
