#!/usr/bin/env python3
"""
Claude Session Log Tool

Replay a Claude Code session as a human-readable transcript or structured JSON.
Shows assistant text, tool calls, and tool results for every turn.

Usage:
    python scripts/session_log.py <session-id>
    python scripts/session_log.py --latest
    python scripts/session_log.py --latest --json
    python scripts/session_log.py --latest --tools-only
    python scripts/session_log.py --latest --full
"""

import json
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone


# ── Helpers ──────────────────────────────────────────────────────────────────

TOOL_RESULT_TRUNCATE = 500


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


def find_latest_session(projects_dir: Path) -> Path | None:
    sessions = find_all_sessions(projects_dir)
    if not sessions:
        return None
    sessions.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return sessions[0]


def parse_iso(s: str) -> datetime:
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        dt = datetime.fromisoformat(s + "T00:00:00")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def fmt_time(ts: str) -> str:
    if not ts:
        return "?"
    try:
        dt = parse_iso(ts)
        return dt.strftime("%H:%M:%S")
    except ValueError:
        return ts


def fmt_datetime(ts: str) -> str:
    if not ts:
        return "?"
    try:
        dt = parse_iso(ts)
        return dt.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return ts


def truncate(text: str, limit: int) -> tuple[str, bool]:
    if len(text) <= limit:
        return text, False
    return text[:limit], True


# ── Parsing ──────────────────────────────────────────────────────────────────

def parse_session(file_path: Path) -> list[dict]:
    """Parse a session JSONL file into a list of message records."""
    records = []
    lines = file_path.read_text(encoding="utf-8").strip().split("\n")

    for line in lines:
        if not line.strip():
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue

        rec_type = data.get("type", "")
        if rec_type not in ("user", "assistant"):
            continue

        msg = data.get("message")
        if not isinstance(msg, dict):
            continue

        records.append({
            "role": msg.get("role", rec_type),
            "timestamp": data.get("timestamp", ""),
            "model": msg.get("model", ""),
            "content": msg.get("content", []),
            "usage": msg.get("usage"),
        })

    return records


def extract_session_meta(records: list[dict]) -> dict:
    """Extract session metadata from parsed records."""
    model = ""
    turns = 0
    first_ts = ""
    last_ts = ""

    for rec in records:
        ts = rec["timestamp"]
        if ts:
            if not first_ts:
                first_ts = ts
            last_ts = ts

        if rec["role"] == "assistant":
            turns += 1
            m = rec.get("model", "")
            if m and not m.startswith("<"):
                model = m

    return {
        "model": model,
        "turns": turns,
        "first_ts": first_ts,
        "last_ts": last_ts,
    }


# ── Human-Readable Output ───────────────────────────────────────────────────

def format_tool_input(name: str, inp: dict) -> str:
    """Format tool input for display."""
    if name == "Read":
        return inp.get("file_path", json.dumps(inp))
    if name == "Write":
        return inp.get("file_path", json.dumps(inp))
    if name == "Edit":
        parts = []
        fp = inp.get("file_path", "")
        if fp:
            parts.append(fp)
        old = inp.get("old_string", "")
        new = inp.get("new_string", "")
        if old or new:
            parts.append(f"\n    old: {old[:120]}")
            parts.append(f"\n    new: {new[:120]}")
        return "".join(parts) if parts else json.dumps(inp)
    if name == "Bash":
        return inp.get("command", json.dumps(inp))
    if name == "Grep":
        pattern = inp.get("pattern", "")
        path = inp.get("path", "")
        return f"{pattern}" + (f" in {path}" if path else "")
    if name == "Glob":
        return inp.get("pattern", json.dumps(inp))
    if name == "Agent":
        desc = inp.get("description", "")
        return desc if desc else json.dumps(inp)
    # Fallback: compact JSON
    s = json.dumps(inp, ensure_ascii=False)
    if len(s) > 200:
        return s[:200] + "..."
    return s


def print_human(records: list[dict], session_id: str, meta: dict,
                tools_only: bool, full: bool):
    sep = "\u2500" * 3  # ───

    print()
    print(f"Session: {session_id}")
    print(f"Date: {fmt_datetime(meta['first_ts'])}")
    if meta["model"]:
        print(f"Model: {meta['model']}")
    print(f"Turns: {meta['turns']}")

    for rec in records:
        role = rec["role"]
        ts = fmt_time(rec["timestamp"])
        content = rec["content"]

        if isinstance(content, str):
            content = [{"type": "text", "text": content}]

        has_tools = any(
            b.get("type") in ("tool_use", "tool_result")
            for b in content if isinstance(b, dict)
        )

        if tools_only and not has_tools:
            continue

        print()
        print(f"{sep} {role} ({ts}) {sep}")

        for block in content:
            if not isinstance(block, dict):
                continue

            btype = block.get("type", "")

            if btype == "text":
                text = block.get("text", "")
                if text and not tools_only:
                    print(text)

            elif btype == "tool_use":
                name = block.get("name", "?")
                inp = block.get("input", {})
                formatted = format_tool_input(name, inp)
                print(f"  \u25b6 {name} {formatted}")

            elif btype == "tool_result":
                tool_id = block.get("tool_use_id", "")
                content_val = block.get("content", "")
                is_error = block.get("is_error", False)

                # Extract text from content
                if isinstance(content_val, list):
                    parts = []
                    for item in content_val:
                        if isinstance(item, dict) and item.get("type") == "text":
                            parts.append(item.get("text", ""))
                    content_val = "\n".join(parts)

                if isinstance(content_val, str):
                    status = "error" if is_error else "ok"
                    if not content_val.strip():
                        print(f"  \u23ce tool_result: [{status}]")
                    else:
                        if full:
                            display = content_val
                            truncated = False
                        else:
                            display, truncated = truncate(content_val, TOOL_RESULT_TRUNCATE)
                        total = len(content_val)
                        trunc_label = f" [{total} chars, truncated]" if truncated else ""
                        if is_error:
                            trunc_label = f" [error]{trunc_label}"
                        print(f"  \u23ce tool_result{trunc_label}")
                        # Indent result content
                        for line in display.split("\n")[:20]:
                            print(f"    {line}")
                        if truncated or content_val.count("\n") > 20:
                            print(f"    ...")

            elif btype == "thinking":
                # Thinking is redacted, just note it exists
                sig = block.get("signature", "")
                if sig:
                    print("  [thinking: redacted]")

    print()


# ── JSON Output ──────────────────────────────────────────────────────────────

def print_json(records: list[dict], session_id: str, meta: dict,
               tools_only: bool):
    messages = []
    for rec in records:
        content = rec["content"]
        if isinstance(content, str):
            content = [{"type": "text", "text": content}]

        has_tools = any(
            b.get("type") in ("tool_use", "tool_result")
            for b in content if isinstance(b, dict)
        )

        if tools_only and not has_tools:
            continue

        # Clean content: remove thinking signatures, keep everything else
        clean_content = []
        for block in content:
            if not isinstance(block, dict):
                continue
            btype = block.get("type", "")
            if btype == "thinking":
                continue  # Skip redacted thinking
            clean_content.append(block)

        entry = {
            "role": rec["role"],
            "timestamp": rec["timestamp"],
            "content": clean_content,
        }
        if rec.get("usage"):
            entry["usage"] = rec["usage"]
        messages.append(entry)

    output = {
        "session_id": session_id,
        "model": meta["model"],
        "turns": meta["turns"],
        "date": fmt_datetime(meta["first_ts"]),
        "messages": messages,
    }

    print(json.dumps(output, indent=2, ensure_ascii=False))


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Claude Session Log Tool")
    parser.add_argument("session_id", nargs="?", help="Session ID to inspect")
    parser.add_argument("--latest", action="store_true",
                        help="Use the most recent session")
    parser.add_argument("--json", action="store_true", dest="json_output",
                        help="Output as structured JSON")
    parser.add_argument("--tools-only", action="store_true",
                        help="Show only turns with tool calls/results")
    parser.add_argument("--full", action="store_true",
                        help="Disable truncation on tool results")
    parser.add_argument("--dir", "-d",
                        help="Claude projects directory (default: ~/.claude/projects)")
    args = parser.parse_args()

    projects_dir = Path(args.dir) if args.dir else get_claude_projects_dir()
    if not projects_dir.exists():
        print(f"Error: Projects directory not found: {projects_dir}", file=sys.stderr)
        sys.exit(1)

    # Resolve session file
    if args.latest:
        session_file = find_latest_session(projects_dir)
        if not session_file:
            print("Error: No sessions found.", file=sys.stderr)
            sys.exit(1)
        session_id = session_file.stem
    else:
        session_id = args.session_id or os.environ.get("AGENT_SESSION_ID")
        if not session_id:
            print("Error: No session ID provided. Pass as argument, use --latest, or set AGENT_SESSION_ID.",
                  file=sys.stderr)
            sys.exit(1)
        sessions = find_all_sessions(projects_dir)
        session_file = find_session(sessions, session_id)
        if not session_file:
            print(f"Error: No session found with ID '{session_id}'", file=sys.stderr)
            sys.exit(1)

    # Parse and output
    records = parse_session(session_file)
    meta = extract_session_meta(records)

    if args.json_output:
        print_json(records, session_id, meta, args.tools_only)
    else:
        print_human(records, session_id, meta, args.tools_only, args.full)


if __name__ == "__main__":
    main()
