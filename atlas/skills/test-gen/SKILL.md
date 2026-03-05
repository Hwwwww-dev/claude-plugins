---
name: test-gen
description: Automated test generation. Analyzes code logic, generates unit and integration tests. Supports multiple testing frameworks.
version: 1.0.0
color: green
---

# Test Generation Skill

Analyzes code logic and branch conditions, then auto-generates high-quality unit and integration tests.

## Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--scope` | Target path | `.` (whole project) |
| `--framework` | Test framework | Auto-detect |
| `--type` | Test type | unit |
| `--coverage-target` | Coverage target (%) | 80 |

## Supported Frameworks

| Framework | Language | Detection |
|-----------|----------|-----------|
| Jest | JavaScript/TypeScript | `package.json` dependencies |
| Vitest | JavaScript/TypeScript | `vite.config` / `vitest.config` |
| Mocha | JavaScript/TypeScript | `package.json` dependencies |
| Pytest | Python | `pytest.ini` / `pyproject.toml` |
| Go Test | Go | `go.mod` present |
| JUnit | Java | `pom.xml` / `build.gradle` |

## Workflow

Phase 0 → Phase 1 → Phase 1.5 → Phase 2 → Phase 3 → Phase 4

### Subagent Assignments

| Phase | Role | Subagent | Notes |
|-------|------|----------|-------|
| 0 | Environment detection | Main process | Detect framework, naming conventions, existing coverage |
| 1 | Target analysis | `atlas:information-gatherer` | Analyze function signatures, branches, dependencies |
| 1.5 | Configuration | User prompt | Mode + scope (always); type/framework/coverage/planner (interactive only) |
| 2 | Test case planning | `atlas:task-planner` or `Plan` | Generate per-method test case list |
| 3 | Test generation | `atlas:atlas-executor` (parallel) | Write test files |
| 4 | Validation | Main process | Run tests, report coverage |

## Phase 0: Environment Detection

Detect: framework type, file naming convention, test directory structure, mock library, current coverage baseline.

## Project Knowledge Base (Check First)

Before Phase 1, check `.claude/repowiki/.meta/` if it exists:

| File | Purpose |
|------|---------|
| `project.pkg.json` | Project config, framework info |
| `modules.pkg.json` | Module structure for scoping |
| `symbols.pkg.json` | Function signatures and parameter types |
| `api.pkg.json` | API endpoints for integration tests |

## Phase 1: Target Analysis

**Subagent**: `atlas:information-gatherer`

Collects: function signatures, parameter types, branch paths, dependencies, existing test coverage.

**Output PKG schema** (written to `.claude/gather/test-gen-<task-id>/context.json`):
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

## Phase 1.5: Configuration

**AskUserQuestion #1** (always): execution mode + test scope.
- Mode: Auto (recommended) | Interactive
- Scope: Whole project | Specific directory

**AskUserQuestion #2** (interactive mode only): test type, framework, coverage target, planner.
- Type: unit (recommended) | integration
- Framework: auto-detect (recommended) | Jest | Vitest | Pytest | Go Test
- Coverage target: 80% (recommended) | 90% | 100%
- Planner: `atlas:task-planner` (recommended) | built-in `Plan`

**Auto mode defaults**: `type=unit`, framework=auto-detect, coverage=80%, planner=`atlas:task-planner`.

## Phase 2: Test Case Planning

**Principle**: Prioritize Phase 1 output; minimize additional file reads.

- **atlas:task-planner** (recommended): trusts gatherer output, direct planning, max 3 supplemental reads
- **Built-in Plan**: self-explores code; use when gatherer output is insufficient

Planning output example:
```
UserService.create
- [ ] should create user and return User object
- [ ] should throw BadRequestException when email is empty
- [ ] should throw BadRequestException when password length < 8
- [ ] should throw ConflictException when email already exists
- Mock: PrismaService.user.{create,findUnique}, HashService.hash
```

## Phase 3: Test Generation

**Subagent**: `atlas:atlas-executor` (multiple, parallel by file)

**File naming conventions**:
| Framework | Source | Test file |
|-----------|--------|-----------|
| Jest/Vitest | `src/user.service.ts` | `src/user.service.test.ts` or `__tests__/user.service.test.ts` |
| Pytest | `src/user_service.py` | `tests/test_user_service.py` |
| Go | `src/user/service.go` | `src/user/service_test.go` |

**Test structure requirements**: Arrange-Act-Assert, descriptive names (should/when/then), minimal but correct mocks, key boundary values covered.

## Phase 4: Validation

**Validation commands**:
| Framework | Command |
|-----------|---------|
| Jest | `npx jest --coverage --testPathPattern=<generated-tests>` |
| Vitest | `npx vitest run --coverage <generated-tests>` |
| Pytest | `pytest --cov=src <generated-tests>` |
| Go | `go test -cover ./...` |

**Coverage report schema**:
```
Tests passed: 25/25  |  Duration: 3.2s
Line coverage:   65% -> 82% (+17%)
Branch coverage: 58% -> 75% (+17%)
Target: 80% — ACHIEVED
```

## Constraints

**Generation / quality:**
- Only generate tests for public methods and functions
- Do not modify existing tests unless explicitly requested
- Follow project's existing test style and mock library
- Use AAA structure; cover key boundaries and error paths

**Execution:**
- Phase 1 must use `atlas:information-gatherer` (haiku model)
- Phase 1.5 must always ask mode + scope; ask type/framework/coverage/planner only in interactive mode
- Phase 2 uses the planner selected by user
- Phase 3 uses `atlas:atlas-executor`; auto mode uses sonnet, interactive mode asks user for model
