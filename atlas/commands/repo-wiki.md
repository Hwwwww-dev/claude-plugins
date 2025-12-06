---
description: Autonomous documentation orchestrator. Generates deeply structured Repo Wiki, supporting project-level to symbol-level analysis, with 4-layer validation mechanism.
argument-hint: [--force] [--lang zh|en] [--depth N] [--scope path] [--skip-symbols] [--features list] [--mode parallel|limited|sequential] [--concurrency N] [--preview]
---

# Repo Wiki Orchestrator

Generates deeply structured project documentation through multi-phase workflow.

## Parameters

| Parameter | Description | Default |
|:----------|:------------|:--------|
| `--force` | Force full build | Smart detection |
| `--lang` | Output language (zh/en) | zh |
| `--depth` | Analysis depth | 2 |
| `--scope` | Limit analysis scope | . |
| `--skip-symbols` | Skip symbol analysis | false |
| `--features` | Specify features, comma-separated | Auto-detect |
| `--mode` | Execution mode | Auto-detect |
| `--concurrency` | Maximum concurrency | 2 |
| `--preview` | Preview mode, show changes only without writing | false |

---

## Execution Flow

P0 Environment Detection -> P1 Change Detection -> P2 Planning -> P3 Information Gathering -> P4 Document Generation -> P5 Index Generation -> P6 Context Optimization -> P7 Validation and Fix

### Subagent Assignment

| Phase | Subagent | Description |
|:------|:---------|:------------|
| 0 | Main process | Create directories, detect mode and scale |
| 1 | `atlas:repo-semantic-analyzer` | INCREMENTAL mode only |
| 2 | `Plan` | **Must TodoWrite** generate detailed execution plan |
| 3 | `atlas:information-gatherer` | Information gathering (see parallel strategy below) |
| 4 | `atlas:atlas-executor` | Document generation (see parallel strategy below) |
| 5 | `atlas:repo-context-indexer` | Generate .index/*.json |
| 6 | Main process | Generate wiki-context.json |
| 7.1 | `atlas:information-gatherer` | Validation (see parallel strategy below) |
| 7.3 | `atlas:atlas-executor` | Fix critical issues (<=2 rounds) |
| 7.4 | Main process | Clean up temporary files |

### Parallel Strategy (Dynamic Assignment)

**Core Principle**: Tasks without dependencies should be parallel as much as possible, limited by `--concurrency`

**Phase 3 Information Gathering**:
| Collector | Dependencies | Parallel Group |
|:----------|:-------------|:---------------|
| project | None | First round parallel |
| modules | None | First round parallel |
| quality | None | First round parallel |
| api | None | First round parallel |
| symbols | modules | Second round (wait for modules to complete) |

**Phase 4 Document Generation** (can be dynamically split based on detected content):
| Executor | Reads PKG | Output | Parallel |
|:---------|:----------|:-------|:---------|
| home | project | index.md | Yes |
| arch-overview | modules | architecture/overview.md | Yes |
| arch-structure | project | architecture/structure.md | Yes |
| arch-deps | project | architecture/dependencies.md | Yes |
| arch-modules | modules | architecture/modules.md, module-graph.md | Yes |
| arch-layers | modules | architecture/layers.md, patterns.md | Yes |
| api | api | api/*.md | Yes |
| guides | project+quality | guides/*.md, quality/*.md | Yes |
| symbols-index | symbols | symbols/index.md | Yes |
| symbols-{module} | symbols | symbols/{module}-module.md | Yes, one per module |
| features-{name} | project+symbols | features/{name}.md | Yes, one per feature |

**Phase 7.1 Validation**:
| Validator | Validation Scope | Parallel |
|:----------|:-----------------|:---------|
| V1-docs | Core document completeness | Yes |
| V2-PKG | PKG data consistency | Yes |
| V3-index | Index file completeness | Yes |
| V4-context | wiki-context.json | Yes |

**Parallel Mode Control**:
| Mode | Behavior |
|:-----|:---------|
| `--mode parallel` | As parallel as possible, limited only by dependencies |
| `--mode limited` | Limited by `--concurrency N` max parallel count |
| `--mode sequential` | All sequential execution |

**Constraints**: 1. Never mix subagent types 2. P2 must TodoWrite 3. P3/P4 must execute per todos 4. Tasks with dependencies must wait for dependencies to complete

### Data Flow

| Phase | Input | Output | Transfer |
|:------|:------|:-------|:---------|
| 0 | Project directory+git | Environment report (mode/scale) | Memory->P1/P2 |
| 1 | Environment report+git diff | semantic-changes.json | File->P2 |
| 2 | P0/P1 report | Execution plan+Todos | Memory->P3 |
| 3 | P2 plan | *.pkg.json + .scripts/*.py | File->P4 |
| 4 | PKG files | *.md | File->P5 |
| 5 | *.md + PKG | .index/*.json | File->P6 |
| 6 | Index files | wiki-context.json | File->P7 |
| 7.1 | All artifacts | v*.json | File->7.2 |
| 7.2 | v*.json | validation-issues.json | File->7.3 |
| 7.3 | issues | Fixed files | File->7.1 (revalidate) |
| 7.4 | - | Clean up temporary files | Delete |
| 7.5 | Validation results | validation-report.md | File |

**Constraints**: P3/4/5/6/7 read from files, don't depend on memory | P7.4 must clean up `.scripts/` `.tmp/` `v*.json` `validation-issues.json`

---

## Phase 0: Environment Detection

**Operations**: Create directories `.claude/repowiki/{.meta,.index,.scripts,.tmp,architecture,api,guides,decisions,symbols,quality,features}` | Detect mode (Wiki doesn't exist/--force/config change->FULL_BUILD | Code changes only->INCREMENTAL) | Determine scale (<100 full|100-500 sampling|500-2000 sharding|>2000 requires --scope)

**Output** (->P1/P2): `{mode: "FULL_BUILD|INCREMENTAL", fileCount: 150, changedFiles: ["src/user.ts"], scale: "small|medium|large|huge"}`

---

## Phase 1: Semantic Change Detection

**Condition**: INCREMENTAL mode only (skip for FULL_BUILD)

**Subagent**: `atlas:repo-semantic-analyzer`

**Operations**: `git diff HEAD~1 HEAD` to get changes | Serena MCP (`find_symbol`/`find_referencing_symbols`) semantic analysis | Identify added/modified/deleted symbols | Determine list of docs needing update

**Output** (.meta/semantic-changes.json):
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "changedFiles": ["src/user.ts"],
  "semanticChanges": {
    "newSymbols": [{"type": "function", "name": "validateUser", "module": "user", "file": "src/user.ts"}],
    "modifiedSymbols": [{"type": "class", "name": "OrderService", "change": "method added"}],
    "deletedSymbols": [],
    "affectedModules": ["user", "order"],
    "affectedDocs": ["symbols/user-module.md", "api/endpoints.md"]
  },
  "impactLevel": "medium"
}
```

---

## Phase 2: Planning

**Subagent**: `Plan`

**Operations**: Analyze project | **Must TodoWrite** dynamically generate execution plan (adjust based on P0/P1 results, --skip-symbols, --features and other parameters)

**Output**:
1. **TodoWrite**: Detailed todos (P3 collector selection, P4 document types, P7 validation items)
2. **Execution plan**: `{collectors: ["project","modules","quality","symbols"], skipSymbols: false, features: ["auth"], priority: ["src/core"]}`

**Generation Principle**: Dynamically decide based on actual project situation, each todo must be specific, executable and verifiable

**Todos Structure Example** (dynamically generated as needed):
```
Phase 3 - Information Gathering:
- [ ] Collect project metadata -> .meta/project.pkg.json
- [ ] Analyze module structure -> .meta/modules.pkg.json
- [ ] Calculate code quality -> .meta/quality.pkg.json
- [ ] Extract API endpoints -> .meta/api.pkg.json
- [ ] Extract symbol information -> .meta/symbols.pkg.json (if not --skip-symbols)

Phase 4 - Document Generation:
- [ ] Generate homepage and architecture docs (home-arch executor)
- [ ] Generate API docs (api executor)
- [ ] Generate development guides (guides executor)
- [ ] Generate symbol docs (symbols executor)
- [ ] Generate feature docs (if specific features detected or --features)

Phase 7 - Validation:
- [ ] Validate document completeness (V1-V4 parallel)
- [ ] Generate validation report
```

---

## Phase 3: Information Gathering

**Core Principle: Better to collect more than miss, better slow than wrong**

**Subagent**: `atlas:information-gatherer` (**Must execute per P2 todos**, mark completed immediately after each completes)

**Output**: `.meta/{project,modules,quality,api,symbols}.pkg.json`

### Information Gathering Mandatory Rules

**Information Density Principle**:
- If one sentence can explain, don't use two
- Use tables instead of lists when possible
- Use symbols instead of text when possible (Yes/No/-> etc)
- Avoid repeating the same point

**Output Precision Requirements**:
- Data must be precise to specific values, prohibit "several", "multiple" and other vague descriptions
- API endpoints must have complete paths, no ellipsis
- Symbol signatures must be complete, no truncation

**Validation Enhancement**:
- Each PKG file must include `_meta.generatedAt` timestamp
- Each document must include generation timestamp at the end
- Links in documents must be validated immediately after generation

**Zero Speculation Principle (see [Constraints section](#constraints))**:
1. **Depth first** - Each module/symbol must read actual source code
2. **Complete coverage** - Cannot miss any public class, function, interface, API
3. **Multiple validation** - Critical information (especially API endpoints) must be confirmed repeatedly
4. **Source code is truth** - All information extracted from source code, speculation prohibited

**API Endpoint Collection** (Strictest):
- Must scan all route definition files (controller, router)
- Must read decorators/annotations (`@Get()`, `@Post()`, `router.get()` etc)
- Must extract complete route path, HTTP method, handler function
- **Absolutely Prohibited**: 1. Guessing routes from function names 2. Guessing endpoints from file names 3. Assuming standard CRUD routes 4. Making up undefined endpoints

**Symbol Collection** (Zero Omission):
- Must use Serena MCP `find_symbol`/`get_symbols_overview`
- Must read method list for each class (`depth=1`)
- Must extract actual parameter signatures for each function
- **Prohibited**: 1. Guessing signatures from naming conventions 2. Sampling or skipping public/protected symbols 3. Skipping test/mock/generated

**Dependency/Config Collection**:
- Must read `package.json`/`go.mod`/`requirements.txt`
- Must analyze actual import/require statements
- **Prohibited**: Assuming a dependency exists or guessing config item names

### Parallel Gathering Strategy

**Execution Method**: Task tool launches multiple collectors simultaneously

| Collector | Dependencies | Parallelizable | Mode Control |
|:----------|:-------------|:---------------|:-------------|
| project/modules/quality/api | None | Yes | parallel: must be 4 parallel / limited: limited by --concurrency / sequential: serial |
| symbols | modules | No | Starts after modules completes |

**Execute in two rounds**: 1. project+modules+quality+api parallel 2. symbols waits for modules

### Collector Definitions

| Collector | Data Source | Key Fields |
|:----------|:------------|:-----------|
| **project** | package.json/README/config | {name, version, language, runtime, framework, database, tree, dependencies[], scripts, envVars, docker, ci} |
| **modules** | Directory+entry files+import analysis | {modules[], graph[], cycles[], layers, controllers[], services[], repositories[], patterns[]} |
| **quality** | File statistics+AST analysis | {totalFiles, totalLines, avgLines, distribution, largeFunctions[], deepNesting[], refactorings[]} |
| **api** | Route files (Serena priority, fallback to Grep) | {endpoints[{method,path,handler,controller,auth,middlewares,params,response}], groups[], authStrategies[], middlewares[]} |
| **symbols** | Serena MCP **Mandatory** | {classes[{name,module,path,visibility,extends,implements,properties[],methods[]}], interfaces[], functions[{name,params,returns}], types[]} |

### PKG JSON Schema Complete Definition

**project.pkg.json**:
```json
{
  "metadata": {
    "name": "Project name",
    "version": "Version number",
    "description": "Description",
    "license": "License",
    "author": "Author",
    "repository": "Repository URL"
  },
  "techStack": {
    "language": "Primary language",
    "framework": "Framework",
    "database": "Database",
    "packageManager": "Package manager"
  },
  "directory": {
    "tree": "Directory tree structure",
    "roles": {"src": "Source code", "tests": "Tests"},
    "stats": {"ts": 45, "tsx": 23}
  },
  "dependencies": {
    "production": [{"name": "...", "version": "...", "purpose": "..."}],
    "development": [...]
  },
  "build": {
    "scripts": {"build": "tsc", "test": "jest"},
    "envVars": ["DATABASE_URL", "API_KEY"],
    "docker": "Dockerfile summary",
    "ci": "CI config summary"
  }
}
```

**modules.pkg.json**:
```json
{
  "modules": [
    {
      "name": "Module name",
      "path": "Path",
      "entry": "Entry file",
      "exports": ["Exported symbol list"],
      "layer": "controller|service|repository|util",
      "patterns": ["singleton", "factory"]
    }
  ],
  "dependencies": {
    "graph": "Mermaid diagram code",
    "cycles": ["Circular dependency warnings"]
  },
  "layers": {
    "controllers": ["File list"],
    "services": ["File list"],
    "repositories": ["File list"]
  }
}
```

**symbols.pkg.json**:
```json
{
  "modules": {
    "ModuleName": {
      "classes": [
        {
          "name": "ClassName",
          "visibility": "public",
          "extends": "BaseClass",
          "implements": ["Interface1"],
          "location": {"file": "src/models/User.ts", "line": 12},
          "properties": [{"name": "prop", "type": "string", "visibility": "public"}],
          "methods": [
            {
              "name": "method",
              "visibility": "public",
              "params": [{"name": "arg", "type": "number"}],
              "returns": "void",
              "description": "JSDoc description"
            }
          ]
        }
      ],
      "interfaces": [...],
      "functions": [...],
      "types": [...]
    }
  },
  "apiEndpoints": [
    {
      "method": "GET",
      "path": "/api/users",
      "handler": "UserController.list",
      "auth": true,
      "params": [],
      "response": "User[]"
    }
  ],
  "stats": {"total": 156, "documented": 142, "coverage": 0.91}
}
```

**quality.pkg.json**:
```json
{
  "complexity": {
    "fileStats": [{"path": "file.ts", "lines": 245, "functions": 12}],
    "largeFunctions": [{"path": "file.ts", "name": "bigFunc", "lines": 89}],
    "deepNesting": [{"path": "file.ts", "name": "func", "depth": 5}]
  },
  "organization": {
    "fileCount": 156,
    "avgFileSize": 120,
    "largeModules": ["module1", "module2"],
    "suggestions": ["Suggest splitting module1"]
  }
}
```

**api.pkg.json**:
```json
{
  "endpoints": [
    {
      "method": "GET",
      "path": "/api/users",
      "handler": "UserController.list",
      "controller": "UserController",
      "auth": true,
      "middlewares": ["AuthGuard"],
      "params": [{"name": "id", "type": "string", "in": "path"}],
      "response": "User[]",
      "description": "Get user list"
    }
  ],
  "groups": [
    {"prefix": "/api/users", "controller": "UserController", "endpoints": [...]}
  ],
  "authStrategies": [{"name": "jwt", "type": "bearer", "scope": "global"}],
  "globalMiddlewares": ["LoggerMiddleware"],
  "routeMiddlewares": [{"path": "/admin/*", "middleware": "AdminGuard"}]
}
```

**API Endpoint Extraction Rules** (Framework-specific):

| Framework | Search Pattern | Example |
|:----------|:---------------|:--------|
| Express/Koa | `router.get/post/put/delete/patch` | `router.get('/users', handler)` |
| NestJS | `@Controller/@Get/@Post/@Put/@Delete/@Patch/@UseGuards` | `@Get('/users/:id')` |
| Go (Gin) | `r.GET/POST/PUT/DELETE` | `r.GET("/users", handler)` |
| Go (net/http) | `http.HandleFunc` | `http.HandleFunc("/users", handler)` |

**symbols Collection Mandatory Process** (Avoid Omission):
1. Glob find all code files (`**/*.{ts,tsx,js,jsx,py,java,go}`)
2. `get_symbols_overview` for each file to get symbol list
3. `find_symbol(depth=1)` for each class to get method list
4. Batch write (50 files per batch), merge at end
5. **Validate**: Count scanned files, classes, total methods - fewer classes than expected indicates omission

### Python Script Assistance (Optional)

**Applicable Scenarios**: Serena MCP unavailable | Large projects (>500 files) | Framework-specific route extraction | Multi-language projects

**Storage Location**: `.claude/repowiki/.scripts/` (temporary, deleted in P7.4)

**Generation Principle**: Detect tech stack -> Select parser (Python AST/TS Compiler/Go AST) -> Adapt to framework features -> Output PKG format

**Framework-specific Scripts** (dynamically generated based on detection):

| Framework | Script | Extracted Content |
|:----------|:-------|:------------------|
| FastAPI/Django/Flask | `extract_fastapi.py` | `@app.get/post` / `path()` routes |
| NestJS/Express | `extract_nestjs.py` | Decorators / `app.get()` calls |
| Spring/Gin | `extract_spring.py` | `@RequestMapping` / `r.GET()` |

**All scripts must be deleted in P7.4 after validation!**

**Subagent Prompt must include**:
1. Output file full path: `.claude/repowiki/.meta/{name}.pkg.json`
2. PKG structure reference JSON Schema above
3. Dependent PKG file paths (symbols needs to read modules.pkg.json)
4. **Mandatory Serena MCP usage rules** (symbols collection):
   - Use Glob to find all code files
   - Use `get_symbols_overview` for each file to get symbol list
   - Use `find_symbol(depth=1)` for each class to get method list
   - Batch write JSON, 50 files per batch
5. **Validation requirement**: After collection, must count and report scanned files, classes, total methods

---

## Phase 4: Document Generation

**Subagent**: `atlas:atlas-executor` (**Must execute per P2 todos**, Task tool launches multiple simultaneously)

**Input**: `.meta/{project,modules,quality,api,symbols}.pkg.json` + P2 todos

**Executor Assignment** (No interdependencies, parallel recommended):

| Executor | Reads PKG | Output Documents | Parallel Control |
|:---------|:----------|:-----------------|:-----------------|
| home-arch | project + modules | index.md, architecture/*.md | parallel: must be 4 parallel / limited: limited by --concurrency / sequential: serial |
| api | api | api/*.md | Same as above |
| guides | project + quality | guides/*.md, decisions/*.md, quality/*.md | Same as above |
| symbols | symbols | symbols/*.md | Same as above |

**Zero Speculation Constraint**: All content 100% from PKG, prohibited to add info not in PKG | When PKG data is empty, mark as "Not detected" rather than guessing

**Subagent Prompt must include**:
1. PKG file full path to read: `.claude/repowiki/.meta/{name}.pkg.json`
2. Output file full path: `.claude/repowiki/{dir}/{name}.md`
3. Reference [Document Standards] example format
4. **Validation requirement**: When PKG data is empty, mark as "Not detected" rather than guessing

### File Mapping (Conditional generation see [Conditional Generation section](#conditional-generation))

| Output Document | Data Source PKG Field |
|:----------------|:----------------------|
| index.md | project.{name, description, tech stack, scripts} |
| architecture/overview.md | modules.layers + Mermaid diagram |
| architecture/structure.md | project.{tree, roles} |
| architecture/dependencies.md | project.{production, development} + Mermaid diagram |
| architecture/modules.md | modules.modules[] |
| architecture/module-graph.md | modules.{graph, cycles} + Mermaid diagram |
| architecture/layers.md | modules.{controllers, services, repositories} |
| architecture/patterns.md | modules.patterns[] |
| api/endpoints.md | api.endpoints[] |
| api/types.md | api.types[] |
| guides/development.md | project.{runtime, packageManager, scripts} |
| guides/build.md | project.{docker, ci, envVars} |
| decisions/adr-log.md | Tech selection inference |
| quality/complexity.md | quality.* |
| symbols/*.md | symbols grouped by module |

---

## Phase 5: AI Index Generation

**Subagent**: `atlas:repo-context-indexer`

**Operations**: Scan *.md | Extract key info (titles/symbol references/link relationships) | Build quick lookup index | Analyze inter-document references

**Output** (.index/*.json):

| Index File | Purpose | Key Fields |
|:-----------|:--------|:-----------|
| quick-lookup.json | Quick locate symbols/features | {project: {name, tech, entryDocs}, quickSearch: {symbolName: {type, file, doc}}} |
| symbol-map.json | Symbol->document mapping | {classes[], interfaces[], functions[], endpoints[], symbolToDocs: {symbolName: [docPaths]}} |
| doc-graph.json | Document relationship graph | {nodes: [{id, type, weight}], edges: [{from, to, type}]} |

### Index File Complete Schema

**quick-lookup.json**:
```json
{
  "project": {
    "name": "my-app",
    "tech": ["TypeScript", "NestJS"],
    "entryDocs": ["index.md", "architecture/overview.md"]
  },
  "quickSearch": {
    "UserService": {
      "type": "class",
      "file": "src/user/user.service.ts",
      "doc": "symbols/user-module.md#userservice"
    },
    "authentication": {
      "type": "feature",
      "doc": "features/authentication.md"
    }
  }
}
```

**symbol-map.json**:
```json
{
  "classes": ["UserService", "OrderService"],
  "interfaces": ["IUser", "IOrder"],
  "functions": ["validateUser", "processOrder"],
  "endpoints": ["/users", "/orders"],
  "symbolToDocs": {
    "UserService": ["symbols/user-module.md", "api/endpoints.md"]
  }
}
```

**doc-graph.json**:
```json
{
  "nodes": [
    {"id": "index.md", "type": "home", "weight": 10},
    {"id": "architecture/overview.md", "type": "arch", "weight": 8}
  ],
  "edges": [
    {"from": "index.md", "to": "architecture/overview.md", "type": "reference"}
  ]
}
```

---

## Phase 6: Context Optimization

**Operations**: Read .index/*.json | Determine high-priority entry documents | Configure quick access paths | Collect metadata statistics | Define context usage rules

**Output** (.claude/wiki-context.json):

### wiki-context.json Complete Schema

```json
{
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00Z",
  "projectName": "my-app",
  "wikiPath": ".claude/repowiki",
  "entryPoints": [
    {
      "path": "index.md",
      "title": "Project Homepage",
      "description": "Project overview and quick start",
      "weight": 10
    },
    {
      "path": "architecture/overview.md",
      "title": "Architecture Overview",
      "description": "System architecture and core modules",
      "weight": 9
    }
  ],
  "quickAccess": {
    "symbols": ".index/symbol-map.json",
    "search": ".index/quick-lookup.json",
    "graph": ".index/doc-graph.json"
  },
  "metadata": {
    "totalDocs": 12,
    "totalSymbols": 58,
    "coverage": 94,
    "lastBuildMode": "FULL_BUILD"
  },
  "contextRules": {
    "maxDocsPerQuery": 5,
    "priorityDocs": ["index.md", "architecture/overview.md"],
    "excludePatterns": ["*.pkg.json", "validation-report.md"]
  }
}
```

**Purpose**: Optimize Claude Code's context understanding and retrieval efficiency for Wiki | Provide quick access index to reduce full-text scanning | Intelligently control context size per conversation

---

## Phase 7: Parallel Validation and Auto-fix

**Last phase, comprehensively check all generated content, auto-fix issues found!**

### 7.1 Parallel Validation

**Execution Method**: Main process **launches 4 validators in parallel in single message** (sequential prohibited)

| Validator | Subagent | Validation Scope | Output | Key Checks |
|:----------|:---------|:-----------------|:-------|:-----------|
| V1-docs | `atlas:information-gatherer` | Document completeness | v1-docs.json | index.md exists >=10 lines / architecture/overview.md exists / guides/development.md exists / H1/H2 structure / Navigation links valid / No TODO/TBD |
| V2-PKG | `atlas:information-gatherer` | PKG consistency | v2-pkg.json | project.pkg.json valid / modules matches directory / symbols coverage >=90% / api endpoints match source / PKG modules -> symbols/*.md exists |
| V3-index | `atlas:information-gatherer` | Index completeness | v3-index.json | quick-lookup.json format correct / symbol-map symbol refs valid / doc-graph nodes correspond to actual docs / Index covers all docs |
| V4-context | `atlas:information-gatherer` | Context validity | v4-context.json | wiki-context.json exists / entryPoints paths valid / quickAccess index files exist / metadata stats accurate |

**Severity levels**: critical (must fix) | warning (suggest fix) | info (notice only)

**Validator Check Details**:

V1-docs Validator:
```json
{
  "checks": [
    {"id": "D1", "name": "index.md exists", "severity": "critical"},
    {"id": "D2", "name": "index.md >= 10 lines", "severity": "critical"},
    {"id": "D3", "name": "architecture/overview.md exists", "severity": "critical"},
    {"id": "D4", "name": "guides/development.md exists", "severity": "critical"},
    {"id": "D5", "name": "H1/H2 structure correct", "severity": "warning"},
    {"id": "D6", "name": "Navigation links valid", "severity": "warning"},
    {"id": "D7", "name": "No TODO/TBD placeholders", "severity": "warning"}
  ]
}
```

V2-PKG Validator:
```json
{
  "checks": [
    {"id": "P1", "name": "project.pkg.json exists and valid", "severity": "critical"},
    {"id": "P2", "name": "modules.pkg.json matches directory structure", "severity": "warning"},
    {"id": "P3", "name": "symbols.pkg.json coverage >= 90%", "severity": "warning"},
    {"id": "P4", "name": "api.pkg.json endpoints match source", "severity": "warning"},
    {"id": "P5", "name": "PKG modules -> symbols/*.md exists", "severity": "warning"}
  ]
}
```

V3-index Validator:
```json
{
  "checks": [
    {"id": "I1", "name": "quick-lookup.json exists and format correct", "severity": "critical"},
    {"id": "I2", "name": "symbol-map.json symbol references valid", "severity": "warning"},
    {"id": "I3", "name": "doc-graph.json nodes correspond to actual docs", "severity": "warning"},
    {"id": "I4", "name": "Index covers all generated docs", "severity": "warning"}
  ]
}
```

V4-context Validator:
```json
{
  "checks": [
    {"id": "C1", "name": "wiki-context.json exists", "severity": "critical"},
    {"id": "C2", "name": "entryPoints paths valid", "severity": "critical"},
    {"id": "C3", "name": "quickAccess index files exist", "severity": "warning"},
    {"id": "C4", "name": "metadata stats accurate", "severity": "info"}
  ]
}
```

### 7.2 Issue Collection

**Input**: v1-docs.json + v2-pkg.json + v3-index.json + v4-context.json

**Output** (.meta/validation-issues.json): `{timestamp, summary: {critical, warning, info, passed}, issues: [{id, severity, message, fix: {type, phase, target}}], fixable: bool, fixPlan: [{phase, action, targets}]}`

### 7.3 Auto-fix (<=2 rounds)

**Condition**: Critical issues exist

**Flow**: Analyze validation-issues.json -> Group by Phase -> Parallel launch atlas:atlas-executor to fix (P3 issues->re-collect PKG / P4 issues->regenerate docs / P5 issues->regenerate index / P6 issues->regenerate wiki-context.json) -> Re-execute 7.1 after fix -> Repeat if still critical and <2 rounds -> Mark "requires manual intervention" if >=2 rounds still has issues

**Fix Flow Diagram**:
```
+-------------------------------------------------------------+
|                     Fix Loop (Max 2 rounds)                  |
+-------------------------------------------------------------+
|  1. Analyze validation-issues.json                           |
|  2. Group fixable issues by Phase                            |
|  3. Parallel launch atlas:atlas-executor for fixes           |
|     - Phase 3 issues -> Re-collect corresponding PKG         |
|     - Phase 4 issues -> Regenerate corresponding docs        |
|     - Phase 5 issues -> Regenerate index                     |
|     - Phase 6 issues -> Regenerate wiki-context.json         |
|  4. Re-execute 7.1 parallel validation after fix             |
|  5. If still critical issues and < 2 rounds, return to step 1|
|  6. If >= 2 rounds still has issues, mark "requires manual"  |
+-------------------------------------------------------------+
```

### 7.4 Clean Up Temporary Files

**Cleanup Targets**: `.scripts/` (temporary scripts) | `.tmp/` (intermediate artifacts) | `v1-docs.json` | `v2-pkg.json` | `v3-index.json` | `v4-context.json` | `validation-issues.json` (after merged to report)

**Cleanup Command**: `rm -rf .claude/repowiki/.{scripts,tmp}/ && rm -f .claude/repowiki/.meta/v*.json .claude/repowiki/.meta/validation-issues.json`

**Keep temporary files for debugging when validation fails and requires manual intervention!**

### 7.5 Generate Final Report

**Output** (.meta/validation-report.md): Execution summary (validation rounds/fix rounds/final status) | Validation results (V1-V4 pass/warning/fail) | Temporary file cleanup status | Generation timestamp

---

## Conditional Generation

| Category | Document | Generation Condition |
|:---------|:---------|:---------------------|
| Core (Required) | index.md / architecture/{overview,structure}.md / guides/development.md | - |
| Conditional | architecture/dependencies.md | Dependency config exists |
| Conditional | architecture/{modules,module-graph}.md | >=2 modules |
| Conditional | architecture/{layers,patterns}.md | Layering/design patterns detected |
| Conditional | api/*.md | API detected |
| Conditional | guides/build.md | Build config exists |
| Conditional | symbols/*.md | `--skip-symbols` not specified |
| Conditional | quality/complexity.md | Complexity issues detected |
| Open | features/*.md | Auto-detected or `--features` specified |

---

## Document Naming Conventions

**Except for features/ and symbols/, all document filenames are strictly fixed!**

### Fixed Naming

**Documents**: index.md | architecture/{overview,structure,dependencies,modules,module-graph,layers,patterns}.md | api/{endpoints,types}.md | guides/{development,build}.md | decisions/adr-log.md | quality/complexity.md

**PKG**: .meta/{project,modules,quality,api,symbols}.pkg.json | .meta/{semantic-changes,validation-report}.md | .meta/validation-issues.json | .meta/v{1,2,3,4}.json (temporary)

**Index**: .index/{quick-lookup,symbol-map,doc-graph}.json

**Context**: .claude/wiki-context.json

### Dynamic Naming

| Directory | Rule | Example |
|:----------|:-----|:--------|
| symbols/ | index.md + {module}-module.md | user-module.md |
| features/ | {feature}.md (kebab-case) | authentication.md |

**Constraints**: symbols/ must have index.md, module docs end with `-module.md` | Prohibited: custom filenames, Chinese, spaces, uppercase

---

## Document Standards

**Universal Constraints**: H1 file title/H2 sections/H3 subsections | Tables left-aligned empty values use `-` | Code blocks specify language | Relative path links | Prohibited: TODO/TBD/broken links/invalid Mermaid

### Key Document Structure Examples

#### index.md Complete Example

```markdown
# {Project Name}

> {One-line description}

## Tech Stack

| Type | Technology | Version |
|:-----|:-----------|:--------|
| Language | TypeScript | 5.0 |
| Framework | NestJS | 10.0 |
| Database | PostgreSQL | 15 |

## Quick Start

**Requirements**: Node.js >= 18, pnpm >= 8

**Install**: `pnpm install`

**Start**: `pnpm dev`

## Navigation

| Category | Document | Description |
|:---------|:---------|:------------|
| Architecture | [Overview](./architecture/overview.md) | System architecture |
| API | [Endpoints](./api/endpoints.md) | API list |

---
*Generated at 2024-01-15T10:30:00Z*
```

#### architecture/overview.md Complete Example

```markdown
# Architecture Overview

## System Architecture Diagram

\`\`\`mermaid
graph TD
    subgraph "Presentation Layer"
        A[Controller]
    end
    subgraph "Business Layer"
        B[Service]
    end
    subgraph "Data Layer"
        C[Repository]
        D[(Database)]
    end
    A --> B --> C --> D
\`\`\`

## Core Modules

| Module | Path | Responsibility |
|:-------|:-----|:---------------|
| User | src/user | User management |
| Order | src/order | Order processing |

## Technical Decisions

| Decision | Choice | Rationale |
|:---------|:-------|:----------|
| ORM | Prisma | Type safety |
| Auth | JWT | Stateless |
```

#### api/endpoints.md Complete Example

```markdown
# API Endpoints

## Overview

| Metric | Value |
|:-------|:------|
| Total endpoints | 12 |
| Requires auth | 10 |

## Endpoint List

| Method | Path | Handler | Auth | Description |
|:-------|:-----|:--------|:----:|:------------|
| GET | /users | UserController.list | Yes | User list |
| POST | /users | UserController.create | Yes | Create user |
| GET | /users/:id | UserController.find | Yes | User details |

## Error Codes

| Status | Meaning | Scenario |
|:-------|:--------|:---------|
| 400 | Bad Request | Validation failed |
| 401 | Unauthorized | Invalid token |
| 404 | Not Found | Resource not found |
```

#### symbols/index.md Complete Example

```markdown
# Symbol Index

## Statistics

| Type | Count |
|:-----|:------|
| Classes | 15 |
| Interfaces | 8 |
| Functions | 23 |
| Types | 12 |

## By Module

| Module | Classes | Interfaces | Functions | Details |
|:-------|:--------|:-----------|:----------|:--------|
| User | 3 | 2 | 5 | [View](./user-module.md) |
| Order | 4 | 3 | 8 | [View](./order-module.md) |

## Public API

### Classes

| Class | Module | Description |
|:------|:-------|:------------|
| UserService | User | User service |

### Functions

| Function | Signature | Description |
|:---------|:----------|:------------|
| validateUser | `(id: string) => boolean` | Validate user |
```

#### quality/complexity.md Complete Example

```markdown
# Complexity Analysis

## File Statistics

| Metric | Value |
|:-------|:------|
| Total files | 45 |
| Total lines | 3,200 |
| Average lines | 71 |

## File Distribution

| Lines | Files | Percentage |
|:------|:------|:-----------|
| 1-50 | 20 | 44% |
| 51-100 | 15 | 33% |
| 101-200 | 8 | 18% |
| 200+ | 2 | 5% |

## Large Function Warnings

| File | Function | Lines | Suggestion |
|:-----|:---------|:------|:-----------|
| order.service.ts | processOrder | 85 | Split into sub-functions |

## Deep Nesting Warnings

| File | Function | Depth | Suggestion |
|:-----|:---------|:------|:-----------|
| validator.ts | validate | 5 | Early return |

## Refactoring Suggestions

### High Priority

1. **order.service.ts**: processOrder too long -> Split

### Medium Priority

1. **validator.ts**: Nesting too deep -> Early return pattern
```

#### features/{name}.md Complete Example

```markdown
# Authentication System

## Overview

JWT-based stateless authentication, supporting access token and refresh token dual-token mechanism.

## Core Components

| Component | Path | Responsibility |
|:----------|:-----|:---------------|
| AuthService | src/auth/auth.service.ts | Auth logic |
| JwtGuard | src/auth/jwt.guard.ts | Route guard |
| AuthController | src/auth/auth.controller.ts | Auth endpoints |

## Data Flow

\`\`\`mermaid
sequenceDiagram
    Client->>AuthController: POST /login
    AuthController->>AuthService: validate
    AuthService->>JwtService: sign
    JwtService-->>Client: tokens
\`\`\`

## Configuration

| Config | Type | Default | Description |
|:-------|:-----|:--------|:------------|
| JWT_SECRET | string | - | Signing secret |
| JWT_EXPIRES | string | 15m | Expiration time |
```

**Other Documents**: architecture/{dependencies,module-graph}.md contain Mermaid dependency graphs | quality/complexity.md contains statistics+warnings+suggestions | features/*.md contains overview+components+data flow (Mermaid)+config

---

## features/ Auto-detection

| Feature Pattern | Matching Files | Generated Document |
|:----------------|:---------------|:-------------------|
| auth/login/jwt | `**/auth/**`, `**/login*` | authentication.md |
| i18n/locale | `**/i18n/**`, `**/locale/**` | i18n.md |
| websocket | `**/*socket*` | realtime.md |
| upload/file | `**/upload*`, `**/file*` | file-handling.md |
| cache/redis | `**/cache*`, `**/redis*` | caching.md |

**Custom**: `--features auth,payment` or `.claude/wiki.config.json`

**Document Structure**: Feature name (H1) | Overview (H2) | Core components (H2) | Data flow (H2, Mermaid optional) | Config (H2, optional)

---

## Constraints

**Zero Speculation Principle (Highest Priority)**:

**Absolutely Prohibited** to speculate, guess, infer! All document content **100% from actual code**!

**Prohibited Speculation Content**: API endpoints (path/method/params/response) | Class names/function names/variable names | Parameter signatures/return types | Module structure/dependency relationships | Config items/environment variables | Any code-related technical details

**Mandatory Validation Flow**: 1. Must read source code before writing to document 2. Each symbol must be verified to exist via Serena MCP/Grep 3. Each API endpoint must be extracted from route definition file 4. Each config item must be extracted from config file 5. Better not to write than to guess

**Information Source Requirements**:
- Symbol info -> `find_symbol`/`get_symbols_overview`
- API endpoints -> Actual reading of route files (`@Get()`, `router.get()` etc)
- Dependencies -> `package.json`/`go.mod`/actual import analysis
- Config items -> `.env.example`/config files

**When uncertain about information, must return to source code to confirm again!**

**Subagent Usage** (see each Phase description):
- P1: `atlas:repo-semantic-analyzer` (INCREMENTAL only)
- P2: `Plan` (must TodoWrite)
- P3: `atlas:information-gatherer` (parallel recommended, must execute per todos)
- P4: `atlas:atlas-executor` (parallel recommended, must execute per todos)
- P5: `atlas:repo-context-indexer`
- P6: Main process
- P7.1: `atlas:information-gatherer` (must be 4 parallel)
- P7.3: `atlas:atlas-executor`
- P7.4: Main process

**Execution Constraints**: Phase order cannot be skipped | symbols waits for modules | PKG is only data medium | Prefer Serena MCP | Format - required sections cannot be omitted/table columns consistent/Mermaid syntax correct/relative path links | Naming - strictly follow conventions | Validation - docs >=10 lines/symbol coverage >=90% (warning)/links 100% valid/Mermaid no errors/must be 4 validators parallel | Cleanup - must delete .scripts/.tmp/v*.json/validation-issues.json after validation passes, keep for debugging when manual intervention needed

**Prohibited**: Skip validation | Silently ignore failures | Placeholder content | Hardcoded info | Any speculated content | Custom filenames

**Error Handling**: No git->FULL_BUILD | >2000 files without scope->terminate | Serena unavailable->fallback to Grep | Collection fails->skip dependent tasks | Executor fails->continue others | Critical issues->auto-fix (<=2 rounds)

---

## Final Report Format

**Must Include**: Execution summary (mode/language/scope/depth) | Generation stats (doc count/total lines/symbol coverage/time) | Validation results (All passed / X warnings / X failures) | Cleanup status (Temporary files deleted / Kept for debugging) | File list (core doc paths) | Next steps (`git add .claude/repowiki && git commit -m "docs: generate repo wiki"`)

---

## Preview Mode

**Trigger**: `/atlas:repo-wiki --preview`

**Flow**: P0-3 execute normally -> P4 generates preview (don't write files) -> P5-7 skipped

**Preview Output**: Build info (mode/changed files/affected docs) | Documents to generate (new/update/unchanged) | PKG data preview (changed symbols) | Expected impact (doc count/line changes)

**Use Cases**: Incremental update verification | Large project estimation | CI/CD integration

---

## Examples

**Commands**:
```bash
/atlas:repo-wiki                                      # Auto-detect all parameters
/atlas:repo-wiki --preview                            # Preview mode
/atlas:repo-wiki --lang en --scope src               # English + limit directory
/atlas:repo-wiki --skip-symbols --mode sequential    # Skip symbols + sequential
/atlas:repo-wiki --features auth,payment             # Specify features
/atlas:repo-wiki --force --concurrency 1             # Force rebuild + limit concurrency
```

**Output Structure**:

Simple library (5 docs):
```
.claude/repowiki/
+-- .meta/
|   +-- project.pkg.json
|   +-- validation-report.md
+-- .index/
|   +-- quick-lookup.json
|   +-- symbol-map.json
|   +-- doc-graph.json
+-- index.md
+-- architecture/
|   +-- overview.md
|   +-- structure.md
+-- guides/
|   +-- development.md
+-- symbols/
    +-- index.md
```

Web application (12+ docs):
```
.claude/repowiki/
+-- .meta/
|   +-- project.pkg.json
|   +-- modules.pkg.json
|   +-- quality.pkg.json
|   +-- api.pkg.json
|   +-- symbols.pkg.json
|   +-- validation-report.md
+-- .index/
|   +-- quick-lookup.json
|   +-- symbol-map.json
|   +-- doc-graph.json
+-- index.md
+-- architecture/
|   +-- overview.md
|   +-- structure.md
|   +-- dependencies.md
|   +-- modules.md
|   +-- module-graph.md
|   +-- layers.md
+-- api/
|   +-- endpoints.md
|   +-- types.md
+-- guides/
|   +-- development.md
|   +-- build.md
+-- symbols/
|   +-- index.md
|   +-- user-module.md
|   +-- order-module.md
+-- features/
    +-- authentication.md
```
