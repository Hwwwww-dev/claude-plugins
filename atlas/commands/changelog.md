---
description: Changelog command. Analyzes git history and automatically generates structured CHANGELOG.md, supporting conventional commits and semantic versioning.
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
| `--dry-run` | Preview only, don't write to file | false |

### Version Auto-Inference Rules

| Change Type | Version Change | Description |
|-------------|----------------|-------------|
| BREAKING CHANGE / "!" | Major (X.0.0) | Breaking changes |
| `feat:` | Minor (x.Y.0) | New features |
| `fix:` / `docs:` / `perf:` | Patch (x.y.Z) | Fixes and optimizations |

### If User Doesn't Specify Options

**Use AskUserQuestion to ask:**

```
Question 1: Output format
- keep-a-changelog: Added/Changed/Fixed/Security (recommended)
- conventional: Features/Bug Fixes/BREAKING CHANGES
- github: GitHub Release style (What's Changed)

Question 2: Version number
- auto: Auto-infer (based on commit types)
- manual: Manually specify (enter X.Y.Z)

Question 3: Analysis range
- last-tag: From previous tag to HEAD
- custom: Custom range (--from X --to Y)

Question 4: Append mode
- append: Append to existing CHANGELOG (preserve history)
- overwrite: Overwrite entire file
```

**If user has specified options (e.g., `/changelog --version 2.0.0 --format conventional`), skip asking.**

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

  ## Collect Content
  1. Commit history (git log --oneline --no-merges)
  2. Commit classification (following conventional commits spec):
     - feat: New features
     - fix: Bug fixes
     - docs: Documentation changes
     - style: Code formatting
     - refactor: Refactoring
     - perf: Performance optimization
     - test: Tests
     - chore: Build/tools
     - BREAKING: Breaking changes (commits containing "!" or `BREAKING CHANGE:`)
  3. Statistics (total commits, file changes, contributors)

  ## Output
  Write to: docs/information/changelog-analysis-<timestamp>.md
  Return: Commit classification results and version inference recommendations
```

**If commits are non-standard (no type prefix)**:
- Try to infer type from commit message content (e.g., contains "add" -> feat, "fix" -> fix)
- Uninferable commits are classified as `Other Changes`

### 2.3 Version Number Inference

**Auto-infer based on commit classification**:

```
Current version: 1.2.3

If BREAKING CHANGE exists: -> 2.0.0 (Major bump)
Else if feat exists: -> 1.3.0 (Minor bump)
Else if fix/docs/perf exists: -> 1.2.4 (Patch bump)
Else: -> Keep 1.2.3 (no release needed)
```

**If user manually specifies `--version`, skip inference and use the specified version.**

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
- Refactored project A (commit hash)
- Optimized performance B (commit hash)

### Fixed
- Fixed Bug #123 (commit hash)
- Fixed memory leak (commit hash)

### Security
- Fixed security vulnerability CVE-XXXX (commit hash)

### Deprecated
- Deprecated old API X (commit hash)

### Removed
- Removed deprecated feature Y (commit hash)
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

### New Features
- Feature description by @username in #PR

### Bug Fixes
- Fix description by @username in #PR

### Documentation
- Documentation update by @username in #PR

### Chores
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
Preview of generated changelog:

------------------------------------
[Generated content]
------------------------------------

Statistics:
- Version: 1.3.0
- Commits: 25
- New features: 8
- Bug fixes: 12
- Others: 5

Tip: Use /changelog without --dry-run parameter to actually write to file
```

**Stop execution, don't write to file.**

### 4.2 Actual Write

**Call atlas:atlas-executor to update file**:

```
Task(subagent_type="atlas:atlas-executor")
prompt: |
  ## Subtask
  Number: #1
  Description: Update CHANGELOG.md file

  ## File
  - <output-path>

  ## Operation
  Mode: <append|overwrite>

  ## Content
  Read: docs/information/changelog-analysis-<timestamp>.md
  Generate format: <keep-a-changelog|conventional|github>

  ## Requirements
  1. If append mode:
     - Insert new version content at file beginning (below title)
     - Preserve all old version records
  2. If overwrite mode:
     - Replace entire file content
  3. Ensure format consistency (heading levels, list format)
```

---

## Step 5: Output Summary

**Fixed output structure**:

```markdown
Changelog generated successfully

## Version Info
- Version: X.Y.Z
- Inference basis: [Major/Minor/Patch] bump based on [BREAKING/feat/fix] commits
- Analysis range: vA.B.C..HEAD (25 commits)

## Change Statistics
- New features: 8
- Bug fixes: 12
- Documentation: 3
- Refactoring: 2

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

### Example 1: Auto-generate (Default Options)

```
User: /changelog

1. Ask user for options:
   - Format: keep-a-changelog
   - Version: auto (inferred as 1.3.0)
   - Range: last-tag (v1.2.3..HEAD)
   - Mode: append

2. Version detection:
   git describe --tags -> v1.2.3

3. Commit analysis:
   git log v1.2.3..HEAD --oneline
   -> 25 commits (8 feat, 12 fix, 5 other)
   -> Version inference: 1.3.0 (Minor bump)

4. Content generation (keep-a-changelog format):
   ## [1.3.0] - 2024-01-15
   ### Added
   - Added user authentication feature
   ...

5. File update (append mode):
   Insert new version content at CHANGELOG.md beginning

6. Output summary
```

### Example 2: Specify Version and Format

```
User: /changelog --version 2.0.0 --format conventional --from v1.5.0

1. Skip asking (parameters specified)

2. Commit analysis:
   git log v1.5.0..HEAD
   -> Found BREAKING CHANGE commits
   -> Verify version 2.0.0 conforms to Major bump spec

3. Content generation (conventional format):
   ## [2.0.0] (2024-01-15)
   ### BREAKING CHANGES
   - Removed old version API...

4. File update and output summary
```

### Example 3: Dry-run Preview

```
User: /changelog --dry-run

1. Execute analysis and content generation

2. Output preview:
   Preview of generated changelog:
   ------------------------------------
   ## [1.3.0] - 2024-01-15
   ...
   ------------------------------------

3. Stop execution, don't write to file
```

---

## Special Scenario Handling

### First Generation (No Existing CHANGELOG)

```
Detection: CHANGELOG.md doesn't exist
Action: Create new file containing:
  - Title: # Changelog
  - Description paragraph: All notable changes...
  - New version content
```

### No Git Tags

```
Detection: git describe --tags fails
Action: Use 0.0.0 as starting point
  -> Analysis range: initial commit..HEAD
  -> Version inference: 0.1.0 (first version)
```

### Non-standard Commits

```
Detection: Commit messages lack conventional commits prefix
Action:
  1. Try smart inference (e.g., "Add feature" -> feat)
  2. Uninferable ones go to "Other Changes" category
  3. Prompt user to use standardized commit format
```

### Version Number Conflict

```
Detection: Specified version already exists in CHANGELOG
Action:
  - Warn user of duplicate version
  - Ask: Overwrite / Use new version number / Cancel
```

---

## Core Constraints

### Must Do
- Strictly follow Semantic Versioning specification
- Analyze all commits, don't miss any changes
- Generated log format maintains consistency
- Append mode must preserve old version content
- Include complete metadata (date, version, commit hash)

### Must Not Do
- Tamper with commit history or messages
- Write to file in dry-run mode
- Skip BREAKING CHANGES warnings
- Infer non-compliant version numbers (e.g., feat -> Major bump)
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
- BREAKING CHANGES must be highlighted in version number and content
- Sensitive information (such as security vulnerability details) should be manually reviewed before release
- Custom templates supported (via `.claude/templates/changelog.md` configuration)
- All git operations are read-only, commit history will not be modified
