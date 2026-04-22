---
name: bugfix
description: Problem diagnosis and fix suggestion. Analyzes root cause, provides fix options, optionally executes fixes.
version: 1.0.0
color: pink
---

# bugfix - Problem Diagnosis & Fix Skill

## Interaction Rules

- **Localization**: `AskUserQuestion` `header`/`question`/`label`/`description` MUST render in the detected conversation language. JSON below is template — translate user-facing strings before calling.
- **Batch prompts**: One `AskUserQuestion` with multiple `questions[]`. Split only when a later question truly depends on an earlier answer.
- **No redundant Cancel**: Cancellation is implicit. Keep only branches driving different follow-up (e.g. `proceed / revise`, `continue / retry / rollback`).

## Agents

| Agent | Role | Model | Output |
|-------|------|-------|--------|
| `atlas:information-gatherer` | Collect issue-related info | haiku | `.claude/gather/bugfix-<ts>/` |
| `atlas:task-planner` | Produce fix plan | inherit | `.claude/plan/bugfix-<ts>/` |
| `atlas:atlas-executor` | Execute fix | user choice | direct file edits |

## Information Flow

```
gatherer → context.json → task-planner → plan.json → executor (no re-scan)
```

## Mode Comparison

| Step | Quick | Diagnose Only | Execute Fix (interactive) | Auto |
|------|-------|---------------|---------------------------|------|
| Execution strategy | auto | no fix | manual confirm | auto |
| Info gathering | **skip** | ask | ask | yes |
| Diagnosis depth | **skip** | ask | ask | quick |
| Checkpoint | **skip** | - | ask | create |
| Planner | **skip (main)** | ask | ask | atlas:task-planner |
| Executor model | **haiku** | - | ask | sonnet |
| Test node | **none** | - | ask | after-fix |
| Test mode | - | - | ask | compile |
| Failure handling | ask | - | ask | ask |
| State file | **create** | - | create | create |

## Workflow

### Quick Mode (--quick)

**Use when**: 1-3 files, location known, simple syntax/type/typo errors.

1. Confirm mode (auto if `--quick`)
2. Create state file `.claude/bugfix/.state/bugfix-<timestamp>.json`
3. Main process locates via Grep/Glob/Read (≤5 calls), analyzes root cause
4. `Task(atlas:atlas-executor, haiku)` — apply fix
5. Output simplified report

**State file (quick)**:
```json
{
  "executionId": "bugfix-<timestamp>", "timestamp": "<ISO-8601>", "task": "<user task>",
  "status": "in_progress", "currentStage": "quick_bugfix",
  "config": {"mode": "quick", "executorModel": "haiku"}
}
```

**Executor prompt**:
```
Task(atlas:atlas-executor, haiku)
  Subtask #1
  Description: [fix description]
  Files: [located files]
  Problem: [root cause]
  Modifications: [specific changes from main process]
  Note: quick mode — only apply explicitly stated fixes
```

**Simplified report**:
```markdown
# Quick Fix Complete
**Execution ID**: bugfix-<timestamp>
**State file**: .claude/bugfix/.state/bugfix-<timestamp>.json
**Problem**: [description]  **Root cause**: [location]
**Modified files**: [file list]  **Status**: success / failed

[if failed] Suggestion: retry with auto mode `/bugfix <problem> --fix`
```

> Risk: skips deep diagnosis and checkpoint — may miss related issues and cannot rollback.

### Standard Mode

**Step 1: Confirm options (AskUserQuestion)**

- Q1: Mode — Quick / Diagnose Only (recommended) / Execute Fix / Auto
- Q2 (non-quick): Info gathering (yes/no); Planner (atlas:task-planner / built-in Plan); Diagnosis depth (quick / deep / full)
- Q3 (execute-fix / auto): Checkpoint (create/skip); Executor model; Test node; Test mode

**Step 2: Create execution environment** (execute-fix / auto only)

```bash
mkdir -p .claude/bugfix/.state
# write bugfix-<timestamp>.json
git stash push -m "atlas-checkpoint-bugfix-<timestamp>"  # if checkpoint enabled
```

**State file (standard)**:
```json
{
  "executionId": "bugfix-<timestamp>", "timestamp": "<ISO-8601>", "task": "<problem description>",
  "status": "initializing", "currentStage": "initialization",
  "mode": "<diagnose-only/execute-fix/auto>",
  "config": {
    "gatherInfo": "<yes/no>", "planner": "<atlas:task-planner/Plan>",
    "diagnosisDepth": "<quick/deep/full>", "executorModel": "<haiku/sonnet/opus>",
    "testNode": "<after-fix/none>", "testMode": "<compile/unit/both>"
  },
  "checkpoint": {"stashId": "atlas-checkpoint-bugfix-<timestamp>", "created": false},
  "diagnosis": null, "fixApplied": false,
  "iterations": {"planning": 0, "execution": 0},
  "todos": [{"id": 1, "description": "...", "status": "pending"}]
}
```

**Step 3: Info gathering**
```
Task(atlas:information-gatherer, haiku)
  taskId: bugfix-<timestamp>
  problemDescription: [user's problem]
  scope: [--scope value]
  outputDir: .claude/gather/bugfix-<timestamp>/
```
Update state: `currentStage = "gathering_completed"`

**Step 4: Root cause analysis & fix planning** (iterable)

1. `Task(<user planner>)` → `.claude/plan/bugfix-<ts>/plan.json`
2. Display: root cause (file:line), type & complexity, fix strategy/steps/risks
3. Validate `plan.json.completeness` — root cause → fix coverage must be 100%; on gap, list and ask to re-plan
4. `AskUserQuestion` → proceed / revise plan / finish (diagnose-only)
5. On revise: re-run planner with feedback; simple → overwrite `plan.json`; complex → `plan.v2.json`, `plan.v3.json`… loop until confirmed

Update state: `currentStage = "planning_approved"`, `planVersion`, `diagnosis`, `iterations.planning`

**Step 5: Execute fix** (execute-fix / auto; retry loop)

1. `Task(atlas:atlas-executor, <user model>)`
2. Display: modified files, fix status
3. Validate against plan — output completion rate; on incomplete, ask: retry / rollback / save progress
4. `AskUserQuestion` → continue verify / retry / rollback
5. On retry → 5.1

Update state: `currentStage = "fix_applied"`, `fixApplied = true`, `iterations.execution`

**Step 6: Verification** (per Step 1 config)
```bash
# compile: tsc --noEmit
# unit:    npm test
# both:    tsc --noEmit && npm test
```
Update state: `currentStage = "testing_completed"`

**Step 7: Cleanup & report**

Update state: `status = "completed"`, `currentStage = "finished"`, `completedAt`.

## Root Cause Output Format

```markdown
## Problem Diagnosis
**Description**: [user description]  **Type**: [error type]  **Complexity**: simple | moderate | complex

## Root Cause
**Location**: [file:line]  **Cause**: [specific reason]  **Impact**: [affected scope]

## Fix Plan
**Strategy**: [direct fix / defensive fix / refactor]
**Steps**: 1. [step] — [file:location]
**Verification**: [method]  **Risks**: [potential risks]
```

## Directory Structure

```
.claude/
├── gather/bugfix-<ts>/context.json
├── plan/bugfix-<ts>/plan.json [+ plan.v2.json, plan.v3.json optional]
└── bugfix/.state/bugfix-<ts>.json
```

Task ID `bugfix-<timestamp>` (e.g. `bugfix-20240115-143000`) stays consistent across steps.

## Examples

**Quick fix**: `/bugfix Login.tsx line 45 onClick not bound --quick` — main greps onClick, reads context, executor(haiku) adds `this.handleLogin = this.handleLogin.bind(this)` in constructor. ~3 min.

**Auto**: `/bugfix user list API returns undefined --auto` — gatherer locates `api/users.ts` + `hooks/useUsers.ts`, planner finds `response.data.users` should be `response.data.list` at line 28, executor(sonnet) applies fix, compile test passes.

## Constraints

### Standard Mode — MUST
- Step 1 staged confirmation (mode → diagnosis → fix/test)
- Execute-fix / auto: create and continuously update `.claude/bugfix/.state/bugfix-<ts>.json` (`currentStage`)
- Pipeline: gather → plan (`completeness`) → fix (`completionStatus`) → test → report
- Use TodoWrite to track diagnosis/fix tasks

### Quick Mode — MUST
- Create state file; ≤5 tool calls; executor(haiku) applies fix; simplified report

### Quick Mode — ALLOWED
- Main process uses Grep/Glob/Read (≤5 calls)
- Main process analyzes root cause directly (no task-planner)
- Skip info gathering and checkpoint

### FORBIDDEN
- Main process modifies files directly (all changes via executor)
- Standard mode skips info gathering and diagnoses directly (except quick)
- Standard mode skips planning and executes fix directly
- Executor re-scans files (must use plan.json or main-process modification points)
- Additional AskUserQuestion after Step 1 (except Step 4 / 5 confirmation loops)
- Standard mode forgets to update `currentStage`
- Proceeding without user confirmation
- Quick mode for complex problems (>3 files or needs dependency analysis)

**Principle**: main process orchestrates / confirms / summarizes; diagnosis and modifications done by subagents.
