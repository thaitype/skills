---
name: claude-session-id
description: Find the latest Claude Code session ID(s). Use when the user asks for the current or most recent session ID, wants to find a session, or needs to look up recent sessions to resume or inspect.
---

# Claude Session ID

Find the most recent Claude Code session(s) with their last message.

## Commands

```bash
# Show the latest session (default)
python3 .claude/skills/claude-session-id/scripts/latest_session.py

# Show the N latest sessions
python3 .claude/skills/claude-session-id/scripts/latest_session.py -n 5

# Use custom projects directory
python3 .claude/skills/claude-session-id/scripts/latest_session.py --dir /path/to/projects
```

## Output

Single session (default):
```
  Session: 82c946c8-1eb8-4c70-9414-813fc0a278e4
  Last active: 2026-03-16 10:32
  Last message (assistant): Here's the updated README with setup instructions...
```

Multiple sessions (`-n 3`):
```
  1. 82c946c8-1eb8-4c70-9414-813fc0a278e4  2026-03-16 10:32
     [assistant] Here's the updated README with setup instructions...

  2. a1b2c3d4-5678-9012-3456-789012345678  2026-03-15 18:00
     [user] Can you fix the login bug?

  3. f0e1d2c3-b4a5-9687-0123-456789abcdef  2026-03-14 09:15
     [assistant] Done. The test suite passes now.
```
