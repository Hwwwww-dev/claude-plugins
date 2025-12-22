---
description: 自主文档编排器。生成深度结构化的 Repo Wiki，支持项目级到符号级分析，含4层验证机制。
argument-hint: [--force] [--lang zh|en] [--depth N] [--scope path] [--skip-symbols] [--features list] [--mode parallel|limited|sequential] [--concurrency N] [--preview]
---

# Repo Wiki 编排器

通过多阶段工作流生成深度结构化的项目文档。

## 参数

| 参数 | 说明 | 默认值 |
|:-----|:-----|:-------|
| `--force` | 强制全量构建 | 智能判断 |
| `--lang` | 输出语言 (zh/en) | zh |
| `--depth` | 分析深度 | 2 |
| `--scope` | 限定分析范围 | . |
| `--skip-symbols` | 跳过符号分析 | false |
| `--features` | 指定功能点，逗号分隔 | 自动检测 |
| `--mode` | 执行模式 | 自动检测 |
| `--concurrency` | 最大并发数 | 2 |
| `--preview` | 预览模式，仅显示变更不写入 | false |

---

## 执行流程

P0环境检测 → P1变更检测 → P2规划 → P3信息收集 → P4文档生成 → P5索引生成 → P6上下文优化 → P7验证修复

### Subagent 分配

| Phase | Subagent | 说明 |
|:------|:---------|:-----|
| 0 | 主进程 | 创建目录、检测模式和规模 |
| 1 | `atlas:repo-semantic-analyzer` | 仅 INCREMENTAL 模式 |
| 2 | `Plan` | **必须 TodoWrite** 生成详细执行计划 |
| 3 | `atlas:information-gatherer` | 信息收集（见下方并行策略） |
| 4 | `atlas:atlas-executor` | 文档生成（见下方并行策略） |
| 5 | `atlas:repo-context-indexer` | 生成 .index/*.json |
| 6 | 主进程 | 生成 wiki-context.json |
| 7.1 | `atlas:information-gatherer` | 验证（见下方并行策略） |
| 7.3 | `atlas:atlas-executor` | 修复 critical 问题（≤2轮）|
| 7.4 | 主进程 | 清理临时文件 |

### 并行策略（动态分配）

**核心原则**: 无依赖关系的任务尽可能并行，受 `--concurrency` 限制

**Phase 3 信息收集**:
| 收集器 | 依赖 | 并行组 |
|:-------|:-----|:-------|
| project | 无 | 第一轮并行 |
| modules | 无 | 第一轮并行 |
| quality | 无 | 第一轮并行 |
| api | 无 | 第一轮并行 |
| symbols | modules | 第二轮（等待 modules 完成）|

**Phase 4 文档生成**（可根据检测到的内容动态拆分）:
| Executor | 读取 PKG | 输出 | 并行 |
|:---------|:---------|:-----|:-----|
| home | project | index.md | ✅ |
| arch-overview | modules | architecture/overview.md | ✅ |
| arch-structure | project | architecture/structure.md | ✅ |
| arch-deps | project | architecture/dependencies.md | ✅ |
| arch-modules | modules | architecture/modules.md, module-graph.md | ✅ |
| arch-layers | modules | architecture/layers.md, patterns.md | ✅ |
| api | api | api/*.md | ✅ |
| guides | project+quality | guides/*.md, quality/*.md | ✅ |
| symbols-index | symbols | symbols/index.md | ✅ |
| symbols-{module} | symbols | symbols/{module}-module.md | ✅ 每模块一个 |
| features-{name} | project+符号 | features/{name}.md | ✅ 每功能一个 |

**Phase 7.1 验证**:
| 验证器 | 验证范围 | 并行 |
|:-------|:---------|:-----|
| V1-文档 | 核心文档完整性 | ✅ |
| V2-PKG | PKG 数据一致性 | ✅ |
| V3-索引 | 索引文件完整性 | ✅ |
| V4-上下文 | wiki-context.json | ✅ |

**并行模式控制**:
| 模式 | 行为 |
|:-----|:-----|
| `--mode parallel` | 尽可能多并行，仅受依赖关系限制 |
| `--mode limited` | 受 `--concurrency N` 限制最大并行数 |
| `--mode sequential` | 全部串行执行 |

**🚨 约束**: ① 严禁混用 subagent 类型 ② P2 必须 TodoWrite ③ P3/P4 必须按 todos 执行 ④ 有依赖关系的任务必须等待依赖完成

### 数据流转

| Phase | 输入 | 输出 | 传递 |
|:------|:-----|:-----|:-----|
| 0 | 项目目录+git | 环境报告(mode/scale) | 内存→P1/P2 |
| 1 | 环境报告+git diff | semantic-changes.json | 文件→P2 |
| 2 | P0/P1 报告 | 执行计划+Todos | 内存→P3 |
| 3 | P2 计划 | *.pkg.json + .scripts/*.py | 文件→P4 |
| 4 | PKG 文件 | *.md | 文件→P5 |
| 5 | *.md + PKG | .index/*.json | 文件→P6 |
| 6 | 索引文件 | wiki-context.json | 文件→P7 |
| 7.1 | 所有产物 | v*.json | 文件→7.2 |
| 7.2 | v*.json | validation-issues.json | 文件→7.3 |
| 7.3 | issues | 修复后文件 | 文件→7.1(重验) |
| 7.4 | - | 清理临时文件 | 删除 |
| 7.5 | 验证结果 | validation-report.md | 文件 |

**约束**: P3/4/5/6/7 从文件读取，不依赖内存 | P7.4 必须清理 `.scripts/` `.tmp/` `v*.json` `validation-issues.json`

---

## Phase 0: 环境检测

**操作**: 创建目录 `.claude/repowiki/{.meta,.index,.scripts,.tmp,architecture,api,guides,decisions,symbols,quality,features}` | 检测模式(Wiki不存在/--force/配置变更→FULL_BUILD | 仅代码变更→INCREMENTAL) | 判断规模(<100全量|100-500采样|500-2000分片|>2000需--scope)

**输出**(→P1/P2): `{mode: "FULL_BUILD|INCREMENTAL", fileCount: 150, changedFiles: ["src/user.ts"], scale: "small|medium|large|huge"}`

---

## Phase 1: 语义变更检测

**条件**: 仅 INCREMENTAL 模式（FULL_BUILD 跳过）

**Subagent**: `atlas:repo-semantic-analyzer`

**操作**: `git diff HEAD~1 HEAD` 获取变更 | Serena MCP (`find_symbol`/`find_referencing_symbols`) 语义分析 | 识别新增/修改/删除符号 | 确定需更新的文档列表

**输出**(.meta/semantic-changes.json):
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

## Phase 2: 规划

**Subagent**: `Plan`

**操作**: 分析项目 | **必须 TodoWrite** 动态生成执行计划（根据P0/P1结果、--skip-symbols、--features 等参数调整）

**输出**:
1. **TodoWrite**: 详细 todos（P3收集器选择、P4文档类型、P7验证项）
2. **执行计划**: `{collectors: ["project","modules","quality","symbols"], skipSymbols: false, features: ["auth"], priority: ["src/core"]}`

**生成原则**: 根据项目实际情况动态决定，每个 todo 具体可执行可验证

**Todos 结构示例**（按实际需要动态生成）:
```
Phase 3 - 信息收集:
- [ ] 收集项目元数据 → .meta/project.pkg.json
- [ ] 分析模块结构 → .meta/modules.pkg.json
- [ ] 统计代码质量 → .meta/quality.pkg.json
- [ ] 提取 API 端点 → .meta/api.pkg.json
- [ ] 提取符号信息 → .meta/symbols.pkg.json（如未 --skip-symbols）

Phase 4 - 文档生成:
- [ ] 生成首页和架构文档 (home-arch executor)
- [ ] 生成 API 文档 (api executor)
- [ ] 生成开发指南 (guides executor)
- [ ] 生成符号文档 (symbols executor)
- [ ] 生成功能文档（如检测到特定功能或 --features）

Phase 7 - 验证:
- [ ] 验证文档完整性 (V1-V4 并行)
- [ ] 生成验证报告
```

---

## Phase 3: 信息收集

**🚨 核心原则：宁多勿少，宁慢勿错 🚨**

**Subagent**: `atlas:information-gatherer`（**必须按 P2 todos 执行**，每完成一个立即标记 completed）

**输出**: `.meta/{project,modules,quality,api,symbols}.pkg.json`

### 信息收集强制规则

**信息密度原则**:
- 一句话能说清的不用两句话
- 能用表格的不用列表
- 能用符号的不用文字（✅❌→等）
- 避免重复说明同一要点

**输出精度要求**:
- 数据精确到具体数值，禁止"若干"、"多个"等模糊描述
- API 端点必须完整路径，禁止省略号
- 符号签名必须完整，不可截断

**验证增强**:
- 每个 PKG 文件必须包含 `_meta.generatedAt` 时间戳
- 每个文档必须在末尾包含生成时间戳
- 文档内的链接必须在生成后立即验证

**🚨 零臆想原则（参见 [约束章节](#约束)）**:
1. **深度优先** - 每个模块/符号必须读取实际源代码
2. **完整覆盖** - 不能遗漏任何公开的类、函数、接口、API
3. **多次验证** - 对关键信息（特别是 API 端点）必须反复确认
4. **源码为准** - 所有信息从源代码提取，禁止推测

**API 端点收集**（最严格）:
- 必须扫描所有路由定义文件（controller、router）
- 必须读取装饰器/注解（`@Get()`, `@Post()`, `router.get()` 等）
- 必须提取完整路由路径、HTTP 方法、处理函数
- **绝对禁止**: ① 根据函数名猜测路由 ② 根据文件名猜测端点 ③ 假设标准 CRUD 路由 ④ 编造未定义的端点

**符号收集**（零遗漏）:
- 必须 Serena MCP `find_symbol`/`get_symbols_overview`
- 对每个类必须读取方法列表（`depth=1`）
- 对每个函数必须提取实际参数签名
- **禁止**: ① 根据命名约定猜测签名 ② 采样或跳过 public/protected 符号 ③ 跳过 test/mock/generated

**依赖/配置收集**:
- 必须读取 `package.json`/`go.mod`/`requirements.txt`
- 必须分析实际 import/require 语句
- **禁止**: 假设存在某个依赖或猜测配置项名称

### 并行收集策略

**执行方式**: Task tool 同时启动多个收集器

| 收集器 | 依赖 | 可并行 | 模式控制 |
|:-------|:-----|:-------|:---------|
| project/modules/quality/api | 无 | ✅ | parallel: 必须4并行 / limited: 受--concurrency限制 / sequential: 串行 |
| symbols | modules | ❌ | 等待 modules 完成后启动 |

**执行分两轮**: ① project+modules+quality+api 并行 ② symbols 等待 modules

### 收集器定义

| 收集器 | 数据来源 | 关键字段 |
|:-------|:---------|:---------|
| **project** | package.json/README/配置 | {name, version, language, runtime, framework, database, tree, dependencies[], scripts, envVars, docker, ci} |
| **modules** | 目录+入口文件+import分析 | {modules[], graph[], cycles[], layers, controllers[], services[], repositories[], patterns[]} |
| **quality** | 文件统计+AST分析 | {totalFiles, totalLines, avgLines, distribution, largeFunctions[], deepNesting[], refactorings[]} |
| **api** | 路由文件(Serena优先,降级Grep) | {endpoints[{method,path,handler,controller,auth,middlewares,params,response}], groups[], authStrategies[], middlewares[]} |
| **symbols** | Serena MCP **强制** | {classes[{name,module,path,visibility,extends,implements,properties[],methods[]}], interfaces[], functions[{name,params,returns}], types[]} |

### PKG JSON Schema 完整定义

**project.pkg.json**:
```json
{
  "metadata": {
    "name": "项目名称",
    "version": "版本号",
    "description": "描述",
    "license": "许可证",
    "author": "作者",
    "repository": "仓库地址"
  },
  "techStack": {
    "language": "主语言",
    "framework": "框架",
    "database": "数据库",
    "packageManager": "包管理器"
  },
  "directory": {
    "tree": "目录树结构",
    "roles": {"src": "源代码", "tests": "测试"},
    "stats": {"ts": 45, "tsx": 23}
  },
  "dependencies": {
    "production": [{"name": "...", "version": "...", "purpose": "..."}],
    "development": [...]
  },
  "build": {
    "scripts": {"build": "tsc", "test": "jest"},
    "envVars": ["DATABASE_URL", "API_KEY"],
    "docker": "Dockerfile 概要",
    "ci": "CI 配置概要"
  }
}
```

**modules.pkg.json**:
```json
{
  "modules": [
    {
      "name": "模块名",
      "path": "路径",
      "entry": "入口文件",
      "exports": ["导出符号列表"],
      "layer": "controller|service|repository|util",
      "patterns": ["singleton", "factory"]
    }
  ],
  "dependencies": {
    "graph": "Mermaid 图表代码",
    "cycles": ["循环依赖警告"]
  },
  "layers": {
    "controllers": ["文件列表"],
    "services": ["文件列表"],
    "repositories": ["文件列表"]
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
              "description": "JSDoc 说明"
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
    "suggestions": ["建议拆分 module1"]
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
      "description": "获取用户列表"
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

**API 端点提取规则**（框架特定）:

| 框架 | 搜索模式 | 示例 |
|:-----|:---------|:-----|
| Express/Koa | `router.get/post/put/delete/patch` | `router.get('/users', handler)` |
| NestJS | `@Controller/@Get/@Post/@Put/@Delete/@Patch/@UseGuards` | `@Get('/users/:id')` |
| Go (Gin) | `r.GET/POST/PUT/DELETE` | `r.GET("/users", handler)` |
| Go (net/http) | `http.HandleFunc` | `http.HandleFunc("/users", handler)` |

**symbols 收集强制流程**（避免遗漏）:
1. Glob 找所有代码文件（`**/*.{ts,tsx,js,jsx,py,java,go}`）
2. 每个文件 `get_symbols_overview` 获取符号列表
3. 每个类 `find_symbol(depth=1)` 获取方法列表
4. 分批写入（每批50文件），最终合并
5. **验证**: 统计扫描文件数、类数、方法总数，类数<预期说明有遗漏

### Python 脚本辅助（可选）

**适用场景**: Serena MCP 不可用 | 大型项目(>500文件) | 特定框架路由提取 | 多语言项目

**存放位置**: `.claude/repowiki/.scripts/`（临时，P7.4删除）

**生成原则**: 检测技术栈 → 选择解析器(Python AST/TS Compiler/Go AST) → 适配框架特性 → 输出 PKG 格式

**框架特定脚本**（根据检测动态生成）:

| 框架 | 脚本 | 提取内容 |
|:-----|:-----|:---------|
| FastAPI/Django/Flask | `extract_fastapi.py` | `@app.get/post` / `path()` 路由 |
| NestJS/Express | `extract_nestjs.py` | 装饰器 / `app.get()` 调用 |
| Spring/Gin | `extract_spring.py` | `@RequestMapping` / `r.GET()` |

**🚨 所有脚本必须在 P7.4 验证后删除！**

**Subagent Prompt 必须包含**:
1. 输出文件完整路径: `.claude/repowiki/.meta/{name}.pkg.json`
2. PKG 结构参考上述 JSON Schema
3. 依赖的 PKG 文件路径（symbols 需读取 modules.pkg.json）
4. **强制 Serena MCP 使用规范**（symbols 收集）:
   - 使用 Glob 找到所有代码文件
   - 对每个文件使用 `get_symbols_overview` 获取符号列表
   - 对每个类使用 `find_symbol(depth=1)` 获取方法列表
   - 分批写入 JSON，每批 50 个文件
5. **验证要求**: 收集完成后必须统计并报告扫描文件数、类数、方法总数

---

## Phase 4: 文档生成

**Subagent**: `atlas:atlas-executor`（**必须按 P2 todos 执行**，Task tool 同时启动多个）

**输入**: `.meta/{project,modules,quality,api,symbols}.pkg.json` + P2 todos

**Executor 分配**（无相互依赖，推荐并行）:

| Executor | 读取 PKG | 输出文档 | 并行控制 |
|:---------|:---------|:---------|:---------|
| home-arch | project + modules | index.md, architecture/*.md | parallel: 必须4并行 / limited: 受--concurrency限制 / sequential: 串行 |
| api | api | api/*.md | 同上 |
| guides | project + quality | guides/*.md, decisions/*.md, quality/*.md | 同上 |
| symbols | symbols | symbols/*.md | 同上 |

**🚨 零臆想约束**: 所有内容100%来自 PKG，禁止添加 PKG 不存在的信息 | PKG 数据为空时标注"未检测到"而非猜测

**Subagent Prompt 必须包含**:
1. 要读取的 PKG 文件完整路径: `.claude/repowiki/.meta/{name}.pkg.json`
2. 输出文件完整路径: `.claude/repowiki/{dir}/{name}.md`
3. 参考【文档规范】中的示例格式
4. **验证要求**: PKG 数据为空时标注"未检测到"而非猜测

### 文件映射（条件生成见[条件生成章节](#条件生成)）

| 输出文档 | 数据来源 PKG 字段 |
|:---------|:------------------|
| index.md | project.{name, description, 技术栈, scripts} |
| architecture/overview.md | modules.layers + Mermaid图 |
| architecture/structure.md | project.{tree, roles} |
| architecture/dependencies.md | project.{production, development} + Mermaid图 |
| architecture/modules.md | modules.modules[] |
| architecture/module-graph.md | modules.{graph, cycles} + Mermaid图 |
| architecture/layers.md | modules.{controllers, services, repositories} |
| architecture/patterns.md | modules.patterns[] |
| api/endpoints.md | api.endpoints[] |
| api/types.md | api.types[] |
| guides/development.md | project.{runtime, packageManager, scripts} |
| guides/build.md | project.{docker, ci, envVars} |
| decisions/adr-log.md | 技术选型推断 |
| quality/complexity.md | quality.* |
| symbols/*.md | symbols 按模块分组 |

---

## Phase 5: AI索引生成

**Subagent**: `atlas:repo-context-indexer`

**操作**: 扫描 *.md | 提取关键信息(标题/符号引用/链接关系) | 构建快速查询索引 | 分析文档间引用关系

**输出**(.index/*.json):

| 索引文件 | 用途 | 关键字段 |
|:---------|:-----|:---------|
| quick-lookup.json | 快速定位符号/功能 | {project: {name, tech, entryDocs}, quickSearch: {符号名: {type, file, doc}}} |
| symbol-map.json | 符号→文档映射 | {classes[], interfaces[], functions[], endpoints[], symbolToDocs: {符号名: [文档路径]}} |
| doc-graph.json | 文档关系图 | {nodes: [{id, type, weight}], edges: [{from, to, type}]} |

### 索引文件完整 Schema

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

## Phase 6: 上下文优化

**操作**: 读取 .index/*.json | 确定高优先级入口文档 | 配置快速访问路径 | 收集元数据统计 | 定义上下文使用规则

**输出**(.claude/wiki-context.json):

### wiki-context.json 完整 Schema

```json
{
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00Z",
  "projectName": "my-app",
  "wikiPath": ".claude/repowiki",
  "entryPoints": [
    {
      "path": "index.md",
      "title": "项目首页",
      "description": "项目概览和快速开始",
      "weight": 10
    },
    {
      "path": "architecture/overview.md",
      "title": "架构总览",
      "description": "系统架构和核心模块",
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

**目的**: 优化 Claude Code 对 Wiki 的上下文理解和检索效率 | 提供快速访问索引减少全文扫描 | 智能控制单次对话的上下文大小

---

## Phase 7: 并行验证与自动修复

**🚨 最后阶段，全面检查所有生成内容，发现问题自动修复！**

### 7.1 并行验证

**执行方式**: 主进程**单条消息并行启动 4 个验证器**（禁止串行）

| 验证器 | Subagent | 验证范围 | 输出 | 关键检查 |
|:-------|:---------|:---------|:-----|:---------|
| V1-文档 | `atlas:information-gatherer` | 文档完整性 | v1-docs.json | index.md存在≥10行 / architecture/overview.md存在 / guides/development.md存在 / H1/H2结构 / 导航链接有效 / 无TODO/TBD |
| V2-PKG | `atlas:information-gatherer` | PKG一致性 | v2-pkg.json | project.pkg.json有效 / modules与目录一致 / symbols覆盖率≥90% / api端点与源码一致 / PKG模块→symbols/*.md存在 |
| V3-索引 | `atlas:information-gatherer` | 索引完整性 | v3-index.json | quick-lookup.json格式正确 / symbol-map符号引用有效 / doc-graph节点对应实际文档 / 索引覆盖所有文档 |
| V4-上下文 | `atlas:information-gatherer` | 上下文有效性 | v4-context.json | wiki-context.json存在 / entryPoints路径有效 / quickAccess索引存在 / metadata统计准确 |

**严重级别**: critical(必须修复) | warning(建议修复) | info(仅提示)

**验证器检查项详情**:

V1-文档验证器:
```json
{
  "checks": [
    {"id": "D1", "name": "index.md 存在", "severity": "critical"},
    {"id": "D2", "name": "index.md ≥10 行", "severity": "critical"},
    {"id": "D3", "name": "architecture/overview.md 存在", "severity": "critical"},
    {"id": "D4", "name": "guides/development.md 存在", "severity": "critical"},
    {"id": "D5", "name": "H1/H2 结构正确", "severity": "warning"},
    {"id": "D6", "name": "导航链接有效", "severity": "warning"},
    {"id": "D7", "name": "无 TODO/TBD 占位符", "severity": "warning"}
  ]
}
```

V2-PKG验证器:
```json
{
  "checks": [
    {"id": "P1", "name": "project.pkg.json 存在且有效", "severity": "critical"},
    {"id": "P2", "name": "modules.pkg.json 与目录结构一致", "severity": "warning"},
    {"id": "P3", "name": "symbols.pkg.json 符号覆盖率 ≥90%", "severity": "warning"},
    {"id": "P4", "name": "api.pkg.json 端点与源码一致", "severity": "warning"},
    {"id": "P5", "name": "PKG 中的模块 → symbols/*.md 存在", "severity": "warning"}
  ]
}
```

V3-索引验证器:
```json
{
  "checks": [
    {"id": "I1", "name": "quick-lookup.json 存在且格式正确", "severity": "critical"},
    {"id": "I2", "name": "symbol-map.json 符号引用有效", "severity": "warning"},
    {"id": "I3", "name": "doc-graph.json 节点对应实际文档", "severity": "warning"},
    {"id": "I4", "name": "索引覆盖所有生成的文档", "severity": "warning"}
  ]
}
```

V4-上下文验证器:
```json
{
  "checks": [
    {"id": "C1", "name": "wiki-context.json 存在", "severity": "critical"},
    {"id": "C2", "name": "entryPoints 路径有效", "severity": "critical"},
    {"id": "C3", "name": "quickAccess 索引文件存在", "severity": "warning"},
    {"id": "C4", "name": "metadata 统计准确", "severity": "info"}
  ]
}
```

### 7.2 问题收集

**输入**: v1-docs.json + v2-pkg.json + v3-index.json + v4-context.json

**输出**(.meta/validation-issues.json): `{timestamp, summary: {critical, warning, info, passed}, issues: [{id, severity, message, fix: {type, phase, target}}], fixable: bool, fixPlan: [{phase, action, targets}]}`

### 7.3 自动修复（≤2轮）

**条件**: 存在 critical 问题

**流程**: 分析 validation-issues.json → 按 Phase 分组 → 并行启动 atlas:atlas-executor 修复（P3问题→重新收集PKG / P4问题→重新生成文档 / P5问题→重新生成索引 / P6问题→重新生成wiki-context.json）→ 修复完成后重新执行 7.1 → 仍有 critical 且<2轮则重复 → ≥2轮仍有问题标记"需人工介入"

**修复流程图**:
```
┌─────────────────────────────────────────────────────────────┐
│                     修复循环 (最多 2 轮)                      │
├─────────────────────────────────────────────────────────────┤
│  1. 分析 validation-issues.json                              │
│  2. 按 Phase 分组可修复问题                                   │
│  3. 并行启动 atlas:atlas-executor 执行修复                    │
│     - Phase 3 问题 → 重新收集对应 PKG                         │
│     - Phase 4 问题 → 重新生成对应文档                         │
│     - Phase 5 问题 → 重新生成索引                             │
│     - Phase 6 问题 → 重新生成 wiki-context.json               │
│  4. 修复完成后，重新执行 7.1 并行验证                          │
│  5. 如果仍有 critical 问题且 < 2 轮，返回步骤 1                │
│  6. 如果 ≥ 2 轮仍有问题，标记为"需人工介入"                    │
└─────────────────────────────────────────────────────────────┘
```

### 7.4 清理临时文件

**清理目标**: `.scripts/` (临时脚本) | `.tmp/` (中间产物) | `v1-docs.json` | `v2-pkg.json` | `v3-index.json` | `v4-context.json` | `validation-issues.json` (合并到 report 后)

**清理命令**: `rm -rf .claude/repowiki/.{scripts,tmp}/ && rm -f .claude/repowiki/.meta/v*.json .claude/repowiki/.meta/validation-issues.json`

**🚨 验证失败且需人工介入时保留临时文件供调试！**

### 7.5 生成最终报告

**输出**(.meta/validation-report.md): 执行概况(验证轮次/修复轮次/最终状态) | 验证结果(V1-V4通过/警告/失败) | 临时文件清理状态 | 生成时间戳

---

## 条件生成

| 类别 | 文档 | 生成条件 |
|:-----|:-----|:---------|
| 核心(必须) | index.md / architecture/{overview,structure}.md / guides/development.md | - |
| 条件 | architecture/dependencies.md | 存在依赖配置 |
| 条件 | architecture/{modules,module-graph}.md | ≥2 模块 |
| 条件 | architecture/{layers,patterns}.md | 检测到分层/设计模式 |
| 条件 | api/*.md | 检测到 API |
| 条件 | guides/build.md | 存在构建配置 |
| 条件 | symbols/*.md | `--skip-symbols` 未指定 |
| 条件 | quality/complexity.md | 检测到复杂度问题 |
| 开放 | features/*.md | 自动检测或 `--features` 指定 |

---

## 文档命名规范

**🚨 除 features/ 和 symbols/ 外，所有文档文件名严格固定！**

### 固定命名

**文档**: index.md | architecture/{overview,structure,dependencies,modules,module-graph,layers,patterns}.md | api/{endpoints,types}.md | guides/{development,build}.md | decisions/adr-log.md | quality/complexity.md

**PKG**: .meta/{project,modules,quality,api,symbols}.pkg.json | .meta/{semantic-changes,validation-report}.md | .meta/validation-issues.json | .meta/v{1,2,3,4}.json(临时)

**索引**: .index/{quick-lookup,symbol-map,doc-graph}.json

**上下文**: .claude/wiki-context.json

### 动态命名

| 目录 | 规则 | 示例 |
|:-----|:-----|:-----|
| symbols/ | index.md + {module}-module.md | user-module.md |
| features/ | {feature}.md (kebab-case) | authentication.md |

**约束**: symbols/ 必须有 index.md，模块文档以 `-module.md` 结尾 | 禁止自创文件名、中文、空格、大写

---

## 文档规范

**通用约束**: H1文件标题/H2章节/H3子节 | 表格左对齐空值填`-` | 代码块指定语言 | 相对路径链接 | 禁止TODO/TBD/断链/无效Mermaid

### 关键文档结构示例

#### index.md 完整示例

```markdown
# {项目名}

> {一句话描述}

## 技术栈

| 类型 | 技术 | 版本 |
|:-----|:-----|:-----|
| 语言 | TypeScript | 5.0 |
| 框架 | NestJS | 10.0 |
| 数据库 | PostgreSQL | 15 |

## 快速开始

**环境要求**: Node.js >= 18, pnpm >= 8

**安装**: `pnpm install`

**启动**: `pnpm dev`

## 导航

| 分类 | 文档 | 说明 |
|:-----|:-----|:-----|
| 架构 | [Overview](./architecture/overview.md) | 系统架构 |
| API | [Endpoints](./api/endpoints.md) | 接口列表 |

---
*生成于 2024-01-15T10:30:00Z*
```

#### architecture/overview.md 完整示例

```markdown
# 架构总览

## 系统架构图

\`\`\`mermaid
graph TD
    subgraph "表现层"
        A[Controller]
    end
    subgraph "业务层"
        B[Service]
    end
    subgraph "数据层"
        C[Repository]
        D[(Database)]
    end
    A --> B --> C --> D
\`\`\`

## 核心模块

| 模块 | 路径 | 职责 |
|:-----|:-----|:-----|
| User | src/user | 用户管理 |
| Order | src/order | 订单处理 |

## 技术决策

| 决策 | 选型 | 理由 |
|:-----|:-----|:-----|
| ORM | Prisma | 类型安全 |
| 认证 | JWT | 无状态 |
```

#### api/endpoints.md 完整示例

```markdown
# API 端点

## 概览

| 指标 | 值 |
|:-----|:---|
| 总端点 | 12 |
| 需认证 | 10 |

## 端点列表

| Method | Path | Handler | Auth | Description |
|:-------|:-----|:--------|:----:|:------------|
| GET | /users | UserController.list | ✓ | 用户列表 |
| POST | /users | UserController.create | ✓ | 创建用户 |
| GET | /users/:id | UserController.find | ✓ | 用户详情 |

## 错误码

| 状态码 | 含义 | 场景 |
|:-------|:-----|:-----|
| 400 | 参数错误 | 校验失败 |
| 401 | 未认证 | Token 无效 |
| 404 | 不存在 | 资源未找到 |
```

#### symbols/index.md 完整示例

```markdown
# 符号索引

## 统计

| 类型 | 数量 |
|:-----|:-----|
| 类 | 15 |
| 接口 | 8 |
| 函数 | 23 |
| 类型 | 12 |

## 按模块分类

| 模块 | 类 | 接口 | 函数 | 详情 |
|:-----|:---|:-----|:-----|:-----|
| User | 3 | 2 | 5 | [查看](./user-module.md) |
| Order | 4 | 3 | 8 | [查看](./order-module.md) |

## 公开 API

### 类

| 类名 | 模块 | 说明 |
|:-----|:-----|:-----|
| UserService | User | 用户服务 |

### 函数

| 函数 | 签名 | 说明 |
|:-----|:-----|:-----|
| validateUser | `(id: string) => boolean` | 验证用户 |
```

#### quality/complexity.md 完整示例

```markdown
# 复杂度分析

## 文件统计

| 指标 | 值 |
|:-----|:---|
| 总文件 | 45 |
| 总行数 | 3,200 |
| 平均行数 | 71 |

## 文件分布

| 行数 | 文件数 | 占比 |
|:-----|:-------|:-----|
| 1-50 | 20 | 44% |
| 51-100 | 15 | 33% |
| 101-200 | 8 | 18% |
| 200+ | 2 | 5% |

## 大函数警告

| 文件 | 函数 | 行数 | 建议 |
|:-----|:-----|:-----|:-----|
| order.service.ts | processOrder | 85 | 拆分为子函数 |

## 深嵌套警告

| 文件 | 函数 | 层数 | 建议 |
|:-----|:-----|:-----|:-----|
| validator.ts | validate | 5 | 提前返回 |

## 重构建议

### 高优先级

1. **order.service.ts**: processOrder 过长 → 拆分

### 中优先级

1. **validator.ts**: 嵌套过深 → 提前返回模式
```

#### features/{name}.md 完整示例

```markdown
# 认证系统

## 概述

基于 JWT 的无状态认证，支持 access token 和 refresh token 双令牌机制。

## 核心组件

| 组件 | 路径 | 职责 |
|:-----|:-----|:-----|
| AuthService | src/auth/auth.service.ts | 认证逻辑 |
| JwtGuard | src/auth/jwt.guard.ts | 路由守卫 |
| AuthController | src/auth/auth.controller.ts | 认证接口 |

## 数据流

\`\`\`mermaid
sequenceDiagram
    Client->>AuthController: POST /login
    AuthController->>AuthService: validate
    AuthService->>JwtService: sign
    JwtService-->>Client: tokens
\`\`\`

## 配置项

| 配置 | 类型 | 默认值 | 说明 |
|:-----|:-----|:-------|:-----|
| JWT_SECRET | string | - | 签名密钥 |
| JWT_EXPIRES | string | 15m | 过期时间 |
```

**其他文档**: architecture/{dependencies,module-graph}.md 包含 Mermaid 依赖图 | quality/complexity.md 包含统计+警告+建议 | features/*.md 包含概述+组件+数据流(Mermaid)+配置

---

## features/ 自动检测

| 特征模式 | 匹配文件 | 生成文档 |
|:---------|:---------|:---------|
| auth/login/jwt | `**/auth/**`, `**/login*` | authentication.md |
| i18n/locale | `**/i18n/**`, `**/locale/**` | i18n.md |
| websocket | `**/*socket*` | realtime.md |
| upload/file | `**/upload*`, `**/file*` | file-handling.md |
| cache/redis | `**/cache*`, `**/redis*` | caching.md |

**自定义**: `--features auth,payment` 或 `.claude/wiki.config.json`

**文档结构**: 功能名(H1) | 概述(H2) | 核心组件(H2) | 数据流(H2,Mermaid可选) | 配置项(H2,可选)

---

## 约束

**🚨🚨🚨 零臆想原则（最高优先级）🚨🚨🚨**:

**绝对禁止**臆想、猜测、推断！所有文档内容**100%来自实际代码**！

**禁止臆想的内容**: API端点(路径/方法/参数/返回值) | 类名/函数名/变量名 | 参数签名/返回类型 | 模块结构/依赖关系 | 配置项/环境变量 | 任何代码相关的技术细节

**强制验证流程**: ① 必须先读取源代码才能写入文档 ② 每个符号必须通过 Serena MCP/Grep 验证存在 ③ 每个 API 端点必须从路由定义文件提取 ④ 每个配置项必须从配置文件提取 ⑤ 宁可不写，也不能猜测

**信息来源要求**:
- 符号信息 → `find_symbol`/`get_symbols_overview`
- API 端点 → 路由文件实际读取（`@Get()`, `router.get()` 等）
- 依赖关系 → `package.json`/`go.mod`/实际 import 分析
- 配置项 → `.env.example`/配置文件

**🚨 发现不确定信息，必须返回源代码再次确认！**

**Subagent 使用**（参见各 Phase 说明）:
- P1: `atlas:repo-semantic-analyzer`（仅 INCREMENTAL）
- P2: `Plan`（必须 TodoWrite）
- P3: `atlas:information-gatherer`（model="haiku"，并行推荐，必须按 todos 执行）
- P4: `atlas:atlas-executor`（并行推荐，必须按 todos 执行，询问用户选择模型）
- P5: `atlas:repo-context-indexer`
- P6: 主进程
- P7.1: `atlas:information-gatherer`（model="haiku"，必须4并行）
- P7.3: `atlas:atlas-executor`（询问用户选择模型）
- P7.4: 主进程

**执行约束**: 阶段顺序不可跳跃 | symbols等待modules | PKG是唯一数据媒介 | 优先Serena MCP | 格式-必需章节不可省略/表格列数一致/Mermaid语法正确/相对路径链接 | 命名-严格遵守规范 | 验证-文档≥10行/符号覆盖≥90%(警告)/链接100%有效/Mermaid无错误/必须4验证器并行 | 清理-验证通过后必删.scripts/.tmp/v*.json/validation-issues.json，失败需人工介入时保留

**禁止**: 跳过验证 | 静默忽略失败 | 占位内容 | 硬编码信息 | 任何臆想内容 | 自定义文件名

**错误处理**: 无git→FULL_BUILD | >2000文件无scope→终止 | Serena不可用→降级Grep | 收集失败→跳过依赖任务 | Executor失败→继续其他 | critical问题→自动修复(≤2轮)

---

## 最终报告格式

**必须包含**: 执行概况(模式/语言/范围/深度) | 生成统计(文档数/总行数/符号覆盖率/耗时) | 验证结果(✅全部通过 / ⚠️X个警告 / ❌X个失败) | 清理状态(已删除临时文件 / 保留供调试) | 文件列表(核心文档路径) | 下一步操作(`git add .claude/repowiki && git commit -m "docs: generate repo wiki"`)

---

## 预览模式

**触发**: `/atlas:repo-wiki --preview`

**流程**: P0-3正常执行 → P4生成预览(不写文件) → P5-7跳过

**预览输出**: 构建信息(模式/变更文件/影响文档) | 将生成文档(新增/更新/不变) | PKG数据预览(变更符号) | 预计影响(文档数/行数变化)

**使用场景**: 增量更新验证 | 大型项目预估 | CI/CD集成

---

## 示例

**命令**:
```bash
/atlas:repo-wiki                                      # 自动检测所有参数
/atlas:repo-wiki --preview                            # 预览模式
/atlas:repo-wiki --lang en --scope src               # 英文+限定目录
/atlas:repo-wiki --skip-symbols --mode sequential    # 跳过符号+串行
/atlas:repo-wiki --features auth,payment             # 指定功能点
/atlas:repo-wiki --force --concurrency 1             # 强制重建+限制并发
```

**输出结构**:

简单库 (5 文档):
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

Web 应用 (12+ 文档):
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
