---
name: refactor
description: Intelligent refactoring. Identifies code issues and executes pattern-based automated refactoring. Supports preview and interactive confirmation.
version: 1.0.0
color: orange
---

# refactor - Intelligent Refactoring Skill

## Interaction Rules

- **Localization**: `AskUserQuestion` `header`/`question`/`label`/`description` MUST render in the detected conversation language. JSON below is template — translate user-facing strings before calling.
- **Batch prompts**: One `AskUserQuestion` with multiple `questions[]`. Split only when a later question truly depends on an earlier answer.
- **No redundant Cancel**: Cancellation is implicit. Keep only branches driving different follow-up (e.g. `proceed / revise`, `continue / retry / rollback`).

## 1. Agents & Tools

### 1.1 Agents

| Agent | Role | Model | Output |
|-------|------|-------|--------|
| `atlas:information-gatherer` | Identify refactoring candidates | haiku | `.claude/gather/refactor-<ts>/` |
| `atlas:task-planner` | Generate refactoring plan | inherit | `.claude/plan/refactor-<ts>/` |
| `atlas:atlas-executor` | Execute refactoring | user-selected | direct file edits |

### 1.2 Tools

`AskUserQuestion` (confirm) · `Task` (invoke subagents) · `tsc` / `npm test` (validate)

### 1.3 Data Flow

```
gatherer → context.json → task-planner → plan.json → executor (no re-scan)
```

---

## 2. Modes & Workflow

### 2.1 Mode Comparison

| Step | Quick | Auto | Interactive | dry-run |
|------|-------|------|-------------|---------|
| Execution strategy | auto | auto | ask | auto |
| Candidate identification | **skip** | yes | yes | yes |
| Checkpoint | **skip** | create | ask | skip |
| Planner | **main (direct)** | atlas:task-planner | ask | atlas:task-planner |
| Executor model | **haiku** | sonnet | ask | - |
| Test node | **none** | unified | ask | - |
| Test mode | - | compile | ask | - |
| State file | **create** | create | create | create |

### 2.2 Supported Refactoring Patterns

| Pattern | Description | Trigger |
|---------|-------------|---------|
| `extract-method` | Extract long functions | function body >50 lines |
| `extract-component` | Extract large components | JSX >100 lines |
| `consolidate-duplicate` | Merge duplicate code | similarity >80% |
| `modernize-js` | Modernize JS | var/callback usage |
| `add-types` | Add TS types | any/missing types |
| `rename-convention` | Unify naming | naming inconsistency |
| `simplify-conditions` | Simplify conditions | if-else nesting >3 |
| `remove-dead-code` | Remove dead code | unused exports |

---

## 3. Standard Workflow (Steps 1-7)

### Step 1: Mode Selection (AskUserQuestion)

**Prompt 1 — execution mode**:
- Quick: skip candidate identification and planning, direct refactor (~3 min)
- Auto (recommended): recommended options, minimal interaction
- Interactive: confirm each key step
- dry-run: plan only, no execution

**Prompt 2 — refactor config (interactive and dry-run only)**:
- Checkpoint: create git stash / skip
- Planner: atlas:task-planner / built-in Plan
- Executor model (execution only): sonnet / haiku / opus

**Prompt 3 — test config (auto/interactive only)**:
- Test node: unified (after all) / per-candidate / none
- Test mode: compile (`tsc --noEmit`) / unit (`npm test`) / both

`--quick` flag → skip prompts and go to Quick Mode.

### Step 2: Create Execution Environment

```bash
mkdir -p .claude/refactor/.state
```

State file `.claude/refactor/.state/refactor-<timestamp>.json`:
```json
{
  "executionId": "refactor-<timestamp>", "timestamp": "<ISO-8601>",
  "task": "<refactor pattern>", "pattern": "<pattern>", "scope": "<scope>",
  "status": "initializing", "currentStage": "initialization",
  "config": {
    "mode": "<auto|interactive|dry-run>",
    "task-planner": "<atlas:task-planner|Plan>",
    "executorModel": "<haiku|sonnet|opus>",
    "testNode": "<unified|per-candidate|none>",
    "testMode": "<compile|unit|both>"
  },
  "checkpoint": { "stashId": "atlas-checkpoint-refactor-<timestamp>", "created": false },
  "candidates": [],
  "progress": { "total": 0, "completed": 0, "failed": 0, "pending": 0 },
  "iterations": { "planning": 0, "execution": 0 },
  "todos": []
}
```

Checkpoint if selected: `git stash push -m "atlas-checkpoint-refactor-<timestamp>"`

### Step 3: Candidate Identification

```
Task(subagent_type="atlas:information-gatherer", model="haiku")
prompt: |
  Task ID: refactor-<timestamp>
  Refactor pattern: <pattern>
  Scope: <scope>
  Output dir: .claude/gather/refactor-<timestamp>/
```

Update state: `currentStage="candidates_identified"`

gatherer `context.json` schema:
```json
{
  "candidates": [
    {"id": 1, "file": "src/services/UserService.ts", "symbol": "processOrder",
     "line": 45, "reason": "function body 89 lines", "codeSnippet": "..."}
  ]
}
```

### Step 4: Refactoring Plan

1. **4.1 Run planner** → `.claude/plan/refactor-<ts>/plan.json`
2. **4.2 Display plan**: candidates (file:line), strategy, risk assessment
3. **4.2.5 Completeness**: `plan.json.completeness` coverage must be 100%. On miss, list uncovered → ask to re-plan (recommended)
4. **4.3 Confirm** (AskUserQuestion): proceed / revise plan / finish preview (dry-run)
5. **4.4 Re-plan if needed**: same planner with revision notes; simple → overwrite `plan.json`; complex → `plan.v2.json`, `plan.v3.json`… → back to 4.2

Update state: `currentStage="planning_approved"`, `planVersion`, `candidates[]`, `progress`, `iterations.planning`

### Step 5: Execute Refactoring

1. **5.1 Run executors**: `Task(atlas:atlas-executor, model=<selected>)`; concurrent or serial per test node setting
2. **5.2 Collect results**: successful/failed candidates with reasons
3. **5.2.5 Completion**: compare plan vs executor `completionStatus`; on incomplete → ask: retry / rollback / save progress
4. **5.3 Display**: succeeded X / failed Y / modified files
5. **5.4 Decision** (AskUserQuestion): continue validation / fix failures / adjust / rollback
6. **5.5 Re-execute if needed**: retry only failed/adjusted → 5.1

Update state: `currentStage="refactoring_completed"`, `candidates[]` statuses, `progress`, `iterations.execution`

### Step 6: Validation

| Test Node | Timing |
|-----------|--------|
| per-candidate | Immediately after each refactor |
| unified | Once after all complete |
| none | Skip |

| Test Mode | Command |
|-----------|---------|
| compile | `tsc --noEmit` |
| unit | `npm test` |
| both | `tsc --noEmit && npm test` |

Update state: `currentStage="testing_completed"`

### Step 7: Cleanup & Report

Final state: `status="completed"`, `currentStage="finished"`, `completedAt`, `checkpoint.cleaned=true`.

---

## 4. Quick Mode Flow (--quick)

**Use when**: 1-3 files, simple rename/extract.

**Entry**: `--quick` flag or user selects "Quick mode" in Step 1.

1. Create state file (same schema, `mode: "quick"`, `executorModel: "haiku"`)
2. Main process locates targets via Grep/Glob/Read (≤5 calls)
3. Main process generates simple plan (no task-planner)
4. Run executor:

```
Task(subagent_type="atlas:atlas-executor", model="haiku")
prompt: |
  Subtask #1
  Description: <pattern> - <user task>
  Files: <located files>
  Changes: <analyzed change points>
  Note: Quick mode, only perform specified refactoring
```

5. Simplified report:

```markdown
# Quick Refactor Complete
**Execution ID**: refactor-<timestamp>
**State file**: .claude/refactor/.state/refactor-<timestamp>.json
**Pattern**: <pattern>  **Modified files**: <file list>  **Status**: succeeded / failed

[If failed] Suggestion: use auto mode: /refactor <pattern>
```

**Risk**: no candidate scan, no checkpoint — cannot rollback. On failure, switch to auto mode.

---

## 5. Directory Structure

```
.claude/
├── gather/refactor-<ts>/context.json
├── plan/refactor-<ts>/plan.json [+ plan.v2.json, plan.v3.json optional]
└── refactor/.state/refactor-<ts>.json
```

Task ID `refactor-<timestamp>` (e.g. `refactor-20240115-153000`) stays consistent from Step 1 through Step 7.

---

## 6. Constraints

### Standard Mode — MUST
- Step 1 phased confirmation (mode → refactor config → test config; dry-run skips test config)
- Create and continuously update `.claude/refactor/.state/refactor-<ts>.json` with `currentStage`
- Pipeline: candidates → plan (`completeness`) → execute (`completionStatus`) → test → report
- Use TodoWrite to track candidate/execution status

### Quick Mode — MUST
- Create state file; ≤5 tool calls to locate; executor(haiku) executes; simplified report

### Quick Mode — ALLOWED
- Main process uses Grep/Glob/Read (≤5 calls)
- Main process generates simple plan directly (no task-planner)
- Skip candidate identification and checkpoint

### FORBIDDEN
- Main process directly modifies files (all modifications via executor)
- Standard mode skips candidate identification and plans directly (except quick)
- Standard mode skips planning and executes directly
- Executor re-scans files (must use plan.json or main-process change points)
- Additional AskUserQuestion after Step 1 (except Step 4.3 / 5.4 confirmation loops)
- Standard mode forgets to update `currentStage`
- Proceeding without user confirmation
- Performing optimizations beyond the specified pattern
- Quick mode for complex tasks (>3 files or needs dependency analysis)
