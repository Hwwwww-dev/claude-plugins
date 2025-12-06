---
description: Test generation command. Analyzes code logic and automatically generates unit tests and integration tests, supports multiple test frameworks.
argument-hint: [--scope path] [--framework jest|vitest|pytest|go] [--type unit|integration] [--coverage-target N]
---

# Test Generation Command

Analyzes code logic and boundary conditions, automatically generates high-quality test cases.

## Parameters

| Parameter | Description | Default |
|:----------|:------------|:--------|
| `--scope` | Generation scope | . (entire project) |
| `--framework` | Test framework | Auto-detect |
| `--type` | Test type | unit |
| `--coverage-target` | Target coverage | 80 |

---

## Supported Test Frameworks

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

Phase 0 Environment Detection -> Phase 1 Target Analysis -> Phase 2 Test Case Planning -> Phase 3 Test Generation -> Phase 4 Validation

### Subagent Assignment

| Phase | Function | Subagent | Description |
|:------|:---------|:---------|:------------|
| 0 | Environment detection | Main process | Detect test framework and existing coverage |
| 1 | Target analysis | `atlas:information-gatherer` | Analyze target code |
| 2 | Test case planning | `Plan` | Plan test cases |
| 3 | Test generation | `atlas:atlas-executor` | Generate test files in parallel |
| 4 | Validation | Main process | Run tests, report coverage |

---

## Phase 0: Environment Detection

**Detection Content**: Test framework type, naming conventions, directory structure, mock libraries, existing coverage

---

## Project Knowledge Base

**Prioritize getting project info from `.claude/repowiki/`** (if exists):

| File | Purpose |
|:-----|:--------|
| `.claude/repowiki/.meta/project.pkg.json` | Project config, test framework info |
| `.claude/repowiki/.meta/modules.pkg.json` | Module structure (determine test scope) |
| `.claude/repowiki/.meta/symbols.pkg.json` | Symbol index (function signatures, parameter types) |
| `.claude/repowiki/.meta/api.pkg.json` | API endpoints (for integration tests) |

**Usage**: Check if these files exist before Phase 1 analysis, can get function signatures and dependency info.

---

## Phase 1: Target Analysis

**Subagent**: `atlas:information-gatherer`

**Analysis Content**: Function signatures, parameter types, branch paths, dependencies, existing test coverage

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

## Phase 2: Test Case Planning

**Subagent**: `Plan`

**Planning Principles**: Happy path + boundary values + exception handling + mock setup

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

**Generation Strategy**: Group by file and generate in parallel, follow existing test style in project

**File Naming Rules**:
| Framework | Source File | Test File |
|:----------|:------------|:----------|
| Jest/Vitest | src/user.service.ts | src/user.service.test.ts or __tests__/user.service.test.ts |
| Pytest | src/user_service.py | tests/test_user_service.py |
| Go | src/user/service.go | src/user/service_test.go |

**Test Structure Requirements**:
- Arrange-Act-Assert three-section pattern
- Descriptive test naming (should/when/then)
- Reasonable mock setup (don't over-mock)
- Cover key boundary values

---

## Phase 4: Validation

**Operations**: Run tests -> Collect coverage -> Compare with target

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
- Tests passed: 25/25
- Execution time: 3.2s

### Coverage Changes
| Metric | Before | After | Change |
|:-------|:-------|:------|:-------|
| Line coverage | 65% | 82% | +17% |
| Branch coverage | 58% | 75% | +17% |

### Target Achievement
- Target: 80% | Current: 82% | Achieved
```

---

## Constraints

**Generation Constraints**:
- Only generate tests for public methods/functions
- Don't modify existing tests (unless explicitly requested)
- Follow existing test style in project
- Use project's existing mock libraries

**Quality Constraints**:
- Each test must have Arrange-Act-Assert structure
- Test naming must describe expected behavior
- Mock setup must be reasonable (don't over-mock)
- Boundary value tests must cover key boundaries

**Execution Constraints**:
- Phase 1 must use information-gatherer
- Phase 2 must use Plan agent
- Phase 3 must use atlas-executor

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
Test generation complete

Generation Statistics:
- New test files: 5
- New test cases: 25
- Covered methods: 15

Test Files:
- __tests__/user.service.test.ts (8 cases)
- __tests__/order.service.test.ts (6 cases)
- __tests__/auth.service.test.ts (5 cases)
- __tests__/payment.service.test.ts (4 cases)
- __tests__/notification.service.test.ts (2 cases)

Coverage Changes:
- Line coverage: 65% -> 82% (+17%)
- Target 80% Achieved

Suggestions:
1. Review generated tests for business logic accuracy
2. Consider adding more boundary case tests
3. Run `npm test` to ensure all tests pass
```

**Partial Failure**:
```
Test generation partially complete

Generation Statistics:
- New test files: 5
- New test cases: 25
- Failed cases: 3

Failure Details:
1. user.service.test.ts:45 - TypeError: Cannot read property 'create' of undefined
   Suggestion: Check PrismaService mock configuration

2. order.service.test.ts:78 - Expected ConflictException but got InternalServerError
   Suggestion: Check exception handling logic

Coverage: 75% (below target 80%)

Suggestions:
1. Fix failing test cases
2. Add tests for missing scenarios
```
