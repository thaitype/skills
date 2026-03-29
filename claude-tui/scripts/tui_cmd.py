#!/usr/bin/env python3
"""
Claude TUI Command Tool

Send slash commands to a Claude Code TUI session via tmux and capture the output.

Usage:
    python scripts/tui_cmd.py <session-id> /context
    python scripts/tui_cmd.py --latest /compact
    python scripts/tui_cmd.py <session-id> /cost
"""

import json
import os
import sys
import shutil
import argparse
import subprocess
import time
import uuid
from pathlib import Path


# ── Helpers ──────────────────────────────────────────────────────────────────

POLL_INTERVAL = 0.5
DEFAULT_TIMEOUT = 30
TMUX_SESSION_PREFIX = "claude-tui-"


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


def get_session_cwd(session_file: Path) -> str | None:
    """Extract the working directory from a session file."""
    lines = session_file.read_text(encoding="utf-8").strip().split("\n")
    for line in lines:
        if not line.strip():
            continue
        try:
            data = json.loads(line)
            cwd = data.get("cwd")
            if cwd:
                return cwd
        except json.JSONDecodeError:
            continue
    return None


def check_tmux():
    if not shutil.which("tmux"):
        print("Error: tmux is not installed.", file=sys.stderr)
        print("Install with: brew install tmux", file=sys.stderr)
        sys.exit(1)


def tmux_run(*args: str, capture: bool = False) -> subprocess.CompletedProcess:
    cmd = ["tmux"] + list(args)
    return subprocess.run(
        cmd,
        capture_output=capture,
        text=True,
        timeout=10,
    )


def tmux_session_exists(session_name: str) -> bool:
    result = tmux_run("has-session", "-t", session_name, capture=True)
    return result.returncode == 0


def capture_pane(session_name: str) -> str:
    result = tmux_run(
        "capture-pane", "-t", session_name, "-p", "-J", "-S", "-200",
        capture=True,
    )
    return result.stdout


def kill_session(session_name: str):
    if tmux_session_exists(session_name):
        tmux_run("kill-session", "-t", session_name)


def wait_for_stable(session_name: str, timeout: float) -> str:
    """Poll capture-pane until output stabilizes (two identical captures)."""
    start = time.time()
    prev = ""

    while time.time() - start < timeout:
        time.sleep(POLL_INTERVAL)
        current = capture_pane(session_name)

        if current == prev and current.strip():
            return current

        prev = current

    # Timeout — return whatever we have
    return prev


def strip_blank_lines(text: str) -> str:
    """Remove leading/trailing blank lines, collapse multiple blank lines."""
    lines = text.split("\n")

    # Strip trailing blank lines
    while lines and not lines[-1].strip():
        lines.pop()

    # Strip leading blank lines
    while lines and not lines[0].strip():
        lines.pop(0)

    return "\n".join(lines)


# ── Main Logic ───────────────────────────────────────────────────────────────

def run_tui_command(session_id: str, command: str, session_file: Path,
                    timeout: float) -> str:
    """Launch claude --resume in tmux, send command, capture output, kill."""
    tmux_name = f"{TMUX_SESSION_PREFIX}{uuid.uuid4().hex[:8]}"

    # Get the working directory from the session
    cwd = get_session_cwd(session_file) or os.getcwd()

    try:
        # 1. Create detached tmux session with claude --resume
        tmux_run(
            "new-session", "-d", "-s", tmux_name,
            "-x", "200", "-y", "50",
            f"cd {cwd} && claude --resume {session_id}",
        )

        # 2. Wait for TUI to initialize (output stabilizes)
        wait_for_stable(tmux_name, timeout=15)

        # 3. Capture pane state before sending command
        before = capture_pane(tmux_name)

        # 4. Send the slash command
        tmux_run("send-keys", "-t", tmux_name, "-l", "--", command)
        tmux_run("send-keys", "-t", tmux_name, "Enter")

        # 5. Brief pause to let the command start processing
        time.sleep(1.0)

        # 6. Poll until output stabilizes
        output = wait_for_stable(tmux_name, timeout=timeout)

        return output

    finally:
        # 7. Always clean up
        kill_session(tmux_name)


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Send slash commands to a Claude Code TUI session via tmux",
    )
    parser.add_argument("session_id", nargs="?", help="Session ID to resume")
    parser.add_argument("command", help="Slash command to send (e.g. /context)")
    parser.add_argument("--latest", action="store_true",
                        help="Use the most recent session")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT,
                        help=f"Max seconds to wait for output (default: {DEFAULT_TIMEOUT})")
    parser.add_argument("--dir", "-d",
                        help="Claude projects directory (default: ~/.claude/projects)")
    args = parser.parse_args()

    # Check tmux is available
    check_tmux()

    projects_dir = Path(args.dir) if args.dir else get_claude_projects_dir()
    if not projects_dir.exists():
        print(f"Error: Projects directory not found: {projects_dir}", file=sys.stderr)
        sys.exit(1)

    # Resolve session
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

    # Run the command
    command = args.command
    if not command.startswith("/"):
        print(f"Warning: '{command}' does not start with /. Sending anyway.", file=sys.stderr)

    print(f"Session: {session_id}")
    print(f"Command: {command}")
    print()

    output = run_tui_command(session_id, command, session_file, args.timeout)
    output = strip_blank_lines(output)

    if output:
        print(output)
    else:
        print("(no output captured)", file=sys.stderr)


if __name__ == "__main__":
    main()
