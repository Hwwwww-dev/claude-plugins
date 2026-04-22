---
name: gather
description: Intelligent information collection. Analyzes project structure, dependencies, code patterns. Outputs structured report for downstream tasks.
version: 1.0.0
color: green
---

# gather - Information Collection

## Interaction Rules

- **Localization**: Render all `AskUserQuestion` `header`/`question`/`label`/`description` strings in the detected system language. Translate user-facing strings before calling.
- **Batch prompts**: One `AskUserQuestion` with multiple `questions[]`. Merge Step 1 and Step 1b into one call when both apply.
- **No redundant Cancel**: Cancellation is implicit.

## Agents & Tools

### Agent

| Agent | Role | Model | Output |
|-------|------|-------|--------|
| `atlas:information-gatherer` | Execute information collection | haiku | `.claude/gather/<task-id>/` |

### Tools

| Tool | Purpose |
|------|---------|
| `AskUserQuestion` | Confirm collection options |
| `Task` | Invoke subagent |
| `TaskCreate/Update/List/Get` | Task system progress tracking |

### Output Structure

```
gatherer → .claude/gather/<task-id>/
    ├── report.md      # human-readable report
    └── context.json   # structured data (for downstream commands)
```

---

## Mode Comparison

| Step | Quick | Auto | Interactive |
|------|-------|------|-------------|
| Collection mode | inferred | inferred (default: project-structure) | ask user |
| Analysis depth | normal | normal | ask user |
| Analysis scope | all | all | ask user |
| Info collection | **main process directly** | gatherer agent | gatherer agent |
| Progress tracking | **none** | Task system | ask user |
| Output format | simplified report | report | report |

### Progress Tracking Options

| Method | Tools | Best for |
|--------|-------|---------|
| **Task system** | TaskCreate/TaskUpdate/TaskList/TaskGet | Single session, dependency tracking, `/todos` visualization |
| **File state** | `.claude/orchestrate/.state/<task-id>.json` | Cross-session, long tasks, `--resume` support |
| **None** | - | Quick mode simple tasks |

---

## Collection Modes

| Mode | Collects |
|------|---------|
| `project-structure` | File stats, module layout, key files, core symbols |
| `dependencies` | Symbol locations, reference points, call context, impact assessment |
| `code-patterns` | Match counts, detailed list, pattern analysis, usage suggestions |
| `impact` | Direct reference points, indirect effects, risk assessment, change suggestions |

---

## Workflow

### Step 1: Mode Selection (AskUserQuestion #1)

```
- Quick: Main process collects directly, no agent (~2 min, 1-3 files)
- Auto (recommended): Use recommended options, minimal interaction
- Interactive: Confirm each option
```

If arguments are fully specified (e.g. `/gather dependencies UserAPI --deep`), skip all prompts.

### Step 1b: Collection Config (AskUserQuestion #2 — Interactive only)

```
Q1: Progress tracking — Task system (recommended) / file state
Q2: Collection mode — project-structure / dependencies / code-patterns / impact
Q3: Analysis depth — normal (recommended) / deep
Q4: Analysis scope — all (recommended) / specific path
```

**Auto mode defaults** (skip Q2): Task system, mode inferred from task, normal depth, all scope.

---

## Quick Mode Flow (--quick)

**Use case**: 1-3 files, quick lookup of a specific symbol or pattern.

**Flow**: Confirm mode → Main process analyzes (≤5 tool calls) → Simplified report

State file:
```json
{
  "executionId": "<task-id>",
  "timestamp": "<ISO-8601>",
  "task": "<user task>",
  "status": "in_progress",
  "currentStage": "quick_gather",
  "config": {"mode": "quick"}
}
```

Path: `.claude/orchestrate/.state/<task-id>.json`

Main process uses Grep/Glob/Read/LSP directly (≤5 calls). No gatherer agent invoked.

Quick report format:
```markdown
# Quick Gather Complete

**Mode**: [collection mode]
**Target**: [symbol/pattern]
**Stats**: [key numbers]

**Key findings**:
- [finding 1]
- [finding 2]

[If insufficient] Suggestion: Use auto mode `/gather <target>` for deeper analysis
```

**Risk**: May miss indirect references. Switch to standard mode if insufficient.

---

## Standard Mode Flow

### Step 2: Invoke information-gatherer

```
Task(subagent_type="atlas:information-gatherer", model="haiku")
prompt: |
  Task ID: <mode>-<target>-<date>
  Collection mode: [selected mode]
  Target: [symbol/pattern/directory]
  Scope: [all / specific path]
  Depth: [normal/deep]
  Output dir: .claude/gather/<task-id>/
```

Update progress after completion:
- Task system: `TaskUpdate(taskId="gather", status="completed")`
- File state: update `.claude/orchestrate/.state/<task-id>.json`

### Step 3: Output Summary

```markdown
Information collection complete

**Mode**: [collection mode]
**Target**: [symbol/pattern]
**Stats**: [key numbers]

**Key findings**:
- [finding 1]
- [finding 2]

**Detailed report**: .claude/gather/<task-id>/report.md

**Next step**: For batch modifications use /orchestrate
```

---

## Project Knowledge Base

Check `.claude/repowiki/` for existing info before collecting:

| File | Contains |
|------|---------|
| `project.pkg.json` | Project metadata, tech stack |
| `modules.pkg.json` | Module structure, dependencies |
| `symbols.pkg.json` | Symbol index |

The gatherer automatically checks and reuses these files.

---

## Constraints

### Standard Mode — MUST do
- Confirm mode (skip if args fully specified)
- Initialize progress tracking: Task system via `TaskCreate` OR file state via `.claude/orchestrate/.state/<task-id>.json`
- Invoke gatherer agent, write to `.claude/gather/<task-id>/`
- Output includes file paths and line numbers (reuse `.claude/repowiki/` when available)
- Task system: use `TaskUpdate` to mark completion

### Quick Mode — MUST do
- Create state file; main process ≤5 tool calls; brief report
- Suggest auto mode if analysis is insufficient

### Quick Mode — ALLOWED
- Main process uses Grep/Glob/Read/LSP directly (≤5 calls)
- Skip gatherer agent
- Skip progress tracking

### FORBIDDEN
- Standard mode: main process reads/analyzes business code directly
- Standard mode: skip gatherer and output directly
- Modify any files
- Auto mode: ask collection config questions
- Quick mode for complex tasks (>3 files or deep dependency analysis)
- Task system: forget `TaskUpdate` after completion
- File state mode: forget to update state file
