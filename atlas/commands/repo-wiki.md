---
description: 自主文档编排器。生成深度结构化的 Repo Wiki，支持项目级到符号级分析，含4层验证机制。
argument-hint: [--force] [--lang zh|en] [--depth N] [--scope path] [--skip-symbols]
---

# Repo Wiki 编排器

**角色**: 通过多阶段工作流生成深度结构化的项目文档。

**参数**: $ARGUMENTS

---

## 参数说明

| 参数 | 说明 | 默认值 |
|-----|------|-------|
| `--force` | 强制全量构建，忽略增量检测 | 智能判断 |
| `--lang zh\|en` | 文档输出语言 | zh |
| `--depth N` | 目录分析深度层级 | 2 |
| `--scope path` | 限定分析范围到指定目录 | . (整个项目) |
| `--skip-symbols` | 跳过符号级分析（加速大项目） | false |

---

## 执行流程

```
┌─────────────────────────────────────────────────────────────────┐
│ Phase 0: 环境检测 + 模式判定                                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Phase 1: 分析规划 (Plan Agent)                                   │
│ - 确定分析范围和策略                                              │
│ - 生成 PKG 收集任务清单                                          │
│ - 确定可并行的收集任务                                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Phase 2: 信息收集 (并行 information-gatherer)                     │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │ project PKG  │  │ modules PKG  │  │ quality PKG  │  并行执行  │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│          ↓                                                       │
│  ┌──────────────────────────────────────────────────┐           │
│  │            symbols PKG (依赖 modules)             │  串行执行  │
│  └──────────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Phase 3: 文档生成 (并行 atlas-executor)                          │
│                                                                  │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐   │
│  │ Home+Arch  │ │    API     │ │   Guides   │ │  Symbols   │   │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Phase 4: 4层验证 + 最终报告                                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 0: 环境检测

### 检测项目 (由 agent 执行)

1. **Wiki 状态**: 检查 `.claude/repowiki` 目录是否存在
2. **代码文件数**: 统计项目中的代码文件数量 (ts/tsx/js/jsx/py/go/java/rs)
   - 排除目录: node_modules, .git, dist, build, out, target, .next, .nuxt, .output, coverage, __pycache__, .venv, venv, .env, env, .tox, .mypy_cache, .pytest_cache, vendor, Pods, .gradle, .idea, .vscode, .claude
3. **最近变更**: 获取最近一次提交的变更文件列表 (用于增量模式判断)

### 模式判定规则

| 条件 | 模式 | 说明 |
|-----|------|------|
| Wiki 目录不存在 | FULL_BUILD | 首次生成 |
| 参数含 --force | FULL_BUILD | 强制重建 |
| 关键配置变更 | FULL_BUILD | 架构可能变化 |
| 仅代码文件变更 | INCREMENTAL | 局部更新 |

**关键配置文件**: package.json, go.mod, Cargo.toml, pyproject.toml, tsconfig.json, docker-compose.yml, pom.xml, build.gradle

### 规模策略

| 文件数 | 规模 | 策略 |
|-------|------|------|
| < 100 | 小型 | 全量分析，无限制 |
| 100-500 | 中型 | 智能采样，depth=2 |
| 500-2000 | 大型 | 分片生成，核心模块优先 |
| > 2000 | 超大 | 必须 --scope 指定范围 |

---

## Phase 1: 分析规划

```
Task(subagent_type="Plan")
prompt: |
  ## 任务
  为 Repo Wiki 生成制定分析计划

  ## 输入
  - 模式: [FULL_BUILD | INCREMENTAL]
  - 文件数: [数量]
  - 变更文件: [列表，仅增量模式]
  - 参数: depth=[N], scope=[path], skip-symbols=[bool]

  ## 输出要求
  1. 确定需要收集的 PKG 层级
  2. 识别可并行执行的收集任务
  3. 确定模块优先级（核心 > 工具 > 测试）
  4. 预估 Token 消耗，必要时建议分片

  ## 输出格式
  ```json
  {
    "parallel_batch_1": ["project", "modules", "quality"],
    "sequential": ["symbols"],
    "priority_modules": ["src/core", "src/api"],
    "skip_paths": ["test/", "mock/", "__fixtures__/"],
    "estimated_tokens": 50000
  }
  ```
```

---

## Phase 2: 信息收集

### 2.1 并行收集 (同一消息发起)

```
// 同时发起 3 个 information-gatherer

Task(subagent_type="atlas:information-gatherer")
prompt: |
  任务 ID: repo-wiki-project
  输出格式: PKG
  PKG 层级: project
  输出: .claude/repowiki/.pkg/project.json

  收集内容:
  - 项目元数据 (name, version, license, author, repository)
  - 技术栈 (language, framework, database, packageManager)
  - 目录拓扑 (tree, roles, stats)
  - 依赖列表 (production, development)
  - 构建配置 (scripts, envVars, docker, ci)

---

Task(subagent_type="atlas:information-gatherer")
prompt: |
  任务 ID: repo-wiki-modules
  输出格式: PKG
  PKG 层级: modules
  分析深度: [depth]
  输出: .claude/repowiki/.pkg/modules.json

  收集内容:
  - 模块边界 (name, path, entry, exports)
  - 依赖关系 (graph, cycles)
  - 分层识别 (controllers, services, repositories)
  - 设计模式 (singleton, factory, observer, di)

---

Task(subagent_type="atlas:information-gatherer")
prompt: |
  任务 ID: repo-wiki-quality
  输出格式: PKG
  PKG 层级: quality
  输出: .claude/repowiki/.pkg/quality.json

  收集内容:
  - 文件统计 (count, avgLines, maxLines)
  - 大函数 (path, name, lines > 50)
  - 深嵌套 (path, name, depth > 4)
  - 重构建议
```

### 2.2 串行收集 (等待 modules 完成)

```
Task(subagent_type="atlas:information-gatherer")
prompt: |
  任务 ID: repo-wiki-symbols
  输出格式: PKG
  PKG 层级: symbols
  上下文: 读取 .claude/repowiki/.pkg/modules.json
  输出: .claude/repowiki/.pkg/symbols.json

  工具优先级: Serena MCP > Grep

  收集内容:
  - 类/接口 (name, visibility, extends, implements, generics)
  - 方法 (name, params, returns, description)
  - 类型定义 (type, interface, alias)
  - API 端点 (method, path, handler, auth)

  采样规则:
  - 优先级: public > protected > private
  - 跳过: @internal, @private, test/, mock/, fixtures/
  - 分批: 符号数 > 100 时每批 50 个
```

---

## Phase 3: 文档生成

### 3.1 并行生成 (同一消息发起 4 个 executor)

```
// Executor 1: 首页 + 架构文档
Task(subagent_type="atlas:atlas-executor")
prompt: |
  子任务: 生成首页和架构文档
  输入: .claude/repowiki/.pkg/project.json, modules.json
  语言: [lang]

  生成文件:
  - 00-Home.md
  - 01-Architecture/Overview.md
  - 01-Architecture/Structure.md
  - 01-Architecture/Dependencies.md
  - 01-Architecture/Modules.md
  - 01-Architecture/Module-Graph.md
  - 01-Architecture/Layers.md
  - 01-Architecture/Patterns.md

  严格遵循【文档格式规范】章节的模板

---

// Executor 2: API 文档
Task(subagent_type="atlas:atlas-executor")
prompt: |
  子任务: 生成 API 文档
  输入: .claude/repowiki/.pkg/symbols.json
  语言: [lang]

  生成文件:
  - 02-API/Endpoints.md
  - 02-API/Types.md

  严格遵循【文档格式规范】章节的模板

---

// Executor 3: 指南文档
Task(subagent_type="atlas:atlas-executor")
prompt: |
  子任务: 生成开发指南
  输入: .claude/repowiki/.pkg/project.json, quality.json
  语言: [lang]

  生成文件:
  - 03-Guides/Development.md
  - 03-Guides/Build.md
  - 04-Decisions/ADR-Log.md
  - 06-Quality/Complexity.md

  严格遵循【文档格式规范】章节的模板

---

// Executor 4: 符号文档
Task(subagent_type="atlas:atlas-executor")
prompt: |
  子任务: 生成符号文档
  输入: .claude/repowiki/.pkg/symbols.json
  语言: [lang]

  生成文件:
  - 05-Symbols/Index.md
  - 05-Symbols/Types.md
  - 05-Symbols/{ModuleName}.md (每个模块一个文件)

  严格遵循【文档格式规范】章节的模板
```

---

## Phase 4: 验证与报告

### 4层验证

| 层级 | 验证项 | 通过标准 | 失败处理 |
|-----|--------|---------|---------|
| 1. 检查清单 | 每个文档存在且非空 | 所有文件 ≥ 10 行 | 列出缺失文件 |
| 2. 内容校验 | 必需章节完整 | 所有 # 标题存在 | 列出缺失章节 |
| 3. 符号覆盖 | 文档化比例 | ≥ 90% 覆盖率 | 列出未覆盖符号 |
| 4. 链接校验 | 相对链接有效 | 100% 链接可达 | 列出失效链接 |

### 验证报告格式

写入 `.claude/repowiki/.validation-report.md`:

```markdown
# 验证报告

生成时间: {ISO时间戳}
模式: {FULL_BUILD | INCREMENTAL}

## 1. 文档清单

| 文档 | 状态 | 行数 |
|-----|------|-----|
| 00-Home.md | ✅ | 45 |
| 01-Architecture/Overview.md | ✅ | 120 |
| ... | ... | ... |

## 2. 章节完整性

| 文档 | 缺失章节 |
|-----|---------|
| (无缺失则不显示此表) | |

## 3. 符号覆盖率

- 总符号数: {N}
- 已文档化: {M} ({M/N * 100}%)
- 未覆盖: {列表}

## 4. 链接校验

- 总链接数: {N}
- 有效: {M}
- 失效: {列表}

## 验证结果

{✅ 通过 | ⚠️ 部分通过 (N 项警告) | ❌ 失败 (N 项错误)}
```

---

## 输出目录结构

```
.claude/repowiki/
│
├── .pkg/                           # PKG 缓存目录 (内部使用，不提交到 git)
│   ├── project.json                #   项目级 PKG：元数据、技术栈、依赖
│   ├── modules.json                #   模块级 PKG：边界、依赖图、分层
│   ├── symbols.json                #   符号级 PKG：类、函数、类型、API
│   └── quality.json                #   质量级 PKG：复杂度、警告
│
├── 00-Home.md                      # 首页：项目概览、技术栈、快速开始、导航
│
├── 01-Architecture/                # 架构文档目录
│   ├── Overview.md                 #   架构总览：系统架构图(Mermaid)、核心模块表、设计理念
│   ├── Structure.md                #   目录结构：目录树、各目录职责说明、文件分布统计
│   ├── Dependencies.md             #   依赖分析：依赖关系图(Mermaid)、生产/开发依赖表
│   ├── Modules.md                  #   模块边界：模块列表、入口文件、导出接口
│   ├── Module-Graph.md             #   模块依赖：模块依赖图(Mermaid)、循环检测、耦合度
│   ├── Layers.md                   #   分层架构：Controller/Service/Repository 分层说明
│   └── Patterns.md                 #   设计模式：识别到的模式及其应用位置
│
├── 02-API/                         # API 文档目录
│   ├── Endpoints.md                #   端点列表：Method/Path/Handler/Auth 表格
│   └── Types.md                    #   类型定义：请求/响应类型、共享类型
│
├── 03-Guides/                      # 开发指南目录
│   ├── Development.md              #   开发指南：环境要求、安装步骤、开发命令
│   └── Build.md                    #   构建配置：构建脚本、环境变量、Docker、CI/CD
│
├── 04-Decisions/                   # 决策记录目录
│   └── ADR-Log.md                  #   架构决策：MADR 格式的决策记录
│
├── 05-Symbols/                     # 符号文档目录
│   ├── Index.md                    #   符号索引：按类型分类的符号清单
│   ├── Types.md                    #   类型汇总：所有 type/interface 定义
│   └── {ModuleName}.md             #   模块符号：该模块的类、函数、类型详情
│
├── 06-Quality/                     # 质量报告目录
│   └── Complexity.md               #   复杂度：文件统计、大函数、深嵌套、重构建议
│
└── .validation-report.md           # 验证报告 (内部使用)
```

---

## 文档格式规范

### 通用规则

| 规则 | 说明 |
|-----|------|
| 标题层级 | 文件标题用 `#`，章节用 `##`，子节用 `###` |
| 表格对齐 | 所有表格列左对齐，使用 `\|:--\|` 语法 |
| 代码块 | 必须指定语言，如 \`\`\`typescript |
| Mermaid | 必须用 \`\`\`mermaid 包裹，图表类型在首行 |
| 链接 | 全部使用相对路径，如 `./01-Architecture/Overview.md` |
| 空行 | 章节之间空一行，表格前后各空一行 |
| 占位符 | 禁止使用 TODO、TBD、待补充等占位文字 |

### 00-Home.md

```markdown
# {项目名称}

> {一句话描述，从 package.json description 或 README 提取}

## 技术栈

| 类型 | 技术 | 版本 |
|:-----|:-----|:-----|
| 语言 | {language} | {version} |
| 框架 | {framework} | {version} |
| 数据库 | {database} | {version} |
| 运行时 | {runtime} | {version} |

## 快速开始

### 环境要求

- {runtime} >= {version}
- {packageManager} >= {version}

### 安装

\`\`\`bash
{install_command}
\`\`\`

### 启动

\`\`\`bash
{start_command}
\`\`\`

## 文档导航

| 分类 | 文档 | 说明 |
|:-----|:-----|:-----|
| 架构 | [Overview](./01-Architecture/Overview.md) | 系统架构总览 |
| 架构 | [Dependencies](./01-Architecture/Dependencies.md) | 依赖分析 |
| API | [Endpoints](./02-API/Endpoints.md) | API 端点列表 |
| 开发 | [Development](./03-Guides/Development.md) | 开发指南 |
| 符号 | [Index](./05-Symbols/Index.md) | 符号索引 |

---

*自动生成于 {YYYY-MM-DDTHH:mm:ssZ} | [重新生成](/atlas:repo-wiki --force)*
```

### 01-Architecture/Overview.md

```markdown
# 架构总览

## 系统架构图

\`\`\`mermaid
graph TD
    subgraph "{layer1_name}"
        A[{component1}]
        B[{component2}]
    end
    subgraph "{layer2_name}"
        C[{component3}]
        D[{component4}]
    end
    subgraph "{layer3_name}"
        E[{component5}]
        F[({database})]
    end

    A --> C
    B --> C
    C --> D
    D --> E
    E --> F
\`\`\`

## 核心模块

| 模块 | 路径 | 职责 | 核心文件 |
|:-----|:-----|:-----|:---------|
| {ModuleName} | {path} | {responsibility} | {main_files} |

## 技术决策

| 决策 | 选型 | 理由 |
|:-----|:-----|:-----|
| 框架 | {framework} | {reason} |
| ORM | {orm} | {reason} |
| 认证 | {auth} | {reason} |

## 设计理念

{2-3 段落说明架构设计的核心理念、原则和约束}
```

### 01-Architecture/Dependencies.md

```markdown
# 依赖分析

## 依赖关系图

\`\`\`mermaid
graph LR
    subgraph "核心依赖"
        A[{project}] --> B[{core_dep1}]
        A --> C[{core_dep2}]
    end
    subgraph "间接依赖"
        B --> D[{indirect_dep1}]
        C --> E[{indirect_dep2}]
    end
\`\`\`

## 生产依赖

| 包名 | 版本 | 用途 | 重要性 |
|:-----|:-----|:-----|:-------|
| {name} | ^{version} | {purpose} | {核心/辅助} |

## 开发依赖

| 包名 | 版本 | 用途 |
|:-----|:-----|:-----|
| {name} | ^{version} | {purpose} |

## 依赖风险

| 风险 | 包名 | 说明 | 建议 |
|:-----|:-----|:-----|:-----|
| 版本过旧 | {name} | 当前 {v1}，最新 {v2} | 升级到 {v2} |
| 无维护 | {name} | 最后更新 {date} | 寻找替代 |
```

### 01-Architecture/Module-Graph.md

```markdown
# 模块依赖图

## 模块关系

\`\`\`mermaid
graph TD
    A[{Module1}] --> B[{Module2}]
    A --> C[{Module3}]
    B --> D[{SharedModule}]
    C --> D

    style D fill:#f9f,stroke:#333
\`\`\`

## 循环依赖检测

{✅ 未检测到循环依赖}

或

{⚠️ 发现循环依赖:}
| 循环路径 | 建议 |
|:---------|:-----|
| A → B → C → A | 提取公共逻辑到 SharedModule |

## 模块耦合度

| 模块 | 入度 | 出度 | 总耦合 | 评级 |
|:-----|:-----|:-----|:-------|:-----|
| {module} | {in} | {out} | {total} | {低/中/高} |

## 依赖方向建议

{说明理想的依赖方向，如：表现层 → 业务层 → 数据层}
```

### 02-API/Endpoints.md

```markdown
# API 端点

## 概览

| 指标 | 值 |
|:-----|:---|
| 总端点数 | {count} |
| 需认证 | {auth_count} |
| 公开 | {public_count} |

## 端点列表

| Method | Path | Handler | Auth | Description |
|:-------|:-----|:--------|:----:|:------------|
| GET | /api/v1/users | UserController.list | ✓ | 获取用户列表 |
| POST | /api/v1/users | UserController.create | ✓ | 创建用户 |
| GET | /api/v1/users/:id | UserController.findOne | ✓ | 获取单个用户 |
| PUT | /api/v1/users/:id | UserController.update | ✓ | 更新用户 |
| DELETE | /api/v1/users/:id | UserController.remove | ✓ | 删除用户 |

## 按模块分组

### {ModuleName}

| Method | Path | Handler | Auth |
|:-------|:-----|:--------|:----:|
| {METHOD} | {path} | {handler} | {✓/✗} |

## 错误码

| 状态码 | 含义 | 场景 |
|:-------|:-----|:-----|
| 400 | Bad Request | 参数校验失败 |
| 401 | Unauthorized | 未登录 |
| 403 | Forbidden | 无权限 |
| 404 | Not Found | 资源不存在 |
| 500 | Internal Error | 服务器错误 |
```

### 05-Symbols/Index.md

```markdown
# 符号索引

## 统计

| 类型 | 数量 |
|:-----|:-----|
| 类 (Class) | {count} |
| 接口 (Interface) | {count} |
| 函数 (Function) | {count} |
| 类型 (Type) | {count} |
| 常量 (Constant) | {count} |
| **总计** | **{total}** |

## 按模块分类

| 模块 | 类 | 接口 | 函数 | 类型 | 详情 |
|:-----|:---|:-----|:-----|:-----|:-----|
| {ModuleName} | {n} | {n} | {n} | {n} | [查看](./ModuleName.md) |

## 公开 API

以下是对外暴露的主要符号：

### 类

| 类名 | 模块 | 说明 |
|:-----|:-----|:-----|
| {ClassName} | {module} | {description} |

### 函数

| 函数名 | 模块 | 签名 |
|:-------|:-----|:-----|
| {funcName} | {module} | `{signature}` |

### 类型

| 类型名 | 模块 | 说明 |
|:-------|:-----|:-----|
| {TypeName} | {module} | {description} |
```

### 05-Symbols/{ModuleName}.md

```markdown
# {ModuleName} 模块

## 概览

| 指标 | 值 |
|:-----|:---|
| 路径 | `{module_path}` |
| 文件数 | {file_count} |
| 类/接口 | {class_count} |
| 函数 | {func_count} |
| 类型 | {type_count} |

## 类

### {ClassName}

\`\`\`typescript
@{Decorator}
class {ClassName} extends {BaseClass} implements {Interface} {
  // 属性和方法签名
}
\`\`\`

| 元素 | 值 |
|:-----|:---|
| 装饰器 | `@{Decorator}` |
| 继承 | {BaseClass} |
| 实现 | {Interface1}, {Interface2} |
| 泛型 | `<{T}, {K}>` |

#### 属性

| 属性 | 类型 | 可见性 | 默认值 | 说明 |
|:-----|:-----|:-------|:-------|:-----|
| {name} | `{type}` | public | {default} | {description} |

#### 方法

| 方法 | 签名 | 说明 |
|:-----|:-----|:-----|
| {name} | `({params}) => {return}` | {description} |

---

## 接口

### {InterfaceName}

\`\`\`typescript
interface {InterfaceName} extends {BaseInterface} {
  {property}: {type};
  {method}({params}): {return};
}
\`\`\`

| 成员 | 类型 | 可选 | 说明 |
|:-----|:-----|:----:|:-----|
| {member} | `{type}` | {?} | {description} |

---

## 函数

| 函数名 | 签名 | 说明 |
|:-------|:-----|:-----|
| {name} | `({params}) => {return}` | {description} |

### {functionName}

\`\`\`typescript
function {functionName}<{T}>({params}): {ReturnType} {
  // ...
}
\`\`\`

| 参数 | 类型 | 必填 | 说明 |
|:-----|:-----|:----:|:-----|
| {param} | `{type}` | ✓ | {description} |

**返回值**: `{ReturnType}` - {description}

---

## 类型定义

\`\`\`typescript
type {TypeName} = {
  {field}: {type};
};

interface {InterfaceName} {
  {field}: {type};
}

enum {EnumName} {
  {Member} = '{value}',
}
\`\`\`
```

### 06-Quality/Complexity.md

```markdown
# 复杂度分析

## 文件统计

| 指标 | 值 |
|:-----|:---|
| 总文件数 | {total_files} |
| 总代码行数 | {total_lines} |
| 平均文件行数 | {avg_lines} |
| 最大文件 | `{max_file}` ({max_lines} 行) |

## 文件分布

| 行数范围 | 文件数 | 占比 |
|:---------|:-------|:-----|
| 1-50 | {n} | {p}% |
| 51-100 | {n} | {p}% |
| 101-200 | {n} | {p}% |
| 201-500 | {n} | {p}% |
| 500+ | {n} | {p}% |

## 大函数警告

> 函数超过 50 行建议拆分

| 文件 | 函数 | 行数 | 建议 |
|:-----|:-----|:-----|:-----|
| `{file}` | {func} | {lines} | {suggestion} |

## 深嵌套警告

> 嵌套超过 4 层影响可读性

| 文件 | 函数 | 嵌套层数 | 建议 |
|:-----|:-----|:---------|:-----|
| `{file}` | {func} | {depth} | {suggestion} |

## 重构建议

### 高优先级

1. **{文件/模块}**: {具体问题} → {建议措施}

### 中优先级

1. **{文件/模块}**: {具体问题} → {建议措施}

### 低优先级

1. **{文件/模块}**: {具体问题} → {建议措施}
```

---

## 约束

### 执行约束

| 约束 | 说明 |
|:-----|:-----|
| 阶段顺序 | Phase 0 → 1 → 2 → 3 → 4，不可跳跃 |
| 并行规则 | 同阶段无依赖任务必须并行，有依赖任务串行 |
| 数据传递 | PKG JSON 是阶段间唯一数据媒介，禁止跨阶段直接传递 |
| 符号分析 | 必须优先使用 Serena MCP，降级时输出警告 |
| 增量模式 | 仅重新收集变更模块的 PKG，仅重新生成受影响文档 |

### 格式约束

| 约束 | 说明 |
|:-----|:-----|
| 模板强制 | 所有文档必须严格遵循【文档格式规范】章节的模板 |
| 章节完整 | 每个模板中的 `##` 章节均为必需，不可省略 |
| 表格格式 | 表头必须存在，列数必须一致，空值填 `-` |
| Mermaid | 架构图、依赖图、模块图为必需，语法必须正确 |
| 链接格式 | 必须使用相对路径 `./path/file.md`，锚点使用 `#section` |

### 验证约束

| 约束 | 阈值 | 失败处理 |
|:-----|:-----|:---------|
| 文档最小行数 | ≥ 10 行 | 报错并列出文件 |
| 符号覆盖率 | ≥ 90% | 警告并列出未覆盖 |
| 链接有效性 | 100% | 报错并列出失效链接 |
| Mermaid 语法 | 无错误 | 报错并定位错误行 |

### 禁止行为

| 禁止 | 后果 |
|:-----|:-----|
| 跳过验证阶段 | 验证未通过不得输出最终报告 |
| 静默忽略失败 | 所有失败必须在报告中明确说明 |
| 使用占位内容 | TODO/TBD/待补充 等视为验证失败 |
| 硬编码项目信息 | 所有信息必须从 PKG 读取 |
| 修改 PKG 格式 | PKG 结构由 information-gatherer 定义 |

### 错误处理

| 阶段 | 错误 | 处理 |
|:-----|:-----|:-----|
| Phase 0 | 无 git 历史 | 使用 FULL_BUILD 模式 |
| Phase 0 | 文件数 > 2000 且无 --scope | 终止并提示指定范围 |
| Phase 1 | Plan 超时 | 使用默认并行策略 |
| Phase 2 | Serena 不可用 | 降级 Grep 并警告 |
| Phase 2 | 某个 PKG 收集失败 | 跳过依赖该 PKG 的后续任务 |
| Phase 3 | 某个 Executor 失败 | 继续其他 Executor，汇总报告失败项 |
| Phase 4 | 覆盖率 < 90% | 警告但继续，在报告中标注 |
| Phase 4 | 链接失效 | 报错，列出所有失效链接 |

---

## 最终报告格式

```markdown
# Repo Wiki 生成完成

## 执行概况

| 项目 | 值 |
|:-----|:---|
| 模式 | {FULL_BUILD \| INCREMENTAL} |
| 语言 | {中文 \| English} |
| 分析范围 | {scope} |
| 分析深度 | {depth} |

## 生成统计

| 指标 | 值 |
|:-----|:---|
| 文档数 | {count} |
| 总行数 | {lines} |
| 符号覆盖率 | {coverage}% |
| 耗时 | {duration} |

## 验证结果

{✅ 全部通过}

或

{⚠️ 部分通过}
| 警告项 | 说明 |
|:-------|:-----|
| 符号覆盖率 | {coverage}% < 90% |

或

{❌ 验证失败}
| 失败项 | 说明 |
|:-------|:-----|
| 缺失文档 | {list} |
| 失效链接 | {list} |

## 生成文件

\`\`\`
.claude/repowiki/
├── 00-Home.md
├── 01-Architecture/ (7 files)
├── 02-API/ (2 files)
├── 03-Guides/ (2 files)
├── 04-Decisions/ (1 file)
├── 05-Symbols/ ({n} files)
└── 06-Quality/ (1 file)
\`\`\`

## 下一步

\`\`\`bash
# 查看文档
cat .claude/repowiki/00-Home.md

# 提交到版本控制
git add .claude/repowiki
git commit -m "docs: generate repo wiki"
\`\`\`
```
