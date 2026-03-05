---
name: git-query
description: Quick Git information query. Query commit history, contributors, file changes, branch status, etc. Supports fuzzy search.
version: 1.0.0
color: cyan
---

# Git Query - Quick Git Information Lookup

Query commit history, contributors, file changes, and more from a Git repository. Supports both live queries and cached queries.

## Script Path

Use the `${CLAUDE_PLUGIN_ROOT}` environment variable (set automatically by Claude Code):

```bash
# Script location
${CLAUDE_PLUGIN_ROOT}/skills/git-query/scripts/query.py        # Standard query
```

**Fallback**: Relative path `scripts/query.py` (relies on Claude to resolve the base path automatically)

## Prerequisites

```bash
# Check if inside a git repository
git rev-parse --is-inside-work-tree 2>/dev/null || echo "❌ Not a Git repository"

# Optional: check for cache file (generated after running /atlas:changelog)
ls .claude/.meta/commits.pkg.json 2>/dev/null && echo "✅ Cache available" || echo "⚠️ No cache, using live query"
```

## Query Type Reference

| Command | Description | Git Command |
|---------|-------------|-------------|
| search <keyword> | Search commit messages | git log --grep |
| author <name> | Author commits | git log --author |
| file <path> | File history | git log --follow |
| stats | Contribution stats | git shortlog -sn |
| recent [n] | Recent commits | git log -n |
| changes [ref] | Change stats | git diff --stat |
| blame <file> | Line-level blame | git blame |
| branches | Branch status | git branch -vv |
| tags | Tag list | git tag -l |
| hotfiles | Hot files | git log --name-only |

## Quick Queries

**All calls use the current project path**

```bash
# Using the script
python3 "${CLAUDE_PLUGIN_ROOT}/skills/git-query/scripts/query.py" search <keyword>  # Search commits
python3 "${CLAUDE_PLUGIN_ROOT}/skills/git-query/scripts/query.py" author <name>     # Author commits
python3 "${CLAUDE_PLUGIN_ROOT}/skills/git-query/scripts/query.py" file <path>       # File history
python3 "${CLAUDE_PLUGIN_ROOT}/skills/git-query/scripts/query.py" stats             # Contribution stats
python3 "${CLAUDE_PLUGIN_ROOT}/skills/git-query/scripts/query.py" recent 10         # Last 10 commits
python3 "${CLAUDE_PLUGIN_ROOT}/skills/git-query/scripts/query.py" branches          # Branch status
python3 "${CLAUDE_PLUGIN_ROOT}/skills/git-query/scripts/query.py" tags              # Tag list
python3 "${CLAUDE_PLUGIN_ROOT}/skills/git-query/scripts/query.py" hotfiles          # Hot files

# Direct git commands (fast queries)
git log --oneline --grep="$QUERY" -20                            # Search commits
git log --author="$AUTHOR" --oneline -20                          # Author commits
git log --follow --oneline -- "$FILE" -20                         # File history
git shortlog -sn --no-merges | head -20                           # Contributor ranking
git log --oneline -n 10                                           # Recent commits
git diff --stat HEAD~10..HEAD                                     # Change stats for last 10 commits
git blame -L 1,20 "$FILE"                                         # File blame (first 20 lines)
git branch -vv                                                    # Branch status
git tag -l                                                        # Tag list
```

## Inline Commands (Fallback)

When the script is unavailable, use inline commands:

<details>
<summary>Contributor ranking</summary>

```bash
git shortlog -sn --no-merges | head -20
```

**Example output**:
```
  150  Zhang San
   87  Li Si
   45  Wang Wu
```
</details>

<details>
<summary>Hot files (most frequently modified)</summary>

```bash
git log --pretty=format: --name-only --since="3 months ago" | grep -v '^$' | sort | uniq -c | sort -rn | head -20
```

**Example output**:
```
  45 src/main.js
  32 package.json
  28 README.md
```
</details>

<details>
<summary>Daily commit statistics</summary>

```bash
git log --pretty=format:'%ad' --date=short | sort | uniq -c | tail -30
```

**Example output**:
```
   5 2025-12-01
   8 2025-12-02
   3 2025-12-03
```
</details>

<details>
<summary>Large file detection</summary>

```bash
git ls-tree -r -l HEAD | sort -k 4 -n -r | head -20 | awk '{printf "%-10s %-50s %s\n", $4, $5, $4/(1024*1024)" MB"}'
```

**Example output**:
```
524288     dist/bundle.js                0.5 MB
262144     public/images/banner.jpg      0.25 MB
```
</details>

<details>
<summary>Commit frequency analysis</summary>

```bash
git log --pretty=format:'%h|%an|%ad|%s' --date=short -50
```

**Example output**:
```
a1b2c3d|Zhang San|2025-12-06|feat: add new feature
e4f5g6h|Li Si|2025-12-05|fix: resolve bug
```
</details>

<details>
<summary>File type statistics</summary>

```bash
git ls-files | grep -o '\.[^.]*$' | sort | uniq -c | sort -rn | head -15
```

**Example output**:
```
  120 .js
   85 .py
   45 .md
   30 .json
```
</details>

## Advanced Queries

### 1. Search Commit Messages

```bash
# Search commits containing a keyword
git log --grep="fix" --oneline -20

# Search by author
git log --author="Zhang San" --oneline -20

# Combined search
git log --grep="feat" --author="Zhang San" --since="2 weeks ago" --oneline
```

### 2. File Change Tracking

```bash
# Full file history (including renames)
git log --follow --oneline -- path/to/file.js

# Change stats per commit for a file
git log --follow --stat -- path/to/file.js

# View file content at a specific commit
git show commit-hash:path/to/file.js
```

### 3. Line-Level Blame

```bash
# See who last modified each line
git blame path/to/file.js

# View a specific line range
git blame -L 10,30 path/to/file.js

# Blame state before a specific commit
git blame commit-hash^ -- path/to/file.js
```

### 4. Branches and Tags

```bash
# Detailed branch status (including upstream relationships)
git branch -vv

# View unmerged branches
git branch --no-merged

# View merged branches
git branch --merged

# Tag list with annotations
git tag -n
```

## PKG Data Source (Optional)

If `/atlas:changelog` has been run, cached commit data is available:

```bash
# Check cache
ls .claude/.meta/commits.pkg.json

# Quick stats (using cache)
python3 -c "
import json
with open('.claude/.meta/commits.pkg.json') as f:
    data = json.load(f)
    print(f'Cached commits: {len(data.get(\"commits\", []))}')
    print(f'Contributors: {len(set(c[\"author\"] for c in data.get(\"commits\", [])))}')
"
```

**Cache priority**: Live Git queries take precedence; PKG cache is only used to speed up large historical data analysis.

## Notes

- **Live queries first** - Ensures the most up-to-date data
- **Fuzzy matching supported** - Author names and commit messages support partial matching
- **Performance tip** - For large repositories, limit query scope with flags like `--since` and `-n`
- **Cache acceleration** - Use PKG cache for frequent historical data queries
- **Cross-platform** - Commands work on Linux, macOS, and Windows (Git Bash)

## Common Use Cases

1. **Code review**: View file history and last modifier
2. **Bug tracking**: Search related commits to locate the version that introduced the issue
3. **Contribution stats**: Generate team contribution reports
4. **Refactoring planning**: Identify hot files for priority refactoring
5. **Release preparation**: View changes since the last tag
