"""Myco — Agent-First symbiotic cognitive substrate.

Root package. Per L1 ``versioning.md``, ``__version__`` is the **single
source of truth** for the package version; ``pyproject.toml`` reads it
dynamically via Hatchling and ``surface/cli.py`` reads it to render
``--help``.

Convention: during active development of a minor release, the package
carries the ``.dev`` suffix. The suffix is dropped at the release
commit. Examples: ``0.4.0.dev`` → ``0.4.0`` at the v0.4.0 release;
``0.4.1.dev`` → ``0.4.1`` at the v0.4.1 release.
"""

__version__ = "0.5.18"
