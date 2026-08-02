---
name: sandbox-init
description: Scaffold an isolated Docker dev sandbox for the current project directory. Generic — not tied to any specific fleet or crew concept; works for any project. Use when the user wants to set up (or a project needs) an isolated container for all builds/runs/tests, e.g. "/sandbox-init" or "/sandbox-init myproject".
---

# Scaffold a project sandbox

This installs a self-contained Docker sandbox in the current project directory, so all
builds/runs/tests happen inside a container instead of on the host.

## Steps

1. **Determine the sandbox name.**
   - Base name: `$ARGUMENTS` if passed, otherwise `$(basename "$PWD")`.
   - Append a 6-char hash of the absolute project path, so two unrelated
     projects that happen to share a base name never collide:
     ```bash
     HASH=$(echo -n "$(realpath .)" | sha256sum | cut -c1-6)
     NAME="<base-name>-${HASH}"
     ```
   - This resolved `NAME` is what `__NAME__` gets substituted with everywhere
     below. It's deterministic (same path → same name every time), so
     re-running this skill or `sandbox.sh rebuild` from the same directory
     always targets the same container — never generate a random suffix.

2. **Check for an existing `sandbox/` directory.** If one already exists, stop and ask
   the user for confirmation before overwriting — do not clobber silently.

3. **Check for a `workspace/` directory** alongside where `sandbox/` will go. The
   sandbox only ever mounts `workspace/` into the container — not the project root —
   so the sandbox's own `Dockerfile`/`docker-compose.yml`/`sandbox.sh` stay invisible
   (and unmodifiable) from inside the container.
   - If `workspace/` already exists, use it as-is.
   - If it doesn't exist and the project's code already lives at the top level (e.g.
     `package.json`, `src/`, `.git/` sit directly in the project root), **stop and ask
     the user** whether to (a) create an empty `workspace/` for new/future work while
     leaving existing code where it is (sandbox won't see the existing code), or (b)
     move the existing code into `workspace/` first. Do not guess — this is a
     structural change to the project layout.
   - If it doesn't exist and the project is empty/new, just create `workspace/`.

4. **Read `templates/Dockerfile`** (bundled with this skill) as a reference baseline —
   Ubuntu 24.04, build-essential/git/curl/jq/tmux, Node 22 + pnpm, Python 3 + venv, a
   non-root `dev` user (uid 1000). Adapt it to the actual project:
   - If the project clearly doesn't need a toolchain present in the reference (e.g. no
     `package.json` → drop Node), remove it.
   - If the project needs something not in the reference (Rust, Go, a specific DB
     client, …), add the install steps yourself — check the project's manifest files
     (`Cargo.toml`, `go.mod`, `requirements.txt`, …) and, if unsure how to install a
     toolchain, look up the official install docs before writing the `RUN` line.
   - Keep the non-root `dev` user, `WORKDIR /workspace`, and `CMD ["sleep", "infinity"]`
     pattern — these aren't stack-specific.

5. **Generate the remaining 3 files** in `sandbox/` under the project root, using
   `templates/docker-compose.yml`, `templates/sandbox.sh`, and `templates/tmux.conf`
   as-is except substituting the sandbox name from step 1 wherever `__NAME__` appears:
   ```bash
   sed "s/__NAME__/$NAME/g" templates/docker-compose.yml > sandbox/docker-compose.yml
   sed "s/__NAME__/$NAME/g" templates/sandbox.sh > sandbox/sandbox.sh
   chmod +x sandbox/sandbox.sh
   cp templates/tmux.conf sandbox/tmux.conf
   ```
   Confirm no `__NAME__` remains anywhere in `sandbox/` before moving on.

6. **Verify:** run `sandbox/sandbox.sh up`, then `sandbox/sandbox.sh status` to confirm
   the container is running.

7. **Tell the user:**
   - What was created and the resolved sandbox name.
   - That all future dev commands in this project must go through
     `sandbox/sandbox.sh exec <cmd>` / `sandbox/sandbox.sh shell` — never directly on
     the host, never raw `docker exec`.
   - Point them at `/sandbox-start` for the full operating rules and how to think about
     upgrading the sandbox later.

## Rules

- NEVER overwrite an existing `sandbox/` without explicit confirmation.
- NEVER hardcode any specific crew/fleet name — the only identity is the resolved
  sandbox name from step 1.
- NEVER omit or hand-simplify the `name:` field in `docker-compose.yml`, and never
  replace the path-hash with a random value — see the comment in
  `templates/docker-compose.yml` for why (Compose project-name collisions can
  recreate/destroy an unrelated project's sandbox container).
- NEVER write to the project's CLAUDE.md/AGENTS.md — this skill only touches `sandbox/`.
- Resource limits (4 cpus, 4g mem, 2048 pids) are fixed defaults, not configurable via
  argument — if a project needs different limits, the user edits `docker-compose.yml`
  directly after generation.
