"""``myco.circulation`` — 万物互联 (mycelium graph).

Governing doctrine: ``docs/architecture/L2_DOCTRINE/circulation.md``.

Responsibility: the link graph inside a substrate (``graph`` + ``perfuse``)
and the inter-substrate publication path (``propagate``, redefined per
§9 E4 as "publish integrated/distilled notes into a downstream
substrate's inbox" — not file sync, not bidirectional).
"""

from .graph import Edge, Graph, build_graph
from .perfuse import perfuse
from .propagate import propagate

__all__ = ["Edge", "Graph", "build_graph", "perfuse", "propagate"]
