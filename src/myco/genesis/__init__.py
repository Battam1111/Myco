"""``myco.genesis`` — one-time substrate bootstrap.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/genesis.md``.
Lands in Stage B.3.

Responsibility: create the initial substrate from scratch — write a fresh
``_canon.yaml`` from template, seed ``notes/``, and register the
substrate with any parent mycelium. Genesis is idempotent but one-shot:
repeat invocations on an already-seeded substrate are a no-op.
"""
