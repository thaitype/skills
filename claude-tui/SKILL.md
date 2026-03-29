---
name: claude-tui
description: Send slash commands (like /context, /compact, /cost) to a Claude Code TUI session via tmux and capture the output. Use when the user wants to run TUI-only commands on a session programmatically.
---

# Claude TUI

Send slash commands to a Claude Code TUI session via tmux and capture the output.
Resumes the target session in a detached tmux pane, sends the command, waits for output to stabilize, captures it, and tears down.

## Prerequisites

- **tmux** must be installed (`brew install tmux` on macOS)

## Commands

```bash
# Send /context to a specific session
python3 .claude/skills/claude-tui/scripts/tui_cmd.py <session-id> /context

# Send /compact to the most recent session
python3 .claude/skills/claude-tui/scripts/tui_cmd.py --latest /compact

# Send /cost to a session
python3 .claude/skills/claude-tui/scripts/tui_cmd.py <session-id> /cost

# Custom timeout (default: 30s)
python3 .claude/skills/claude-tui/scripts/tui_cmd.py --latest --timeout 60 /compact

# Use custom projects directory
python3 .claude/skills/claude-tui/scripts/tui_cmd.py --latest --dir /path/to/projects /context
```

## Output

```
Session: 82c946c8-1eb8-4c70-9414-813fc0a278e4
Command: /context

Context Usage
...
```

## How it works

1. Launches `claude --resume <session-id>` in a detached tmux session
2. Waits for the TUI to initialize (polls until pane output stabilizes)
3. Sends the slash command via `tmux send-keys`
4. Polls every 0.5s until output stabilizes (two identical captures), max 30s
5. Captures the final pane content
6. Kills the tmux session and Claude process
