---
description: Autonomous documentation orchestrator. Generates deeply structured Repo Wiki with project-to-symbol level analysis and 4-layer validation mechanism.
argument-hint: [--force] [--lang zh|en] [--depth N] [--scope path] [--skip-symbols] [--features list] [--mode parallel|limited|sequential] [--concurrency N] [--preview]
---

# Repo Wiki Orchestrator

Generates deeply structured project documentation through multi-phase workflow.

## Parameters

| Parameter | Description | Default |
|:----------|:------------|:--------|
| `--force` | Force full build | Auto-detect |
| `--lang` | Output language (zh/en) | zh |
| `--depth` | Analysis depth | 2 |
| `--scope` | Limit analysis scope | . |
| `--skip-symbols` | Skip symbol analysis | false |
| `--features` | Specify features, comma-separated | Auto-detect |
| `--mode` | Execution mode | Auto-detect |
| `--concurrency` | Max concurrency | 2 |
| `--preview` | Preview mode, show changes without writing | false |

---

## Execution Flow

### Flow Overview

P0 Environment Detection → User Configuration → P1 Change Detection → P2 Planning → P3 Information Gathering → P4 Document Generation → P5 Index Generation → P6 Context Optimization → P7 Validation & Fix

### User Configuration Flow

**First AskUserQuestion: Execution Mode and Document Scope**

```
Question 1: Execution Mode
- Auto Mode (Recommended): Use recommended options, minimize interaction
- Interactive Mode: Confirm at each key step
- Preview Mode: Analyze only, no document generation

Question 2: Document Scope
- Full Documentation (Recommended): Include all modules, API, symbol docs
- Core Documentation: Generate architecture and development guides only
- Minimal Documentation: Generate homepage and architecture overview only
- Custom: Specify required document types
```

**Second AskUserQuestion: Document Configuration (Interactive Mode Only)**

If user selects **Interactive Mode**, ask for detailed configuration:

```
Question 1: Document Depth
- Depth 2 (Recommended): Project → Module → Class/Function level
- Depth 1: Project → Module level
- Depth 3: Include detailed info for all symbols
- Depth 0: Project-level overview only

Question 2: Document Language
- Chinese (Recommended): All documents in Chinese
- English: All documents in English
- Bilingual: Generate both Chinese and English documents

Question 3: Symbol Analysis
- Include Symbols (Recommended): Extract classes, functions, interfaces, etc.
- Skip Symbols: Generate architecture and API docs only

Question 4: Specific Features
- Auto-detect (Recommended): Automatically identify feature modules from code
- Specify Features: Enter comma-separated feature list (e.g., auth,payment)
- Skip Features: Do not generate feature documentation

Question 5: Concurrency Control
- Parallel Mode (Recommended): Maximize concurrency for fast generation
- Limited Concurrency: Use --concurrency parameter to specify max concurrency
- Sequential Mode: Generate one by one, suitable for debugging
```

**Auto Mode Behavior** (Skip second AskUserQuestion):
- Document Depth: 2
- Document Language: Chinese
- Symbol Analysis: Include symbols (unless --skip-symbols)
- Specific Features: Auto-detect (unless --features specified)
- Concurrency Control: Parallel mode, max concurrency 2

**Preview Mode Behavior**:
- Execute P0-3 phases (Environment Detection → Change Detection → Planning → Information Gathering)
- Output preview report (document list to generate, change impact, PKG data preview)
- Skip P4-7 phases (no actual document generation)

### Subagent Assignment

| Phase | Subagent | Description |
|:------|:---------|:------------|
| 0 | Main Process | Create directories, detect mode and scale |
| 1 | `atlas:repo-semantic-analyzer` | INCREMENTAL mode only |
| 2 | `Plan` | **Must TodoWrite** to generate detailed execution plan |
| 3 | `atlas:information-gatherer` | Information gathering (see parallel strategy below) |
| 4 | `atlas:atlas-executor` | Document generation (see parallel strategy below) |
| 5 | `atlas:repo-context-indexer` | Generate .index/*.json |
| 6 | Main Process | Generate wiki-context.json |
| 7.1 | `atlas:information-gatherer` | Validation (see parallel strategy below) |
| 7.3 | `atlas:atlas-executor` | Fix critical issues (<=2 rounds) |
| 7.4 | Main Process | Clean temporary files |

### Parallel Strategy (Dynamic Assignment)

**Core Principle**: Tasks without dependencies should run in parallel as much as possible, limited by `--concurrency`

**Phase 3 Information Gathering**:
| Gatherer | Dependencies | Parallel Group |
|:---------|:-------------|:---------------|
| project | None | First round parallel |
| modules | None | First round parallel |
| quality | None | First round parallel |
| api | None | First round parallel |
| symbols | modules | Second round (wait for modules to complete) |

**Phase 4 Document Generation** (Can be dynamically split based on detected content):
| Executor | Read PKG | Output | Parallel |
|:---------|:---------|:-------|:---------|
| home | project | index.md | ✅ |
| arch-overview | modules | architecture/overview.md | ✅ |
| arch-structure | project | architecture/structure.md | ✅ |
| arch-deps | project | architecture/dependencies.md | ✅ |
| arch-modules | modules | architecture/modules.md, module-graph.md | ✅ |
| arch-layers | modules | architecture/layers.md, patterns.md | ✅ |
| api | api | api/*.md | ✅ |
| guides | project+quality | guides/*.md, quality/*.md | ✅ |
| symbols-index | symbols | symbols/index.md | ✅ |
| symbols-{module} | symbols | symbols/{module}-module.md | ✅ One per module |
| features-{name} | project+symbols | features/{name}.md | ✅ One per feature |

**Phase 7.1 Validation**:
| Validator | Validation Scope | Parallel |
|:----------|:-----------------|:---------|
| V1-Docs | Core document completeness | ✅ |
| V2-PKG | PKG data consistency | ✅ |
| V3-Index | Index file completeness | ✅ |
| V4-Context | wiki-context.json | ✅ |

**Parallel Mode Control**:
| Mode | Behavior |
|:-----|:---------|
| `--mode parallel` | Maximize parallelism, limited only by dependencies |
| `--mode limited` | Limited by `--concurrency N` max parallel count |
| `--mode sequential` | Execute all sequentially |

**Constraints**: 1. Never mix subagent types 2. P2 must TodoWrite 3. P3/P4 must execute according to todos 4. Tasks with dependencies must wait for dependencies to complete

### Data Flow

| Phase | Input | Output | Transfer |
|:------|:------|:-------|:---------|
| 0 | Project directory+git | Environment report (mode/scale) | Memory→P1/P2 |
| 1 | Environment report+git diff | semantic-changes.json | File→P2 |
| 2 | P0/P1 reports | Execution plan+Todos | Memory→P3 |
| 3 | P2 plan | *.pkg.json + .scripts/*.py | File→P4 |
| 4 | PKG files | *.md | File→P5 |
| 5 | *.md + PKG | .index/*.json | File→P6 |
| 6 | Index files | wiki-context.json | File→P7 |
| 7.1 | All artifacts | v*.json | File→7.2 |
| 7.2 | v*.json | validation-issues.json | File→7.3 |
| 7.3 | issues | Fixed files | File→7.1 (re-validate) |
| 7.4 | - | Clean temporary files | Delete |
| 7.5 | Validation results | validation-report.md | File |

**Constraints**: P3/4/5/6/7 read from files, not memory | P7.4 must clean `.scripts/` `.tmp/` `v*.json` `validation-issues.json`

---

## Phase 0: Environment Detection

**Operations**: Create directories `.claude/repowiki/{.meta,.index,.scripts,.tmp,architecture,api,guides,decisions,symbols,quality,features}` | Detect mode (Wiki not exists/--force/config changed→FULL_BUILD | Code changes only→INCREMENTAL) | Determine scale (<100 full scan|100-500 sampling|500-2000 sharding|>2000 requires --scope)

**Output** (→P1/P2): `{mode: "FULL_BUILD|INCREMENTAL", fileCount: 150, changedFiles: ["src/user.ts"], scale: "small|medium|large|huge"}`

---

## Phase 1: Semantic Change Detection

**Condition**: INCREMENTAL mode only (skip for FULL_BUILD)

**Subagent**: `atlas:repo-semantic-analyzer`

**Operations**: `git diff HEAD~1 HEAD` to get changes | Serena MCP (`find_symbol`/`find_referencing_symbols`) semantic analysis | Identify added/modified/deleted symbols | Determine docs to update

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

**Operations**: Analyze project | **Must TodoWrite** to dynamically generate execution plan (adjust based on P0/P1 results, --skip-symbols, --features, etc.)

**Output**:
1. **TodoWrite**: Detailed todos (P3 gatherer selection, P4 document types, P7 validation items)
2. **Execution Plan**: `{collectors: ["project","modules","quality","symbols"], skipSymbols: false, features: ["auth"], priority: ["src/core"]}`

**Generation Principles**: Dynamically decide based on actual project situation, each todo should be specific, executable, and verifiable

**Todos Structure Example** (Dynamically generated based on actual needs):
```
Phase 3 - Information Gathering:
- [ ] Collect project metadata → .meta/project.pkg.json
- [ ] Analyze module structure → .meta/modules.pkg.json
- [ ] Collect code quality stats → .meta/quality.pkg.json
- [ ] Extract API endpoints → .meta/api.pkg.json
- [ ] Extract symbol info → .meta/symbols.pkg.json (if not --skip-symbols)

Phase 4 - Document Generation:
- [ ] Generate homepage and architecture docs (home-arch executor)
- [ ] Generate API docs (api executor)
- [ ] Generate development guides (guides executor)
- [ ] Generate symbol docs (symbols executor)
- [ ] Generate feature docs (if features detected or --features specified)

Phase 7 - Validation:
- [ ] Validate document completeness (V1-V4 parallel)
- [ ] Generate validation report
```

---

## Phase 3: Information Gathering

**Core Principle: Better More Than Less, Better Slow Than Wrong**

**Subagent**: `atlas:information-gatherer` (**Must execute according to P2 todos**, mark completed immediately after each task)

**Output**: `.meta/{project,modules,quality,api,symbols}.pkg.json`

### Information Gathering Mandatory Rules

**Information Density Principle**:
- One sentence is enough, don't use two
- Use tables instead of lists when possible
- Use symbols instead of text when possible (e.g., check/cross/arrow)
- Avoid repeating the same point

**Output Precision Requirements**:
- Data must be precise with specific values, no vague descriptions like "several" or "multiple"
- API endpoints must have complete paths, no ellipsis
- Symbol signatures must be complete, no truncation

**Validation Enhancement**:
- Each PKG file must include `_meta.generatedAt` timestamp
- Each document must include generation timestamp at the end
- Links in documents must be validated immediately after generation

**Zero Speculation Principle (See [Constraints Section](#constraints))**:
1. **Depth First** - Must read actual source code for each module/symbol
2. **Complete Coverage** - Cannot miss any public classes, functions, interfaces, APIs
3. **Multiple Validations** - Critical info (especially API endpoints) must be confirmed repeatedly
4. **Source Code as Truth** - All info extracted from source code, speculation forbidden

**API Endpoint Collection** (Strictest):
- Must scan all route definition files (controller, router)
- Must read decorators/annotations (`@Get()`, `@Post()`, `router.get()`, etc.)
- Must extract complete route path, HTTP method, handler function
- **Absolutely Forbidden**: 1. Guessing routes from function names 2. Guessing endpoints from file names 3. Assuming standard CRUD routes 4. Fabricating undefined endpoints

**Symbol Collection** (Zero Omission):
- Must use Serena MCP `find_symbol`/`get_symbols_overview`
- Must read method list for each class (`depth=1`)
- Must extract actual parameter signatures for each function
- **Forbidden**: 1. Guessing signatures from naming conventions 2. Sampling or skipping public/protected symbols 3. Skipping test/mock/generated

**Dependency/Config Collection**:
- Must read `package.json`/`go.mod`/`requirements.txt`
- Must analyze actual import/require statements
- **Forbidden**: Assuming a dependency exists or guessing config item names

### Parallel Collection Strategy

**Execution Method**: Task tool starts multiple gatherers simultaneously

| Gatherer | Dependencies | Parallel | Mode Control |
|:---------|:-------------|:---------|:-------------|
| project/modules/quality/api | None | ✅ | parallel: must run 4 in parallel / limited: limited by --concurrency / sequential: serial |
| symbols | modules | ❌ | Start after modules completes |

**Execute in Two Rounds**: 1. project+modules+quality+api parallel 2. symbols waits for modules

### Gatherer Definitions

| Gatherer | Data Source | Key Fields |
|:---------|:------------|:-----------|
| **project** | package.json/README/config | {name, version, language, runtime, framework, database, tree, dependencies[], scripts, envVars, docker, ci} |
| **modules** | directories+entry files+import analysis | {modules[], graph[], cycles[], layers, controllers[], services[], repositories[], patterns[]} |
| **quality** | file stats+AST analysis | {totalFiles, totalLines, avgLines, distribution, largeFunctions[], deepNesting[], refactorings[]} |
| **api** | route files (Serena preferred, fallback to Grep) | {endpoints[{method,path,handler,controller,auth,middlewares,params,response}], groups[], authStrategies[], middlewares[]} |
| **symbols** | Serena MCP **mandatory** | {classes[{name,module,path,visibility,extends,implements,properties[],methods[]}], interfaces[], functions[{name,params,returns}], types[]} |

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

**Symbols Collection Mandatory Flow** (Avoid omissions):
1. Glob to find all code files (`**/*.{ts,tsx,js,jsx,py,java,go}`)
2. `get_symbols_overview` for each file to get symbol list
3. `find_symbol(depth=1)` for each class to get method list
4. Write in batches (50 files per batch), merge at the end
5. **Validation**: Count scanned files, classes, total methods; fewer classes than expected indicates omissions

### Python Script Assistance (Optional)

**Applicable Scenarios**: Serena MCP unavailable | Large projects (>500 files) | Framework-specific route extraction | Multi-language projects

**Storage Location**: `.claude/repowiki/.scripts/` (temporary, deleted in P7.4)

**Generation Principles**: Detect tech stack → Select parser (Python AST/TS Compiler/Go AST) → Adapt to framework features → Output PKG format

**Framework-specific Scripts** (Dynamically generated based on detection):

| Framework | Script | Extraction Content |
|:----------|:-------|:-------------------|
| FastAPI/Django/Flask | `extract_fastapi.py` | `@app.get/post` / `path()` routes |
| NestJS/Express | `extract_nestjs.py` | Decorators / `app.get()` calls |
| Spring/Gin | `extract_spring.py` | `@RequestMapping` / `r.GET()` |

**All scripts must be deleted in P7.4 after validation!**

**Subagent Prompt Must Include**:
1. Output file full path: `.claude/repowiki/.meta/{name}.pkg.json`
2. PKG structure reference from JSON Schema above
3. Dependent PKG file paths (symbols needs to read modules.pkg.json)
4. **Mandatory Serena MCP Usage Specification** (symbols collection):
   - Use Glob to find all code files
   - Use `get_symbols_overview` for each file to get symbol list
   - Use `find_symbol(depth=1)` for each class to get method list
   - Write JSON in batches, 50 files per batch
5. **Validation Requirements**: After collection, must count and report scanned file count, class count, total method count

---

## Phase 4: Document Generation

**Subagent**: `atlas:atlas-executor` (**Must execute according to P2 todos**, Task tool starts multiple simultaneously)

**Input**: `.meta/{project,modules,quality,api,symbols}.pkg.json` + P2 todos

**Executor Assignment** (No interdependencies, parallel recommended):

| Executor | Read PKG | Output Documents | Parallel Control |
|:---------|:---------|:-----------------|:-----------------|
| home-arch | project + modules | index.md, architecture/*.md | parallel: must run 4 in parallel / limited: limited by --concurrency / sequential: serial |
| api | api | api/*.md | Same as above |
| guides | project + quality | guides/*.md, decisions/*.md, quality/*.md | Same as above |
| symbols | symbols | symbols/*.md | Same as above |

**Zero Speculation Constraint**: All content 100% from PKG, forbidden to add info not in PKG | When PKG data is empty, mark as "Not detected" instead of guessing

**Subagent Prompt Must Include**:
1. PKG file full path to read: `.claude/repowiki/.meta/{name}.pkg.json`
2. Output file full path: `.claude/repowiki/{dir}/{name}.md`
3. Reference example format from [Document Specifications]
4. **Validation Requirements**: When PKG data is empty, mark as "Not detected" instead of guessing

### File Mapping (See [Conditional Generation Section](#conditional-generation) for conditions)

| Output Document | Data Source PKG Fields |
|:----------------|:-----------------------|
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
| decisions/adr-log.md | Tech decision inference |
| quality/complexity.md | quality.* |
| symbols/*.md | symbols grouped by module |

---

## Phase 5: AI Index Generation

**Subagent**: `atlas:repo-context-indexer`

**Operations**: Scan *.md | Extract key info (titles/symbol references/link relationships) | Build quick query index | Analyze inter-document references

**Output** (.index/*.json):

| Index File | Purpose | Key Fields |
|:-----------|:--------|:-----------|
| quick-lookup.json | Quick symbol/feature lookup | {project: {name, tech, entryDocs}, quickSearch: {symbolName: {type, file, doc}}} |
| symbol-map.json | Symbol→Document mapping | {classes[], interfaces[], functions[], endpoints[], symbolToDocs: {symbolName: [docPaths]}} |
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

## Phase 7: Parallel Validation and Auto-Fix

**Final phase, comprehensively check all generated content, auto-fix issues found!**

### 7.1 Parallel Validation

**Execution Method**: Main process **starts 4 validators in parallel in a single message** (serial forbidden)

| Validator | Subagent | Validation Scope | Output | Key Checks |
|:----------|:---------|:-----------------|:-------|:-----------|
| V1-Docs | `atlas:information-gatherer` | Document completeness | v1-docs.json | index.md exists with >=10 lines / architecture/overview.md exists / guides/development.md exists / H1/H2 structure / Navigation links valid / No TODO/TBD |
| V2-PKG | `atlas:information-gatherer` | PKG consistency | v2-pkg.json | project.pkg.json valid / modules match directory / symbols coverage >=90% / api endpoints match source / PKG modules → symbols/*.md exist |
| V3-Index | `atlas:information-gatherer` | Index completeness | v3-index.json | quick-lookup.json format correct / symbol-map symbol refs valid / doc-graph nodes match actual docs / Index covers all docs |
| V4-Context | `atlas:information-gatherer` | Context validity | v4-context.json | wiki-context.json exists / entryPoints paths valid / quickAccess indexes exist / metadata stats accurate |

**Severity Levels**: critical (must fix) | warning (suggest fix) | info (notice only)

**Validator Check Details**:

V1-Docs Validator:
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
    {"id": "P3", "name": "symbols.pkg.json symbol coverage >= 90%", "severity": "warning"},
    {"id": "P4", "name": "api.pkg.json endpoints match source", "severity": "warning"},
    {"id": "P5", "name": "PKG modules → symbols/*.md exist", "severity": "warning"}
  ]
}
```

V3-Index Validator:
```json
{
  "checks": [
    {"id": "I1", "name": "quick-lookup.json exists and format correct", "severity": "critical"},
    {"id": "I2", "name": "symbol-map.json symbol refs valid", "severity": "warning"},
    {"id": "I3", "name": "doc-graph.json nodes match actual docs", "severity": "warning"},
    {"id": "I4", "name": "Index covers all generated docs", "severity": "warning"}
  ]
}
```

V4-Context Validator:
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

### 7.3 Auto-Fix (<=2 rounds)

**Condition**: Critical issues exist

**Flow**: Analyze validation-issues.json → Group by Phase → Start atlas:atlas-executor in parallel for fixes (P3 issues→re-collect PKG / P4 issues→re-generate docs / P5 issues→re-generate index / P6 issues→re-generate wiki-context.json) → After fix, re-execute 7.1 → If still critical and <2 rounds, repeat → >=2 rounds still has issues, mark "requires manual intervention"

**Fix Flow Diagram**:
```
+-------------------------------------------------------------+
|                     Fix Loop (max 2 rounds)                  |
+-------------------------------------------------------------+
|  1. Analyze validation-issues.json                           |
|  2. Group fixable issues by Phase                            |
|  3. Start atlas:atlas-executor in parallel for fixes         |
|     - Phase 3 issues → Re-collect corresponding PKG          |
|     - Phase 4 issues → Re-generate corresponding docs        |
|     - Phase 5 issues → Re-generate index                     |
|     - Phase 6 issues → Re-generate wiki-context.json         |
|  4. After fix, re-execute 7.1 parallel validation            |
|  5. If still critical issues and < 2 rounds, return to step 1|
|  6. If >= 2 rounds still has issues, mark "manual required"  |
+-------------------------------------------------------------+
```

### 7.4 Clean Temporary Files

**Clean Targets**: `.scripts/` (temp scripts) | `.tmp/` (intermediate artifacts) | `v1-docs.json` | `v2-pkg.json` | `v3-index.json` | `v4-context.json` | `validation-issues.json` (merged into report)

**Clean Command**: `rm -rf .claude/repowiki/.{scripts,tmp}/ && rm -f .claude/repowiki/.meta/v*.json .claude/repowiki/.meta/validation-issues.json`

**Keep temp files for debugging when validation fails and requires manual intervention!**

### 7.5 Generate Final Report

**Output** (.meta/validation-report.md): Execution summary (validation rounds/fix rounds/final status) | Validation results (V1-V4 passed/warning/failed) | Temp file cleanup status | Generation timestamp

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

## Document Naming Convention

**All document filenames are strictly fixed except features/ and symbols/!**

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

**Constraints**: symbols/ must have index.md, module docs end with `-module.md` | No custom filenames, Chinese, spaces, or uppercase

---

## Document Specifications

**General Constraints**: H1 file title/H2 sections/H3 subsections | Tables left-aligned, empty values use `-` | Code blocks specify language | Relative path links | No TODO/TBD/broken links/invalid Mermaid

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

| Decision | Choice | Reason |
|:---------|:-------|:-------|
| ORM | Prisma | Type safety |
| Auth | JWT | Stateless |
```

#### api/endpoints.md Complete Example

```markdown
# API Endpoints

## Overview

| Metric | Value |
|:-------|:------|
| Total Endpoints | 12 |
| Auth Required | 10 |

## Endpoint List

| Method | Path | Handler | Auth | Description |
|:-------|:-----|:--------|:----:|:------------|
| GET | /users | UserController.list | Y | User list |
| POST | /users | UserController.create | Y | Create user |
| GET | /users/:id | UserController.find | Y | User details |

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
| Total Files | 45 |
| Total Lines | 3,200 |
| Average Lines | 71 |

## File Distribution

| Lines | File Count | Percentage |
|:------|:-----------|:-----------|
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

1. **order.service.ts**: processOrder too long → Split

### Medium Priority

1. **validator.ts**: Nesting too deep → Early return pattern
```

#### features/{name}.md Complete Example

```markdown
# Authentication System

## Overview

JWT-based stateless authentication supporting access token and refresh token dual-token mechanism.

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
| JWT_SECRET | string | - | Signing key |
| JWT_EXPIRES | string | 15m | Expiration time |
```

**Other Documents**: architecture/{dependencies,module-graph}.md include Mermaid dependency diagrams | quality/complexity.md includes stats+warnings+suggestions | features/*.md includes overview+components+data flow (Mermaid)+config

---

## features/ Auto-Detection

| Feature Pattern | Matching Files | Generated Document |
|:----------------|:---------------|:-------------------|
| auth/login/jwt | `**/auth/**`, `**/login*` | authentication.md |
| i18n/locale | `**/i18n/**`, `**/locale/**` | i18n.md |
| websocket | `**/*socket*` | realtime.md |
| upload/file | `**/upload*`, `**/file*` | file-handling.md |
| cache/redis | `**/cache*`, `**/redis*` | caching.md |

**Custom**: `--features auth,payment` or `.claude/wiki.config.json`

**Document Structure**: Feature name (H1) | Overview (H2) | Core Components (H2) | Data Flow (H2, Mermaid optional) | Configuration (H2, optional)

---

## Constraints

**Zero Speculation Principle (Highest Priority)**:

**Absolutely forbidden** to speculate, guess, or infer! All document content **100% from actual code**!

**Forbidden Speculation Content**: API endpoints (path/method/params/response) | Class/function/variable names | Parameter signatures/return types | Module structure/dependencies | Config items/environment variables | Any code-related technical details

**Mandatory Validation Flow**: 1. Must read source code before writing docs 2. Each symbol must be verified via Serena MCP/Grep 3. Each API endpoint must be extracted from route definition files 4. Each config item must be extracted from config files 5. Better to not write than to guess

**Information Source Requirements**:
- Symbol info → `find_symbol`/`get_symbols_overview`
- API endpoints → Actual route file reading (`@Get()`, `router.get()`, etc.)
- Dependencies → `package.json`/`go.mod`/actual import analysis
- Config items → `.env.example`/config files

**When uncertain about info, must return to source code to confirm again!**

**Subagent Usage** (See each Phase description):
- P1: `atlas:repo-semantic-analyzer` (INCREMENTAL only)
- P2: `Plan` (must TodoWrite)
- P3: `atlas:information-gatherer` (model="haiku", parallel recommended, must execute according to todos)
- P4: `atlas:atlas-executor` (parallel recommended, must execute according to todos, ask user to select model)
- P5: `atlas:repo-context-indexer`
- P6: Main process
- P7.1: `atlas:information-gatherer` (model="haiku", must run 4 in parallel)
- P7.3: `atlas:atlas-executor` (ask user to select model)
- P7.4: Main process

**Execution Constraints**: Phase order cannot be skipped | symbols waits for modules | PKG is the only data medium | Prefer Serena MCP | Format - required sections cannot be omitted/table columns consistent/Mermaid syntax correct/relative path links | Naming - strictly follow conventions | Validation - docs >=10 lines/symbol coverage >=90% (warning)/links 100% valid/Mermaid no errors/must run 4 validators in parallel | Cleanup - must delete .scripts/.tmp/v*.json/validation-issues.json after validation passes, keep for debugging when manual intervention required

**Forbidden**: Skip validation | Silently ignore failures | Placeholder content | Hardcoded info | Any speculation | Custom filenames

**Error Handling**: No git→FULL_BUILD | >2000 files without scope→terminate | Serena unavailable→fallback to Grep | Collection failed→skip dependent tasks | Executor failed→continue others | Critical issues→auto-fix (<=2 rounds)

### Segmented Output Specification

**Trigger Conditions** (Segment if any condition met):
- Single output exceeds 800 characters
- List exceeds 15 items
- Code block exceeds 30 lines

### Pre-Output Confirmation

Confirm output documents include:
- [ ] Project overview
- [ ] Module documentation (each module)
- [ ] API documentation (if any)
- [ ] Symbol index

---

## Final Report Format

**Must Include**: Execution summary (mode/language/scope/depth) | Generation stats (doc count/total lines/symbol coverage/duration) | Validation results (All passed / X warnings / X failures) | Cleanup status (Temp files deleted / Kept for debugging) | File list (core doc paths) | Next steps (`git add .claude/repowiki && git commit -m "docs: generate repo wiki"`)

---

## Preview Mode

**Trigger**: `/atlas:repo-wiki --preview`

**Flow**: P0-3 execute normally → P4 generates preview (no file writing) → P5-7 skipped

**Preview Output**: Build info (mode/changed files/affected docs) | Documents to generate (new/updated/unchanged) | PKG data preview (changed symbols) | Estimated impact (doc count/line changes)

**Use Cases**: Incremental update verification | Large project estimation | CI/CD integration

---

## Examples

**Commands**:
```bash
/atlas:repo-wiki                                      # Auto-detect all parameters
/atlas:repo-wiki --preview                            # Preview mode
/atlas:repo-wiki --lang en --scope src               # English + limited directory
/atlas:repo-wiki --skip-symbols --mode sequential    # Skip symbols + sequential
/atlas:repo-wiki --features auth,payment             # Specify features
/atlas:repo-wiki --force --concurrency 1             # Force rebuild + limit concurrency
```

**Output Structure**:

Simple library (5 docs):
```
.claude/repowiki/
├── .meta/
│   ├── project.pkg.json
│   └── validation-report.md
├── .index/
│   ├── quick-lookup.json
│   ├── symbol-map.json
│   └── doc-graph.json
├── index.md
├── architecture/
│   ├── overview.md
│   └── structure.md
├── guides/
│   └── development.md
└── symbols/
    └── index.md
```

Web application (12+ docs):
```
.claude/repowiki/
├── .meta/
│   ├── project.pkg.json
│   ├── modules.pkg.json
│   ├── quality.pkg.json
│   ├── api.pkg.json
│   ├── symbols.pkg.json
│   └── validation-report.md
├── .index/
│   ├── quick-lookup.json
│   ├── symbol-map.json
│   └── doc-graph.json
├── index.md
├── architecture/
│   ├── overview.md
│   ├── structure.md
│   ├── dependencies.md
│   ├── modules.md
│   ├── module-graph.md
│   └── layers.md
├── api/
│   ├── endpoints.md
│   └── types.md
├── guides/
│   ├── development.md
│   └── build.md
├── symbols/
│   ├── index.md
│   ├── user-module.md
│   └── order-module.md
└── features/
    └── authentication.md
```
