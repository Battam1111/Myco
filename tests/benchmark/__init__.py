"""Benchmark suite for the Myco mycelium graph builder.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/circulation.md``
(the graph this suite stresses) and ``docs/architecture/L2_DOCTRINE/
homeostasis.md`` (the "scale invariants" L2 line — graph build must
extrapolate to 10K-file substrates).

Tests in this package are NOT part of the regular ``pytest`` run.
They opt in only when ``MYCO_RUN_BENCHMARKS=1`` is set in the
environment, so the unit + integration suites stay fast. See
``tests/benchmark/README.md`` for how to run, what each test
measures, and the baselines pinned in ``baselines.json``.
"""
