---
name: git-query
description: Quick Git information query. Query commit history, contributors, file changes, branch status, etc. Supports fuzzy search.
version: 1.0.0
color: cyan
---

# Git Query - Quick Git Information Lookup

Query commit history, contributors, file changes, and more from Git repository. Supports real-time and cached queries.

## Script Path

Use the `${CLAUDE_PLUGIN_ROOT}` environment variable (automatically set by Claude Code):

```bash
# Script location
${CLAUDE_PLUGIN_ROOT}/skills/git-query/scripts/query.py        # Standard query
```

**Alternative**: Relative path `scripts/query.py` (depends on Claude auto-resolving base path)

## Prerequisites

```bash
# Check if inside a git repository
git rev-parse --is-inside-work-tree 2>/dev/null || echo "Not a Git repository"

# Optional: Check cache file (generated after running /atlas:changelog)
ls .claude/.meta/commits.pkg.json 2>/dev/null && echo "Cache available" || echo "No cache, using real-time query"
```

## Query Type Reference

| Command | Description | Git Command |
|---------|-------------|-------------|
| search <keyword> | Search commit messages | git log --grep |
| author <name> | Author commits | git log --author |
| file <path> | File history | git log --follow |
| stats | Contribution statistics | git shortlog -sn |
| recent [n] | Recent commits | git log -n |
| changes [ref] | Change statistics | git diff --stat |
| blame <file> | Line-level tracking | git blame |
| branches | Branch status | git branch -vv |
| tags | Tag list | git tag -l |
| hotfiles | Hot files | git log --name-only |

## Quick Queries

**All calls use current project path**

```bash
# Using script for queries
python3 "${CLAUDE_PLUGIN_ROOT}/skills/git-query/scripts/query.py" search <keyword>  # Search commits
python3 "${CLAUDE_PLUGIN_ROOT}/skills/git-query/scripts/query.py" author <name>     # Author commits
python3 "${CLAUDE_PLUGIN_ROOT}/skills/git-query/scripts/query.py" file <path>       # File history
python3 "${CLAUDE_PLUGIN_ROOT}/skills/git-query/scripts/query.py" stats             # Contribution stats
python3 "${CLAUDE_PLUGIN_ROOT}/skills/git-query/scripts/query.py" recent 10         # Recent 10 commits
python3 "${CLAUDE_PLUGIN_ROOT}/skills/git-query/scripts/query.py" branches          # Branch status
python3 "${CLAUDE_PLUGIN_ROOT}/skills/git-query/scripts/query.py" tags              # Tag list
python3 "${CLAUDE_PLUGIN_ROOT}/skills/git-query/scripts/query.py" hotfiles          # Hot files

# Direct git commands (quick queries)
git log --oneline --grep="$QUERY" -20                            # Search commits
git log --author="$AUTHOR" --oneline -20                          # Author commits
git log --follow --oneline -- "$FILE" -20                         # File history
git shortlog -sn --no-merges | head -20                           # Contributor ranking
git log --oneline -n 10                                           # Recent commits
git diff --stat HEAD~10..HEAD                                     # Change stats for recent 10 commits
git blame -L 1,20 "$FILE"                                         # File tracking (first 20 lines)
git branch -vv                                                    # Branch status
git tag -l                                                        # Tag list
```

## Inline Commands (Fallback)

When the script is unavailable, you can use inline commands:

<details>
<summary>Contributor Ranking</summary>

```bash
git shortlog -sn --no-merges | head -20
```

**Example Output**:
```
  150  Zhang San
   87  Li Si
   45  Wang Wu
```
</details>

<details>
<summary>Hot Files (Most Frequently Modified)</summary>

```bash
git log --pretty=format: --name-only --since="3 months ago" | grep -v '^$' | sort | uniq -c | sort -rn | head -20
```

**Example Output**:
```
  45 src/main.js
  32 package.json
  28 README.md
```
</details>

<details>
<summary>Daily Commit Statistics</summary>

```bash
git log --pretty=format:'%ad' --date=short | sort | uniq -c | tail -30
```

**Example Output**:
```
   5 2025-12-01
   8 2025-12-02
   3 2025-12-03
```
</details>

<details>
<summary>Large File Detection</summary>

```bash
git ls-tree -r -l HEAD | sort -k 4 -n -r | head -20 | awk '{printf "%-10s %-50s %s\n", $4, $5, $4/(1024*1024)" MB"}'
```

**Example Output**:
```
524288     dist/bundle.js                0.5 MB
262144     public/images/banner.jpg      0.25 MB
```
</details>

<details>
<summary>Commit Frequency Analysis</summary>

```bash
git log --pretty=format:'%h|%an|%ad|%s' --date=short -50
```

**Example Output**:
```
a1b2c3d|Zhang San|2025-12-06|feat: add new feature
e4f5g6h|Li Si|2025-12-05|fix: resolve bug
```
</details>

<details>
<summary>File Type Statistics</summary>

```bash
git ls-files | grep -o '\.[^.]*$' | sort | uniq -c | sort -rn | head -15
```

**Example Output**:
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
# Search commits containing keyword
git log --grep="fix" --oneline -20

# Search author's commits
git log --author="Zhang San" --oneline -20

# Combined search
git log --grep="feat" --author="Zhang San" --since="2 weeks ago" --oneline
```

### 2. File Change Tracking

```bash
# Full file history (including renames)
git log --follow --oneline -- path/to/file.js

# Change statistics for each commit to file
git log --follow --stat -- path/to/file.js

# View file content at specific commit
git show commit-hash:path/to/file.js
```

### 3. Code Line-Level Tracking

```bash
# View last modifier of each line
git blame path/to/file.js

# View specific line range
git blame -L 10,30 path/to/file.js

# Track state before specific commit
git blame commit-hash^ -- path/to/file.js
```

### 4. Branches and Tags

```bash
# Detailed branch status (including upstream relationship)
git branch -vv

# View unmerged branches
git branch --no-merged

# View merged branches
git branch --merged

# Tag list (with annotations)
git tag -n
```

## PKG Data Source (Optional)

If you've run `/atlas:changelog`, you can use cached commit data:

```bash
# Check cache
ls .claude/.meta/commits.pkg.json

# Quick statistics (using cache)
python3 -c "
import json
with open('.claude/.meta/commits.pkg.json') as f:
    data = json.load(f)
    print(f'Cached commits: {len(data.get(\"commits\", []))}')
    print(f'Contributors: {len(set(c[\"author\"] for c in data.get(\"commits\", [])))}')
"
```

**Cache Priority**: Real-time Git queries take priority; PKG cache is only used to accelerate analysis of large historical data.

## Notes

- **Real-time queries preferred** - Ensures latest data
- **Fuzzy matching supported** - Author names, commit messages support partial matching
- **Performance optimization** - For large repositories, limit query scope (use --since, -n, etc.)
- **Cache acceleration** - Use PKG cache when frequently querying historical data
- **Cross-platform compatible** - Commands work on Linux, macOS, Windows (Git Bash)

## Common Use Cases

1. **Code Review**: View file history and modifiers
2. **Bug Tracking**: Search related commits, locate version that introduced the issue
3. **Contribution Statistics**: Generate team contribution reports
4. **Refactoring Planning**: Identify hot files, prioritize refactoring
5. **Release Preparation**: View changes since last tag
