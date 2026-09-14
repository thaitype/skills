# skills

My skills for Claude Code Agent. Use as reference and adjust to your own needs.

## Table of Contents

| Skill | Description |
|-------|-------------|
| [`time`](#time) | Get the current local time and date |
| [`todo`](#todo) | Manage personal tasks and daily plans |
| [`money`](#money) | Track personal income, expenses, and transfers between accounts |
| [`claude-session-id`](#claude-session-id) | Find latest Claude Code session ID(s) by project |
| [`claude-context`](#claude-context) | Check context window usage for a session |
| [`claude-usage`](#claude-usage) | Show token usage and estimated API cost for a session |
| [`claude-session-log`](#claude-session-log) | Replay a session as a human-readable transcript or JSON |
| [`claude-tui`](#claude-tui) | Send slash commands to a Claude TUI session via tmux |
| [`sync-git`](#sync-git) | Sync a git repo with remote — pull, auto-commit, push |
| [`skill-creator`](#skill-creator) | Guidance for creating and packaging new skills |
| [`docker-playwright`](#docker-playwright) | Run Playwright tests inside a shared Docker container |
| [`sandbox-init`](#sandbox-init) | Scaffold an isolated Docker dev sandbox for a project |
| [`sandbox-start`](#sandbox-start) | Reference for working inside an existing project sandbox |
| [`english-teacher-roleplay`](#english-teacher-roleplay) | Roleplay partner + English teacher giving Thai feedback notes |

See also: [typ-fleet skills](#typ-fleet-skills) — a dedicated section below for skills that depend
on the typ-fleet ecosystem rather than working standalone.

## Setup

Skills are loaded by Claude Code from `.claude/skills/` in your project (or home directory).

Install with [`skills`](https://github.com/vercel-labs/skills):

```bash
# Install to current project (prompts you to select which skill(s) to add)
npx skills@latest add thaitype/skills

# Install a specific skill without prompting
npx skills@latest add thaitype/skills --skill <skill-name>

# Install globally (available in all projects)
npx skills@latest add thaitype/skills --skill <skill-name> --global
```

**Prerequisite:** Python 3 is required for skills that include scripts (`todo`, `money`, `claude-context`, `claude-usage`, `claude-session-id`, `claude-session-log`, `claude-tui`).

---

## Skills

### `time`

Get the current local time and date. Runs the system `date` command. No setup required.

```bash
npx skills@latest add thaitype/skills --skill time
```

---

### `todo`

Manage personal tasks and daily plans stored locally as a JSONL event log. Supports add, list, update, check off, delete, and daily plan generation.

```bash
npx skills@latest add thaitype/skills --skill todo
```

**Setup:**

The script resolves the data file path relative to the workspace root (`my-data/tasks.jsonl`). Override with an env var if needed:

| Variable | Default | Description |
|----------|---------|-------------|
| `AGENT_TASKS_FILE` | `<workspace>/my-data/tasks.jsonl` | Path to the JSONL task file |

The file and directory are created automatically on first use.

---

### `money`

Track personal income, expenses, and transfers between accounts via a Python CLI. Supports adding transactions, transfers, listing/filtering history, categories/accounts management, balances, and income vs. expense summaries.

```bash
npx skills@latest add thaitype/skills --skill money
```

**Setup:**

Data is stored in `data/skills_data/money/` (created automatically on first write). Override the location with an env var if needed:

| Variable | Default | Description |
|----------|---------|-------------|
| `MONEY_STATE_DIR` | `data/skills_data/money/` (relative to the script) | Path to the money data directory |

---

### `claude-session-id`

Find the latest Claude Code session ID(s) with their last message. Supports filtering by project path (`-p`) and showing multiple sessions (`-n`).

```bash
npx skills@latest add thaitype/skills --skill claude-session-id
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
npx skills@latest add thaitype/skills --skill claude-context
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
npx skills@latest add thaitype/skills --skill claude-usage
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
npx skills@latest add thaitype/skills --skill claude-session-log
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
npx skills@latest add thaitype/skills --skill claude-tui
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

### `sync-git`

Sync the current git repo with remote — fetch, pull with rebase, auto-commit all changes, and push with retry. Handles worktrees, stale locks, conflicts, and network errors with structured exit codes.

```bash
npx skills@latest add thaitype/skills --skill sync-git
```

**Exit codes:**

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Running inside a worktree (merge first) |
| `2` | Rebase/merge conflict (manual resolution needed) |
| `3` | Push rejected after 3 retries |
| `4` | Network/SSH error |

---

### `skill-creator`

Guidance for creating and packaging new skills. Covers skill anatomy, design principles, progressive disclosure, and the full creation workflow. No setup required.

```bash
npx skills@latest add thaitype/skills --skill skill-creator
```

---

### `docker-playwright`

Run Playwright tests for the current project inside a shared, long-lived Docker container (the `pw` container, running the official `mcr.microsoft.com/playwright` image with `$HOME/gits` mounted at `/work`).

```bash
npx skills@latest add thaitype/skills --skill docker-playwright
```

**Prerequisites:** Docker

---

### `sandbox-init`

Scaffold an isolated Docker dev sandbox in the current project directory, so all builds/runs/tests happen inside a container instead of on the host. Generic — not tied to any specific project type.

```bash
npx skills@latest add thaitype/skills --skill sandbox-init
```

**Prerequisites:** Docker

---

### `sandbox-start`

Reference for working inside a project that already has a `sandbox/` directory (from `sandbox-init`) — the sandbox rule, exec/shell conventions, and how to think about upgrading it over time. No parameters, no automation.

```bash
npx skills@latest add thaitype/skills --skill sandbox-start
```

---

### `english-teacher-roleplay`

Turns Claude into an English-speaking roleplay partner who also acts as an English teacher — stays in character replying in English, then adds a short, friendly Thai feedback note pointing out grammar, word choice, or naturalness fixes each turn.

```bash
npx skills@latest add thaitype/skills --skill english-teacher-roleplay
```

---

## typ-fleet skills

Skills under [`typ-fleet-skills/`](typ-fleet-skills/). **Not standalone** — they reference the
`ship` CLI (`ship peek`, `ship ls --json`, `ship cron add`, etc.) and a `locker/` convention that
only exists in a crew's home in that ecosystem. They will not do anything useful dropped into an
unrelated project without adapting those references first.

| Skill | Description |
|-------|-------------|
| [`typ-direct-work`](typ-fleet-skills/typ-direct-work/SKILL.md) | Discipline for directing work carried out by other crews |
| [`typ-do-work`](typ-fleet-skills/typ-do-work/SKILL.md) | Discipline for crews doing work assigned by a director |

### `typ-direct-work`

For a crew directing work carried out by other crews: hold the commissioner's literal brief,
follow up on a fixed timer backed by a state file, filter every arrival against the right
engagement, verify the load-bearing claim yourself, and close only on the commissioner's quoted
acceptance.

---

### `typ-do-work`

For a crew doing work assigned by a director: prove your checks can actually fail, verify from a
cold state rather than your warm machine, report not-done when a check doesn't hold, and name what
you did not establish.
