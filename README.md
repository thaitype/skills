# skills

My skills for Claude Code Agent. Use as reference and adjust to your own needs.

## Setup

Skills are loaded by Claude Code from `.claude/skills/` in your project (or home directory). Copy any skill folder there to enable it.

```bash
# Copy a skill into your project
cp -r <skill-name> /path/to/your/project/.claude/skills/

# Or install globally (available in all projects)
cp -r <skill-name> ~/.claude/skills/
```

**Prerequisite:** Python 3 is required for skills that include scripts (`todo`, `claude-context`).

---

## Skills

### `time`

Get the current local time and date. No setup required.

---

### `claude-context`

Check context window usage for Claude Code sessions by reading `.jsonl` session files.

No installation required beyond copying the skill folder. By default reads from `~/.claude/projects/`.

**Environment variables:**

| Variable | Default | Description |
|----------|---------|-------------|
| `CLAUDE_PROJECTS_DIR` | `~/.claude/projects` | Path to Claude projects directory |
| `AGENT_SESSION_ID` | — | Session ID fallback when not passed as argument |

---

### `todo`

Manage personal tasks and daily plans stored locally as a JSONL event log.

**Setup:**

The script resolves the data file path relative to the workspace root (`my-data/tasks.jsonl`). Override with an env var if needed:

| Variable | Default | Description |
|----------|---------|-------------|
| `AGENT_TASKS_FILE` | `<workspace>/my-data/tasks.jsonl` | Path to the JSONL task file |

The file and directory are created automatically on first use.

---

### `skill-creator`

Guidance for creating and packaging new skills. No setup required.
