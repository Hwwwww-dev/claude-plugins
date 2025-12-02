---
description: 自主文档编排器。生成深度结构化的 Repo Wiki，支持项目级到符号级分析，含4层验证机制。
argument-hint: [--force] [--lang zh|en] [--depth N] [--scope path] [--skip-symbols] [--features list] [--mode parallel|limited|sequential] [--concurrency N]
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

---

## 执行流程

Phase 0 环境检测 → Phase 1 规划 → Phase 2 信息收集 → Phase 3 文档生成 → Phase 4 验证

### Subagent 分配（必须严格遵守）

| Phase | 功能 | Subagent | 说明 |
|:------|:-----|:---------|:-----|
| 0 | 环境检测 | 主进程 | 不需要 subagent |
| 1 | 规划 | `Plan` | 必须生成详细 todos |
| 2 | 信息收集 | `atlas:information-gatherer` | 读取 todos 执行 |
| 3 | 文档生成 | `atlas:atlas-executor` | 读取 todos 执行 |
| 4 | 验证 | 主进程 | 不需要 subagent |

**🚨 严禁混用 subagent！Plan 只做规划，information-gatherer 只做信息收集，atlas-executor 只做文档生成！**

### 数据流转

| Phase | 读取 | 输出 | 传递方式 |
|:------|:-----|:-----|:---------|
| 0 | 项目目录、git 状态 | 环境报告 (mode, fileCount, changedFiles) | 内存传递给 Phase 1 |
| 1 | Phase 0 环境报告 | 执行计划 JSON | 内存传递给 Phase 2 |
| 2 | Phase 1 计划 | PKG 文件 (.meta/*.pkg.json) | 文件写入 |
| 3 | PKG 文件 | 文档文件 (*.md) | 文件写入 |
| 4 | 文档文件、PKG 文件 | 验证报告 + 最终报告 | 文件写入 + 输出 |

**关键约束**: Phase 2/3/4 必须从文件读取 PKG，不依赖内存传递

---

## Phase 0: 环境检测

**输入**: 项目目录、git 状态、命令参数

**输出** (传递给 Phase 1):
```json
{
  "mode": "FULL_BUILD | INCREMENTAL",
  "fileCount": 150,
  "changedFiles": ["src/user.ts"],
  "scale": "small | medium | large | huge"
}
```

**操作**:
- 创建目录 `.claude/repowiki/{.meta,architecture,api,guides,decisions,symbols,quality,features}`
- 检测构建模式: FULL_BUILD (Wiki不存在/--force/配置变更) | INCREMENTAL (仅代码变更)
- 判断规模: <100 全量 | 100-500 采样 | 500-2000 分片 | >2000 需 --scope

---

## Phase 1: 规划

**Subagent**: `Plan` (必须使用 Task tool 的 subagent_type="Plan")

**输入**: Phase 0 环境报告

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
Phase 2 - 信息收集（根据需要选择）:
- 收集项目元数据 → .meta/project.pkg.json
- 分析模块结构 → .meta/modules.pkg.json
- 统计代码质量 → .meta/quality.pkg.json
- 提取符号信息 → .meta/symbols.pkg.json（如未 --skip-symbols）

Phase 3 - 文档生成（根据条件生成规则选择）:
- 生成首页和架构文档
- 生成 API 文档（如检测到 API）
- 生成开发指南
- 生成符号文档（如未 --skip-symbols）
- 生成功能文档（如检测到特定功能或 --features）

Phase 4 - 验证:
- 验证文档完整性
- 生成验证报告
```

**🚨 关键要求**:
1. Plan agent **必须**调用 TodoWrite 生成 todos
2. todos 内容**根据项目实际情况动态决定**，尽可能信息
3. 后续 agent **必须严格按照 todos 顺序执行**

**执行计划 JSON** (传递给 Phase 2):
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

## Phase 2: 信息收集

**Subagent**: `atlas:information-gatherer` (必须使用 Task tool 的 subagent_type="atlas:information-gatherer")

**🚨 必须严格按照 Phase 1 生成的 todos 执行，每完成一个 todo 立即标记为 completed**

**输入**: Phase 1 执行计划 + Phase 1 生成的 todos

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

## Phase 3: 文档生成

**Subagent**: `atlas:atlas-executor` (必须使用 Task tool 的 subagent_type="atlas:atlas-executor")

**🚨 必须严格按照 Phase 1 生成的 todos 执行，每完成一个 todo 立即标记为 completed**

**输入** (从文件读取):
- `.meta/project.pkg.json`
- `.meta/modules.pkg.json`
- `.meta/quality.pkg.json`
- `.meta/symbols.pkg.json`
- Phase 1 生成的 todos（必须遵循）

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

## Phase 4: 验证

**输入** (从文件读取):
- 所有生成的 *.md 文档
- `.meta/symbols.pkg.json` (计算覆盖率)

**输出**:
- `.meta/validation-report.md` (写入文件)
- 最终报告 (输出到用户)

### 验证项

| 层级 | 项目 | 标准 |
|:-----|:-----|:-----|
| 1 | 文档存在 | ≥10 行 |
| 2 | 章节完整 | H1/H2 存在 |
| 3 | 符号覆盖 | ≥90% |
| 4 | 链接有效 | 100% |

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
- Phase 1 规划 → **必须使用 `Plan`**，禁止使用其他 subagent
- Phase 2 信息收集 → **必须使用 `atlas:information-gatherer`**，禁止使用 Plan 或 atlas-executor
- Phase 3 文档生成 → **必须使用 `atlas:atlas-executor`**，禁止使用 Plan 或 information-gatherer
- **🚨 混用 subagent 是严重错误，必须严格遵守上述分配！**

**Todos 管理（最高优先级）**:
- Phase 1 的 Plan agent **必须**通过 TodoWrite 生成详细的执行 todos
- Phase 2/3 的 agent **必须**严格按照 todos 顺序执行
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

## 示例

### 命令用法

```bash
# 基础用法 - 自动检测所有参数
/atlas:repo-wiki

# 英文文档，限定 src 目录
/atlas:repo-wiki --lang en --scope src

# 大项目：跳过符号，串行执行
/atlas:repo-wiki --skip-symbols --mode sequential

# 指定功能点
/atlas:repo-wiki --features auth,payment,notification

# 强制重建，限制并发
/atlas:repo-wiki --force --concurrency 1
```

### 输出示例

**简单库** (5 文件):
```
.claude/repowiki/
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
