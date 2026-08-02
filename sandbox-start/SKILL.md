---
name: sandbox-start
description: Reference for working inside a project that already has a sandbox/ directory (from sandbox-init) — the sandbox rule, exec/shell conventions, and how to think about upgrading it over time. No parameters, no automation. Read this before doing dev work in such a project, or when the user asks how to work with / upgrade an existing sandbox.
---

# Working with a project sandbox

This is knowledge, not an action — there is nothing to run. Read it, then follow the
conventions below for the rest of the session.

## The sandbox rule

All software development work in this project happens inside its Docker sandbox
container, never on the host. Concretely, on the host you must never:

- Install packages or toolchains (`apt install`, `npm install -g`, `pip install`, …)
- Run build tools, compilers, dev servers, or test suites directly
- Start services or daemons that bind host ports (except ones explicitly published in
  `sandbox/docker-compose.yml`)

The only host-side actions are: managing the sandbox container itself
(`sandbox/sandbox.sh ...`), editing files in the project's own directory, and git
operations on the project's own repo.

## How to run things

```bash
sandbox/sandbox.sh up        # start (or create) the sandbox
sandbox/sandbox.sh status    # check container state
sandbox/sandbox.sh exec CMD  # run one command inside the sandbox
sandbox/sandbox.sh shell     # interactive shell inside the sandbox
sandbox/sandbox.sh down      # stop the sandbox
sandbox/sandbox.sh rebuild   # rebuild the image after editing sandbox/Dockerfile
```

Before running any build/run/install/test command, check: does it start with
`sandbox/sandbox.sh exec` (or run from inside `sandbox/sandbox.sh shell`)? If not, stop
and rewrite it.

Need a new tool? Add it to `sandbox/Dockerfile`, then `sandbox/sandbox.sh rebuild` —
never install it on the host.

## Thinking about upgrades

There is no automated upgrade tool — `sandbox/Dockerfile` mixes a generic base (Ubuntu
version, non-root user, tmux config, `sandbox.sh` itself) with this project's own
toolchain choices, and the two aren't tagged apart. When you want to bring a sandbox up
to date:

1. Compare `sandbox/sandbox.sh` and `sandbox/docker-compose.yml` against a freshly
   generated reference (e.g. run `/sandbox-init` in a scratch directory) by eye — these
   two files rarely have project-specific edits, so differences are usually genuine
   upstream improvements.
2. For `sandbox/Dockerfile`, only touch the parts that match the generic base pattern
   (base image tag, apt package list for core tools, the `dev` user block). Leave
   anything that looks like a deliberate project-specific choice alone.
3. After any change, run `sandbox/sandbox.sh rebuild` and re-verify the project's own
   build/test commands still pass inside the container.
