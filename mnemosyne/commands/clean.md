---
description: Use when user says "clean" or wants to remove expired/low-value contexts
argument-hint: [--days N] [--quality-below Q] [--unused-days M] [--dry-run]
---

> Schema: index.json v4.0.0 (see context-save/SKILL.md).

# /mnemosyne:clean

## Iron Law
NO BATCH DELETE WITHOUT DRY-RUN FIRST.

## Strategies (composable; `importance=pin` never cleaned)
- `--days N`: created >N days ago (archived/normal).
- `--quality-below Q`: quality_score < Q.
- `--unused-days M`: `last_accessed` >M days ago.

## Steps
1. Compute candidates; physically purge archived >30 days; soft-delete others to `.archive/`.
2. Dry-Run preview: count / estimated size / sample list.
3. AskUserQuestion to exclude entries:
```json
{
  "title":"Cleanup Preview",
  "style":"multi-select",
  "description":"Select records to exclude; unselected will be cleaned",
  "options":["<id1> <title1>","<id2> <title2>"]
}
```
4. Execute cleanup; update index.

## Gates
- G1: Dry-Run completed (explicit or implicit)
- G2: user confirmed (or `--dry-run` preview-only)
- Final: all moves/deletions succeed; index consistent

## Output
```
Cleanup complete: deleted <N> contexts (archived <A>, purged <P>), freed <X> MB
```
