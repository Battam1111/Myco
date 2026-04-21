"""Deprecation shim for ``myco.meta`` → ``myco.cycle``.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/homeostasis.md``
§ "Governance verbs" (the senesce / fruit / molt / winnow / ramify
/ graft cluster). The old ``meta`` name predated the v0.5.3 fungal
vocabulary rename; both import paths resolve through v1.0.0.

v0.5.3 renamed the cross-cutting verb-composer package ``meta`` →
``cycle`` because every verb it holds (``germinate``/``fruit``/
``molt``/``winnow``/``ramify``/``senesce``/``graft``) is a life-
cycle event of the fungal substrate. "meta" was a programming-
meta-ism, "cycle" matches the biology. Shim preserves every v0.5.x
import path. Scheduled for removal at v1.0.0.

Particularly important: ``from myco.meta import session_end_run``
was the public-surface name for v0.4 and the backward-compat re-
export at v0.5.0-v0.5.2. It keeps importing here with the old name.

Submodule re-exports (bump/craft/evolve/scaffold/session_end):
loading ``myco.meta.<old_name>`` returns the renamed ``myco.cycle``
module under the old name so pre-v0.5.3 test suites continue to
import them unchanged.
"""

from __future__ import annotations

import sys as _sys
import warnings as _w

from myco.cycle import (
    fruit as _fruit_mod,
)
from myco.cycle import (
    molt as _molt_mod,
)
from myco.cycle import (
    ramify as _ramify_mod,
)
from myco.cycle import (
    senesce as _senesce_mod,
)
from myco.cycle import (
    winnow as _winnow_mod,
)
from myco.cycle.senesce import run as session_end_run

_WARNED = False


def _warn_once() -> None:
    global _WARNED
    if _WARNED:
        return
    _WARNED = True
    _w.warn(
        "myco.meta is a deprecated shim for myco.cycle "
        "(renamed at v0.5.3 for fungal-vocabulary consistency: "
        "every verb is a life-cycle event). Both import paths work "
        "across the 0.x line; the shim is scheduled for removal at "
        "v1.0.0.",
        DeprecationWarning,
        stacklevel=2,
    )


_warn_once()


# Re-export the renamed modules under their v0.5.0-v0.5.2 names so
# ``from myco.meta.scaffold import _handler_path`` and cousins keep
# resolving without an edit to the caller.
craft = _fruit_mod
bump = _molt_mod
evolve = _winnow_mod
scaffold = _ramify_mod
session_end = _senesce_mod

# Register them in ``sys.modules`` so `import myco.meta.scaffold`
# works (not just `from myco.meta import scaffold`).
for _alias, _mod in (
    ("craft", _fruit_mod),
    ("bump", _molt_mod),
    ("evolve", _winnow_mod),
    ("scaffold", _ramify_mod),
    ("session_end", _senesce_mod),
):
    _sys.modules[f"myco.meta.{_alias}"] = _mod


__all__ = [
    "session_end_run",
    "craft",
    "bump",
    "evolve",
    "scaffold",
    "session_end",
]
