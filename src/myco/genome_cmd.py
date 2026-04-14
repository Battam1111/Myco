#!/usr/bin/env python3
"""
Myco Config Command — read/write adapter configuration in _canon.yaml.

Manages the [adapters] section of _canon.yaml, which is reserved for
external tool configuration (MemPalace endpoints, adapter settings, etc.).
The [adapters] section is NOT validated by myco immune — it's external config,
not knowledge consistency. This keeps lint focused on what matters.

Usage:
    myco config --set adapters.mempalace.endpoint http://localhost:8765
    myco config --get adapters.mempalace.endpoint
    myco config --list
    myco config --list adapters
"""

from pathlib import Path

from myco.io_utils import load_yaml_safe


def _find_canon(project_dir: Path) -> Path | None:
    canon = project_dir / "_canon.yaml"
    return canon if canon.exists() else None


def _load_canon(canon_path: Path) -> dict:
    return load_yaml_safe(canon_path)


def _save_canon(canon_path: Path, data: dict):
    try:
        import yaml
    except ImportError:
        raise RuntimeError("pyyaml not installed")
    with open(canon_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def _nested_set(d: dict, key_path: str, value: str):
    """Set a nested key (dot-separated) in dict d."""
    parts = key_path.split(".")
    current = d
    for part in parts[:-1]:
        if part not in current or not isinstance(current[part], dict):
            current[part] = {}
        current = current[part]
    current[parts[-1]] = value


def _nested_get(d: dict, key_path: str):
    """Get a nested key (dot-separated) from dict d. Returns None if not found."""
    parts = key_path.split(".")
    current = d
    for part in parts:
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _flatten(d: dict, prefix: str = "") -> list:
    """Flatten nested dict to list of (key_path, value) pairs."""
    items = []
    for k, v in d.items():
        full_key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            items.extend(_flatten(v, full_key))
        else:
            items.append((full_key, v))
    return items


def run_config(args) -> int:
    project_dir = Path(args.project_dir).resolve()
    canon_path = _find_canon(project_dir)

    if canon_path is None:
        print(f"❌ No _canon.yaml found in {project_dir}")
        print(f"   Run: myco seed <name> --level 1  to create one")
        return 1

    data = _load_canon(canon_path)

    # ── --list ──────────────────────────────────────────────────────
    if args.list is not None:
        section = args.list.strip() if args.list else None

        if section:
            # List a specific section
            sub = _nested_get(data, section)
            if sub is None:
                print(f"  (no configuration under '{section}')")
                return 0
            if isinstance(sub, dict):
                pairs = _flatten(sub, section)
            else:
                pairs = [(section, sub)]
        else:
            # List everything
            pairs = _flatten(data)

        if not pairs:
            print(f"  (empty)")
            return 0

        max_key = max(len(k) for k, _ in pairs)
        for k, v in pairs:
            print(f"  {k:<{max_key}}  =  {v}")
        return 0

    # ── --get ───────────────────────────────────────────────────────
    if args.get:
        key = args.get
        # Validate it's under adapters
        if not key.startswith("adapters.") and key != "adapters":
            print(f"⚠️  myco config only manages 'adapters.*' keys.")
            print(f"   For other _canon.yaml fields, edit the file directly.")
            return 1

        value = _nested_get(data, key)
        if value is None:
            print(f"  (not set)")
            return 0
        print(value)
        return 0

    # ── --set ───────────────────────────────────────────────────────
    if args.set:
        if len(args.set) != 2:
            print(f"❌ Usage: myco config --set <key> <value>")
            return 1
        key, value = args.set

        # Validate it's under adapters
        if not key.startswith("adapters."):
            print(f"⚠️  myco config only manages 'adapters.*' keys.")
            print(f"   Example: myco config --set adapters.mempalace.endpoint http://localhost:8765")
            print(f"   For other _canon.yaml fields, edit the file directly.")
            return 1

        _nested_set(data, key, value)
        _save_canon(canon_path, data)
        print(f"  ✅ {key} = {value}")
        print(f"     (written to {canon_path})")
        return 0

    # ── --unset ─────────────────────────────────────────────────────
    if args.unset:
        key = args.unset
        if not key.startswith("adapters."):
            print(f"⚠️  myco config only manages 'adapters.*' keys.")
            return 1
        parts = key.split(".")
        current = data
        for part in parts[:-1]:
            if not isinstance(current, dict) or part not in current:
                print(f"  (key '{key}' not found — nothing to unset)")
                return 0
            current = current[part]
        if parts[-1] in current:
            del current[parts[-1]]
            _save_canon(canon_path, data)
            print(f"  ✅ Unset: {key}")
        else:
            print(f"  (key '{key}' not found — nothing to unset)")
        return 0

    print("❌ Specify --set, --get, --list, or --unset")
    return 1
