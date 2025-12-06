---
name: dep-query
description: Quick dependency query. Query dependency versions, vulnerabilities, usage locations, update history, etc. Supports fuzzy search.
version: 1.0.0
color: orange
---

# Dependency Query - Quick Dependency Lookup

Query project dependency information from the `.claude/.meta/dependencies.pkg.json` index.

## Script Path

Use the `${CLAUDE_PLUGIN_ROOT}` environment variable (automatically set by Claude Code):

```bash
# Script location
${CLAUDE_PLUGIN_ROOT}/skills/dep-query/scripts/query_deps.py
```

**Alternative**: Relative path `scripts/query_deps.py` (depends on Claude auto-resolving base path)

## Prerequisites

```bash
# Check if dependency index exists
ls .claude/.meta/dependencies.pkg.json 2>/dev/null || echo "Please run /atlas:deps first"
```

## Query Types

| Command | Description | Example |
|---------|-------------|---------|
| `pkg <name>` | Query dependency details | dep-query pkg lodash |
| `vuln [severity]` | List vulnerabilities | dep-query vuln critical |
| `outdated` | Outdated dependencies | dep-query outdated |
| `tree <name>` | Dependency tree | dep-query tree react |
| `usage <name>` | Usage locations | dep-query usage axios |
| `stats` | Statistics overview | dep-query stats |

## Quick Queries

**All calls must set `DEPS_TARGET_DIR=$PWD`**

```bash
# Dependency details
DEPS_TARGET_DIR=$PWD python3 "${CLAUDE_PLUGIN_ROOT}/skills/dep-query/scripts/query_deps.py" pkg <name>

# Vulnerability query
DEPS_TARGET_DIR=$PWD python3 "${CLAUDE_PLUGIN_ROOT}/skills/dep-query/scripts/query_deps.py" vuln          # All vulnerabilities
DEPS_TARGET_DIR=$PWD python3 "${CLAUDE_PLUGIN_ROOT}/skills/dep-query/scripts/query_deps.py" vuln critical # Critical only

# Outdated dependencies
DEPS_TARGET_DIR=$PWD python3 "${CLAUDE_PLUGIN_ROOT}/skills/dep-query/scripts/query_deps.py" outdated

# Dependency tree
DEPS_TARGET_DIR=$PWD python3 "${CLAUDE_PLUGIN_ROOT}/skills/dep-query/scripts/query_deps.py" tree <name>

# Usage locations
DEPS_TARGET_DIR=$PWD python3 "${CLAUDE_PLUGIN_ROOT}/skills/dep-query/scripts/query_deps.py" usage <name>

# Statistics overview
DEPS_TARGET_DIR=$PWD python3 "${CLAUDE_PLUGIN_ROOT}/skills/dep-query/scripts/query_deps.py" stats

# Cross-project query
DEPS_TARGET_DIR="/path/to/other-project" python3 "${CLAUDE_PLUGIN_ROOT}/skills/dep-query/scripts/query_deps.py" pkg express
```

## Inline Commands (Fallback)

When the script is unavailable, you can use inline Python:

<details>
<summary>Dependency Details Query</summary>

```bash
python3 -c "
import json, sys
pkg_name = '$QUERY'.lower()

try:
    with open('.claude/.meta/dependencies.pkg.json') as f:
        data = json.load(f)
        deps = data.get('dependencies', [])

        # Fuzzy match
        matches = [d for d in deps if pkg_name in d.get('name', '').lower()]

        if not matches:
            print(f'No dependencies found containing \"{pkg_name}\"')
            print(f'\\nProject dependencies ({len(deps)} total):')
            for d in deps[:15]:
                print(f'  - {d.get(\"name\", \"-\")} @ {d.get(\"version\", \"-\")}')
        elif len(matches) == 1:
            d = matches[0]
            print(f'Dependency: {d.get(\"name\", \"-\")}')
            print(f'Version: {d.get(\"version\", \"-\")}')
            print(f'Type: {d.get(\"type\", \"-\")}')  # dependencies/devDependencies
            if d.get('latest'):
                print(f'Latest: {d[\"latest\"]}')
            if d.get('description'):
                print(f'Description: {d[\"description\"]}')
            if d.get('license'):
                print(f'License: {d[\"license\"]}')
            if d.get('vulnerabilities'):
                vulns = d['vulnerabilities']
                print(f'Vulnerabilities: {len(vulns)} found')
                for v in vulns:
                    print(f'  [{v.get(\"severity\",\"unknown\").upper()}] {v.get(\"title\",\"-\")}')
        else:
            print(f'Found {len(matches)} matching dependencies:')
            for d in matches:
                vuln_count = len(d.get('vulnerabilities', []))
                vuln_mark = f' {vuln_count} vulns' if vuln_count > 0 else ''
                print(f'  - {d.get(\"name\", \"-\")} @ {d.get(\"version\", \"-\")}{vuln_mark}')
except FileNotFoundError:
    print('Dependency index not found, please run /atlas:deps first')
except Exception as e:
    print(f'Query failed: {e}')
"
```
</details>

<details>
<summary>Vulnerability List</summary>

```bash
python3 -c "
import json
severity_filter = '$SEVERITY'.lower() if '$SEVERITY' else None

try:
    with open('.claude/.meta/dependencies.pkg.json') as f:
        data = json.load(f)
        deps = data.get('dependencies', [])

        # Collect all vulnerabilities
        all_vulns = []
        for d in deps:
            for v in d.get('vulnerabilities', []):
                all_vulns.append({
                    'package': d.get('name', '-'),
                    'version': d.get('version', '-'),
                    'severity': v.get('severity', 'unknown'),
                    'title': v.get('title', '-'),
                    'cve': v.get('cve', '-')
                })

        # Filter by severity
        if severity_filter:
            all_vulns = [v for v in all_vulns if v['severity'].lower() == severity_filter]

        if not all_vulns:
            msg = f' ({severity_filter})' if severity_filter else ''
            print(f'No vulnerabilities found{msg}')
        else:
            # Sort by severity
            severity_order = {'critical': 0, 'high': 1, 'moderate': 2, 'low': 3, 'unknown': 4}
            all_vulns.sort(key=lambda x: severity_order.get(x['severity'].lower(), 5))

            print(f'Found {len(all_vulns)} vulnerabilities:')
            for v in all_vulns:
                icon = {'critical':'[CRITICAL]','high':'[HIGH]','moderate':'[MODERATE]','low':'[LOW]'}.get(v['severity'].lower(),'[UNKNOWN]')
                print(f'\\n{icon} {v[\"title\"]}')
                print(f'   Package: {v[\"package\"]}@{v[\"version\"]}')
                if v['cve'] != '-':
                    print(f'   CVE: {v[\"cve\"]}')
except FileNotFoundError:
    print('Dependency index not found, please run /atlas:deps first')
except Exception as e:
    print(f'Query failed: {e}')
"
```
</details>

<details>
<summary>Outdated Dependencies</summary>

```bash
python3 -c "
import json

try:
    with open('.claude/.meta/dependencies.pkg.json') as f:
        data = json.load(f)
        deps = data.get('dependencies', [])

        # Find outdated dependencies
        outdated = []
        for d in deps:
            current = d.get('version', '')
            latest = d.get('latest', '')
            if latest and current != latest:
                outdated.append({
                    'name': d.get('name', '-'),
                    'current': current,
                    'latest': latest,
                    'type': d.get('type', '-')
                })

        if not outdated:
            print('All dependencies are up to date!')
        else:
            print(f'Found {len(outdated)} outdated dependencies:')
            for d in outdated:
                type_mark = '[prod]' if d['type'] == 'dependencies' else '[dev]'
                print(f'  {type_mark} {d[\"name\"]}')
                print(f'      Current: {d[\"current\"]}')
                print(f'      Latest: {d[\"latest\"]}')
except FileNotFoundError:
    print('Dependency index not found, please run /atlas:deps first')
except Exception as e:
    print(f'Query failed: {e}')
"
```
</details>

<details>
<summary>Dependency Tree</summary>

```bash
python3 -c "
import json
pkg_name = '$QUERY'.lower()

try:
    with open('.claude/.meta/dependencies.pkg.json') as f:
        data = json.load(f)
        tree = data.get('dependency_tree', {})

        # Find package dependency tree
        matches = {k: v for k, v in tree.items() if pkg_name in k.lower()}

        if not matches:
            print(f'No dependency tree found for \"{pkg_name}\"')
        else:
            for pkg, children in matches.items():
                print(f'{pkg}')
                if children:
                    for i, child in enumerate(children):
                        is_last = i == len(children) - 1
                        prefix = '--- ' if is_last else '|-- '
                        print(f'{prefix}{child}')
                else:
                    print('  (no dependencies)')
except FileNotFoundError:
    print('Dependency index not found, please run /atlas:deps first')
except KeyError:
    print('Dependency tree data incomplete, please re-run /atlas:deps')
except Exception as e:
    print(f'Query failed: {e}')
"
```
</details>

<details>
<summary>Usage Locations</summary>

```bash
python3 -c "
import json
pkg_name = '$QUERY'.lower()

try:
    with open('.claude/.meta/dependencies.pkg.json') as f:
        data = json.load(f)
        usage = data.get('usage_locations', {})

        # Find package usage locations
        matches = {k: v for k, v in usage.items() if pkg_name in k.lower()}

        if not matches:
            print(f'No usage locations found for \"{pkg_name}\"')
        else:
            for pkg, locations in matches.items():
                print(f'{pkg} used in:')
                if locations:
                    for loc in locations[:20]:  # Limit display count
                        print(f'  [file] {loc}')
                    if len(locations) > 20:
                        print(f'  ... and {len(locations) - 20} more locations')
                else:
                    print('  (no direct references detected)')
except FileNotFoundError:
    print('Dependency index not found, please run /atlas:deps first')
except KeyError:
    print('Usage location data incomplete, please re-run /atlas:deps')
except Exception as e:
    print(f'Query failed: {e}')
"
```
</details>

<details>
<summary>Statistics Overview</summary>

```bash
python3 -c "
import json

try:
    with open('.claude/.meta/dependencies.pkg.json') as f:
        data = json.load(f)

        deps = data.get('dependencies', [])
        prod_deps = [d for d in deps if d.get('type') == 'dependencies']
        dev_deps = [d for d in deps if d.get('type') == 'devDependencies']

        # Count vulnerabilities
        vuln_count = sum(len(d.get('vulnerabilities', [])) for d in deps)
        critical = sum(1 for d in deps for v in d.get('vulnerabilities', []) if v.get('severity') == 'critical')
        high = sum(1 for d in deps for v in d.get('vulnerabilities', []) if v.get('severity') == 'high')

        # Count outdated
        outdated = sum(1 for d in deps if d.get('latest') and d.get('version') != d.get('latest'))

        print('=== Dependency Statistics ===')
        print(f'Production dependencies: {len(prod_deps)}')
        print(f'Development dependencies: {len(dev_deps)}')
        print(f'Total: {len(deps)}')
        print(f'\\nOutdated dependencies: {outdated}')
        print(f'\\nSecurity vulnerabilities: {vuln_count}')
        if critical > 0:
            print(f'  Critical: {critical}')
        if high > 0:
            print(f'  High: {high}')

        # Largest packages (if size info available)
        if any(d.get('size') for d in deps):
            largest = sorted([d for d in deps if d.get('size')],
                           key=lambda x: x.get('size', 0), reverse=True)[:5]
            print(f'\\nLargest dependencies:')
            for d in largest:
                size_mb = d.get('size', 0) / 1024 / 1024
                print(f'  {d.get(\"name\", \"-\")}: {size_mb:.2f} MB')
except FileNotFoundError:
    print('Dependency index not found, please run /atlas:deps first')
except Exception as e:
    print(f'Query failed: {e}')
"
```
</details>

## Notes

- **Fuzzy matching supported** - Enter partial names (e.g., `react` matches `react-dom`, `react-router`, etc.)
- **Index outdated?** - Run `/atlas:deps` to regenerate the index
- **Data source** - All data comes from `.claude/.meta/dependencies.pkg.json`
- **Vulnerability severity levels** - critical > high > moderate > low
- **Fallback** - When index doesn't exist, read directly from `package.json` or `requirements.txt`
