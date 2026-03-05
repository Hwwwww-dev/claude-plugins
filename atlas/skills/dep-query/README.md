# Dependency Query Skill

Quick dependency lookup tool - query project dependency information from an index.

## Features

- 📦 **Dependency details** - View version, license, description, and more
- 🔒 **Security vulnerability check** - View known vulnerabilities by severity level
- ⚠️  **Outdated dependency detection** - Compare current version against the latest
- 🌳 **Dependency tree** - View the dependency relationship tree for a package
- 📍 **Usage location tracking** - Find where a package is referenced in the project
- 📊 **Statistics overview** - Overall dependency health summary

## Prerequisites

1. Run `/atlas:deps` first to generate the dependency index
2. Index file location: `.claude/.meta/dependencies.pkg.json`

## Usage

### Method 1: Via Skill

```bash
# In Claude Code
/skill dep-query

# Then follow the prompts to run query commands
```

### Method 2: Direct script invocation

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

## Query Commands in Detail

### pkg - Dependency Details

```bash
python3 scripts/query_deps.py pkg <name>
```

Supports fuzzy matching. Displays:
- Version info (current / latest)
- Dependency type (production / dev)
- License info
- Security vulnerabilities (if any)
- Package description and homepage

**Example output**:
```
📦 Dependency: lodash
   Version: 4.17.20
   Type: dependencies
   Latest: 4.17.21 ⚠️  Outdated
   License: MIT

⚠️  Vulnerabilities (1):
   🟠 [HIGH] Prototype Pollution
      CVE: CVE-2021-23337
```

### vuln - Vulnerability List

```bash
python3 scripts/query_deps.py vuln [severity]
```

Optional severity filter:
- `critical` - Critical vulnerabilities
- `high` - High severity vulnerabilities
- `moderate` - Moderate vulnerabilities
- `low` - Low severity vulnerabilities

**Example output**:
```
⚠️  Found 3 vulnerabilities:

🔴 [CRITICAL] Remote Code Execution
   Package: express@4.17.1
   CVE: CVE-2022-24999
   Details: https://...

🟠 [HIGH] Prototype Pollution
   Package: lodash@4.17.20
   CVE: CVE-2021-23337
```

### outdated - Outdated Dependencies

```bash
python3 scripts/query_deps.py outdated
```

Lists all dependencies whose version is behind the latest release.

**Example output**:
```
⚠️  Found 5 outdated dependencies:

📦 lodash
   Current: 4.17.20
   Latest:  4.17.21

🛠️  jest
   Current: 27.0.0
   Latest:  29.5.0
```

### tree - Dependency Tree

```bash
python3 scripts/query_deps.py tree <name>
```

Displays the direct dependency tree for a package.

**Example output**:
```
📦 react-dom@18.2.0
├── react
├── scheduler
└── loose-envify
```

### usage - Usage Locations

```bash
python3 scripts/query_deps.py usage <name>
```

Finds all files in the project that reference the package.

**Example output**:
```
📦 axios used in:
   1. 📄 src/api/client.ts
   2. 📄 src/services/user.service.ts
   3. 📄 tests/api.test.ts
  ... and 12 more locations
```

### stats - Statistics Overview

```bash
python3 scripts/query_deps.py stats
```

Displays the overall health of project dependencies.

**Example output**:
```
=== Dependency Statistics ===

📦 Production dependencies: 45
🛠️  Dev dependencies: 23
📊 Total: 68

⚠️  Outdated: 5

🔒 Security vulnerabilities: 3
   🔴 Critical: 1
   🟠 High: 2

💾 Largest dependencies:
   webpack: 5.23 MB
   typescript: 3.45 MB
   eslint: 2.17 MB
```

## Data Structure

Expected structure of the dependency index file (`dependencies.pkg.json`):

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

1. **Stale index** - If dependencies have been updated, re-run `/atlas:deps` to regenerate the index
2. **Fuzzy matching** - All queries support partial name matching (e.g. `react` matches `react-dom`)
3. **Cross-project queries** - Use `DEPS_TARGET_DIR` to query dependencies in other projects
4. **Data completeness** - Some features (e.g. dependency tree, usage locations) rely on index completeness

## FAQ

### Q: Getting "dependency index not found"?
A: Run `/atlas:deps` to generate the index.

### Q: Dependency tree or usage locations show "data unavailable"?
A: The index may be incomplete. Re-run `/atlas:deps` and ensure those features are included.

### Q: How do I query dependencies for another project?
A: Set the `DEPS_TARGET_DIR` environment variable to point to the target project directory.

### Q: Which package managers are supported?
A: Depends on the `/atlas:deps` command implementation. Typically supports npm/yarn/pnpm (JS) and pip (Python).
