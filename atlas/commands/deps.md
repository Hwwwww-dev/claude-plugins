---
description: Dependency management command. Analyzes project dependencies, detects security vulnerabilities, version conflicts, and upgrade suggestions, supports auto-fix.
argument-hint: [--scope path] [--type security|outdated|conflicts|tree|all] [--fix] [--upgrade major|minor|patch]
---

# /deps - Dependency Management

User input: $ARGUMENTS

---

## Step 1: Confirm Execution Options

**If user doesn't specify options, use AskUserQuestion to ask:**

```
Question 1: Analysis type
- security: Security vulnerability detection (CVE, malicious packages)
- outdated: Outdated dependency analysis (version gap, update suggestions)
- conflicts: Version conflict detection (peer dependency, duplicate packages)
- tree: Dependency tree analysis (depth, package size, redundancy)
- all: All analysis (default)

Question 2: Analysis scope
- Default: Project root directory
- Specified: Enter path (e.g., packages/core)

Question 3: Fix strategy
- report: Generate report only (default)
- fix: Auto-fix fixable issues
- interactive: Interactive fix selection

Question 4: Upgrade strategy (outdated type only)
- patch: Patch version (1.0.x)
- minor: Minor version (1.x.0)
- major: Major version (x.0.0)
```

**If user has specified (e.g., `/deps --type security --fix`), skip asking.**

---

## Parameters

| Parameter | Description | Default |
|:----------|:------------|:--------|
| `--scope` | Analysis scope (directory/file) | . (project root) |
| `--type` | Analysis type | all |
| `--fix` | Auto-fix fixable issues | false |
| `--upgrade` | Upgrade strategy (patch/minor/major) | patch |
| `--interactive` | Interactive fix selection | false |
| `--no-dev` | Exclude dev dependencies | false |

---

## Analysis Types

| Type | Check Content | Output |
|:-----|:--------------|:-------|
| **security** | CVE vulnerabilities, malicious packages, license risks | Vulnerability list, CVSS scores, fix suggestions |
| **outdated** | Outdated dependencies, version gaps, breaking changes | Current version, latest version, upgrade suggestions |
| **conflicts** | Version conflicts, peer dependencies, duplicate packages | Conflict list, solutions, dependency tree |
| **tree** | Dependency depth, package size, transitive dependencies, redundancy | Dependency tree, size analysis, optimization suggestions |
| **all** | All types above | Comprehensive report |

---

## Execution Flow

Phase 0 Environment Detection -> Phase 1 Dependency Scan -> Phase 2 Problem Analysis -> Phase 3 Report Generation -> Phase 4 Auto-fix (optional)

### Subagent Assignment

| Phase | Function | Subagent | Description |
|:------|:---------|:---------|:------------|
| 0 | Environment detection | Main process | Detect package manager, lockfile, config files |
| 1 | Dependency scan | `atlas:dependency-analyzer` | Read dependency list, build dependency tree |
| 2 | Problem analysis | `atlas:dependency-analyzer` | Execute various type analyses in parallel |
| 3 | Report generation | Main process | Merge results, generate unified report |
| 4 | Auto-fix | `atlas:atlas-executor` | Execute auto-fixable issues |

---

## Phase 0: Environment Detection

**Input**: --scope parameter

**Output**: Environment configuration info

**Detection Content**:

| Detection Item | Description |
|:---------------|:------------|
| Package manager | npm/yarn/pnpm/bun (detect lockfile) |
| Lockfile | package-lock.json/yarn.lock/pnpm-lock.yaml/bun.lockb |
| Config files | package.json/lerna.json/pnpm-workspace.yaml |
| Monorepo | Detect if monorepo structure |
| Node version | Detect engines field and actual version |

**Operations**:
1. Detect directory specified by --scope
2. Identify package manager type
3. Read package.json and lockfile
4. Output environment info for subsequent phases

---

## Phase 1: Dependency Scan

**Subagent**: `atlas:dependency-analyzer`

**Input**: Phase 0 environment configuration

**Output**: `.claude/.meta/dependencies.json`

**Scan Content**:
- dependencies: Production dependencies
- devDependencies: Development dependencies
- peerDependencies: Peer dependencies
- optionalDependencies: Optional dependencies
- Transitive dependency tree
- Package metadata (version, license, repository)

**Data Structure**:
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
      "transitives": [...]
    }
  }
}
```

---

## Phase 2: Problem Analysis

**Subagent**: `atlas:dependency-analyzer` (multiple instances in parallel)

**Input**:
- `.claude/.meta/dependencies.json`
- Analysis type (--type parameter)

**Output**: Analysis result JSON for each type

**Parallel Strategy**:
- --type all: Start 4 analyzers (security, outdated, conflicts, tree)
- --type security: Start 1 analyzer
- Multiple types: Start corresponding number for specified types

**Subagent Prompt must include**:
1. Analysis dimension (single dimension)
2. Dependency data path
3. Analysis rules reference (see rules table below)
4. Output format requirements

### Analysis Rules

#### Security

| Check Item | Description | Severity |
|:-----------|:------------|:---------|
| CVE vulnerabilities | Known security vulnerabilities | critical/high/medium/low |
| Malicious packages | Typosquatting, supply chain attack | critical |
| License risks | GPL, AGPL and other copyleft licenses | warning |
| Deprecated packages | deprecated flag | info |
| Maintenance status | Not updated for >2 years | info |

**Data Sources**:
- npm audit / yarn audit / pnpm audit
- OSV (Open Source Vulnerabilities)
- GitHub Advisory Database

#### Outdated

| Check Item | Description | Suggestion |
|:-----------|:------------|:-----------|
| Patch version | 1.0.0 -> 1.0.5 | Recommended upgrade |
| Minor version | 1.0.0 -> 1.5.0 | Evaluate before upgrade |
| Major version | 1.0.0 -> 2.0.0 | Careful evaluation (breaking changes) |
| Version gap | Behind >10 minor versions | Staged upgrade recommended |
| EOL version | React 16.x (no longer supported) | Upgrade ASAP |

#### Conflicts

| Check Item | Description | Solution |
|:-----------|:------------|:---------|
| Version conflict | Multiple packages require different versions | resolutions/overrides |
| Peer Dependency | Unmet peer dependencies | Install missing dependencies |
| Duplicate packages | Multiple versions coexist | dedupe/resolutions |
| Circular dependency | A->B->C->A | Refactor dependency relationships |

#### Tree (Dependency Tree)

| Analysis Item | Description | Optimization Suggestion |
|:--------------|:------------|:------------------------|
| Dependency depth | Maximum dependency level | Reduce depth (<5 levels) |
| Package count | Total package count | Remove unused dependencies |
| Package size | node_modules size | Find lighter alternatives |
| Transitive dependencies | Indirect dependency count | Review necessity |
| Redundant dependencies | Multiple packages providing same functionality | Unify toolchain |

### Output Format

Each analyzer instance outputs JSON containing:
- `type`: Analysis type
- `timestamp`: Timestamp
- `issues[]`: Issue list (contains severity, package, version, message, solution, autoFixable)
- `summary`: Statistics (critical, warning, info, total)

---

## Phase 3: Report Generation

**Executor**: Main process

**Input**: Phase 2 analysis result JSON for each type

**Output**: `.claude/deps/report-{date}.md`

**Report Contains**:
- Overview (package manager, total dependencies, detected issues)
- Security report (vulnerability list, CVSS scores, affected packages, fix commands)
- Outdated report (current version, latest version, version gap, upgrade suggestions)
- Conflict report (conflict list, involved packages, solutions)
- Dependency tree analysis (depth, size, optimization suggestions)
- Fix suggestions (grouped by auto-fix and manual fix)

**Report Example**:

```markdown
# Dependency Analysis Report

Generated: 2024-01-15 10:30:00
Package Manager: npm 10.2.0
Analysis Scope: /Users/project

## Overview

- Total dependencies: 347 (direct: 42, transitive: 305)
- Security vulnerabilities: 3 (critical: 1, high: 2)
- Outdated dependencies: 12 (major: 3, minor: 9)
- Version conflicts: 2
- node_modules size: 245 MB

## Security Vulnerabilities (3)

### [CVE-2024-1234] axios <1.6.0 - SSRF Vulnerability

- **Severity**: Critical (CVSS 9.1)
- **Current version**: 1.4.0
- **Fixed version**: >=1.6.0
- **Impact scope**: Direct dependency
- **Fix command**: `npm install axios@^1.6.0`
- **Auto-fixable**: Yes

...

## Recommendations

1. Prioritize fixing critical security vulnerabilities
2. Use `npm dedupe` to eliminate duplicate dependencies
3. Consider replacing moment.js with date-fns (reduce package size)
```

---

## Phase 4: Auto-fix (Optional)

**Condition**: Only execute when --fix or --interactive parameter exists

**Subagent**: `atlas:atlas-executor`

**Input**: Phase 3 report issues list where autoFixable=true

**Output**: Fixed files + fix report

**Auto-fixable Issues**:
- Security vulnerabilities (version upgrade)
- Outdated dependencies (upgrade per --upgrade strategy)
- Duplicate packages (dedupe)
- Missing peer dependencies (install)

**Fix Strategy**:

| Issue Type | Fix Method | Command |
|:-----------|:-----------|:--------|
| Security vulnerability | Upgrade to fixed version | `npm install pkg@fixed-version` |
| Outdated dependency | Upgrade per strategy | `npm update pkg` |
| Duplicate packages | dedupe | `npm dedupe` |
| Peer Dependency | Install missing dependency | `npm install peer-pkg` |
| Deprecated package | Find alternative | (manual) |

**Interactive Mode** (--interactive):
```
Found 5 auto-fixable issues:

1. [CRITICAL] axios 1.4.0 -> 1.6.0 (fix CVE-2024-1234)
2. [WARNING] lodash 4.17.15 -> 4.17.21 (security update)
3. [INFO] react 18.2.0 -> 18.3.0 (feature update)
4. [INFO] Duplicate: webpack 5.88.0 and 5.90.0
5. [WARNING] Missing peer: react-dom@^18.0.0

Select items to fix (space to select, Enter to confirm):
[x] 1. axios upgrade
[x] 2. lodash upgrade
[ ] 3. react upgrade
[x] 4. webpack dedupe
[x] 5. Install react-dom
```

**Fix Principles**:
- Prioritize security vulnerability fixes
- Control version span per --upgrade strategy
- Maintain lockfile consistency
- Run install after fix to update lockfile
- Don't auto-fix breaking changes (requires manual evaluation)

**Fix Report** contains: Fix statistics, fix details, follow-up suggestions

---

## Conditional Execution

| Condition | Behavior |
|:----------|:---------|
| No package.json | Prompt not a valid Node.js project |
| No lockfile | Suggest running `npm install` first to generate lockfile |
| --scope path invalid | Error and exit |
| No issues detected | Report dependency health is good |
| --fix but no fixable items | Report no auto-fixable issues |

---

## Constraints

**Execution Constraints**:
- Phase 2 must use `atlas:dependency-analyzer` agent
- Phase 4 must use `atlas:atlas-executor` agent
- Different analysis types must execute in parallel
- Each analyzer only handles single type

**Analysis Constraints**:
- Only report issues, don't fix without permission (unless --fix)
- Strictly judge vulnerability severity by CVSS scores
- Provide actionable fix commands
- autoFixable must be carefully determined

**Fix Constraints**:
- Backup package.json and lockfile before fix
- Verify dependencies installable after fix
- Don't cross major versions (unless --upgrade major)
- Record all modification operations

**Report Constraints**:
- Issues must include package name, version, severity
- Must provide fix commands
- Must sort by severity
- Must indicate if auto-fixable

---

## Examples

### Basic Usage

```bash
# Full dependency analysis
/deps

# Security check only
/deps --type security

# Check outdated dependencies
/deps --type outdated

# Check and auto-fix
/deps --fix

# Interactive fix
/deps --interactive

# Specify scope
/deps --scope packages/core
```

### Advanced Usage

```bash
# Security check and auto-fix
/deps --type security --fix

# Upgrade minor versions
/deps --type outdated --upgrade minor --fix

# Exclude dev dependencies
/deps --no-dev

# Dependency tree analysis
/deps --type tree

# Monorepo specific package
/deps --scope packages/api --type security
```

### Integration with Other Commands

```bash
# Workflow example
/deps --type security              # 1. Detect security issues
/deps --type security --fix        # 2. Auto-fix
npm test                           # 3. Run tests to verify
/atlas:review --scope package.json # 4. Review changes
```

---

## Supported Package Managers

| Package Manager | Lockfile | Audit Command | Dedupe |
|:----------------|:---------|:--------------|:-------|
| npm | package-lock.json | `npm audit` | `npm dedupe` |
| yarn | yarn.lock | `yarn audit` | `yarn dedupe` |
| pnpm | pnpm-lock.yaml | `pnpm audit` | `pnpm dedupe` |
| bun | bun.lockb | `bun audit` | (built-in) |

---

## Notes

- Analysis requires reading lockfile, ensure install has been run
- Security vulnerability data comes from npm audit and public databases
- Auto-fix may introduce breaking changes, suggest testing first
- Monorepo needs to analyze each package separately or use --scope
- Prefer using project-configured package manager
