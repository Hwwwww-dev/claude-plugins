---
description: Task coordination and concurrent execution engine. Handles complex multi-step tasks, batch operations, and project-level changes. Supports rollback and checkpoint resume.
argument-hint: <task description> [--quick] [--parallel|--sequential] [--dry-run] [--no-gather] [--auto-rollback] [--resume <id>]
---

# /orchestrate - Task Coordination Engine

## 1. Agents and Tools

### 1.1 Agent Description

| Agent | Responsibility | Model | Output Location |
|-------|----------------|-------|-----------------|
| `atlas:information-gatherer` | Collect project information (structure, dependencies, code snippets) | haiku | `.claude/gather/<task-id>/` |
| `atlas:planner` | Create execution plan based on gatherer output | inherit | `.claude/plan/<task-id>/` |
| `atlas:atlas-executor` | Execute specific subtasks | user selected | Direct file modifications |

### 1.2 Tool Description

| Tool | Purpose | Invocation |
|------|---------|------------|
| `AskUserQuestion` | Interact with user for confirmation | Main process direct call |
| `Task` | Invoke subagent | `Task(subagent_type="...", model="...")` |
| `git stash` | Create/restore checkpoints | Bash execution |

### 1.3 Information Flow

```
gatherer → .claude/gather/<task-id>/context.json
    ↓
planner → reads context.json → outputs .claude/plan/<task-id>/plan.json
    ↓
main process → reads plan.json → embeds in executor prompt
    ↓
executor → directly modifies files (no re-scanning needed)
```

**Core Principle**: Planner outputs precise modification points, executor executes directly.

---

## 2. Orchestration Plan

### 2.1 Mandatory Flow

```
Confirm mode+test → Checkpoint → Information gathering → Select planner → Planning → Select model → Execution → Unified testing → Report
```

**Prohibited**: Main process reading code directly / Main process modifying files directly / Skipping any step

### 2.2 Mode Behavior Definition

| Step | Quick Mode | Auto Mode | Interactive Mode | dry-run |
|------|------------|-----------|------------------|---------|
| Execution strategy | auto | auto | ask user | auto |
| Information gathering | **skip** | yes (unless repowiki sufficient) | ask user | yes |
| Checkpoint | **skip** | create | ask user | skip |
| Planner selection | **skip (main process plans directly)** | atlas:planner | ask user | atlas:planner |
| Executor model | **haiku** | sonnet | ask user | - |
| Test node | **no test** | unified test | ask user | - |
| Test mode | - | compile test | ask user | - |
| Failure handling | ask user | ask user | ask user | - |
| State file | create | create | create | create |

### 2.3 Execution Steps

**Step 1: Phased Option Confirmation**

**First AskUserQuestion: Execution Mode Selection**

```
Question: Execution mode
- Quick mode: Skip information gathering and planning, execute directly (suitable for small changes to 1-3 files, 3-5 minutes)
- Auto mode (recommended): Use recommended options, reduce interaction
- Interactive mode: Confirmation required at each key step
- dry-run: Plan only, no execution
```

**Second AskUserQuestion: Basic Configuration (Interactive mode and dry-run only)**

If user selects **Interactive mode** or **dry-run**, ask for basic configuration:

```
Question 1: Information gathering
- Yes (recommended): Use gatherer to collect project information
- No: Skip information gathering (suitable when repowiki is sufficient)

Question 2: Checkpoint
- Create (recommended): Create git stash checkpoint, supports rollback
- Skip: Don't create checkpoint (dry-run skips by default)

Question 3: Planner selection
- atlas:planner (recommended): Trust gatherer output, minimize scanning
- Built-in Plan: Will explore and verify on its own

Question 4: Executor model
- sonnet (recommended): Balance performance and cost
- haiku: Fast simple tasks
- opus: Complex high-quality requirements
```

**Auto mode behavior** (skips second AskUserQuestion):
- Information gathering: Yes (unless repowiki sufficient)
- Checkpoint: Create
- Planner: atlas:planner
- Executor model: sonnet
- Failure handling: Ask user

**Quick mode behavior** (skips second and third AskUserQuestion):
- Information gathering: Skip
- Checkpoint: Skip
- Planner: Skip (main process plans directly)
- Executor model: haiku
- Testing: No test
- State file: Create

**Third AskUserQuestion: Test Configuration**

Ask for test configuration:

```
Question 1: Test node
- Unified test (recommended): Verify after all executions complete
- After each subtask: Test immediately after each executor completes
- No test: Skip verification

Question 2: Test mode
- Compile test (recommended): tsc --noEmit to ensure syntax correctness
- Unit test: npm test to ensure functionality
- Compile+Unit: Complete verification
```

**Note**:
- Both auto mode and interactive mode will ask for test configuration
- Only dry-run mode skips test configuration questions
- **Quick mode skips all questions and proceeds directly to execution**

---

### 2.4 Quick Mode Flow (--quick)

**Applicable Scenarios**:
- Modifying 1-3 files
- Clear small tasks (e.g., "modify function signature", "add type annotations", "fix single bug")
- User already knows exactly what to change

**Flow**:
```
Confirm mode → Create state file → Main process quick locate → Execute directly → Update state → Report
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
  "currentStage": "quick_mode",
  "config": {
    "mode": "quick",
    "executorModel": "haiku"
  },
  "subtasks": [],
  "progress": { "total": 1, "completed": 0, "failed": 0, "pending": 1 }
}' > .claude/orchestrate/.state/<task-id>.json
```

**Step Q3: Main Process Quick Locate**
```
Main process allowed to use Grep/Glob/Read to quickly locate target files (≤5 tool calls)
Generate simple modification plan (without calling planner agent)
Directly build executor prompt
```

**Step Q4: Execute Directly**
```
Task(subagent_type="atlas:atlas-executor", model="haiku")
prompt: |
  Subtask #1
  Description: [user task]
  Files: [files located by main process]
  Modification points: [modification points analyzed by main process]
  Note: Quick mode, only make explicitly mentioned changes
```

**Step Q5: Update State and Report**
```bash
# Update state file
Update .state/<task-id>.json: {
  status: "completed",
  currentStage: "finished",
  completedAt: "<ISO-8601>",
  progress: { total: 1, completed: 1, failed: 0, pending: 0 }
}
```

```markdown
# Quick Execution Complete

**Task**: [description]
**Execution ID**: <task-id>
**Modified files**: [file list]
**Status**: ✅ Success / ❌ Failed
**State file**: .claude/orchestrate/.state/<task-id>.json

[If failed] Suggestion: Use auto mode to re-execute `/orchestrate <task>`
```

**⚠️ Quick Mode Risk Warning**:
- Skips dependency analysis, may miss impact points
- Skips checkpoint, cannot rollback
- If executor fails, suggest user switch to auto mode for re-execution

---

### 2.5 Standard Mode Execution Steps

**Step 2: Create Execution Environment**
```bash
# Create state directory
mkdir -p .claude/orchestrate/.state

# Initialize state file
echo '{
  "executionId": "<task-id>",
  "timestamp": "<ISO-8601-timestamp>",
  "task": "<user task description>",
  "status": "initializing",
  "currentStage": "initialization",
  "config": {
    "mode": "<auto/interactive/dry-run>",
    "planner": "<atlas:planner/Plan>",
    "executorModel": "<haiku/sonnet/opus>",
    "testNode": "<unified/per-task/none>",
    "testMode": "<compile/unit/both>"
  },
  "checkpoint": {
    "stashId": "atlas-checkpoint-<task-id>",
    "created": false
  },
  "subtasks": [],
  "progress": {
    "total": 0,
    "completed": 0,
    "failed": 0,
    "pending": 0
  },
  "iterations": {
    "planning": 0,
    "execution": 0
  }
}' > .claude/orchestrate/.state/<task-id>.json

# Create checkpoint (non dry-run)
git stash push -m "atlas-checkpoint-{execution-id}"

# Update state
Update .state/<task-id>.json: {
  checkpoint.created: true,
  currentStage: "checkpoint_created"
}
```

**Step 3: Information Gathering**
```
Task(subagent_type="atlas:information-gatherer", model="haiku")
prompt: |
  Task ID: <task-id>
  Task description: [user task]
  Collection target: [scope, focus areas]
  Output directory: .claude/gather/<task-id>/

After completion update state:
.state/<task-id>.json: currentStage="gathering_completed"
```

**Step 4: Task Planning (supports iterative modification)**

**Important: The entire flow uses a unified task-id, all files operate in the same directory**

```
┌─────────────────────────────────────────┐
│ 4.1 Execute Planning (first time)       │
│ Task(subagent_type="<user selected      │
│ planner>")                              │
│ Output: .claude/plan/<task-id>/plan.json│
└─────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│ 4.2 Present Plan to User                │
│ Read and format output plan.json        │
│ Display: subtask list, execution        │
│ strategy, impact scope                  │
└─────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│ 4.3 User Confirmation                   │
│ AskUserQuestion:                        │
│ - Continue execution (recommended)      │
│ - Modify plan: user provides feedback   │
│ - Cancel task                           │
└─────────────────────────────────────────┘
         ↓
    [User selects modify]
         ↓
┌─────────────────────────────────────────┐
│ 4.4 Re-plan (versioned)                 │
│ Use same planner, pass in feedback      │
│ Output strategy (choose one):           │
│ Option A: Overwrite plan.json (simple)  │
│ Option B: Create plan.v2.json,          │
│           plan.v3.json                  │
│           Keep history (complex)        │
│ Return to 4.2 (loop until confirmed)    │
└─────────────────────────────────────────┘

After completion update state:
.state/<task-id>.json: {
  currentStage: "planning_approved",
  planVersion: "final" or "v3",  # final version used
  planHistory: ["v1", "v2", "v3"],  # optional: history list
  subtasks: [
    {"id": 1, "status": "pending", "description": "...", "files": [...]},
    {"id": 2, "status": "pending", "description": "...", "files": [...]},
    ...
  ],
  progress: {
    total: N,
    completed: 0,
    failed: 0,
    pending: N
  },
  iterations.planning: <loop count>
}

Output file example:
.claude/plan/<task-id>/
├── plan.json (or plan.final.json)  # final confirmed plan
├── plan.v1.json  # optional: first version (if keeping history)
├── plan.v2.json  # optional: second version (if keeping history)
└── ...
```

**Step 5: Task Execution (supports iterative modification)**

```
┌─────────────────────────────────────────┐
│ 5.1 Concurrently Launch Executors       │
│ Task(subagent_type="atlas:atlas-        │
│ executor")                              │
│ model=<user selected model>             │
│ One executor per subtask                │
└─────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│ 5.2 Collect Execution Results           │
│ Record successful/failed subtasks       │
└─────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│ 5.3 Present Execution Results           │
│ - Success: X subtasks                   │
│ - Failed: Y subtasks (with reasons)     │
│ - Modified file list                    │
└─────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│ 5.4 User Decision                       │
│ AskUserQuestion:                        │
│ - Continue verification (recommended    │
│   if all successful)                    │
│ - Fix failed tasks: re-plan and execute │
│   for failed items                      │
│ - Adjust results: user provides feedback│
│ - Rollback changes                      │
└─────────────────────────────────────────┘
         ↓
    [User selects fix/adjust]
         ↓
┌─────────────────────────────────────────┐
│ 5.5 Re-execute Failed/Adjusted Tasks    │
│ Return to 5.1 (only for subtasks        │
│ needing modification)                   │
└─────────────────────────────────────────┘

After completion update state:
.state/<task-id>.json: {
  currentStage: "execution_completed",
  subtasks: [update each subtask status: "completed"/"failed"],
  progress: {
    total: N,
    completed: X,
    failed: Y,
    pending: 0
  },
  iterations.execution: <loop count>
}
```

**Step 6: Verification Testing** (execute based on Step 1 selection)

| Test Node | Execution Timing |
|-----------|------------------|
| After each subtask | Run test immediately after each executor completes |
| Unified test | Run test once after all executors complete |
| No test | Skip |

| Test Mode | Command |
|-----------|---------|
| Compile test | `tsc --noEmit` |
| Unit test | `npm test` |
| Compile+Unit | `tsc --noEmit && npm test` |

```bash
# Update state
Update .state/<task-id>.json: currentStage="testing_completed"
```

**Step 7: Cleanup and Report**

```bash
# Update final state
Update .state/<task-id>.json: {
  status: "completed",
  currentStage: "finished",
  completedAt: "<ISO-8601-timestamp>",
  checkpoint: {
    stashId: "...",
    created: true,
    cleaned: true  # if checkpoint cleaned
  }
}

# Output report (see Section 5)
```

---

## 3. Key Details

### 3.1 Main Process Responsibilities

**Allowed**:
- ✅ Use AskUserQuestion to interact with user
- ✅ Use Task to invoke agents
- ✅ Read agent outputs (`.claude/gather/`, `.claude/plan/`)
- ✅ Git checkpoint operations

**Prohibited**:
- ❌ Use Read/Grep/Glob to read code files
- ❌ Use Edit/Write to modify code files
- ❌ Directly analyze code logic

### 3.2 Task ID Management Principles

**Unified Task ID**:
- One task uses the **same** task-id from Step 1 to Step 7
- Format: `<action>-<date>-<time>` (e.g., `add-types-20240115-103000`)
- All related files are associated with this ID

**Directory Structure**:
```
.claude/
├── gather/<task-id>/          # gatherer output (unchanged)
│   └── context.json
├── plan/<task-id>/             # planner output (versioned)
│   ├── plan.json (or plan.final.json)
│   ├── plan.v1.json (optional)
│   └── plan.v2.json (optional)
├── orchestrate/.state/         # state files
│   └── <task-id>.json
```

**Versioning Strategy**:
- **Simple scenarios** (1-2 modifications): Directly overwrite `plan.json`
- **Complex scenarios** (3+ modifications): Create version files `plan.v2.json`, `plan.v3.json`, etc.
- State file records `planVersion` field, pointing to the final version used

### 3.3 Information Transfer Requirements

**Gatherer output must include**:
- `context.json.codeSnippets`: Key code snippets (with line numbers)
- `context.json.recommendations`: Suggestions for planner

**Planner output must include**:
- `plan.json.subtasks[].modifications`: Modification points precise to line numbers
- `plan.json.subtasks[].context`: Embedded code snippets

**Executor input must include**:
- Modification points extracted from plan.json (or plan.final.json) (directly embedded in prompt)
- No additional file reading needed

### 3.4 File Conflict Handling

Parallel executors modifying the same file will cause conflicts:

1. **Group by file**: Operations modifying the same file go to the same executor
2. **Serialize**: Tasks that must be separate execute sequentially
3. **Phase**: Complete shared dependencies first, then execute subsequent tasks in parallel

### 3.5 Failure Handling

**auto-rollback mode**: Automatic `git stash pop`

**manual mode**:
```
Subtask #N failed
Options: Rollback / Skip / Retry / Terminate
```

### 3.6 Complete State File Example

Complete state file structure during execution:

```json
{
  "executionId": "add-types-20240115-103000",
  "timestamp": "2024-01-15T10:30:00Z",
  "task": "Add TypeScript types to all React components",
  "status": "in_progress",
  "currentStage": "execution_completed",
  "config": {
    "mode": "auto",
    "planner": "atlas:planner",
    "executorModel": "sonnet",
    "testNode": "unified",
    "testMode": "compile"
  },
  "checkpoint": {
    "stashId": "atlas-checkpoint-add-types-20240115-103000",
    "created": true,
    "cleaned": false
  },
  "subtasks": [
    {
      "id": 1,
      "status": "completed",
      "description": "Add types to auth components",
      "files": ["Login.tsx", "Register.tsx"]
    },
    {
      "id": 2,
      "status": "completed",
      "description": "Add types to dashboard components",
      "files": ["Overview.tsx", "Analytics.tsx"]
    },
    {
      "id": 3,
      "status": "failed",
      "description": "Add types to shared components",
      "files": ["Button.tsx", "Input.tsx"],
      "error": "Type definition conflict"
    }
  ],
  "progress": {
    "total": 3,
    "completed": 2,
    "failed": 1,
    "pending": 0
  },
  "iterations": {
    "planning": 1,
    "execution": 2
  },
  "completedAt": null
}
```

### 3.7 Checkpoint Resume

```bash
/orchestrate --resume <task-id>
```

**Resume Flow**:
1. Read `.claude/orchestrate/.state/<task-id>.json`
2. Check `currentStage` field to determine interruption point
3. Continue execution from interrupted stage (skip completed steps)
4. Maintain user's previous configuration options
5. Restore execution progress based on `subtasks` and `progress`

**Stage Mapping**:
- `initialization` → Start from Step 2
- `checkpoint_created` → Start from Step 3
- `gathering_completed` → Start from Step 4
- `planning_approved` → Start from Step 5
- `execution_completed` → Start from Step 6
- `testing_completed` → Output report
- `finished` → Completed, no resume needed

**Resume Example**:
```
Read state: add-types-20240115-103000.json
Found: currentStage = "execution_completed", 1 failed subtask

Display progress:
✅ Subtask #1: Completed
✅ Subtask #2: Completed
❌ Subtask #3: Failed - Type definition conflict

Ask user:
- Retry failed task (recommended)
- Skip failed, continue testing
- Rollback all changes
- Abandon task
```

---

## 4. Examples

### Example 1: Quick Mode (~3 minutes)

```
User: /orchestrate modify UserAPI.login return type --quick

1. Select quick mode → Skip all subsequent questions
2. Main process quick locate:
   - Grep "UserAPI" → Find src/api/UserAPI.ts
   - Read file → Locate login method
   - Generate modification plan (without calling planner)
3. Executor(haiku): Modify src/api/UserAPI.ts → Success ✓
4. Simplified report: Task complete, modified 1 file
```

### Example 2: Auto Mode (~20 minutes)

```
User: /orchestrate add TypeScript types to all React components

1. Select auto mode → Use recommended configuration
   - gatherer + planner + sonnet + compile test
2. Create checkpoint: git stash push -m "atlas-checkpoint-..."
3. Gatherer: Collect component info → .claude/gather/<id>/context.json
4. Planner: Generate plan → .claude/plan/<id>/plan.json
   → Display: 3 subtasks → User confirms ✓
5. Executor: Execute 3 subtasks in parallel → All successful ✓
6. Test: tsc --noEmit → Pass ✓
7. Report: Successfully modified 6 files
```

### Example 3: Interactive Mode (with iterative modification)

```
User: /orchestrate refactor user authentication module

1. Select interactive mode → Confirm each configuration item
   - Information gathering: Yes | Checkpoint: Create | Planner: atlas:planner | Model: opus
2. Gatherer + Planner → Display 3 subtasks
   → User: "Need to refactor middleware first" → Re-plan ✓
3. Executor: Execute 3 subtasks
   → middleware: Success | login: Failed | register: Success
   → User selects fix → Retry login → Success ✓
4. Test: tsc --noEmit && npm test → Pass ✓
5. Report: Successfully refactored user authentication module
```

### Example 4: dry-run Mode

```
User: /orchestrate batch update API routes --dry-run

1. Select dry-run → Skip checkpoint and test configuration
2. Gatherer: Collect API route information
3. Planner: Generate plan → Display preview
   - Affected files: 12 | Subtasks: 4 | Strategy: parallel
4. Output preview report (no execution)
5. Prompt: To execute, use /orchestrate --resume <task-id>
```

---

## 5. Output Format

### Quick Mode Report

```markdown
# Quick Execution Complete

**Task**: [description]
**Modified files**: [file list]
**Status**: ✅ Success / ❌ Failed

[If failed]
**Failure reason**: [reason]
**Suggestion**: Use auto mode to re-execute `/orchestrate <task>`
```

### Standard Mode Execution Report

```markdown
# Atlas Execution Report

## Task
[description]

## Execution ID
task-20240115-103000

## Configuration
- Execution mode: [Auto/Interactive/dry-run]
- Planner: [atlas:planner/Plan]
- Executor model: [haiku/sonnet/opus]
- Test node: [Unified test/After each subtask/No test]
- Test mode: [Compile test/Unit test/Compile+Unit]

## Statistics
- Subtasks: X
- Success: Y / Failed: Z
- Planning iterations: N
- Execution iterations: M

## Modified Files
- file1.ts (lines 45-60)
- file2.ts (line 120)

## Failure Details (if any)
- Subtask#N: [reason] → [Fixed/Pending]

## State File
- Location: `.claude/orchestrate/.state/task-20240115-103000.json`
- Final status: completed
- Current stage: finished

## Checkpoint
- Status: Cleaned / Available for rollback
- Stash ID: atlas-checkpoint-{execution-id}
- Recovery command: `git stash list` to view, `git stash apply stash@{N}` to restore

## Checkpoint Resume
- Command: `/orchestrate --resume task-20240115-103000`
- Description: If task interrupted, use this command to continue from interruption point

## Recommendations
- [Recommendation 1]
- [Recommendation 2]
```

---

## 6. Core Constraints

### Standard Mode Must Do

- ✅ **Step 1**: Confirm all configurations at once at the start (execution mode, planner, model, test options)
- ✅ **Step 2**: Create state directory `.claude/orchestrate/.state/` and state file `<task-id>.json`
- ✅ **Step 2**: Update state file's `currentStage` field after each key step completes
- ✅ **Step 2**: Create git checkpoint (non dry-run/quick mode)
- ✅ **Step 3**: Use `Task(subagent_type="atlas:information-gatherer", model="haiku")`
- ✅ **Step 4**: Use user-selected planner, output to `.claude/plan/<task-id>/`
- ✅ **Step 4.2-4.4**: Present plan to user, support iterative modification until user confirms
- ✅ **Step 5**: Extract modification points from plan.json and embed in executor prompt
- ✅ **Step 5.3-5.5**: Present execution results, support user fixing failed tasks or adjusting results
- ✅ **Step 6**: Execute verification testing based on Step 1 selection
- ✅ **Step 7**: Update final state to `completed` and output fixed format report

### Quick Mode Must Do

- ✅ **Step Q1**: Confirm user selects quick mode
- ✅ **Step Q2**: Create state file `.claude/orchestrate/.state/<task-id>.json`
- ✅ **Step Q3**: Main process quick locate target files (≤5 tool calls)
- ✅ **Step Q4**: Use `Task(subagent_type="atlas:atlas-executor", model="haiku")`
- ✅ **Step Q5**: Update state file and output report
- ✅ Suggest user switch to auto mode on failure

### Quick Mode Allowed

- ✅ Main process use Grep/Glob/Read to quickly locate files (≤5 times)
- ✅ Main process directly generate simple modification plan (without calling planner)
- ✅ Skip information gathering and checkpoint

### Prohibited

- ❌ Main process directly modify files (all modifications must go through executor)
- ❌ Standard mode skip information gathering and plan directly (unless --no-gather or quick mode)
- ❌ Standard mode skip planning and execute directly
- ❌ Executor re-scan files (should use plan.json or modification points provided by main process)
- ❌ Additional AskUserQuestion after Step 1 (except for Step 4.3 and 5.4 confirmation loops)
- ❌ Standard mode forget to update state file's `currentStage`
- ❌ Continue to next step without user confirmation
- ❌ Quick mode for complex tasks (>3 files or involving dependency analysis)


**In this orchestrator, all operations must be completed in Subagents. The main conversation only handles invoking Subagents and outputting reports. No direct operations in the main conversation are allowed. (Except reading workflow documents)**
