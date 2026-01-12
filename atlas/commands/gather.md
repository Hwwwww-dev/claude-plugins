---
description: Intelligent information gathering command. Analyzes project structure, dependencies, code patterns, and outputs structured reports.
argument-hint: <analysis-target> [--quick] [--scope path] [--depth N] [--output report|pkg]
---

# /gather - Information Gathering

## I. Agents and Tools Involved

### 1.1 Agent Description

| Agent | Responsibility | Model | Output Location |
|-------|----------------|-------|-----------------|
| `atlas:information-gatherer` | Execute information gathering | haiku | `.claude/gather/<task-id>/` |

### 1.2 Tool Description

| Tool | Purpose |
|------|---------|
| `AskUserQuestion` | Confirm gathering options |
| `Task` | Invoke subagent |

### 1.3 Information Flow

```
gatherer → .claude/gather/<task-id>/
    ├── report.md      # Human-readable report
    └── context.json   # Structured data (for subsequent commands)
```

---

## II. Orchestration Plan

### 2.1 Mandatory Flow

```
Confirm execution mode → Confirm gathering config (interactive mode) → Invoke gatherer → Output summary
```

### 2.2 Mode Behavior Definition

| Step | Quick Mode | Auto Mode | Interactive Mode |
|------|------------|-----------|------------------|
| Gathering mode | Smart inference | Smart inference (default: project-structure) | Ask user |
| Analysis depth | normal | normal | Ask user |
| Analysis scope | all | all | Ask user |
| Information gathering | **Main process direct analysis** | gatherer agent | gatherer agent |
| State file | Create | Create | Create |
| Output format | Simplified report | report | report |

### 2.3 Gathering Mode Description

| Mode | Content Gathered |
|------|------------------|
| `project-structure` | File statistics, module structure, key files, core symbols |
| `dependencies` | Symbol location, reference locations, call context, impact assessment |
| `code-patterns` | Match statistics, detailed list, pattern analysis, usage suggestions |
| `impact` | Direct reference points, indirect impact, risk assessment, modification suggestions |

### 2.4 Execution Mode Selection

**First AskUserQuestion: Execution Mode Selection**

```
Question: Execution mode
- Quick mode: Main process direct gathering, no agent invocation (suitable for single file or small scope analysis, ~2 minutes)
- Auto mode (recommended): Use recommended options, reduce interaction
- Interactive mode: Every option requires confirmation
```

**Second AskUserQuestion: Gathering Config (Interactive Mode Only)**

If user selects **Interactive Mode**, ask for gathering configuration:

```
Question 1: Gathering mode
- project-structure: Project structure analysis
- dependencies: Dependency relationship mapping
- code-patterns: Code pattern search
- impact: Modification impact analysis

Question 2: Analysis depth
- normal (recommended): Standard analysis
- deep: Deep analysis, more detailed

Question 3: Analysis scope
- all (recommended): Entire project
- specific: Specified directory/file
```

**Auto Mode Behavior** (skip second AskUserQuestion):
- Gathering mode: Smart inference based on user task description (default: project-structure if not specified)
- Analysis depth: normal
- Analysis scope: all

**Quick Mode Behavior** (skip second AskUserQuestion):
- Gathering mode: Smart inference based on user task description
- Analysis depth: normal
- Analysis scope: all
- Information gathering: Main process direct analysis (no gatherer agent invocation)
- State file: Create

**Note**: If user has specified parameters (e.g., `/gather dependencies UserAPI --deep`), skip all questions.

---

### 2.5 Quick Mode Flow (--quick)

**Applicable Scenarios**:
- Analyzing 1-3 files
- Quick understanding of specific symbols or patterns

**Flow**:
```
Confirm mode → Create state file → Main process direct analysis → Update state → Simplified report
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
  "task": "<user-task>",
  "status": "in_progress",
  "currentStage": "quick_gather",
  "config": { "mode": "quick" }
}' > .claude/orchestrate/.state/<task-id>.json
```

**Step Q3: Main Process Direct Analysis**
```
Main process allowed to use Grep/Glob/Read/LSP for direct analysis (≤5 tool calls)
Directly gather target information without invoking gatherer agent
```

**Step Q4: Output Simplified Report**
```markdown
# Quick Gathering Complete

**Execution ID**: <task-id>
**State File**: .claude/orchestrate/.state/<task-id>.json
**Mode**: [gathering mode]
**Target**: [target symbol/pattern]
**Statistics**: [key numbers]

**Core Findings**:
- [Finding 1]
- [Finding 2]

[If deep analysis needed] Suggestion: Use auto mode `/gather <target>`
```

**Quick Mode Risk Notes**:
- Skips deep dependency analysis, may miss indirect references
- If analysis is insufficient, suggest user switch to auto mode

---

### 2.6 Standard Mode Execution Steps

**Step 1: Phased Option Confirmation**

(See 2.4 Execution Mode Selection)

**Step 2: Invoke information-gatherer**
```
Task(subagent_type="atlas:information-gatherer", model="haiku")
prompt: |
  Task ID: <mode>-<target>-<date>
  Gathering mode: [selected mode]
  Target: [symbol name/pattern/directory]
  Scope: [all/specified path]
  Depth: [normal/deep]
  Output directory: .claude/gather/<task-id>/
```

**Step 3: Output Summary**

---

## III. Key Details

### 3.1 Main Process Responsibilities

**Allowed**: AskUserQuestion / Task invocation / Output summary

**Prohibited**: Read/Grep/Glob to read code / Direct analysis / Modify files

### 3.2 Project Knowledge Base

Prioritize retrieving existing information from `.claude/repowiki/`:

| File | Purpose |
|------|---------|
| `project.pkg.json` | Project metadata, tech stack |
| `modules.pkg.json` | Module structure, dependencies |
| `symbols.pkg.json` | Symbol index |

The gatherer will automatically check and reuse these files.

### 3.3 Output Format

```markdown
📊 Information Gathering Complete

**Mode**: [gathering mode]
**Target**: [target symbol/pattern]
**Statistics**: [key numbers]

**Core Findings**:
- [Finding 1]
- [Finding 2]

💾 **Detailed Report**: .claude/gather/<task-id>/report.md

🔜 **Next Steps**: For batch modifications, use /orchestrate
```

---

## IV. Examples

### Example 1: Quick Mode (~2 minutes)

```
User: /gather dependencies UserAPI --quick

1. Select quick mode → Skip all subsequent questions
2. Main process quick location:
   - LSP findReferences "UserAPI" → Locate src/api/UserAPI.ts
   - Grep "UserAPI" → Scan reference points
   - Analyze call context (≤5 tool calls)
3. Output simplified report: 23 reference points, 8 files
4. Hint: For deep analysis, use `/gather dependencies UserAPI`
```

### Example 2: Auto Mode - Project Structure Analysis

```
User: /gather project-structure

1. Select auto mode → Use recommended config (normal depth + all scope)
2. Gatherer(haiku): Execute project structure analysis
   - Glob "**/*.{ts,tsx}" → Count file distribution
   - LSP documentSymbol → Extract core symbols
   - Analyze module dependencies
3. Output: .claude/gather/project-structure-20240115/
   - report.md: 156 files, 45 modules, 12 entry points
   - context.json: Structured data (for subsequent commands)
```

### Example 3: Interactive Mode - Dependency Analysis

```
User: /gather dependencies UserAPI

1. Select interactive mode → Confirm config:
   - Gathering mode: dependencies | Depth: deep | Scope: all
2. Gatherer(haiku): Deep analysis of UserAPI dependencies
   - LSP findReferences → 23 direct references
   - LSP incomingCalls → Trace call chain
   - Analyze impact scope and risk level
3. Output: .claude/gather/dependencies-UserAPI-20240115/
   - report.md: 23 reference points, 8 files, 3 high-risk calls
   - context.json: Reference details (file path + line number)
```

### Example 4: Integration with /orchestrate

```
User: /gather dependencies UserAPI
      /orchestrate update all UserAPI calls

1. /gather output: .claude/gather/dependencies-UserAPI-20240115/context.json
2. /orchestrate auto-reads context.json → Skip redundant gathering
3. Planner generates plan based on existing data → Save ~5 minutes
```

---

## V. Core Constraints

### Standard Mode Must Do

- ✅ **Step 1**: First confirm execution mode (quick/auto/interactive)
- ✅ **Step 1**: Auto mode skips second AskUserQuestion, uses recommended config
- ✅ **Step 1**: Interactive mode requires confirmation of all gathering config
- ✅ **Step 1**: Skip all questions when parameters are fully specified
- ✅ Use gatherer agent to execute gathering
- ✅ Output includes file paths and line numbers
- ✅ Write results to `.claude/gather/`

### Quick Mode Must Do

- ✅ **Step Q1**: Confirm user selects quick mode
- ✅ **Step Q2**: Create state file
- ✅ **Step Q3**: Main process direct analysis (≤5 tool calls)
- ✅ **Step Q4**: Output simplified report (including execution ID and state file path)
- ✅ Suggest user switch to auto mode when analysis is insufficient

### Quick Mode Allowed

- ✅ Main process uses Grep/Glob/Read/LSP for direct analysis (≤5 times)
- ✅ Skip gatherer agent invocation

### Prohibited

- ❌ Standard mode main process directly reading code
- ❌ Standard mode main process direct analysis
- ❌ Modifying any files
- ❌ Standard mode skipping gatherer and outputting directly
- ❌ Asking for gathering config in auto mode
- ❌ Using quick mode for complex tasks (>3 files or requiring deep dependency analysis)
