---
name: context-save
description: Save current session context (decisions, progress, resumable steps) with dedup detection, quality scoring, and auto-classification
version: 4.0.0
---

**Path Rule:** All `.claude` paths refer to the project root `.claude/`, not `~/.claude/`.

# Context Save v4.0

## Iron Laws
- Only record "facts/decisions/outcomes"; write "Not mentioned" for missing info.
- Do not save large code blocks: only summaries + `file:line` references; long snippets go to `snippets/`.
- Do not write to disk without user confirmation.

> Violating the letter of this rule IS violating the spirit.

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
Weighted by section completeness: Intent(15)+Decisions(10)+Changes(20)+Progress(10)+Issues(10)+Tech(5)+FileMap(10)+Continuation(10)+Stats(5)+Snippets(5). Empty sections score 0; "Not mentioned" scores 0.

## Auto-Classification Rules (Heuristic)
- bugfix: Commit/title contains fix/bug/hotfix; changes concentrated in `*.test.*`, `src/*` small-scope fixes.
- feature: Contains feat/feature/add/new; adds routes/APIs/components/table schemas.
- refactor: Contains refactor/rename/restructure; extensive renaming/abstraction changes.
- exploration: Contains spike/poc/explore/benchmark.
- config: Primarily config/CI/environment/script changes (.yml/.json/.env/.sh etc.).

## Gate Execution Protocol (Must pass sequentially)
1→2→3→4→5; if any Gate fails, stop and report.

### Step 1 (Gate 1) User Confirmation
- Generate quick preview: one-line summary, estimated rounds/file changes, involved modules.
- **Localization**: Detect the system/conversation language (e.g., `zh-CN`, `en`, `ja`) and render ALL `header`/`question`/`label`/`description` strings in that language. Never hardcode English. If the user has been conversing in Chinese, the prompt MUST be in Chinese.
- **Dynamic Tags**: Do NOT use a fixed tag list. Derive 4–6 candidate tags from the actual conversation context — involved modules, file paths, tech stack, domain keywords, and the auto-classified `category`. Each candidate's `description` should cite why (e.g., "detected in `src/auth/*` edits").
- Call AskUserQuestion (MCP) to collect **Title** and **Tags** only. Do NOT ask a separate "Action" question — proceeding to Step 2 after the user answers is the implicit confirmation; cancellation is handled by the user declining/aborting the prompt.
- Example skeleton (replace strings with the detected language; replace Tags options with context-derived candidates):
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
- Gate condition: User provides Title and at least 1 Tag.

### Step 2 (Gate 2) Dedup Detection (Similar Entry Alert)
- Read history from `.claude/mnemosyne/index.json`, flag candidates by title Jaccard≥0.8 or Levenshtein≤0.2, summary similarity≥0.75.
- If matched, call AskUserQuestion to ask: Merge/Save New/Cancel.
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
- Merge: Update old record's `context.md` §3/§4/§8, and update index fields `summary/quality_score/tags/file_map/completion_status/last_accessed`.
- Gate condition: If Merge is selected, verify old record exists and is writable; if Save New, proceed to Step 3.

### Step 3 (Gate 3) Smart Extraction (10-Section Template)
Extraction rule: Only write facts; write "Not mentioned" for missing info.
1. Intent  2. Key Decisions  3. Code Changes  4. Progress  5. Issues & Solutions
6. Tech Context  7. File Map  8. Continuation Guide  9. Session Stats  10. Key Code Snippets
- Code changes: List new/modified/deleted files, dependencies, and commands; long snippets go to `snippets/`.
- Gate condition: All 10 sections exist and are non-empty (or explicitly marked "Not mentioned").

### Step 4 (Gate 4) Scoring & Classification
- Calculate `quality_score` based on "Quality Score Definition"; derive `completion_status` from §4 (e.g., Done/Partial/Pending).
- Calculate `category` using heuristics; default `importance=normal`; `file_map` derived from §3/§7.
- Display summary to user (no re-confirmation needed).
- Gate condition: `quality_score`∈[0,100], `category`∈enum, all fields complete.

### Step 5 (Final Gate) Write
- Directory: `.claude/mnemosyne/<YYYYMMDD-HHmmss>-<slug>/`; generate/validate `index.json`.
- Write `context.md` and update `index.json` (append or merge).
- Success criteria:
  - `context.md` contains frontmatter + 10 sections;
  - `index.json` has 1 entry appended/updated, `schema_version=4.0.0`.

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

If you find yourself thinking any of the following, **STOP immediately**:

- "The user already described everything, no need to ask" → WRONG. Always confirm via AskUserQuestion.
- "This is a simple save, skip the quality check" → WRONG. Every save deserves quality scoring.
- "I'll just save without checking for duplicates" → WRONG. Dedup check is mandatory.
- "The section template is too long, I'll abbreviate" → WRONG. All 10 sections must be populated.
- "I can skip the Gate, it's obvious" → WRONG. Gates exist because "obvious" is often wrong.

## Rationalization Prevention

| Your Excuse | The Truth |
|---|---|
| "User already specified everything" | Confirmation ≠ assumption. Call AskUserQuestion to verify. |
| "Too simple to need the full flow" | Simple tasks are where shortcuts cause the most damage. |
| "No time for duplicate checking" | Duplicate records waste more time than checking prevents. |
| "Quality scoring is subjective" | The formula is defined. Apply it objectively. |
| "The user won't notice missing sections" | Incomplete saves are technical debt. |
