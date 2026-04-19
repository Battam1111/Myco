"""``myco-install fresh`` — editable-default bootstrap.

v0.5.2 (MAJOR 11): the primary install path for anyone running
Myco as the L0 doctrine intends — as a substrate whose kernel the
agent can mutate, not as a frozen library imported from
``site-packages``.

End-to-end flow:

1. Check that ``git`` is on PATH. If not, fail with a clear
   "install git, then re-run" message.
2. Resolve the target directory. Refuse to touch a non-empty
   directory unless ``--force`` is passed.
3. ``git clone <repo> <target>`` (defaults:
   ``https://github.com/Battam1111/Myco.git``). ``--branch <REF>``
   and ``--depth <N>`` pass through.
4. ``<python> -m pip install -e <target>[mcp]`` using the same
   Python interpreter the ``myco-install`` CLI is running under.
   This ensures the editable install lands in the same environment
   the user's ``myco`` / ``mcp-server-myco`` console scripts
   resolve to after bootstrap.
5. Verify by invoking ``<python> -m myco --version``.
6. Optionally run one or more ``myco-install host <client>``
   steps in the same session (``--configure claude-code cursor
   windsurf …``) so the MCP hosts immediately point at the
   editable install.
7. Print a short "what just happened / what next" summary.

``--dry-run`` prints every step without executing anything.
``--yes`` skips any interactive confirmations (currently none, but
reserved for future prompts).

This is a side-effect-heavy command; every step validates before
moving on and aborts loud on any error. No half-states.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from collections.abc import Iterable, Sequence
from pathlib import Path

from .clients import CLIENTS, MycoInstallError, dispatch

__all__ = ["run_fresh", "DEFAULT_REPO"]


#: Default upstream source. Override with ``--repo``.
DEFAULT_REPO: str = "https://github.com/Battam1111/Myco.git"


#: Default target directory for ``fresh``. Picked to be out of
#: ``$HOME`` root (so ``ls ~`` doesn't get cluttered) but still a
#: conventional location for user-owned source clones.
def _default_target() -> Path:
    # ``~/myco`` is short, memorable, and consistent with how Rust
    # installs to ``~/.cargo`` and how many Python users already keep
    # top-level source clones in ``~/<proj>``. Users who want XDG
    # conformance can pass an explicit target.
    return Path.home() / "myco"


def _run(
    cmd: Sequence[str],
    *,
    cwd: Path | None = None,
    dry_run: bool,
    stream: bool = True,
) -> subprocess.CompletedProcess[str] | None:
    """Run ``cmd`` with clear logging. In ``dry_run`` mode, print
    the would-run command and return None."""
    rendered = " ".join(str(c) for c in cmd)
    if dry_run:
        prefix = "[dry-run] " + (f"(cd {cwd}) " if cwd else "")
        print(f"{prefix}{rendered}")
        return None
    print(f"$ {rendered}" + (f"  # in {cwd}" if cwd else ""))
    if stream:
        result = subprocess.run(cmd, cwd=cwd, check=False)
        if result.returncode != 0:
            raise MycoInstallError(f"command exited {result.returncode}: {rendered}")
        return result  # type: ignore[return-value]
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)


def _require_git(dry_run: bool) -> str:
    git = shutil.which("git")
    if git is None:
        raise MycoInstallError(
            "git is not on PATH. myco-install fresh needs git to "
            "clone the source; install it (https://git-scm.com) and "
            "re-run. Or skip editable install: see the 'Non-evolving "
            "install' section in README."
        )
    return git


def _assert_target_available(target: Path, force: bool, dry_run: bool) -> None:
    if not target.exists():
        return
    if not target.is_dir():
        raise MycoInstallError(
            f"target {target} exists but is not a directory; pick another --target path"
        )
    # Empty is fine (git clone handles that); non-empty requires --force.
    has_children = any(target.iterdir())
    if has_children and not force:
        raise MycoInstallError(
            f"target {target} is not empty. Pick a fresh path, or "
            f"pass --force to overwrite (destroys existing content)."
        )
    if has_children and force and not dry_run:
        # --force + real run: blow it away. --dry-run never touches
        # the filesystem.
        for child in target.iterdir():
            if child.is_dir() and not child.is_symlink():
                shutil.rmtree(child)
            else:
                child.unlink()


def _configure_hosts(
    target: Path,
    clients: Iterable[str],
    dry_run: bool,
    global_: bool,
) -> list[str]:
    """Run ``myco-install host <client>`` for each requested client
    inside the freshly cloned install. ``dispatch`` lives in the
    same process so no subprocess hop; the `home=Path.home()` +
    `cwd=target` context mirrors how the user will run it later.
    """
    results: list[str] = []
    unknown = [c for c in clients if c not in CLIENTS]
    if unknown:
        raise MycoInstallError(
            f"unknown --configure client(s): {unknown}. Known: {sorted(CLIENTS)}"
        )
    for client in clients:
        if dry_run:
            print(f"[dry-run] would configure host: {client}")
            continue
        # Anchor cwd to the editable clone so project-scoped writers
        # (Claude Code's .mcp.json, Cursor's .cursor/mcp.json, etc.)
        # land inside the clone, not the shell's original cwd.
        out = dispatch(
            client,
            dry_run=False,
            global_=global_,
            uninstall=False,
            home=Path.home(),
            cwd=target,
        )
        print(out)
        results.append(out)
    return results


def run_fresh(
    *,
    target: Path | None,
    repo: str,
    branch: str | None,
    depth: int | None,
    configure: Sequence[str],
    global_: bool,
    force: bool,
    dry_run: bool,
    yes: bool,
    extras: str,
    python: str | None = None,
    git: str | None = None,
) -> int:
    """Execute the editable-default bootstrap. Returns POSIX exit code."""
    del yes  # reserved for future prompts; no interactive paths yet

    # Pre-validate --configure BEFORE any side-effecting step so a
    # typo in a client name does not leave the user with a half-
    # cloned / half-installed state.
    if configure:
        unknown = [c for c in configure if c not in CLIENTS]
        if unknown:
            raise MycoInstallError(
                f"unknown --configure client(s): {unknown}. Known: {sorted(CLIENTS)}"
            )

    git = git or _require_git(dry_run)
    python_exe = python or sys.executable

    target = (target or _default_target()).resolve()
    _assert_target_available(target, force=force, dry_run=dry_run)

    # 1. clone
    clone_cmd: list[str] = [git, "clone"]
    if branch:
        clone_cmd += ["--branch", branch]
    if depth is not None:
        clone_cmd += ["--depth", str(int(depth))]
    clone_cmd += [repo, str(target)]
    _run(clone_cmd, dry_run=dry_run)

    # 2. editable pip install
    #    Use the same Python the CLI is running under so the editable
    #    install lands in this environment.
    pip_target = f"{target}[{extras}]" if extras else str(target)
    pip_cmd: list[str] = [
        python_exe,
        "-m",
        "pip",
        "install",
        "-e",
        pip_target,
    ]
    _run(pip_cmd, dry_run=dry_run)

    # 3. verify
    verify_cmd: list[str] = [python_exe, "-m", "myco", "--help"]
    if dry_run:
        print(f"[dry-run] would verify: {' '.join(verify_cmd)}")
    else:
        result = subprocess.run(
            verify_cmd,
            cwd=target,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise MycoInstallError(
                f"post-install verification failed "
                f"(exit {result.returncode}):\n{result.stderr.strip()}"
            )

    # 4. configure hosts (optional)
    if configure:
        _configure_hosts(target, configure, dry_run, global_)

    # 5. summary
    _print_summary(
        target=target,
        repo=repo,
        branch=branch,
        configured=list(configure),
        dry_run=dry_run,
        python_exe=python_exe,
    )
    return 0


def _print_summary(
    *,
    target: Path,
    repo: str,
    branch: str | None,
    configured: list[str],
    dry_run: bool,
    python_exe: str,
) -> None:
    lines: list[str] = []
    if dry_run:
        lines.append("")
        lines.append("[dry-run complete] no filesystem changes made.")
    else:
        lines.append("")
        lines.append(f"Myco installed editable at:  {target}")
        lines.append(
            f"Source (clone origin):       {repo}" + (f" @ {branch}" if branch else "")
        )
        lines.append(f"Python interpreter:          {python_exe}")
        if configured:
            lines.append(f"MCP hosts configured:        {', '.join(configured)}")
        lines.append("")
        lines.append("Next:")
        lines.append(f"  cd {target}")
        lines.append("  myco --help                    # sanity-check the CLI")
        lines.append("  myco genesis --project-dir <your-project> \\")
        lines.append(
            "               --substrate-id <slug>        # bootstrap a downstream substrate"
        )
        lines.append("")
        lines.append("Upgrade your kernel later with:")
        lines.append(f"  cd {target} && git pull")
        lines.append("  myco immune                    # verify no drift after upgrade")
    for line in lines:
        print(line)
