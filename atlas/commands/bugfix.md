---
description: Problem diagnosis and fix suggestions. Analyze root cause, provide fix solutions, optionally execute fixes.
argument-hint: <problem description> [--quick] [--scope path] [--fix] [--auto]
---

# /bugfix - Problem Diagnosis and Fix

## 1. Agents and Tools

### 1.1 Agent Description

| Agent | Responsibility | Model | Output Location |
|-------|----------------|-------|-----------------|
| `atlas:information-gatherer` | Collect problem-related information | haiku | `.claude/gather/bugfix-<ts>/` |
| `atlas:planner` | Develop fix plan | inherit | `.claude/plan/bugfix-<ts>/` |
| `atlas:atlas-executor` | Execute fix | User's choice | Direct file modification |

### 1.2 Tool Description

| Tool | Purpose |
|------|---------|
| `AskUserQuestion` | Confirm options |
| `Task` | Call subagent |
| `git stash` | Create checkpoint |

### 1.3 Information Flow

```
gatherer → .claude/gather/bugfix-<ts>/context.json
    ↓
planner → .claude/plan/bugfix-<ts>/plan.json
    ↓
executor → Direct fix (no re-scanning needed)
```

---

## 2. Orchestration Plan

### 2.1 Mandatory Flow

```
Problem Analysis → Confirm Options → Information Gathering → Root Cause Analysis → Planning → [--fix] Execution → Testing → Report
```

### 2.2 Mode Behavior Definition

| Step | Quick Mode | Diagnose Only | Execute Fix (Interactive) | Auto Mode |
|------|------------|---------------|---------------------------|-----------|
| Execution Strategy | auto | No execution | Manual confirmation | auto |
| Information Gathering | **Skip** | Ask | Ask | Yes |
| Diagnosis Depth | **Skip** | Ask | Ask | Quick |
| Checkpoint | **Skip** | - | Ask | Create |
| Planner | **Skip (main process locates directly)** | Ask | Ask | atlas:planner |
| Executor Model | **haiku** | - | Ask | sonnet |
| Test Node | **No test** | - | Ask | After fix |
| Test Mode | - | - | Ask | Compile test |
| Failure Handling | Ask user | - | Ask user | Ask user |
| State File | **Create** | - | Create | Create |

### 2.3 Execution Steps

**Step 1: Phased Option Confirmation**

**First AskUserQuestion: Execution Mode Selection**

```
Question: Execution Mode
- Quick Mode: Skip information gathering, fix directly (suitable for clear single-point bugs, ~3 minutes)
- Diagnose Only (Recommended): Only analyze the problem, output fix plan
- Execute Fix: Automatically execute fix after diagnosis
- Auto Mode: Use recommended options, reduce interaction
```

**Second AskUserQuestion: Diagnosis Configuration**

```
Question 1: Information Gathering
- Yes (Recommended): Use gatherer to collect problem-related information
- No: Skip information gathering (suitable when problem scope is clear)

Question 2: Planner Selection
- atlas:planner (Recommended): Trust gatherer output, minimize scanning
- Built-in Plan: Will explore and verify on its own

Question 3: Diagnosis Depth
- Quick (Recommended): Focus on the problem itself
- Deep: Analyze impact scope and potential cascading issues
- Full: Comprehensive diagnosis (including code quality, security, etc.)
```

**Auto Mode Behavior** (Skip second AskUserQuestion):
- Information Gathering: Yes
- Planner: atlas:planner
- Diagnosis Depth: Quick
- Failure Handling: Ask user

**Quick Mode Behavior** (Skip second and third AskUserQuestion):
- Information Gathering: Skip
- Checkpoint: Skip
- Planner: Skip (main process locates directly)
- Executor Model: haiku
- Test: No test
- State File: Create

**Third AskUserQuestion: Fix and Test Configuration** (Execute Fix mode and Auto mode only)

If user selected **Execute Fix** or **Auto Mode**, ask for fix and test configuration:

```
Question 1: Create Checkpoint
- Create (Recommended): Can rollback on failure
- Skip: Don't create

Question 2: Executor Model
- sonnet (Recommended): Balance performance and quality
- haiku: Quick simple fixes
- opus: Complex high-quality requirements

Question 3: Test Node
- After Fix (Recommended): Test after fix completion
- No Test: Skip verification

Question 4: Test Mode
- Compile Test (Recommended): tsc --noEmit
- Unit Test: npm test
- Compile + Unit: Full verification
```

**Notes**:
- Diagnose Only mode skips the third AskUserQuestion
- Both Auto mode and Execute Fix mode require the third AskUserQuestion
- **Quick mode skips all questions and proceeds directly to execution**

---

### 2.4 Quick Mode Flow (--quick)

**Applicable Scenarios**:
- Fix clear bugs in 1-3 files
- User has already located the problem
- Simple syntax errors, type errors, typos

**Flow**:
```
Confirm Mode → Main Process Quick Locate → Direct Fix → Simplified Report
```

**Step Q1: Confirm Quick Mode**
```
AskUserQuestion:
Question: Execution Mode
- Quick Mode ✓
```

**Step Q2: Create State File**
```bash
# Create state directory
mkdir -p .claude/orchestrate/.state

# Initialize state file
echo '{
  "executionId": "bugfix-<timestamp>",
  "timestamp": "<ISO-8601>",
  "task": "<user task>",
  "status": "in_progress",
  "currentStage": "quick_bugfix",
  "config": { "mode": "quick", "executorModel": "haiku" }
}' > .claude/orchestrate/.state/bugfix-<timestamp>.json
```

**Step Q3: Main Process Quick Locate**
```
Main process is allowed to use Grep/Glob/Read to quickly locate target files (≤5 tool calls)
Analyze root cause
Directly build executor prompt (without calling planner agent)
```

**Step Q4: Direct Fix**
```
Task(subagent_type="atlas:atlas-executor", model="haiku")
prompt: |
  Subtask #1
  Description: [Problem fix]
  Files: [Files located by main process]
  Problem: [Root cause analysis]
  Modification Points: [Modification points analyzed by main process]
  Note: Quick mode, only do explicitly mentioned fixes
```

**Step Q5: Simplified Report**
```markdown
# Quick Fix Complete

**Execution ID**: bugfix-<timestamp>
**State File**: .claude/orchestrate/.state/bugfix-<timestamp>.json
**Problem**: [Description]
**Root Cause**: [Location]
**Modified Files**: [File list]
**Status**: ✅ Success / ❌ Failed

[If failed] Suggestion: Use auto mode to re-execute `/bugfix <problem> --fix`
```

**Quick Mode Risk Notes**:
- Skips deep diagnosis, may miss related issues
- Skips checkpoint, cannot rollback
- If executor fails, suggest user switch to auto mode

---

### 2.5 Standard Mode Execution Steps

**Step 2: Create Execution Environment** (Execute Fix and Auto mode only)

```bash
# Create state directory
mkdir -p .claude/bugfix/.state

# Initialize state file
echo '{
  "executionId": "bugfix-<timestamp>",
  "timestamp": "<ISO-8601-timestamp>",
  "task": "<problem description>",
  "status": "initializing",
  "currentStage": "initialization",
  "mode": "<diagnose-only/execute-fix/auto>",
  "config": {
    "gatherInfo": "<yes/no>",
    "planner": "<atlas:planner/Plan>",
    "diagnosisDepth": "<quick/deep/full>",
    "executorModel": "<haiku/sonnet/opus>",
    "testNode": "<after-fix/none>",
    "testMode": "<compile/unit/both>"
  },
  "checkpoint": {
    "stashId": "atlas-checkpoint-bugfix-<timestamp>",
    "created": false
  },
  "diagnosis": null,
  "fixApplied": false,
  "iterations": {
    "planning": 0,
    "execution": 0
  }
}' > .claude/bugfix/.state/bugfix-<timestamp>.json

# Create checkpoint (if selected)
git stash push -m "atlas-checkpoint-bugfix-<timestamp>"

# Update state
Update .state/bugfix-<timestamp>.json: {
  checkpoint.created: true,
  currentStage: "checkpoint_created"
}
```

**Step 3: Information Gathering**
```
Task(subagent_type="atlas:information-gatherer", model="haiku")
prompt: |
  Task ID: bugfix-<timestamp>
  Problem Description: [User's problem]
  Search Scope: [scope]
  Output Directory: .claude/gather/bugfix-<timestamp>/
```

After completion, update state:
.state/bugfix-<timestamp>.json: currentStage="gathering_completed"
```

**Step 4: Root Cause Analysis and Fix Planning** (Supports iterative modification)

**Important: Use unified bugfix-<timestamp> ID, all files operate in the same directory**

```
┌─────────────────────────────────────────┐
│ 4.1 Execute Planning (First time)       │
│ Task(subagent_type="<user's planner>")  │
│ Output: .claude/plan/bugfix-<ts>/plan.json│
└─────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│ 4.2 Display Diagnosis Results           │
│ - Root cause analysis (file:line)       │
│ - Problem type and complexity           │
│ - Fix plan (strategy, steps, risks)     │
└─────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│ 4.3 User Confirmation                   │
│ AskUserQuestion:                        │
│ - Continue execution (if Execute Fix)  │
│ - Modify plan: User suggests changes   │
│ - Complete diagnosis: Output report only│
└─────────────────────────────────────────┘
         ↓
    [User selects modify]
         ↓
┌─────────────────────────────────────────┐
│ 4.4 Re-planning (Versioned)             │
│ Use same planner, pass in modifications │
│ Output strategy:                        │
│ - Simple: Overwrite plan.json          │
│ - Complex: Create plan.v2.json, plan.v3.json│
│ Return to 4.2 (loop until user confirms)│
└─────────────────────────────────────────┘

After completion, update state:
.state/bugfix-<timestamp>.json: {
  currentStage: "planning_approved",
  planVersion: "final" or "v2",
  diagnosis: {
    location: "file:line",
    type: "...",
    complexity: "simple/moderate/complex"
  },
  iterations.planning: <iteration count>
}

Output file example:
.claude/plan/bugfix-<timestamp>/
├── plan.json (or plan.final.json)  # Final plan
├── plan.v1.json  # Optional: Historical version
└── plan.v2.json  # Optional: Historical version
```

**Step 5: Execute Fix** (Execute Fix mode only, supports iteration)

```
┌─────────────────────────────────────────┐
│ 5.1 Execute Fix                         │
│ Task(subagent_type="atlas:atlas-executor")│
│ model=<user's selected model>           │
└─────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│ 5.2 Display Fix Results                 │
│ - Modified files and locations          │
│ - Fix status (success/failure)          │
└─────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│ 5.3 User Decision                       │
│ AskUserQuestion:                        │
│ - Continue verification (recommended)  │
│ - Re-fix: User unsatisfied, adjust plan│
│ - Rollback changes                      │
└─────────────────────────────────────────┘
         ↓
    [User selects re-fix]
         ↓
┌─────────────────────────────────────────┐
│ 5.4 Re-execute                          │
│ Return to 5.1                           │
└─────────────────────────────────────────┘

After completion, update state:
.state/bugfix-<timestamp>.json: {
  currentStage: "fix_applied",
  fixApplied: true,
  iterations.execution: <iteration count>
}
```

**Step 6: Verification Testing** (Execute based on Step 1 selection)

```bash
# Execute tests based on configuration
Execute based on testMode: tsc --noEmit / npm test / both

# Update state
Update .state/bugfix-<timestamp>.json: currentStage="testing_completed"
```

**Step 7: Cleanup and Report**

```bash
# Update final state
Update .state/bugfix-<timestamp>.json: {
  status: "completed",
  currentStage: "finished",
  completedAt: "<ISO-8601-timestamp>"
}

# Output report (see Chapter 4)
```

---

## 3. Key Details

### 3.1 Task ID Management Principles

**Unified Task ID**:
- Format: `bugfix-<timestamp>` (e.g., `bugfix-20240115-143000`)
- Use the **same** ID from Step 1 to Step 7
- All related files are associated with this ID

**Directory Structure**:
```
.claude/
├── gather/bugfix-<timestamp>/     # gatherer output (unchanged)
│   └── context.json
├── plan/bugfix-<timestamp>/        # planner output (versioned)
│   ├── plan.json (or plan.final.json)
│   ├── plan.v1.json (optional)
│   └── plan.v2.json (optional)
├── bugfix/.state/                  # State files
│   └── bugfix-<timestamp>.json
```

**Versioning Strategy**:
- **Simple scenarios**: Directly overwrite `plan.json`
- **Complex scenarios**: Create version files `plan.v2.json`, `plan.v3.json`, etc.
- State file records `planVersion` field

### 3.2 Main Process Responsibilities

**Allowed**: AskUserQuestion / Task calls / Read agent output / Git operations

**Prohibited**: Read/Grep/Glob to read code / Edit/Write to modify files / Direct code analysis

### 3.3 Root Cause Analysis Output Format

```markdown
## Problem Diagnosis
**Problem Description**: [User's description]
**Problem Type**: [Error type]
**Complexity**: simple | moderate | complex

## Root Cause Analysis
**Location**: [file:line]
**Cause**: [Specific cause]
**Impact**: [Impact scope]

## Fix Plan
**Strategy**: [Direct fix/Defensive fix/Refactor]
**Steps**: 1. [Step] - [file:location]
**Verification**: [Verification method]
**Risks**: [Potential risks]
```

---

## 4. Examples

### Example 1: Quick Fix (~3 minutes) - Clear single-point bug

```
User: /bugfix Login.tsx line 45 onClick not bound --quick

1. Select Quick Mode → Skip all subsequent questions
2. Main process locates: Grep "onClick" src/components/Login.tsx
   → Found line 45: <button onClick={handleLogin}>
   → Read context: handleLogin defined at line 12, but not bound to this
3. Root cause confirmed: handleLogin not bound in constructor for class component
4. Executor(haiku): Add this.handleLogin = this.handleLogin.bind(this) in constructor
5. Fix complete: src/components/Login.tsx (1 modification)
6. Output: ✅ Quick fix successful | Suggestion: Consider using arrow functions to avoid binding issues
```

### Example 2: Auto Mode - Bug requiring diagnosis

```
User: /bugfix User list API returns undefined --auto

1. Select Auto Mode → Use recommended config (gatherer + atlas:planner + quick diagnosis)
2. Create checkpoint: git stash push -m "atlas-checkpoint-bugfix-20240115-143000"
3. Gatherer collects: Search "user list" related code → Locate api/users.ts, hooks/useUsers.ts
4. Planner diagnoses: Root cause at api/users.ts:28 - response.data.users should be response.data.list
   → Complexity: simple | Impact: All callers of useUsers hook
5. User confirms plan ✓
6. Executor(sonnet): Fix field mapping at api/users.ts line 28
7. Test: tsc --noEmit ✓ | Output report: 1 file modified, root cause fixed
```

### Example 3: Interactive Mode - Complex bug fix

```
User: /bugfix Order status not updating after submission --fix

1. Select Execute Fix → Config: Deep diagnosis + opus + compile + unit test
2. Create checkpoint + Gatherer collects: Order-related files (5) + State management (3)
3. Planner deep diagnosis:
   → Root cause 1: store/order.ts:45 - Async action not awaited
   → Root cause 2: api/order.ts:67 - Missing error handling causes silent failure
   → Complexity: moderate | Related impact: Cart, payment flow
4. User reviews plan → Request: "Keep original error handling logic"
5. Planner re-plans (v2): Adjust fix strategy, preserve try-catch structure
6. User confirms ✓ → Executor(opus): Fix 2 files
7. Test: tsc ✓ + npm test ✓ (All order-related test cases pass)
8. Report: 2 files modified | Iterations: 2 planning, 1 execution | Checkpoint available for rollback
```

---

## 5. Core Constraints

### Standard Mode Must Do

- ✅ **Step 1**: Phased configuration confirmation (first question for execution mode, second for diagnosis config, third for fix and test config)
- ✅ **Step 2**: Create state directory `.claude/bugfix/.state/` and state file (Execute Fix mode and Auto mode)
- ✅ **Step 2**: Update state file's `currentStage` field after each key step
- ✅ **Step 3**: Use `Task(subagent_type="atlas:information-gatherer", model="haiku")`
- ✅ **Step 4**: Use user's selected planner, output to `.claude/plan/bugfix-<ts>/`
- ✅ **Step 4.2-4.4**: Display diagnosis to user, support iterative modification until user confirms
- ✅ **Step 5**: Extract modification points from plan.json and embed in executor prompt (Execute Fix mode and Auto mode)
- ✅ **Step 5.2-5.4**: Display fix results, support user re-fix or adjustment
- ✅ **Step 6**: Execute verification tests based on Step 1 selection
- ✅ **Step 7**: Update final state and output report

### Quick Mode Must Do

- ✅ **Step Q1**: Confirm user selects quick mode
- ✅ **Step Q2**: Create state file `.claude/orchestrate/.state/bugfix-<timestamp>.json`
- ✅ **Step Q3**: Main process quickly locates target files (≤5 tool calls)
- ✅ **Step Q4**: Use `Task(subagent_type="atlas:atlas-executor", model="haiku")`
- ✅ **Step Q5**: Output simplified report (including execution ID and state file path)
- ✅ Suggest user switch to auto mode on failure

### Quick Mode Allowed

- ✅ Main process uses Grep/Glob/Read to quickly locate files (≤5 times)
- ✅ Main process directly analyzes root cause (without calling planner)
- ✅ Skip information gathering and checkpoint

### Prohibited

- ❌ Main process directly modifies files (all modifications must go through executor)
- ❌ Standard mode skips information gathering for direct diagnosis (unless quick mode)
- ❌ Standard mode skips planning for direct fix execution
- ❌ Executor re-scans files (should use plan.json or modification points provided by main process)
- ❌ Additional AskUserQuestion after Step 1 (except for confirmation loops in Step 4.3 and 5.3)
- ❌ Standard mode forgets to update state file's `currentStage`
- ❌ Continue to next step without user confirmation
- ❌ Quick mode for complex problems (>3 files or involving dependency analysis)


**In this command, all operations must be completed in Subagents. The main conversation is only responsible for calling Subagents and outputting reports. No direct operations are allowed in the main conversation. (Except for reading documents in the flow)**
