---
name: docker-playwright
description: Run Playwright tests inside a Docker container (the long-lived "pw" container running the official mcr.microsoft.com/playwright image, with $HOME/gits mounted at /work). Use when the user wants to run, debug, or report Playwright tests via Docker, e.g. "run playwright in docker", "/docker-playwright tests/smoke.spec.ts", or "run the smoke tests in the pw container".
---

Run Playwright tests for the current project inside a shared Docker container.

## Constants (edit these if your setup differs)

- `CONTAINER=pw` — container name
- `IMAGE=mcr.microsoft.com/playwright:v1.59.1-noble` — must match the project's `@playwright/test` version (browser binaries are baked into the image)
- `HOST_ROOT=$HOME/gits` mounted at `MOUNT=/work` — the host→container path mapping

## Arguments

Everything passed after the skill name is forwarded verbatim to `playwright test`
(e.g. `tests/smoke.spec.ts --grep @smoke --project chromium`). A bare invocation runs the full suite.

## Gotchas

- **Never use `docker exec -it`** — the `-it` flags fail with "cannot attach stdin to a TTY-enabled container" when not run from a real terminal (scripts, CI, this agent). Use plain `docker exec`.
- **Headed runs** (`--headed`/`--ui`/`--debug`) need a display the container lacks. If the user wants headed, tell them to prefix with `xvfb-run`: `xvfb-run npx playwright test --headed`. Note `--ui`/`--debug` also need VNC/X-forwarding to actually view — impractical without extra setup. Default runs are headless.

## Steps

### 1. Map the current directory into the container

```bash
HOST_PWD="$(pwd)"
case "$HOST_PWD" in
  "$HOME/gits") CPATH="/work" ;;
  "$HOME/gits"/*) CPATH="/work/${HOST_PWD#$HOME/gits/}" ;;
  *) echo "ERROR: CWD ($HOST_PWD) is outside \$HOME/gits — not visible inside the pw container. cd into a project under \$HOME/gits, or ask the user which container path to use." >&2; exit 1 ;;
esac
echo "Container path: $CPATH"
```

If the mapping fails, stop and ask the user for the intended container path rather than running against a bogus directory.

### 2. Ensure the container is running

```bash
if docker ps --format '{{.Names}}' | grep -qx pw; then
  :  # already running
elif docker ps -a --format '{{.Names}}' | grep -qx pw; then
  docker start pw
else
  docker run -d \
    --name pw \
    --init \
    --ipc=host \
    -v "$HOME/gits:/work" \
    -w /work \
    -u "$(id -u):$(id -g)" \
    mcr.microsoft.com/playwright:v1.59.1-noble \
    sleep infinity
fi
```

### 3. Install dependencies only if missing

`node_modules` lives in the mounted host tree, so it persists between runs — only install when absent.

```bash
docker exec pw bash -lc "cd '$CPATH' && [ -d node_modules ] || npm install"
```

### 4. Run the tests (no -it)

Forward the user's args verbatim. `$ARGS` is whatever was passed to the skill (empty = full suite).

```bash
docker exec pw bash -lc "cd '$CPATH' && npx playwright test $ARGS"
```

### 5. Report results

Summarize pass/fail from the output. If tests failed, remind the user they can view the HTML report (it binds `0.0.0.0` so it's reachable from the host):

```bash
docker exec pw bash -lc "cd '$CPATH' && npx playwright show-report --host 0.0.0.0"
```

## Common failure: "No tests found"

The config's `testDir` points to a directory with no `*.spec.ts` files. Check `playwright.config.ts` for the `testDir` value and confirm test files exist there.

## Troubleshooting: agent can't run docker (permission denied)

**Symptom:** any docker command fails with
`permission denied while trying to connect to the docker API at unix:///var/run/docker.sock`.

The socket is owned `root:docker` (mode `660`), so the caller must be a member of the `docker` group. Diagnose which case you're in:

```bash
getent group docker            # is the USER a member at the OS level?
id -nG | tr ' ' '\n' | grep -x docker   # does THIS process carry the group?
```

### Case 1 — user is NOT in the docker group

`getent group docker` does not list the user. The group must be granted. **Stop and ask the human to run:**

```bash
sudo usermod -aG docker "$USER"   # then fully log out and back in
```

(Do not run this yourself — it needs sudo and a re-login to take effect.)

### Case 2 — user IS a member, but this process lacks the group

`getent group docker` lists the user, yet `id -nG` here does not show `docker`. This is the usual case: **supplementary groups are frozen when a process starts and inherited by all children** — they are never re-read from `/etc/group`. So if Claude Code (or an ancestor) was launched before the membership took effect, it stays without the group until restarted.

Find the stale ancestor holding the old group set (a long-lived **tmux server** is the common culprit):

```bash
pid=$$; while [ "$pid" -gt 1 ]; do ps -o pid=,ppid=,comm= -p "$pid"; pid=$(ps -o ppid= -p "$pid"); done
# inspect a suspect ancestor's groups (docker gid from `getent group docker`):
grep -E '^(Name|Groups)' /proc/<ANCESTOR_PID>/status
```

**Immediate workaround (no restart needed):** because the user *is* a member, you can run a single docker command in a fresh child that re-reads `/etc/group`:

```bash
sg docker -c "docker exec pw bash -lc 'cd /work/<project> && npx playwright test'"
```

**Permanent fix — ask the human to restart the stale ancestor:**

- If Claude Code runs under **tmux**: `tmux kill-server`, then from a shell where `id -nG | grep docker` shows `docker`, start tmux and launch `claude` inside it. (Restarting only the tmux *window* is not enough — the background tmux **server** keeps the stale groups.)
- Otherwise: fully log out and back in, then start Claude Code from the fresh session.

After the restart, confirm with `id -nG | grep docker` here — plain `docker` will then work and the `sg` wrapper is unnecessary.