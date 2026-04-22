---
name: context-save
description: Save current session context (decisions, progress, resumable steps) with dedup detection, quality scoring, and auto-classification
version: 4.0.0
---

**Path Rule:** `.claude` = project root `.claude/`, not `~/.claude/`.

# Context Save v4.0

## Iron Laws
- Record facts/decisions/outcomes only; missing info = "Not mentioned".
- No large code blocks: summary + `file:line` only; long snippets → `snippets/`.
- No disk write without user confirmation.

> Violating the letter IS violating the spirit.

## index.json Schema (4.0.0)
```json
{
  "id": "string",
  "title": "string",
  "summary": "string",
  "tags": ["string"],
  "category": "bugfix|feature|refactor|exploration|config",
  "quality_score": 0,
  "importance": "pin|normal|archive",
  "access_count": 0,
  "last_accessed": "ISO timestamp",
  "created_at": "ISO timestamp",
  "schema_version": "4.0.0",
  "file_map": ["string"],
  "completion_status": "string"
}
```

## Quality Score Definition (0-100)
Weighted by section completeness: Intent(15)+Decisions(10)+Changes(20)+Progress(10)+Issues(10)+Tech(5)+FileMap(10)+Continuation(10)+Stats(5)+Snippets(5). Empty or "Not mentioned" = 0.

## Auto-Classification Rules (Heuristic)
- bugfix: title/commit contains fix/bug/hotfix; small-scope changes in `*.test.*`, `src/*`.
- feature: feat/feature/add/new; new routes/APIs/components/schemas.
- refactor: refactor/rename/restructure; large renaming/abstraction.
- exploration: spike/poc/explore/benchmark.
- config: config/CI/env/script changes (.yml/.json/.env/.sh).

## Gate Execution Protocol (Sequential)
1→2→3→4→5; any Gate fail → stop and report.

### Step 1 (Gate 1) User Confirmation
- Preview: one-line summary, estimated rounds/file changes, modules.
- **Localization**: Detect system/conversation language (`zh-CN`, `en`, `ja`, ...); render ALL `header`/`question`/`label`/`description` in that language. Never hardcode English. User conversing in Chinese → prompt MUST be Chinese.
- **Dynamic Tags**: No fixed list. Derive 4–6 candidates from context — modules, file paths, tech stack, domain keywords, auto-classified `category`. Each `description` cites source (e.g., "detected in `src/auth/*` edits").
- Call AskUserQuestion (MCP) for **Title** and **Tags** only. No separate "Action" question — proceeding to Step 2 = implicit confirmation; cancel = user aborts prompt.
- Skeleton (replace strings with detected language; replace Tags with context-derived candidates):
```json
{
  "questions": [
    {
      "header": "<Title i18n>",
      "question": "<Choose a title for this save i18n>",
      "options": [
        {"label": "<Use suggested i18n>", "description": "<auto-title>"},
        {"label": "<Custom i18n>", "description": "<I will enter a custom title i18n>"}
      ],
      "multiSelect": false
    },
    {
      "header": "<Tags i18n>",
      "question": "<Select tags (max 4) i18n>",
      "options": [
        {"label": "<dynamic-tag-1>", "description": "<why this tag, from context>"},
        {"label": "<dynamic-tag-2>", "description": "<why this tag, from context>"},
        {"label": "<dynamic-tag-3>", "description": "<why this tag, from context>"},
        {"label": "<dynamic-tag-4>", "description": "<why this tag, from context>"}
      ],
      "multiSelect": true
    }
  ]
}
```
- Gate: Title + ≥1 Tag provided.

### Step 2 (Gate 2) Dedup Detection (Similar Entry Alert)
- Read `.claude/mnemosyne/index.json`; flag candidates by title Jaccard≥0.8 or Levenshtein≤0.2, summary similarity≥0.75.
- On match, AskUserQuestion: Merge/Save New/Cancel.
```json
{
  "questions": [
    {
      "header": "Dup",
      "question": "Similar record detected, choose an action:",
      "options": [
        {"label": "Merge", "description": "Merge into existing record"},
        {"label": "Save New", "description": "Save as a new record"},
        {"label": "Cancel", "description": "Cancel and go back"}
      ],
      "multiSelect": false
    }
  ]
}
```
- Merge: update old record's `context.md` §3/§4/§8 + index fields `summary/quality_score/tags/file_map/completion_status/last_accessed`.
- Gate: Merge → verify old record exists and writable; Save New → Step 3.

### Step 3 (Gate 3) Smart Extraction (10-Section Template)
Rule: facts only; missing = "Not mentioned".
1. Intent  2. Key Decisions  3. Code Changes  4. Progress  5. Issues & Solutions
6. Tech Context  7. File Map  8. Continuation Guide  9. Session Stats  10. Key Code Snippets
- Code changes: list new/modified/deleted files, deps, commands; long snippets → `snippets/`.
- Gate: all 10 sections non-empty (or explicit "Not mentioned").

### Step 4 (Gate 4) Scoring & Classification
- Compute `quality_score` per definition; derive `completion_status` from §4 (Done/Partial/Pending).
- Compute `category` via heuristics; default `importance=normal`; `file_map` from §3/§7.
- Show summary to user (no re-confirmation).
- Gate: `quality_score`∈[0,100], `category`∈enum, all fields complete.

### Step 5 (Final Gate) Write
- Directory: `.claude/mnemosyne/<YYYYMMDD-HHmmss>-<slug>/`; generate/validate `index.json`.
- Write `context.md`; update `index.json` (append or merge).
- Success:
  - `context.md` has frontmatter + 10 sections;
  - `index.json` has 1 appended/updated entry, `schema_version=4.0.0`.

## context.md Template (10 Sections)
```markdown
---
id: "<YYYYMMDD-HHmmss>"
title: "<title>"
project: "<project name>"
project_path: "<project path>"
created_at: "<ISO>"
updated_at: "<ISO>"
tags: ["<tags>"]
summary: "<one-line>"
completion: <percent>
---

# <title>
> <one-line>

## 1. Intent
## 2. Key Decisions
|#|Decision|Choice|Reason|
|--|--------|------|------|

## 3. Code Changes
- New:
- Modified:
- Deleted:
- Deps:
- Commands:

## 4. Progress
**Completion**: <X>%
- Done:
- In progress:
- Pending:

## 5. Issues & Solutions
|Issue|Status|Solution|
|-----|------|--------|

## 6. Tech Context
## 7. File Map
## 8. Continuation Guide
## 9. Session Stats
## 10. Key Code Snippets
```

## Success Output
```
✅ Context Saved
📁 .claude/mnemosyne/<folder>/
🏷️ <tags>  📊 quality=<score>  📈 files=<N>
💡 /mnemosyne:load <id> to restore
```

## Red Flags (Self-Check)

Thinking any of these → **STOP**:

- "User already described everything, no need to ask" → WRONG. Always AskUserQuestion.
- "Simple save, skip quality check" → WRONG. Every save gets scored.
- "Save without dedup check" → WRONG. Dedup is mandatory.
- "Template too long, abbreviate" → WRONG. All 10 sections populated.
- "Gate is obvious, skip" → WRONG. "Obvious" is often wrong.

## Rationalization Prevention

| Your Excuse | The Truth |
|---|---|
| "User already specified everything" | Confirmation ≠ assumption. AskUserQuestion to verify. |
| "Too simple for full flow" | Shortcuts damage simple tasks most. |
| "No time for dedup" | Duplicate records waste more time than the check. |
| "Quality scoring is subjective" | Formula is defined. Apply it objectively. |
| "User won't notice missing sections" | Incomplete saves = technical debt. |
