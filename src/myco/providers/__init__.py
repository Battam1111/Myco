"""Declared opt-in escape hatch for LLM provider coupling.

L0 principle 1 states: *agents call LLMs; the substrate does not
embed provider calls in its own logic.* At v0.5.6 this invariant
became mechanically enforced by the MP1 immune dimension, which
scans ``src/myco/`` for imports of known LLM provider SDKs.

This package is the **single, named, auditable exception** to that
rule. It is intentionally empty at v0.5.6: no concrete provider
module ships with Myco, because the default trust boundary is
"substrate never calls an LLM directly." Any module added here is
MP1-exempt **by path** — MP1 skips the entire
``src/myco/providers/`` subtree during its scan.

That exemption is load-bearing and easy to abuse. The full contract
for adding a concrete provider module is:

1. **Canon flip.** Set ``canon.system.no_llm_in_substrate: false``
   in ``_canon.yaml``. This flips MP1's cross-check from HIGH-
   severity enforcement to LOW-severity surfacing: the agent still
   sees every provider import, but CI no longer gates on them.
   The flag documents to every downstream reader ("this substrate
   embeds provider calls") so no one is surprised later.

2. **Contract-bumping ``molt``.** Run ``myco molt`` (or the v0.5
   equivalent) to advance ``contract_version`` and write an entry
   in ``docs/contract_changelog.md`` explaining *why* this
   substrate is accepting provider coupling. Every consumer of
   the canon sees the bump on their next pull.

3. **Craft approval.** Before the ``molt`` commit, a design craft
   must land under ``docs/primordia/`` (three rounds of
   self-debate/refute/reflect, per the repository's authoring
   norm) naming the specific provider, the failure modes it
   introduces, and the fallback path when the provider is down.

Adding a real provider is reversible: delete the module, flip the
canon field back to ``true``, bump the contract again. MP1 will
start enforcing on the next ``myco immune`` pass.

For most substrates — including Myco's self-substrate at v0.5.7 —
this package should remain empty. The escape hatch exists so the
invariant stays true-by-mechanism rather than
true-because-nobody-needed-to-break-it; embedded provider coupling
that is **named** and **declared** is categorically different from
embedded provider coupling that slipped in by accident.
"""

from __future__ import annotations

__all__: tuple[str, ...] = ()
