---
description: Smart refactoring command. Identifies code issues and executes automated refactoring for specific patterns, supports preview and interactive confirmation.
argument-hint: <pattern> [--scope path] [--dry-run] [--interactive]
---

# Smart Refactoring Command

Identifies code issues matching specific patterns and executes automated refactoring.

## Parameters

| Parameter | Description | Default |
|:----------|:------------|:--------|
| `pattern` | Refactoring pattern (required) | - |
| `--scope` | Refactoring scope | . (entire project) |
| `--dry-run` | Preview only, don't actually modify | false |
| `--interactive` | Interactive confirmation one by one | false |

---

## Refactoring Patterns

| Pattern | Description | Detection Criteria | Example |
|:--------|:------------|:-------------------|:--------|
| `extract-method` | Extract long functions into smaller functions | Function body >50 lines | Split processOrder into multiple sub-functions |
| `extract-component` | Extract large components into sub-components | JSX/template >100 lines | Split Dashboard into Header/Content/Sidebar |
| `consolidate-duplicate` | Consolidate duplicate code | Similarity >80%, >=3 occurrences | Extract common function |
| `modernize-js` | JavaScript modernization | var/callback/legacy syntax | var->const, callback->async/await |
| `add-types` | Add TypeScript types | any/missing types | any->concrete types, add interface definitions |
| `rename-convention` | Unify naming conventions | Inconsistent naming | snake_case->camelCase |
| `simplify-conditions` | Simplify conditional logic | Complex if-else | Early return, ternary expressions |
| `remove-dead-code` | Remove dead code | Unused exports/variables | Delete unreferenced code |

---

## Execution Flow

Phase 0 Pattern Parsing -> Phase 1 Candidate Identification -> Phase 2 Planning -> Phase 3 Execute/Preview -> Phase 4 Validation

### Subagent Assignment

| Phase | Function | Subagent | Description |
|:------|:---------|:---------|:------------|
| 0 | Pattern parsing | Main process | Validate pattern validity |
| 1 | Candidate identification | `atlas:information-gatherer` | Scan code matching pattern |
| 2 | Planning | `Plan` | Generate refactoring plan |
| 3 | Execution | `atlas:atlas-executor` | Execute refactoring in parallel |
| 4 | Validation | Main process | Run tests/type checks |

---

## Phase 0: Pattern Parsing

**Input**: Command parameters

**Operations**:
1. Validate pattern is a supported pattern
2. Parse --scope to determine scope
3. Record execution options (dry-run/interactive)

**Failure Scenarios**:
- Unknown pattern -> List supported patterns, terminate
- Scope doesn't exist -> Error, terminate

---

## Project Knowledge Base

**Prioritize getting project info from `.claude/repowiki/`** (if exists):

| File | Purpose |
|:-----|:--------|
| `.claude/repowiki/.meta/modules.pkg.json` | Module structure (for dependency analysis) |
| `.claude/repowiki/.meta/symbols.pkg.json` | Symbol index (accelerate candidate identification) |
| `.claude/repowiki/.meta/quality.pkg.json` | Quality analysis (identified problem points) |

**Usage**: Check if these files exist before Phase 1 identification, can accelerate candidate identification process.

---

## Phase 1: Candidate Identification

**Subagent**: `atlas:information-gatherer`

**Input**: Refactoring pattern + scope + `.claude/repowiki/` existing info (if exists)

**Output**: `.claude/refactor/.meta/candidates.pkg.json` - Contains candidate list (id, file, symbol, line, reason, complexity, suggestedSplits)

### Detection Rules for Each Pattern

| Pattern | Detection Criteria | Output Content |
|:--------|:-------------------|:---------------|
| `extract-method` | Function body >50 lines or cyclomatic complexity >10 | Function location, split points, naming suggestions |
| `extract-component` | JSX/template >100 lines or props >10 | Component location, sub-component suggestions, props analysis |
| `consolidate-duplicate` | Similarity >80%, >=3 occurrences | Duplicate location list, similarity, merge suggestions |
| `modernize-js` | Uses var/callback/arguments/with | Legacy syntax locations, modern alternatives |
| `add-types` | any/missing types | Type missing locations, inferred type suggestions |
| `rename-convention` | Naming doesn't follow project conventions | Non-standard naming list, suggested new names |
| `simplify-conditions` | if-else >3 levels or conditions >3 operators | Complex condition locations, simplification suggestions |
| `remove-dead-code` | Unreferenced exports | Dead code locations, reference analysis results |

---

## Phase 2: Planning

**Subagent**: `Plan`

**Input**: `.claude/refactor/.meta/candidates.pkg.json`

**Output**: Refactoring execution plan + TodoWrite todos

**Planning Content**: Sort candidates by dependencies -> Assign subtasks -> Decide execution strategy (parallel/sequential) -> Generate detailed steps

---

## Phase 3: Execute/Preview

### --dry-run Mode
**Executor**: Main process
**Output**: Preview report (don't modify files), show change summary and expected impact

### --interactive Mode
**Executor**: Main process + atlas:atlas-executor
**Flow**: Show change preview one by one -> Ask [Execute/Skip/Terminate] -> Execute based on selection

### Default Mode (Direct Execution)
**Subagent**: `atlas:atlas-executor` (multiple in parallel)

**Execution Strategy**:
- No dependency conflicts: Execute all subtasks in parallel
- Has dependency conflicts: Execute sequentially per dependencies

**Subtask Prompt must include**: Refactoring pattern and rules + Target files and symbols + Candidate details + Code style consistency requirements

---

## Phase 4: Validation

**Executor**: Main process

**Operations**: Detect test framework -> Run related tests -> Run type checks -> Report validation results

**Validation Command Detection**:
| Detection | Command |
|:----------|:--------|
| package.json test script | `npm test` / `yarn test` |
| TypeScript | `tsc --noEmit` |
| ESLint | `eslint --fix` |

---

## Constraints

**Pattern Constraints**:
- Only execute refactoring for specified pattern
- Don't do other optimizations "along the way"
- Maintain existing code style

**Safety Constraints**:
- Record original code before refactoring
- Provide rollback suggestions when validation fails
- Don't modify test files (unless explicitly requested)

**Execution Constraints**:
- Phase 1 must use information-gatherer
- Phase 2 must use Plan agent
- Phase 3 must use atlas-executor (when not dry-run)

---

## Examples

### Basic Usage
```bash
/atlas:refactor extract-method              # Extract long functions
/atlas:refactor extract-method --dry-run    # Preview only
/atlas:refactor extract-method --interactive # Interactive confirmation
/atlas:refactor add-types --scope src/services # Limit scope
/atlas:refactor modernize-js --scope src    # JS modernization
```

### Output Examples

**Preview Mode**:
```
Refactoring Preview
Pattern: extract-method | Scope: src/services | Candidates: 5

Change Preview:
1. processOrder (order.service.ts:45) -> Split into 3 functions
2. handleRegistration (user.service.ts:23) -> Split into 2 functions
...

Expected Impact: Modify 3 files, add 7 private functions
```

**Execution Complete**:
```
Refactoring Complete
Pattern: extract-method | Executed: 5/5 candidates

Modified Files:
- src/order/order.service.ts (+3 functions)
- src/user/user.service.ts (+2 functions)

Validation Results:
- Type check passed
- Tests passed (42/42)
```
