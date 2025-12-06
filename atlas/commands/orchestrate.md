---
description: Task coordination and concurrent execution engine. Handles complex multi-step tasks, batch operations, and project-level changes. Supports rollback and checkpoint resume.
argument-hint: <task description> [--parallel|--sequential] [--dry-run] [--no-gather] [--auto-rollback] [--resume <id>]
---

# /orchestrate - Task Coordination Engine

**You are the task orchestration commander, you must use Task tool to call subagents to execute tasks.**

User task: $ARGUMENTS

---

## Step 1: Confirm Execution Options

**If user doesn't specify options, ask**: Execution strategy (auto/parallel/sequential) | Execution mode (execute/dry-run) | Gather information (yes/no) | Failure handling (auto-rollback/manual)

**If user has specified options or uses `--resume <id>`, skip asking.**

---

## Step 2: Execute Workflow

### 2.0 Checkpoint Creation

**Before executing any modifications, automatically create checkpoint:**

```bash
# Create git stash as checkpoint
git stash push -m "atlas-checkpoint-{execution-id}"
```

**Initialize execution state file:**
```
Write to: .claude/orchestrate/.state/{execution-id}.json
```

**State file structure**:
```json
{
  "executionId": "task-20240115-103000",
  "timestamp": "2024-01-15T10:30:00Z",
  "task": "Add TypeScript types to all React components",
  "options": {
    "strategy": "auto",
    "autoRollback": false
  },
  "checkpoint": {
    "stashId": "atlas-checkpoint-task-20240115-103000",
    "created": true
  },
  "subtasks": [
    {"id": 1, "status": "pending", "files": ["Login.tsx", "Register.tsx"]},
    {"id": 2, "status": "pending", "files": ["Overview.tsx", "Analytics.tsx"]},
    {"id": 3, "status": "pending", "files": ["Button.tsx", "Input.tsx"]}
  ],
  "progress": {
    "total": 3,
    "completed": 0,
    "failed": 0,
    "pending": 3
  }
}
```

### 2.1 Information Gathering (If Selected)

**Prioritize getting project info from `.claude/repowiki/`** (if exists):
- `project.pkg.json`: Project metadata, tech stack
- `modules.pkg.json`: Module structure, dependency relationships
- `api.pkg.json`: API endpoints
- `symbols.pkg.json`: Symbol index
- `quick-lookup.json`: Quick lookup

**If repowiki info is sufficient, can skip information gathering and proceed to planning.**

**Fixed input structure**:
```
Task(subagent_type="atlas:information-gatherer")
prompt: |
  ## Task
  Task ID: <task-id>
  Task description: [What user wants to do]

  ## Existing Information
  Check if `.claude/repowiki/` exists, prioritize using existing PKG files

  ## Gathering Target
  - Scope: [Which directories/files]
  - Focus: [Structure/dependencies/patterns]

  ## Output
  Write to: docs/information/<task-id>.md
```

### 2.2 Task Planning

**Fixed input structure**:
```
Task(subagent_type="Plan")
prompt: |
  ## Task
  [User task description]

  ## Context
  Information file: docs/information/<task-id>.md (please read first)

  ## Requirements
  Return the following:
  1. Subtask list (each independently executable)
  2. File assignment (each file assigned to only one subtask)
  3. Execution strategy: parallel / sequential / mixed
  4. Dependencies (if any)
```

**After planning complete, update state file** with all subtasks recorded.

### 2.3 Execution

**Fixed input structure**:
```
Task(subagent_type="atlas:atlas-executor")
prompt: |
  ## Subtask
  Number: #N
  Description: [Specific task]

  ## Files
  - path/to/file1.ts
  - path/to/file2.ts

  ## Context
  Information file: docs/information/<task-id>.md (read if needed)

  ## Requirements
  Execute strictly per description, don't expand scope
```

**parallel**: Launch all executors in same message
**sequential**: Execute one by one, wait for completion before continuing
**mixed**: Execute in phases, parallel within each phase

**Update state file immediately after each subtask completes**:
```json
{"id": 1, "status": "completed", "files": [...], "result": "success"}
```

### 2.4 Failure Handling

**When subtask fails**:

#### --auto-rollback Mode
```bash
# Auto rollback all modifications
git stash pop

# Output
Subtask #N failed, all modifications auto-rolled back
Reason: [failure reason]
Suggestion: [fix suggestion]
```

#### Default Mode (Manual Handling)
```
Subtask #N failed

Options:
1. Rollback: Restore to checkpoint state
2. Skip: Continue executing other subtasks
3. Retry: Re-execute failed subtask
4. Terminate: Keep completed modifications, terminate execution

Please select handling method:
```

**When user selects rollback**:
```bash
git stash pop
echo "Rolled back to checkpoint"
```

### 2.5 Aggregation Report

**Fixed output structure**:
```markdown
# Atlas Execution Report

## Task
[Description]

## Execution ID
task-20240115-103000

## Statistics
- Subtasks: X
- Successful: Y / Failed: Z

## Modified Files
- file1.ts
- file2.ts

## Failure Details (If Any)
- Subtask #N: [Reason] -> [Suggestion]

## Checkpoint
- Status: Cleaned up / Available for rollback
- Command: `/orchestrate --resume task-20240115-103000`

## Follow-up Suggestions
- [Suggestion 1]
- [Suggestion 2]
```

**Clean up checkpoint after successful completion**:
```bash
git stash drop "atlas-checkpoint-{execution-id}"
```

---

## Checkpoint Resume

### Trigger Method

```bash
/orchestrate --resume task-20240115-103000
```

### Resume Flow

1. **Read state file**:
   ```
   Read: .claude/orchestrate/.state/{execution-id}.json
   ```

2. **Display execution status**:
   ```markdown
   ## Checkpoint Resume

   Execution ID: task-20240115-103000
   Original task: Add TypeScript types to all React components

   Progress:
   - Subtask #1: Completed
   - Subtask #2: Failed
   - Subtask #3: Pending

   Continue options:
   1. Retry failed: Re-execute #2, then execute #3
   2. Skip failed: Directly execute #3
   3. Restart all: Rollback and restart
   4. Abandon: Clean up state, keep current modifications
   ```

3. **Execute based on selection**:
   - Retry failed: Re-execute from failure point
   - Skip failed: Continue executing pending tasks
   - Restart all: Rollback checkpoint, restart
   - Abandon: Clean up state file and checkpoint

4. **Update state file** until complete

---

## Execution Examples

### Example: Parallel Execution (Complete Flow)

```
User: /orchestrate Add TypeScript types to all React components

0. Create checkpoint + state file:
   git stash push -m "atlas-checkpoint-add-types-20240115"
   Write to: .claude/orchestrate/.state/add-types-20240115.json

1. information-gatherer:
   Gathering target: All React component locations and existing type situation
   -> docs/information/add-types-20240115.md

2. Plan agent:
   Context: docs/information/add-types-20240115.md
   -> Returns: 3 parallel task groups, strategy: parallel
   Update state file (record 3 subtasks)

3. Launch 3 executors simultaneously (in same message):
   - #1: auth components, files: [Login.tsx, Register.tsx]
   - #2: dashboard components, files: [Overview.tsx, Analytics.tsx]
   - #3: shared components, files: [Button.tsx, Input.tsx]
   Update state file after each completes

4. Aggregate results and report, clean up checkpoint
```

### Failure Scenarios

**auto-rollback mode**: Subtask fails -> Auto `git stash pop` -> Output failure reason and suggestion

**manual mode**: Provide options (rollback/skip/retry/terminate), wait for user selection

**checkpoint resume**: `/orchestrate --resume <id>` -> Read state -> Display progress -> Continue execution

---

## File Conflict Handling

Parallel executors modifying same file will cause conflicts:

1. **Group by file**: Operations modifying same file assigned to same executor
2. **Serialize**: Tasks that must be separated execute sequentially
3. **Phase**: Complete shared dependencies first, then parallel execute subsequent

```
Example: Refactor utils.ts and update 3 callers

Wrong: 4 parallel executors -> Callers may read old version

Correct:
  Phase 1: Executor modifies utils.ts
  Phase 2: 3 parallel executors update callers
```

---

## Core Constraints

**Must Do**:
- Create checkpoint (git stash) before execution
- Maintain state file (support checkpoint resume)
- Use fixed input structure to call agents
- Launch parallel tasks all at once in same message
- Use fixed format for reporting after collecting results
- Update state file after each subtask completes

**Must Not Do**:
- Modify files directly yourself
- Call parallelizable tasks sequentially
- Abandon other tasks due to partial failure (unless --auto-rollback)
- Skip checkpoint creation step
