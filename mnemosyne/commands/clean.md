---
description: Clean up expired or unused context records.
argument-hint: [--days N] [--dry-run]
---

# /mnemosyne:clean - Clean Contexts

User input: $ARGUMENTS

---

## Cleanup Rules

1. **Clean by time**: `--days N` delete records older than N days (default 90 days)
2. **Preview mode**: `--dry-run` only show records to be deleted, without actual deletion

---

## Execution Flow

1. **Scan records**: Find contexts matching cleanup criteria
2. **Show preview**: List records to be cleaned
3. **Confirm cleanup**: Use AskUserQuestion for confirmation
4. **Execute cleanup**: Delete folders and update index

---

## Preview Output

```markdown
## Cleanup Preview

Context records older than 90 days will be cleaned:

| # | ID | Title | Time |
|---|-----|------|------|
| 1 | 20240901-100000 | Old project config | 2024-09-01 |
| 2 | 20240815-140000 | Test feature | 2024-08-15 |
| 3 | 20240801-090000 | Initialization | 2024-08-01 |

3 contexts will be cleaned, freeing approximately 0.5 MB

Confirm cleanup?
```

---

## Confirmation Flow

**Use AskUserQuestion**:
- Option 1: Confirm cleanup
- Option 2: Cancel
- Option 3: Adjust days

---

## Output Format

Cleanup successful:
```
Cleanup Complete

Deleted 3 expired contexts
Space freed: 0.5 MB
```

No cleanup needed:
```
No Cleanup Needed

No expired contexts found matching the criteria
```

Dry-run mode:
```
Preview Mode (--dry-run)

The above records will be deleted during actual cleanup
Use `/mnemosyne:clean --days 90` to execute cleanup
```
