---
name: context-load
description: Interactive loading of historical contexts: supports by ID, smart recommendation, or search; with conflict detection and stale warning
version: 4.0.0
---

**Path Rule:** All `.claude` paths refer to the project root `.claude/`.

> Schema reference: All field names follow the index.json v4.0.0 schema defined in context-save/SKILL.md.

# Context Load v4.0

## Iron Law
NO LOAD WITHOUT EXISTENCE VERIFICATION.

> Violating the letter of this rule IS violating the spirit.

## Overall Flow (5 Gates)
1. Mode selection (AskUserQuestion) → 2. Target resolution & existence check → 3. Conflict detection (unsaved work) → 4. Stale warning (>7 days) → 5. Load & counters update

### Step 1 (Gate 1) Mode Selection
- Immediately call AskUserQuestion to choose: By ID / Recommend / Search.
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
- By ID: Match ID exactly from `.claude/mnemosyne/index.json`, and verify the directory and `context.md` exist.
- Recommend: Rank Top-N by current repo context:
  - Intersection between `file_map` and paths from `git --no-pager status --porcelain` (more overlap → higher rank);
  - Tag/keyword similarity to current branch name/working directory name;
  - Recency (created_at DESC).
- Search: Reuse context-search filtering/sorting rules.
- Gate: Candidates exist (≥1) and the chosen record's directory/files exist.

### Step 3 (Gate 3) Conflict Detection (Unsaved Work)
- Run `git --no-pager status --porcelain`; if there are unstaged or uncommitted changes:
  - Call AskUserQuestion:
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
- Gate: If Save first, must trigger `mnemosyne:context-save` first; if Proceed, continue; Cancel exits.

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
- Gate: User confirms to continue.

### Step 5 (Final Gate) Load & Update Counters
- Read `context.md` and output to user: Title/saved time/one-line summary/Completion/Next Steps.
- Update index: `access_count += 1`, `last_accessed = now()`.
- Success criteria: Content displayed successfully and index persisted with updates.

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

If you find yourself thinking any of the following, **STOP immediately**:

- "I know which context to load, skip the question" → WRONG. Always let the user choose.
- "No need to check for unsaved work" → WRONG. Conflict detection protects the user.
- "This old context is probably still valid" → WRONG. Always warn if >7 days stale.
- "I'll skip the recommendation step" → WRONG. Smart recommendations save user time.
- "Existence check is unnecessary, the file should be there" → WRONG. Iron Law: NO LOAD WITHOUT EXISTENCE VERIFICATION.

## Rationalization Prevention

| Your Excuse | The Truth |
|---|---|
| "The user specified an ID, no need to ask" | Verify existence first. IDs can be wrong. |
| "Current work is trivial, no conflict risk" | Even trivial work matters. Always check git status. |
| "The context was saved recently, it's fresh" | "Recently" is subjective. Check the actual timestamp. |
| "Recommendation is slow, just load directly" | Speed without accuracy is waste. Recommend first. |
| "The user knows what they want" | Informed choice > assumed choice. Present options. |
