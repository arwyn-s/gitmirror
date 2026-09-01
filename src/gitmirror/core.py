"""Per-repo state checks and mirroring."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from . import git
from .config import Repo

State = Literal["in-sync", "behind", "error"]


@dataclass(frozen=True)
class Result:
    repo: Repo
    state: State
    detail: str


def _short(sha: str) -> str:
    return sha[:7]


def check_one(repo: Repo) -> Result:
    """Read-only: compare local HEAD against the remote branch tip."""
    try:
        remote = git.remote_sha(repo.url, repo.branch)
        if not repo.path.exists() or not git.is_repo(repo.path):
            return Result(repo, "behind", "not cloned")
        local = git.head_sha(repo.path)
    except git.GitError as exc:
        return Result(repo, "error", str(exc))

    if local == remote:
        return Result(repo, "in-sync", "in sync")
    return Result(repo, "behind", f"local {_short(local)} → remote {_short(remote)}")


def sync_one(repo: Repo, purge: bool = False) -> Result:
    """Overwrite the local copy so it matches the remote branch exactly."""
    try:
        if not repo.path.exists() or not git.is_repo(repo.path):
            git.clone(repo.url, repo.path, repo.branch)
            return Result(repo, "in-sync", f"cloned {_short(git.head_sha(repo.path))}")

        before = git.head_sha(repo.path)
        git.fetch(repo.path, repo.branch)
        git.hard_reset(repo.path, repo.branch, purge)
        after = git.head_sha(repo.path)
    except git.GitError as exc:
        return Result(repo, "error", str(exc))

    if before == after:
        return Result(repo, "in-sync", "already in sync")
    return Result(repo, "in-sync", f"updated {_short(before)} → {_short(after)}")
