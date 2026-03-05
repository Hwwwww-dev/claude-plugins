---
name: deps
description: Dependency management. Analyzes project dependencies, detects vulnerabilities, version conflicts, and upgrade suggestions. Supports auto-fix.
version: 1.0.0
color: purple
---

# deps - Dependency Management

User input: $ARGUMENTS

---

## Step 1: Confirm Execution Options

If options are not specified, ask:

**Question 1: Analysis type**
- `security`: Security vulnerability detection (CVE, malicious packages)
- `outdated`: Outdated dependency analysis (version gap, upgrade suggestions)
- `conflicts`: Version conflict detection (peer dependency, duplicate packages)
- `tree`: Dependency tree analysis (depth, package size, redundancy)
- `all`: All analysis types (default recommended)

**Question 2: Analysis scope**
- Project root (default recommended)
- Specific path: e.g. `packages/core`

**Question 3: Fix strategy**
- `report`: Generate report only (default recommended)
- `fix`: Auto-fix resolvable issues
- `interactive`: Interactively select fixes

**Question 4: Upgrade strategy** (only when type includes `outdated`)
- `patch`: Patch versions only (1.0.x, default recommended)
- `minor`: Minor version upgrade (1.x.0)
- `major`: Major version upgrade (x.0.0, may have breaking changes)

**Auto mode** (when `--fix` or full args specified): user args take priority; unspecified defaults to `type=all`, `scope=.`, `upgrade=patch`; fix strategy from `--fix/--interactive`; dev scope from `--no-dev`.

**If user already specified options (e.g. `/deps --type security --fix`), skip related questions.**

---

## Parameters

| Parameter | Description | Default |
|:----------|:------------|:--------|
| `--scope` | Analysis scope (directory/file) | . (project root) |
| `--type` | Analysis type | all |
| `--fix` | Auto-fix resolvable issues | false |
| `--upgrade` | Upgrade strategy (patch/minor/major) | patch |
| `--interactive` | Interactively select fix items | false |
| `--no-dev` | Exclude dev dependencies | false |

---

## Analysis Types

| Type | Checks | Output |
|:-----|:-------|:-------|
| **security** | CVE vulnerabilities, malicious packages, license risk | Vulnerability list, CVSS score, fix suggestions |
| **outdated** | Outdated deps, version gaps, breaking changes | Current/latest versions, upgrade suggestions |
| **conflicts** | Version conflicts, peer dependency, duplicate packages | Conflict list, solutions, dependency tree |
| **tree** | Dependency depth, package size, transitive deps, redundancy | Dep tree, size analysis, optimization suggestions |
| **all** | All of the above | Comprehensive report |

---

## Workflow

Phase 0 Environment Detection → Phase 1 Dependency Scan → Phase 2 Issue Analysis → Phase 3 Report Generation → Phase 4 Auto-fix (optional)

### Subagent Assignment

| Phase | Function | Subagent | Notes |
|:------|:---------|:---------|:------|
| 0 | Environment detection | Main process | Detect package manager, lockfile, config files |
| 1 | Dependency scan | `atlas:dependency-analyzer` | Read dependency manifest, build dep tree |
| 2 | Issue analysis | `atlas:dependency-analyzer` | Run each analysis type in parallel |
| 3 | Report generation | Main process | Merge results, generate unified report |
| 4 | Auto-fix | `atlas:atlas-executor` | Execute auto-fixable issues |

---

## Phase 0: Environment Detection

**Input**: `--scope` parameter

**Output**: Environment config info

| Detection Item | Description |
|:--------------|:------------|
| Package manager | npm/yarn/pnpm/bun (detected via lockfile) |
| Lockfile | package-lock.json / yarn.lock / pnpm-lock.yaml / bun.lockb |
| Config files | package.json / lerna.json / pnpm-workspace.yaml |
| Monorepo | Detect if monorepo structure |
| Node version | Check `engines` field and actual version |

**Steps**:
1. Inspect directory at `--scope`
2. Identify package manager type
3. Read package.json and lockfile
4. Output environment info for subsequent phases

---

## Phase 1: Dependency Scan

**Subagent**: `atlas:dependency-analyzer`

**Input**: Phase 0 environment config

**Output**: `.claude/.meta/dependencies.json`

**Scan items**: dependencies, devDependencies, peerDependencies, optionalDependencies, transitive dependency tree, package metadata (version, license, repository)

**Data schema**:
```json
{
  "manager": "npm",
  "lockfile": "package-lock.json",
  "dependencies": {
    "react": {
      "version": "18.2.0",
      "type": "dependencies",
      "resolved": "...",
      "license": "MIT",
      "transitives": []
    }
  }
}
```

---

## Phase 2: Issue Analysis

**Subagent**: `atlas:dependency-analyzer` (multiple instances in parallel)

**Input**: `.claude/.meta/dependencies.json` + `--type` parameter

**Parallel strategy**:
- `--type all`: Launch 4 analyzers (security, outdated, conflicts, tree)
- `--type security`: Launch 1 analyzer
- Multiple types: launch corresponding number

**Subagent prompt must include**:
1. Analysis dimension (single dimension)
2. Dependency data path
3. Analysis rules (see tables below)
4. Output format requirements

### Analysis Rules

#### Security

| Check | Description | Severity |
|:------|:------------|:---------|
| CVE vulnerabilities | Known security vulnerabilities | critical/high/medium/low |
| Malicious packages | Typosquatting, supply chain attack | critical |
| License risk | GPL, AGPL and other copyleft licenses | warning |
| Deprecated packages | Marked as deprecated | info |
| Maintenance status | No update for >2 years | info |

**Data sources**: npm audit / yarn audit / pnpm audit, OSV (Open Source Vulnerabilities), GitHub Advisory Database

#### Outdated

| Check | Description | Suggestion |
|:------|:------------|:-----------|
| Patch version | 1.0.0 → 1.0.5 | Recommended upgrade |
| Minor version | 1.0.0 → 1.5.0 | Evaluate before upgrading |
| Major version | 1.0.0 → 2.0.0 | Review carefully (breaking changes) |
| Version gap | >10 minor versions behind | Phased upgrade recommended |
| EOL version | e.g. React 16.x (end of support) | Upgrade urgently |

#### Conflicts

| Check | Description | Solution |
|:------|:------------|:---------|
| Version conflict | Multiple packages require different versions | resolutions/overrides |
| Peer dependency | Unsatisfied peer dependencies | Install missing deps |
| Duplicate packages | Multiple versions coexist | dedupe/resolutions |
| Circular dependency | A→B→C→A | Refactor dependency relationships |

#### Tree

| Analysis Item | Description | Optimization |
|:-------------|:------------|:-------------|
| Dependency depth | Max dependency levels | Reduce depth (<5 levels) |
| Package count | Total package count | Remove unused dependencies |
| Package size | node_modules size | Find lighter alternatives |
| Transitive deps | Indirect dependency count | Review necessity |
| Redundant deps | Multiple packages with same function | Unify toolchain |

### Output Format

Each analyzer instance outputs JSON containing:
- `type`: Analysis type
- `timestamp`: Timestamp
- `issues[]`: Issue list (severity, package, version, message, solution, autoFixable)
- `summary`: Stats (critical, warning, info, total)

---

## Phase 3: Report Generation

**Executor**: Main process

**Input**: Phase 2 analysis result JSONs

**Output**: `.claude/deps/report-{date}.md`

**Report template**:
```markdown
# Dependency Analysis Report

Generated: <ISO-8601>
Package manager: <npm|yarn|pnpm|bun> <version>
Scope: <scope>

## Overview
- Total dependencies: X (direct: A, transitive: B)
- Security vulnerabilities: critical/high/medium/low/total
- Outdated: major/minor/patch/total
- Conflicts: N | Depth: D | Size: S

## Critical Issues (by severity)
- [CRITICAL] <pkg>@<version> → <fixedIn> | CVE/CVSS | Command: <cmd> | autoFixable: true/false

## Next Steps
- Fix critical/high first, then minor/major upgrades
- Run install + tests after each fix
```

---

## Phase 4: Auto-fix (Optional)

**Condition**: Only when `--fix` or `--interactive` is specified

**Subagent**: `atlas:atlas-executor`

**Input**: Issues where `autoFixable=true` from Phase 3 report

**Output**: Fixed files + fix report

**Auto-fixable**: Security vulnerability upgrades, outdated deps (per `--upgrade`), dedupe, missing peer installations

**Fix strategies**:

| Issue Type | Fix Method | Command |
|:-----------|:-----------|:--------|
| Security vulnerability | Upgrade to fixed version | `npm install pkg@fixed-version` |
| Outdated dependency | Upgrade per strategy | `npm update pkg` |
| Duplicate packages | Dedupe | `npm dedupe` |
| Peer dependency | Install missing dep | `npm install peer-pkg` |
| Deprecated package | Find replacement | (manual) |

**Fix principles**: Security first, then updates; no cross-major (unless `--upgrade major`); backup `package.json/lockfile` before changes; must run install + tests after fix; log all changes.

---

## Conditional Execution

| Condition | Behavior |
|:----------|:---------|
| No package.json | Prompt: not a valid Node.js project |
| No lockfile | Suggest running `npm install` first |
| Invalid `--scope` path | Error and exit |
| No issues found | Report: dependencies are healthy |
| `--fix` but nothing fixable | Report: no auto-fixable issues |

---

## Package Manager Support

| Manager | Lockfile | Audit Command | Dedupe |
|:--------|:---------|:--------------|:-------|
| npm | package-lock.json | `npm audit` | `npm dedupe` |
| yarn | yarn.lock | `yarn audit` | `yarn dedupe` |
| pnpm | pnpm-lock.yaml | `pnpm audit` | `pnpm dedupe` |
| bun | bun.lockb | `bun audit` | (built-in) |

---

## Constraints

**Execution**:
- ✅ Phase 2: only `atlas:dependency-analyzer`; Phase 4: only `atlas:atlas-executor`
- ✅ Parallel by type (single instance per dimension)

**Analysis/Reporting**:
- ✅ Report only, no fixes (unless `--fix`/`--interactive`)
- ✅ Strict CVSS severity classification
- ✅ Each issue includes command + autoFixable flag
- ✅ Sort by severity

**Fixes**:
- ✅ Backup `package.json/lockfile` before changes
- ❌ Do not cross major version (unless `--upgrade major`)
- ✅ Run install + verify after fix
- ✅ Log all modifications

---

## Notes

- Analysis requires lockfile; ensure `install` has been run
- Security data sourced from npm audit and public databases
- Auto-fix may introduce breaking changes; test first
- Monorepo: analyze each package separately or use `--scope`
- Use the package manager configured in the project
