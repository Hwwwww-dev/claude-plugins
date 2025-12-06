---
description: Project health check command. One-click project health diagnosis, integrating code quality, security vulnerabilities, dependency status, and architecture assessment, outputs comprehensive health score and improvement suggestions.
argument-hint: [--scope path] [--quick] [--export json|html] [--ci]
---

# /health - Project Health Check

User input: $ARGUMENTS

---

## Step 1: Confirm Check Options

**If user doesn't specify options, use AskUserQuestion to ask:**

```
Question 1: Check mode
- full (default): Complete check (5 dimensions)
- quick: Quick check (security and code quality only)
- security: Security check only
- quality: Code quality check only

Question 2: Check scope
- all: Entire project
- scope: Specified directory/module

Question 3: Export format
- markdown (default): Markdown report
- json: JSON format (suitable for CI)
- html: HTML visual report

Question 4: CI mode
- no (default): Normal mode
- yes: CI mode (includes threshold checks)
```

**If user has specified (e.g., `/health --quick --scope src/`), skip asking.**

---

## Step 2: Environment Detection (P0)

**Detect if necessary tools are available:**

```bash
# Check git repository
git rev-parse --is-inside-work-tree 2>/dev/null

# Check package.json (Node.js project)
test -f package.json

# Check common security tools
command -v npm audit 2>/dev/null
command -v yarn audit 2>/dev/null
```

**Output environment info:**
```markdown
Environment Detection
- Git repository: Yes
- Project type: Node.js
- Package manager: npm/yarn
- Available tools: npm audit, eslint
```

---

## Step 3: Parallel Scanning (P1)

**Select scanning dimensions based on check mode:**

### Full Mode (5 Dimensions)

**Launch 4 subagents simultaneously for parallel scanning:**

#### Subagent 1: Security Scan
```
Task(subagent_type="atlas:code-reviewer")
prompt: |
  ## Task
  Task ID: health-security-<timestamp>
  Check type: security

  ## Scope
  - Path: <scope>
  - Depth: deep

  ## Check Items
  1. Dependency vulnerability detection:
     - Run: npm audit / yarn audit
     - Detect: High-risk dependencies in package.json
     - Evaluate: CVE vulnerability level

  2. Hardcoded secret scan:
     - Search patterns: API_KEY, SECRET, PASSWORD, TOKEN
     - Detect: .env file leaks
     - Check: Sensitive info in config files

  ## Output
  Write to: .claude/health/.scan/security-<timestamp>.json
  Format:
  {
    "dimension": "security",
    "score": 0-100,
    "weight": 0.30,
    "issues": [
      {
        "severity": "critical|high|medium|low",
        "type": "dependency|hardcoded-secret|config",
        "description": "Issue description",
        "location": "file path:line number",
        "recommendation": "Fix suggestion"
      }
    ],
    "summary": "Brief description"
  }
```

#### Subagent 2: Code Quality Scan
```
Task(subagent_type="atlas:information-gatherer")
prompt: |
  ## Task
  Task ID: health-quality-<timestamp>
  Check type: code-quality

  ## Scope
  - Path: <scope>
  - File types: .js, .ts, .jsx, .tsx

  ## Check Items
  1. Code complexity:
     - Loop nesting depth > 3
     - Function lines > 100
     - File lines > 500

  2. Code coverage (if coverage/ directory exists):
     - Read: coverage/coverage-summary.json
     - Extract: line/branch/function coverage

  3. Issue patterns:
     - TODO/FIXME count
     - console.log remnants
     - Commented out code blocks

  ## Output
  Write to: .claude/health/.scan/quality-<timestamp>.json
  Format same as above, score and weight(0.25)
```

#### Subagent 3: Dependency Health Scan
```
Task(subagent_type="atlas:dependency-analyzer")
prompt: |
  ## Task
  Task ID: health-dependencies-<timestamp>
  Check type: dependency-health

  ## Check Items
  1. Outdated dependencies:
     - Run: npm outdated / yarn outdated
     - Count: major/minor/patch outdated

  2. Dependency conflicts:
     - Detect: Duplicate dependencies in package-lock.json
     - Evaluate: Version inconsistency issues

  3. Dependency size:
     - Count: dependencies count
     - Analyze: Large dependencies (>5MB)

  ## Output
  Write to: .claude/health/.scan/dependencies-<timestamp>.json
  Format same as above, score and weight(0.20)
```

#### Subagent 4: Architecture Quality Scan
```
Task(subagent_type="atlas:code-reviewer")
prompt: |
  ## Task
  Task ID: health-architecture-<timestamp>
  Check type: architecture

  ## Check Items
  1. Circular dependencies:
     - Analyze: Import relationship graph
     - Detect: Circular reference paths

  2. Module coupling:
     - Count: Cross-module reference count
     - Evaluate: High coupling modules (referenced >20 times)

  3. Directory structure:
     - Check: Whether follows conventional directory structure
     - Evaluate: Flat vs nesting depth

  ## Output
  Write to: .claude/health/.scan/architecture-<timestamp>.json
  Format same as above, score and weight(0.15)
```

#### Maintainability Check (Main Process Execution)
```
Quick check directly in main conversation:
1. Documentation coverage:
   - Count: README.md, API docs existence
   - Check: Whether core modules have documentation
2. Naming conventions:
   - Search: Pinyin naming, meaningless variable names
3. Comment quality:
   - Count: Comment lines / code lines

Output: .claude/health/.scan/maintainability-<timestamp>.json
Weight: 0.10
```

### Quick Mode (2 Dimensions)

**Execute Subagent 1 and 2 only (security scan and code quality)**

### Security/Quality Mode (Single Dimension)

**Execute corresponding subagent only**

---

## Step 4: Score Calculation (P2)

**After all scans complete, read all JSON files:**

```bash
cat .claude/health/.scan/security-<timestamp>.json
cat .claude/health/.scan/quality-<timestamp>.json
cat .claude/health/.scan/dependencies-<timestamp>.json
cat .claude/health/.scan/architecture-<timestamp>.json
cat .claude/health/.scan/maintainability-<timestamp>.json
```

**Calculate composite score:**

```
Total = Sum(dimension score x dimension weight)

Example:
security: 75 x 0.30 = 22.5
quality: 80 x 0.25 = 20.0
dependencies: 70 x 0.20 = 14.0
architecture: 85 x 0.15 = 12.75
maintainability: 90 x 0.10 = 9.0
-------------------------------
Total = 78.25 ~ 78 (Grade B)
```

**Grade Mapping:**

| Score | Grade | Status | Description |
|-------|-------|--------|-------------|
| 90-100 | A | Excellent | Production ready, no major issues |
| 80-89 | B | Good | Deployable, some room for improvement |
| 70-79 | C | Average | Needs optimization, moderate issues |
| 60-69 | D | Poor | Not recommended for deployment, many issues |
| <60 | F | Critical | Deployment prohibited, severe issues |

---

## Step 5: Report Generation (P3)

**Create report directory:**
```bash
mkdir -p .claude/health/
```

### Markdown Format (Default)

**Write to file:** `.claude/health/report-<timestamp>.md`

**Report Structure:**
```markdown
# Project Health Check Report

**Check time**: 2024-01-15 14:30:00
**Check mode**: full
**Check scope**: Entire project

---

## Composite Score

### Summary
**Score**: 78 / 100
**Grade**: B (Good)
**Status**: Deployable

### Dimension Scores

| Dimension | Score | Weight | Contribution | Status |
|-----------|-------|--------|--------------|--------|
| Security | 75 | 30% | 22.5 | Average |
| Code Quality | 80 | 25% | 20.0 | Good |
| Dependency Health | 70 | 20% | 14.0 | Average |
| Architecture Quality | 85 | 15% | 12.75 | Good |
| Maintainability | 90 | 10% | 9.0 | Excellent |

---

## Detailed Issues

### Security (75/100)

#### Critical (1)
- **CVE-2023-12345**: lodash dependency has prototype pollution vulnerability
  - Location: package.json:23
  - Suggestion: Upgrade to 4.17.21 or higher

#### High (2)
- **Hardcoded secret**: API_KEY exposed in source code
  - Location: src/config/api.ts:15
  - Suggestion: Migrate to environment variable (.env)

- **Dependency vulnerability**: axios version too low
  - Location: package.json:45
  - Suggestion: Upgrade to 1.6.0+

#### Medium (5)
- TODO comments contain sensitive information
- .env.example missing
- ...

---

### Code Quality (80/100)

#### High (3)
- **Complexity too high**: UserService.handleRequest cyclomatic complexity is 25
  - Location: src/services/user.ts:120-185
  - Suggestion: Split into multiple smaller functions

- **File too large**: components/Dashboard.tsx has 850 lines
  - Location: src/components/Dashboard.tsx
  - Suggestion: Split into multiple sub-components

#### Medium (8)
- 12 console.log remnants
- 45 TODO/FIXME comments
- Test coverage only 65% (recommended >=80%)
- ...

---

### Dependency Health (70/100)

#### High (4)
- **Major version outdated**: react 16.x (latest 18.x)
- **Major version outdated**: webpack 4.x (latest 5.x)
- **Size too large**: moment.js (289KB, suggest replacing with date-fns)
- **Duplicate dependency**: lodash has 3 versions (4.17.19, 4.17.20, 4.17.21)

#### Medium (12)
- 23 minor versions outdated
- 45 patch versions outdated
- ...

---

### Architecture Quality (85/100)

#### Medium (2)
- **Circular dependency**: utils/helpers.ts <-> services/user.ts
  - Path: helpers -> user -> api -> helpers
  - Suggestion: Extract common logic to independent module

- **High coupling**: AuthService referenced by 18 modules
  - Suggestion: Consider dependency injection or interface abstraction

#### Low (5)
- components/ directory nesting depth reaches 5 levels
- Some modules missing index.ts export
- ...

---

### Maintainability (90/100)

#### Good
- README.md is comprehensive
- Core modules have documentation coverage
- Naming conventions are basically consistent

#### Low (3)
- API documentation incomplete (7/12 endpoints missing description)
- 3 pinyin naming instances
- Some comments are outdated
- ...

---

## Improvement Suggestions

### High Priority (Within 2 Weeks)
1. **Security fixes**:
   - Upgrade lodash to 4.17.21+
   - Migrate hardcoded secrets to environment variables
   - Upgrade axios to latest version

2. **Code refactoring**:
   - Simplify UserService.handleRequest complexity
   - Split Dashboard.tsx into sub-components

3. **Dependency upgrade**:
   - Upgrade React to 18.x (evaluate compatibility)
   - Replace moment.js with date-fns (reduce 220KB)

### Medium Priority (1-2 Months)
4. **Test coverage**:
   - Increase test coverage to 80%+
   - Add unit tests for critical business logic

5. **Architecture optimization**:
   - Resolve circular dependency issues
   - Refactor high coupling modules (AuthService)

6. **Dependency cleanup**:
   - Unify lodash versions
   - Clean up unused dependencies (run depcheck)

### Low Priority (Continuous Improvement)
7. **Code cleanup**:
   - Remove console.log and debug code
   - Clean up outdated comments
   - Fix pinyin naming

8. **Documentation improvements**:
   - Complete API documentation
   - Update outdated documentation

---

## CI Integration

**Threshold settings** (recommended):
- Minimum score: 70 (Grade C)
- Critical issues: 0
- High issues: <=3

**CI command**:
```bash
/health --ci --export json

# Or via script check
node scripts/check-health.js
```

**Failure handling**: CI fails when score below threshold, blocking merge

---

## Next Steps

1. **Immediate**: Fix 1 Critical security issue
2. **This week**: Handle 2 High-level code quality issues
3. **This month**: Upgrade major dependencies, resolve circular dependencies
4. **Continuous**: Run `/health` check regularly (recommended weekly)

---

**Report generated**: 2024-01-15 14:30:15
**Next check suggested**: 2024-01-22 (7 days later)

**Quick fix commands**:
```bash
# Upgrade dependencies
npm update lodash axios

# Code cleanup
/orchestrate Remove all console.log

# Test coverage
npm run test:coverage
```
```

### JSON Format (CI Mode)

**Write to file:** `.claude/health/report-<timestamp>.json`

```json
{
  "timestamp": "2024-01-15T14:30:00Z",
  "mode": "full",
  "scope": ".",
  "summary": {
    "score": 78,
    "grade": "B",
    "status": "good",
    "passCI": true
  },
  "dimensions": [
    {
      "name": "security",
      "score": 75,
      "weight": 0.30,
      "contribution": 22.5,
      "status": "warning",
      "issues": {
        "critical": 1,
        "high": 2,
        "medium": 5,
        "low": 3
      }
    },
    {
      "name": "quality",
      "score": 80,
      "weight": 0.25,
      "contribution": 20.0,
      "status": "good",
      "issues": {
        "critical": 0,
        "high": 3,
        "medium": 8,
        "low": 12
      }
    }
    // ... other dimensions
  ],
  "issues": [
    {
      "dimension": "security",
      "severity": "critical",
      "type": "dependency",
      "description": "lodash dependency has CVE-2023-12345 prototype pollution vulnerability",
      "location": "package.json:23",
      "recommendation": "Upgrade to 4.17.21 or higher"
    }
    // ... all issues
  ],
  "recommendations": [
    {
      "priority": "high",
      "category": "security",
      "action": "Upgrade lodash to 4.17.21+",
      "impact": "Fix Critical security vulnerability",
      "effort": "low"
    }
    // ... all recommendations
  ],
  "ci": {
    "threshold": 70,
    "pass": true,
    "blockers": []
  }
}
```

### HTML Format

**Write to file:** `.claude/health/report-<timestamp>.html`

**Contains:**
- Visual score dashboard
- Interactive issue filters
- Trend charts (if historical data available)
- Export buttons (PDF/PNG)

---

## Step 6: CI Check (--ci Mode Only)

**If `--ci` option is specified:**

```bash
# Read JSON report
report=.claude/health/report-<timestamp>.json

# Check thresholds
score=$(jq '.summary.score' $report)
critical=$(jq '[.issues[] | select(.severity=="critical")] | length' $report)
high=$(jq '[.issues[] | select(.severity=="high")] | length' $report)

# CI thresholds (configurable)
MIN_SCORE=70
MAX_CRITICAL=0
MAX_HIGH=3

# Determine pass/fail
if [ $score -lt $MIN_SCORE ]; then
  echo "CI Failed: Score $score < $MIN_SCORE"
  exit 1
fi

if [ $critical -gt $MAX_CRITICAL ]; then
  echo "CI Failed: $critical Critical issues found"
  exit 1
fi

if [ $high -gt $MAX_HIGH ]; then
  echo "CI Warning: $high High issues found (threshold: $MAX_HIGH)"
fi

echo "CI Passed: Health check passed"
```

**CI Output:**
```markdown
Project Health Check CI

Score: 78 >= 70 (Pass)
Critical issues: 0 (Pass)
High issues: 5 (Exceeds threshold 3, Warning)

Status: PASS (Merge allowed, recommend fixing High issues)
```

**If failed:**
```markdown
Project Health Check CI

Score: 58 < 70 (Fail)
Critical issues: 2 (Fail)
High issues: 12 (Fail)

Blockers:
1. lodash CVE-2023-12345
2. Hardcoded API key

Status: FAIL (Merge blocked)
```

---

## Execution Examples

### Example 1: Complete Check

```
User: /health

1. Ask for options (if not specified)
2. Environment detection
3. Parallel launch 4 subagents (security/quality/dependencies/architecture) + main process checks maintainability
4. Wait for all scans to complete
5. Read 5 JSON results
6. Calculate composite score: 78/100 (Grade B)
7. Generate Markdown report: .claude/health/report-20240115-143000.md
8. Output summary + report path
```

### Example 2: Quick Mode

```
User: /health --quick

1. Skip asking
2. Environment detection
3. Parallel launch 2 subagents (security/quality)
4. Calculate score (these two dimensions only)
5. Generate simplified report
```

### Example 3: CI Mode

```
User: /health --ci --export json

1. Environment detection
2. Complete scan (5 dimensions)
3. Generate JSON report
4. Execute CI threshold check
5. Output PASS/FAIL + specific reasons
```

---

## Output Format

**Fixed output structure:**

```markdown
Project Health Check Complete

## Composite Score
**Score**: 78 / 100
**Grade**: B (Good)
**Status**: Deployable

## Dimension Distribution
- Security: 75/100 (Average)
- Code Quality: 80/100 (Good)
- Dependency Health: 70/100 (Average)
- Architecture Quality: 85/100 (Good)
- Maintainability: 90/100 (Excellent)

## Key Issues
- Critical: 1
- High: 7
- Medium: 28

**Full report**: .claude/health/report-20240115-143000.md

## Next Steps
1. Immediate: Fix 1 Critical security issue
2. This week: Handle 2 High-level code quality issues
3. This month: Upgrade major dependencies

**Recommended check frequency**: Weekly
```

---

## Historical Trends (Optional)

**If historical reports exist, show trends:**

```markdown
## Health Trends

| Date | Score | Grade | Change |
|------|-------|-------|--------|
| 2024-01-15 | 78 | B | +5 |
| 2024-01-08 | 73 | C | -2 |
| 2024-01-01 | 75 | C | - |

**Improving**: Security +10, Code Quality +5
**Needs improvement**: Dependency Health -3
```

---

## Parameter Description

| Parameter | Description | Default | Example |
|-----------|-------------|---------|---------|
| --scope | Check scope (directory path) | . | --scope src/ |
| --quick | Quick mode (security and quality only) | false | --quick |
| --export | Export format | markdown | --export json |
| --ci | CI mode (includes threshold check) | false | --ci |

---

## Configuration File (Optional)

**Custom configuration supported:** `.claude/health/config.json`

```json
{
  "thresholds": {
    "minScore": 70,
    "maxCritical": 0,
    "maxHigh": 3
  },
  "weights": {
    "security": 0.30,
    "quality": 0.25,
    "dependencies": 0.20,
    "architecture": 0.15,
    "maintainability": 0.10
  },
  "ignore": {
    "patterns": ["**/node_modules/**", "**/dist/**"],
    "rules": ["console-log", "todo-comments"]
  }
}
```

---

## Core Constraints

**Must Do**:
- Parallel scan multiple dimensions (unless quick/single dimension mode)
- Use fixed JSON output format (for CI parsing)
- Provide specific file paths and line numbers
- Give actionable fix suggestions
- Save historical reports (support trend analysis)

**Must Not Do**:
- Fix issues yourself (diagnosis only, don't modify code)
- Serial scanning (affects efficiency)
- Output incomplete reports (must include all dimensions)
- Ignore CI threshold checks (must execute in --ci mode)

---

## Integration with Other Commands

```bash
# Workflow example
/health                                # 1. Diagnose project health
/gather dependencies <package>         # 2. Analyze impact scope of problem dependency
/orchestrate Upgrade all <package> references    # 3. Batch fix
/health --quick                        # 4. Verify fix effect
```

---

## Notes

- First run may be slow (5-10 minutes), subsequent checks will be faster
- CI mode recommended before each PR merge
- Historical reports retained for 30 days (configurable)
- Large projects (>100k lines) recommend using --quick mode
