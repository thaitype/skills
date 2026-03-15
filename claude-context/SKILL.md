---
name: claude-context
description: Check context usage and session info for any Claude Code session. Use when the user asks about context usage, token count, session info, or wants to list/inspect Claude sessions.
---

# Claude Context

Check context window usage for Claude Code sessions by reading `.jsonl` session files.

## When to use

- "how much context is this session using?"
- "check context for session X"
- "show session info for <id>"

## Commands

```bash
# Show context summary for a session (falls back to $AGENT_SESSION_ID if no arg)
python3 .claude/skills/claude-context/scripts/session_summary.py <session-id>

# Use custom projects directory
python3 .claude/skills/claude-context/scripts/session_summary.py <session-id> --dir /path/to/projects
```

## Output

The script shows:
- **Context used** — tokens used vs context window (matches official `/context`)
- **Free space** — remaining tokens
- **Autocompact buffer** — 3.3% of context window reserved for auto-compaction
- **Session info** — ID, project path, resume command
- **Last message** — most recent user or assistant message

## How context is calculated

Context used = the **latest** API call's `input_tokens + cache_read_input_tokens + cache_creation_input_tokens`. This represents the total tokens sent to the model in the most recent turn, which equals the current context window usage.

After compaction (no new API call yet), the script estimates context from the compact summary size + system overhead (~18k) + post-compact messages.
