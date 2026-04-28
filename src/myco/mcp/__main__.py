"""``python -m myco.mcp`` legacy entry point (v0.6.13+).

Back-compat redirect to :func:`myco.boundary.mcp.main`. Importing
this module triggers the stderr deprecation pointer in
``myco/mcp/__init__.py``; we then delegate the actual server boot
to the canonical entry point so behaviour is byte-identical to
``python -m myco.boundary.mcp``.

See ``myco.mcp.__init__`` docstring for the full migration
rationale and removal schedule.
"""

from __future__ import annotations

import sys

# The import below triggers ``myco.mcp.__init__`` which emits the
# deprecation pointer to stderr exactly once per process spawn.
from myco.mcp import main

if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
