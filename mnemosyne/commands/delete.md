---
description: Use when user says "delete" or wants to remove a specific context record
argument-hint: <id> [--force]
---

> Schema: index.json v4.0.0 (see context-save/SKILL.md).

# /mnemosyne:delete

## Iron Law
NO DELETE WITHOUT EXPLICIT CONFIRMATION.

## Safety Model
Soft delete: move to `.claude/mnemosyne/.archive/<id>/`, set `importance=archive`. Physical purge only after 30 days in archive (by clean batch).

## Steps
1. Verify index entry and directory/`context.md` exist.
2. Show preview: Title/ID/Tags/Time/quality_score.
3. Unless `--force`, AskUserQuestion:
```json
{
  "title":"Delete Confirmation",
  "style":"single-select",
  "description":"Moved to .archive (recoverable within 30 days)",
  "options":["Confirm","Cancel"]
}
```
4. Move directory; update index: `importance=archive`, `last_accessed=now()`.

## Gates
- G1: existence verified
- G2: confirmed (or `--force`)
- Final: directory moved + index updated

## Output
```
Archived: <title> (<id>)  →  .claude/mnemosyne/.archive/<id>/
```

## Restore
Move directory back; reset `importance=normal` in index.
