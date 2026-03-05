# Git Query Skill

Quick Git information lookup tool for querying commit history, contributors, file changes, branch status, and more.

## Features

- 🔍 **Commit search**: Search commit messages by keyword
- 👤 **Author query**: Look up commit records for a specific author
- 📄 **File history**: Track the full change history of a file
- 📊 **Contribution stats**: Show commit counts for all contributors
- 🕐 **Recent commits**: Quickly view the most recent commits
- 🌿 **Branch status**: View all local branches and their status
- 🏷️ **Tag list**: List all tags in the repository
- 🔥 **Hot files**: Identify the most frequently modified files

## Quick Start

### Using the Script

```bash
# Search commits
python3 "${CLAUDE_PLUGIN_ROOT}/skills/git-query/scripts/query.py" search "fix bug"

# Query by author
python3 "${CLAUDE_PLUGIN_ROOT}/skills/git-query/scripts/query.py" author "Zhang San"

# File history
python3 "${CLAUDE_PLUGIN_ROOT}/skills/git-query/scripts/query.py" file src/main.js

# Contribution stats
python3 "${CLAUDE_PLUGIN_ROOT}/skills/git-query/scripts/query.py" stats

# Recent commits
python3 "${CLAUDE_PLUGIN_ROOT}/skills/git-query/scripts/query.py" recent 10

# Branch status
python3 "${CLAUDE_PLUGIN_ROOT}/skills/git-query/scripts/query.py" branches

# Tag list
python3 "${CLAUDE_PLUGIN_ROOT}/skills/git-query/scripts/query.py" tags

# Hot files
python3 "${CLAUDE_PLUGIN_ROOT}/skills/git-query/scripts/query.py" hotfiles
```

### Direct Git Commands

```bash
# Search commits
git log --oneline --grep="keyword" -20

# Contributor ranking
git shortlog -sn --no-merges | head -20

# Hot files
git log --pretty=format: --name-only --since="3 months ago" | grep -v '^$' | sort | uniq -c | sort -rn | head -20
```

## Example Output

### Commit Search

```
🔍 Searching commits: "fix bug"

Hash    | Date       | Author    | Message
--------------------------------------------------------------------------------
a1b2c3d | 2025-12-06 | Zhang San | fix: resolve bug in auth module
e4f5g6h | 2025-12-05 | Li Si     | fix: bug in payment flow

✅ Found 2 matches (up to 20 shown)
```

### Hot Files

```
🔥 Hot files (last 3 months)

Changes | File Path
--------------------------------------------------------------------------------
     48 | src/main.js
     32 | package.json
     28 | README.md

✅ 120 files modified in total (showing top 20)
```

## Full Documentation

See [SKILL.md](./SKILL.md) for complete usage instructions and advanced features.

## Dependencies

- Python 3.6+
- Git 2.0+

## License

MIT
