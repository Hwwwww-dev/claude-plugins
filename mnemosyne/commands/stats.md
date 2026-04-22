---
description: Use when user says "stats" or wants to see context storage statistics
argument-hint:
---

> Schema: index.json v4.0.0 (see context-save/SKILL.md).

# /mnemosyne:stats

## Capabilities
Usage pattern (load frequency); storage optimization advice; overall health score.

## Steps
1. Read `.claude/mnemosyne/index.json`; compute stats.
2. Output report with health score and advice.
3. AskUserQuestion for follow-up:
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
- <N> records older than 90 days and unused. Consider `/mnemosyne:clean --days 90 --unused-days 90`
- <M> records with quality_score below 40. Consider `/mnemosyne:clean --quality-below 40`
```
