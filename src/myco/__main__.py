"""``python -m myco`` entry point.

Delegates to :func:`myco.boundary.surface.cli.main`.
"""

from __future__ import annotations

import sys

from myco.boundary.surface.cli import main

if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
