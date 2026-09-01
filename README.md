# repotrack

Keep a set of git repositories mirrored locally from a YAML manifest.

The flow is **one-way: remote → local**. Each directory under `base_dir` is a
disposable copy of a remote branch, not a place to work. Syncing overwrites it
— local commits, uncommitted edits, a checked-out different branch, and
untracked files are all discarded without prompting.

So there are only two states:

- **in sync** — local `HEAD` matches the remote branch tip
- **behind** — anything else (different commit, not cloned yet, wrong branch)

## Install

```sh
uv sync
uv run repotrack --help
```

## Usage

```sh
repotrack repos.yml              # mirror every repo in the manifest
repotrack repos.yml --status     # report only, change nothing
```

Options:

| Flag | Meaning |
| --- | --- |
| `--status` | Read-only check. Compares local `HEAD` to `git ls-remote`; touches nothing on disk. |
| `--purge` | Sync with `git clean -fdx`, so gitignored files (venvs, build output) are deleted too. Default keeps them. |
| `-j`, `--jobs` | Parallel workers (default 8). |
| `--only NAME` | Limit to one repo by name; repeatable. |

## Manifest

```yaml
base_dir: ~/src/mirrors    # required; ~ and $VARS expanded
default_branch: main       # optional, used when a repo omits `branch`

repos:
  - url: https://github.com/astral-sh/uv.git
  - url: https://github.com/python/cpython.git
    branch: "3.13"
  - url: git@github.com:you/notes.git
    name: my-notes         # optional; defaults to the repo name in the URL
```

See `repotrack.example.yml`.

## Exit codes

| Code | Meaning |
| --- | --- |
| 0 | Everything in sync |
| 1 | A repo is behind (`--status`), or a repo errored |
| 2 | Bad manifest or bad usage |

Git itself is used for all remote access, so SSH keys, credential helpers, and
`~/.gitconfig` work exactly as they do on the command line.
