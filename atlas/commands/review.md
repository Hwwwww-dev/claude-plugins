---
description: Code review command. Performs multi-dimensional automated review on specified code scope (security, performance, style, architecture), supports auto-fix.
argument-hint: [--scope path] [--type security|performance|style|architecture|all] [--fix] [--severity critical|warning|all]
---

# Code Review Command

Performs multi-dimensional automated code review, discovers potential issues and provides fix suggestions.

## Parameters

| Parameter | Description | Default |
|:----------|:------------|:--------|
| `--scope` | Review scope (directory/file/git diff) | git diff (uncommitted changes) |
| `--type` | Review type | all |
| `--fix` | Auto-fix fixable issues | false |
| `--severity` | Minimum severity level to report | all |

---

## Review Types

| Type | Description | Check Items |
|:-----|:------------|:------------|
| `security` | Security review | SQL injection, XSS, hardcoded secrets, sensitive data leaks, insecure dependencies |
| `performance` | Performance review | N+1 queries, memory leaks, unnecessary re-renders, excessive complexity |
| `style` | Style review | Naming conventions, code structure, consistency, comment quality |
| `architecture` | Architecture review | Layer violations, circular dependencies, coupling level, module boundaries |
| `all` | Full review | All types above |

---

## Execution Flow

Phase 0 Scope Determination -> Phase 1 Code Analysis -> Phase 2 Parallel Review -> Phase 3 Report Aggregation -> Phase 4 Auto-fix (optional)

### Subagent Assignment

| Phase | Function | Subagent | Description |
|:------|:---------|:---------|:------------|
| 0 | Scope determination | Main process | Parse parameters, determine review scope |
| 1 | Code analysis | `atlas:information-gatherer` | Collect target code information |
| 2 | Parallel review | `atlas:code-reviewer` | Multiple instances review different dimensions in parallel |
| 3 | Report aggregation | Main process | Merge results, generate unified report |
| 4 | Auto-fix | `atlas:atlas-executor` | Execute auto-fixable issues |

---

## Phase 0: Scope Determination

**Input**: Command parameters

**Output**: Review target list

**Scope determination rules**:
| Scenario | Scope |
|:---------|:------|
| No --scope | git diff (uncommitted change files) |
| --scope . | Entire project (exclude node_modules, .git, etc.) |
| --scope src | Specified directory |
| --scope src/user.ts | Specified file |

**Operations**:
1. Parse --scope parameter
2. If not specified, get git diff changed file list
3. Filter non-code files
4. Output target file list

---

## Project Knowledge Base

**Prioritize getting project info from `.claude/repowiki/`** (if exists):

| File | Purpose |
|:-----|:--------|
| `.claude/repowiki/.meta/modules.pkg.json` | Module structure, dependency relationships (for architecture review) |
| `.claude/repowiki/.meta/api.pkg.json` | API endpoint information (for security review) |
| `.claude/repowiki/.meta/symbols.pkg.json` | Symbol index (accelerate code location) |

**Usage**: Check if these files exist before Phase 1 analysis, prioritize using existing information.

---

## Phase 1: Code Analysis

**Subagent**: `atlas:information-gatherer`

**Input**: Phase 0 target file list + `.claude/repowiki/` existing info (if exists)

**Output**: `.claude/review/.meta/targets.pkg.json` (contains file path, language, line count, symbols, imports/exports, statistics)

---

## Phase 2: Parallel Review

**Subagent**: `atlas:code-reviewer` (multiple instances in parallel)

**Input**:
- `.claude/review/.meta/targets.pkg.json`
- Review type (--type parameter)

**Output**: Review result JSON for each dimension

**Parallel Strategy**:
- --type all: Start 4 code-reviewers (security, performance, style, architecture)
- --type security: Start 1 code-reviewer
- Multiple types: Start corresponding number for specified types

**Subagent Prompt must include**:
1. Review dimension (single dimension)
2. Target file path list
3. Review rules reference (see rules table below)
4. Output format requirements

### Review Rules

#### Security

| Rule ID | Check Item | Severity |
|:--------|:-----------|:---------|
| SEC001 | SQL injection | critical |
| SEC002 | XSS vulnerability | critical |
| SEC003 | Hardcoded secrets | critical |
| SEC004 | Sensitive info logging | warning |
| SEC005 | Insecure random numbers | info |
| SEC006 | eval/Function usage | warning |
| SEC007 | Path traversal | critical |
| SEC008 | CORS configuration | warning |

#### Performance

| Rule ID | Check Item | Severity |
|:--------|:-----------|:---------|
| PERF001 | N+1 queries | warning |
| PERF002 | Unoptimized loops | info |
| PERF003 | Memory leak risk | warning |
| PERF004 | Unnecessary re-renders | info |
| PERF005 | Synchronous blocking | warning |
| PERF006 | Regex backtracking | warning |
| PERF007 | Large object copies | info |

#### Style

| Rule ID | Check Item | Severity |
|:--------|:-----------|:---------|
| STYLE001 | Function too long | warning |
| STYLE002 | Nesting too deep | warning |
| STYLE003 | Non-standard naming | info |
| STYLE004 | Magic numbers | info |
| STYLE005 | Duplicate code | warning |
| STYLE006 | TODO/FIXME | info |
| STYLE007 | Dead code | info |
| STYLE008 | Too many parameters | info |

#### Architecture

| Rule ID | Check Item | Severity |
|:--------|:-----------|:---------|
| ARCH001 | Circular dependencies | warning |
| ARCH002 | Layer violations | warning |
| ARCH003 | Module boundaries | info |
| ARCH004 | High coupling | info |
| ARCH005 | Missing abstraction | info |
| ARCH006 | Singleton abuse | info |

### Output Format

Each code-reviewer instance outputs JSON containing:
- `dimension`: Review dimension
- `timestamp`: Timestamp
- `issues[]`: Issue list (ruleId, severity, file, line, column, code, message, suggestion, autoFixable, fixedCode)
- `summary`: Statistics (critical, warning, info, total)

---

## Phase 3: Report Aggregation

**Executor**: Main process

**Input**: Phase 2 review result JSON for each dimension

**Output**: `.claude/review/report-{date}.md`

**Report Contains**:
- Overview (review scope, types, total issues, critical issues, warnings, info)
- Issue distribution (by dimension and severity)
- Critical issue details (file, code, suggestion, auto-fixable or not)
- Warning and info issue list
- Fix suggestions (grouped by auto-fix and manual fix)

---

## Phase 4: Auto-fix (Optional)

**Condition**: Only execute when --fix parameter exists

**Subagent**: `atlas:atlas-executor`

**Input**: Phase 3 report issues list where autoFixable=true

**Output**: Fixed files + fix report

**Execution Strategy**:
1. Group by file, one subtask per file
2. Execute subtasks in parallel
3. Each fix maintains original code style

**Fix Principles**:
- Only fix issues where autoFixable=true
- Maintain code format consistency
- Don't introduce new issues
- Verify syntax correctness after fix

**Fix Report** contains: Fix statistics, fix details, follow-up suggestions

---

## Conditional Execution

| Condition | Behavior |
|:----------|:---------|
| No changed files | Prompt no review needed, exit |
| Target files >100 | Suggest using --scope to narrow scope |
| --fix but no fixable issues | Report no auto-fixable issues |
| Review type has no issues | Report that dimension passed |

---

## Constraints

**Execution Constraints**:
- Phase 2 must use `atlas:code-reviewer` agent
- Phase 4 must use `atlas:atlas-executor` agent
- Different review dimensions must execute in parallel
- Each code-reviewer only handles single dimension

**Review Constraints**:
- Only report issues, don't fix without permission (unless --fix)
- Strictly judge severity by rules
- Provide actionable fix suggestions
- autoFixable must be carefully determined

**Report Constraints**:
- Issues must include file path and line number
- Must provide code snippet context
- Must sort by severity
- Must indicate if auto-fixable

---

## Examples

### Basic Usage
```bash
# Review uncommitted changes
/atlas:review

# Review specified directory
/atlas:review --scope src/services

# Security review only
/atlas:review --type security

# Review and auto-fix
/atlas:review --fix

# Show critical issues only
/atlas:review --severity critical
```
