"""Entry point: ``python -m myco_kernel_bridge``.

Invokes the daemon main loop and exits with its return code.
"""

from __future__ import annotations

import sys

from myco_kernel_bridge.daemon import main


if __name__ == "__main__":
    sys.exit(main())
