# Dependency Query Skill

Quick dependency query tool - Query project dependency information from index.

## Features

- **Dependency Details** - View version, license, description, and more
- **Security Vulnerability Check** - View known vulnerabilities by severity level
- **Outdated Dependency Detection** - Compare current version with latest version
- **Dependency Tree Display** - View package dependency relationship tree
- **Usage Location Tracking** - Find package reference locations in project
- **Statistics Overview** - Overall dependency health statistics

## Prerequisites

1. Run `/atlas:deps` first to generate the dependency index
2. Index file location: `.claude/.meta/dependencies.pkg.json`

## Usage

### Method 1: Via Skill Call

```bash
# In Claude Code
/skill dep-query

# Then execute query commands as prompted
```

### Method 2: Direct Script Call

```bash
# Set environment variable (optional, defaults to current directory)
export DEPS_TARGET_DIR=/path/to/your/project

# Query dependency details
python3 scripts/query_deps.py pkg lodash

# View all vulnerabilities
python3 scripts/query_deps.py vuln

# View critical vulnerabilities only
python3 scripts/query_deps.py vuln critical

# View outdated dependencies
python3 scripts/query_deps.py outdated

# View dependency tree
python3 scripts/query_deps.py tree react

# View usage locations
python3 scripts/query_deps.py usage axios

# Statistics overview
python3 scripts/query_deps.py stats
```

## Query Command Details

### pkg - Dependency Details

```bash
python3 scripts/query_deps.py pkg <name>
```

Supports fuzzy matching, displays:
- Version information (current/latest)
- Dependency type (production/development)
- License information
- Security vulnerabilities (if any)
- Package description and homepage

**Example Output**:
```
[pkg] Dependency: lodash
   Version: 4.17.20
   Type: dependencies
   Latest: 4.17.21 [outdated]
   License: MIT

[warn] Vulnerabilities (1 found):
   [HIGH] Prototype Pollution
      CVE: CVE-2021-23337
```

### vuln - Vulnerability List

```bash
python3 scripts/query_deps.py vuln [severity]
```

Optional severity filter:
- `critical` - Critical vulnerabilities
- `high` - High severity vulnerabilities
- `moderate` - Moderate severity vulnerabilities
- `low` - Low severity vulnerabilities

**Example Output**:
```
[warn] Found 3 vulnerabilities:

[CRITICAL] Remote Code Execution
   Package: express@4.17.1
   CVE: CVE-2022-24999
   Details: https://...

[HIGH] Prototype Pollution
   Package: lodash@4.17.20
   CVE: CVE-2021-23337
```

### outdated - Outdated Dependencies

```bash
python3 scripts/query_deps.py outdated
```

Lists all dependency packages with versions behind the latest.

**Example Output**:
```
[warn] Found 5 outdated dependencies:

[prod] lodash
   Current: 4.17.20
   Latest: 4.17.21

[dev] jest
   Current: 27.0.0
   Latest: 29.5.0
```

### tree - Dependency Tree

```bash
python3 scripts/query_deps.py tree <name>
```

Displays the direct dependency relationship tree for a package.

**Example Output**:
```
[pkg] react-dom@18.2.0
|-- react
|-- scheduler
--- loose-envify
```

### usage - Usage Locations

```bash
python3 scripts/query_deps.py usage <name>
```

Finds file locations in the project that reference the package.

**Example Output**:
```
[pkg] axios used in:
   1. [file] src/api/client.ts
   2. [file] src/services/user.service.ts
   3. [file] tests/api.test.ts
  ... and 12 more locations
```

### stats - Statistics Overview

```bash
python3 scripts/query_deps.py stats
```

Displays overall health status of project dependencies.

**Example Output**:
```
=== Dependency Statistics ===

[prod] Production dependencies: 45
[dev] Development dependencies: 23
[total] Total: 68

[warn] Outdated dependencies: 5

[security] Security vulnerabilities: 3
   Critical: 1
   High: 2

[size] Largest dependencies:
   webpack: 5.23 MB
   typescript: 3.45 MB
   eslint: 2.17 MB
```

## Data Structure

Expected structure of dependency index file (`dependencies.pkg.json`):

```json
{
  "dependencies": [
    {
      "name": "lodash",
      "version": "4.17.20",
      "latest": "4.17.21",
      "type": "dependencies",
      "description": "Lodash modular utilities.",
      "license": "MIT",
      "homepage": "https://lodash.com/",
      "vulnerabilities": [
        {
          "severity": "high",
          "title": "Prototype Pollution",
          "cve": "CVE-2021-23337",
          "url": "https://..."
        }
      ],
      "size": 1048576
    }
  ],
  "dependency_tree": {
    "react-dom@18.2.0": ["react", "scheduler", "loose-envify"]
  },
  "usage_locations": {
    "axios": ["src/api/client.ts", "src/services/user.service.ts"]
  }
}
```

## Notes

1. **Index outdated** - If dependencies have been updated, re-run `/atlas:deps` to regenerate the index
2. **Fuzzy matching** - All queries support partial name matching (e.g., `react` matches `react-dom`)
3. **Cross-project query** - Use `DEPS_TARGET_DIR` to query dependencies of other projects
4. **Data integrity** - Some features (like dependency tree, usage locations) depend on index completeness

## FAQ

### Q: Getting "dependency index not found"?
A: Run `/atlas:deps` to generate the index.

### Q: Dependency tree or usage locations showing "data unavailable"?
A: Index may be incomplete, re-run `/atlas:deps` ensuring these features are included.

### Q: How to query dependencies of other projects?
A: Set the `DEPS_TARGET_DIR` environment variable to point to the target project directory.

### Q: Which package managers are supported?
A: Depends on the `/atlas:deps` command implementation, typically supports npm/yarn/pnpm (JS) and pip (Python).
