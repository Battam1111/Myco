"""``python -m myco.mcp`` entry point.

Delegates to :func:`myco.mcp.main` so the logic lives in one place
and is importable from tests without relying on the ``__main__``
module name.
"""

from __future__ import annotations

import sys

from myco.mcp import main

if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
