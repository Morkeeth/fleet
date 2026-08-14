"""Vendor-agnostic token/runtime collector.

NOT self-report. An agent cannot measure its own token spend from inside its own
run — it can only estimate, and an estimate presented as a measurement is the
failure this repo is named after. This reads the harness's own per-turn usage
records off disk and sums them.

Each provider is an adapter over the same shape, and the shapes are not alike:
Claude Code emits a per-turn `usage` object that is summed, Codex emits a
cumulative running total that is taken at its maximum. Getting that distinction
wrong multiplies the answer by the turn count, which is why each adapter states
which kind it is reading. Cursor is declared and unimplemented, and says so out
loud rather than silently reporting zero — a collector that returns 0 for an
unsupported provider is a metric that lies about its own scope.
"""
from __future__ import annotations

import datetime as dt
import glob
import json
import os

SUPPORTED = {"claude-code", "codex"}
DECLARED_UNSUPPORTED = {"cursor"}


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
    for path in glob.glob(os.path.expanduser(pattern), recursive=True):
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


def _codex(pattern: str, since: dt.datetime | None) -> list[Row]:
    """Codex rollout logs: `event_msg` records whose payload.type is `token_count`.

    The counter is CUMULATIVE, not per-turn. `payload.info.total_token_usage` is a
    running total for the session and `last_token_usage` is the delta. Summing the
    totals would multiply the answer by the number of turns; summing the deltas
    double-counts, because a token_count event can repeat without the total moving.
    Measured over 43 real sessions: the totals were monotonic in 42, and where the
    two methods disagreed the delta-sum was higher every single time, by 0.86%
    overall. So we take the maximum running total and treat it as a floor.

    The floor leaks on a resumed session whose counter restarts — max() then sees
    the larger leg rather than the sum. That is under-reporting, which is the
    direction this repo is willing to be wrong in.
    """
    rows = []
    for path in glob.glob(os.path.expanduser(pattern), recursive=True):
        row = Row(os.path.basename(path)[:8])
        peak = {}
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
                    payload = ev.get("payload") or {}
                    if payload.get("type") != "token_count":
                        continue
                    total = (payload.get("info") or {}).get("total_token_usage") or {}
                    for k in ("output_tokens", "input_tokens", "cached_input_tokens"):
                        peak[k] = max(peak.get(k, 0), total.get(k) or 0)
                    row.turns += 1
        except OSError:
            continue
        if row.turns == 0:
            continue
        row.output = peak.get("output_tokens", 0)
        row.input = peak.get("input_tokens", 0)
        row.cache_read = peak.get("cached_input_tokens", 0)
        if since and row.last:
            try:
                if dt.datetime.fromisoformat(row.last) < since:
                    continue
            except ValueError:
                pass
        rows.append(row)
    return rows


ADAPTERS = {"claude-code": _claude_code, "codex": _codex}


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
        found = ADAPTERS[provider](pattern, since)
        if not found:
            skipped.append(f"{provider} (no transcripts matched {pattern})")
        rows.extend(found)
    rows.sort(key=lambda r: r.output, reverse=True)
    return rows, skipped
