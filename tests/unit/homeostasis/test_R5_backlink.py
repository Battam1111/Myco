"""tests/unit/surface/test_R5_backlink.py — R5 behavioral contract (v0.6.0).

Per craft v0.6.0 §K.2: behavioral contract for R5
"cross-reference on creation". SE4 dim emits when a doctrine→src
or craft→source-note link is one-way (no reciprocal back-link).
"""

from __future__ import annotations

from myco.homeostasis.dimensions.semantic.se4_reciprocal_backlink import (
    SE4ReciprocalBacklink,
)


def test_se4_dim_id():
    dim = SE4ReciprocalBacklink()
    assert dim.id == "SE4"
    assert dim.category.value == "semantic"


def test_se4_v0_6_0_empty_whitelist():
    """SE4 v0.6.0 ships with an empty white-list per the dim's docstring.

    The dim infrastructure is registered; specific reciprocal-pair
    patterns to enforce are codified in v0.6.x patches.
    """
    dim = SE4ReciprocalBacklink()
    assert dim.fixable is False
    # v0.6.0 emit-zero-finding-by-design (whitelist empty).
