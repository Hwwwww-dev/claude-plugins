---
name: context-search
description: Search historical session contexts with fuzzy matching and post-result interactive loading
version: 4.0.0
---

**Path Rule:** All `.claude` paths refer to the project root `.claude/`.

> Schema reference: All field names follow the index.json v4.0.0 schema defined in context-save/SKILL.md.

# Context-Search v4.0

## Iron Law
Only trust index.json as the source of truth; do not fabricate entries.

## Gate Protocol (6 Steps)
1. Parse query → 2. Load index → 3. Filter → 4. Match (incl. fuzzy) → 5. Sort → 6. Post-result interaction

### Step 1 (Gate 1) Parse Query
- `$ARGUMENTS`: `<keyword> [--tag tag] [--from date] [--to date]`; no keyword means "list all".
- Gate: Identify keyword (or list-all), tag, and date range.

### Step 2 (Gate 2) Load Index
- Read `.claude/mnemosyne/index.json` (array). If missing/empty → output empty-result template and suggest saving first.
- Gate: Either parsed successfully or empty-result branch triggered.

### Step 3 (Gate 3) Filter
- First filter candidates by tag and date window.
- Gate: Obtain 0..N candidates.

### Step 4 (Gate 4) Matching (Exact + Fuzzy)
- Priority levels: title (P1) > summary (P2) > content (P3, read files only if P1/P2 both 0).
- Fuzzy:
  - Substring/case-insensitive matching;
  - Approximate: Jaro-Winkler≥0.88 or Levenshtein ratio≤0.25 counts as a hit;
  - Split keywords and take max match.
- Gate: Annotate each record with match-level and score.

### Step 5 (Gate 5) Sorting
- Sort by match level first, then recency (`created_at` DESC), tie-break by similarity score DESC.
- Gate: Produce final ordered result set.

### Step 6 (Final Gate) Result Display + Interaction
- Show result summary (ID/Title/Tags/Time/Match).
- Immediately call AskUserQuestion: whether to load an entry directly or refine filter.
```json
{
  "title":"Search Results",
  "style":"single-select",
  "description":"Choose a record to load, or cancel to refine",
  "options":["Load <id1>","Load <id2>","Refine","Cancel"]
}
```
- If Load <idX> → call `mnemosyne:context-load`; Refine → back to Step 1; Cancel ends.

## No-Result Output
```markdown
No matching contexts found for "<keyword>".
- Try broader keywords
- Remove tag/date filters
- Use /mnemosyne:list to browse all
```

## Red Lines
- Skipping index and reading files one-by-one for full-text search (allowed only when P1/P2 produce zero results).
- Constructing or displaying non-existent records.
- Arbitrarily changing sorting criteria.
