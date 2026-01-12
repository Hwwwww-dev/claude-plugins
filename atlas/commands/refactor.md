---
description: Intelligent refactoring command. Identifies code issues and performs automated refactoring for specific patterns, with preview and interactive confirmation support.
argument-hint: <pattern> [--quick] [--scope path] [--dry-run] [--interactive]
---

# /refactor - Intelligent Refactoring Command

## 1. Agents and Tools Involved

### 1.1 Agent Description

| Agent | Responsibility | Model | Output Location |
|-------|----------------|-------|-----------------|
| `atlas:information-gatherer` | Identify candidates matching the pattern | haiku | `.claude/gather/refactor-<ts>/` |
| `atlas:planner` | Create refactoring plan | inherit | `.claude/plan/refactor-<ts>/` |
| `atlas:atlas-executor` | Execute refactoring | User's choice | Direct file modification |

### 1.2 Tool Description

| Tool | Purpose |
|------|---------|
| `AskUserQuestion` | Confirm options |
| `Task` | Invoke subagent |
| `tsc` / `npm test` | Validate results |

### 1.3 Information Flow

```
gatherer → .claude/gather/refactor-<ts>/context.json
    ↓
planner → .claude/plan/refactor-<ts>/plan.json
    ↓
executor → Direct refactoring (no re-scanning needed)
```

---

## 2. Orchestration Plan

### 2.1 Mandatory Flow

```
Pattern parsing → Confirm options → Candidate identification → Planning → Execute/Preview → Test → Report
```

### 2.2 Mode Behavior Definition

| Step | Quick Mode | Auto Mode | Interactive Mode | dry-run |
|------|------------|-----------|------------------|---------|
| Execution strategy | auto | auto | Ask user | auto |
| Candidate identification | **Skip** | Yes | Yes | Yes |
| Checkpoint | **Skip** | Create | Ask user | Skip |
| Planner selection | **Skip (main process plans directly)** | atlas:planner | Ask user | atlas:planner |
| Executor model | **haiku** | sonnet | Ask user | - |
| Test node | **No test** | Unified test | Ask user | - |
| Test mode | - | Compile test | Ask user | - |
| State file | **Create** | Create | Create | Create |

### 2.3 Supported Refactoring Patterns

| Pattern | Description | Identification Criteria |
|---------|-------------|------------------------|
| `extract-method` | Extract long functions | Function body >50 lines |
| `extract-component` | Extract large components | JSX >100 lines |
| `consolidate-duplicate` | Merge duplicate code | Similarity >80% |
| `modernize-js` | JS modernization | var/callback |
| `add-types` | Add TS types | any/missing types |
| `rename-convention` | Unify naming | Inconsistent naming |
| `simplify-conditions` | Simplify conditions | if-else >3 levels |
| `remove-dead-code` | Remove dead code | Unused exports |

### 2.4 Execution Steps

**Step 1: Phased Option Confirmation**

**First AskUserQuestion: Execution Mode Selection**

```
Question: Execution mode
- Quick mode: Skip candidate identification and planning, refactor directly (suitable for single-file small refactoring, ~3 minutes)
- Auto mode (recommended): Use recommended options, reduce interaction
- Interactive mode: Confirmation required at each key step
- dry-run: Plan only, no execution
```

**Second AskUserQuestion: Refactoring Configuration (Interactive mode and dry-run only)**

If user selects **Interactive mode** or **dry-run**, ask for refactoring configuration:

```
Question 1: Checkpoint
- Create (recommended): Create git stash checkpoint, supports rollback
- Skip: No checkpoint (dry-run defaults to skip)

Question 2: Planner selection
- atlas:planner (recommended): Trust gatherer output, minimize scanning
- Built-in Plan: Will explore and verify on its own

Question 3: Executor model (execution mode only)
- sonnet (recommended): Balance performance and quality
- haiku: Fast simple refactoring
- opus: Complex high-quality requirements
```

**Auto mode behavior** (skip second AskUserQuestion):
- Checkpoint: Create
- Planner: atlas:planner
- Executor model: sonnet

**Quick mode behavior** (skip second and third AskUserQuestion):
- Candidate identification: Skip
- Checkpoint: Skip
- Planner: Skip (main process plans directly)
- Executor model: haiku
- Test: No test
- State file: Create

**Third AskUserQuestion: Test Configuration**

Ask for test configuration:

```
Question 1: Test node
- Unified test (recommended): Verify after all executions complete
- After each candidate: Test immediately after each refactoring
- No test: Skip verification

Question 2: Test mode
- Compile test (recommended): tsc --noEmit to ensure syntax correctness
- Unit test: npm test to ensure functionality
- Compile + Unit: Complete verification
```

**Note**:
- Both auto mode and interactive mode will ask for test configuration
- Only dry-run mode skips test configuration question
- **Quick mode skips all questions and proceeds directly to execution**

---

### 2.5 Quick Mode Flow (--quick)

**Applicable scenarios**:
- Refactoring 1-3 files
- Simple renaming, method extraction, etc.

**Flow**:
```
Confirm mode → Main process quick locate → Direct execution → Simplified report
```

**Step Q1: Confirm Quick Mode**
```
AskUserQuestion:
Question: Execution mode
- Quick mode ✓
```

**Step Q2: Create State File**
```bash
mkdir -p .claude/refactor/.state
echo '{
  "executionId": "refactor-<timestamp>",
  "timestamp": "<ISO-8601>",
  "task": "<user task>",
  "status": "in_progress",
  "currentStage": "quick_refactor",
  "config": { "mode": "quick", "executorModel": "haiku" }
}' > .claude/refactor/.state/refactor-<timestamp>.json
```

**Step Q3: Main Process Quick Locate**
```
Main process is allowed to use Grep/Glob/Read to quickly locate target files (≤5 tool calls)
Generate simple modification plan (without calling planner agent)
Directly build executor prompt
```

**Step Q4: Direct Execution**
```
Task(subagent_type="atlas:atlas-executor", model="haiku")
prompt: |
  Subtask #1
  Description: [refactoring pattern] - [user task]
  Files: [files located by main process]
  Modification points: [modification points analyzed by main process]
  Note: Quick mode, only do explicitly mentioned refactoring
```

**Step Q5: Simplified Report**
```markdown
# Quick Refactoring Complete

**Execution ID**: refactor-<timestamp>
**State file**: .claude/refactor/.state/refactor-<timestamp>.json
**Pattern**: [refactoring pattern]
**Modified files**: [file list]
**Status**: ✅ Success / ❌ Failed

[If failed] Suggestion: Use auto mode to re-execute `/refactor <pattern>`
```

**Risk warnings**:
- Skipping candidate identification may miss refactoring points
- Skipping checkpoint prevents rollback
- If executor fails, suggest user switch to auto mode

---

### 2.6 Standard Mode Execution Steps

**Step 2: Create Execution Environment** (when executing refactoring)

```bash
# Create state directory
mkdir -p .claude/refactor/.state

# Initialize state file
echo '{
  "executionId": "refactor-<timestamp>",
  "timestamp": "<ISO-8601-timestamp>",
  "task": "<refactoring pattern>",
  "pattern": "<pattern>",
  "scope": "<scope>",
  "status": "initializing",
  "currentStage": "initialization",
  "config": {
    "mode": "<auto/interactive/dry-run>",
    "planner": "<atlas:planner/Plan>",
    "executorModel": "<haiku/sonnet/opus>",
    "testNode": "<unified/per-candidate/none>",
    "testMode": "<compile/unit/both>"
  },
  "checkpoint": {
    "stashId": "atlas-checkpoint-refactor-<timestamp>",
    "created": false
  },
  "candidates": [],
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
}' > .claude/refactor/.state/refactor-<timestamp>.json

# Create checkpoint (if selected)
git stash push -m "atlas-checkpoint-refactor-<timestamp>"

# Update state
Update .state/refactor-<timestamp>.json: {
  checkpoint.created: true,
  currentStage: "checkpoint_created"
}
```

**Step 3: Candidate Identification**
```
Task(subagent_type="atlas:information-gatherer", model="haiku")
prompt: |
  Task ID: refactor-<timestamp>
  Refactoring pattern: [pattern]
  Scope: [scope]
  Output directory: .claude/gather/refactor-<timestamp>/
```

After completion, update state:
.state/refactor-<timestamp>.json: currentStage="candidates_identified"
```

**Step 4: Refactoring Planning** (supports iterative modification)

**Important: Use unified refactor-<timestamp> ID, all files operate in the same directory**

```
┌─────────────────────────────────────────┐
│ 4.1 Execute Planning (first time)       │
│ Task(subagent_type="<user selected planner>") │
│ Output: .claude/plan/refactor-<ts>/plan.json│
└─────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│ 4.2 Display Refactoring Plan            │
│ - Identified candidates (file:line)     │
│ - Refactoring strategy and steps        │
│ - Risk assessment                       │
└─────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│ 4.3 User Confirmation                   │
│ AskUserQuestion:                        │
│ - Continue execution (execution mode)   │
│ - Modify plan: User proposes adjustments│
│ - Complete preview: Output report only (preview mode) │
└─────────────────────────────────────────┘
         ↓
    [User selects modify]
         ↓
┌─────────────────────────────────────────┐
│ 4.4 Re-planning (versioned)             │
│ Use same planner, pass in modifications │
│ Output strategy:                        │
│ - Simple: Overwrite plan.json           │
│ - Complex: Create plan.v2.json, plan.v3.json│
│ Return to 4.2 (loop until user confirms)│
└─────────────────────────────────────────┘

After completion, update state:
.state/refactor-<timestamp>.json: {
  currentStage: "planning_approved",
  planVersion: "final" or "v3",
  candidates: [
    {"id": 1, "status": "pending", "file": "...", "description": "..."},
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
.claude/plan/refactor-<timestamp>/
├── plan.json (or plan.final.json)  # Final plan
├── plan.v1.json  # Optional: historical version
└── plan.v2.json  # Optional: historical version
```

**Step 5: Execute Refactoring** (execution mode, supports iteration)

```
┌─────────────────────────────────────────┐
│ 5.1 Concurrent/Serial Refactoring       │
│ Task(subagent_type="atlas:atlas-executor")│
│ model=<user selected model>             │
│ Concurrent/serial based on test node    │
└─────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│ 5.2 Collect Refactoring Results         │
│ - Successful candidates                 │
│ - Failed candidates with reasons        │
└─────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│ 5.3 Display Results                     │
│ - Success: X candidates                 │
│ - Failed: Y candidates                  │
│ - Modified file list                    │
└─────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│ 5.4 User Decision                       │
│ AskUserQuestion:                        │
│ - Continue validation (recommended if all success) │
│ - Fix failures: Re-refactor failed candidates │
│ - Adjust results: User proposes modifications │
│ - Rollback changes                      │
└─────────────────────────────────────────┘
         ↓
    [User selects fix/adjust]
         ↓
┌─────────────────────────────────────────┐
│ 5.5 Re-execute                          │
│ Return to 5.1 (only for failed/adjusted candidates) │
└─────────────────────────────────────────┘

After completion, update state:
.state/refactor-<timestamp>.json: {
  currentStage: "refactoring_completed",
  candidates: [update each candidate's status],
  progress: {
    total: N,
    completed: X,
    failed: Y,
    pending: 0
  },
  iterations.execution: <loop count>
}
```

**Step 6: Validation Testing** (execute based on Step 1 selection)

| Test Node | Execution Timing |
|-----------|------------------|
| After each candidate | Test immediately after each refactoring |
| Unified test | Test once after all complete |
| No test | Skip |

| Test Mode | Command |
|-----------|---------|
| Compile test | `tsc --noEmit` |
| Unit test | `npm test` |
| Compile + Unit | `tsc --noEmit && npm test` |

```bash
# Update state
Update .state/refactor-<timestamp>.json: currentStage="testing_completed"
```

**Step 7: Cleanup and Report**

```bash
# Update final state
Update .state/refactor-<timestamp>.json: {
  status: "completed",
  currentStage: "finished",
  completedAt: "<ISO-8601-timestamp>",
  checkpoint: {
    stashId: "...",
    created: true,
    cleaned: true  # If checkpoint has been cleaned
  }
}

# Output report (see Chapter 4)
```

---

## 3. Key Details

### 3.1 Task ID Management Principles

**Unified Task ID**:
- Format: `refactor-<timestamp>` (e.g., `refactor-20240115-153000`)
- Use the **same** ID from Step 1 to Step 7
- All related files are associated with this ID

**Directory Structure**:
```
.claude/
├── gather/refactor-<timestamp>/    # gatherer output (unchanged)
│   └── context.json
├── plan/refactor-<timestamp>/      # planner output (versioned)
│   ├── plan.json (or plan.final.json)
│   ├── plan.v1.json (optional)
│   └── plan.v2.json (optional)
├── refactor/.state/                # State files
│   └── refactor-<timestamp>.json
```

**Versioning Strategy**:
- **Simple scenario**: Directly overwrite `plan.json`
- **Complex scenario**: Create version files `plan.v2.json`, `plan.v3.json`, etc.
- State file records `planVersion` field

### 3.2 Main Process Responsibilities

**Allowed**: AskUserQuestion / Task invocation / Read agent output / Run validation commands

**Prohibited**: Read/Grep/Glob to read code / Edit/Write to modify files / Direct code analysis

### 3.3 Candidate Identification Output

gatherer's context.json must include:
```json
{
  "candidates": [
    {
      "id": 1,
      "file": "src/services/UserService.ts",
      "symbol": "processOrder",
      "line": 45,
      "reason": "Function body 89 lines",
      "codeSnippet": "..."
    }
  ]
}
```

### 3.4 Pattern Constraints

- Only execute refactoring for the specified pattern
- Do not "incidentally" make other optimizations
- Maintain existing code style

---

## 4. Examples

### Example 1: Quick Mode (~3 minutes) - Single File Small Refactoring

```
User: /refactor extract-method --scope src/utils/helper.ts --quick

1. AskUserQuestion → User selects "Quick mode" → Skip all subsequent questions
2. Main process quick locate: Grep "function.*{" → Found processData() 89 lines
3. Main process analysis: Identify extractable segment L45-L78 (data validation logic)
4. Executor(haiku): Extract as validateUserData() independent function
5. Impact scope: 1 file | Changes: +15 lines -34 lines (net -19 lines)
6. Output simplified report → Suggestion: For more refactoring points, use auto mode
```

### Example 2: Auto Mode (~15 minutes) - Standard Refactoring Flow

```
User: /refactor extract-method --scope src/services

1. AskUserQuestion → User selects "Auto mode" → Use recommended configuration
2. Create checkpoint: git stash push -m "atlas-checkpoint-refactor-20240115"
3. Gatherer(haiku): Scan src/services/ → Identify 5 candidates (function body >50 lines)
   - UserService.processOrder (89 lines) | PaymentService.validate (67 lines) | ...
4. Planner: Generate plan.json → User confirms execution ✓
5. Executor(sonnet): Execute 5 extract-method refactorings in parallel
   - Success: 5/5 | New functions: 8 | Modified files: 4
6. Test: tsc --noEmit ✓ → Output complete report (with rollback command)
```

### Example 3: Interactive Mode (with Iterative Modification)

```
User: /refactor add-types --scope src/services --interactive

1. AskUserQuestion → User selects "Interactive mode" → Confirm configuration item by item
   - Checkpoint: Create | Planner: atlas:planner | Model: sonnet | Test: Compile + Unit
2. Gatherer: Identify 12 functions with missing types → Planner generates plan
3. User review: "Exclude legacy/ directory" → Re-plan → 8 candidates remaining ✓
4. Executor round 1: 7 success / 1 failed (PaymentService.process type conflict)
5. User selects "Fix failures" → Executor retry: Adjust generic constraints → Success ✓
6. Test: tsc --noEmit ✓ + npm test ✓ → 8/8 complete
7. Output report: Modified 6 files | Added 23 type definitions | iterations: planning=2, execution=2
```

### Example 4: dry-run Mode - Preview Without Execution

```
User: /refactor modernize-js --scope src --dry-run

1. AskUserQuestion → User selects "dry-run" → Skip checkpoint and test configuration
2. Gatherer(haiku): Scan src/ → Identify 15 modernization candidates
   - var declarations: 8 | callback patterns: 5 | legacy loops: 2
3. Planner: Generate detailed refactoring plan (no execution)
4. Output preview report:
   - Estimated modifications: 9 files | Estimated changes: +45 lines -62 lines
   - Risk assessment: Low (no breaking changes)
5. Prompt: After confirmation, execute `/refactor modernize-js --scope src`
```

---

## 5. Core Constraints

### Standard Mode Must Do

- ✅ **Step 1**: Phased configuration confirmation (execution mode → refactoring config → test config)
- ✅ **Step 1**: Auto mode skips second AskUserQuestion, directly uses recommended configuration
- ✅ **Step 1**: dry-run mode skips third AskUserQuestion, no test configuration needed
- ✅ **Step 2**: Create state directory `.claude/refactor/.state/` and state file (when executing refactoring)
- ✅ **Step 2**: Update state file's `currentStage` field after each key step completes
- ✅ **Step 3**: Use `Task(subagent_type="atlas:information-gatherer", model="haiku")`
- ✅ **Step 4**: Use user-selected planner, output to `.claude/plan/refactor-<ts>/`
- ✅ **Step 4.2-4.4**: Display refactoring plan to user, support iterative modification until user confirms
- ✅ **Step 5**: Extract modification points from plan.json and embed in executor prompt (when executing refactoring)
- ✅ **Step 5.2-5.5**: Display refactoring results, support user fixing failures or adjusting results
- ✅ **Step 6**: Execute validation testing based on Step 1 selection
- ✅ **Step 7**: Update final state and output report

### Quick Mode Must Do

- ✅ **Step Q1**: Confirm user selects quick mode
- ✅ **Step Q2**: Create state file `.claude/refactor/.state/refactor-<timestamp>.json`
- ✅ **Step Q3**: Main process quick locate target files (≤5 tool calls)
- ✅ **Step Q4**: Use `Task(subagent_type="atlas:atlas-executor", model="haiku")`
- ✅ **Step Q5**: Output simplified report (with execution ID and state file path)
- ✅ Suggest user switch to auto mode on failure

### Quick Mode Allowed

- ✅ Main process uses Grep/Glob/Read to quickly locate files (≤5 times)
- ✅ Main process directly generates simple modification plan (without calling planner)
- ✅ Skip candidate identification and checkpoint

### Prohibited

- ❌ Main process directly modifies files (all modifications must go through executor)
- ❌ Standard mode skips candidate identification and goes directly to planning (unless quick mode)
- ❌ Standard mode skips planning and goes directly to execution
- ❌ Executor re-scans files (should use plan.json or modification points provided by main process)
- ❌ Additional AskUserQuestion after Step 1 (except for confirmation loops in Step 4.3 and 5.4)
- ❌ Standard mode forgets to update state file's `currentStage`
- ❌ Continue to next step without user confirmation
- ❌ "Incidentally" make other optimizations (only execute refactoring for specified pattern)
- ❌ Quick mode for complex tasks (>3 files or involving dependency analysis)
