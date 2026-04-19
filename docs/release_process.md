# Myco Release Process

> **Status**: introduced v0.5.7. Canonical runbook for shipping a new
> Myco release to the four delivery channels (git main, git tag,
> GitHub Release, PyPI). Replaces the implicit "read CHANGELOG
> verification commands" runbook that governed v0.4 – v0.5.6.
> **Audience**: the Agent shipping the release, humans reviewing it.

---

## Prerequisites

1. **Clean tree with no uncommitted work.** `git status` must show
   nothing before a release commit is authored — mixing release work
   with unrelated edits makes the commit un-reviewable.
2. **Owner authorization.** User has explicitly said "ship vX.Y.Z".
   Never release on inference. Uncertain? Ask.
3. **CI green on `main`.** The `.github/workflows/ci.yml` pipeline
   must pass on the commit that will be tagged. Releasing a red
   commit burns a PyPI filename (PyPI does not allow republishing a
   tarball with the same name) and creates downstream breakage.
4. **Target channels enabled.** `twine` configured with PyPI
   credentials (either `~/.pypirc` or `TWINE_PASSWORD` env var);
   `gh` CLI authenticated against the `Battam1111/Myco` repo.

---

## Step 1 — Bump version sources (5 places)

A Myco release bumps five independent files. Missing any one is
either a test failure or a silent drift:

| File | Field | Notes |
|---|---|---|
| `src/myco/__init__.py` | `__version__` | Single source of truth — pyproject uses `dynamic = ["version"]` with Hatchling pointing here. |
| `_canon.yaml` | `contract_version` | Bump for any L1/L2 change. Stays aligned with `synced_contract_version`. |
| `_canon.yaml` | `synced_contract_version` | Always equals `contract_version` on a clean `assimilate`. |
| `_canon.yaml` | `metrics.test_count` | Current `pytest --collect-only -q` count. Stale values here are the SE2-class drift the audit catches. |
| `.claude-plugin/plugin.json` | `version` | Pinned to `myco.__version__` by `test_plugin_version_tracks_package_version`. |

The canonical way to bump `contract_version` + `synced_contract_version`
+ `docs/contract_changelog.md` entry in one shot is:

```bash
python -m myco molt --contract vX.Y.Z
```

`molt` refuses if the canon is already at the new version and refuses
invalid version strings. The other two files (`__init__.py` and
`plugin.json`) are bumped by hand.

---

## Step 2 — Update CHANGELOG + contract_changelog

- `CHANGELOG.md`: move the current `[Unreleased]` block's contents
  into a new `[X.Y.Z] — <YYYY-MM-DD>` block; re-open an empty
  `[Unreleased]` block above. Keep-a-Changelog format.
- `docs/contract_changelog.md`: prepend a new top section if the
  release bumps `contract_version`. Describe the contract-surface
  delta (R1–R7 wording, verb count, dimension count, schema shape).

Both files are mechanically checked at release time: an audit pass
that finds an empty `[X.Y.Z]` block or a `contract_version` with no
matching changelog entry fires SE2.

---

## Step 3 — Verify before tagging

Run all five gates locally. Any red = stop.

```bash
pytest -q                               # all tests green
python -m mypy src/myco                 # mypy 0 errors
python -m ruff check src tests          # ruff 0 errors
python -m ruff format --check src tests # ruff format drift 0
python -m myco immune                   # immune 0 findings
python -m build && python -m twine check dist/*
```

---

## Step 4 — Commit + tag

One commit bundles everything the release contains:

```bash
git add -A
git commit -m "vX.Y.Z — <short topic>"
git tag -a vX.Y.Z -m "vX.Y.Z release"
```

Never amend a release commit after the tag lands. If something's
wrong, bump to `vX.Y.(Z+1)` with a fresh commit. PyPI filename burn
is permanent.

---

## Step 5 — Push main + tag

```bash
git push origin main
git push origin vX.Y.Z
```

CI runs on both `main` push and the tag push. Wait for both to
return green before proceeding.

---

## Step 6 — GitHub Release

```bash
gh release create vX.Y.Z \
    --title "vX.Y.Z — <short topic>" \
    --notes-file <path-to-release-notes.md> \
    dist/*.whl dist/*.tar.gz
```

Release notes should include:
- Short headline (1-2 sentences).
- Highlights (3-5 bullets).
- Pointer to `CHANGELOG.md` for the full entry.
- Pointer to the governing craft doc under `docs/primordia/`.
- `myco --version` verification command.

---

## Step 7 — PyPI upload

```bash
python -m twine upload dist/*
```

Set `TWINE_USERNAME=__token__` and `TWINE_PASSWORD=<PyPI-API-token>`
in the shell, or use `~/.pypirc`. Never paste a token into a chat
log or a committed file.

After upload: `pip install myco==X.Y.Z` should succeed from a clean
venv.

---

## Step 8 — Post-release verification

```bash
pip install --no-cache-dir "myco==X.Y.Z"
myco --version                              # reports X.Y.Z
python -c "import myco; print(myco.__version__)"
```

Update the `[Unreleased]` block in `CHANGELOG.md` if new entries have
accumulated during the release window.

---

## Channels summary

Every Myco release lands on **four** channels, all named `vX.Y.Z`:

| Channel | What | Verification |
|---|---|---|
| Git main | Commit on `main` branch | `git log --oneline vX.Y.Z...main` is empty |
| Git tag | Annotated tag `vX.Y.Z` | `git describe --tags --exact-match HEAD` |
| GitHub Release | Release page with sdist + wheel attached | `gh release view vX.Y.Z` |
| PyPI | `myco-X.Y.Z-py3-none-any.whl` + `myco-X.Y.Z.tar.gz` | `pip install --no-cache-dir myco==X.Y.Z` from a fresh venv |

A release is not "done" until all four channels reflect the same
version. Missing one is a shipping drift equivalent to SE2.

---

## Rollback

PyPI does not support deleting a release and re-publishing the same
version. If a released wheel is broken:

1. **Yank**, don't delete, on PyPI (`pip install` warns but still
   works for pinned consumers).
2. Bump to `vX.Y.(Z+1)` and ship the fix immediately.
3. Update `CHANGELOG.md` to note the yank and the replacement
   version.

Never force-push over a release tag. Tag history is contract; break
it and every consumer who pinned to the old SHA loses reproducibility.

---

## Historical precedents

- **v0.5.0 → v0.5.1** (2026-04-17): v0.5.0 tarball filename was burned
  on PyPI due to a metadata error; we jumped to v0.5.1 rather than
  re-upload. The PyPI filename-burn policy is why every release
  commit is non-amendable.
- **v0.5.6** (2026-04-17): introduced the four-channel verification
  table that this doc formalizes.
- **v0.5.7** (2026-04-19): added CI workflow + this runbook so
  shipping the next release does not require reading prior
  CHANGELOG entries to reconstruct the process.
