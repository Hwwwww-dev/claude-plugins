---
description: Changelog command. Analyzes git history to automatically generate structured CHANGELOG.md, supporting conventional commits and semantic versioning.
argument-hint: [--from tag|commit] [--to tag|commit] [--version X.Y.Z] [--format keep-a-changelog|conventional|github] [--output path]
---

# /changelog - Changelog Generator

User input: $ARGUMENTS

---

## Step 1: Parse Arguments and Confirm Options

### Parameter Table

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--from` | Starting point (tag or commit) | Previous tag |
| `--to` | Ending point (tag or commit) | HEAD |
| `--version` | New version number (X.Y.Z) | Auto-inferred |
| `--format` | Output format | keep-a-changelog |
| `--output` | Output path | CHANGELOG.md |
| `--append` | Append mode (preserve old content) | true |
| `--dry-run` | Preview only, do not write to file | false |

### Version Auto-Inference Rules

| Change Type | Version Change | Description |
|-------------|----------------|-------------|
| BREAKING CHANGE / "!" | Major (X.0.0) | Incompatible changes |
| `feat:` | Minor (x.Y.0) | New features |
| `fix:` / `docs:` / `perf:` | Patch (x.y.Z) | Fixes and optimizations |

### Staged Confirmation Options

**First AskUserQuestion: Execution Mode Selection**

```
Question: Execution mode
- Auto mode (recommended): Use recommended options, minimize interaction
- Interactive mode: Each configuration option requires confirmation
- dry-run: Preview only, do not write to file
```

**Second AskUserQuestion: Generation Configuration (Interactive mode and dry-run only)**

If the user selects **Interactive mode** or **dry-run**, ask about generation configuration:

```
Question 1: Output format
- keep-a-changelog (recommended): Added/Changed/Fixed/Security
- conventional: Features/Bug Fixes/BREAKING CHANGES
- github: GitHub Release style (What's Changed)

Question 2: Version number
- auto (recommended): Auto-infer (based on commit types)
- manual: Manually specify (enter X.Y.Z)

Question 3: Analysis range
- last-tag (recommended): From last tag to HEAD
- custom: Custom range (--from X --to Y)

Question 4: Append mode
- append (recommended): Append to existing CHANGELOG (preserve history)
- overwrite: Overwrite entire file
```

**Auto mode behavior** (skip second AskUserQuestion):
- Output format: keep-a-changelog
- Version number: auto (auto-inferred)
- Analysis range: last-tag (from last tag to HEAD)
- Append mode: append
- Failure handling: Ask user

**Note**:
- If user has specified options via parameters (e.g., `/changelog --version 2.0.0 --format conventional`), skip all questions
- dry-run mode will ask about generation configuration but will not actually write to file

---

## Step 2: Version Detection and Commit Analysis

### 2.1 Detect Current Version

```bash
# Get latest tag
git describe --tags --abbrev=0

# If no tag exists, use 0.0.0 as starting point
```

### 2.2 Analyze Commit History

**Call atlas:commit-analyzer subtask**:

```
Task(subagent_type="atlas:commit-analyzer")
prompt: |
  ## Task
  Task ID: changelog-analysis-<timestamp>
  Analysis range: <from>..<to>

  ## Content to Collect
  1. Commit history (git log --oneline --no-merges)
  2. Commit classification (following conventional commits specification):
     - feat: New features
     - fix: Bug fixes
     - docs: Documentation changes
     - style: Code formatting
     - refactor: Refactoring
     - perf: Performance optimization
     - test: Tests
     - chore: Build/tooling
     - BREAKING: Breaking changes (commits containing "!" or `BREAKING CHANGE:`)
  3. Statistics (total commits, files changed, contributors)

  ## Output
  Write to: docs/information/changelog-analysis-<timestamp>.md
  Return: Commit classification results and version inference suggestions
```

**If commits are non-standard (no type prefix)**:
- Attempt to infer type from commit message content (e.g., contains "add" → feat, "fix" → fix)
- Uninferable commits are categorized as `Other Changes`

### 2.3 Version Number Inference

**Auto-inference based on commit classification**:

```
Current version: 1.2.3

If BREAKING CHANGE exists: → 2.0.0 (Major bump)
Else if feat exists: → 1.3.0 (Minor bump)
Else if fix/docs/perf exists: → 1.2.4 (Patch bump)
Else: → Keep 1.2.3 (no release needed)
```

**If user manually specifies `--version`, skip inference and use the specified version directly.**

---

## Step 3: Change Classification and Content Generation

### 3.1 Generate Content by Format

#### Format: keep-a-changelog

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- New feature 1 (commit hash)
- New feature 2 (commit hash)

### Changed
- Refactor project A (commit hash)
- Optimize performance B (commit hash)

### Fixed
- Fix Bug #123 (commit hash)
- Fix memory leak (commit hash)

### Security
- Fix security vulnerability CVE-XXXX (commit hash)

### Deprecated
- Deprecate old API X (commit hash)

### Removed
- Remove deprecated feature Y (commit hash)
```

#### Format: conventional

```markdown
## [X.Y.Z] (YYYY-MM-DD)

### Features
- **scope**: Feature description (commit hash)
- Feature description 2 (commit hash)

### Bug Fixes
- **scope**: Fix description (commit hash)

### Performance Improvements
- Performance optimization description (commit hash)

### BREAKING CHANGES
- Breaking change description (commit hash)
```

#### Format: github

```markdown
## What's Changed

### 🚀 New Features
- Feature description by @username in #PR

### 🐛 Bug Fixes
- Fix description by @username in #PR

### 📚 Documentation
- Documentation update by @username in #PR

### 🏗️ Chores
- Dependency update by @username in #PR

**Full Changelog**: https://github.com/owner/repo/compare/v1.2.3...v1.3.0
```

### 3.2 Include Contributors List

```markdown
### Contributors
- @user1 (5 commits)
- @user2 (3 commits)
- @user3 (1 commit)
```

---

## Step 4: File Update

### 4.1 Dry-run Mode

**If `--dry-run` is specified**:
```markdown
📄 Preview of generated changelog:

────────────────────────────────────
[Generated content]
────────────────────────────────────

📊 Statistics:
- Version: 1.3.0
- Commits: 25
- New features: 8
- Bug fixes: 12
- Other: 5

💡 Tip: Use /changelog without --dry-run parameter to actually write to file
```

**Stop execution, do not write to file.**

### 4.2 Actual Write

**Call atlas:atlas-executor to perform file update** (ask user to select model):

```
Task(subagent_type="atlas:atlas-executor", model=user_selection)
prompt: |
  ## Subtask
  Number: #1
  Description: Update CHANGELOG.md file

  ## Files
  - <output-path>

  ## Operation
  Mode: <append|overwrite>

  ## Content
  Read from: docs/information/changelog-analysis-<timestamp>.md
  Generation format: <keep-a-changelog|conventional|github>

  ## Requirements
  1. If append mode:
     - Insert new version content at the beginning of file (below the title)
     - Preserve all old version records
  2. If overwrite mode:
     - Replace entire file content
  3. Ensure format consistency (heading levels, list formatting)
```

---

## Step 5: Output Summary

**Fixed output structure**:

```markdown
✅ Changelog generated

## Version Information
- Version: X.Y.Z
- Inference basis: [Major/Minor/Patch] bump based on [BREAKING/feat/fix] commits
- Analysis range: vA.B.C..HEAD (25 commits)

## Change Statistics
- 🚀 New features: 8
- 🐛 Bug fixes: 12
- 📚 Documentation: 3
- ♻️ Refactoring: 2

## File Location
- Output file: CHANGELOG.md
- Format: keep-a-changelog
- Mode: append (old versions preserved)

## Next Steps
1. Review changes: `cat CHANGELOG.md | head -50`
2. Commit changes: `git add CHANGELOG.md && git commit -m "docs: update changelog for vX.Y.Z"`
3. Create tag: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
4. Push to remote: `git push origin main --tags`
```

---

## Execution Examples

### Example 1: Auto Generation (Auto Mode)

```
User: /changelog

1. First AskUserQuestion - Execution mode:
   - Execution mode: Auto mode (recommended) ✓

   [Auto use recommended configuration, skip second AskUserQuestion]
   - Format: keep-a-changelog
   - Version: auto (inferred as 1.3.0)
   - Range: last-tag (v1.2.3..HEAD)
   - Mode: append

2. Version detection:
   git describe --tags → v1.2.3

3. Commit analysis:
   git log v1.2.3..HEAD --oneline
   → 25 commits (8 feat, 12 fix, 5 other)
   → Version inference: 1.3.0 (Minor bump)

4. Content generation (keep-a-changelog format):
   ## [1.3.0] - 2024-01-15
   ### Added
   - Add user authentication feature
   ...

5. File update (append mode):
   Insert new version content at the beginning of CHANGELOG.md

6. Output summary
```

### Example 2: Interactive Mode

```
User: /changelog

1. First AskUserQuestion - Execution mode:
   - Execution mode: Interactive mode ✓

2. Second AskUserQuestion - Generation configuration:
   - Output format: conventional ✓
   - Version number: manual ✓
   - Analysis range: custom ✓
   - Append mode: append ✓

3. User input:
   - Version number: 2.0.0
   - Starting point: v1.5.0
   - Ending point: HEAD

4. Commit analysis:
   git log v1.5.0..HEAD
   → Found BREAKING CHANGE commits
   → Verify version 2.0.0 conforms to Major bump specification

5. Content generation (conventional format):
   ## [2.0.0] (2024-01-15)
   ### BREAKING CHANGES
   - Remove legacy API...

6. File update and output summary
```

### Example 3: Specified Parameters (Skip All Questions)

```
User: /changelog --version 2.0.0 --format conventional --from v1.5.0

1. Skip all questions (parameters already specified)

2. Commit analysis:
   git log v1.5.0..HEAD
   → Found BREAKING CHANGE commits
   → Verify version 2.0.0 conforms to Major bump specification

3. Content generation (conventional format):
   ## [2.0.0] (2024-01-15)
   ### BREAKING CHANGES
   - Remove legacy API...

4. File update and output summary
```

### Example 4: Dry-run Preview

```
User: /changelog --dry-run

1. First AskUserQuestion - Execution mode:
   - Execution mode: dry-run ✓

2. Second AskUserQuestion - Generation configuration:
   - Output format: keep-a-changelog ✓
   - Version number: auto ✓
   - Analysis range: last-tag ✓

3. Execute analysis and content generation

4. Output preview:
   📄 Preview of generated changelog:
   ────────────────────────────────────
   ## [1.3.0] - 2024-01-15
   ...
   ────────────────────────────────────

3. Stop execution, do not write to file
```

---

## Special Scenario Handling

### First Generation (No Existing CHANGELOG)

```
Detection: CHANGELOG.md does not exist
Action: Create new file containing:
  - Title: # Changelog
  - Description paragraph: All notable changes...
  - New version content
```

### No Git Tags

```
Detection: git describe --tags fails
Action: Use 0.0.0 as starting point
  → Analysis range: Initial commit..HEAD
  → Inferred version: 0.1.0 (first version)
```

### Non-Standard Commits

```
Detection: Commit messages lack conventional commits prefix
Action:
  1. Attempt smart inference (e.g., "Add feature" → feat)
  2. Uninferable commits go into "Other Changes" category
  3. Prompt user to use standard commit format
```

### Version Number Conflict

```
Detection: Specified version number already exists in CHANGELOG
Action:
  - Warn user about duplicate version number
  - Ask: Overwrite / Use new version number / Cancel
```

---

## Core Constraints

### Must Do
- Strictly follow Semantic Versioning specification
- Analyze all commits, do not miss any changes
- Maintain consistency in generated log format
- Append mode must preserve old version content
- Include complete metadata (date, version, commit hash)

### Must Not Do
- Tamper with commit history or commit messages
- Write to file in dry-run mode
- Skip BREAKING CHANGES warnings
- Infer non-compliant version numbers (e.g., feat → Major bump)
- Overwrite user's manually edited custom content (identify and preserve)

---

## Integration with Other Commands

```bash
# Workflow example

# 1. Generate changelog
/changelog --version 2.1.0

# 2. Review content
cat CHANGELOG.md | head -100

# 3. Batch update version numbers (if needed)
/orchestrate Update version number to 2.1.0 in all package.json files

# 4. Commit and release
git add .
git commit -m "chore: release v2.1.0"
git tag -a v2.1.0 -m "Release v2.1.0"
git push origin main --tags
```

---

## Output File Examples

### Keep-a-Changelog Format

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2024-01-15

### Added
- User authentication system with JWT support (a1b2c3d)
- Dark mode toggle in settings page (e4f5g6h)
- Export data to CSV functionality (i7j8k9l)

### Changed
- Refactor API client to use axios instead of fetch (m0n1o2p)
- Update UI library to v5.2.0 (q3r4s5t)

### Fixed
- Fix memory leak in WebSocket connection (u6v7w8x)
- Resolve race condition in payment processing (y9z0a1b)

### Security
- Patch XSS vulnerability in comment rendering (c2d3e4f)

## [1.2.3] - 2023-12-10

...
```

### Conventional Commits Format

```markdown
# Changelog

## [1.3.0] (2024-01-15)

### Features
- **auth**: add JWT-based authentication (a1b2c3d)
- **ui**: implement dark mode toggle (e4f5g6h)
- **export**: support CSV data export (i7j8k9l)

### Bug Fixes
- **websocket**: fix memory leak on disconnect (u6v7w8x)
- **payment**: resolve race condition (y9z0a1b)

### Performance Improvements
- **api**: optimize database query caching (g7h8i9j)

## [1.2.3] (2023-12-10)

...
```

---

## Notes

- Generated logs may require manual review (especially for non-standard commits)
- BREAKING CHANGES must be prominently displayed in both version number and content
- Sensitive information (such as security vulnerability details) should be manually reviewed before release
- Custom templates are supported (configure via `.claude/templates/changelog.md`)
- All git operations are read-only and will not modify commit history
