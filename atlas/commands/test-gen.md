---
description: Test generation command. Analyzes code logic and automatically generates unit tests and integration tests, supporting multiple testing frameworks.
argument-hint: [--scope path] [--framework jest|vitest|pytest|go] [--type unit|integration] [--coverage-target N]
---

# Test Generation Command

Analyzes code logic and boundary conditions to automatically generate high-quality test cases.

## Parameters

| Parameter | Description | Default |
|:----------|:------------|:--------|
| `--scope` | Generation scope | . (entire project) |
| `--framework` | Testing framework | Auto-detect |
| `--type` | Test type | unit |
| `--coverage-target` | Target coverage | 80 |

---

## Supported Testing Frameworks

| Framework | Language | Detection Method |
|:----------|:---------|:-----------------|
| Jest | JavaScript/TypeScript | package.json dependencies |
| Vitest | JavaScript/TypeScript | vite.config / vitest.config |
| Mocha | JavaScript/TypeScript | package.json dependencies |
| Pytest | Python | pytest.ini / pyproject.toml |
| Go Test | Go | go.mod exists |
| JUnit | Java | pom.xml / build.gradle |

---

## Execution Flow

Phase 0 Environment Detection → Phase 1 Target Analysis → Phase 1.5 Configuration Selection → Phase 2 Test Case Planning → Phase 3 Test Generation → Phase 4 Validation

### Subagent Assignment

| Phase | Function | Subagent | Description |
|:------|:---------|:---------|:------------|
| 0 | Environment Detection | Main Process | Detect testing framework and existing coverage |
| 1 | Target Analysis | `atlas:information-gatherer` | Analyze target code |
| 1.5 | Configuration Selection | User Selection | First prompt: execution mode + test scope; Second prompt: test configuration (interactive mode only) |
| 2 | Test Case Planning | `atlas:planner` or `Plan` | Plan test cases |
| 3 | Test Generation | `atlas:atlas-executor` | Generate test files in parallel |
| 4 | Validation | Main Process | Run tests, report coverage |

---

## Phase 0: Environment Detection

**Detection Items**: Testing framework type, naming conventions, directory structure, mock libraries, existing coverage

---

## Project Knowledge Base

**Prioritize retrieving project information from `.claude/repowiki/`** (if exists):

| File | Purpose |
|:-----|:--------|
| `.claude/repowiki/.meta/project.pkg.json` | Project configuration, testing framework info |
| `.claude/repowiki/.meta/modules.pkg.json` | Module structure (determine test scope) |
| `.claude/repowiki/.meta/symbols.pkg.json` | Symbol index (function signatures, parameter types) |
| `.claude/repowiki/.meta/api.pkg.json` | API endpoints (for integration tests) |

**Usage**: Check if these files exist before Phase 1 analysis to obtain function signatures and dependency information.

---

## Phase 1: Target Analysis

**Subagent**: `atlas:information-gatherer`

**Analysis Items**: Function signatures, parameter types, branch paths, dependencies, existing test coverage

**PKG Structure**:
```json
{
  "targets": [
    {
      "file": "src/user/user.service.ts",
      "symbol": "UserService",
      "methods": [
        {
          "name": "create",
          "signature": "create(data: CreateUserDto): Promise<User>",
          "branches": [
            {"condition": "email exists", "outcome": "throw ConflictException"},
            {"condition": "validation fails", "outcome": "throw BadRequestException"}
          ],
          "dependencies": ["PrismaService", "HashService"],
          "hasExistingTest": false
        }
      ]
    }
  ],
  "summary": {
    "totalTargets": 15,
    "withoutTests": 7,
    "estimatedNewTests": 25
  }
}
```

---

## Phase 1.5: Configuration Selection

**Prompt user configuration in stages**:

**First AskUserQuestion: Execution Mode and Test Scope**
```
AskUserQuestion(questions=[
  {
    "question": "Execution Mode",
    "header": "Mode",
    "options": [
      {"label": "Auto Mode (Recommended)", "description": "Use recommended options, minimize interaction"},
      {"label": "Interactive Mode", "description": "Confirmation required at each key step"}
    ]
  },
  {
    "question": "Test Scope",
    "header": "Scope",
    "options": [
      {"label": "Entire Project", "description": "Generate tests for all code"},
      {"label": "Specific Directory", "description": "Generate tests only for specified directory"}
    ]
  }
])
```

**Second AskUserQuestion: Test Configuration (Interactive Mode Only)**

If user selected **Interactive Mode**, prompt for test configuration:

```
AskUserQuestion(questions=[
  {
    "question": "Test Type",
    "header": "Type",
    "options": [
      {"label": "Unit Tests (Recommended)", "description": "Test individual functions and classes"},
      {"label": "Integration Tests", "description": "Test interactions between modules"}
    ]
  },
  {
    "question": "Testing Framework",
    "header": "Framework",
    "options": [
      {"label": "Auto-detect (Recommended)", "description": "Automatically select based on project configuration"},
      {"label": "Jest", "description": "JavaScript/TypeScript"},
      {"label": "Vitest", "description": "JavaScript/TypeScript (Vite)"},
      {"label": "Pytest", "description": "Python"},
      {"label": "Go Test", "description": "Go"}
    ]
  },
  {
    "question": "Coverage Target",
    "header": "Coverage",
    "options": [
      {"label": "80% (Recommended)", "description": "Standard coverage target"},
      {"label": "90%", "description": "High coverage target"},
      {"label": "100%", "description": "Full coverage"}
    ]
  },
  {
    "question": "Select Test Case Planner",
    "header": "Planner",
    "options": [
      {"label": "atlas:planner (Recommended)", "description": "Trust gatherer output, minimize additional scanning, efficient planning"},
      {"label": "Built-in Plan", "description": "Claude Code built-in planner, will explore and verify independently"}
    ]
  }
])
```

**Auto Mode Behavior** (skip second AskUserQuestion):
- Test Type: Unit Tests
- Testing Framework: Auto-detect
- Coverage Target: 80%
- Planner: atlas:planner

---

## Phase 2: Test Case Planning

**Subagent**: Call the corresponding planner based on user selection

**Core Principle**: Prioritize Phase 1 output, minimize additional reads.

### Option A: atlas:planner (Recommended)

**Features**: Trust gatherer output, plan directly based on existing information, <=3 supplementary reads

```
Task(subagent_type="atlas:planner")
prompt: |
  ## Task
  Generate test case plan for target code

  ## Gatherer Output Location
  `.claude/gather/test-gen-<task-id>/`
  - `context.json`: Target analysis data (function signatures, branch paths, dependencies)

  ## Output Requirements
  Output test case plan in the fixed format defined by planner agent
```

### Option B: Built-in Plan

**Features**: Will explore code independently, suitable for scenarios where gatherer information is insufficient

```
Task(subagent_type="Plan")
prompt: |
  ## Task
  Generate test case plan for target code

  ## Mandatory Information Source (Must Read First)
  **Phase 1 Output**: `.claude/gather/test-gen-<task-id>/`
  - `context.json`: Target analysis data (function signatures, branch paths, dependencies)

  **You Must**:
  1. First read the above files
  2. Plan test cases based on existing signatures and branch information
  3. Only perform supplementary reads in the following cases:
     - Branch conditions unclear (need to check specific logic)
     - Mock targets unclear (need to confirm dependency interfaces)

  ## Information Sufficiency Check
  - [ ] Function signatures and parameter types
  - [ ] Branch path list
  - [ ] Dependencies (mock targets)
  - [ ] Existing test coverage status

  If all 4 items obtained → **Prohibit additional reads**, plan directly
  If missing < 5 items → Targeted supplementation
  If missing 5+ items → Mark gatherer information insufficient, suggest re-collection

  ## Output
  Test case list for each target:
  - Happy path tests
  - Boundary value tests
  - Exception handling tests
  - Mock setup instructions
```

**Test Case Planning Example**:
```markdown
### UserService.create
- [ ] Should successfully create user and return User object
- [ ] Should throw BadRequestException when email is empty
- [ ] Should throw BadRequestException when password length < 8
- [ ] Should throw ConflictException when email already exists
- Mock: PrismaService.user.{create,findUnique}, HashService.hash
```

---

## Phase 3: Test Generation

**Subagent**: `atlas:atlas-executor` (multiple in parallel)

**Generation Strategy**: Group by file and generate in parallel, follow existing project test style

**File Naming Rules**:
| Framework | Source File | Test File |
|:----------|:------------|:----------|
| Jest/Vitest | src/user.service.ts | src/user.service.test.ts or __tests__/user.service.test.ts |
| Pytest | src/user_service.py | tests/test_user_service.py |
| Go | src/user/service.go | src/user/service_test.go |

**Test Structure Requirements**:
- Arrange-Act-Assert pattern
- Descriptive test naming (should/when/then)
- Reasonable mock setup (avoid over-mocking)
- Cover critical boundary values

---

## Phase 4: Validation

**Operations**: Run tests → Collect coverage → Compare with target

**Validation Commands**:
| Framework | Command |
|:----------|:--------|
| Jest | `npx jest --coverage --testPathPattern=<generated tests>` |
| Vitest | `npx vitest run --coverage <generated tests>` |
| Pytest | `pytest --cov=src <generated tests>` |
| Go | `go test -cover ./...` |

**Report Example**:
```markdown
### Execution Results
- Tests Passed: 25/25
- Execution Time: 3.2s

### Coverage Changes
| Metric | Before | After | Change |
|:-------|:-------|:------|:-------|
| Line Coverage | 65% | 82% | +17% |
| Branch Coverage | 58% | 75% | +17% |

### Target Achievement
- Target: 80% | Current: 82% | Achieved
```

---

## Constraints

**Generation Constraints**:
- Only generate tests for public methods/functions
- Do not modify existing tests (unless explicitly requested)
- Follow existing project test style
- Use project's existing mock libraries

**Quality Constraints**:
- Each test must have Arrange-Act-Assert structure
- Test names must describe expected behavior
- Mock setup must be reasonable (avoid over-mocking)
- Boundary value tests must cover critical boundaries

**Execution Constraints**:
- Phase 1 must use information-gatherer (model="haiku")
- Phase 1.5 first AskUserQuestion must prompt for execution mode and test scope
- Phase 1.5 second AskUserQuestion only prompts for test configuration in interactive mode (test type, framework, coverage, planner)
- Phase 1.5 auto mode uses recommended options (unit tests, auto-detect framework, 80% coverage, atlas:planner)
- Phase 2 must use the selected planner
- Phase 3 must use atlas-executor (prompt user to select model in interactive mode, use sonnet in auto mode)

---

## Examples

### Basic Usage
```bash
# Generate tests for entire project
/atlas:test-gen

# Specify scope
/atlas:test-gen --scope src/services

# Specify framework
/atlas:test-gen --framework vitest

# Generate integration tests
/atlas:test-gen --type integration

# Set coverage target
/atlas:test-gen --coverage-target 90
```

### Output Examples

**Generation Complete**:
```
Test Generation Complete

Generation Statistics:
- New test files: 5
- New test cases: 25
- Methods covered: 15

Test Files:
- __tests__/user.service.test.ts (8 cases)
- __tests__/order.service.test.ts (6 cases)
- __tests__/auth.service.test.ts (5 cases)
- __tests__/payment.service.test.ts (4 cases)
- __tests__/notification.service.test.ts (2 cases)

Coverage Changes:
- Line Coverage: 65% → 82% (+17%)
- Target 80% Achieved

Recommendations:
1. Review generated tests for business logic accuracy
2. Consider adding more boundary case tests
3. Run `npm test` to ensure all tests pass
```

**Partial Failure**:
```
Test Generation Partially Complete

Generation Statistics:
- New test files: 5
- New test cases: 25
- Failed cases: 3

Failure Details:
1. user.service.test.ts:45 - TypeError: Cannot read property 'create' of undefined
   Suggestion: Check PrismaService mock configuration

2. order.service.test.ts:78 - Expected ConflictException but got InternalServerError
   Suggestion: Check exception handling logic

Coverage: 75% (Target 80% not reached)

Recommendations:
1. Fix failed test cases
2. Add tests for missing scenarios
```
