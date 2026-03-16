---
name: todo
description: Manage personal tasks and daily plans. Use when the user wants to add, view, update, check off, or delete tasks. Also use when drafting or viewing a daily plan. Tasks are stored locally in my-data/tasks.jsonl (JSONL event log). Daily plans are freeform markdown files in my-data/daily-plans/YYYY-MM-DD.md.
---

# Todo Skill

## Task Storage

Tasks are stored as append-only events in `my-data/tasks.jsonl`. Use the helper script for all task operations.

**Script path:** `.claude/skills/todo/scripts/tasks.py`

## Task Fields

| Field | Values |
|-------|--------|
| `title` | string |
| `checked` | `false` (open) / `true` (done) |
| `priority` | `P0` (urgent+important) · `P1` (not urgent+important) · `P2` (urgent+not important) · `P3` (neither) |
| `domain` | `Personal` · `Work` |
| `due_date` | `YYYY-MM-DD` or omit |

## Commands

```bash
# Add
python3 .claude/skills/todo/scripts/tasks.py add --title "..." --priority P1 --domain Work --due 2026-03-20

# List (default: hide checked tasks)
python3 .claude/skills/todo/scripts/tasks.py list
python3 .claude/skills/todo/scripts/tasks.py list --domain Work
python3 .claude/skills/todo/scripts/tasks.py list --priority P0
python3 .claude/skills/todo/scripts/tasks.py list --all        # include checked
python3 .claude/skills/todo/scripts/tasks.py list --checked    # only checked

# Check off / Update
python3 .claude/skills/todo/scripts/tasks.py update <id> --checked true
python3 .claude/skills/todo/scripts/tasks.py update <id> --priority P0 --due 2026-03-18

# Delete
python3 .claude/skills/todo/scripts/tasks.py delete <id>

# Get full detail
python3 .claude/skills/todo/scripts/tasks.py get <id>
```

IDs support short prefix (first 8 chars shown in list output).

## Daily Plan

Daily plans are freeform markdown stored at `my-data/daily-plans/YYYY-MM-DD.md`.

When drafting a daily plan:
1. Run `list` to get open tasks (optionally filter by domain)
2. Draft a time-blocked plan in markdown — consider the user's routine and task priorities
3. Write to `my-data/daily-plans/YYYY-MM-DD.md`

**Example plan format:**
```markdown
# Daily Plan — Mar 15, 2026

08:00 ...
09:00 ...
...
```
