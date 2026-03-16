---
name: claude-usage
description: Show token usage and estimated API cost for a Claude Code session. Use when the user asks about session cost, how much a session spent, token breakdown, API usage, or wants to analyze spend over a date range.
---

# Claude Usage

Aggregates token usage and calculates estimated API cost from a session's `.jsonl` file.

## Commands

```bash
# Show total usage for a session (falls back to $AGENT_SESSION_ID if no arg)
python3 .claude/skills/claude-usage/scripts/usage_summary.py <session-id>

# Filter by date range (ISO format, date-only or datetime)
python3 .claude/skills/claude-usage/scripts/usage_summary.py <session-id> --start 2026-03-01
python3 .claude/skills/claude-usage/scripts/usage_summary.py <session-id> --start 2026-03-01T09:00:00 --end 2026-03-16T23:59:59

# Use custom projects directory
python3 .claude/skills/claude-usage/scripts/usage_summary.py <session-id> --dir /path/to/projects
```

## Output

```
  Session: <id>
  Period:  2026-03-01 09:00  →  2026-03-16 18:42
  Turns:   42

  Tokens
    Input:        1.2m
    Cache write:  45.3k
    Cache read:   890.1k
    Output:       123.4k

  Estimated cost: $1.2345

  By model:                           (shown only if session used multiple models)
    claude-sonnet-4-6               38 turns  $1.10
    claude-opus-4-6                  4 turns  $0.13
```

## How cost is calculated

Each assistant turn's tokens are multiplied by the model's per-token price and summed:

| Token type       | Billed as     |
|------------------|---------------|
| `input_tokens`   | input price   |
| `cache_creation` | cache write   |
| `cache_read`     | cache read    |
| `output_tokens`  | output price  |

Prices are estimates based on public Anthropic pricing. Actual billing may differ.
