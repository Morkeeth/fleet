"""Load and validate a fleet config.

The config is the whole point of this repo. Without it, the rules in RULES.md are
prose a reader has to hand-translate into their own stack; with it, they are
behaviour a program can act on.

Two formats, because a hard dependency is a cold-start failure: `fleet.yaml` when
PyYAML is installed, `fleet.json` always. The JSON path is what makes `fleet open`
runnable by someone who has just cloned this and installed nothing.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

VERSION = 1

# Anything not in here is a typo, and a typo that silently does nothing is worse
# than an error — that is the whole failure class this repo exists to fight.
TOP_LEVEL = {"version", "fleet", "projects", "agents", "approval", "outcomes", "transcripts"}
APPROVAL_VALUES = {"ask", "auto", "never"}


class ConfigError(Exception):
    """Raised with a sentence a human can act on, never a stack trace."""


def find_config(start: Path | None = None) -> Path:
    """Nearest fleet.yaml / fleet.json, walking up from `start`."""
    here = (start or Path.cwd()).resolve()
    for d in [here, *here.parents]:
        for name in ("fleet.yaml", "fleet.yml", "fleet.json"):
            p = d / name
            if p.is_file():
                return p
    raise ConfigError(
        "no fleet.yaml or fleet.json found here or in any parent directory.\n"
        "       Copy examples/fake-fleet.json to ./fleet.json and edit it, or pass --config PATH."
    )


def _parse(path: Path) -> dict:
    text = path.read_text()
    if path.suffix in (".yaml", ".yml"):
        try:
            import yaml  # optional
        except ImportError:
            raise ConfigError(
                f"{path.name} is YAML but PyYAML is not installed.\n"
                "       Either `pip install pyyaml`, or use fleet.json instead — the schema is identical."
            )
        try:
            data = yaml.safe_load(text)
        except Exception as e:  # yaml raises several types
            raise ConfigError(f"{path.name} is not valid YAML: {e}")
    else:
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise ConfigError(f"{path.name} is not valid JSON (line {e.lineno}, column {e.colno}): {e.msg}")
    if not isinstance(data, dict):
        raise ConfigError(f"{path.name}: top level must be a mapping, found {type(data).__name__}.")
    return data


def load(path: Path | None = None) -> "Config":
    path = Path(path).expanduser() if path else find_config()
    if not path.is_file():
        raise ConfigError(f"no config at {path}")
    return Config(_parse(path), path)


class Config:
    def __init__(self, data: dict, path: Path):
        self.path = path
        self.raw = data
        self._validate()

    # -- validation ---------------------------------------------------------
    def _validate(self) -> None:
        d = self.raw
        unknown = set(d) - TOP_LEVEL
        if unknown:
            raise ConfigError(
                f"{self.path.name}: unknown top-level key(s): {', '.join(sorted(unknown))}.\n"
                f"       Known keys: {', '.join(sorted(TOP_LEVEL))}."
            )
        v = d.get("version")
        if v != VERSION:
            raise ConfigError(
                f"{self.path.name}: version is {v!r}, this tool speaks version {VERSION}."
            )
        projects = d.get("projects")
        if not isinstance(projects, list) or not projects:
            raise ConfigError(f"{self.path.name}: 'projects' must be a non-empty list.")
        for i, p in enumerate(projects):
            if not isinstance(p, dict) or "name" not in p or "root" not in p:
                raise ConfigError(
                    f"{self.path.name}: projects[{i}] needs at least 'name' and 'root'."
                )
        for key in ("irreversible", "outward_facing"):
            val = (d.get("approval") or {}).get(key, "ask")
            if val not in APPROVAL_VALUES:
                raise ConfigError(
                    f"{self.path.name}: approval.{key} is {val!r}; expected one of "
                    f"{', '.join(sorted(APPROVAL_VALUES))}."
                )

    # -- accessors ----------------------------------------------------------
    @property
    def name(self) -> str:
        return (self.raw.get("fleet") or {}).get("name", "fleet")

    @property
    def state_file(self) -> Path:
        raw = (self.raw.get("fleet") or {}).get("state_file", ".fleet-state.json")
        return self._resolve(raw)

    @property
    def projects(self) -> list[dict]:
        return list(self.raw["projects"])

    @property
    def approval(self) -> dict:
        a = dict(self.raw.get("approval") or {})
        a.setdefault("irreversible", "ask")
        a.setdefault("outward_facing", "ask")
        return a

    @property
    def agents(self) -> dict:
        a = dict(self.raw.get("agents") or {})
        a.setdefault("provider", "unset")
        a.setdefault("transport", "local")
        return a

    @property
    def outcomes(self) -> list[dict]:
        return list(self.raw.get("outcomes") or [])

    @property
    def transcripts(self) -> list[dict]:
        return list(self.raw.get("transcripts") or [])

    def project_root(self, project: dict) -> Path:
        return self._resolve(project["root"])

    def _resolve(self, raw: str) -> Path:
        p = Path(os.path.expanduser(str(raw)))
        return p if p.is_absolute() else (self.path.parent / p)
