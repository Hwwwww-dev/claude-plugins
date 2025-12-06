---
description: Smart information gathering command. Analyzes project structure, dependency relationships, and code patterns, outputs structured reports.
argument-hint: <analysis target> [--scope path] [--depth N] [--output report|pkg]
---

# /gather - Information Gathering

User input: $ARGUMENTS

---

## Step 1: Confirm Gathering Options

**If user doesn't specify mode, use AskUserQuestion to ask:**

```
Question 1: Gathering mode
- project-structure: Project structure analysis
- dependencies: Dependency relationship mapping
- code-patterns: Code pattern search
- impact: Modification impact analysis

Question 2: Analysis depth
- normal (default): Standard analysis
- deep: Deep analysis, more detailed

Question 3: Analysis scope
- all: Entire project
- specific: Specified directory/file
```

**If user has specified (e.g., `/gather dependencies UserAPI --deep`), skip asking.**

---

## Step 2: Call information-gatherer

**Fixed input structure**:
```
Task(subagent_type="atlas:information-gatherer")
prompt: |
  ## Task
  Task ID: <mode>-<target>-<date>
  Gathering mode: [project-structure / dependencies / code-patterns / impact]

  ## Target
  - Target: [symbol name / pattern / directory]
  - Scope: [entire project / specified path]
  - Depth: [normal / deep]

  ## Gathering Content
  [List specific items to collect based on mode]

  ## Output
  Write to: docs/information/<task-id>.md
  Return: Concise summary to main conversation
```

---

## Gathering Mode Details

| Mode | Gathered Content |
|:-----|:-----------------|
| **project-structure** | File statistics, module structure, key file list, core symbol list |
| **dependencies** | Symbol location, reference locations (file:line), call context, impact assessment |
| **code-patterns** | Match statistics, detailed list (file:line), pattern analysis, usage suggestions |
| **impact** | Direct reference points, indirect impact scope, risk assessment, modification suggestions |

---

## Output Format

**Fixed output structure**:
```markdown
Information gathering complete

## Mode: [gathering mode]
## Target: [target symbol/pattern]
## Statistics: [key numbers]

## Core Findings
- [Finding 1]
- [Finding 2]

Detailed report: docs/information/<task-id>.md

Next suggestion: [Use /orchestrate for batch modifications if needed]
```

---

## Examples

### Basic Usage
```bash
/gather project-structure              # Project structure analysis
/gather dependencies UserAPI           # Dependency analysis
/gather code-patterns "useState"       # Pattern search
/gather impact AuthService             # Impact analysis
```

### Advanced Options
```bash
/gather dependencies LoginComponent --deep
/gather code-patterns "import.*react" --focus src/components
```

---

## Integration with /orchestrate

```bash
# Workflow example
/gather dependencies UserAPI           # 1. Analyze reference points
/orchestrate Update all UserAPI calls  # 2. Batch execute based on gathered results
```

---

## Project Knowledge Base

**Prioritize getting project info from `.claude/repowiki/`** (if exists):

| File | Purpose |
|:-----|:--------|
| `.claude/repowiki/.meta/project.pkg.json` | Project metadata, tech stack, dependencies |
| `.claude/repowiki/.meta/modules.pkg.json` | Module structure, dependency relationships |
| `.claude/repowiki/.meta/api.pkg.json` | API endpoint information |
| `.claude/repowiki/.meta/symbols.pkg.json` | Symbol index |
| `.claude/repowiki/.index/quick-lookup.json` | Quick lookup index |

**Usage**: Check if these files exist before gathering, prioritize reading them to reduce redundant analysis.

---

## Notes

- `/gather` is read-only analysis, doesn't modify code
- Results written to `docs/information/` for later reuse
- All outputs include complete file paths and line numbers
- Prioritize using existing information from `.claude/repowiki/`
