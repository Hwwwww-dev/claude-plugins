---
name: health
description: Project health check. One-click diagnosis of code quality, security vulnerabilities, dependency status, and architecture. Outputs comprehensive health score with improvement suggestions.
version: 1.0.0
color: purple
---

# Health Check Skill

Diagnoses project health across 5 dimensions via parallel subagent scanning, producing a scored report with actionable recommendations.

## Parameters

| Parameter | Description | Default |
|:----------|:------------|:--------|
| `--scope` | Directory to check | `.` |
| `--quick` | Fast mode: security + quality only | false |
| `--export` | Output format: `markdown\|json\|html` | markdown |
| `--ci` | CI mode with threshold enforcement | false |

## Execution Modes

| Mode | Dimensions | Use Case |
|:-----|:-----------|:---------|
| `full` | 5 (security, quality, dependencies, architecture, maintainability) | Default complete check |
| `quick` | 2 (security, quality) | Fast feedback |
| `security` | 1 | Security-only audit |
| `quality` | 1 | Code quality only |

## Workflow

### Step 1: Configuration

If arguments fully specified (e.g. `--quick --scope src/ --export json`), skip all prompts. Otherwise ask: Execution mode — Auto (recommended defaults) or Interactive (custom: check mode / scope / export format / detail level / CI mode).

**Auto defaults**: `mode=full`, `scope=.`, `export=markdown`, `detail=full`, `ci=no`

### Step 2: Environment Detection

Detect git repo, project type (Node.js/etc.), available tools (`npm audit`, `yarn audit`, `eslint`). Output environment summary before scanning.

### Step 3: Parallel Scanning

**Full mode** — launch 4 subagents simultaneously:

| Subagent | Type | Checks | Weight | Output |
|:---------|:-----|:-------|:-------|:-------|
| security | `atlas:code-reviewer` | Dependency CVEs, hardcoded secrets | 0.30 | `.claude/health/.scan/security-<ts>.json` |
| quality | `atlas:information-gatherer` (haiku) | Nesting >3, functions >100L, TODOs | 0.25 | `.claude/health/.scan/quality-<ts>.json` |
| dependencies | `atlas:dependency-analyzer` | Outdated, conflicts, large packages | 0.20 | `.claude/health/.scan/dependencies-<ts>.json` |
| architecture | `atlas:code-reviewer` | Circular deps, high coupling (>20 refs) | 0.15 | `.claude/health/.scan/architecture-<ts>.json` |

**Maintainability** (main process): doc coverage, naming conventions, comment ratio → `.claude/health/.scan/maintainability-<ts>.json` (weight 0.10)

**Quick mode**: subagents 1+2 only. Single-dimension modes: one subagent.

Scan output schema:
```json
{
  "dimension": "security", "score": 0, "weight": 0.30,
  "issues": [
    {"severity": "critical|high|medium|low",
     "type": "dependency|hardcoded-secret|config",
     "description": "...", "location": "file:line", "recommendation": "..."}
  ],
  "summary": "..."
}
```

### Step 4: Score Calculation

`total = Σ (dimension_score × weight)`

| Score | Grade | Status |
|:------|:------|:-------|
| 90-100 | A | Production-ready |
| 80-89 | B | Deployable, minor improvements |
| 70-79 | C | Needs optimization |
| 60-69 | D | Not recommended for deployment |
| <60 | F | Critical issues, block deployment |

### Step 5: Report Generation

**Markdown** (default) → `.claude/health/report-<ts>.md`

```markdown
# Project Health Report
**Time**: <ISO-8601> | **Mode**: <mode> | **Scope**: <scope>

## Overall Score
**Score**: <0-100> | **Grade**: <A-F> | **Status**: <good|warning|bad|fail>

## Dimension Scores
| Dimension | Score | Weight | Contribution | Status |
...

## Critical Issues
- Critical: X | High: Y | Medium: Z | Low: N

## Recommendations (by priority)
- High: fix critical/high severity issues
- Medium: quality/architecture/dependency improvements
- Low: coverage/docs/cleanup
```

**JSON** → `.claude/health/report-<ts>.json`
```json
{
  "timestamp": "...", "mode": "full", "scope": ".",
  "summary": {"score": 78, "grade": "B", "status": "good", "passCI": true},
  "dimensions": [{"name": "security", "score": 75, "weight": 0.3, "contribution": 22.5, "issues": {"critical": 1, "high": 2, "medium": 5, "low": 3}}],
  "issues": [{"dimension": "...", "severity": "critical", "type": "...", "description": "...", "location": "...", "recommendation": "..."}],
  "recommendations": [{"priority": "high", "category": "security", "action": "...", "impact": "...", "effort": "low"}],
  "ci": {"threshold": 70, "pass": true, "blockers": []}
}
```

**HTML** → `.claude/health/report-<ts>.html` — visual dashboard with score gauge, interactive issue filters, trend charts (if history exists).

### Step 6: CI Check (`--ci` only)

Thresholds (configurable via `.claude/health/config.json`): `minScore=70`, `maxCritical=0`, `maxHigh=3`. Exit code 1 if score < minScore or critical > maxCritical. Warn if high > maxHigh.

## History Trend

If prior reports exist, display trend table:

| Date | Score | Grade | Change |
|:-----|:------|:------|:-------|
| YYYY-MM-DD | 78 | B | +5 |

## Optional Config: `.claude/health/config.json`

```json
{
  "thresholds": {"minScore": 70, "maxCritical": 0, "maxHigh": 3},
  "weights": {"security": 0.3, "quality": 0.25, "dependencies": 0.2, "architecture": 0.15, "maintainability": 0.1},
  "ignore": {"patterns": ["**/node_modules/**", "**/dist/**"], "rules": ["console-log"]}
}
```

## Constraints

**MUST**:
- Scan dimensions in parallel (unless quick/single-dimension)
- Use fixed JSON schema for scan outputs (CI-parseable)
- Include exact file paths and line numbers in issues
- Provide actionable fix recommendations
- Preserve historical reports for trend analysis

**FORBIDDEN**:
- Fixing issues (diagnose only, never modify code)
- Serial scanning (degrades performance)
- Incomplete reports (all active dimensions required)
- Skipping CI threshold check when `--ci` is set
