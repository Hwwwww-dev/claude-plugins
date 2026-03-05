---
name: repo-wiki
description: Autonomous documentation orchestrator. Generates deep structured Repo Wiki with project-to-symbol level analysis and 4-layer validation.
version: 1.0.0
color: pink
---

# Repo Wiki Skill

Multi-phase autonomous orchestrator that generates a deep structured project wiki — from project overview down to symbol level — with 4-layer validation and auto-repair.

## Parameters

| Parameter | Description | Default |
|:----------|:------------|:--------|
| `--force` | Force full rebuild | auto-detect |
| `--lang` | Output language: `zh\|en` | zh |
| `--depth` | Analysis depth (0-3) | 2 |
| `--scope` | Limit analysis path | `.` |
| `--skip-symbols` | Skip symbol extraction | false |
| `--features` | Comma-separated feature list | auto-detect |
| `--mode` | `parallel\|limited\|sequential` | auto-detect |
| `--concurrency` | Max parallel subagents | 2 |
| `--preview` | Analyze only, no file output | false |

## Pipeline Overview

```
P0 Environment → P1 Semantic Diff → P2 Plan → P3 Gather → P4 Generate → P5 Index → P6 Context → P7 Validate+Fix
```

## Configuration

**First prompt**: execution mode (Auto / Interactive / Preview) + doc scope (Full / Core / Minimal / Custom)

**Second prompt** (interactive only): depth / language / symbol analysis / feature points / concurrency

**Auto defaults**: `depth=2`, `lang=zh`, symbols=included, features=auto-detect, `concurrency=2`

**Preview mode**: runs P0-P3 only, outputs preview report, skips P4-P7.

## Subagent Assignment

| Phase | Subagent | Notes |
|:------|:---------|:------|
| P0 | Main process | Create dirs, detect mode and scale |
| P1 | `atlas:repo-semantic-analyzer` | INCREMENTAL only |
| P2 | `Plan` | **Must TodoWrite** execution plan |
| P3 | `atlas:information-gatherer` | Per-collector, follow P2 todos |
| P4 | `atlas:atlas-executor` | Per-document, follow P2 todos |
| P5 | `atlas:repo-context-indexer` | Generate `.index/*.json` |
| P6 | Main process | Generate `wiki-context.json` |
| P7.1 | `atlas:information-gatherer` | 4 validators in parallel |
| P7.3 | `atlas:atlas-executor` | Fix critical issues (≤2 rounds) |
| P7.4 | Main process | Cleanup temp files |

## Parallel Strategy

**Concurrency modes**:

| Mode | Behavior |
|:-----|:---------|
| `parallel` | Maximum concurrency, limited only by task dependencies |
| `limited` | Capped at `--concurrency N` |
| `sequential` | Serial execution (debug only) |

**P3 collection rounds**:
1. `project` + `modules` + `quality` + `api` — parallel (no deps)
2. `symbols` — after `modules` completes

**P4 executor groups** (all independent, run in parallel):

| Executor | Reads PKG | Outputs |
|:---------|:----------|:--------|
| home-arch | project + modules | index.md, architecture/*.md |
| api | api | api/*.md |
| guides | project + quality | guides/*.md, decisions/*.md, quality/*.md |
| symbols | symbols | symbols/*.md |
| features-{name} | project + symbols | features/{name}.md (one per feature) |

**P7.1 validators** (all 4 in parallel, never serial):

| Validator | Scope | Output |
|:----------|:------|:-------|
| V1-docs | Core document completeness | v1-docs.json |
| V2-pkg | PKG data consistency | v2-pkg.json |
| V3-index | Index file integrity | v3-index.json |
| V4-context | wiki-context.json validity | v4-context.json |

## Phase Details

### P0: Environment Detection

Create dirs: `.claude/repowiki/{.meta,.index,.scripts,.tmp,architecture,api,guides,decisions,symbols,quality,features}`

Detect build mode:
- Wiki missing / `--force` / config changed → `FULL_BUILD`
- Code changes only → `INCREMENTAL`

Detect scale: <100 files=full scan | 100-500=sampling | 500-2000=sharded | >2000=require `--scope`

Output: `{mode, fileCount, changedFiles, scale}`

### P1: Semantic Change Detection (INCREMENTAL only)

Subagent `atlas:repo-semantic-analyzer`: `git diff HEAD~1 HEAD` → Serena MCP symbol analysis → identify affected docs.

Output `.meta/semantic-changes.json`:
```json
{
  "timestamp": "...", "changedFiles": ["src/user.ts"],
  "semanticChanges": {
    "newSymbols": [{"type": "function", "name": "validateUser", "module": "user", "file": "src/user.ts"}],
    "modifiedSymbols": [{"type": "class", "name": "OrderService", "change": "method added"}],
    "deletedSymbols": [], "affectedModules": ["user"], "affectedDocs": ["symbols/user-module.md"]
  },
  "impactLevel": "medium"
}
```

### P2: Planning

Subagent `Plan` — **must TodoWrite** with dynamic todos derived from P0/P1 results, `--skip-symbols`, `--features`:

```
Phase 3: [ ] project.pkg.json  [ ] modules.pkg.json  [ ] quality.pkg.json  [ ] api.pkg.json  [ ] symbols.pkg.json
Phase 4: [ ] home+arch docs  [ ] api docs  [ ] guides  [ ] symbols  [ ] features (if detected)
Phase 7: [ ] V1-V4 parallel validation  [ ] validation report
```

### P3: Information Gathering

Subagent `atlas:information-gatherer` (model=haiku), **must follow P2 todos**, mark each completed immediately.

**Zero-fabrication rule**: all data extracted from actual source code only. No guessing, no inference.

**Collectors**:

| Collector | Source | Key Fields |
|:----------|:-------|:-----------|
| project | package.json / README / config | name, version, language, framework, database, tree, dependencies, scripts, envVars, docker, ci |
| modules | dirs + entry files + import analysis | modules[], graph[], cycles[], layers, controllers[], services[], repositories[], patterns[] |
| quality | file stats + AST | totalFiles, totalLines, avgLines, distribution, largeFunctions[], deepNesting[], refactorings[] |
| api | route files (Serena first, fallback Grep) | endpoints[{method,path,handler,controller,auth,middlewares,params,response}], groups[], authStrategies[] |
| symbols | Serena MCP **mandatory** | classes[{name,visibility,extends,implements,properties[],methods[]}], interfaces[], functions[], types[] |

**API extraction by framework**:

| Framework | Search Pattern |
|:----------|:--------------|
| Express/Koa | `router.get/post/put/delete/patch` |
| NestJS | `@Controller/@Get/@Post/@Put/@Delete/@Patch/@UseGuards` |
| Gin | `r.GET/POST/PUT/DELETE` |
| net/http | `http.HandleFunc` |
| FastAPI/Flask | `@app.get/post`, `path()` |

**Symbol collection mandatory flow**:
1. Glob all code files (`**/*.{ts,tsx,js,jsx,py,java,go}`)
2. `get_symbols_overview` per file
3. `find_symbol(depth=1)` per class for method list
4. Write in batches of 50 files, merge at end
5. Validate: file count, class count, method total — shortfall = missing coverage

**PKG Schemas** (all files written to `.claude/repowiki/.meta/`):

`project.pkg.json`:
```json
{
  "metadata": {"name": "...", "version": "...", "description": "...", "license": "...", "author": "...", "repository": "..."},
  "techStack": {"language": "...", "framework": "...", "database": "...", "packageManager": "..."},
  "directory": {"tree": "...", "roles": {"src": "source", "tests": "tests"}, "stats": {"ts": 45}},
  "dependencies": {"production": [{"name": "...", "version": "...", "purpose": "..."}], "development": [...]},
  "build": {"scripts": {"build": "tsc"}, "envVars": ["DATABASE_URL"], "docker": "...", "ci": "..."}
}
```

`modules.pkg.json`:
```json
{
  "modules": [{"name": "...", "path": "...", "entry": "...", "exports": [], "layer": "controller|service|repository|util", "patterns": []}],
  "dependencies": {"graph": "<mermaid>", "cycles": []},
  "layers": {"controllers": [], "services": [], "repositories": []}
}
```

`symbols.pkg.json`:
```json
{
  "modules": {
    "ModuleName": {
      "classes": [{"name": "...", "visibility": "public", "extends": "...", "implements": [], "location": {"file": "...", "line": 0}, "properties": [], "methods": [{"name": "...", "visibility": "public", "params": [], "returns": "void", "description": "..."}]}],
      "interfaces": [], "functions": [], "types": []
    }
  },
  "apiEndpoints": [{"method": "GET", "path": "/api/users", "handler": "...", "auth": true, "params": [], "response": "..."}],
  "stats": {"total": 156, "documented": 142, "coverage": 0.91}
}
```

`quality.pkg.json` / `api.pkg.json`: complexity stats + full endpoint list (see original schemas).

**Each PKG must include** `_meta.generatedAt` timestamp.

### P4: Document Generation

Subagent `atlas:atlas-executor`, **must follow P2 todos**. All content 100% from PKG — never add information not present in PKG. Mark "not detected" when PKG field is empty.

**Conditional generation**:

| Category | Documents | Condition |
|:---------|:----------|:----------|
| Core (always) | index.md, architecture/{overview,structure}.md, guides/development.md | — |
| Conditional | architecture/dependencies.md | dependency config exists |
| Conditional | architecture/{modules,module-graph}.md | ≥2 modules |
| Conditional | architecture/{layers,patterns}.md | layering/patterns detected |
| Conditional | api/*.md | API detected |
| Conditional | guides/build.md | build config exists |
| Conditional | symbols/*.md | `--skip-symbols` not set |
| Conditional | quality/complexity.md | complexity issues detected |
| Open | features/*.md | auto-detected or `--features` |

**Required H2 sections per document**:

| Document | Required Sections |
|:---------|:-----------------|
| index.md | Tech Stack / Quick Start / Navigation (+ timestamp) |
| architecture/overview.md | System Diagram (Mermaid) / Core Modules / Tech Decisions |
| api/endpoints.md | Overview / Endpoint List / Error Codes |
| symbols/index.md | Stats / By Module / Public API |
| quality/complexity.md | File Stats / Large Functions / Deep Nesting / Refactoring Suggestions |
| features/{name}.md | Overview / Core Components / Data Flow / Config |

**File naming**:
- Fixed: `index.md`, `architecture/{overview,structure,dependencies,modules,module-graph,layers,patterns}.md`, `api/{endpoints,types}.md`, `guides/{development,build}.md`, `decisions/adr-log.md`, `quality/complexity.md`
- Dynamic: `symbols/{module}-module.md`, `features/{feature}.md` (kebab-case)
- Forbidden: custom names, Chinese chars, spaces, uppercase

### P5: AI Index Generation

Subagent `atlas:repo-context-indexer` → `.index/*.json`:

`quick-lookup.json`: `{project: {name, tech, entryDocs}, quickSearch: {"SymbolName": {type, file, doc}}}`

`symbol-map.json`: `{classes[], interfaces[], functions[], endpoints[], symbolToDocs: {"ClassName": ["doc.md"]}}`

`doc-graph.json`: `{nodes: [{id, type, weight}], edges: [{from, to, type: "reference"}]}`

### P6: Context Optimization (main process)

Read `.index/*.json`, generate `.claude/wiki-context.json`:

```json
{
  "version": "1.0.0", "timestamp": "...", "projectName": "...", "wikiPath": ".claude/repowiki",
  "entryPoints": [{"path": "index.md", "title": "...", "description": "...", "weight": 10}],
  "quickAccess": {"symbols": ".index/symbol-map.json", "search": ".index/quick-lookup.json", "graph": ".index/doc-graph.json"},
  "metadata": {"totalDocs": 12, "totalSymbols": 58, "coverage": 94, "lastBuildMode": "FULL_BUILD"},
  "contextRules": {"maxDocsPerQuery": 5, "priorityDocs": ["index.md", "architecture/overview.md"], "excludePatterns": ["*.pkg.json"]}
}
```

### P7: Validation and Auto-Repair

#### 7.1 Parallel Validation (4 validators simultaneously, never serial)

| Validator | Subagent | Critical Checks |
|:----------|:---------|:----------------|
| V1-docs | `atlas:information-gatherer` | index.md exists ≥10L / overview.md exists / development.md exists / valid H1+H2 / no TODO/TBD |
| V2-pkg | `atlas:information-gatherer` | project.pkg.json valid / modules match dirs / symbols coverage ≥90% / api endpoints match source |
| V3-index | `atlas:information-gatherer` | quick-lookup.json format valid / symbol refs valid / doc-graph nodes exist / all docs indexed |
| V4-context | `atlas:information-gatherer` | wiki-context.json exists / entryPoints paths valid / quickAccess files exist |

Severity: `critical` (must fix) / `warning` (recommended) / `info` (note only)

#### 7.2 Issue Collection

Merge v1-v4 JSON → `.meta/validation-issues.json`:
```json
{"timestamp": "...", "summary": {"critical": 0, "warning": 2, "info": 1, "passed": 15}, "issues": [{"id": "D1", "severity": "critical", "message": "...", "fix": {"type": "...", "phase": 4, "target": "..."}}], "fixable": true}
```

#### 7.3 Auto-Repair (≤2 rounds)

If critical issues exist:
1. Group by phase → launch `atlas:atlas-executor` in parallel per group
   - Phase 3 issue → re-collect PKG
   - Phase 4 issue → re-generate doc
   - Phase 5 issue → re-generate index
   - Phase 6 issue → re-generate wiki-context.json
2. Re-run P7.1 after fix
3. Repeat if still critical and round < 2
4. After 2 rounds with remaining criticals → flag "requires human intervention"

#### 7.4 Cleanup

```bash
rm -rf .claude/repowiki/.{scripts,tmp}/ && rm -f .claude/repowiki/.meta/v*.json .claude/repowiki/.meta/validation-issues.json
```

**Preserve temp files if human intervention required (for debugging).**

#### 7.5 Final Report

Output `.meta/validation-report.md`: execution summary / V1-V4 results / cleanup status / timestamp.

## Constraints

**Zero-fabrication (highest priority)**:
- All doc content 100% from actual source code
- Forbidden: guessing API paths, class names, param signatures, module structure, config keys
- Mandatory: read source before writing / verify every symbol via Serena MCP or Grep / mark "not detected" rather than guess

**Execution constraints**:
- Phase order is strict — no skipping
- `symbols` collector must wait for `modules`
- PKG files are the sole data medium between phases
- Prioritize Serena MCP over Grep for symbol lookup
- All 4 validators must run in parallel
- After successful validation: delete `.scripts/`, `.tmp/`, `v*.json`, `validation-issues.json`

**Error handling**:
- No git → force FULL_BUILD
- >2000 files without `--scope` → abort with message
- Serena unavailable → fallback to Grep
- Collection failure → skip dependent tasks, continue others
- Executor failure → continue remaining executors
- Critical issues → auto-repair ≤2 rounds

**Forbidden**:
- Skipping validation
- Silent failure on errors
- Placeholder / stub content
- Hardcoded project-specific values
- Custom file names outside the naming spec

## Final Report Format

Must include: execution summary (mode/lang/scope/depth) | generation stats (doc count/lines/symbol coverage/duration) | validation result (all pass / N warnings / N failures) | cleanup status | key document paths | next step (`git add .claude/repowiki && git commit -m "docs: generate repo wiki"`)
