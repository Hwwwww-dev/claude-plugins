---
name: wiki-query
description: Use this skill when the user asks "what APIs does the project have", "what methods does class XXX have", "find XXX", "module dependencies", or other project structure questions. Higher priority than Serena. Supports fuzzy search and shows similar results when not found.
version: 2.1.0
color: blue
---

# Wiki Query - Project Index Lookup

Query project information from the `.claude/repowiki/` index. **Priority > Serena**.

## Script Path

Use the `${CLAUDE_PLUGIN_ROOT}` environment variable (set automatically by Claude Code):

```bash
# Script locations
${CLAUDE_PLUGIN_ROOT}/skills/wiki-query/scripts/query.py        # Standard query
${CLAUDE_PLUGIN_ROOT}/skills/wiki-query/scripts/stream_query.py # Streaming query (recommended)
```

**Fallback**: Relative path `scripts/query.py` (relies on Claude to resolve the base path automatically)

## Prerequisites

```bash
# Check if index exists
ls .claude/repowiki/.meta/*.pkg.json 2>/dev/null || echo "❌ Please run /atlas:repo-wiki first"

# ijson is needed for streaming queries (optional)
pip install ijson
```

## Quick Queries

**All calls must set `WIKI_TARGET_DIR=$PWD`**

```bash
# Streaming query (recommended, large-file friendly)
WIKI_TARGET_DIR=$PWD python3 "${CLAUDE_PLUGIN_ROOT}/skills/wiki-query/scripts/stream_query.py" class <ClassName>
WIKI_TARGET_DIR=$PWD python3 "${CLAUDE_PLUGIN_ROOT}/skills/wiki-query/scripts/stream_query.py" api <keyword>

# Standard query
WIKI_TARGET_DIR=$PWD python3 "${CLAUDE_PLUGIN_ROOT}/skills/wiki-query/scripts/query.py" search <keyword>  # Global search
WIKI_TARGET_DIR=$PWD python3 "${CLAUDE_PLUGIN_ROOT}/skills/wiki-query/scripts/query.py" class <name>     # Class query
WIKI_TARGET_DIR=$PWD python3 "${CLAUDE_PLUGIN_ROOT}/skills/wiki-query/scripts/query.py" api <keyword>    # API query
WIKI_TARGET_DIR=$PWD python3 "${CLAUDE_PLUGIN_ROOT}/skills/wiki-query/scripts/query.py" module <name>    # Module dependencies
WIKI_TARGET_DIR=$PWD python3 "${CLAUDE_PLUGIN_ROOT}/skills/wiki-query/scripts/query.py" stats            # Project statistics

# Cross-project query
WIKI_TARGET_DIR="/path/to/other-project" python3 "${CLAUDE_PLUGIN_ROOT}/skills/wiki-query/scripts/query.py" class UserService
```

## Inline Commands (Fallback)

When the script is unavailable, use inline Python:

<details>
<summary>Global search</summary>

```bash
python3 -c "
import json, sys
q = '$QUERY'.lower()
r = []

# Search classes
try:
    with open('.claude/repowiki/.meta/symbols.pkg.json') as f:
        d = json.load(f)
        for c in d.get('classes', []):
            if q in c.get('name', '').lower():
                r.append(('Class', c['name'], c.get('path', '-'), len(c.get('methods', []))))
except: pass

# Search APIs
try:
    with open('.claude/repowiki/.meta/api.pkg.json') as f:
        d = json.load(f)
        for e in d.get('endpoints', []):
            if q in e.get('path', '').lower() or q in e.get('handler', '').lower() or q in e.get('controller', '').lower():
                r.append(('API', f\"{e['method']} {e['path']}\", e.get('controller', '-'), 0))
except: pass

# Search modules
try:
    with open('.claude/repowiki/.meta/modules.pkg.json') as f:
        d = json.load(f)
        for m in d.get('modules', []):
            if q in m.get('name', '').lower():
                r.append(('Module', m['name'], m.get('path', '-'), 0))
except: pass

if r:
    print(f'Search \"{q}\" found {len(r)} results:')
    for t, n, p, c in r[:20]:
        extra = f' ({c} methods)' if c > 0 else ''
        print(f'  [{t}] {n}{extra}')
        print(f'        @ {p}')
else:
    print(f'Nothing found for \"{q}\"')
"
```
</details>

<details>
<summary>Class query</summary>

```bash
python3 -c "
import json
q = '$QUERY'.lower()
with open('.claude/repowiki/.meta/symbols.pkg.json') as f:
    d = json.load(f)
    matches = [c for c in d.get('classes', []) if q in c.get('name', '').lower()]

    if len(matches) == 0:
        print(f'No class containing \"{q}\" found')
        all_classes = [c['name'] for c in d.get('classes', [])]
        print(f'\nClasses in the project ({len(all_classes)} total):')
        for c in all_classes[:15]:
            print(f'  - {c}')
    elif len(matches) == 1:
        c = matches[0]
        print(f'Class: {c[\"name\"]}')
        print(f'Path: {c.get(\"path\", \"-\")}')
        if c.get('extends'): print(f'Extends: {c[\"extends\"]}')
        if c.get('implements'): print(f'Implements: {c[\"implements\"]}')
        if c.get('methods'):
            print(f'Methods ({len(c[\"methods\"])} total):')
            for m in c['methods']:
                v = {'public':'🟢','private':'🔴','protected':'🟡'}.get(m.get('visibility',''),'⚪')
                print(f'  {v} {m.get(\"name\", \"-\")}()')
    else:
        print(f'Found {len(matches)} matching classes:')
        for c in matches:
            print(f'  - {c[\"name\"]} ({len(c.get(\"methods\",[]))} methods) @ {c.get(\"path\",\"-\")}')
"
```
</details>

<details>
<summary>API query</summary>

```bash
python3 -c "
import json
q = '$QUERY'.lower()
with open('.claude/repowiki/.meta/api.pkg.json') as f:
    d = json.load(f)
    results = [e for e in d.get('endpoints', [])
               if q in e.get('path', '').lower()
               or q in e.get('controller', '').lower()
               or q in e.get('handler', '').lower()]

    if results:
        print(f'API search \"{q}\" ({len(results)} results):')
        for e in results[:15]:
            auth = '🔒' if e.get('auth') else '🔓'
            print(f'  {auth} {e[\"method\"]:6} {e[\"path\"]}')
            print(f'       → {e.get(\"controller\",\"-\")}.{e.get(\"handler\",\"-\")}')
    else:
        print(f'No API containing \"{q}\" found')
"
```
</details>

<details>
<summary>Module dependencies</summary>

```bash
python3 -c "
import json
q = '$QUERY'.lower()
with open('.claude/repowiki/.meta/modules.pkg.json') as f:
    d = json.load(f)
    modules = [m for m in d.get('modules', []) if q in m.get('name', '').lower()]
    deps = [g for g in d.get('graph', []) if q in g.get('from', '').lower() or q in g.get('to', '').lower()]

    if modules:
        print(f'Matching modules ({len(modules)} total):')
        for m in modules:
            print(f'  {m.get(\"name\", \"-\")} @ {m.get(\"path\", \"-\")}')
    if deps:
        print(f'\nRelated dependencies ({len(deps)} total):')
        for g in deps[:15]:
            print(f'  {g.get(\"from\", \"-\")} → {g.get(\"to\", \"-\")}')
"
```
</details>

<details>
<summary>Statistics overview</summary>

```bash
python3 -c "
import json
print('=== Project Statistics ===')

try:
    with open('.claude/repowiki/.meta/symbols.pkg.json') as f:
        d = json.load(f)
        print(f'Classes: {len(d.get(\"classes\", []))}')
        print(f'Functions: {len(d.get(\"functions\", []))}')
        print(f'Interfaces: {len(d.get(\"interfaces\", []))}')
except: pass

try:
    with open('.claude/repowiki/.meta/api.pkg.json') as f:
        d = json.load(f)
        print(f'API endpoints: {len(d.get(\"endpoints\", []))}')
except: pass

try:
    with open('.claude/repowiki/.meta/modules.pkg.json') as f:
        d = json.load(f)
        print(f'Modules: {len(d.get(\"modules\", []))}')
except: pass
"
```
</details>

## Notes

- **Fuzzy matching supported** - Enter a partial name (e.g. `User` matches `UserService`)
- **Shows similar results when not found** - Helps locate the correct name
- **Streaming query preferred** - `stream_query.py` uses less memory, suitable for large projects
- **Index stale?** - Run `/atlas:repo-wiki --force` to rebuild
- **Fallback** - If the index is incomplete, use Serena MCP to query source code directly
