---
description: Code review command. Performs multi-dimensional automated review (security, performance, style, architecture) on specified code scope, with auto-fix support.
argument-hint: [--scope path] [--type security|performance|style|architecture|all] [--fix] [--quick] [--severity critical|warning|all]
---

# /review - Code Review

## 1. Agents and Tools

### 1.1 Agent Description

| Agent | Responsibility | Model | Output Location |
|-------|----------------|-------|-----------------|
| `atlas:information-gatherer` | Collect target code information | haiku | `.claude/gather/review-<ts>/` |
| `atlas:code-reviewer` | Execute single-dimension review | User selected | Returns review result JSON |
| `atlas:atlas-executor` | Execute auto-fix | User selected | Directly modifies files |

### 1.2 Tool Description

| Tool | Purpose |
|------|---------|
| `AskUserQuestion` | Confirm options |
| `Task` | Call subagent |
| `tsc` / `npm test` | Validate results |

### 1.3 Information Flow

```
gatherer → .claude/gather/review-<ts>/context.json
    ↓
code-reviewer → Read context.json → Output review result JSON
    ↓
Main process → Aggregate report → .claude/review/report-<date>.md
    ↓
[--fix] executor → Fix autoFixable issues
```

---

## 2. Orchestration Plan

### 2.1 Mandatory Flow

```
Scope determination → Confirm options → Code analysis → Parallel review → Report aggregation → [--fix] Fix → Test → Output
```

### 2.2 Mode Behavior Definition

| Step | Quick Mode | Default | With --fix | Options |
|------|------------|---------|------------|---------|
| Information gathering | **Skip** | Yes | Yes | Yes / No |
| Review type | User specified | all | all | security / performance / style / architecture / all |
| Severity filter | all | all | all | critical / warning / all |
| Planner | **Skip** | - | Ask | atlas:planner / Built-in Plan |
| Reviewer model | **haiku** | Ask | Ask | haiku / sonnet / opus |
| Executor model | - | - | Ask | haiku / sonnet / opus |
| Test node | **Skip** | - | Ask | After fix / No test |
| Test mode | - | - | Ask | Compile test / Unit test / Compile+Unit |
| State file | **Create** | Create | Create | - |

### 2.3 Review Types

| Type | Check Items |
|------|-------------|
| `security` | SQL injection, XSS, hardcoded keys, sensitive data leakage |
| `performance` | N+1 queries, memory leaks, unnecessary re-renders |
| `style` | Naming conventions, code structure, consistency |
| `architecture` | Layer violations, circular dependencies, coupling |

### 2.4 Execution Mode Selection

**First AskUserQuestion: Execution Mode Selection**

```
Question: Execution mode
- Quick mode: Skip information gathering, review directly (suitable for single file or small scope review, ~3 minutes)
- Standard mode (recommended): Use gatherer to collect information before review
```

### 2.5 Execution Steps

**Step 1: Scope Determination**
- No --scope: git diff (uncommitted changes)
- --scope .: Entire project
- --scope src: Specified directory

**Step 2: Phased Option Confirmation**

**Second AskUserQuestion: Reviewer Model Selection (Standard mode only)**

```
Question: Reviewer model
- haiku: Quick review, suitable for simple checks
- sonnet (recommended): Balance between performance and cost
- opus: Deep review, for complex code with high quality requirements
```

**Second AskUserQuestion: Fix Configuration (Only with --fix)**

If user uses **--fix** parameter, ask for fix configuration:

```
Question 1: Planner selection
- atlas:planner (recommended): Trust gatherer output, minimize scanning
- Built-in Plan: Will explore and validate on its own

Question 2: Executor model
- haiku: Quick simple fixes
- sonnet (recommended): Balance between performance and cost
- opus: Complex fixes with high quality requirements
```

**Third AskUserQuestion: Test Configuration (Only with --fix)**

If user uses **--fix** parameter, ask for test configuration:

```
Question 1: Test node
- After fix (recommended): Test after fix completion
- No test: Skip validation

Question 2: Test mode
- Compile test (recommended): tsc --noEmit to ensure syntax correctness
- Unit test: npm test to ensure functionality
- Compile+Unit: Complete validation
```

**Notes**:
- Quick mode skips all questions and proceeds directly to review flow
- Only standard mode with --fix will ask the third and fourth AskUserQuestion
- If not using --fix, only ask for Reviewer model, then proceed directly to review flow

---

### 2.6 Quick Mode Flow (--quick)

**Applicable Scenarios**:
- Review 1-3 files
- Quick check of specific code snippets

**Flow**:
```
Confirm mode → Main process quick locate → Direct review → Simplified report
```

**Step Q1: Confirm Quick Mode**
```
AskUserQuestion:
Question: Execution mode
- Quick mode ✓
```

**Step Q2: Create State File**
```bash
mkdir -p .claude/orchestrate/.state
echo '{
  "executionId": "<task-id>",
  "timestamp": "<ISO-8601>",
  "task": "<user task>",
  "status": "in_progress",
  "currentStage": "quick_review",
  "config": { "mode": "quick", "reviewerModel": "haiku" }
}' > .claude/orchestrate/.state/<task-id>.json
```

**Step Q3: Main Process Quick Locate**
```
Main process is allowed to use Grep/Glob/Read to quickly locate target files (≤5 tool calls)
Directly build code-reviewer prompt
```

**Step Q4: Direct Review**
```
Task(subagent_type="atlas:code-reviewer", model="haiku")
prompt: |
  Review dimension: [user specified or all]
  Target files: [files located by main process]
  Code snippets: [code read by main process]
  Note: Quick mode, output simplified report
```

**Step Q5: Simplified Report**
```markdown
# Quick Review Complete

**Execution ID**: <task-id>
**State file**: .claude/orchestrate/.state/<task-id>.json
**Scope**: [file list]
**Review type**: [security/performance/style/architecture/all]
**Issues found**: X critical, Y warning

[Issue list]

[If autoFixable exists] Suggestion: Use `/review --fix` for auto-fix
```

**Quick Mode Risk Notes**:
- Skips gatherer, may miss context dependencies
- Does not support --fix (need to switch to standard mode)
- If review fails, suggest user switch to standard mode and re-execute

---

### 2.7 Standard Mode Execution Steps

**Step 3: Code Analysis**
```
Task(subagent_type="atlas:information-gatherer", model="haiku")
prompt: |
  Task ID: review-<timestamp>
  Target files: [file list]
  Output directory: .claude/gather/review-<timestamp>/
```

**Step 4: Parallel Review**
```
Task(subagent_type="atlas:code-reviewer", model=user selected)
prompt: |
  Review dimension: [security/performance/style/architecture]
  Gatherer output: .claude/gather/review-<timestamp>/
```

--type all: Launch 4 code-reviewers in parallel

**Step 5: Report Aggregation**
- Merge results from all dimensions
- Sort by severity
- Output `.claude/review/report-<date>.md`

**Step 6: (--fix) Auto-Fix**
```
Task(subagent_type="atlas:atlas-executor", model=user selected)
prompt: |
  Fix task: Issues with autoFixable=true
  Modification points: [extracted from review results]
```

**Step 7: (--fix) Validation Test** (Execute based on Step 2 selection)

**Step 8: Output Report**

---

## 3. Key Details

### 3.1 Main Process Responsibilities

**Allowed**: AskUserQuestion / Task calls / Read agent output / Aggregate reports

**Prohibited**: Read/Grep/Glob to read code / Edit/Write to modify files / Direct code analysis

### 3.2 Review Result Format

Each code-reviewer outputs:
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

---

## 4. Examples

### Example 1: Quick Review (~3 minutes)

```
User: /review --scope src/api/user.ts --quick
1. AskUserQuestion: Execution mode → User selects "Quick mode"
2. Main process locate: Glob match → Read user.ts (156 lines)
3. Task(code-reviewer, haiku): Review dimension all
4. Review results: security=0, performance=1, style=2, architecture=0
5. Output simplified report → warning: 1 (N+1 query risk L45-52)
6. Suggestion: Use `/review --fix` for auto-fix
```

### Example 2: Standard Review (Multi-dimensional)

```
User: /review --scope src/services --type all
1. AskUserQuestion: Execution mode → User selects "Standard mode"
2. AskUserQuestion: Reviewer model → User selects sonnet
3. Task(gatherer, haiku): Collect 12 files → .claude/gather/review-1704067200/
4. Launch 4 Task(code-reviewer, sonnet) in parallel: security/performance/style/architecture
5. Aggregate results: critical=2, warning=5, info=8
6. Output report → .claude/review/report-2024-01-01.md
7. Key issues: SQL injection(L45), memory leak(L128), circular dependency(services→utils→services)
```

### Example 3: Security Review + Fix

```
User: /review --type security --fix
1. AskUserQuestion: Execution mode → User selects "Standard mode"
2. AskUserQuestion: Reviewer model → opus (deep security review)
3. AskUserQuestion: Planner → atlas:planner / Executor model → sonnet
4. AskUserQuestion: Test configuration → After fix + Compile test
5. Task(gatherer): Collect → Task(code-reviewer, opus): Found 2 critical (autoFixable)
6. Task(executor, sonnet): Fix SQL injection(L45) + XSS vulnerability(L89)
7. Validate: tsc --noEmit ✓ → Output report → critical: 0, fixed: 2
```

---

## 5. Core Constraints

### Standard Mode Must Do

- ✅ Ask for execution mode selection
- ✅ Ask for Reviewer model selection
- ✅ Ask for planner and test options when using --fix
- ✅ Use gatherer to collect code information
- ✅ Review different dimensions in parallel
- ✅ Include file path and line number in issues

### Quick Mode Must Do

- ✅ **Step Q1**: Confirm user selects quick mode
- ✅ **Step Q2**: Create state file at `.claude/orchestrate/.state/<task-id>.json`
- ✅ **Step Q3**: Main process quick locate target files (≤5 tool calls)
- ✅ **Step Q4**: Use `Task(subagent_type="atlas:code-reviewer", model="haiku")`
- ✅ **Step Q5**: Output simplified report (include execution ID and state file path)
- ✅ Suggest user switch to standard mode on failure

### Quick Mode Allowed

- ✅ Main process uses Grep/Glob/Read to quickly locate files (≤5 times)
- ✅ Main process directly builds code-reviewer prompt (without calling gatherer)
- ✅ Skip checkpoints

### Prohibited

- ❌ Main process directly reads code (standard mode)
- ❌ Main process directly modifies files
- ❌ Auto-fix without using --fix
- ❌ Careless autoFixable judgment
- ❌ Quick mode with --fix (need to switch to standard mode)
- ❌ Quick mode for complex reviews (>3 files or requires dependency analysis)
