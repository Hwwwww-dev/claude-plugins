---
description: Use when user says "clean" or wants to remove expired/low-value contexts
argument-hint: [--days N] [--quality-below Q] [--unused-days M] [--dry-run]
---

> Schema reference: All field names follow the index.json v4.0.0 schema defined in context-save/SKILL.md.

# /mnemosyne:clean (Enhanced Inline)

## Iron Law
NO BATCH DELETE WITHOUT DRY-RUN FIRST.

## Strategies (Composable)
- Time: `--days N` deletes records created before N days ago (archived/normal; pinned never cleaned).
- Quality: `--quality-below Q` deletes records with quality score < Q.
- Access: `--unused-days M` deletes records not accessed for M days (`last_accessed`).
- Never clean: skip all with `importance=pin`.

## Steps
1. Compute candidates (index filtering + physically delete archived >30 days; others soft-delete to `.archive/`).
2. Preview (Dry-Run): count/estimated size/sample list.
3. AskUserQuestion to allow selecting exclusions. Example:
```json
{
  "title":"Cleanup Preview",
  "style":"multi-select",
  "description":"Select records to exclude; unselected will be cleaned",
  "options":["<id1> <title1>","<id2> <title2>"]
}
```
4. Execute cleanup and update index.

## Gate Conditions
- Gate 1: Dry-Run must be completed first (explicit or implicit).
- Gate 2: User confirms in interaction (or `--dry-run` for preview only).
- Final Gate: All moves/deletions succeed and index consistency passes.

## Output
```
Cleanup complete: deleted <N> contexts (archived <A>, purged <P>), freed <X> MB
```
