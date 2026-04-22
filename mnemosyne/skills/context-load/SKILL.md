---
name: context-load
description: Interactive loading of historical contexts: supports by ID, smart recommendation, or search; with conflict detection and stale warning
version: 4.0.0
---

**Path Rule:** `.claude` = project root `.claude/`.

> Schema: field names follow index.json v4.0.0 in context-save/SKILL.md.

# Context Load v4.0

## Iron Law
NO LOAD WITHOUT EXISTENCE VERIFICATION.

> Violating the letter IS violating the spirit.

## Localization Rule
All AskUserQuestion `header`/`question`/`label`/`description` MUST render in detected system/conversation language (`zh-CN`, `en`, `ja`, ...). Never hardcode English. JSON blocks below are structural templates — translate every user-facing string before invoking.

## Overall Flow (5 Gates)
1. Mode selection → 2. Target resolution & existence check → 3. Conflict detection (unsaved work) → 4. Stale warning (>7d) → 5. Load & counters update

### Step 1 (Gate 1) Mode Selection
- Call AskUserQuestion: By ID / Recommend / Search.
```json
{
  "questions": [
    {
      "header": "Mode",
      "question": "Choose loading mode",
      "options": [
        {"label": "By ID", "description": "Load by exact ID"},
        {"label": "Recommend", "description": "Recommend based on current work"},
        {"label": "Search", "description": "Search by keyword/tag"}
      ],
      "multiSelect": false
    }
  ]
}
```
- Gate: User makes a clear choice.

### Step 2 (Gate 2) Target Resolution & Existence Check
- By ID: exact ID match from `.claude/mnemosyne/index.json`; verify directory and `context.md` exist.
- Recommend: Top-N ranked by:
  - `file_map` ∩ `git --no-pager status --porcelain` paths (more overlap → higher rank);
  - Tag/keyword similarity to branch name / cwd name;
  - Recency (created_at DESC).
- Search: reuse context-search filtering/sorting.
- Gate: ≥1 candidate exists; chosen record's directory/files exist.

### Step 3 (Gate 3) Conflict Detection (Unsaved Work)
- Run `git --no-pager status --porcelain`; on unstaged/uncommitted changes, AskUserQuestion:
```json
{
  "questions": [
    {
      "header": "Conflicts",
      "question": "Unsaved work detected, choose an action:",
      "options": [
        {"label": "Save first", "description": "Save current work first"},
        {"label": "Proceed anyway", "description": "Continue loading anyway"},
        {"label": "Cancel", "description": "Cancel this load"}
      ],
      "multiSelect": false
    }
  ]
}
```
- Gate: Save first → trigger `mnemosyne:context-save` first; Proceed → continue; Cancel → exit.

### Step 4 (Gate 4) Stale Warning
- If `now - created_at > 7d`, warn as `stale`:
```json
{
  "questions": [
    {
      "header": "Stale",
      "question": "This record is older than 7 days. Continue loading?",
      "options": [
        {"label": "Load anyway", "description": "Load this record anyway"},
        {"label": "Back", "description": "Go back and reselect"}
      ],
      "multiSelect": false
    }
  ]
}
```
- Gate: User confirms continue.

### Step 5 (Final Gate) Load & Update Counters
- Read `context.md`; output: Title / saved time / one-line summary / Completion / Next Steps.
- Update index: `access_count += 1`, `last_accessed = now()`.
- Success: content displayed; index persisted.

## Output Template
```markdown
## Context Loaded
**Title**: <title>  **Saved at**: <YYYY-MM-DD HH:mm>  **Stale**: <yes/no>

### Summary
<summary>

### Progress
- [x] ...
- [ ] ...

### Next Steps
<actions>
```

## Red Flags (Self-Check)

Thinking any of these → **STOP**:

- "I know which context to load, skip the question" → WRONG. Let user choose.
- "No need to check unsaved work" → WRONG. Conflict detection protects user.
- "Old context probably still valid" → WRONG. Always warn if >7d.
- "Skip recommendation step" → WRONG. Saves user time.
- "File should be there, skip existence check" → WRONG. Iron Law: NO LOAD WITHOUT EXISTENCE VERIFICATION.

## Rationalization Prevention

| Your Excuse | The Truth |
|---|---|
| "User specified an ID, no need to ask" | Verify existence. IDs can be wrong. |
| "Trivial work, no conflict risk" | Always check git status. |
| "Saved recently, it's fresh" | "Recently" is subjective. Check timestamp. |
| "Recommendation is slow" | Speed without accuracy = waste. |
| "User knows what they want" | Informed > assumed. Present options. |
