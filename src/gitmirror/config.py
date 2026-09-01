"""Manifest loading and validation."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml


class ConfigError(Exception):
    """The manifest is missing, malformed, or self-contradictory."""


@dataclass(frozen=True)
class Repo:
    name: str
    url: str
    branch: str
    path: Path


@dataclass(frozen=True)
class Config:
    base_dir: Path
    repos: list[Repo]


def _expand(value: str) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(value)))


def _name_from_url(url: str) -> str:
    name = url.rstrip("/").rsplit("/", 1)[-1]
    name = name.rsplit(":", 1)[-1]  # git@host:owner/repo with no slash
    return name[:-4] if name.endswith(".git") else name


def load_config(path: str | Path) -> Config:
    path = Path(path)
    try:
        raw = yaml.safe_load(path.read_text())
    except FileNotFoundError:
        raise ConfigError(f"no such config file: {path}") from None
    except yaml.YAMLError as exc:
        raise ConfigError(f"{path}: invalid YAML: {exc}") from None

    if not isinstance(raw, dict):
        raise ConfigError(f"{path}: top level must be a mapping")

    base_dir_raw = raw.get("base_dir")
    if not base_dir_raw:
        raise ConfigError(f"{path}: 'base_dir' is required")
    base_dir = _expand(str(base_dir_raw))

    default_branch = raw.get("default_branch")
    entries = raw.get("repos")
    if not entries:
        raise ConfigError(f"{path}: 'repos' is required and must not be empty")
    if not isinstance(entries, list):
        raise ConfigError(f"{path}: 'repos' must be a list")

    repos: list[Repo] = []
    seen: dict[str, str] = {}
    for i, entry in enumerate(entries):
        where = f"{path}: repos[{i}]"
        if not isinstance(entry, dict):
            raise ConfigError(f"{where}: must be a mapping")
        url = entry.get("url")
        if not url:
            raise ConfigError(f"{where}: 'url' is required")
        branch = entry.get("branch") or default_branch
        if not branch:
            raise ConfigError(
                f"{where}: no 'branch' and no top-level 'default_branch'"
            )
        name = entry.get("name") or _name_from_url(str(url))
        if name in seen:
            raise ConfigError(
                f"{where}: name '{name}' already used by {seen[name]}"
            )
        seen[name] = str(url)
        repos.append(
            Repo(
                name=str(name),
                url=str(url),
                branch=str(branch),
                path=base_dir / str(name),
            )
        )

    return Config(base_dir=base_dir, repos=repos)
