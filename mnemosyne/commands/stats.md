---
description: Display context storage statistics.
argument-hint:
---

# /mnemosyne:stats - Statistics

---

## Execution Flow

1. **Read index**: Get all records from `index.json`
2. **Calculate statistics**:
   - Total count
   - Distribution by tags
   - Distribution by time
   - Quality score distribution
   - Storage space usage

---

## Output Format

```markdown
## Mnemosyne Statistics

### Overview
| Metric | Value |
|------|------|
| **Total contexts** | 15 |
| **Storage location** | .claude/mnemosyne/ |
| **Space used** | 2.3 MB |
| **Earliest record** | 2024-12-01 |
| **Latest record** | 2024-12-25 |

### Tag Distribution
| Tag | Count |
|------|------|
| feature | 8 |
| bugfix | 4 |
| refactor | 2 |
| config | 1 |

### Quality Scores
| Score | Count |
|------|------|
| 8/8 (complete) | 10 |
| 7/8 | 3 |
| 6/8 | 2 |

### Time Distribution
| Month | Count |
|------|------|
| 2024-12 | 10 |
| 2024-11 | 5 |

---

Use `/mnemosyne:clean` to clean up expired records
```

---

## Empty Data Handling

```
Mnemosyne Statistics

No saved contexts yet

Use `/mnemosyne:save` to start saving session contexts
```
