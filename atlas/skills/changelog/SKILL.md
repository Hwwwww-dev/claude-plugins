---
name: changelog
description: Automated changelog generation. Analyzes git history, generates structured CHANGELOG.md with conventional commits and semantic versioning support.
version: 1.0.0
color: blue
---

# Changelog Generation Skill

Analyzes git commit history and generates a structured CHANGELOG.md with semantic versioning support.

## Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--from` | Start point (tag or commit) | Last tag |
| `--to` | End point (tag or commit) | HEAD |
| `--version` | New version number (X.Y.Z) | Auto-inferred |
| `--format` | Output format | keep-a-changelog |
| `--output` | Output path | CHANGELOG.md |
| `--append` | Append mode (preserve old content) | true |
| `--dry-run` | Preview only, no file write | false |

## Version Auto-Inference

| Commit Type | Version Bump | Rule |
|-------------|-------------|------|
| `BREAKING CHANGE` / `!` | Major (X.0.0) | Breaking API change |
| `feat:` | Minor (x.Y.0) | New feature |
| `fix:` / `docs:` / `perf:` | Patch (x.y.Z) | Fix or improvement |

## Execution Mode (AskUserQuestion #1)

- **Auto mode** (recommended): Use defaults, skip further prompts
- **Interactive mode**: Confirm each config option
- **dry-run**: Preview output, no file write

If `--from`/`--version` etc. are already passed as arguments, skip all prompts.

**AskUserQuestion #2** (interactive / dry-run only): format, version, range, append vs overwrite.

Auto mode defaults: `format=keep-a-changelog`, `version=auto`, `range=last-tag`, `mode=append`.

## Workflow

1. **Parse arguments** — detect `--from`, `--to`, `--version`, `--format`, `--dry-run`
2. **Detect current version** — `git describe --tags --abbrev=0`; use `0.0.0` if no tags
3. **Analyze commits** — delegate to `atlas:commit-analyzer`:
   - Classify by conventional type: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`, `BREAKING`
   - Non-conventional commits: infer from message keywords, or group as `Other Changes`
   - Write result to `docs/information/changelog-analysis-<timestamp>.md`
4. **Infer version** — apply bump rules (skip if `--version` specified)
5. **Generate content** — render in selected format (see schemas below)
6. **Write or preview** — append/overwrite file; in dry-run, print preview and stop
7. **Output summary**

## Output Format Schemas

### keep-a-changelog
```markdown
## [X.Y.Z] - YYYY-MM-DD
### Added
- Feature description (commit-hash)
### Changed / Fixed / Security / Deprecated / Removed
- ...
### Contributors
- @user1 (N commits)
```

### conventional
```markdown
## [X.Y.Z] (YYYY-MM-DD)
### Features / Bug Fixes / Performance Improvements / BREAKING CHANGES
- **scope**: description (commit-hash)
```

### github
```markdown
## What's Changed
### New Features / Bug Fixes / Documentation / Chores
- description by @username in #PR
**Full Changelog**: https://github.com/owner/repo/compare/vA.B.C...vX.Y.Z
```

## Subagent Usage

| Phase | Subagent | Task |
|-------|----------|------|
| Commit analysis | `atlas:commit-analyzer` | Classify commits, collect stats |
| File write | `atlas:atlas-executor` | Append/overwrite CHANGELOG.md |

## Special Cases

| Scenario | Handling |
|----------|----------|
| No CHANGELOG.md | Create new file with header + version section |
| No git tags | Use `0.0.0` as base, analyze from initial commit |
| Non-conventional commits | Infer from keywords; unresolvable → `Other Changes` |
| Version conflict | Warn and ask: overwrite / use different version / cancel |

## Constraints

**Must do:**
- Follow Semantic Versioning strictly
- Analyze all commits without omission
- Maintain consistent format (heading levels, list style)
- Preserve all previous version entries in append mode
- Include full metadata: date, version, commit hash

**Forbidden:**
- Modify commit history or commit messages
- Write any file in dry-run mode
- Skip BREAKING CHANGE warnings
- Infer version incorrectly (e.g., feat → Major bump)
- Overwrite user-manually-edited custom sections

## Summary Output Format

```
Changelog generated

Version: X.Y.Z  (Minor bump — based on feat commits)
Range:   vA.B.C..HEAD (25 commits)
Stats:   8 features | 12 fixes | 3 docs | 2 refactors
File:    CHANGELOG.md (append mode)

Next steps:
  git add CHANGELOG.md && git commit -m "docs: update changelog for vX.Y.Z"
  git tag -a vX.Y.Z -m "Release vX.Y.Z" && git push origin main --tags
```
