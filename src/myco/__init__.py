"""Myco — Agent-First symbiotic cognitive substrate.

Root package. Per L1 ``versioning.md``, ``__version__`` is the **single
source of truth** for the package version; ``pyproject.toml`` reads it
dynamically via Hatchling and ``surface/cli.py`` reads it to render
``--help``.

Convention: during active development of a minor release, the package
carries the ``.dev`` suffix. The suffix is dropped at the release
commit. Examples: ``0.4.0.dev`` → ``0.4.0`` at the v0.4.0 release;
``0.4.1.dev`` → ``0.4.1`` at the v0.4.1 release.

v0.6.0 (2026-04-28) is the unified evolution + thorough refactor
release. See ``docs/primordia/_landed/v0_6_x/v0_6_0_unified_evolution_and_thorough_refactor_craft_2026-04-28.md``
for the LANDED craft. Per ``L0_VISION.md:223`` v0.6 is a MAJOR-class
release (re-audits Living Bets), even though the SemVer label reads
"MINOR" — Myco's contract semantics override the naming convention.

Note on ``post1`` suffix (PEP 440): the canonical release is v0.6.0.
The ``.post1`` suffix on ``__version__`` exists solely to dodge the
PyPI namespace burn on ``myco-0.6.0-py3-none-any.whl`` (the filename
was used by an earlier experimental release run and PyPI permanently
forbids re-uploading deleted filenames per supply-chain policy).
``server.json::version``, ``plugin.json::version``, ``CITATION.cff``,
and the git tag remain at ``"0.6.0"`` — only the PyPI artifact wears
the ``.post1`` suffix. Per PEP 440 §post-releases, ``0.6.0.post1`` is
not a version increment; it is "the same 0.6.0 release with a fresh
artifact name".
"""

__version__ = "0.8.7"
