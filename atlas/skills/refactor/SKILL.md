---
name: refactor
description: Intelligent refactoring. Identifies code issues and executes pattern-based automated refactoring. Supports preview and interactive confirmation.
version: 1.0.0
color: orange
---

# refactor - Intelligent Refactoring Skill

## Interaction Rules

- **Localization**: All `AskUserQuestion` `header`/`question`/`label`/`description` strings MUST be rendered in the detected system/conversation language. Never hardcode English — the JSON examples below are structural templates; translate every user-facing string before calling the tool.
- **Batch prompts**: Prefer a single `AskUserQuestion` call with multiple `questions[]` over sequential calls. Only split when a later question genuinely depends on the earlier answer.
- **No redundant Cancel**: Confirmation prompts MUST NOT add an explicit `Cancel` option — cancellation is implicit (the user can decline/abort). Keep only branches that drive different follow-up behavior (e.g. `proceed / revise`, `continue / retry / rollback`).

## 1. Agents & Tools

### 1.1 Agents

| Agent | Role | Model | Output |
|-------|------|-------|--------|
| `atlas:information-gatherer` | Identify refactoring candidates | haiku | `.claude/gather/refactor-<ts>/` |
| `atlas:task-planner` | Generate refactoring plan | inherit | `.claude/plan/refactor-<ts>/` |
| `atlas:atlas-executor` | Execute refactoring | user-selected | direct file edits |

### 1.2 Tools

| Tool | Purpose |
|------|---------|
| `AskUserQuestion` | Confirm options |
| `Task` | Invoke subagents |
| `tsc` / `npm test` | Validate results |

### 1.3 Data Flow

```
gatherer → .claude/gather/refactor-<ts>/context.json
    ↓
task-planner → .claude/plan/refactor-<ts>/plan.json
    ↓
executor → direct file modifications (no re-scanning)
```

---

## 2. Modes & Workflow

### 2.1 Mode Comparison

| Step | Quick | Auto | Interactive | dry-run |
|------|-------|------|-------------|---------|
| Execution strategy | auto | auto | ask user | auto |
| Candidate identification | **skip** | yes | yes | yes |
| Checkpoint | **skip** | create | ask user | skip |
| Planner | **main process (direct)** | atlas:task-planner | ask user | atlas:task-planner |
| Executor model | **haiku** | sonnet | ask user | - |
| Test node | **none** | unified | ask user | - |
| Test mode | - | compile | ask user | - |
| State file | **create** | create | create | create |

### 2.2 Supported Refactoring Patterns

| Pattern | Description | Trigger Condition |
|---------|-------------|------------------|
| `extract-method` | Extract long functions | function body >50 lines |
| `extract-component` | Extract large components | JSX >100 lines |
| `consolidate-duplicate` | Merge duplicate code | similarity >80% |
| `modernize-js` | Modernize JS | var/callback usage |
| `add-types` | Add TS types | any/missing types |
| `rename-convention` | Unify naming | naming inconsistency |
| `simplify-conditions` | Simplify conditions | if-else nesting >3 levels |
| `remove-dead-code` | Remove dead code | unused exports |

---

## 3. Standard Workflow (Steps 1-7)

### Step 1: Mode Selection (AskUserQuestion)

**First prompt — execution mode:**
- Quick mode: skip candidate identification and planning, direct refactor (~3 min)
- Auto mode (recommended): use recommended options, minimal interaction
- Interactive mode: confirm at each key step
- dry-run: plan only, no execution

**Second prompt — refactor config (interactive and dry-run only):**
- Checkpoint: create git stash / skip
- Planner: atlas:task-planner / built-in Plan
- Executor model (execution modes only): sonnet / haiku / opus

**Third prompt — test config (auto/interactive only):**
- Test node: unified (after all) / per-candidate / none
- Test mode: compile (`tsc --noEmit`) / unit (`npm test`) / both

If `--quick` flag is present, skip all prompts and go directly to Quick Mode flow.

### Step 2: Create Execution Environment

```bash
mkdir -p .claude/refactor/.state
```

State file `.claude/refactor/.state/refactor-<timestamp>.json`:
```json
{
  "executionId": "refactor-<timestamp>",
  "timestamp": "<ISO-8601>",
  "task": "<refactor pattern>",
  "pattern": "<pattern>",
  "scope": "<scope>",
  "status": "initializing",
  "currentStage": "initialization",
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

Create checkpoint if selected:
```bash
git stash push -m "atlas-checkpoint-refactor-<timestamp>"
```

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
    {
      "id": 1,
      "file": "src/services/UserService.ts",
      "symbol": "processOrder",
      "line": 45,
      "reason": "function body 89 lines",
      "codeSnippet": "..."
    }
  ]
}
```

### Step 4: Refactoring Plan

1. **4.1 Run planner**: `Task(subagent_type="<selected planner>")` → outputs `.claude/plan/refactor-<ts>/plan.json`
2. **4.2 Display plan**: candidates (file:line), refactoring strategy, risk assessment
3. **4.2.5 Completeness check**: read `plan.json.completeness`; coverage must be 100%. If not, list uncovered items → ask user to re-plan (recommended)
4. **4.3 User confirm** (AskUserQuestion): proceed / revise plan / finish preview (dry-run)
5. **4.4 Re-plan if needed**: use same planner with revision notes; simple → overwrite `plan.json`; complex → create `plan.v2.json`, `plan.v3.json`…; loop back to 4.2

Update state: `currentStage="planning_approved"`, `planVersion`, `candidates[]`, `progress`, `iterations.planning`

### Step 5: Execute Refactoring

1. **5.1 Run executors**: `Task(subagent_type="atlas:atlas-executor", model=<selected>)`; concurrent or serial per test node setting
2. **5.2 Collect results**: successful candidates, failed candidates with reasons
3. **5.2.5 Completion check**: compare plan vs executor `completionStatus`; if incomplete → ask user: retry / rollback / save progress
4. **5.3 Display results**: succeeded X / failed Y / modified files list
5. **5.4 User decision** (AskUserQuestion): continue to validation / fix failures / adjust / rollback
6. **5.5 Re-execute if needed**: retry only failed/adjusted candidates; loop back to 5.1

Update state: `currentStage="refactoring_completed"`, `candidates[]` statuses, `progress`, `iterations.execution`

### Step 6: Validation

| Test Node | Timing |
|-----------|--------|
| per-candidate | immediately after each refactor |
| unified | once after all complete |
| none | skip |

| Test Mode | Command |
|-----------|---------|
| compile | `tsc --noEmit` |
| unit | `npm test` |
| both | `tsc --noEmit && npm test` |

Update state: `currentStage="testing_completed"`

### Step 7: Cleanup & Report

Update final state:
```json
{
  "status": "completed",
  "currentStage": "finished",
  "completedAt": "<ISO-8601>",
  "checkpoint": { "stashId": "...", "created": true, "cleaned": true }
}
```

---

## 4. Quick Mode Flow (--quick)

**Use when**: 1-3 files, simple rename/extract operations.

**Entry**: `--quick` flag or user selects "Quick mode" in Step 1.

**Steps:**

1. Create state file (same schema, `mode: "quick"`, `executorModel: "haiku"`)
2. Main process locates targets with Grep/Glob/Read (max 5 tool calls)
3. Main process generates simple modification plan (no task-planner)
4. Run executor:

```
Task(subagent_type="atlas:atlas-executor", model="haiku")
prompt: |
  Subtask #1
  Description: <pattern> - <user task>
  Files: <located files>
  Changes: <analyzed change points>
  Note: Quick mode, only perform the specified refactoring
```

5. Output simplified report:

```markdown
# Quick Refactor Complete

**Execution ID**: refactor-<timestamp>
**State file**: .claude/refactor/.state/refactor-<timestamp>.json
**Pattern**: <pattern>
**Modified files**: <file list>
**Status**: succeeded / failed

[If failed] Suggestion: use auto mode: /refactor <pattern>
```

**Risk**: no candidates scan, no checkpoint — cannot rollback. If failed, switch to auto mode.

---

## 5. Directory Structure

```
.claude/
├── gather/refactor-<timestamp>/
│   └── context.json
├── plan/refactor-<timestamp>/
│   ├── plan.json
│   ├── plan.v2.json  (optional)
│   └── plan.v3.json  (optional)
└── refactor/.state/
    └── refactor-<timestamp>.json
```

Task ID format: `refactor-<timestamp>` (e.g. `refactor-20240115-153000`). Same ID used from Step 1 through Step 7.

---

## 6. Constraints

### Standard Mode — MUST

- ✅ Step 1 phased confirmation (mode → refactor config → test config; dry-run skips test config)
- ✅ Create and continuously update `.claude/refactor/.state/refactor-<ts>.json` with `currentStage`
- ✅ Pipeline: candidates → plan (with `completeness`) → execute (with `completionStatus`) → test → report
- ✅ Use TodoWrite to track candidate/execution status

### Quick Mode — MUST

- ✅ Create state file; main process ≤5 tool calls to locate; executor(haiku) executes; output simplified report

### Quick Mode — ALLOWED

- ✅ Main process uses Grep/Glob/Read to locate files (max 5 calls)
- ✅ Main process generates simple plan directly (no task-planner)
- ✅ Skip candidate identification and checkpoint

### FORBIDDEN

- ❌ Main process directly modifies files (all modifications must go through executor)
- ❌ Standard mode skips candidate identification and plans directly (except quick mode)
- ❌ Standard mode skips planning and executes directly
- ❌ Executor re-scans files (must use plan.json or main-process-provided change points)
- ❌ Additional AskUserQuestion after Step 1 (except Step 4.3 and 5.4 confirmation loops)
- ❌ Standard mode forgets to update `currentStage` in state file
- ❌ Proceeding to next step without user confirmation
- ❌ Performing additional optimizations beyond the specified pattern
- ❌ Using quick mode for complex tasks (>3 files or requiring dependency analysis)
