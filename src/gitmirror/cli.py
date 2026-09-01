"""Command line entry point."""

from __future__ import annotations

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .config import ConfigError, Repo, load_config
from .core import Result, check_one, sync_one
from .report import line, name_width, summary


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="gitmirror",
        description=(
            "Mirror the git repos listed in a YAML manifest into a local "
            "directory. The flow is one-way: local copies are overwritten to "
            "match their remote branch, discarding any local changes."
        ),
    )
    p.add_argument("config", help="path to the YAML manifest")
    p.add_argument(
        "--status",
        action="store_true",
        help="report which repos are behind, change nothing",
    )
    p.add_argument(
        "--purge",
        action="store_true",
        help="also delete gitignored files when syncing (git clean -fdx)",
    )
    p.add_argument(
        "-j", "--jobs", type=int, default=8, help="parallel workers (default: 8)"
    )
    p.add_argument(
        "--only",
        action="append",
        metavar="NAME",
        help="limit to this repo name (repeatable)",
    )
    return p


def _run(repos: list[Repo], args, console: Console) -> list[Result]:
    width = name_width([r.name for r in repos])
    branch_width = max(len(r.branch) for r in repos)
    verb = "checking" if args.status else "syncing"
    results: list[Result] = []

    def work(repo: Repo) -> Result:
        if args.status:
            return check_one(repo)
        return sync_one(repo, purge=args.purge)

    with Progress(
        SpinnerColumn(),
        TextColumn("[dim]{task.description}[/dim]"),
        console=console,
        transient=True,
        disable=not console.is_terminal,
    ) as progress:
        with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
            tasks = {}
            for repo in repos:
                future = pool.submit(work, repo)
                tasks[future] = progress.add_task(f"{verb} {repo.name}", total=None)
            for future in as_completed(tasks):
                progress.remove_task(tasks[future])
                result = future.result()
                results.append(result)
                progress.console.print(line(result, width, branch_width))

    return results


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    console = Console()
    errors = Console(stderr=True, soft_wrap=True, highlight=False)

    try:
        config = load_config(args.config)
    except ConfigError as exc:
        errors.print(f"[red]error:[/red] {exc}")
        return 2

    repos = config.repos
    if args.only:
        wanted = set(args.only)
        repos = [r for r in repos if r.name in wanted]
        missing = wanted - {r.name for r in config.repos}
        if missing:
            errors.print(
                f"[red]error:[/red] not in manifest: {', '.join(sorted(missing))}"
            )
            return 2

    results = _run(repos, args, console)
    console.print(summary(results, args.status))

    if any(r.state == "error" for r in results):
        return 1
    if args.status and any(r.state == "behind" for r in results):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
