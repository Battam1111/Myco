"""Substrate-local plugin registration for the research-assistant example.

Imported at ``Substrate.load()`` time. Registers the DEC1 local
dimension by calling :func:`register_external_dimension`. See
``docs/architecture/L2_DOCTRINE/extensibility.md`` for the full
plugin-axis protocol.
"""

from __future__ import annotations

from myco.homeostasis.registry import register_external_dimension

from .dimensions.dec1_decision_authors import DEC1DecisionAuthors

register_external_dimension(DEC1DecisionAuthors)
