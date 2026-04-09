"""
Template resolution for Myco package.

Uses importlib.resources to locate templates bundled with the package,
so that `pip install myco` users get templates without needing the git repo.
"""

import sys
from pathlib import Path

if sys.version_info >= (3, 9):
    from importlib.resources import files as _resource_files

    def get_templates_dir() -> Path:
        """Return the path to the bundled templates directory."""
        return Path(str(_resource_files("myco") / "templates"))
else:
    # Python 3.8 fallback
    import importlib.resources as _resources

    def get_templates_dir() -> Path:
        """Return the path to the bundled templates directory."""
        with _resources.path("myco", "templates") as p:
            return Path(p)


def get_template(name: str) -> str:
    """Read a template file by name and return its content."""
    path = get_templates_dir() / name
    return path.read_text(encoding="utf-8")


def fill_template(content: str, replacements: dict) -> str:
    """Replace {{PLACEHOLDER}} tokens with actual values."""
    for key, value in replacements.items():
        content = content.replace(f"{{{{{key}}}}}", value)
    return content
