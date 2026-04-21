"""Version primitives.

Governing doctrine: ``docs/architecture/L1_CONTRACT/versioning.md``
(contract version grammar + package version sync rules; consumed
by :class:`SH1PackageVersionRef`).

Two grammars are supported — one for package versions (PEP 440 subset)
and one for contract versions (``vMAJOR.MINOR.PATCH[-<tag>]``). Both
are deliberately minimal re-implementations rather than delegating to
``packaging`` — we only need internal ordering and equality, not
parity with PyPI's version grammar. Widening either grammar is a
contract change that gets its own craft.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import ClassVar

__all__ = ["PackageVersion", "ContractVersion"]


_PACKAGE_RE = re.compile(
    r"^(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)"
    r"(?:\.dev(?P<dev>\d*))?$"
)
_CONTRACT_RE = re.compile(
    r"^v?(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)"
    r"(?:-(?P<tag>[A-Za-z0-9._-]+))?$"
)


@dataclass(frozen=True, order=True)
class PackageVersion:
    """PEP 440 subset: ``MAJOR.MINOR.PATCH`` optionally with ``.devN``.

    Ordering: ``0.4.0.dev < 0.4.0 < 0.4.1``. Within the ``.dev`` track,
    ``.dev`` (no number) sorts *before* ``.dev0``, which sorts before
    ``.dev1``, etc.
    """

    # Ordering key — plain ``.dev`` sorts before ``.dev<n>`` (represented
    # by (0, 0)) which in turn sorts before a finalized release (1, 0).
    major: int
    minor: int
    patch: int
    _release_kind: int  # 0 = dev, 1 = final
    _dev_num: int

    _GRAMMAR: ClassVar[str] = "MAJOR.MINOR.PATCH[.devN]"

    @classmethod
    def parse(cls, text: str) -> PackageVersion:
        """Parse ``text`` (``MAJOR.MINOR.PATCH[.devN]``) into a ``PackageVersion``.

        Raises ``ValueError`` on shape mismatch. Accepts ``.dev``
        (anonymous dev) as well as ``.dev<int>`` (numbered).
        """
        m = _PACKAGE_RE.match(text)
        if not m:
            raise ValueError(f"not a valid package version ({cls._GRAMMAR}): {text!r}")
        dev = m.group("dev")
        if dev is None:
            kind, num = 1, 0
        else:
            kind, num = 0, int(dev) if dev else -1
        return cls(
            int(m["major"]),
            int(m["minor"]),
            int(m["patch"]),
            kind,
            num,
        )

    def __str__(self) -> str:  # pragma: no cover - trivial
        base = f"{self.major}.{self.minor}.{self.patch}"
        if self._release_kind == 1:
            return base
        return f"{base}.dev" if self._dev_num == -1 else f"{base}.dev{self._dev_num}"


@dataclass(frozen=True, order=True)
class ContractVersion:
    """``vMAJOR.MINOR.PATCH[-<tag>]``.

    The leading ``v`` is optional on read and normalized away; ``__str__``
    re-adds it. The pre-release tag is compared lexicographically; this
    happens to work for ``alpha.1 < alpha.2 < beta.1`` and we accept the
    narrow scope (widen via craft if we ever outgrow it).
    """

    major: int
    minor: int
    patch: int
    # Ordering key — absence of tag (final release) must sort AFTER any
    # tagged pre-release. ``(1, "")`` > ``(0, tag)`` for all tags.
    _has_final: int  # 0 = has pre-release tag, 1 = final
    _tag: str

    _GRAMMAR: ClassVar[str] = "vMAJOR.MINOR.PATCH[-<tag>]"

    @classmethod
    def parse(cls, text: str) -> ContractVersion:
        """Parse ``text`` (``vMAJOR.MINOR.PATCH[-<tag>]``) into a ``ContractVersion``.

        Leading ``v`` is optional on read and dropped in storage;
        ``__str__`` re-adds it. Raises ``ValueError`` on shape
        mismatch.
        """
        m = _CONTRACT_RE.match(text)
        if not m:
            raise ValueError(f"not a valid contract version ({cls._GRAMMAR}): {text!r}")
        tag = m["tag"] or ""
        return cls(
            int(m["major"]),
            int(m["minor"]),
            int(m["patch"]),
            0 if tag else 1,
            tag,
        )

    def __str__(self) -> str:  # pragma: no cover - trivial
        base = f"v{self.major}.{self.minor}.{self.patch}"
        return f"{base}-{self._tag}" if self._tag else base
