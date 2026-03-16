# skills

My skills for Claude Code Agent. Use as reference and adjust to your own needs.

## Setup

Skills are loaded by Claude Code from `.claude/skills/` in your project (or home directory).

Install a skill directly from GitHub using `degit`:

```bash
# Install to current project
npx degit thaitype/skills/<skill-name> .claude/skills/<skill-name>

# Install globally (available in all projects)
npx degit thaitype/skills/<skill-name> ~/.claude/skills/<skill-name>
```

**Prerequisite:** Python 3 is required for skills that include scripts (`todo`, `claude-context`, `claude-usage`, `claude-session-id`).

---

## Skills

### `time`

Get the current local time and date. No setup required.

```bash
npx degit thaitype/skills/time ~/.claude/skills/time
```

---

### `claude-context`

Check context window usage for Claude Code sessions by reading `.jsonl` session files.

```bash
npx degit thaitype/skills/claude-context ~/.claude/skills/claude-context
```

By default reads from `~/.claude/projects/`.

**Environment variables:**

| Variable | Default | Description |
|----------|---------|-------------|
| `CLAUDE_PROJECTS_DIR` | `~/.claude/projects` | Path to Claude projects directory |
| `AGENT_SESSION_ID` | — | Session ID fallback when not passed as argument |

---

### `todo`

Manage personal tasks and daily plans stored locally as a JSONL event log.

```bash
npx degit thaitype/skills/todo ~/.claude/skills/todo
```

**Setup:**

The script resolves the data file path relative to the workspace root (`my-data/tasks.jsonl`). Override with an env var if needed:

| Variable | Default | Description |
|----------|---------|-------------|
| `AGENT_TASKS_FILE` | `<workspace>/my-data/tasks.jsonl` | Path to the JSONL task file |

The file and directory are created automatically on first use.

---

### `claude-session-id`

Find the latest Claude Code session ID(s) with their last message. Defaults to 1, use `-n` for more.

```bash
npx degit thaitype/skills/claude-session-id ~/.claude/skills/claude-session-id
```

**Environment variables:**

| Variable | Default | Description |
|----------|---------|-------------|
| `CLAUDE_PROJECTS_DIR` | `~/.claude/projects` | Path to Claude projects directory |

---

### `claude-usage`

Show token usage and estimated API cost for a Claude Code session. Supports optional date range filtering.

```bash
npx degit thaitype/skills/claude-usage ~/.claude/skills/claude-usage
```

**Environment variables:**

| Variable | Default | Description |
|----------|---------|-------------|
| `CLAUDE_PROJECTS_DIR` | `~/.claude/projects` | Path to Claude projects directory |
| `AGENT_SESSION_ID` | — | Session ID fallback when not passed as argument |

---

### `skill-creator`

Guidance for creating and packaging new skills. No setup required.

```bash
npx degit thaitype/skills/skill-creator ~/.claude/skills/skill-creator
```
