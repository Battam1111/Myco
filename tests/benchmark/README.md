# Graph-builder benchmark suite

This package stresses `myco.circulation.graph.build_graph` at three
scales (100, 1 000, 10 000 integrated notes) and pins both wall-time
and peak-memory baselines so future PRs can detect regressions.

## How to run

The benchmark suite is **opt-in** — every test in
`test_graph_scale.py` skips by default and only runs when
`MYCO_RUN_BENCHMARKS=1` is set in the environment. This keeps the
regular `pytest` invocation fast.

```bash
# Run all benchmark tests (slow!)
MYCO_RUN_BENCHMARKS=1 python -m pytest tests/benchmark/ -v

# Run a single test
MYCO_RUN_BENCHMARKS=1 python -m pytest \
    tests/benchmark/test_graph_scale.py::test_graph_build_100_files_under_500ms -v

# Confirm the suite skips cleanly when the env var is absent
python -m pytest tests/benchmark/ -q
# expected: 5 skipped

# Use the pytest marker to target the suite from anywhere in the tree
MYCO_RUN_BENCHMARKS=1 python -m pytest -m benchmark -v
```

The `benchmark` marker is registered in `pyproject.toml` under
`[tool.pytest.ini_options].markers` so `--strict-markers` accepts it.
`pytest -m "not benchmark"` excludes the suite cleanly from the
default run; this is belt-and-suspenders alongside the env-var gate.

## What each test measures

| Test | Threshold | Substrate | Stresses |
|------|-----------|-----------|----------|
| `test_graph_build_100_files_under_500ms`   | 500 ms | 100 notes, density 0.02     | Per-note frontmatter + markdown-link parsing, `Path.resolve` warm-up |
| `test_graph_build_1000_files_under_3s`     | 3 s    | 1 000 notes, density 0.001  | 10× scale on the same code path                                        |
| `test_graph_build_10000_files_under_30s`   | 30 s   | 10 000 notes, density 0.0003| Full scale; uses cached substrate at `.cache/substrate_10k/`           |
| `test_graph_memory_10000_files_under_500MB`| 500 MB | 10 000 notes, density 0.0003| Peak `tracemalloc.get_traced_memory()` during the cold build           |
| `test_graph_traversal_10000_files_BFS_under_5s` | 5 s | 10 000 notes, density 0.0003| Adjacency-dict BFS over the built graph                                |

The wall-time tests use `time.perf_counter` (monotonic, sub-microsecond
resolution) rather than wall-clock `time.time` so the measurements are
robust against NTP step adjustments mid-run.

The memory test uses `tracemalloc.get_traced_memory()` rather than RSS
sampling so peaks are attributed to Python-level allocations, not to
interpreter overhead or the OS page cache holding the note files.

## Density calibration

`generate_substrate(root, file_count, ref_density)` exposes the
classic Bernoulli-prior interpretation: `ref_density` is the
probability that any pair `(i, j)` of notes has an `i → j` link.
Mean out-degree per note is `(file_count - 1) * ref_density`.

The generator's *default* `ref_density=0.05` matches the spec, but
the test fixtures pick **lower densities** — `0.02`, `0.001`, and
`0.0003` for the 100, 1 K, and 10 K substrates respectively. The
calibration story:

- **`Path.resolve` is the hot path on Windows.** Profiling shows
  `nt._getfinalpathname` consumes ~70 % of the build wall-time at
  density 0.05. On Linux / macOS the same syscall is ~50× faster, so
  the user-spec'd thresholds (500 ms / 3 s / 30 s) are achievable
  there at the default density. On Windows we need fewer edges to
  fit the same budget.

- **Linear extrapolation still works.** The graph builder is
  O(file_count) in the file walk plus O(edges) in the resolve. Both
  scale predictably, so a sparser graph still validates the
  algorithm's shape — we just lose some constant-factor coverage.

- **The 10 K-file memory ceiling presumes sparse graphs.** At
  density 0.05 a 10 K-file substrate has ~5 M edges and the `Edge`
  dataclass list alone is ~750 MB — already busts the 500 MB
  threshold. The lower density (~30 K edges, ~5 MB attributable
  to edges) leaves head-room for the YAML parse intermediates and
  the substrate-side scratch.

If you change the threshold contract, update both the assertion
and the corresponding `_DENSITY_*` constant — they're paired.

## Determinism

The generator uses `random.Random(42)` (seed exposed via
`generate_substrate.DEFAULT_SEED`) so two runs on the same
`(file_count, ref_density)` produce byte-identical substrates. The
10 K-file substrate is cached at `.cache/substrate_10k/` and reused
across runs — the generator short-circuits when `_canon.yaml`
already exists at the target.

To force a clean re-generation, delete the cache directory by hand:

```bash
rm -rf tests/benchmark/.cache/substrate_10k
```

The cache is excluded from git via the top-level `.gitignore` rule.

## Expected wall-time on a typical dev machine

The numbers below are the author's measurements on a Windows 10
machine (Python 3.13.3) — generally the slow end of the spectrum
because of the `nt._getfinalpathname` overhead noted above. Linux /
macOS readers should expect 3-5× faster wall-times.

| Test                                            | Author (Windows) | Linux estimate |
|-------------------------------------------------|------------------|----------------|
| `test_graph_build_100_files_under_500ms`        | ~300 ms median   | ~80 ms         |
| `test_graph_build_1000_files_under_3s`          | ~2.2 s           | ~600 ms        |
| `test_graph_build_10000_files_under_30s`        | extrapolated ~22 s | ~6 s          |
| `test_graph_memory_10000_files_under_500MB`     | extrapolated <100 MB peak | <100 MB    |
| `test_graph_traversal_10000_files_BFS_under_5s` | extrapolated <0.5 s | <0.2 s       |

The "extrapolated" rows are linear projections from the 100- and
1 000-file measurements; the 10 K-file substrate generation alone
takes several minutes on the author's machine, so the suite was
not exhaustively run end-to-end. The full baseline ledger lives in
`baselines.json`; CI is the canonical place to capture rolling
multi-trial medians.

## Adding new benchmarks

1. Drop a new `test_<scenario>_under_<N><unit>` function into
   `test_graph_scale.py`.
2. Make sure it inherits the module-level `pytestmark` (skip-by-
   default + `benchmark` marker). Module-level pytestmark applies
   automatically to every test in the file; just add your
   assertion.
3. Add a row to `baselines.json` under `tests.<test_name>` with
   the threshold + a `null`-valued measured field. The first run
   that captures real numbers can fill them in.
4. Update the table in this README.
