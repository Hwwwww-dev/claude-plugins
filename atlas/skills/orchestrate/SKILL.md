---
name: orchestrate
description: Task orchestration & parallel execution engine. Handles complex multi-step tasks, batch operations, project-wide changes. Supports rollback and resume.
version: 1.0.0
color: blue
---

# orchestrate - Task Orchestration Engine

## Interaction Rules

- **Localization**: `AskUserQuestion` `header`/`question`/`label`/`description` MUST render in the detected conversation language. JSON below is template — translate user-facing strings before calling.
- **Batch prompts**: One `AskUserQuestion` with multiple `questions[]`. Split only when a later question truly depends on an earlier answer. (Merge Steps 1 / 1b / 1c whenever applicable.)
- **No redundant Cancel**: Cancellation is implicit. Keep only branches driving different follow-up (e.g. `proceed / revise`, `continue / retry / rollback`).

## Agents & Tools

| Agent | Role | Model | Output |
|-------|------|-------|--------|
| `atlas:information-gatherer` | Collect project info (structure, deps, snippets) | haiku | `.claude/gather/<task-id>/` |
| `atlas:task-planner` | Generate execution plan from gatherer output | inherit | `.claude/plan/<task-id>/` |
| `atlas:atlas-executor` | Execute individual subtasks | user-selected | direct file edits |

Tools: `AskUserQuestion` (confirm) · `Task` (invoke subagents) · `git stash` (checkpoints)

### Data Pipeline

```
gatherer → context.json → task-planner → plan.json → main → executor → file edits
```

**Core principle**: task-planner outputs precise modification points; executor executes directly (no re-scan).

---

## Mode Comparison

| Step | Quick | Auto | Interactive | dry-run |
|------|-------|------|-------------|---------|
| Execution strategy | auto | auto | ask | auto |
| Info gathering | **skip** | yes (unless repowiki sufficient) | ask | yes |
| Checkpoint | **skip** | create | ask | skip |
| Planner | **main (direct)** | atlas:task-planner | ask | atlas:task-planner |
| Executor model | **haiku** | sonnet | ask | - |
| Testing | **none** | unified | ask | - |
| Test mode | - | compile | ask | - |
| Failure handling | ask | ask | ask | - |
| State file | create | create | create | create |

---

## Workflow

### Step 1: Mode Selection (AskUserQuestion #1)

- **Quick**: Skip gathering/planning, direct execution (1-3 files, clear target)
- **Auto** (recommended): Recommended options, minimal interaction
- **Interactive**: Confirm each key step
- **dry-run**: Plan only, no execution

`--quick` flag → skip to Quick Mode.

### Step 1b: Base Config (AskUserQuestion #2 — Interactive/dry-run only)

```
Q1: Info gathering — yes (recommended) / no (skip if repowiki sufficient)
Q2: Checkpoint — create (recommended) / skip (dry-run defaults skip)
Q3: Planner — atlas:task-planner (recommended) / built-in Plan
Q4: Executor model — sonnet (recommended) / haiku / opus
```

### Step 1c: Test Config (AskUserQuestion #3 — Auto/Interactive only)

```
Q1: Test node — unified after all (recommended) / after each subtask / none
Q2: Test mode — compile: tsc --noEmit / unit: npm test / both
```

---

## Quick Mode Flow (--quick)

**Use case**: 1-3 files, clear target, no dependency analysis.

**Flow**: Confirm mode → Create state file → Locate files (≤5 calls) → Execute → Update state → Report

**State file** at `.claude/orchestrate/.state/<task-id>.json`:
```json
{
  "executionId": "<task-id>", "timestamp": "<ISO-8601>", "task": "<user task>",
  "status": "in_progress", "currentStage": "quick_mode",
  "config": {"mode": "quick", "executorModel": "haiku"},
  "subtasks": [],
  "progress": {"total": 1, "completed": 0, "failed": 0, "pending": 1}
}
```

**Execution** — main process uses Grep/Glob/Read (≤5 calls) to locate, then:
```
Task(subagent_type="atlas:atlas-executor", model="haiku")
prompt: |
  Subtask #1
  Description: [user task]
  Files: [located files]
  Modifications: [identified changes]
  Note: Quick mode — only make explicitly mentioned changes
```

**Risk**: No dependency analysis or checkpoint. On failure, retry with auto mode.

---

## Standard Mode Flow

### Step 2: Create Execution Environment

```bash
mkdir -p .claude/orchestrate/.state
```

State file schema:
```json
{
  "executionId": "<task-id>", "timestamp": "<ISO-8601>", "task": "<user task>",
  "status": "initializing", "currentStage": "initialization",
  "config": {
    "mode": "<auto|interactive|dry-run>",
    "task-planner": "<atlas:task-planner|Plan>",
    "executorModel": "<haiku|sonnet|opus>",
    "testNode": "<unified|per-task|none>",
    "testMode": "<compile|unit|both>"
  },
  "checkpoint": {"stashId": "atlas-checkpoint-<task-id>", "created": false},
  "subtasks": [],
  "progress": {"total": 0, "completed": 0, "failed": 0, "pending": 0},
  "iterations": {"planning": 0, "execution": 0}
}
```

Checkpoint (non-dry-run): `git stash push -m "atlas-checkpoint-{execution-id}"`

### Step 3: Information Gathering

```
Task(subagent_type="atlas:information-gatherer", model="haiku")
prompt: |
  Task ID: <task-id>
  Task description: [user task]
  Collection target: [scope and focus]
  Output dir: .claude/gather/<task-id>/
```

Update state: `currentStage = "gathering_completed"`

### Step 4: Task Planning (iterable)

1. **4.1 Run planner** → `.claude/plan/<task-id>/plan.json`
2. **4.2 Show plan**: Subtask list, execution strategy, impact scope
3. **4.2.5 Completeness**: `plan.json.completeness` must have `coverage=100%`, `uncovered=[]`, all validations true. On fail, ask user to re-plan.
4. **4.3 Confirm** (AskUserQuestion): Proceed / Revise plan / Cancel
5. **4.4 Re-plan** (on request): Same planner with feedback. Simple → overwrite `plan.json`; complex → `plan.v2.json`, `plan.v3.json`… → back to 4.2.

Update state after approval:
```json
{
  "currentStage": "planning_approved",
  "planVersion": "final",
  "subtasks": [{"id": 1, "status": "pending", "description": "...", "files": ["..."]}],
  "progress": {"total": N, "completed": 0, "failed": 0, "pending": N},
  "iterations": {"planning": <count>}
}
```

### Step 5: Task Execution (iterable)

1. **5.1 Launch executors in parallel**: `Task(atlas:atlas-executor, model=<selected>)` — one per subtask
2. **5.2 Collect results** per subtask
3. **5.2.5 Verify**: Compare `plan.json` against executor `completionStatus`. Show completion rate + incomplete items.
4. **5.3 Display**: X succeeded / Y failed (reasons) / modified files
5. **5.4 Decision** (AskUserQuestion): Proceed to testing / Retry failed / Adjust / Rollback
6. **5.5 Re-execute** (on request): → 5.1 for failed subtasks only

Update state after execution:
```json
{
  "currentStage": "execution_completed",
  "subtasks": [{"id": 1, "status": "completed|failed"}],
  "progress": {"total": N, "completed": X, "failed": Y, "pending": 0},
  "iterations": {"execution": <count>}
}
```

### Step 6: Verification Testing

| Test node | Timing |
|-----------|--------|
| per-task | After each executor |
| unified | Once after all executors |
| none | Skip |

| Test mode | Command |
|-----------|---------|
| compile | `tsc --noEmit` |
| unit | `npm test` |
| both | `tsc --noEmit && npm test` |

Update state: `currentStage = "testing_completed"`

### Step 7: Cleanup & Report

Update final state:
```json
{
  "status": "completed",
  "currentStage": "finished",
  "completedAt": "<ISO-8601>",
  "checkpoint": {"stashId": "...", "created": true, "cleaned": true}
}
```

---

## File Structure

**Task ID**: `<action>-<date>-<time>` (e.g. `add-types-20240115-103000`)

```
.claude/
├── gather/<task-id>/context.json
├── plan/<task-id>/plan.json [+ plan.v2.json, plan.v3.json optional]
└── orchestrate/.state/<task-id>.json
```

**Data requirements**:
- `context.json.codeSnippets`: Key snippets with line numbers
- `plan.json.subtasks[].modifications`: Precise line-level change points
- Executor prompt embeds modifications from plan.json — no re-scanning

**File conflict resolution** (parallel executors):
1. Group same-file modifications under one executor
2. Serialize inseparable tasks
3. Phase: shared dependencies first, then parallelize

---

## Resume / Rollback

**Resume**: `/orchestrate --resume <task-id>` — read state → locate via `currentStage` → skip completed → reuse config

**Stage mapping**:
```
initialization      → Step 2
checkpoint_created  → Step 3
gathering_completed → Step 4
planning_approved   → Step 5
execution_completed → Step 6
testing_completed   → Report
finished            → Done
```

**Failure handling**:
- `--auto-rollback`: `git stash pop` automatically
- Manual: Ask user — Rollback / Skip / Retry / Abort

---

## Output Format

### Quick Mode Report
```markdown
# Quick Execution Complete
**Task**: [description]
**Modified files**: [file list]
**Status**: success / failed

[If failed]
**Reason**: [reason]
**Suggestion**: Retry with auto mode: `/orchestrate <task>`
```

### Standard Mode Report
```markdown
# Atlas Execution Report

## Task / Execution ID
[description] / task-20240115-103000

## Config
Mode / Planner / Executor model / Test node / Test mode

## Stats
Subtasks: X total · Success Y / Failed Z · Planning iterations N · Execution iterations M

## Modified Files
- file1.ts (lines 45-60)
- file2.ts (line 120)

## Failures (if any)
- Subtask #N: [reason] → [fixed/pending]

## State File
Path: `.claude/orchestrate/.state/task-20240115-103000.json` · Final: completed | finished

## Checkpoint
Status: cleaned / available for rollback · Stash ID: atlas-checkpoint-{execution-id}
Restore: `git stash list` → `git stash apply stash@{N}`

## Resume
`/orchestrate --resume task-20240115-103000`
```

---

## Constraints

### Standard Mode — MUST
- Confirm all config in Step 1 (mode/planner/model/testing) in one go
- Create and continuously update state file (`currentStage`, `subtasks/progress`)
- Create checkpoint (non-quick, non-dry-run); pipeline: gather → plan → execute → test → report
- Plan passes completeness check; execution reconciles against `completionStatus`

### Quick Mode — MUST
- Create state file; ≤5 tool calls to locate; executor(haiku); update state; output brief report

### Quick Mode — ALLOWED
- Main process uses Grep/Glob/Read (≤5 calls)
- Main process generates simple plan without task-planner
- Skip info gathering and checkpoint

### FORBIDDEN
- Main process directly modifies files (all edits via executor)
- Standard mode skips info gathering and plans directly (unless --no-gather or quick)
- Standard mode skips planning and executes directly
- Executor re-scans files (must use plan.json modifications)
- Additional AskUserQuestion after Step 1 (except Steps 4.3 / 5.4 confirmation loops)
- Standard mode fails to update `currentStage`
- Proceeding without user confirmation
- Quick mode for complex tasks (>3 files or needs dependency analysis)

**Principle**: Delegate to subagents. Main process only orchestrates, confirms, reads artifacts, and summarizes.
