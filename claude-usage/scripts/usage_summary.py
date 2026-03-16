#!/usr/bin/env python3
"""
Claude Usage Summary Tool

Aggregates token usage and estimated API cost for a Claude Code session.

Usage:
    python scripts/usage_summary.py <session-id>
    python scripts/usage_summary.py                          # uses $AGENT_SESSION_ID
    python scripts/usage_summary.py <id> --start 2026-03-01
    python scripts/usage_summary.py <id> --start 2026-03-01T00:00:00 --end 2026-03-16T23:59:59
"""

import json
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field


# ── Pricing (USD per million tokens) ────────────────────────────────────────
# (input, cache_write, cache_read, output)

MODEL_PRICING: dict[str, tuple[float, float, float, float]] = {
    "claude-opus-4":     (15.00, 18.75,  1.50, 75.00),
    "claude-sonnet-4":   ( 3.00,  3.75,  0.30, 15.00),
    "claude-haiku-4":    ( 0.80,  1.00,  0.08,  4.00),
    "claude-3-5-sonnet": ( 3.00,  3.75,  0.30, 15.00),
    "claude-3-5-haiku":  ( 0.80,  1.00,  0.08,  4.00),
    "claude-3-opus":     (15.00, 18.75,  1.50, 75.00),
    "claude-3-sonnet":   ( 3.00,  3.75,  0.30, 15.00),
    "claude-3-haiku":    ( 0.25,  0.30,  0.03,  1.25),
    "claude-2.1":        ( 8.00,  8.00,  8.00, 24.00),
    "claude-2.0":        ( 8.00,  8.00,  8.00, 24.00),
}
DEFAULT_PRICING = (3.00, 3.75, 0.30, 15.00)


def get_pricing(model_id: str) -> tuple[float, float, float, float]:
    lower = model_id.lower()
    for prefix, pricing in MODEL_PRICING.items():
        if lower.startswith(prefix):
            return pricing
    return DEFAULT_PRICING


def calc_cost(input_t: int, cache_write: int, cache_read: int, output_t: int,
              pricing: tuple[float, float, float, float]) -> float:
    p_in, p_cw, p_cr, p_out = pricing
    return (
        input_t   * p_in  / 1_000_000 +
        cache_write * p_cw / 1_000_000 +
        cache_read  * p_cr / 1_000_000 +
        output_t  * p_out / 1_000_000
    )


# ── Helpers ──────────────────────────────────────────────────────────────────

def get_claude_projects_dir() -> Path:
    env = os.environ.get("CLAUDE_PROJECTS_DIR")
    if env:
        return Path(env)
    return Path.home() / ".claude" / "projects"


def find_all_sessions(projects_dir: Path) -> list[Path]:
    if not projects_dir.exists():
        return []
    return list(projects_dir.rglob("*.jsonl"))


def find_session(sessions: list[Path], session_id: str) -> Path | None:
    for s in sessions:
        if s.stem == session_id:
            return s
    return None


def parse_iso(s: str) -> datetime:
    """Parse ISO datetime string, assume UTC if no timezone given."""
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        # Try date-only
        dt = datetime.fromisoformat(s + "T00:00:00")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def format_tokens(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.2f}m"
    if n >= 1_000:
        return f"{n / 1_000:.1f}k"
    return str(n)


# ── Data ─────────────────────────────────────────────────────────────────────

@dataclass
class ModelUsage:
    model: str
    turns: int = 0
    input_tokens: int = 0
    cache_write_tokens: int = 0
    cache_read_tokens: int = 0
    output_tokens: int = 0

    @property
    def cost(self) -> float:
        return calc_cost(
            self.input_tokens, self.cache_write_tokens,
            self.cache_read_tokens, self.output_tokens,
            get_pricing(self.model),
        )

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.cache_write_tokens + self.cache_read_tokens + self.output_tokens


# ── Parsing ───────────────────────────────────────────────────────────────────

def parse_session(file_path: Path,
                  start: datetime | None = None,
                  end: datetime | None = None) -> tuple[dict[str, ModelUsage], str, str]:
    """
    Returns (usage_by_model, first_ts, last_ts).
    Aggregates one ModelUsage entry per model seen.
    """
    usage_by_model: dict[str, ModelUsage] = {}
    first_ts = ""
    last_ts = ""
    current_model = "unknown"

    lines = file_path.read_text(encoding="utf-8").strip().split("\n")

    for line in lines:
        if not line.strip():
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue

        ts_raw = data.get("timestamp", "")
        if ts_raw:
            try:
                ts_dt = parse_iso(ts_raw)
                if start and ts_dt < start:
                    continue
                if end and ts_dt > end:
                    continue
                if not first_ts or ts_raw < first_ts:
                    first_ts = ts_raw
                if not last_ts or ts_raw > last_ts:
                    last_ts = ts_raw
            except ValueError:
                pass

        msg = data.get("message")
        if not isinstance(msg, dict):
            continue

        role = msg.get("role", "")
        model = msg.get("model", "")
        usage = msg.get("usage", {})

        if model and model != "<synthetic>" and not model.startswith("<"):
            current_model = model

        if role == "assistant" and usage:
            m = current_model
            if m not in usage_by_model:
                usage_by_model[m] = ModelUsage(model=m)
            u = usage_by_model[m]
            u.turns += 1
            u.input_tokens       += usage.get("input_tokens", 0)
            u.cache_write_tokens += usage.get("cache_creation_input_tokens", 0)
            u.cache_read_tokens  += usage.get("cache_read_input_tokens", 0)
            u.output_tokens      += usage.get("output_tokens", 0)

    return usage_by_model, first_ts, last_ts


# ── Output ────────────────────────────────────────────────────────────────────

def fmt_ts(ts: str) -> str:
    if not ts:
        return "—"
    try:
        dt = parse_iso(ts)
        return dt.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return ts


def print_usage(session_id: str, usage_by_model: dict[str, ModelUsage],
                first_ts: str, last_ts: str):
    if not usage_by_model:
        print("  No usage data found for the given filters.")
        return

    total_turns = sum(u.turns for u in usage_by_model.values())
    total_input = sum(u.input_tokens for u in usage_by_model.values())
    total_cw    = sum(u.cache_write_tokens for u in usage_by_model.values())
    total_cr    = sum(u.cache_read_tokens for u in usage_by_model.values())
    total_out   = sum(u.output_tokens for u in usage_by_model.values())
    total_cost  = sum(u.cost for u in usage_by_model.values())

    print()
    print(f"  Session: {session_id}")
    print(f"  Period:  {fmt_ts(first_ts)}  →  {fmt_ts(last_ts)}")
    print(f"  Turns:   {total_turns}")
    print()
    print(f"  Tokens")
    print(f"    Input:        {format_tokens(total_input)}")
    print(f"    Cache write:  {format_tokens(total_cw)}")
    print(f"    Cache read:   {format_tokens(total_cr)}")
    print(f"    Output:       {format_tokens(total_out)}")
    print()
    print(f"  Estimated cost: ${total_cost:.4f}")

    if len(usage_by_model) > 1:
        print()
        print(f"  By model:")
        for model, u in sorted(usage_by_model.items(), key=lambda x: -x[1].cost):
            print(f"    {model:<30}  {u.turns:>3} turns  ${u.cost:.4f}")

    print()


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Claude Session Usage & Cost Tool")
    parser.add_argument("session_id", nargs="?", help="Session ID")
    parser.add_argument("--start", help="Filter turns from this ISO datetime (inclusive)")
    parser.add_argument("--end",   help="Filter turns until this ISO datetime (inclusive)")
    parser.add_argument("--dir", "-d", help="Claude projects directory (default: ~/.claude/projects)")
    args = parser.parse_args()

    projects_dir = Path(args.dir) if args.dir else get_claude_projects_dir()
    if not projects_dir.exists():
        print(f"Error: Projects directory not found: {projects_dir}", file=sys.stderr)
        sys.exit(1)

    session_id = args.session_id or os.environ.get("AGENT_SESSION_ID")
    if not session_id:
        print("Error: No session ID provided. Pass as argument or set AGENT_SESSION_ID.", file=sys.stderr)
        sys.exit(1)

    sessions = find_all_sessions(projects_dir)
    match = find_session(sessions, session_id)
    if not match:
        print(f"Error: No session found with ID '{session_id}'", file=sys.stderr)
        sys.exit(1)

    start = parse_iso(args.start) if args.start else None
    end   = parse_iso(args.end)   if args.end   else None

    usage_by_model, first_ts, last_ts = parse_session(match, start, end)
    print_usage(session_id, usage_by_model, first_ts, last_ts)


if __name__ == "__main__":
    main()
