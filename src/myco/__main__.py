"""``python -m myco`` entry point.

During Stage A / Stage B.1–B.6 this deliberately raises
``NotImplementedError``. The real entry is wired in Stage B.7 when
``surface/cli.py`` lands. Raising loudly (rather than silently noop-ing
or producing a cryptic ``ImportError``) documents the target shape and
forces Stage B.7 to land before any v0.4.0 release candidate.
"""


def _unimplemented() -> None:
    raise NotImplementedError(
        "myco.surface.cli:main is not implemented yet. "
        "The CLI surface lands in Stage B.7 of the v0.4.0 rewrite; "
        "until then `python -m myco` has no behavior. See "
        "docs/architecture/L3_IMPLEMENTATION/migration_strategy.md."
    )


if __name__ == "__main__":
    _unimplemented()
