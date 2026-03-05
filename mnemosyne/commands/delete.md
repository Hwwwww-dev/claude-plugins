---
description: Use when user says "delete" or wants to remove a specific context record
argument-hint: <id> [--force]
---

> Schema reference: All field names follow the index.json v4.0.0 schema defined in context-save/SKILL.md.

# /mnemosyne:delete (Enhanced Inline)

## Iron Law
NO DELETE WITHOUT EXPLICIT CONFIRMATION.

## Safety Model
- Soft delete first: move to `.claude/mnemosyne/.archive/<id>/` and set `importance=archive` in the index;
- Physical deletion only after 30 days in archive (handled by clean batch).

## Steps
1. Verify existence: both index entry and directory/`context.md` must exist.
2. Show deletion preview (Title/ID/Tags/Time/quality_score).
3. If `--force` not provided: call AskUserQuestion to confirm. Example:
```json
{
  "title":"Delete Confirmation",
  "style":"single-select",
  "description":"The record will be moved into .archive (recoverable within 30 days)",
  "options":["Confirm","Cancel"]
}
```
4. Perform soft delete: move directory; update index record `importance=archive`, `last_accessed=now()`.

## Gate Conditions
- Gate 1: Existence verified;
- Gate 2: User confirmed (or `--force`);
- Final Gate: Directory moved successfully and index updated.

## Output
```
Archived: <title> (<id>)  →  .claude/mnemosyne/.archive/<id>/
```

## Restore
- Move directory back to original path and set `importance` back to `normal` in the index.
