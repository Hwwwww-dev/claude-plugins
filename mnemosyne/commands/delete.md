---
description: Delete a specific context record. Requires confirmation before execution.
argument-hint: <id> [--force]
---

# /mnemosyne:delete - Delete Context

User input: $ARGUMENTS

---

## Execution Flow

1. **Validate ID**: Check if the specified context exists
2. **Show details**: Display information about the context to be deleted
3. **Confirm deletion**: Use AskUserQuestion for confirmation
4. **Execute deletion**: Delete folder and update index

---

## Confirmation Flow

```markdown
## Delete Confirmation

The following context will be deleted:

**Title**: Implement user authentication
**ID**: 20241225-103000
**Tags**: feature, auth, React
**Saved at**: 2024-12-25 10:30

This action cannot be undone. Confirm deletion?
```

**Use AskUserQuestion**:
- Option 1: Confirm delete
- Option 2: Cancel

---

## Force Delete

Use `--force` parameter to skip confirmation:
```
/mnemosyne:delete 20241225-103000 --force
```

---

## Output Format

Deletion successful:
```
Context Deleted

Deleted: Implement user authentication (20241225-103000)
```

Deletion cancelled:
```
Deletion cancelled
```

ID not found:
```
Context with ID "xxx" not found

Use `/mnemosyne:list` to view all contexts
```
