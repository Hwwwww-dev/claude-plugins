---
description: Project health check command. One-click project health diagnosis integrating code quality, security vulnerabilities, dependency status, and architecture assessment, outputting comprehensive health scores and improvement recommendations.
argument-hint: [--scope path] [--quick] [--export json|html] [--ci]
---

# /health - Project Health Check

User input: $ARGUMENTS

---

## Step 1: Phased Confirmation of Check Options

**If user has specified complete options (e.g., `/health --quick --scope src/ --export json`), skip all prompts.**

**First AskUserQuestion: Execution Mode Selection**

```
Question: Execution Mode
- Auto mode (recommended): Use recommended configuration, complete check of entire project
- Interactive mode: Customize check scope and detailed configuration
```

**Second AskUserQuestion: Check Configuration (Interactive mode only)**

If user selected **Interactive mode**, ask for detailed configuration:

```
Question 1: Check Mode
- full (default): Complete check (5 dimensions)
- quick: Quick check (security and code quality only)
- security: Security check only
- quality: Code quality check only

Question 2: Check Scope
- all (default): Entire project
- scope: Specify directory/module

Question 3: Export Format
- markdown (default): Markdown report
- json: JSON format (suitable for CI)
- html: HTML visual report

Question 4: Report Detail Level
- full (default): Include all issue details
- summary: Summary and key issues only
- minimal: Scores and statistics only

Question 5: CI Mode
- no (default): Normal mode
- yes: CI mode (includes threshold checks)
```

**Auto mode behavior** (skip second AskUserQuestion):
- Check mode: full (complete check of 5 dimensions)
- Check scope: all (entire project)
- Export format: markdown
- Report detail level: full
- CI mode: no
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
🔍 Environment Detection
- Git repository: ✓
- Project type: Node.js
- Package manager: npm/yarn
- Available tools: npm audit, eslint
```

---

## Step 3: Parallel Scanning (P1)

**Select scan dimensions based on check mode:**

### Full Mode (5 dimensions)

**Launch 4 subagents for parallel scanning:**

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
     - Assess: CVE vulnerability levels

  2. Hardcoded secret scanning:
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
Task(subagent_type="atlas:information-gatherer", model="haiku")
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

  3. Problem patterns:
     - TODO/FIXME count
     - Leftover console.log
     - Commented-out code blocks

  ## Output
  Write to: .claude/health/.scan/quality-<timestamp>.json
  Same format as above, score and weight(0.25)
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
     - Assess: Version inconsistency issues

  3. Dependency size:
     - Count: Number of dependencies
     - Analyze: Large dependencies (>5MB)

  ## Output
  Write to: .claude/health/.scan/dependencies-<timestamp>.json
  Same format as above, score and weight(0.20)
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
     - Assess: Highly coupled modules (referenced >20 times)

  3. Directory structure:
     - Check: Whether following conventional directory structure
     - Assess: Flat vs nesting depth

  ## Output
  Write to: .claude/health/.scan/architecture-<timestamp>.json
  Same format as above, score and weight(0.15)
```

#### Maintainability Check (executed in main conversation)
```
Quick check directly in main conversation:
1. Documentation coverage:
   - Count: README.md, API docs existence
   - Check: Whether core modules have documentation
2. Naming conventions:
   - Search: Pinyin naming, meaningless variable names
3. Comment quality:
   - Count: Comment lines / code lines ratio

Output: .claude/health/.scan/maintainability-<timestamp>.json
Weight: 0.10
```

### Quick Mode (2 dimensions)

**Execute only Subagent 1 and 2 (security scan and code quality)**

### Security/Quality Mode (single dimension)

**Execute only the corresponding subagent**

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
Total = Σ (dimension score × dimension weight)

Example:
security: 75 × 0.30 = 22.5
quality: 80 × 0.25 = 20.0
dependencies: 70 × 0.20 = 14.0
architecture: 85 × 0.15 = 12.75
maintainability: 90 × 0.10 = 9.0
-------------------------------
Total = 78.25 ≈ 78 (Grade B)
```

**Grade mapping:**

| Score | Grade | Status | Description |
|-------|-------|--------|-------------|
| 90-100 | A | 🟢 Excellent | Production ready, no major issues |
| 80-89 | B | 🟢 Good | Deployable, minor improvements possible |
| 70-79 | C | 🟡 Fair | Needs optimization, moderate issues |
| 60-69 | D | 🟠 Poor | Not recommended for deployment, many issues |
| <60 | F | 🔴 Critical | Deployment prohibited, severe issues |

---

## Step 5: Report Generation (P3)

**Create report directory:**
```bash
mkdir -p .claude/health/
```

### Markdown Format (default)

**Write to file:** `.claude/health/report-<timestamp>.md`

**Report structure:**
```markdown
# Project Health Check Report

**Check time**: 2024-01-15 14:30:00
**Check mode**: full
**Check scope**: Entire project

---

## Composite Score

### Overall
**Score**: 78 / 100
**Grade**: B (Good)
**Status**: 🟢 Deployable

### Dimension Scores

| Dimension | Score | Weight | Contribution | Status |
|-----------|-------|--------|--------------|--------|
| 🔒 Security | 75 | 30% | 22.5 | 🟡 Fair |
| ⚙️ Code Quality | 80 | 25% | 20.0 | 🟢 Good |
| 📦 Dependency Health | 70 | 20% | 14.0 | 🟡 Fair |
| 🏗️ Architecture Quality | 85 | 15% | 12.75 | 🟢 Good |
| 🔧 Maintainability | 90 | 10% | 9.0 | 🟢 Excellent |

---

## Detailed Issues

### 🔒 Security (75/100)

#### ⚠️ Critical (1)
- **CVE-2023-12345**: lodash dependency has prototype pollution vulnerability
  - Location: package.json:23
  - Recommendation: Upgrade to 4.17.21 or higher

#### ⚠️ High (2)
- **Hardcoded secret**: API_KEY exposed in source code
  - Location: src/config/api.ts:15
  - Recommendation: Migrate to environment variables (.env)

- **Dependency vulnerability**: axios version too low
  - Location: package.json:45
  - Recommendation: Upgrade to 1.6.0+

#### ℹ️ Medium (5)
- TODO comments contain sensitive information
- .env.example missing
- ...

---

### ⚙️ Code Quality (80/100)

#### ⚠️ High (3)
- **Excessive complexity**: UserService.handleRequest cyclomatic complexity is 25
  - Location: src/services/user.ts:120-185
  - Recommendation: Split into multiple smaller functions

- **File too large**: components/Dashboard.tsx has 850 lines
  - Location: src/components/Dashboard.tsx
  - Recommendation: Split into multiple sub-components

#### ℹ️ Medium (8)
- 12 leftover console.log statements
- 45 TODO/FIXME comments
- Test coverage only 65% (recommended ≥80%)
- ...

---

### 📦 Dependency Health (70/100)

#### ⚠️ High (4)
- **Major version outdated**: react 16.x (latest 18.x)
- **Major version outdated**: webpack 4.x (latest 5.x)
- **Oversized**: moment.js (289KB, recommend replacing with date-fns)
- **Duplicate dependency**: lodash has 3 versions (4.17.19, 4.17.20, 4.17.21)

#### ℹ️ Medium (12)
- 23 minor versions outdated
- 45 patch versions outdated
- ...

---

### 🏗️ Architecture Quality (85/100)

#### ⚠️ Medium (2)
- **Circular dependency**: utils/helpers.ts ↔ services/user.ts
  - Path: helpers → user → api → helpers
  - Recommendation: Extract common logic to independent module

- **High coupling**: AuthService referenced by 18 modules
  - Recommendation: Consider dependency injection or interface abstraction

#### ℹ️ Low (5)
- components/ directory nesting depth reaches 5 levels
- Some modules missing index.ts exports
- ...

---

### 🔧 Maintainability (90/100)

#### ✅ Good
- README.md is comprehensive
- Core modules have documentation coverage
- Naming conventions are generally consistent

#### ℹ️ Low (3)
- API documentation incomplete (7/12 endpoints missing descriptions)
- 3 pinyin naming instances (e.g., yonghu, denglu)
- Some comments are outdated
- ...

---

## Improvement Recommendations

### 🎯 High Priority (within 2 weeks)
1. **Security fixes**:
   - Upgrade lodash to 4.17.21+
   - Migrate hardcoded secrets to environment variables
   - Upgrade axios to latest version

2. **Code refactoring**:
   - Simplify UserService.handleRequest complexity
   - Split Dashboard.tsx into sub-components

3. **Dependency upgrades**:
   - Upgrade React to 18.x (assess compatibility)
   - Replace moment.js with date-fns (reduce 220KB)

### 📌 Medium Priority (1-2 months)
4. **Test coverage**:
   - Increase test coverage to 80%+
   - Add unit tests for critical business logic

5. **Architecture optimization**:
   - Resolve circular dependency issues
   - Refactor highly coupled modules (AuthService)

6. **Dependency cleanup**:
   - Unify lodash versions
   - Clean up unused dependencies (run depcheck)

### 💡 Low Priority (continuous improvement)
7. **Code cleanup**:
   - Remove console.log and debug code
   - Clean up outdated comments
   - Fix pinyin naming

8. **Documentation improvement**:
   - Complete API documentation
   - Update outdated documentation

---

## CI Integration

**Threshold settings** (recommended):
- Minimum score: 70 (Grade C)
- Critical issues: 0
- High issues: ≤3

**CI command**:
```bash
/health --ci --export json

# Or check via script
node scripts/check-health.js
```

**Failure handling**: CI fails when score is below threshold, blocking merge

---

## Next Steps

1. **Execute immediately**: Fix 1 Critical security issue
2. **This week's plan**: Address 2 High-level code quality issues
3. **This month's goal**: Upgrade major dependencies, resolve circular dependencies
4. **Continuous improvement**: Run `/health` check regularly (recommended weekly)

---

**Report generated at**: 2024-01-15 14:30:15
**Next check recommended**: 2024-01-22 (7 days later)

**Quick fix commands**:
```bash
# Upgrade dependencies
npm update lodash axios

# Code cleanup
/orchestrate remove all console.log

# Test coverage
npm run test:coverage
```
```

### JSON Format (CI mode)

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

**Includes:**
- Visual score dashboard
- Interactive issue filters
- Trend charts (if historical data exists)
- Export buttons (PDF/PNG)

---

## Step 6: CI Check (--ci mode only)

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
  echo "❌ CI Failed: Score $score < $MIN_SCORE"
  exit 1
fi

if [ $critical -gt $MAX_CRITICAL ]; then
  echo "❌ CI Failed: $critical Critical issues found"
  exit 1
fi

if [ $high -gt $MAX_HIGH ]; then
  echo "⚠️ CI Warning: $high High issues found (threshold: $MAX_HIGH)"
fi

echo "✅ CI Passed: Health check passed"
```

**CI output:**
```markdown
🏥 Project Health Check CI

✅ Score: 78 ≥ 70 (Passed)
✅ Critical issues: 0 (Passed)
⚠️ High issues: 5 (Exceeds threshold 3, Warning)

Status: PASS (Merge allowed, recommend fixing High issues)
```

**If failed:**
```markdown
🏥 Project Health Check CI

❌ Score: 58 < 70 (Failed)
❌ Critical issues: 2 (Failed)
❌ High issues: 12 (Failed)

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
3. Launch 4 subagents for parallel scanning (security/quality/dependencies/architecture) + main conversation checks maintainability
4. Wait for all scans to complete
5. Read 5 JSON results
6. Calculate composite score: 78/100 (Grade B)
7. Generate Markdown report: .claude/health/report-20240115-143000.md
8. Output summary + report path
```

### Example 2: Quick Mode

```
User: /health --quick

1. Skip prompts
2. Environment detection
3. Launch 2 subagents in parallel (security/quality)
4. Calculate score (only these two dimensions)
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
🏥 Project Health Check Complete

## Composite Score
**Score**: 78 / 100
**Grade**: B (Good)
**Status**: 🟢 Deployable

## Dimension Distribution
- 🔒 Security: 75/100 (🟡 Fair)
- ⚙️ Code Quality: 80/100 (🟢 Good)
- 📦 Dependency Health: 70/100 (🟡 Fair)
- 🏗️ Architecture Quality: 85/100 (🟢 Good)
- 🔧 Maintainability: 90/100 (🟢 Excellent)

## Key Issues
- ⚠️ Critical: 1
- ⚠️ High: 7
- ℹ️ Medium: 28

📊 **Full Report**: .claude/health/report-20240115-143000.md

## Next Steps
1. Fix immediately: 1 Critical security issue
2. This week's plan: Address 2 High-level code quality issues
3. This month's goal: Upgrade major dependencies

🔄 **Recommended check frequency**: Weekly
```

---

## Historical Trends (optional)

**If historical reports exist, show trends:**

```markdown
## Health Trends

| Date | Score | Grade | Change |
|------|-------|-------|--------|
| 2024-01-15 | 78 | B | +5 ⬆️ |
| 2024-01-08 | 73 | C | -2 ⬇️ |
| 2024-01-01 | 75 | C | — |

**Improvement areas**: Security +10, Code Quality +5
**Needs improvement**: Dependency Health -3
```

---

## Parameter Reference

| Parameter | Description | Default | Example |
|-----------|-------------|---------|---------|
| --scope | Check scope (directory path) | . | --scope src/ |
| --quick | Quick mode (security and quality only) | false | --quick |
| --export | Export format | markdown | --export json |
| --ci | CI mode (includes threshold checks) | false | --ci |

---

## Configuration File (optional)

**Supports custom configuration:** `.claude/health/config.json`

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

**Must do**:
- Parallel scan multiple dimensions (unless quick/single dimension mode)
- Use fixed JSON output format (for CI parsing)
- Provide specific file paths and line numbers
- Give actionable fix recommendations
- Save historical reports (support trend analysis)

**Must not do**:
- Fix issues yourself (diagnose only, no code modifications)
- Sequential scanning (impacts efficiency)
- Output incomplete reports (must include all dimensions)
- Skip CI threshold checks (must execute in --ci mode)

---

## Integration with Other Commands

```bash
# Workflow example
/health                                # 1. Diagnose project health
/gather dependencies <package>         # 2. Analyze impact scope of problematic dependency
/orchestrate upgrade all <package> references    # 3. Batch fix
/health --quick                        # 4. Verify fix results
```

---

## Chunked Output Specification

**Trigger conditions** (chunk if any condition met):
- Single output exceeds 800 characters
- List exceeds 15 items
- Code block exceeds 30 lines

### Pre-output Confirmation

Confirm the output report contains:
- [ ] Health score
- [ ] Analysis results for each dimension
- [ ] Issue list
- [ ] Improvement recommendations

---

## Notes

- First run may be slow (5-10 minutes), subsequent checks will be faster
- CI mode recommended before each PR merge
- Historical reports retained for 30 days (configurable)
- For large projects (>100k lines), recommend using --quick mode
