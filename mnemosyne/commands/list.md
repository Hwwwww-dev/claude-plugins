---
description: Use when user says "list" or wants to see all saved session contexts
argument-hint: [--limit N] [--tag tag] [--sort time|tag|quality_score|last_accessed] [--group tag|date]
---

> Schema reference: All field names follow the index.json v4.0.0 schema defined in context-save/SKILL.md.

# /mnemosyne:list (Enhanced Inline)

## Capabilities
- Sorting: by time/tag/quality_score/last_accessed;
- Grouping: by tag or date;
- Post-action interactions: load/delete/search.

## Steps
1. Read `.claude/mnemosyne/index.json`, sort/group per params and paginate (default `--limit 10`).
2. Output table: ID/Title/Tags/created_at/quality_score/last_accessed.
3. AskUserQuestion: choose to load/delete an entry, or go to search. Example:
```json
{
  "title":"List Actions",
  "style":"single-select",
  "options":["Load <id>","Delete <id>","Search...","Close"]
}
```

## Empty List
```
No saved contexts yet. Use /mnemosyne:save first.
```
