"""``myco.circulation`` — 万物互联 (mycelium graph).

Governing doctrine: ``docs/architecture/L2_DOCTRINE/circulation.md``.

Responsibility: the link graph inside a substrate (``graph`` +
``traverse``) and the inter-substrate publication path
(``propagate``, redefined per §9 E4 as "publish integrated/
distilled notes into a downstream substrate's inbox" — not file
sync, not bidirectional).

v0.5.3: ``perfuse`` was renamed to ``traverse`` (the verb walks the
mycelial graph to report anastomotic health; ``perfuse`` was
borrowed from animal circulation metaphor). Internal function name
stays ``perfuse()`` to minimize churn.
"""

from .graph import (
    Edge,
    Graph,
    build_graph,
    invalidate_graph_cache,
    load_persisted_graph,
    persist_graph,
)
from .propagate import propagate
from .traverse import perfuse

__all__ = [
    "Edge",
    "Graph",
    "build_graph",
    "invalidate_graph_cache",
    "load_persisted_graph",
    "perfuse",
    "persist_graph",
    "propagate",
]
