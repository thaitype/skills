#!/usr/bin/env python3
"""
Find the most recent Claude Code session(s) and print session ID with last message.

Usage:
    python scripts/latest_session.py          # latest 1 session
    python scripts/latest_session.py -n 5     # latest 5 sessions
"""

import json
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime


def get_claude_projects_dir() -> Path:
    env = os.environ.get("CLAUDE_PROJECTS_DIR")
    if env:
        return Path(env)
    return Path.home() / ".claude" / "projects"


def find_sessions_sorted(projects_dir: Path) -> list[Path]:
    """Return all .jsonl session files sorted by modification time (newest first)."""
    if not projects_dir.exists():
        return []
    sessions = list(projects_dir.rglob("*.jsonl"))
    sessions.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return sessions


def extract_last_message(file_path: Path) -> tuple[str, str, str]:
    """
    Extract the last user/assistant text message from a session file.
    Returns (role, text, timestamp).
    """
    last_role = ""
    last_text = ""
    last_ts = ""

    try:
        lines = file_path.read_text(encoding="utf-8").strip().split("\n")
    except (OSError, UnicodeDecodeError):
        return last_role, last_text, last_ts

    for line in reversed(lines):
        if not line.strip():
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue

        msg = data.get("message")
        if not isinstance(msg, dict):
            continue

        role = msg.get("role", "")
        if role not in ("user", "assistant"):
            continue

        content = msg.get("content", "")
        text = _extract_text(content)
        if not text:
            continue

        ts = data.get("timestamp", "")
        return role, text, ts

    return last_role, last_text, last_ts


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


def truncate(text: str, max_len: int = 150) -> str:
    text = text.replace("\n", " ").strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def fmt_ts(ts: str) -> str:
    if not ts:
        return ""
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return ts


def main():
    parser = argparse.ArgumentParser(description="Find latest Claude Code session(s)")
    parser.add_argument("-n", "--count", type=int, default=1,
                        help="Number of latest sessions to show (default: 1)")
    parser.add_argument("--dir", "-d",
                        help="Claude projects directory (default: ~/.claude/projects)")
    args = parser.parse_args()

    projects_dir = Path(args.dir) if args.dir else get_claude_projects_dir()
    if not projects_dir.exists():
        print(f"Error: Projects directory not found: {projects_dir}", file=sys.stderr)
        sys.exit(1)

    sessions = find_sessions_sorted(projects_dir)
    if not sessions:
        print("No sessions found.", file=sys.stderr)
        sys.exit(1)

    count = min(args.count, len(sessions))

    for i, session_path in enumerate(sessions[:count]):
        sid = session_path.stem
        role, text, ts = extract_last_message(session_path)

        if count == 1:
            print(f"  Session ID: {sid}")
            if ts:
                print(f"  Date: {fmt_ts(ts)}")
            if text:
                print(f"  Last message ({role}): {truncate(text)}")
        else:
            time_str = fmt_ts(ts) if ts else "—"
            msg_str = truncate(text, 100) if text else "(empty)"
            print(f"  {i + 1}. Session ID: {sid}")
            print(f"     Date: {time_str}")
            print(f"     Last message ({role}): {msg_str}")
            if i < count - 1:
                print()


if __name__ == "__main__":
    main()
