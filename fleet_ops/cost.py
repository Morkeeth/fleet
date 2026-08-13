"""Vendor-agnostic token/runtime collector.

NOT self-report. An agent cannot measure its own token spend from inside its own
run — it can only estimate, and an estimate presented as a measurement is the
failure this repo is named after. This reads the harness's own per-turn usage
records off disk and sums them.

Each provider is an adapter over the same shape. Claude Code is implemented
because its transcripts are newline-delimited JSON with a `usage` object per
turn. Codex and Cursor are declared and unimplemented, and say so out loud rather
than silently reporting zero — a collector that returns 0 for an unsupported
provider is a metric that lies about its own scope.
"""
from __future__ import annotations

import datetime as dt
import glob
import json
import os

SUPPORTED = {"claude-code"}
DECLARED_UNSUPPORTED = {"codex", "cursor"}


class Row:
    __slots__ = ("session", "output", "input", "cache_read", "cache_create", "turns", "first", "last")

    def __init__(self, session):
        self.session = session
        self.output = self.input = self.cache_read = self.cache_create = self.turns = 0
        self.first = self.last = None

    @property
    def wall_minutes(self):
        if not (self.first and self.last):
            return None
        try:
            delta = dt.datetime.fromisoformat(self.last) - dt.datetime.fromisoformat(self.first)
            return delta.total_seconds() / 60
        except ValueError:
            return None


def _claude_code(pattern: str, since: dt.datetime | None) -> list[Row]:
    rows = []
    for path in glob.glob(os.path.expanduser(pattern)):
        row = Row(os.path.basename(path)[:8])
        try:
            with open(path) as f:
                for line in f:
                    try:
                        ev = json.loads(line)
                    except ValueError:
                        continue
                    ts = ev.get("timestamp")
                    if ts:
                        row.first = row.first or ts[:19]
                        row.last = ts[:19]
                    usage = (ev.get("message") or {}).get("usage") or ev.get("usage")
                    if usage:
                        row.output += usage.get("output_tokens", 0)
                        row.input += usage.get("input_tokens", 0)
                        row.cache_read += usage.get("cache_read_input_tokens", 0)
                        row.cache_create += usage.get("cache_creation_input_tokens", 0)
                        row.turns += 1
        except OSError:
            continue
        if row.turns == 0:
            continue
        if since and row.last:
            try:
                if dt.datetime.fromisoformat(row.last) < since:
                    continue
            except ValueError:
                pass
        rows.append(row)
    return rows


def collect(transcripts: list[dict], since: dt.datetime | None = None):
    """Returns (rows, skipped) — `skipped` names every source NOT counted.

    The skipped list is the honest half. Without it, a fleet running three
    providers reports one provider's spend as if it were the total.
    """
    rows: list[Row] = []
    skipped: list[str] = []
    for src in transcripts:
        provider = src.get("provider", "unset")
        pattern = src.get("glob")
        if provider not in SUPPORTED:
            why = "declared but not implemented" if provider in DECLARED_UNSUPPORTED else "unknown provider"
            skipped.append(f"{provider} ({why})")
            continue
        if not pattern:
            skipped.append(f"{provider} (no 'glob' in config)")
            continue
        found = _claude_code(pattern, since)
        if not found:
            skipped.append(f"{provider} (no transcripts matched {pattern})")
        rows.extend(found)
    rows.sort(key=lambda r: r.output, reverse=True)
    return rows, skipped
