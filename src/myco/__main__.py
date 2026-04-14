"""``python -m myco`` entry point.

Delegates to :func:`myco.surface.cli.main`.
"""

from __future__ import annotations

import sys

from myco.surface.cli import main


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
