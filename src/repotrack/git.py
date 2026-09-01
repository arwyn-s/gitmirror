"""Thin wrappers over the system git binary."""

from __future__ import annotations

import subprocess
from pathlib import Path


class GitError(Exception):
    """A git command failed, or the remote does not have what we asked for."""


def run_git(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        check=False,
    )


def _checked(args: list[str], cwd: Path | None = None) -> str:
    proc = run_git(args, cwd)
    if proc.returncode != 0:
        lines = (proc.stderr or proc.stdout).strip().splitlines()
        detail = lines[-1].strip() if lines else f"git {args[0]} failed"
        raise GitError(detail.removeprefix("fatal: ").removeprefix("error: "))
    return proc.stdout.strip()


def is_repo(path: Path) -> bool:
    return run_git(["-C", str(path), "rev-parse", "--git-dir"]).returncode == 0


def head_sha(path: Path) -> str:
    return _checked(["-C", str(path), "rev-parse", "HEAD"])


def remote_sha(url: str, branch: str) -> str:
    out = _checked(["ls-remote", url, f"refs/heads/{branch}"])
    if not out:
        raise GitError(f"no branch '{branch}' on remote")
    return out.split()[0]


def clone(url: str, path: Path, branch: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _checked(["clone", "--branch", branch, url, str(path)])


def fetch(path: Path, branch: str) -> None:
    _checked(["-C", str(path), "fetch", "--prune", "origin", branch])


def hard_reset(path: Path, branch: str, purge: bool = False) -> None:
    """Force the worktree to exactly match origin/<branch>."""
    _checked(["-C", str(path), "checkout", "-B", branch, "FETCH_HEAD"])
    _checked(["-C", str(path), "reset", "--hard", "FETCH_HEAD"])
    _checked(["-C", str(path), "clean", "-fdx" if purge else "-fd"])
