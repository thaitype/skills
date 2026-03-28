---
name: claude-session-log
description: Show a full action log (text, tool calls, tool results) for a Claude Code session. Use when the user wants to replay, debug, or inspect what happened in a session, especially after running claude -p.
---

# Claude Session Log

Replay a Claude Code session as a human-readable transcript or structured JSON.
Shows assistant text, tool calls, and tool results for every turn.

## Commands

```bash
# Show log for a specific session
python3 .claude/skills/claude-session-log/scripts/session_log.py <session-id>

# Show log for the most recent session
python3 .claude/skills/claude-session-log/scripts/session_log.py --latest

# JSON output (always full content, no truncation)
python3 .claude/skills/claude-session-log/scripts/session_log.py --latest --json

# Show only tool calls and results (skip pure text)
python3 .claude/skills/claude-session-log/scripts/session_log.py --latest --tools-only

# Disable truncation on tool results (default: 500 chars)
python3 .claude/skills/claude-session-log/scripts/session_log.py --latest --full

# Use custom projects directory
python3 .claude/skills/claude-session-log/scripts/session_log.py --latest --dir /path/to/projects
```

## Output

Human-readable (default):
```
Session: 82c946c8-1eb8-4c70-9414-813fc0a278e4
Date: 2026-03-28 14:58
Model: claude-opus-4-6
Turns: 5

--- user (14:58:04) ---
Fix the bug in parser.py

--- assistant (14:58:06) ---
Let me read the file first.

  > Read scripts/parser.py
    [2847 chars, truncated]
    def parse(input):
        tokens = input.split()
        ...

  > Edit scripts/parser.py
    old: if t.startswith("--"):
    new: if t.startswith("--") or t.startswith("-"):

Fixed the parser to handle single-dash flags.

--- user (14:58:12) ---
  < tool_result (Read): [ok]
  < tool_result (Edit): [ok]

--- assistant (14:58:15) ---
Done. The parser now handles both --flag and -f syntax.
```

JSON mode (`--json`):
```json
{
  "session_id": "82c946c8-...",
  "model": "claude-opus-4-6",
  "turns": 5,
  "messages": [
    {
      "role": "user",
      "timestamp": "2026-03-28T14:58:04Z",
      "content": [{"type": "text", "text": "Fix the bug..."}]
    },
    {
      "role": "assistant",
      "timestamp": "2026-03-28T14:58:06Z",
      "content": [
        {"type": "text", "text": "Let me read the file first."},
        {"type": "tool_use", "name": "Read", "input": {"file_path": "scripts/parser.py"}}
      ]
    }
  ]
}
```
