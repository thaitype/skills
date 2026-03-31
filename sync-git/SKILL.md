---
name: sync-git
description: Sync the current git repo with remote — pull, auto-commit, push, and resolve conflicts. Use when user says "sync", "sync repo", "push changes", "save changes", or wants to commit and push all changes. Also use when user mentions conflicts during sync.
---

# Sync Git

## Usage

Run the sync script from the repo root:

```bash
bash .claude/skills/sync-git/scripts/sync.sh
```

## Interpret output

- **exit 0** — Success. Show the stdout summary to the user. Done.
- **exit 1** — Worktree detected. Follow **Fallback: Worktree** below.
- **exit 2** — Rebase conflict. Follow **Fallback: Conflict Resolution** below.
- **exit 3** — Push rejected after 3 retries. Follow **Fallback: Push Failure** below.
- **exit 4** — Network/SSH error. Tell user to check SSH agent or connection.

---

## Fallback: Worktree

If running inside a worktree (not the main working tree):

1. **Commit** any uncommitted changes in the worktree branch.
2. **Determine the main working tree's branch**:
   ```bash
   MAIN_TREE="$(git worktree list | head -1 | awk '{print $1}')"
   TARGET_BRANCH="$(git -C "$MAIN_TREE" branch --show-current)"
   ```
3. **Switch to the main repo and merge**:
   ```bash
   cd "$MAIN_TREE"
   git merge <worktree-branch> --no-edit
   ```
   If there are conflicts, resolve using **Fallback: Conflict Resolution** rules.
4. **Clean up the worktree** (remove it after successful merge):
   ```bash
   git worktree remove <worktree-path>
   git branch -d <worktree-branch>
   ```
   If merge failed, leave the worktree intact and report the error.

Then re-run the sync script from the main repo.

## Fallback: Conflict Resolution

When rebase or merge conflicts occur:

- For text/content files (`.md`, `.txt`, etc.): accept **both** changes — combine content from both sides so no data is lost.
- For config/generated files (`.json`, lock files, etc.): accept **theirs** (remote) to keep config in sync across machines.
- After resolving:
  ```bash
  git add -A
  git rebase --continue
  ```

Then re-run the sync script to push.

## Fallback: Push Failure

If push is still rejected after script retries:

1. Run `git fetch origin` and `git log --oneline origin/<branch>..HEAD` to understand divergence.
2. Try `git pull --rebase origin <branch>` manually, resolving any conflicts per rules above.
3. Push again. If still failing, report to user.
