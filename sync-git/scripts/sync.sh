#!/usr/bin/env bash
set -euo pipefail

# Exit codes
EXIT_OK=0
EXIT_WORKTREE=1
EXIT_CONFLICT=2
EXIT_PUSH_FAILED=3
EXIT_NETWORK=4

MAX_RETRIES=3
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
LOCK_FILE="$REPO_ROOT/.git/index.lock"

# --- Helpers ---

die() {
  local code="$1"; shift
  echo "$*" >&2
  exit "$code"
}

is_worktree() {
  local main_tree
  main_tree="$(git worktree list | head -1 | awk '{print $1}')"
  [[ "$PWD" != "$main_tree" ]]
}

remove_stale_lock() {
  [[ ! -f "$LOCK_FILE" ]] && return 0
  if pgrep -f "git" > /dev/null 2>&1; then
    # Check if lock is older than 5 seconds (likely stale even with git running)
    local lock_age
    lock_age=$(( $(date +%s) - $(stat -f %m "$LOCK_FILE" 2>/dev/null || stat -c %Y "$LOCK_FILE" 2>/dev/null || echo 0) ))
    if (( lock_age < 5 )); then
      die $EXIT_PUSH_FAILED "PUSH_FAILED: index.lock exists and git process is active"
    fi
  fi
  rm -f "$LOCK_FILE"
  echo "Removed stale index.lock"
}

check_network() {
  local output
  if ! output=$(git ls-remote origin HEAD 2>&1); then
    die $EXIT_NETWORK "NETWORK: cannot reach remote — $output"
  fi
}

# --- Main ---

# Step 0: Worktree check
if is_worktree; then
  die $EXIT_WORKTREE "WORKTREE: must merge worktree first"
fi

# Step 1: Remove stale lock
remove_stale_lock

# Step 2: Check network
check_network

BRANCH="$(git branch --show-current)"

# Step 3: Fetch
git fetch origin "$BRANCH" 2>/dev/null || true  # OK if remote branch doesn't exist yet

AHEAD=$(git rev-list --count "origin/$BRANCH..HEAD" 2>/dev/null || echo 0)
BEHIND=$(git rev-list --count "HEAD..origin/$BRANCH" 2>/dev/null || echo 0)

echo "Branch: $BRANCH (ahead: $AHEAD, behind: $BEHIND)"

# Step 4: Pull if behind
if (( BEHIND > 0 )); then
  stashed=false
  if ! git diff --quiet 2>/dev/null || ! git diff --cached --quiet 2>/dev/null; then
    git stash -q
    stashed=true
  fi

  if ! git pull --rebase origin "$BRANCH" 2>&1; then
    # Check if conflict
    if git diff --name-only --diff-filter=U 2>/dev/null | grep -q .; then
      die $EXIT_CONFLICT "CONFLICT: rebase conflict, manual resolution needed"
    fi
    die $EXIT_NETWORK "NETWORK: pull failed"
  fi

  if $stashed; then
    if ! git stash pop -q 2>&1; then
      die $EXIT_CONFLICT "CONFLICT: stash pop conflict, manual resolution needed"
    fi
  fi
fi

# Step 5: Stage and commit
git add -A

if git diff --cached --quiet 2>/dev/null; then
  echo "Nothing to commit — already up to date"
  # Still might need to push if ahead
  if (( AHEAD == 0 )); then
    echo "Sync complete: no changes"
    exit $EXIT_OK
  fi
else
  TIMESTAMP="$(date +%Y-%m-%dT%H:%M:%S%z)"
  git commit -q -m "$(cat <<EOF
sync: $TIMESTAMP

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
  echo "Committed: sync: $TIMESTAMP"
fi

# Step 6: Push with retry
for attempt in $(seq 1 $MAX_RETRIES); do
  if git push -u origin "$BRANCH" 2>&1; then
    # Count what we pushed
    files_changed=$(git diff --stat HEAD~1 HEAD 2>/dev/null | tail -1 || echo "")
    echo "Pushed to origin/$BRANCH"
    [[ -n "$files_changed" ]] && echo "$files_changed"
    echo "Sync complete"
    exit $EXIT_OK
  fi

  echo "Push rejected (attempt $attempt/$MAX_RETRIES), pulling and retrying..."

  if ! git pull --rebase origin "$BRANCH" 2>&1; then
    if git diff --name-only --diff-filter=U 2>/dev/null | grep -q .; then
      die $EXIT_CONFLICT "CONFLICT: rebase conflict during push retry, manual resolution needed"
    fi
  fi
done

die $EXIT_PUSH_FAILED "PUSH_FAILED: rejected after $MAX_RETRIES retries"
