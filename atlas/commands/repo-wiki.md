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

Phase 0 环境检测 → Phase 1 语义变更检测 → Phase 2 规划 → Phase 3 信息收集 → Phase 4 文档生成 → Phase 5 AI索引生成 → Phase 6 上下文优化 → Phase 7 验证

### Subagent 分配（必须严格遵守）

| Phase | 功能 | Subagent | 说明 |
|:------|:-----|:---------|:-----|
| 0 | 环境检测 | 主进程 | 不需要 subagent |
| 1 | 语义变更检测 | `atlas:repo-semantic-analyzer` | 检测语义级变更 |
| 2 | 规划 | `Plan` | 必须生成详细 todos |
| 3 | 信息收集 | `atlas:information-gatherer` | 读取 todos 执行 |
| 4 | 文档生成 | `atlas:atlas-executor` | 读取 todos 执行 |
| 5 | AI索引生成 | `atlas:repo-context-indexer` | 生成快速查询索引 |
| 6 | 上下文优化 | 主进程 | 生成 wiki-context.json |
| 7 | 验证 | `atlas:atlas-executor` | 全面检查所有生成内容 |

**🚨 严禁混用 subagent！Plan 只做规划，information-gatherer 只做信息收集，atlas-executor 负责文档生成和验证，repo-semantic-analyzer 只做变更检测，repo-context-indexer 只做索引生成！**

### 数据流转

| Phase | 读取 | 输出 | 传递方式 |
|:------|:-----|:-----|:---------|
| 0 | 项目目录、git 状态 | 环境报告 (mode, fileCount, changedFiles) | 内存传递给 Phase 1/2 |
| 1 | Phase 0 环境报告、git diff | 变更影响分析 (.meta/semantic-changes.json) | 文件写入 + 传递给 Phase 2 |
| 2 | Phase 0/1 报告 | 执行计划 JSON | 内存传递给 Phase 3 |
| 3 | Phase 2 计划 | PKG 文件 (.meta/*.pkg.json) | 文件写入 |
| 4 | PKG 文件 | 文档文件 (*.md) | 文件写入 |
| 5 | 文档文件、PKG 文件 | 索引文件 (.index/*.json) | 文件写入 |
| 6 | 索引文件 | wiki-context.json | 文件写入 |
| 7 | 所有生成内容 | 验证报告 (.meta/validation-report.md) + 最终报告 | 文件写入 + 输出 |

**关键约束**: Phase 3/4/5/6/7 必须从文件读取 PKG/索引，不依赖内存传递

---

## Phase 0: 环境检测

**输入**: 项目目录、git 状态、命令参数

**输出** (传递给 Phase 2):
```json
{
  "mode": "FULL_BUILD | INCREMENTAL",
  "fileCount": 150,
  "changedFiles": ["src/user.ts"],
  "scale": "small | medium | large | huge"
}
```

**操作**:
- 创建目录 `.claude/repowiki/{.meta,.index,architecture,api,guides,decisions,symbols,quality,features}`
- 检测构建模式: FULL_BUILD (Wiki不存在/--force/配置变更) | INCREMENTAL (仅代码变更)
- 判断规模: <100 全量 | 100-500 采样 | 500-2000 分片 | >2000 需 --scope

---

## Phase 1: 语义变更检测

**条件**: 仅在 **INCREMENTAL** 模式执行（FULL_BUILD 跳过此阶段）

**Subagent**: `atlas:repo-semantic-analyzer` (必须使用 Task tool 的 subagent_type="atlas:repo-semantic-analyzer")

**输入**:
- Phase 0 环境报告 (mode, changedFiles)
- git diff 输出

**输出** (写入文件):
- `.meta/semantic-changes.json`

**输出格式**:
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "changedFiles": ["src/user.ts", "src/order.ts"],
  "semanticChanges": {
    "newSymbols": [
      {"type": "function", "name": "validateUser", "module": "user", "file": "src/user.ts"}
    ],
    "modifiedSymbols": [
      {"type": "class", "name": "OrderService", "module": "order", "file": "src/order.ts", "change": "method added"}
    ],
    "deletedSymbols": [],
    "affectedModules": ["user", "order"],
    "affectedDocs": ["symbols/user-module.md", "api/endpoints.md"]
  },
  "impactLevel": "medium"
}
```

**操作**:
1. 使用 `git diff HEAD~1 HEAD` 获取文件变更
2. 对变更文件进行语义分析（使用 Serena MCP 的 `find_symbol` / `find_referencing_symbols`）
3. 识别新增/修改/删除的符号（类、函数、接口等）
4. 分析变更影响范围（依赖关系、引用位置）
5. 确定需要更新的文档文件列表
6. 输出结构化的变更影响分析到 `.meta/semantic-changes.json`

**Subagent Prompt 必须包含**:
1. git diff 命令获取变更内容
2. 输出文件完整路径: `.claude/repowiki/.meta/semantic-changes.json`
3. 使用 Serena MCP 工具进行语义分析
4. 输出格式必须符合上述 JSON schema

---

## Phase 2: 规划

**Subagent**: `Plan` (必须使用 Task tool 的 subagent_type="Plan")

**输入**: Phase 0 环境报告 + Phase 1 语义变更分析（如有）

**输出**:
1. **TodoWrite** - 必须使用 TodoWrite 工具生成详细的执行计划
2. **执行计划 JSON** - 传递给后续阶段

### Todos 生成要求

Plan agent 必须通过 **TodoWrite** 根据项目实际情况动态生成 todos：

**生成原则**:
- 根据 Phase 0 环境检测结果决定需要哪些收集器和文档
- 根据 --skip-symbols、--features 等参数调整 todos
- 根据项目规模和类型决定并行策略
- 每个 todo 必须具体、可执行、可验证

**Todos 结构**（按实际需要生成）:
```
Phase 3 - 信息收集（根据需要选择）:
- 收集项目元数据 → .meta/project.pkg.json
- 分析模块结构 → .meta/modules.pkg.json
- 统计代码质量 → .meta/quality.pkg.json
- 提取符号信息 → .meta/symbols.pkg.json（如未 --skip-symbols）

Phase 4 - 文档生成（根据条件生成规则选择）:
- 生成首页和架构文档
- 生成 API 文档（如检测到 API）
- 生成开发指南
- 生成符号文档（如未 --skip-symbols）
- 生成功能文档（如检测到特定功能或 --features）

Phase 6 - 验证:
- 验证文档完整性
- 生成验证报告
```

**🚨 关键要求**:
1. Plan agent **必须**调用 TodoWrite 生成 todos
2. todos 内容**根据项目实际情况动态决定**，尽可能信息
3. 后续 agent **必须严格按照 todos 顺序执行**

**执行计划 JSON** (传递给 Phase 3):
```json
{
  "collectors": ["project", "modules", "quality", "symbols"],
  "skipSymbols": false,
  "features": ["auth"],
  "priority": ["src/core", "src/api"]
}
```

**操作**: Plan Agent 分析项目，通过 TodoWrite 生成详细执行计划

---

## Phase 3: 信息收集

**Subagent**: `atlas:information-gatherer` (必须使用 Task tool 的 subagent_type="atlas:information-gatherer")

**🚨 必须严格按照 Phase 2 生成的 todos 执行，每完成一个 todo 立即标记为 completed**

**输入**: Phase 2 执行计划 + Phase 2 生成的 todos

**输出** (写入文件):
- `.meta/project.pkg.json`
- `.meta/modules.pkg.json`
- `.meta/quality.pkg.json`
- `.meta/symbols.pkg.json`

### 并行策略

| 模式 | 行为 |
|:-----|:-----|
| parallel | 推荐并行，受 --concurrency 限制 |
| limited | 严格限制并发数为 N |
| sequential | 串行执行 |

**依赖关系**: symbols 依赖 modules，其余无依赖

### 收集器

#### project → .meta/project.pkg.json

| 分类 | 字段 | 来源 |
|:-----|:-----|:-----|
| 元数据 | name, version, description, license, repository | package.json / go.mod / README |
| 技术栈 | language, runtime, framework, database, packageManager | 文件扩展名 / 依赖 / 配置 |
| 目录 | tree, roles, stats | 目录扫描 |
| 依赖 | production[], development[] | 配置文件 |
| 构建 | scripts, envVars, docker, ci | 配置文件 / .env.example |

#### modules → .meta/modules.pkg.json

| 分类 | 字段 | 来源 |
|:-----|:-----|:-----|
| 边界 | modules[].{name, path, entry, exports} | 目录 + 入口文件 |
| 依赖 | graph[], cycles[] | import/require 分析 |
| 分层 | layers, controllers[], services[], repositories[] | 装饰器 / 目录名 |
| 模式 | patterns[].{type, location} | 代码模式匹配 |

#### quality → .meta/quality.pkg.json

| 分类 | 字段 | 来源 |
|:-----|:-----|:-----|
| 统计 | totalFiles, totalLines, avgLines, maxFile, distribution | 文件统计 |
| 警告 | largeFunctions[], deepNesting[] | AST / 行数分析 |
| 建议 | refactorings[].{priority, target, issue, suggestion} | 规则匹配 |

#### symbols (依赖 modules) → .meta/symbols.pkg.json

工具: Serena MCP 优先，降级 Grep

| 分类 | 字段 |
|:-----|:-----|
| 类 | classes[].{name, module, path, visibility, extends, implements, properties[], methods[]} |
| 接口 | interfaces[].{name, module, extends, members[]} |
| 函数 | functions[].{name, module, params[], returns, description} |
| 类型 | types[].{name, kind, definition} |
| API | endpoints[].{method, path, handler, auth, description} |

采样: public > protected > private | 跳过 @internal / test / mock | 分批 50 个

**Subagent Prompt 必须包含**:
1. 输出文件完整路径: `.claude/repowiki/.meta/{name}.pkg.json`
2. PKG 结构参考上述字段定义
3. 依赖的 PKG 文件路径 (symbols 需读取 `.claude/repowiki/.meta/modules.pkg.json`)

---

## Phase 4: 文档生成

**Subagent**: `atlas:atlas-executor` (必须使用 Task tool 的 subagent_type="atlas:atlas-executor")

**🚨 必须严格按照 Phase 2 生成的 todos 执行，每完成一个 todo 立即标记为 completed**

**输入** (从文件读取):
- `.meta/project.pkg.json`
- `.meta/modules.pkg.json`
- `.meta/quality.pkg.json`
- `.meta/symbols.pkg.json`
- Phase 2 生成的 todos（必须遵循）

**输出** (写入文件): 各 *.md 文档

### Executor

| Executor | 读取文件 | 输出文件 |
|:---------|:---------|:---------|
| home-arch | `.meta/project.pkg.json`, `.meta/modules.pkg.json` | index.md, architecture/*.md |
| api | `.meta/symbols.pkg.json` | api/*.md |
| guides | `.meta/project.pkg.json`, `.meta/quality.pkg.json` | guides/*.md, decisions/*.md, quality/*.md |
| symbols | `.meta/symbols.pkg.json` | symbols/*.md |

依赖: 无相互依赖，遵循并行策略

**Subagent Prompt 必须包含**:
1. 要读取的 PKG 文件完整路径: `.claude/repowiki/.meta/{name}.pkg.json`
2. 输出文件完整路径: `.claude/repowiki/{dir}/{name}.md`
3. 参考【文档规范】中的示例格式

### 文件映射

| 文件 | 数据来源 |
|:-----|:---------|
| index.md | project.{name, description, 技术栈, scripts} |
| architecture/overview.md | modules.layers + Mermaid |
| architecture/structure.md | project.{tree, roles} |
| architecture/dependencies.md | project.{production, development} |
| architecture/modules.md | modules.modules[] |
| architecture/module-graph.md | modules.{graph, cycles} |
| architecture/layers.md | modules.{controllers, services, repositories} |
| architecture/patterns.md | modules.patterns[] |
| api/endpoints.md | symbols.endpoints[] |
| api/types.md | symbols.types[] |
| guides/development.md | project.{runtime, packageManager, scripts} |
| guides/build.md | project.{docker, ci, envVars} |
| decisions/adr-log.md | 技术选型推断 |
| quality/complexity.md | quality.* |
| symbols/*.md | symbols 按模块分组 |

---

## Phase 5: AI索引生成

**Subagent**: `atlas:repo-context-indexer` (必须使用 Task tool 的 subagent_type="atlas:repo-context-indexer")

**输入** (从文件读取):
- 所有生成的 *.md 文档
- `.meta/project.pkg.json`
- `.meta/modules.pkg.json`
- `.meta/symbols.pkg.json`

**输出** (写入文件):
- `.index/quick-lookup.json` - 快速查询索引
- `.index/symbol-map.json` - 符号映射表
- `.index/doc-graph.json` - 文档关系图

### 索引结构

#### quick-lookup.json
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

#### symbol-map.json
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

#### doc-graph.json
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

**操作**:
1. 扫描所有生成的 markdown 文档
2. 提取关键信息（标题、符号引用、链接关系）
3. 构建快速查询索引，支持符号名、功能名快速定位
4. 生成符号到文档的映射表
5. 分析文档间引用关系，构建文档关系图
6. 输出结构化索引文件到 `.index/` 目录

**Subagent Prompt 必须包含**:
1. 输入文档目录: `.claude/repowiki/`
2. 输出索引目录: `.claude/repowiki/.index/`
3. 索引格式必须符合上述 JSON schema
4. 优先索引高频访问的符号和文档

---

## Phase 6: 上下文优化

**输入** (从文件读取):
- `.index/quick-lookup.json`
- `.index/symbol-map.json`
- `.index/doc-graph.json`

**输出** (写入文件):
- `.claude/wiki-context.json` - Wiki 上下文配置

### wiki-context.json 格式

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

**操作**:
1. 读取索引文件
2. 确定高优先级入口文档（index.md、overview.md 等）
3. 配置快速访问路径，指向索引文件
4. 收集元数据统计信息
5. 定义上下文使用规则（单次查询最大文档数、优先级文档等）
6. 输出 wiki-context.json 到 `.claude/` 目录
7. 该文件可被 Claude Code 自动识别，优化 Wiki 相关查询的上下文加载

**目的**:
- 优化 Claude Code 对 Wiki 的上下文理解和检索效率
- 提供快速访问索引，减少全文扫描
- 智能控制单次对话的上下文大小

---

## Phase 7: 验证（最终检查）

**Subagent**: `atlas:atlas-executor` (必须使用 Task tool 的 subagent_type="atlas:atlas-executor")

**🚨 这是最后一个阶段，必须全面检查所有生成的内容，不能有任何疏漏！**

**输入** (从文件读取):
- 所有生成的 *.md 文档
- `.meta/*.pkg.json` (PKG 文件)
- `.index/*.json` (索引文件)
- `.claude/wiki-context.json` (上下文配置)
- Phase 2 生成的 todos（对照执行结果）

**输出**:
- `.meta/validation-report.md` (写入文件)
- 验证结果摘要 + 最终报告 (返回给主进程)

### 验证项

| 层级 | 项目 | 标准 | 操作 |
|:-----|:-----|:-----|:-----|
| 1 | 核心文档存在 | index.md 必须存在且 ≥10 行 | 检查文件存在性和行数 |
| 2 | 必需文档完整 | architecture/overview.md, guides/development.md 等 | 逐一检查必需文档 |
| 3 | 章节结构正确 | H1/H2 存在，表格格式正确 | 解析 markdown 结构 |
| 4 | 导航链接有效 | index.md 中所有链接指向存在的文件 | 验证相对链接 |
| 5 | 符号覆盖率 | ≥90% (警告) | 对比 symbols.pkg.json |
| 6 | 索引完整性 | quick-lookup.json 包含所有文档 | 对比 .index/ 和文档 |
| 7 | 上下文配置有效 | wiki-context.json 格式正确且路径有效 | 验证 JSON 和路径 |

### 关键检查项

**index.md 专项检查**:
1. 文件存在且内容非空
2. 包含正确的项目名称 (H1)
3. 技术栈表格存在且有数据
4. 导航表格中的链接全部有效
5. 生成时间戳存在

**文档一致性检查**:
1. PKG 文件中记录的模块 → 对应的 symbols/*.md 是否存在
2. 检测到的 API → api/endpoints.md 是否包含
3. 条件生成的文档 → 是否符合生成条件

**索引完整性检查**:
1. .index/ 目录下所有 JSON 文件格式正确
2. quick-lookup.json 中的符号引用有效
3. symbol-map.json 中的文档链接存在
4. doc-graph.json 中的节点对应实际文档

**上下文配置检查**:
1. wiki-context.json 存在且格式正确
2. entryPoints 中的文档路径有效
3. quickAccess 中的索引文件存在

### 验证失败处理

| 问题类型 | 严重性 | 处理方式 |
|:---------|:-------|:---------|
| index.md 不存在/为空 | 🔴 严重 | 报告错误，建议重新执行 Phase 4 |
| 必需文档缺失 | 🔴 严重 | 列出缺失文档，建议补充生成 |
| wiki-context.json 无效 | 🔴 严重 | 报告错误，建议重新执行 Phase 6 |
| 链接失效 | 🟡 警告 | 列出失效链接，建议修复 |
| 符号覆盖不足 | 🟡 警告 | 报告覆盖率，列出未覆盖符号 |
| 章节结构异常 | 🟡 警告 | 报告异常文档，建议检查 |
| 索引不完整 | 🟡 警告 | 列出缺失项，建议重新索引 |

### Subagent Prompt 必须包含

1. Wiki 目录路径: `.claude/repowiki/`
2. 必须检查的核心文档列表
3. 必须检查的索引文件列表: `.index/quick-lookup.json`, `.index/symbol-map.json`, `.index/doc-graph.json`
4. 必须检查的上下文配置: `.claude/wiki-context.json`
5. 验证报告输出路径: `.claude/repowiki/.meta/validation-report.md`
6. 验证项优先级: 核心文档 > 必需文档 > 索引 > 上下文 > 链接 > 覆盖率
7. 返回结构化验证结果 + 最终报告给主进程

---

## 条件生成

| 类别 | 文档 | 条件 |
|:-----|:-----|:-----|
| 核心 | index.md, architecture/overview.md, architecture/structure.md, guides/development.md | 必须 |
| 条件 | architecture/dependencies.md | 存在依赖配置 |
| 条件 | architecture/modules.md, module-graph.md | ≥2 模块 |
| 条件 | architecture/layers.md | 检测到分层 |
| 条件 | architecture/patterns.md | 检测到设计模式 |
| 条件 | api/*.md | 检测到 API |
| 条件 | guides/build.md | 存在构建配置 |
| 条件 | symbols/*.md | --skip-symbols 未指定 |
| 条件 | quality/complexity.md | 检测到复杂度问题 |
| 开放 | features/*.md | 自动检测或 --features |

---

## 文档规范

### 通用

- 标题: H1 文件标题, H2 章节, H3 子节
- 表格: 左对齐, 空值填 `-`
- 代码块: 指定语言
- 链接: 相对路径
- 禁止: TODO/TBD, 断链, 无效 Mermaid

### index.md

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

### architecture/overview.md

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

### architecture/dependencies.md

```markdown
# 依赖分析

## 依赖关系图

\`\`\`mermaid
graph LR
    A[项目] --> B[nestjs]
    A --> C[prisma]
    B --> D[express]
\`\`\`

## 生产依赖

| 包名 | 版本 | 用途 | 重要性 |
|:-----|:-----|:-----|:-------|
| @nestjs/core | ^10.0 | 核心框架 | 核心 |
| prisma | ^5.0 | ORM | 核心 |

## 开发依赖

| 包名 | 版本 | 用途 |
|:-----|:-----|:-----|
| typescript | ^5.0 | 编译 |
| jest | ^29.0 | 测试 |
```

### architecture/module-graph.md

```markdown
# 模块依赖图

## 模块关系

\`\`\`mermaid
graph TD
    User --> Common
    Order --> User
    Order --> Common
    style Common fill:#f9f
\`\`\`

## 循环检测

✅ 未检测到循环依赖

## 耦合度

| 模块 | 入度 | 出度 | 评级 |
|:-----|:-----|:-----|:-----|
| Common | 2 | 0 | 低 |
| User | 1 | 1 | 低 |
| Order | 0 | 2 | 中 |
```

### api/endpoints.md

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

### symbols/index.md

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

### quality/complexity.md

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

### features/{name}.md

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

---

## features/

### 自动检测

| 特征 | 模式 | 文件 |
|:-----|:-----|:-----|
| auth/login/jwt | `**/auth/**`, `**/login*` | authentication.md |
| i18n/locale | `**/i18n/**`, `**/locale/**` | i18n.md |
| websocket | `**/*socket*` | realtime.md |
| upload/file | `**/upload*`, `**/file*` | file-handling.md |
| cache/redis | `**/cache*`, `**/redis*` | caching.md |

### 自定义

`--features auth,payment` 或 `.claude/wiki.config.json`

### 规范

功能名(H1) | 概述(H2) | 核心组件(H2) | 数据流(H2,可选) | 配置项(H2,可选)

---

## 约束

**Subagent 使用（最高优先级）**:
- Phase 1 语义变更检测 → **必须使用 `atlas:repo-semantic-analyzer`**，仅在 INCREMENTAL 模式执行
- Phase 2 规划 → **必须使用 `Plan`**，禁止使用其他 subagent
- Phase 3 信息收集 → **必须使用 `atlas:information-gatherer`**，禁止使用 Plan 或 atlas-executor
- Phase 4 文档生成 → **必须使用 `atlas:atlas-executor`**，禁止使用 Plan 或 information-gatherer
- Phase 5 AI索引生成 → **必须使用 `atlas:repo-context-indexer`**，禁止使用其他 subagent
- Phase 6 上下文优化 → **主进程执行**，生成 wiki-context.json
- Phase 7 验证 → **必须使用 `atlas:atlas-executor`**，全面检查所有生成内容，不能有任何疏漏
- **🚨 混用 subagent 是严重错误，必须严格遵守上述分配！**

**Todos 管理（最高优先级）**:
- Phase 2 的 Plan agent **必须**通过 TodoWrite 生成详细的执行 todos
- Phase 3/4 的 agent **必须**严格按照 todos 顺序执行
- 每完成一个 todo，**必须立即**通过 TodoWrite 标记为 completed
- **🚨 不按 todos 执行是严重错误！**

**执行**: 阶段顺序不可跳跃 | symbols 等待 modules | PKG 是唯一数据媒介 | 优先 Serena MCP

**格式**: 必需章节不可省略 | 表格列数一致 | Mermaid 语法正确 | 相对路径链接

**验证**: 文档≥10行 | 符号覆盖≥90%(警告) | 链接100%有效 | Mermaid无错误

**禁止**: 跳过验证 | 静默忽略失败 | 占位内容 | 硬编码信息

**错误处理**: 无 git→FULL_BUILD | >2000文件无scope→终止 | Serena不可用→降级Grep | 收集失败→跳过依赖任务 | Executor失败→继续其他

---

## 最终报告

执行概况(模式/语言/范围) | 生成统计(文档数/行数/覆盖率) | 验证结果 | 文件列表 | 下一步操作

---

## 预览模式

### 触发方式

```bash
/atlas:repo-wiki --preview
```

### 预览流程

**--preview 模式下，Phase 0-3 正常执行，Phase 4-7 改为预览输出：**

1. **Phase 0-3**: 正常执行（环境检测、变更分析、规划、信息收集）
2. **Phase 4**: 不写入文件，而是生成文档预览
3. **Phase 5-7**: 跳过

### 预览输出格式

```markdown
# Repo Wiki 预览

## 构建信息
| 指标 | 值 |
|:-----|:---|
| 模式 | INCREMENTAL |
| 变更文件 | 3 |
| 影响文档 | 5 |

## 将生成/更新的文档

### 新增文档
| 文件 | 预计行数 | 说明 |
|:-----|:---------|:-----|
| symbols/payment-module.md | ~80 | 新增 payment 模块符号文档 |

### 更新文档
| 文件 | 变更类型 | 影响范围 |
|:-----|:---------|:---------|
| index.md | 更新 | 导航表格新增 payment 链接 |
| symbols/user-module.md | 更新 | UserService.create 签名变更 |
| api/endpoints.md | 更新 | 新增 POST /api/payments |

### 不变文档
- architecture/overview.md
- guides/development.md
- quality/complexity.md

## PKG 数据预览

### 变更符号
| 符号 | 文件 | 变更类型 |
|:-----|:-----|:---------|
| PaymentService | src/payment/payment.service.ts | 新增 |
| UserService.create | src/user/user.service.ts | 签名变更 |

## 预计影响
- 新增文档: 1 个
- 更新文档: 4 个
- 总行数变化: +120 行

---
使用 `/atlas:repo-wiki` 执行实际生成
```

### 使用场景

1. **增量更新验证**: 检查变更检测是否准确识别了影响范围
2. **大型项目预估**: 在执行前了解将生成的文档数量
3. **CI/CD 集成**: 在 PR 中展示文档变更预览

---

## 示例

### 命令用法

```bash
# 基础用法 - 自动检测所有参数
/atlas:repo-wiki

# 预览模式 - 仅显示将要生成的文档，不实际写入
/atlas:repo-wiki --preview

# 英文文档，限定 src 目录
/atlas:repo-wiki --lang en --scope src

# 大项目：跳过符号，串行执行
/atlas:repo-wiki --skip-symbols --mode sequential

# 指定功能点
/atlas:repo-wiki --features auth,payment,notification

# 强制重建，限制并发
/atlas:repo-wiki --force --concurrency 1

# 预览增量更新
/atlas:repo-wiki --preview
```

### 输出示例

**简单库** (5 文件):
```
.claude/repowiki/
├── .meta/           # PKG 数据
├── .index/          # 快速查询索引
├── index.md
├── architecture/
│   ├── overview.md
│   └── structure.md
├── guides/
│   └── development.md
└── symbols/
    └── index.md
```

**Web 应用** (12 文件):
```
.claude/repowiki/
├── .meta/           # PKG 数据
│   ├── project.pkg.json
│   ├── modules.pkg.json
│   ├── symbols.pkg.json
│   └── validation-report.md
├── .index/          # AI 索引
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

### 最终报告示例

```markdown
# Repo Wiki 生成完成

## 执行概况
| 项目 | 值 |
|:-----|:---|
| 模式 | FULL_BUILD |
| 语言 | zh |
| 范围 | . |
| 深度 | 2 |

## 生成统计
| 指标 | 值 |
|:-----|:---|
| 文档数 | 12 |
| 总行数 | 1,245 |
| 符号覆盖率 | 94% |
| 耗时 | 2m 34s |

## 验证结果
✅ 全部通过

## 下一步
git add .claude/repowiki && git commit -m "docs: generate repo wiki"
```
