---
name: comment-review
description: Review source-code comments and decide whether each comment should be removed, reduced, or kept.
---
# Comment Review

## Guideline

The best comment is no comment.

Code, types, and tests should be self-explanatory whenever possible.

A comment should exist only when it preserves important reasoning, constraints, assumptions, or intent that cannot be clearly understood from the code or tests.

## Task

Review comments in the code and classify each meaningful comment as one of:

1. **Remove**
2. **Reduce**
3. **Keep**

Do not modify implementation behavior unless explicitly asked.

## Rules

For each comment:

1. If it only describes what the code does, **Remove** it.
2. If the same information is already clear from code, types, names, or tests, **Remove** it.
3. If it contains useful reasoning mixed with implementation narration, history, repetition, or unnecessary detail, **Reduce** it to the essential reason.
4. If it explains a non-obvious constraint, invariant, assumption, external limitation, or intentional behavior, **Keep** it.
5. If removing the comment would make a reasonable maintainer or agent more likely to make an incorrect change, **Keep** it.
6. If the comment contains speculative, outdated, unverifiable, or historical information that is not required to understand the current code, remove that part.
   If nothing useful remains, **Remove** the entire comment.
7. If the comment describes behavior better expressed by a test, prefer the test. Remove the comment when it becomes redundant.
8. If the comment conflicts with the implementation or tests, do not assume either side is correct. Mark it for investigation.
9. Never rewrite a comment merely to restate the implementation in shorter words.
10. Prefer the shortest comment that preserves the necessary reasoning.

## Reduce

Use **Reduce** when a comment has valuable information but contains unnecessary detail.

Example:

Before:

```rust
// The service can return the same record more than once because requests
// are retried internally and responses may overlap, so this collection
// needs to remove duplicated entries before the next stage processes them.
```

After:

```rust
// Upstream responses may overlap, so deduplicate before processing.
```

Preserve the reason. Remove narration.

## Remove

Remove comments such as:

```rust
// Increment retry count
retry_count += 1;
```

```rust
// Return the result
return result;
```

```rust
// Check whether the value exists
if value.is_some() {
```

## Keep

Keep comments that preserve non-obvious reasoning:

```rust
// Order matters: authorization must complete before protected data is loaded.
```

```rust
// This operation must remain idempotent because jobs may be delivered more than once.
```

## Conflict Handling

A comment is not a source of truth.

If a comment disagrees with the code or tests:

1. Identify what the comment claims.
2. Identify what the implementation actually does.
3. Check relevant tests and nearby code.
4. Report the mismatch.
5. Do not change behavior solely to match the comment.

## Output

For every reviewed comment, report:

```text
Decision: Remove | Reduce | Keep | Investigate

Reason:
<short explanation>

Suggested comment:
<only when Reduce is selected>
```

When reviewing an entire file, prefer editing the comments directly and report only notable decisions or conflicts.

## Principle

Comments should preserve reasoning, not narrate code.

When useful reasoning exists, keep only the minimum text necessary to preserve it.