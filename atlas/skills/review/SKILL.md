---
name: review
description: Multi-dimensional code review. Analyzes security, performance, style, and architecture. Supports auto-fix and parallel review agents.
version: 1.0.0
color: orange
---

# review - Code Review Skill

## Interaction Rules

- **Localization**: Render all `AskUserQuestion` `header`/`question`/`label`/`description` strings in the detected system language. JSON below is structural — translate user-facing strings before calling.
- **Batch prompts**: Prefer one `AskUserQuestion` with multiple `questions[]`. Split only when a later question depends on an earlier answer.
- **No redundant Cancel**: Cancellation is implicit. Keep only branches that drive different follow-up behavior.

## Agents

| Agent | Role | Model | Output |
|-------|------|-------|--------|
| `atlas:information-gatherer` | Collect target code info | haiku | `.claude/gather/review-<ts>/` |
| `atlas:code-reviewer` | Single-dimension review | user choice | review result JSON |
| `atlas:atlas-executor` | Auto-fix | user choice | modifies files directly |

## Information Flow

```
gatherer → .claude/gather/review-<ts>/context.json
    ↓
code-reviewer → reads context.json → outputs review JSON
    ↓
main process → aggregate report → .claude/review/report-<date>.md
    ↓
[--fix] executor → fix autoFixable issues
```

## Review Types

| Type | Checks |
|------|--------|
| `security` | SQL injection, XSS, hardcoded secrets, sensitive data leakage |
| `performance` | N+1 queries, memory leaks, unnecessary re-renders |
| `style` | Naming conventions, code structure, consistency |
| `architecture` | Layer violations, circular dependencies, coupling |

## Mode Comparison

| Step | Quick Mode | Default | With --fix | Options |
|------|-----------|---------|------------|---------|
| Info gathering | **skip** | yes | yes | yes / no |
| Review type | user-specified | all | all | security / performance / style / architecture / all |
| Severity filter | all | all | all | critical / warning / all |
| Planner | **skip** | - | ask | atlas:task-planner / built-in Plan |
| Reviewer model | **haiku** | ask | ask | haiku / sonnet / opus |
| Executor model | - | - | ask | haiku / sonnet / opus |
| Test node | **skip** | - | ask | after-fix / none |
| Test mode | - | - | ask | compile / unit / compile+unit |
| State file | **create** | create | create | - |

## Workflow

### Quick Mode (--quick)

**Use when**: reviewing 1-3 files or a specific snippet.

1. Confirm mode (or auto-select with `--quick`)
2. Create state file at `.claude/orchestrate/.state/<task-id>.json`
3. Main process locates files via Grep/Glob/Read (max 5 calls)
4. `Task(atlas:code-reviewer, haiku)` with specified dimensions
5. Output simplified report

**State file schema (quick)**:
```json
{
  "executionId": "<task-id>",
  "timestamp": "<ISO-8601>",
  "task": "<user task>",
  "status": "in_progress",
  "currentStage": "quick_review",
  "config": {"mode": "quick", "reviewerModel": "haiku"}
}
```

**Simplified report**:
```markdown
# Quick Review Complete

**Execution ID**: <task-id>
**State file**: .claude/orchestrate/.state/<task-id>.json
**Scope**: [file list]
**Review type**: [security/performance/style/architecture/all]
**Issues found**: X critical, Y warning

[issue list]

[if autoFixable issues exist] Suggestion: use `/review --fix` to auto-fix
```

> Risk: skips gatherer, may miss context dependencies. `--fix` not supported in quick mode.

### Standard Mode

**Step 1: Scope**
- No `--scope`: git diff (uncommitted changes)
- `--scope .`: entire project
- `--scope src`: specified directory

**Step 2: Confirm options (AskUserQuestion)**

- Q1: Mode — Quick / Standard (recommended)
- Q2 (standard only): Reviewer model — haiku / sonnet (recommended) / opus
- Q3 (--fix only): Planner — `atlas:task-planner` (recommended) / built-in Plan; Executor model
- Q4 (--fix only): Test node — after-fix (recommended) / none; Test mode — compile / unit / compile+unit

**Step 3: Info gathering**
```
Task(atlas:information-gatherer, haiku)
  taskId: review-<timestamp>
  targetFiles: [file list]
  outputDir: .claude/gather/review-<timestamp>/
```

**Step 4: Parallel review**
```
Task(atlas:code-reviewer, <user model>)
  dimension: [security / performance / style / architecture]
  gathererOutput: .claude/gather/review-<timestamp>/
```
With `--type all`: launch 4 code-reviewers in parallel.

**Step 5: Aggregate report**
- Merge all dimensions, sort by severity
- Output to `.claude/review/report-<date>.md`

**Step 6: (--fix) Auto-fix**
```
Task(atlas:atlas-executor, <user model>)
  fixTasks: issues where autoFixable=true
  modifications: [extracted from review results]
```

**Step 7: (--fix) Verification** — run tests per Step 2 config

**Step 8: Output final report**

## Review Result Schema

Each `code-reviewer` outputs:
```json
{
  "dimension": "security",
  "issues": [
    {
      "ruleId": "SEC001",
      "severity": "critical",
      "file": "src/api.ts",
      "line": 45,
      "message": "SQL injection risk",
      "suggestion": "Use parameterized queries",
      "autoFixable": true,
      "fixedCode": "..."
    }
  ],
  "summary": {"critical": 1, "warning": 2, "info": 0}
}
```

## Examples

**Quick review**: `/review --scope src/api/user.ts --quick` — main process locates file, single code-reviewer (haiku), simplified report in ~3 min.

**Security review + fix**: `/review --type security --fix` — gatherer → code-reviewer (opus) → executor (sonnet) fixes autoFixable issues → compile test.

## Constraints

### Standard Mode — Must Do

- Confirm mode and reviewer model; confirm planner/test config for `--fix`
- gatherer → parallel reviewer(s) → aggregate report
- Issues must include file path and line; mark `autoFixable` with care

### Quick Mode — Must Do

- Create state file; main process max 5 tool calls; reviewer(haiku); simplified report

### Quick Mode — Allowed

- Main process uses Grep/Glob/Read to locate files (max 5 calls)
- Main process builds code-reviewer prompt directly (no gatherer)
- Skip checkpoints

### Forbidden

- Main process reads code directly (standard mode)
- Main process modifies files directly
- Auto-fix without `--fix` flag
- Marking `autoFixable` carelessly
- `--fix` in quick mode (requires standard mode)
- Quick mode for complex reviews (>3 files or dependency analysis needed)
