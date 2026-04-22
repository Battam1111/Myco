# Contributing to Myco

Contributors come in two shapes: humans who mostly read this file, and
agents who mostly execute it. Both are welcome; the rules below are
identical. The agent audience is not an afterthought — Myco is an
Agent-First substrate, and its own maintenance is mostly done by
agents driving a human reviewer.

Before anything else, read
[`docs/architecture/L0_VISION.md`](docs/architecture/L0_VISION.md)
(five root principles) and
[`docs/architecture/L1_CONTRACT/protocol.md`](docs/architecture/L1_CONTRACT/protocol.md)
(seven hard rules). The rest of this file assumes you have.

## Before you start

For anything beyond a typo or a one-line bug fix, **open an issue or a
draft PR first**. Architectural proposals land as dated markdown under
[`docs/primordia/`](docs/primordia/) *before* any code moves —
approved crafts then become the spec the implementation conforms to.
This is not optional; the immune system blocks merges that skip it.

If you are unsure whether a change is "architectural," it probably
is. When in doubt, open a discussion.

## Dev environment

```bash
git clone https://github.com/Battam1111/Myco.git
cd Myco
pip install -e ".[dev,mcp]"
pytest                              # full suite
python -m myco immune               # all 11 lint dimensions green
python -m myco --version
```

That is the entire setup. No pre-commit hooks, no vendored toolchain,
no Docker. If `pytest` or `myco immune` fails on a clean clone of
`main`, that's a bug — file it before anything else.

## Daily loop

Three commands cover 95% of contributor work:

```bash
pytest tests/ -q                    # run tests
python -m myco immune               # run self-substrate lint
python -m myco --json hunger        # see what the substrate wants
```

Tests live at `tests/unit/<subsystem>/` mirroring `src/myco/`. Every
new module gets a matching test file. `myco immune` is authoritative
for "did I break something structural"; CI re-runs it on every PR.

## The top-down rule (L0 → L3)

Changes that touch **identity (L0)**, **contract (L1)**, or
**doctrine (L2)** land as a dated markdown under `docs/primordia/`
before any code moves. The immune system will otherwise fail the PR.
L3 implementation changes do not require a craft doc; L4 substrate
changes (notes under `notes/`) never do.

## The three-round craft convention

When a proposal is architectural, the craft doc under `docs/primordia/`
walks three rounds:

1. **Round 1 — claim.** What change, why now, what it replaces.
2. **Round 2 — rebut.** Every counter-argument you can find against
   your own claim. Do not skip this.
3. **Round 3 — reflect.** What the debate revealed; the final
   decision and its explicit trade-offs.

Bug fixes and ordinary features do not need this. It is a discipline
for decisions that would be hard to reverse.

## What agents should do differently from humans

Agents running inside Claude Code or Cowork should run the boot and
close rituals every session. The plugin hooks fire these
automatically; this block is the fallback when hooks are unavailable:

```
python -m myco hunger --execute     # boot: surface HIGH reflexes first
# ... your actual work ...
python -m myco senesce              # close (full, for /compact): assimilate + immune --fix
python -m myco senesce --quick      # close (quick, for abrupt exits): assimilate only
```

Agents must also:

- Call `myco sense` before asserting any substrate fact — memory is
  not a source.
- Write only to paths declared in
  `_canon.yaml::system.write_surface.allowed`. Any other path is
  substrate pollution and the immune system will reject the commit.
- Capture decisions with `myco eat` the moment they occur, not at
  session end.

## What not to touch without prior discussion

These files are load-bearing for the entire project and changes are
gated by a craft doc + explicit owner approval:

- `_canon.yaml` — identity, write-surface, contract version.
- `src/myco/surface/manifest.yaml` — the single source of truth for
  CLI and MCP verbs. One manifest edit reshapes both surfaces; drifts
  are easy to introduce and hard to detect.
- Any file under `docs/architecture/L0_VISION.md`,
  `docs/architecture/L1_CONTRACT/`, or `docs/architecture/L2_DOCTRINE/`.
- `.claude-plugin/plugin.json` version — pinned to
  `myco.__version__` by test, bumped together at release time.
- Historical CHANGELOG sections — only the current `[Unreleased]`
  block is live; dated releases are frozen.

## Pull-request checklist

A PR is ready when:

- [ ] Tests pass locally (`pytest tests/ -q`).
- [ ] `python -m myco immune` exits 0.
- [ ] A `CHANGELOG.md` entry exists under `[Unreleased]` if the change
      is user-visible (a new flag, a new public function, a new
      manifest verb, a public doc).
- [ ] A craft doc exists under `docs/primordia/` if the change
      touches L0/L1/L2.
- [ ] The PR description says what changed and why — not just what
      files moved.
- [ ] If the change was AI-assisted, a human reviewed it and the PR
      description matches what the diff actually does.

Commit-message style is **not** enforced for external contributors.
Write messages that explain the why; anything clearer than "update"
is welcome. (Maintainers use `Stage X.Y: <description>` internally;
that convention is not required of you.)

## Release automation

`.github/workflows/release.yml` fans every tag push out to the four
channels that must stay in lockstep: PyPI, the MCP Registry, the
GitHub release, and the tagged commit on `main`. The pre-flight
step inside the workflow verifies that `GITHUB_REF` matches
`src/myco/__init__.py`'s `__version__`, `server.json::version`,
`server.json::packages[0].version`, and `.claude-plugin/plugin.json`'s
`version` before anything is published — preventing the "0.5.12 on
PyPI, 0.5.11 in the registry" drift class that tripped us on v0.5.11.

Release ceremony for maintainers (one helper + four git verbs):

```bash
# 1. Atomic bump of every version-carrying file + canon + changelog.
#    Does __init__.py / plugin.json / CITATION.cff / server.json (x2),
#    then runs `myco molt --contract vX.Y.Z`, then runs pytest.
#    Refuses dirty worktree + downgrades by default.
python scripts/bump_version.py --to X.Y.Z

# 2. Replace the `(Fill in: ...)` auto-stub in
#    docs/contract_changelog.md with the real narrative — the
#    Release workflow uses that section as the GitHub-release body.

# 3. Commit, tag, push.
git add -A && git commit -m "vX.Y.Z — <summary>"
git tag vX.Y.Z
git push origin main vX.Y.Z

# 4. Watch the Release workflow (~3 min) publish to PyPI, MCP
#    Registry, and create the GitHub release.
```

For edge cases (pre-releases, rollback), see
``scripts/bump_version.py --help``.

One-time setup (done once per repo, never again):

1. **PyPI trusted publisher.** Visit
   https://pypi.org/manage/project/myco/settings/publishing/ and add a
   publisher with `Owner: Battam1111`, `Repository name: Myco`,
   `Workflow name: release.yml`, `Environment name` blank. Save.
   After this, the workflow's `pypa/gh-action-pypi-publish` step
   uploads via OIDC and no secret is needed in the repo.
2. **MCP Registry GitHub-OIDC.** No UI configuration — the registry
   already trusts any GitHub Actions OIDC token whose repository
   matches a claimed namespace (`io.github.Battam1111/*`).

Fallback if trusted publisher isn't configured: add a PyPI API
token as a repo secret named `PYPI_API_TOKEN` and uncomment the
`with: password:` line in `release.yml`. Works identically, just
less secure.

The workflow is idempotent — if PyPI already has the version, it
`skip-existing: true` silently. If the GitHub release already
exists (you created it manually), it skips that step too. Only
the MCP Registry publish fails noisily on duplicate, which is the
correct behaviour (you don't want to silently "republish" the
same version).

## AI-assisted contributions

Agents are welcome to land changes. The only rule is the one above:
a human must review the PR and the description must match the diff.
Low-quality AI PRs that regenerate half the codebase to fix a typo
waste reviewer time and will be closed — we borrow the
[FastAPI framing](https://fastapi.tiangolo.com/contributing/): a PR
that shifts human effort from contributor to reviewer is a DoS on the
project, not a contribution.

If you are an agent reading this: run `myco hunger` before touching
anything, call `myco sense` before asserting substrate facts, capture
decisions with `myco eat` as you go. The substrate's own discipline
is a good proxy for "will this PR land cleanly."

## Reporting bugs

A good bug report includes:

- `python -m myco --version` output.
- Platform + Python version.
- Minimal reproduction (smallest substrate, smallest command
  sequence).
- `python -m myco --json immune` output if the bug is structural.
- Expected vs actual behavior.

If you suspect a regression, `git bisect` against `v0.4.0` is usually
faster than a maintainer guessing.

## Governance

One maintainer has final say on merges. Reviewers are welcome —
anyone may review anyone's PR. Nobody merges their own code.

## Code of Conduct

Be kind. We follow the spirit of the
[Contributor Covenant](https://www.contributor-covenant.org/).
Disagreement on technical decisions is expected and good; dismissive
tone toward other contributors (human or agent) is not.

---

Thank you for contributing. See you in the mycelium.
