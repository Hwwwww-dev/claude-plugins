---
name: orchestrate
description: Task orchestration & parallel execution engine. Handles complex multi-step tasks, batch operations, project-wide changes. Supports rollback and resume.
version: 1.0.0
color: blue
---

# orchestrate - Task Orchestration Engine

## Interaction Rules

- **Localization**: All `AskUserQuestion` `header`/`question`/`label`/`description` strings MUST be rendered in the detected system/conversation language. Never hardcode English — the JSON examples below are structural templates; translate every user-facing string before calling the tool.
- **Batch prompts**: Prefer a single `AskUserQuestion` call with multiple `questions[]` over sequential calls. Only split when a later question genuinely depends on the earlier answer. (Steps 1 / 1b / 1c SHOULD be merged into one call whenever the later steps apply.)
- **No redundant Cancel**: Confirmation prompts MUST NOT add an explicit `Cancel` option — cancellation is implicit. Keep only branches that drive different follow-up behavior (e.g. `proceed / revise`, `continue / retry / rollback`).

## Agents & Tools

### Agents

| Agent | Role | Model | Output |
|-------|------|-------|--------|
| `atlas:information-gatherer` | Collect project info (structure, deps, code snippets) | haiku | `.claude/gather/<task-id>/` |
| `atlas:task-planner` | Generate execution plan from gatherer output | inherit | `.claude/plan/<task-id>/` |
| `atlas:atlas-executor` | Execute individual subtasks | user-selected | direct file edits |

### Tools

| Tool | Purpose |
|------|---------|
| `AskUserQuestion` | Confirm options with user |
| `Task` | Invoke subagents |
| `git stash` | Create/restore checkpoints |

### Data Pipeline

```
gatherer → .claude/gather/<task-id>/context.json
    ↓
task-planner → reads context.json → .claude/plan/<task-id>/plan.json
    ↓
main process → reads plan.json → embeds into executor prompt
    ↓
executor → edits files directly (no re-scanning)
```

**Core principle**: task-planner outputs precise modification points; executor executes directly.

---

## Mode Comparison

| Step | Quick | Auto | Interactive | dry-run |
|------|-------|------|-------------|---------|
| Execution strategy | auto | auto | ask user | auto |
| Info gathering | **skip** | yes (unless repowiki sufficient) | ask user | yes |
| Checkpoint | **skip** | create | ask user | skip |
| Planner | **main process plans directly** | atlas:task-planner | ask user | atlas:task-planner |
| Executor model | **haiku** | sonnet | ask user | - |
| Testing | **none** | unified | ask user | - |
| Test mode | - | compile | ask user | - |
| Failure handling | ask user | ask user | ask user | - |
| State file | create | create | create | create |

---

## Workflow

### Step 1: Mode Selection (AskUserQuestion #1)

Ask the user to choose execution mode:
- **Quick**: Skip gathering/planning, direct execution (1-3 files, clear target)
- **Auto** (recommended): Use recommended options, minimal interaction
- **Interactive**: Confirm each key step
- **dry-run**: Plan only, no execution

If `--quick` flag is provided, skip to Quick Mode flow.

### Step 1b: Base Config (AskUserQuestion #2 — Interactive/dry-run only)

If user chose **Interactive** or **dry-run**, ask:

```
Q1: Info gathering — yes (recommended) / no (skip if repowiki sufficient)
Q2: Checkpoint — create (recommended) / skip (dry-run defaults to skip)
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

**Use case**: 1-3 files, clear target, no dependency analysis needed.

**Flow**: Confirm mode → Create state file → Locate files (≤5 tool calls) → Execute → Update state → Report

**State file init**:
```json
{
  "executionId": "<task-id>",
  "timestamp": "<ISO-8601>",
  "task": "<user task>",
  "status": "in_progress",
  "currentStage": "quick_mode",
  "config": {"mode": "quick", "executorModel": "haiku"},
  "subtasks": [],
  "progress": {"total": 1, "completed": 0, "failed": 0, "pending": 1}
}
```

Path: `.claude/orchestrate/.state/<task-id>.json`

**Execution**: Main process uses Grep/Glob/Read (≤5 calls) to locate files, then:
```
Task(subagent_type="atlas:atlas-executor", model="haiku")
prompt: |
  Subtask #1
  Description: [user task]
  Files: [located files]
  Modifications: [identified changes]
  Note: Quick mode — only make explicitly mentioned changes
```

**Risk**: No dependency analysis or checkpoint. If failed, retry with auto mode.

---

## Standard Mode Flow

### Step 2: Create Execution Environment

```bash
mkdir -p .claude/orchestrate/.state
```

State file schema:
```json
{
  "executionId": "<task-id>",
  "timestamp": "<ISO-8601>",
  "task": "<user task>",
  "status": "initializing",
  "currentStage": "initialization",
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

Create checkpoint (non-dry-run): `git stash push -m "atlas-checkpoint-{execution-id}"`

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

### Step 4: Task Planning (supports iteration)

1. **4.1 Run planner**: `Task(subagent_type="<selected planner>")` → `.claude/plan/<task-id>/plan.json`
2. **4.2 Show plan to user**: Display subtask list, execution strategy, impact scope
3. **4.2.5 Completeness check**: Verify `plan.json.completeness`: `coverage=100%`, `uncovered=[]`, all validations true. If failed, ask user whether to re-plan.
4. **4.3 User confirmation** (AskUserQuestion): Proceed / Revise plan / Cancel
5. **4.4 Re-plan** (if user requests): Use same planner with feedback. Simple: overwrite `plan.json`; complex: generate `plan.v2.json`, `plan.v3.json`... Loop back to 4.2.

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

### Step 5: Task Execution (supports iteration)

1. **5.1 Launch executors in parallel**: `Task(subagent_type="atlas:atlas-executor", model=<selected>)` — one per subtask
2. **5.2 Collect results**: Track success/failure per subtask
3. **5.2.5 Completeness verification**: Compare `plan.json` against executor `completionStatus`. Show completion rate + incomplete items.
4. **5.3 Show results**: X succeeded / Y failed (with reasons) / modified files list
5. **5.4 User decision** (AskUserQuestion): Proceed to testing / Retry failed / Adjust / Rollback
6. **5.5 Re-execute** (if user requests): Loop back to 5.1 for failed subtasks only

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
| per-task | Run after each executor completes |
| unified | Run once after all executors finish |
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

**Task ID format**: `<action>-<date>-<time>` (e.g. `add-types-20240115-103000`)

```
.claude/
├── gather/<task-id>/
│   └── context.json
├── plan/<task-id>/
│   ├── plan.json
│   ├── plan.v1.json  (optional)
│   └── plan.v2.json  (optional)
└── orchestrate/.state/
    └── <task-id>.json
```

**Data requirements**:
- `context.json.codeSnippets`: Key code snippets with line numbers
- `plan.json.subtasks[].modifications`: Precise line-level change points
- Executor prompt must embed modifications from plan.json — no additional file scanning

**File conflict resolution** (parallel executors):
1. Group modifications to the same file under one executor
2. Serialize tasks that cannot be separated
3. Phase execution: complete shared dependencies first, then parallelize

---

## Resume / Rollback

**Resume**: `/orchestrate --resume <task-id>`

Read state file → locate stage via `currentStage` → skip completed steps → reuse original config

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

## Task
[description]

## Execution ID
task-20240115-103000

## Config
- Mode: [auto/interactive/dry-run]
- Planner: [atlas:task-planner/Plan]
- Executor model: [haiku/sonnet/opus]
- Test node: [unified/per-task/none]
- Test mode: [compile/unit/both]

## Stats
- Subtasks: X total
- Success: Y / Failed: Z
- Planning iterations: N
- Execution iterations: M

## Modified Files
- file1.ts (lines 45-60)
- file2.ts (line 120)

## Failures (if any)
- Subtask #N: [reason] → [fixed/pending]

## State File
- Path: `.claude/orchestrate/.state/task-20240115-103000.json`
- Final status: completed | finished

## Checkpoint
- Status: cleaned / available for rollback
- Stash ID: atlas-checkpoint-{execution-id}
- Restore: `git stash list` → `git stash apply stash@{N}`

## Resume
- Command: `/orchestrate --resume task-20240115-103000`
```

---

## Constraints

### Standard Mode — MUST do
- ✅ Confirm all config in Step 1 (mode/planner/model/testing) in one go
- ✅ Create and continuously update state file (`currentStage`, `subtasks/progress`)
- ✅ Create checkpoint (non-quick, non-dry-run); follow: gather → plan → execute → test → report
- ✅ Plan must pass completeness check; execution must reconcile against `completionStatus`

### Quick Mode — MUST do
- ✅ Create state file; main process ≤5 tool calls to locate files; use executor(haiku); update state and output brief report

### Quick Mode — ALLOWED
- ✅ Main process uses Grep/Glob/Read to locate files (≤5 calls)
- ✅ Main process generates simple modification plan without calling task-planner
- ✅ Skip info gathering and checkpoint

### FORBIDDEN
- ❌ Main process directly modifies files (all edits must go through executor)
- ❌ Standard mode skips info gathering and plans directly (unless --no-gather or quick mode)
- ❌ Standard mode skips planning and executes directly
- ❌ Executor re-scans files (must use modifications from plan.json)
- ❌ Additional AskUserQuestion after Step 1 (except Steps 4.3 and 5.4 confirmation loops)
- ❌ Standard mode fails to update `currentStage` in state file
- ❌ Proceeding without user confirmation
- ❌ Quick mode for complex tasks (>3 files or requires dependency analysis)

**Principle**: Delegate everything possible to subagents. Main process only orchestrates, confirms, reads artifacts, and summarizes reports.
