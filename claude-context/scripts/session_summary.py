#!/usr/bin/env python3
"""
Claude Session Summary Tool

Finds a Claude session by ID and prints a summary matching the official /context report format.

Usage:
    python scripts/session_summary.py <session-id>             # summarize by full ID
    python scripts/session_summary.py                          # uses $AGENT_SESSION_ID
"""

import json
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field


# ── Config ──────────────────────────────────────────────────────────────────

MODEL_CONTEXT_WINDOWS = {
    "claude-opus-4": 1_000_000,
    "claude-sonnet-4": 1_000_000,
    "claude-haiku-4": 1_000_000,
    "claude-3-5-sonnet": 1_000_000,
    "claude-3-5-haiku": 1_000_000,
    "claude-3-opus": 1_000_000,
    "claude-2.1": 200_000,
    "claude-2.0": 100_000,
}

DEFAULT_CONTEXT_WINDOW = 1_000_000

# Auto-compact: buffer is 3.3% of context window (matches official /context)
AUTO_COMPACT_BUFFER_PCT = 0.033


# ── Helpers ─────────────────────────────────────────────────────────────────

def get_claude_projects_dir() -> Path:
    env = os.environ.get("CLAUDE_PROJECTS_DIR")
    if env:
        return Path(env)
    return Path.home() / ".claude" / "projects"


def find_all_sessions(projects_dir: Path) -> list[Path]:
    sessions = []
    if not projects_dir.exists():
        return sessions
    for jsonl in projects_dir.rglob("*.jsonl"):
        sessions.append(jsonl)
    return sessions


def find_session(sessions: list[Path], session_id: str) -> Path | None:
    for s in sessions:
        if s.stem == session_id:
            return s
    return None


def get_model_display(model_id: str) -> str:
    """e.g. 'claude-opus-4-6' -> 'claude-opus-4-6[1m]'"""
    if not model_id or model_id == "Unknown":
        return "Unknown"
    window = get_context_window(model_id)
    suffix = f"[{window // 1_000_000}m]" if window >= 1_000_000 else f"[{window // 1_000}k]"
    return f"{model_id}{suffix}"


def get_context_window(model_id: str) -> int:
    lower = model_id.lower()
    for prefix, window in MODEL_CONTEXT_WINDOWS.items():
        if lower.startswith(prefix):
            return window
    return DEFAULT_CONTEXT_WINDOW


def format_tokens(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.0f}m"
    if n >= 1_000:
        return f"{n / 1_000:.0f}k"
    return str(n)


def format_tokens_k(n: int) -> str:
    """Format as Xk like the official report."""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.0f}m"
    if n >= 1_000:
        return f"{n / 1_000:.1f}k" if n < 10_000 else f"{n / 1_000:.0f}k"
    return str(n)


def truncate(text: str, max_len: int = 120) -> str:
    text = text.replace("\n", " ").strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def _extract_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return "\n".join(parts)
    return ""


# ── Session parsing ─────────────────────────────────────────────────────────

@dataclass
class SessionSummary:
    session_id: str
    project: str
    model: str = "Unknown"
    # Context used = latest message's (input + cache_read + cache_create)
    context_used: int = 0
    context_window: int = DEFAULT_CONTEXT_WINDOW
    turns: int = 0
    message_count: int = 0
    latest_cache_read: int = 0
    last_message_role: str = ""
    last_message_text: str = ""
    last_message_ts: str | None = None
    project_path: str = ""
    is_compacted: bool = False

    @property
    def usage_pct(self) -> float:
        return (self.context_used / self.context_window * 100) if self.context_window else 0

    @property
    def free_tokens(self) -> int:
        return max(0, self.context_window - self.context_used)

    @property
    def free_pct(self) -> float:
        return (self.free_tokens / self.context_window * 100) if self.context_window else 0


# Approximate tokens per character (rough estimate for post-compact sizing)
CHARS_PER_TOKEN = 4

# Baseline system overhead: system prompt + tools + memory + skills (~18k typical)
SYSTEM_OVERHEAD_TOKENS = 18_000


def _estimate_tokens(text: str) -> int:
    """Rough token estimate from text length."""
    return len(text) // CHARS_PER_TOKEN


def parse_session(file_path: Path) -> SessionSummary:
    session_id = file_path.stem
    project = file_path.parent.name

    summary = SessionSummary(session_id=session_id, project=project)

    lines = file_path.read_text(encoding="utf-8").strip().split("\n")

    # Track post-compact message tokens for estimation
    post_compact_tokens = 0
    compacted = False

    for line in lines:
        if not line.strip():
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue

        # Get project path from cwd field
        cwd = data.get("cwd", "")
        if cwd and not summary.project_path:
            summary.project_path = cwd

        msg = data.get("message")
        if not isinstance(msg, dict):
            continue

        role = msg.get("role", "")
        model = msg.get("model", "")
        content = msg.get("content", "")
        usage = msg.get("usage", {})
        ts = data.get("timestamp")

        # Use latest real model (skip <synthetic>)
        if model and model != "<synthetic>" and not model.startswith("<"):
            summary.model = model
            summary.context_window = get_context_window(model)

        if role in ("user", "assistant"):
            summary.message_count += 1

        # Detect compaction: the summary message injected after /compact
        text = _extract_text(content)
        if role == "user" and text.startswith(
            "This session is being continued from a previous conversation"
        ):
            compacted = True
            summary.is_compacted = True
            # Reset context — old usage is stale
            summary.context_used = 0
            post_compact_tokens = SYSTEM_OVERHEAD_TOKENS + _estimate_tokens(text)

        if usage and role == "assistant":
            summary.turns += 1
            # Context used = total input tokens for this API call
            input_t = usage.get("input_tokens", 0)
            cache_read = usage.get("cache_read_input_tokens", 0)
            cache_create = usage.get("cache_creation_input_tokens", 0)
            call_context = input_t + cache_read + cache_create
            if call_context > 0:
                summary.context_used = call_context
            if cache_read > 0:
                summary.latest_cache_read = cache_read

        # After compaction, accumulate message sizes for estimation
        if compacted and role in ("user", "assistant") and text:
            post_compact_tokens += _estimate_tokens(text)

        # Track last user/assistant message with text
        if role in ("user", "assistant") and text:
            summary.last_message_role = role
            summary.last_message_text = text
            summary.last_message_ts = ts

    # If compacted and no new API call gave us updated usage, use estimate
    if compacted and summary.context_used == 0:
        summary.context_used = post_compact_tokens

    return summary


def calculate_auto_compact(context_used: int, context_window: int) -> dict:
    buffer_tokens = int(context_window * AUTO_COMPACT_BUFFER_PCT)
    buffer_pct = AUTO_COMPACT_BUFFER_PCT * 100
    free_tokens = max(0, context_window - context_used)
    free_pct = (free_tokens / context_window * 100) if context_window else 0

    return {
        "buffer_tokens": buffer_tokens,
        "buffer_pct": buffer_pct,
        "free_tokens": free_tokens,
        "free_pct": free_pct,
    }


# ── Output ──────────────────────────────────────────────────────────────────


def print_session_summary(summary: SessionSummary):
    ac = calculate_auto_compact(summary.context_used, summary.context_window)

    model_display = get_model_display(summary.model)
    used_str = format_tokens(summary.context_used)
    window_str = format_tokens(summary.context_window)
    free_str = format_tokens_k(ac['free_tokens'])
    buf_str = format_tokens_k(ac['buffer_tokens'])

    print()
    print(f"  Context: {used_str}/{window_str} tokens ({summary.usage_pct:.1f}%) - {model_display}")
    print(f"  Free: {free_str} ({ac['free_pct']:.1f}%)")
    print(f"  Autocompact buffer: {buf_str} ({ac['buffer_pct']:.1f}%)")

    if summary.is_compacted:
        print(f"  ** Session has been compacted **")

    print()
    print(f"  Session: {summary.session_id}")
    print(f"  Project: {summary.project_path}")
    print(f"  Resume:  claude --resume {summary.session_id}")
    print(f"  Turns:   {summary.turns} | Messages: {summary.message_count}")

    # Last message
    if summary.last_message_text:
        time_str = ""
        if summary.last_message_ts:
            try:
                t = datetime.fromisoformat(summary.last_message_ts.replace("Z", "+00:00"))
                time_str = t.strftime("%H:%M")
            except ValueError:
                pass
        prefix = "user" if summary.last_message_role == "user" else "assistant"
        print()
        print(f"  Last message ({prefix} {time_str}):")
        print(f"     {truncate(summary.last_message_text, 200)}")

    print()


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Claude Session Summary Tool")
    parser.add_argument("session_id", nargs="?", help="Session ID")
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

    summary = parse_session(match)
    print_session_summary(summary)


if __name__ == "__main__":
    main()
