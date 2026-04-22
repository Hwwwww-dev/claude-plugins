---
name: context-search
description: Search historical session contexts with fuzzy matching and post-result interactive loading
version: 4.0.0
---

**Path Rule:** `.claude` = project root `.claude/`.

> Schema: field names follow index.json v4.0.0 in context-save/SKILL.md.

# Context-Search v4.0

## Iron Law
index.json is the sole source of truth; never fabricate entries.

## Localization Rule
All AskUserQuestion `header`/`question`/`label`/`description` MUST render in detected system/conversation language. Never hardcode English. JSON blocks below are structural templates — translate every user-facing string before invoking.

## Gate Protocol (6 Steps)
1. Parse query → 2. Load index → 3. Filter → 4. Match (incl. fuzzy) → 5. Sort → 6. Post-result interaction

### Step 1 (Gate 1) Parse Query
- `$ARGUMENTS`: `<keyword> [--tag tag] [--from date] [--to date]`; no keyword = "list all".
- Gate: identify keyword (or list-all), tag, date range.

### Step 2 (Gate 2) Load Index
- Read `.claude/mnemosyne/index.json` (array). Missing/empty → output no-result template and suggest saving first.
- Gate: parsed OR empty-result branch triggered.

### Step 3 (Gate 3) Filter
- Pre-filter candidates by tag and date window.
- Gate: 0..N candidates.

### Step 4 (Gate 4) Matching (Exact + Fuzzy)
- Priority: title (P1) > summary (P2) > content (P3, read files only if P1/P2 both 0).
- Fuzzy:
  - substring/case-insensitive;
  - Jaro-Winkler≥0.88 or Levenshtein ratio≤0.25 = hit;
  - split keywords, take max match.
- Gate: annotate each record with match-level + score.

### Step 5 (Gate 5) Sorting
- match level → recency (`created_at` DESC) → similarity score DESC.
- Gate: final ordered result set.

### Step 6 (Final Gate) Result Display + Interaction
- Show result summary (ID/Title/Tags/Time/Match).
- Call AskUserQuestion: load an entry or refine. Options derived from actual result set (Top-N ids); translate all strings.
```json
{
  "questions": [
    {
      "header": "<Results i18n>",
      "question": "<Choose a record to load, or refine/cancel i18n>",
      "options": [
        {"label": "<Load id1>", "description": "<title1>"},
        {"label": "<Load id2>", "description": "<title2>"},
        {"label": "<Refine i18n>", "description": "<Back to Step 1 i18n>"},
        {"label": "<Cancel i18n>", "description": "<End search i18n>"}
      ],
      "multiSelect": false
    }
  ]
}
```
- Load <idX> → call `mnemosyne:context-load`; Refine → Step 1; Cancel → end.

## No-Result Output
```markdown
No matching contexts found for "<keyword>".
- Try broader keywords
- Remove tag/date filters
- Use /mnemosyne:list to browse all
```

## Red Lines
- Skipping index for file-by-file full-text search (allowed only when P1/P2 = 0).
- Fabricating or displaying non-existent records.
- Arbitrarily changing sort criteria.
