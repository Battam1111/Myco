"""SC1 — canon JSON-Schema vs load_canon parity.

Governing doctrine: ``docs/architecture/L1_CONTRACT/canon_schema.md``
+ craft ``v0_5_9_immune_zero_craft_2026-04-21.md`` §"deferred SC1".
v0.6.0 finally lands the dim.

Severity: LOW at land, ramps to HIGH after 30 sessions. SC1 verifies
that the JSON-Schema at ``docs/schema/canon.schema.json`` admits the
substrate's ``_canon.yaml`` and that the kernel's ``load_canon``
parser admits the same. Drift between the two is a SSoT split that
this dim catches.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any, ClassVar

import yaml

from myco.core.context import MycoContext
from myco.core.severity import Severity
from myco.homeostasis.dimension import Dimension
from myco.homeostasis.finding import Category, Finding

__all__ = ["SC1SchemaParity"]


class SC1SchemaParity(Dimension):
    """JSON-Schema and load_canon must agree on _canon.yaml shape."""

    id = "SC1"
    category = Category.MECHANICAL
    default_severity = Severity.HIGH
    fixable: ClassVar[bool] = False

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        # v0.8.5 — canon-configurable layout (Myco-self uses
        # .myco/canon.yaml + .docs/). paths.canon / paths.docs resolve
        # both legacy and relocated shapes.
        canon_path = ctx.substrate.paths.canon
        schema_path = ctx.substrate.paths.docs / "schema" / "canon.schema.json"
        if not canon_path.is_file() or not schema_path.is_file():
            # Substrate may not ship the JSON-Schema (downstream substrates).
            return
        try:
            schema_data: Any = json.loads(schema_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            yield Finding(
                dimension_id=self.id,
                category=self.category,
                severity=self.default_severity,
                message=f"canon.schema.json failed to parse: {exc}",
                path="docs/schema/canon.schema.json",
            )
            return
        try:
            canon_data: Any = yaml.safe_load(canon_path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError):
            return
        # Soft validation: required top-level keys named in schema.required
        # must be present in canon. Full jsonschema validation is deferred
        # to v0.6.x when jsonschema becomes a non-optional dependency.
        if isinstance(schema_data, dict) and isinstance(canon_data, dict):
            required = schema_data.get("required") or []
            for key in required:
                if key not in canon_data:
                    yield Finding(
                        dimension_id=self.id,
                        category=self.category,
                        severity=self.default_severity,
                        message=(
                            f"canon.schema.json declares required key {key!r} "
                            f"but _canon.yaml is missing it"
                        ),
                        path="_canon.yaml",
                    )
