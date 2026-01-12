---
description: View all saved session context list.
argument-hint: [--limit N] [--tag tag]
---

# /mnemosyne:list - List Contexts

User input: $ARGUMENTS

---

## Execution Flow

**Read index file**: `.claude/mnemosyne/index.json`

**Supported parameters**:
- `--limit N`: Limit display count (default 10)
- `--tag tag`: Filter by tag

---

## Output Format

```markdown
## 📚 Saved Contexts (5 total)

| # | ID | Title | Tags | Time | Quality |
|---|-----|------|------|------|------|
| 1 | 20241225-103000 | Implement user authentication | feature, auth | 12-25 10:30 | 8/8 |
| 2 | 20241224-150000 | Fix login page bug | bugfix | 12-24 15:00 | 7/8 |
| 3 | 20241223-090000 | Project initial configuration | config | 12-23 09:00 | 8/8 |

---

💡 Use `/mnemosyne:load <ID>` to load a specific context
💡 Use `/mnemosyne:search <keyword>` to search contexts
```

---

## Empty List Handling

If no saved contexts exist:
```
📭 No saved contexts yet

Use `/mnemosyne:save` to save current session context
```
