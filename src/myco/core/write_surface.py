"""Write-surface policy + guarded-write helper.

v0.5.8 upgraded R6 (the "write only to allowed surface" hard-contract
rule) from "checked by `immune --fix`" to "enforced on every
kernel-side write". Previously every verb that mutated the substrate
(`eat`, `sporulate`, `ramify`, `fruit`, `molt`, `propagate`,
`germinate`, `boot_brief.patch_entry_point`) wrote bytes directly with
no check against `canon.system.write_surface.allowed`. The audit
classified this as a P0 trust-boundary break.

This module is the chokepoint every kernel write now routes through:

    from myco.core.write_surface import guarded_write
    guarded_write(ctx, path, content)

The helper:

1. Resolves ``path`` to a substrate-relative POSIX string.
2. Matches that path against ``ctx.substrate.canon.system.write_surface.allowed``
   using glob semantics.
3. If allowed, delegates to :func:`myco.core.io_atomic.atomic_utf8_write`
   for the actual write (atomic + UTF-8 + LF-normalised).
4. If disallowed, either raises :class:`WriteSurfaceViolation` OR, when
   the ``MYCO_ALLOW_UNSAFE_WRITE=1`` environment variable is set, logs
   the bypass and proceeds.

The bypass is intentional — certain workflows (test tmp dirs, scripted
ingest) need write access outside the declared surface. The env var
makes it explicit; the bypass is audited by immune (future SE-class
dim via the ``.myco_state/unsafe_writes.log`` trail, TODO v0.5.9).

The helper imports ``ctx`` lazily (by type-name) to avoid a
core→runtime circular import. Callers pass a ``MycoContext`` instance.
"""

from __future__ import annotations

import fnmatch
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .errors import MycoError
from .io_atomic import atomic_utf8_write

if TYPE_CHECKING:
    from .context import MycoContext

__all__ = [
    "WriteSurfaceViolation",
    "UNSAFE_WRITE_ENV",
    "is_path_allowed",
    "guarded_write",
]


#: Environment variable that, when set to "1" / "true" / "yes" / "on",
#: allows :func:`guarded_write` to proceed on a disallowed path. Used
#: by test fixtures (conftest sets this at session scope) and by
#: users who knowingly need to write outside the surface.
UNSAFE_WRITE_ENV = "MYCO_ALLOW_UNSAFE_WRITE"


class WriteSurfaceViolation(MycoError):
    """Raised when a kernel write targets a path outside
    ``_canon.yaml::system.write_surface.allowed`` and the unsafe-write
    bypass is not set.

    Exit code 3 inherited from :class:`MycoError`. Caller-friendly
    message names the path and the surface it violated.
    """


def _unsafe_bypass_enabled() -> bool:
    """Return True if MYCO_ALLOW_UNSAFE_WRITE is truthy."""
    value = os.environ.get(UNSAFE_WRITE_ENV, "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def _normalise_to_substrate_relative(
    path: Path, substrate_root: Path
) -> str | None:
    """Return ``path`` as a POSIX substrate-relative string, or None
    if ``path`` escapes ``substrate_root``.

    Matches the pattern used elsewhere in the kernel (``graph._rel``).
    The relative path uses ``/`` separators regardless of platform so
    the glob match is portable.
    """
    try:
        # Prefer resolve() so that symlinks that cross into / out of
        # the substrate surface to their real destination before the
        # glob check. This is a security property: an attacker-
        # planted symlink at `notes/evil → /etc/passwd` would pass
        # a naive basename-based check but fail resolve-then-match.
        resolved = path.resolve()
        rel = resolved.relative_to(substrate_root.resolve())
    except (ValueError, OSError):
        return None
    return str(rel).replace(os.sep, "/")


def is_path_allowed(
    path: Path,
    ctx: "MycoContext",
) -> tuple[bool, str | None]:
    """Check whether ``path`` falls within the substrate's declared
    write surface.

    Returns ``(True, rel)`` when allowed (``rel`` is the
    substrate-relative POSIX string that matched a rule) or
    ``(False, rel_or_None)`` when not. The second element is the
    relative path if it could be computed, or None if ``path`` escapes
    the substrate root entirely (still disallowed).

    The canon's ``system.write_surface.allowed`` is read as a list of
    fnmatch-style globs. A path is allowed when ANY glob matches.

    Missing-canon case: if the canon cannot be read or the
    ``write_surface.allowed`` list is absent/empty, returns ``(False,
    rel)`` — the default is strict, matching R6's "any other path is
    substrate pollution".
    """
    substrate_root = ctx.substrate.root
    rel = _normalise_to_substrate_relative(path, substrate_root)
    if rel is None:
        return (False, None)

    try:
        surface: Any = ctx.substrate.canon.system.write_surface
        patterns: list[str] = list(surface.allowed)
    except AttributeError:
        return (False, rel)

    for pattern in patterns:
        # fnmatch.fnmatch is case-insensitive on Windows; we want
        # case-sensitive matching because substrate paths are
        # case-sensitive on POSIX (the write surface is a substrate
        # contract, not a filesystem one). Use fnmatchcase explicitly.
        if fnmatch.fnmatchcase(rel, pattern):
            return (True, rel)

    return (False, rel)


def guarded_write(
    ctx: "MycoContext",
    path: Path,
    content: str,
    *,
    newline: str | None = "\n",
    encoding: str = "utf-8",
    make_parents: bool = True,
) -> str:
    """Write ``content`` to ``path`` iff ``path`` is within the
    substrate's write surface.

    On success, returns the substrate-relative POSIX path for the
    caller to log / surface in Result payloads. On disallowed path,
    raises :class:`WriteSurfaceViolation` unless ``MYCO_ALLOW_UNSAFE_WRITE``
    is set, in which case the bypass is taken and the write proceeds.

    All actual bytes are written via :func:`atomic_utf8_write` so the
    write is atomic + UTF-8 + LF-normalised regardless of platform.
    """
    allowed, rel = is_path_allowed(path, ctx)
    if not allowed:
        if _unsafe_bypass_enabled():
            # Caller has explicitly opted in. Proceed with the write.
            # TODO v0.5.9: append to .myco_state/unsafe_writes.log for
            # future SE-class dimension that surfaces bypass frequency.
            pass
        else:
            surface_list = []
            try:
                surface_list = list(
                    ctx.substrate.canon.system.write_surface.allowed
                )
            except AttributeError:
                pass
            raise WriteSurfaceViolation(
                f"refusing to write outside allowed surface: "
                f"{rel if rel is not None else path} is not matched "
                f"by any pattern in "
                f"canon.system.write_surface.allowed = {surface_list}. "
                f"To override explicitly, set "
                f"{UNSAFE_WRITE_ENV}=1 in the environment."
            )

    atomic_utf8_write(
        path,
        content,
        newline=newline,
        encoding=encoding,
        make_parents=make_parents,
    )
    return rel if rel is not None else str(path)
