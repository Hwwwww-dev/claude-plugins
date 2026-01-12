---
description: Search historical session contexts. Supports multi-dimensional search by title, tags, content, and time.
argument-hint: <keyword> [--tag tag] [--from date] [--to date]
---

# /mnemosyne:search - Search Contexts

User input: $ARGUMENTS

---

## Search Dimensions

1. **Title search**: Match context titles
2. **Tag search**: `--tag` filter by tags
3. **Content search**: Full-text search in context content
4. **Time filter**: `--from` and `--to` specify time range

---

## Execution Flow

1. **Parse arguments**: Extract keywords and filter conditions
2. **Read index**: Get metadata from `index.json`
3. **Execute search**:
   - First filter by tags (if specified)
   - Then filter by time (if specified)
   - Finally match keywords against titles and content
4. **Sort results**: Sort by relevance and time

---

## Output Format

```markdown
## Search Results: "authentication"

Found 3 matching contexts:

### 1. Implement user authentication
- **ID**: 20241225-103000
- **Tags**: feature, auth, React
- **Time**: 2024-12-25 10:30
- **Match**: title, content

### 2. Fix authentication token expiration issue
- **ID**: 20241220-140000
- **Tags**: bugfix, auth
- **Time**: 2024-12-20 14:00
- **Match**: title

### 3. Authentication module refactoring
- **ID**: 20241215-090000
- **Tags**: refactor, auth
- **Time**: 2024-12-15 09:00
- **Match**: content

---

Use `/mnemosyne:load <ID>` to load a specific context
```

---

## No Results Handling

```
Search: "xxx"

No matching contexts found

Try:
- Use broader keywords
- Remove tag filters
- Expand time range
```
