"""``python -m myco.boundary.install`` entry point. Delegates to :func:`main`."""

from __future__ import annotations

import sys

from myco.boundary.install import main

if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
