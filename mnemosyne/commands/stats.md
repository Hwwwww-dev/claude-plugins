---
description: Use when user says "stats" or wants to see context storage statistics
argument-hint:
---

> Schema reference: All field names follow the index.json v4.0.0 schema defined in context-save/SKILL.md.

# /mnemosyne:stats (Enhanced Inline)

## Capabilities
- Add usage pattern analysis: which contexts were loaded/how often.
- Add storage optimization advice: recommend cleanup strategies based on stats.
- Add overall health score.

## Steps
1. Read `.claude/mnemosyne/index.json` and compute statistics.
2. Output a report with health score and optimization advice.
3. AskUserQuestion to provide follow-up options. Example:
```json
{
  "title":"Stats Actions",
  "style":"single-select",
  "options":["Clean...","List top 10 most accessed...","Close"]
}
```

## Output
```markdown
## Mnemosyne Statistics
**Health Score**: <A-F> (based on age, quality_score, access rate)

| Metric | Value |
|--------|-------|
| Total contexts | <N> |
| Total size | <X> MB |
| Avg. quality (quality_score) | <Q> |

### Usage Pattern
| Top 3 Accessed | Accesses (access_count) |
|----------------|----------|
| <id1>          | <n>      |

### Optimization Advice
- <N> records are older than 90 days and unused. Consider `/mnemosyne:clean --days 90 --unused-days 90`
- <M> records have quality_score below 40. Consider `/mnemosyne:clean --quality-below 40`
```
