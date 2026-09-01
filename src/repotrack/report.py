"""Console line rendering."""

from __future__ import annotations

from .core import Result

GLYPH = {"in-sync": ("[green]✓[/green]", "green"),
         "behind": ("[yellow]↓[/yellow]", "yellow"),
         "error": ("[red]✗[/red]", "red")}


def name_width(names: list[str]) -> int:
    return max((len(n) for n in names), default=0)


def line(result: Result, width: int, branch_width: int) -> str:
    glyph, color = GLYPH[result.state]
    name = result.repo.name.ljust(width)
    branch = result.repo.branch.ljust(branch_width)
    return (
        f"{glyph} [bold]{name}[/bold]  [dim]{branch}[/dim]  "
        f"[{color}]{result.detail}[/{color}]"
    )


def summary(results: list[Result], status_only: bool) -> str:
    in_sync = sum(1 for r in results if r.state == "in-sync")
    behind = sum(1 for r in results if r.state == "behind")
    errors = sum(1 for r in results if r.state == "error")

    if status_only:
        parts = [f"[green]{in_sync} in sync[/green]"]
        if behind:
            parts.append(f"[yellow]{behind} behind[/yellow]")
    else:
        changed = sum(
            1 for r in results
            if r.state == "in-sync" and r.detail != "already in sync"
        )
        suffix = f" [yellow]({changed} updated)[/yellow]" if changed else ""
        parts = [f"[green]{in_sync} in sync[/green]{suffix}"]
    if errors:
        parts.append(f"[red]{errors} error{'s' if errors > 1 else ''}[/red]")
    return "[dim] · [/dim]".join(parts)
