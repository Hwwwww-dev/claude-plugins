# Git Query Skill

Quick Git information query tool for querying commit history, contributors, file changes, branch status, and more.

## Features

- **Commit Search**: Search commit messages by keyword
- **Author Query**: Query commit records by specific author
- **File History**: Track complete change history of files
- **Contribution Statistics**: Display commit counts for all contributors
- **Recent Commits**: Quickly view recent commit records
- **Branch Status**: View all local branches and their status
- **Tag List**: List all tags in the repository
- **Hot Files**: Identify most frequently modified files

## Quick Start

### Using Script Queries

```bash
# Search commits
python3 "${CLAUDE_PLUGIN_ROOT}/skills/git-query/scripts/query.py" search "fix bug"

# Query author
python3 "${CLAUDE_PLUGIN_ROOT}/skills/git-query/scripts/query.py" author "Zhang San"

# File history
python3 "${CLAUDE_PLUGIN_ROOT}/skills/git-query/scripts/query.py" file src/main.js

# Contribution statistics
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

### Using Git Commands Directly

```bash
# Search commits
git log --oneline --grep="keyword" -20

# Contributor ranking
git shortlog -sn --no-merges | head -20

# Hot files
git log --pretty=format: --name-only --since="3 months ago" | grep -v '^$' | sort | uniq -c | sort -rn | head -20
```

## Output Examples

### Search Commits

```
[search] Searching commit messages: "fix bug"

Commit Hash | Date       | Author    | Message
--------------------------------------------------------------------------------
a1b2c3d | 2025-12-06 | Zhang San | fix: resolve bug in auth module
e4f5g6h | 2025-12-05 | Li Si | fix: bug in payment flow

[ok] Found 2 matching records (showing max 20)
```

### Hot Files

```
[hot] Hot Files (last 3 months)

Modifications | File Path
--------------------------------------------------------------------------------
      48 | src/main.js
      32 | package.json
      28 | README.md

[ok] Total 120 files modified (showing top 20)
```

## Detailed Documentation

See [SKILL.md](./SKILL.md) for complete usage instructions and advanced features.

## Dependencies

- Python 3.6+
- Git 2.0+

## License

MIT
