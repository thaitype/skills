# skills

My skills for Claude Code Agent. Use as reference and adjust to your own needs.

## Table of Contents

| Skill | Description |
|-------|-------------|
| [`time`](#time) | Get the current local time and date |
| [`todo`](#todo) | Manage personal tasks and daily plans |
| [`claude-session-id`](#claude-session-id) | Find latest Claude Code session ID(s) by project |
| [`claude-context`](#claude-context) | Check context window usage for a session |
| [`claude-usage`](#claude-usage) | Show token usage and estimated API cost for a session |
| [`claude-session-log`](#claude-session-log) | Replay a session as a human-readable transcript or JSON |
| [`claude-tui`](#claude-tui) | Send slash commands to a Claude TUI session via tmux |
| [`skill-creator`](#skill-creator) | Guidance for creating and packaging new skills |

## Setup

Skills are loaded by Claude Code from `.claude/skills/` in your project (or home directory).

Install a skill directly from GitHub using `degit`:

```bash
# Install to current project
npx degit thaitype/skills/<skill-name> .claude/skills/<skill-name>

# Install globally (available in all projects)
npx degit thaitype/skills/<skill-name> ~/.claude/skills/<skill-name>
```

**Prerequisite:** Python 3 is required for skills that include scripts (`todo`, `claude-context`, `claude-usage`, `claude-session-id`, `claude-session-log`, `claude-tui`).

---

## Skills

### `time`

Get the current local time and date. Runs the system `date` command. No setup required.

```bash
npx degit thaitype/skills/time ~/.claude/skills/time
```

---

### `todo`

Manage personal tasks and daily plans stored locally as a JSONL event log. Supports add, list, update, check off, delete, and daily plan generation.

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

Find the latest Claude Code session ID(s) with their last message. Supports filtering by project path (`-p`) and showing multiple sessions (`-n`).

```bash
npx degit thaitype/skills/claude-session-id ~/.claude/skills/claude-session-id
```

**Options:**

| Flag | Description |
|------|-------------|
| `-n <count>` | Number of latest sessions to show (default: 1) |
| `-p <path>` | Filter sessions to a specific project path |
| `--dir <path>` | Override Claude projects directory |

**Environment variables:**

| Variable | Default | Description |
|----------|---------|-------------|
| `CLAUDE_PROJECTS_DIR` | `~/.claude/projects` | Path to Claude projects directory |

---

### `claude-context`

Check context window usage for Claude Code sessions by reading `.jsonl` session files. Shows tokens used, free space, autocompact buffer, session info, and last message.

```bash
npx degit thaitype/skills/claude-context ~/.claude/skills/claude-context
```

**Environment variables:**

| Variable | Default | Description |
|----------|---------|-------------|
| `CLAUDE_PROJECTS_DIR` | `~/.claude/projects` | Path to Claude projects directory |
| `AGENT_SESSION_ID` | — | Session ID fallback when not passed as argument |

---

### `claude-usage`

Show token usage and estimated API cost for a Claude Code session. Supports optional date range filtering and per-model breakdown.

```bash
npx degit thaitype/skills/claude-usage ~/.claude/skills/claude-usage
```

**Environment variables:**

| Variable | Default | Description |
|----------|---------|-------------|
| `CLAUDE_PROJECTS_DIR` | `~/.claude/projects` | Path to Claude projects directory |
| `AGENT_SESSION_ID` | — | Session ID fallback when not passed as argument |

---

### `claude-session-log`

Replay a Claude Code session as a human-readable transcript or structured JSON. Shows assistant text, tool calls, and tool results for every turn. Useful for debugging `claude -p` runs.

```bash
npx degit thaitype/skills/claude-session-log ~/.claude/skills/claude-session-log
```

**Options:**

| Flag | Description |
|------|-------------|
| `--latest` | Auto-pick the most recent session |
| `--json` | Output as structured JSON (no truncation) |
| `--tools-only` | Show only turns with tool calls/results |
| `--full` | Disable 500-char truncation on tool results |
| `--dir <path>` | Override Claude projects directory |

**Environment variables:**

| Variable | Default | Description |
|----------|---------|-------------|
| `CLAUDE_PROJECTS_DIR` | `~/.claude/projects` | Path to Claude projects directory |
| `AGENT_SESSION_ID` | — | Session ID fallback when not passed as argument |

---

### `claude-tui`

Send slash commands (like `/context`, `/compact`, `/cost`) to a Claude Code TUI session via tmux and capture the output. Resumes the target session in a detached tmux pane, sends the command, waits for stable output, and tears down.

```bash
npx degit thaitype/skills/claude-tui ~/.claude/skills/claude-tui
```

**Prerequisites:** tmux (`brew install tmux`)

**Options:**

| Flag | Description |
|------|-------------|
| `--latest` | Auto-pick the most recent session |
| `--timeout <secs>` | Max seconds to wait for output (default: 30) |
| `--dir <path>` | Override Claude projects directory |

**Environment variables:**

| Variable | Default | Description |
|----------|---------|-------------|
| `CLAUDE_PROJECTS_DIR` | `~/.claude/projects` | Path to Claude projects directory |
| `AGENT_SESSION_ID` | — | Session ID fallback when not passed as argument |

---

### `skill-creator`

Guidance for creating and packaging new skills. Covers skill anatomy, design principles, progressive disclosure, and the full creation workflow. No setup required.

```bash
npx degit thaitype/skills/skill-creator ~/.claude/skills/skill-creator
```
