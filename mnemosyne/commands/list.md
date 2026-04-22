---
description: Use when user says "list" or wants to see all saved session contexts
argument-hint: [--limit N] [--tag tag] [--sort time|tag|quality_score|last_accessed] [--group tag|date]
---

> Schema: index.json v4.0.0 (see context-save/SKILL.md).

# /mnemosyne:list

## Capabilities
Sort by time/tag/quality_score/last_accessed; group by tag/date; post-action load/delete/search.

## Steps
1. Read `.claude/mnemosyne/index.json`; sort/group per params; paginate (default `--limit 10`).
2. Output table: ID/Title/Tags/created_at/quality_score/last_accessed.
3. AskUserQuestion for follow-up:
```json
{
  "title":"List Actions",
  "style":"single-select",
  "options":["Load <id>","Delete <id>","Search...","Close"]
}
```

## Empty
```
No saved contexts yet. Use /mnemosyne:save first.
```
