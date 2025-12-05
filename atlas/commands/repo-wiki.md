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

Phase 0 环境检测 → Phase 1 语义变更检测 → Phase 2 规划 → Phase 3 信息收集 → Phase 4 文档生成 → Phase 5 AI索引生成 → Phase 6 上下文优化 → Phase 7 并行验证与自动修复

### Subagent 分配（必须严格遵守）

| Phase | 功能 | Subagent | 并行 | 说明 |
|:------|:-----|:---------|:-----|:-----|
| 0 | 环境检测 | 主进程 | - | 不需要 subagent |
| 1 | 语义变更检测 | `atlas:repo-semantic-analyzer` | - | 检测语义级变更 |
| 2 | 规划 | `Plan` | - | 必须生成详细 todos |
| 3 | 信息收集 | `atlas:information-gatherer` | 推荐 **4+1** | 推荐并行4个(project/modules/quality/api) + 串行1个(symbols)，可用 Python 脚本辅助 |
| 4 | 文档生成 | `atlas:atlas-executor` | 推荐 **4个** | 推荐并行4个(home-arch/api/guides/symbols) |
| 5 | AI索引生成 | `atlas:repo-context-indexer` | - | 生成快速查询索引 |
| 6 | 上下文优化 | 主进程 | - | 生成 wiki-context.json |
| 7.1 | 并行验证 | `atlas:information-gatherer` | **必须 4个** | 4 个验证器并行检查 |
| 7.3 | 自动修复 | `atlas:atlas-executor` | 按需 | 修复 critical 问题（最多 2 轮）|
| 7.4 | 清理 | 主进程 | - | 删除临时脚本和中间文件 |

**🚨 严禁混用 subagent！Plan 只做规划，information-gatherer 只做信息收集，atlas-executor 负责文档生成和验证，repo-semantic-analyzer 只做变更检测，repo-context-indexer 只做索引生成！**

**🚨 当 `--mode parallel` 时，Phase 3/4 必须并行执行！同时启动多个 subagent！**

### 数据流转

| Phase | 读取 | 输出 | 传递方式 |
|:------|:-----|:-----|:---------|
| 0 | 项目目录、git 状态 | 环境报告 (mode, fileCount, changedFiles) | 内存传递给 Phase 1/2 |
| 1 | Phase 0 环境报告、git diff | 变更影响分析 (.meta/semantic-changes.json) | 文件写入 + 传递给 Phase 2 |
| 2 | Phase 0/1 报告 | 执行计划 JSON | 内存传递给 Phase 3 |
| 3 | Phase 2 计划 | PKG 文件 (project/modules/quality/api/symbols.pkg.json)，临时脚本 (.scripts/*.py) | 文件写入 |
| 4 | PKG 文件 | 文档文件 (*.md) | 文件写入 |
| 5 | 文档文件、PKG 文件 | 索引文件 (.index/*.json) | 文件写入 |
| 6 | 索引文件 | wiki-context.json | 文件写入 |
| 7.1 | 所有生成内容 | 验证结果 (.meta/v*.json) | 文件写入 |
| 7.2 | 验证结果 | 问题收集 (.meta/validation-issues.json) | 文件写入 |
| 7.3 | 问题收集 | 修复后的文件 | 文件写入 |
| 7.4 | - | 清理 .scripts/, .tmp/, v*.json | 文件删除 |
| 7.5 | 所有验证结果 | 验证报告 (.meta/validation-report.md) | 文件写入 |

**关键约束**:
- Phase 3/4/5/6/7 必须从文件读取 PKG/索引，不依赖内存传递
- **临时文件必须在 Phase 7.4 清理**: `.scripts/`, `.tmp/`, `v*.json`, `validation-issues.json`

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
- 创建目录 `.claude/repowiki/{.meta,.index,.scripts,.tmp,architecture,api,guides,decisions,symbols,quality,features}`
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

## Phase 3: 信息收集（深度收集）

**Subagent**: `atlas:information-gatherer` (必须使用 Task tool 的 subagent_type="atlas:information-gatherer")

**🚨🚨🚨 核心原则：宁多勿少，宁慢勿错！🚨🚨🚨**

**信息收集必须做到**:
1. **深度优先** - 对每个模块/符号必须读取实际源代码
2. **完整覆盖** - 不能遗漏任何公开的类、函数、接口、API
3. **多次验证** - 对关键信息（特别是 API 端点）必须反复确认
4. **源码为准** - 所有信息必须从源代码中提取，禁止推测

**🚨 必须严格按照 Phase 2 生成的 todos 执行，每完成一个 todo 立即标记为 completed**

**输入**: Phase 2 执行计划 + Phase 2 生成的 todos

**输出** (写入文件):
- `.meta/project.pkg.json`
- `.meta/modules.pkg.json`
- `.meta/quality.pkg.json`
- `.meta/api.pkg.json`
- `.meta/symbols.pkg.json`

### 信息收集强制要求

**🚨 必须遵守的收集原则**:

1. **API 端点收集**:
   - 必须扫描所有路由定义文件（controller、router 等）
   - 必须读取装饰器/注解内容（`@Get()`, `@Post()`, `router.get()` 等）
   - 必须提取完整的路由路径、HTTP 方法、处理函数
   - **禁止根据函数名猜测路由**
   - **禁止根据文件名猜测端点**

2. **符号收集**:
   - 必须使用 Serena MCP 的 `find_symbol` / `get_symbols_overview`
   - 对每个类必须读取其方法列表
   - 对每个函数必须提取实际参数签名
   - **禁止根据命名约定猜测签名**

3. **依赖收集**:
   - 必须读取 `package.json` / `go.mod` / `requirements.txt` 等
   - 必须分析实际的 import/require 语句
   - **禁止假设存在某个依赖**

4. **配置收集**:
   - 必须读取 `.env.example` / 配置文件
   - 必须提取实际使用的环境变量
   - **禁止猜测配置项名称**

### 并行收集策略

**推荐并行启动多个 `atlas:information-gatherer` subagent 以提高效率。**

**执行方式**: 使用 **Task tool 调用** 同时启动多个收集器。

| 收集器 | Subagent | 依赖 | 可并行 |
|:-------|:---------|:-----|:-------|
| project | `atlas:information-gatherer` | 无 | ✅ |
| modules | `atlas:information-gatherer` | 无 | ✅ |
| quality | `atlas:information-gatherer` | 无 | ✅ |
| api | `atlas:information-gatherer` | 无 | ✅ |
| symbols | `atlas:information-gatherer` | modules | ❌（等待 modules 完成） |

**并行执行分两轮**:
1. **第一轮（可并行）**: project、modules、quality、api 四个收集器
2. **第二轮（串行）**: 等待 modules 完成后，启动 symbols 收集器

**并行模式**:

| 模式 | 行为 | 并行要求 |
|:-----|:-----|:---------|
| parallel | 第一轮 4 个并行 + 第二轮 symbols | **必须并行** |
| limited | 受 --concurrency 限制的并行数 | 推荐并行 |
| sequential | 全部串行执行 | 串行执行 |

**🚨 当 `--mode parallel` 时，必须并行启动多个收集器！**

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

#### api → .meta/api.pkg.json

**🚨🚨🚨 API 端点收集强制规则 🚨🚨🚨**

工具: Serena MCP 优先，降级 Grep

| 分类 | 字段 |
|:-----|:-----|
| 端点 | endpoints[].{method, path, handler, controller, auth, middlewares[], params[], response, description} |
| 路由组 | groups[].{prefix, controller, endpoints[]} |
| 认证 | authStrategies[].{name, type, scope} |
| 中间件 | globalMiddlewares[], routeMiddlewares[] |

**必须执行的步骤**:
1. **扫描路由文件** - 必须找到所有 controller/router 文件
2. **读取装饰器** - 必须读取 `@Get()`, `@Post()`, `@Put()`, `@Delete()`, `@Patch()` 等
3. **提取路由路径** - 从装饰器参数中提取，如 `@Get('/users/:id')`
4. **确认处理函数** - 必须确认对应的处理方法名
5. **检查认证装饰器** - 如 `@Auth()`, `@UseGuards()`, `@Public()` 等
6. **提取路由前缀** - 从 `@Controller()` 或 router 定义中提取

**Express/Koa 项目**:
```javascript
// 必须搜索这些模式
router.get('/path', handler)
router.post('/path', handler)
app.get('/path', handler)
app.use('/prefix', router)
```

**NestJS 项目**:
```typescript
// 必须搜索这些装饰器
@Controller('prefix')
@Get('path')
@Post('path')
@UseGuards(AuthGuard)
```

**Go 项目**:
```go
// 必须搜索这些模式
r.GET("/path", handler)
r.POST("/path", handler)
r.Group("/prefix")
http.HandleFunc("/path", handler)
```

**🚨 绝对禁止**:
- 根据函数名猜测路由（如 `getUsers` → `/users`）
- 根据文件名猜测端点（如 `user.controller.ts` → `/user`）
- 假设存在标准 CRUD 路由
- 编造任何未在代码中明确定义的端点
- 推断路由参数类型（必须从装饰器/注解中提取）

#### symbols (依赖 modules) → .meta/symbols.pkg.json

工具: Serena MCP **强制使用**，**禁止猜测**

**🚨 零遗漏原则（最高优先级）🚨**:
1. **必须使用 Serena MCP 完整扫描所有代码文件**
2. **禁止根据文件名/目录猜测类名**
3. **禁止采样或跳过任何 public/protected 符号**
4. **每个类必须读取完整方法列表**（使用 `find_symbol(depth=1)`）
5. **宁慢勿漏，宁多勿少**

| 分类 | 字段 |
|:-----|:-----|
| 类 | classes[].{name, module, path, visibility, extends, implements, properties[], methods[]} |
| 接口 | interfaces[].{name, module, extends, members[]} |
| 函数 | functions[].{name, module, params[], returns, description} |
| 类型 | types[].{name, kind, definition} |

**分批处理策略**（避免内存溢出）:
- 每批 50 个文件
- 增量写入 JSON
- **只过滤 private 符号**，其他全部保留
- **禁止跳过 test/mock/generated 代码**

### Python 脚本辅助（可选）

当 Serena MCP 不可用或需要处理特定框架时，可生成临时 Python 脚本辅助提取：

**🚨 关键**: 脚本必须**根据项目实际使用的语言和框架动态生成**，不可使用固定模板！

**脚本存放**: `.claude/repowiki/.scripts/` (临时目录，验证后删除)

**适用场景**:
| 场景 | 说明 |
|:-----|:-----|
| 大型项目 | >500 文件时提高效率 |
| 特定框架 | FastAPI/Django/NestJS/Express/Spring 等路由提取 |
| Serena 降级 | LSP 不可用时的备选 |
| 多语言项目 | 需要同时分析多种语言 |

**脚本生成原则**:
1. **检测项目技术栈**: 分析 package.json / requirements.txt / go.mod / pom.xml 等
2. **选择对应解析器**: Python AST / TypeScript Compiler API / Go AST 等
3. **适配框架特性**: 根据框架的路由定义方式生成提取逻辑
4. **输出 PKG 格式**: 脚本输出必须符合 `.meta/*.pkg.json` 的结构

**脚本示例** (仅供参考，需根据项目实际情况生成):

<details>
<summary>Python 项目示例 (AST)</summary>

```python
#!/usr/bin/env python3
"""符号提取脚本 - 自动生成，验证后删除"""
import ast, json, sys

def extract_symbols(file_path: str) -> dict:
    with open(file_path, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read())
    symbols = {"classes": [], "functions": []}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            symbols["classes"].append({
                "name": node.name, "line": node.lineno,
                "methods": [m.name for m in node.body if isinstance(m, ast.FunctionDef)]
            })
        elif isinstance(node, ast.FunctionDef) and node.col_offset == 0:
            symbols["functions"].append({"name": node.name, "line": node.lineno})
    return symbols

if __name__ == "__main__":
    print(json.dumps(extract_symbols(sys.argv[1]), indent=2))
```
</details>

<details>
<summary>TypeScript/JavaScript 项目示例</summary>

```python
#!/usr/bin/env python3
"""TypeScript 符号提取 - 使用正则"""
import re, json, sys
from pathlib import Path

def extract_ts_symbols(file_path: str) -> dict:
    content = Path(file_path).read_text()
    symbols = {"classes": [], "functions": [], "interfaces": []}
    for m in re.finditer(r'(?:export\s+)?class\s+(\w+)', content):
        symbols["classes"].append({"name": m.group(1)})
    for m in re.finditer(r'(?:export\s+)?(?:async\s+)?function\s+(\w+)', content):
        symbols["functions"].append({"name": m.group(1)})
    for m in re.finditer(r'(?:export\s+)?interface\s+(\w+)', content):
        symbols["interfaces"].append({"name": m.group(1)})
    return symbols

if __name__ == "__main__":
    print(json.dumps(extract_ts_symbols(sys.argv[1]), indent=2))
```
</details>

<details>
<summary>Go 项目示例</summary>

```python
#!/usr/bin/env python3
"""Go 符号提取"""
import re, json, sys
from pathlib import Path

def extract_go_symbols(file_path: str) -> dict:
    content = Path(file_path).read_text()
    symbols = {"structs": [], "functions": [], "interfaces": []}
    for m in re.finditer(r'type\s+(\w+)\s+struct\s*{', content):
        symbols["structs"].append({"name": m.group(1)})
    for m in re.finditer(r'func\s+(?:\([^)]+\)\s+)?(\w+)\s*\(', content):
        symbols["functions"].append({"name": m.group(1)})
    for m in re.finditer(r'type\s+(\w+)\s+interface\s*{', content):
        symbols["interfaces"].append({"name": m.group(1)})
    return symbols

if __name__ == "__main__":
    print(json.dumps(extract_go_symbols(sys.argv[1]), indent=2))
```
</details>

**框架特定脚本** (根据检测到的框架生成):
| 框架 | 脚本名 | 提取内容 |
|:-----|:-------|:---------|
| FastAPI | `extract_fastapi.py` | @app.get/post 装饰器路由 |
| Django | `extract_django.py` | urls.py 中的 path() 定义 |
| NestJS | `extract_nestjs.py` | @Controller/@Get/@Post 装饰器 |
| Express | `extract_express.py` | app.get/post/use 调用 |
| Spring | `extract_spring.py` | @RequestMapping 注解 |
| Gin | `extract_gin.py` | r.GET/POST 路由注册 |

**🚨 重要**: 所有脚本必须在 Phase 7 验证完成后删除！

**Subagent Prompt 必须包含**:
1. 输出文件完整路径: `.claude/repowiki/.meta/{name}.pkg.json`
2. PKG 结构参考上述字段定义
3. 依赖的 PKG 文件路径 (symbols 需读取 `.claude/repowiki/.meta/modules.pkg.json`)
4. **强制 Serena MCP 使用规范**:
   ```
   对于 symbols 收集，必须执行以下步骤：
   a) 使用 Glob 找到所有代码文件（**/*.ts, **/*.tsx, **/*.java, **/*.py 等）
   b) 对每个文件使用 mcp__serena__get_symbols_overview 获取符号列表
   c) 对每个类使用 mcp__serena__find_symbol(depth=1) 获取完整方法列表
   d) 分批写入 JSON，每批 50 个文件
   e) 最终合并所有批次到 .meta/symbols.pkg.json
   ```
5. **验证要求**: 收集完成后，必须统计并报告：
   - 扫描的文件数
   - 收集的类数量
   - 收集的方法总数
   - 如果类数 < 预期，说明存在遗漏

---

## Phase 4: 文档生成

**推荐并行启动多个 `atlas:atlas-executor` subagent 以提高效率。**

**执行方式**: 使用 **Task tool 调用** 同时启动多个 executor，每个 executor 负责一类文档。

**🚨 必须严格按照 Phase 2 生成的 todos 执行，每完成一个 todo 立即标记为 completed**

**输入** (从文件读取):
- `.meta/project.pkg.json`
- `.meta/modules.pkg.json`
- `.meta/quality.pkg.json`
- `.meta/api.pkg.json`
- `.meta/symbols.pkg.json`
- Phase 2 生成的 todos（必须遵循）

**输出** (写入文件): 各 *.md 文档

### Executor 分配

**推荐并行启动以下 executor：**

| Executor | Subagent | 读取文件 | 输出文件 |
|:---------|:---------|:---------|:---------|
| home-arch | `atlas:atlas-executor` | `.meta/project.pkg.json`, `.meta/modules.pkg.json` | index.md, architecture/*.md |
| api | `atlas:atlas-executor` | `.meta/api.pkg.json` | api/*.md |
| guides | `atlas:atlas-executor` | `.meta/project.pkg.json`, `.meta/quality.pkg.json` | guides/*.md, decisions/*.md, quality/*.md |
| symbols | `atlas:atlas-executor` | `.meta/symbols.pkg.json` | symbols/*.md |

**并行模式**:

| 模式 | 行为 | 并行要求 |
|:-----|:-----|:---------|
| parallel | 4 个 executor 同时启动 | **必须并行** |
| limited | 受 --concurrency 限制的并行数 | 推荐并行 |
| sequential | 全部串行执行 | 串行执行 |

**🚨 当 `--mode parallel` 时，必须并行启动多个 executor！**

**执行要求**:
1. 这 4 个 executor **无相互依赖**，推荐并行调用
2. 每个 executor 独立读取自己需要的 PKG 文件
3. 每个 executor 负责生成自己的文档集

**Subagent Prompt 必须包含**:
1. 要读取的 PKG 文件完整路径: `.claude/repowiki/.meta/{name}.pkg.json`
2. 输出文件完整路径: `.claude/repowiki/{dir}/{name}.md`
3. 参考【文档规范】中的示例格式
4. **🚨 零臆想约束**: 所有内容必须100%来自 PKG 文件，禁止添加任何 PKG 中不存在的信息
5. **验证要求**: 如果 PKG 中某项数据为空或不存在，对应文档章节应标注"未检测到"而非猜测内容

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

## Phase 7: 并行验证与自动修复

**🚨 这是最后一个阶段，必须全面检查所有生成的内容，发现问题自动修复！**

### 7.1 并行验证（启动多个验证器）

**执行方式**: 主进程**并行**启动 4 个验证器，每个验证器负责不同维度

| 验证器 | Subagent | 验证范围 | 输出 |
|:-------|:---------|:---------|:-----|
| V1-文档 | `atlas:information-gatherer` | 核心文档完整性、章节结构、链接有效性 | `.meta/v1-docs.json` |
| V2-PKG | `atlas:information-gatherer` | PKG 数据与源码一致性、符号覆盖率 | `.meta/v2-pkg.json` |
| V3-索引 | `atlas:information-gatherer` | 索引完整性、符号映射、文档关系图 | `.meta/v3-index.json` |
| V4-上下文 | `atlas:information-gatherer` | wiki-context.json 有效性、路径引用 | `.meta/v4-context.json` |

**🚨 必须使用单条消息并行启动 4 个 Task！不可串行执行！**

#### V1-文档验证器
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

#### V2-PKG验证器
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

#### V3-索引验证器
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

#### V4-上下文验证器
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

### 7.2 问题收集与分类

**输入**: 4 个验证器的输出 JSON

**输出**: `.meta/validation-issues.json`

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "summary": {"critical": 2, "warning": 5, "info": 1, "passed": 12},
  "issues": [
    {"id": "D1", "severity": "critical", "message": "index.md 不存在", "fix": {"type": "regenerate", "phase": 4, "target": "index.md"}}
  ],
  "fixable": true,
  "fixPlan": [{"phase": 4, "action": "重新生成 index.md", "targets": ["index.md"]}]
}
```

### 7.3 自动修复循环（最多 2 轮）

**条件**: 存在 `severity: critical` 的问题

**流程**:
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

**修复 Subagent**: `atlas:atlas-executor`

### 7.4 清理临时文件

**🚨 验证通过后必须执行清理！**

**清理目标**:
| 目录/文件 | 说明 | 清理条件 |
|:----------|:-----|:---------|
| `.claude/repowiki/.scripts/` | 临时 Python 脚本 | 始终清理 |
| `.claude/repowiki/.tmp/` | 中间产物 | 始终清理 |
| `.meta/v1-docs.json` | V1 验证输出 | 验证通过后清理 |
| `.meta/v2-pkg.json` | V2 验证输出 | 验证通过后清理 |
| `.meta/v3-index.json` | V3 验证输出 | 验证通过后清理 |
| `.meta/v4-context.json` | V4 验证输出 | 验证通过后清理 |
| `.meta/validation-issues.json` | 问题收集 | 合并到 report 后清理 |

**清理命令**:
```bash
rm -rf .claude/repowiki/.scripts/
rm -rf .claude/repowiki/.tmp/
rm -f .claude/repowiki/.meta/v*.json
rm -f .claude/repowiki/.meta/validation-issues.json
```

**🚨 警告**: 如果验证失败且需要人工介入，保留临时文件供调试！

### 7.5 生成最终报告

**输出**: `.meta/validation-report.md`

```markdown
# 验证报告

## 执行概况
| 项目 | 值 |
|:-----|:---|
| 验证轮次 | 1 |
| 修复轮次 | 0 |
| 最终状态 | ✅ 通过 |

## 验证结果
| 验证器 | 通过 | 警告 | 失败 |
|:-------|:-----|:-----|:-----|
| V1-文档 | 7 | 0 | 0 |
| V2-PKG | 4 | 1 | 0 |
| V3-索引 | 4 | 0 | 0 |
| V4-上下文 | 4 | 0 | 0 |

## 临时文件清理
✅ 已清理 .scripts/, .tmp/, 验证中间文件

---
*验证于 2024-01-15T10:35:00Z*
```

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

## 文档命名规范

**🚨 除 features/ 和 symbols/ 外，所有文档文件名严格固定，禁止自定义！**

### 固定命名（必须严格遵守）

**文档文件**:
| 目录 | 文件名 | 说明 |
|:-----|:-------|:-----|
| `/` | `index.md` | 项目首页，必须 |
| `architecture/` | `overview.md` | 架构总览，必须 |
| `architecture/` | `structure.md` | 目录结构，必须 |
| `architecture/` | `dependencies.md` | 依赖分析 |
| `architecture/` | `modules.md` | 模块列表 |
| `architecture/` | `module-graph.md` | 模块依赖图 |
| `architecture/` | `layers.md` | 分层架构 |
| `architecture/` | `patterns.md` | 设计模式 |
| `api/` | `endpoints.md` | API 端点列表 |
| `api/` | `types.md` | 类型定义 |
| `guides/` | `development.md` | 开发指南，必须 |
| `guides/` | `build.md` | 构建指南 |
| `decisions/` | `adr-log.md` | 架构决策记录 |
| `quality/` | `complexity.md` | 复杂度分析 |

**PKG 数据文件** (`.meta/`):
| 文件名 | 说明 | Phase |
|:-------|:-----|:------|
| `project.pkg.json` | 项目元数据 | 3 |
| `modules.pkg.json` | 模块结构 | 3 |
| `quality.pkg.json` | 代码质量 | 3 |
| `api.pkg.json` | API 端点信息 | 3 |
| `symbols.pkg.json` | 符号信息 | 3 |
| `semantic-changes.json` | 语义变更（增量模式）| 1 |
| `validation-report.md` | 验证报告 | 7.5 |
| `validation-issues.json` | 验证问题（临时）| 7.2 |
| `v1-docs.json` | V1 验证结果（临时）| 7.1 |
| `v2-pkg.json` | V2 验证结果（临时）| 7.1 |
| `v3-index.json` | V3 验证结果（临时）| 7.1 |
| `v4-context.json` | V4 验证结果（临时）| 7.1 |

**索引文件** (`.index/`):
| 文件名 | 说明 | Phase |
|:-------|:-----|:------|
| `quick-lookup.json` | 快速查询索引 | 5 |
| `symbol-map.json` | 符号映射表 | 5 |
| `doc-graph.json` | 文档关系图 | 5 |

**上下文配置** (`.claude/`):
| 文件名 | 说明 | Phase |
|:-------|:-----|:------|
| `wiki-context.json` | Wiki 上下文配置 | 6 |

### 动态命名（按项目内容生成）

| 目录 | 命名规则 | 示例 |
|:-----|:---------|:-----|
| `symbols/` | `index.md` + `{module-name}-module.md` | `user-module.md`, `order-module.md` |
| `features/` | `{feature-name}.md` | `authentication.md`, `payment.md` |

### 命名约束

1. **symbols/**: 必须有 `index.md`，模块文档以 `-module.md` 结尾
2. **features/**: 文件名使用 kebab-case，与功能名对应
3. **禁止**: 自创文件名、中文文件名、空格、大写字母

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

**🚨🚨🚨 零臆想原则（最高优先级）🚨🚨🚨**:

**绝对禁止任何形式的臆想、猜测、推断！所有文档内容必须100%来自实际代码！**

- **禁止臆想的内容**:
  - API 端点（路径、方法、参数、返回值）
  - 类名、函数名、变量名
  - 参数签名、返回类型
  - 模块结构、依赖关系
  - 配置项、环境变量
  - 任何代码相关的技术细节

- **强制验证流程**:
  1. **必须先读取源代码**才能写入文档
  2. **每个符号**必须通过 Serena MCP 或 Grep 验证存在
  3. **每个 API 端点**必须从路由定义文件中提取
  4. **每个配置项**必须从配置文件中提取
  5. **宁可不写，也不能猜测**

- **信息来源要求**:
  - 符号信息 → 必须来自 `find_symbol` / `get_symbols_overview`
  - API 端点 → 必须来自路由文件的实际读取（如 `@Get()`, `router.get()` 等）
  - 依赖关系 → 必须来自 `package.json` / `go.mod` / 实际 import 分析
  - 配置项 → 必须来自 `.env.example` / 配置文件

- **🚨 发现任何不确定的信息，必须返回源代码再次确认！**
- **🚨 臆想是最严重的错误，宁愿文档不完整，也绝不允许包含任何猜测内容！**

**Subagent 使用（最高优先级）**:
- Phase 1 语义变更检测 → **必须使用 `atlas:repo-semantic-analyzer`**，仅在 INCREMENTAL 模式执行
- Phase 2 规划 → **必须使用 `Plan`**，禁止使用其他 subagent
- Phase 3 信息收集 → **推荐并行启动多个 `atlas:information-gatherer`**（`--mode parallel` 时必须并行），禁止使用 Plan 或 atlas-executor
- Phase 4 文档生成 → **推荐并行启动多个 `atlas:atlas-executor`**（`--mode parallel` 时必须并行），禁止使用 Plan 或 information-gatherer
- Phase 5 AI索引生成 → **必须使用 `atlas:repo-context-indexer`**，禁止使用其他 subagent
- Phase 6 上下文优化 → **主进程执行**，生成 wiki-context.json
- Phase 7.1 并行验证 → **必须并行启动 4 个 `atlas:information-gatherer`**（V1-文档/V2-PKG/V3-索引/V4-上下文）
- Phase 7.3 自动修复 → **使用 `atlas:atlas-executor`**，修复 critical 问题，最多 2 轮
- Phase 7.4 清理 → **主进程执行**，删除 .scripts/、.tmp/、v*.json 等临时文件
- **🚨 混用 subagent 是严重错误，必须严格遵守上述分配！**

**Todos 管理（最高优先级）**:
- Phase 2 的 Plan agent **必须**通过 TodoWrite 生成详细的执行 todos
- Phase 3/4 的 agent **必须**严格按照 todos 顺序执行
- 每完成一个 todo，**必须立即**通过 TodoWrite 标记为 completed
- **🚨 不按 todos 执行是严重错误！**

**执行**: 阶段顺序不可跳跃 | symbols 等待 modules | PKG 是唯一数据媒介 | 优先 Serena MCP

**格式**: 必需章节不可省略 | 表格列数一致 | Mermaid 语法正确 | 相对路径链接

**命名**: 严格遵守文档命名规范 | .meta/*.pkg.json 固定 | .index/*.json 固定 | features/symbols 动态命名

**验证**: 文档≥10行 | 符号覆盖≥90%(警告) | 链接100%有效 | Mermaid无错误 | **必须 4 个验证器并行**

**清理**: 验证通过后**必须删除** .scripts/ .tmp/ v*.json validation-issues.json | 验证失败需人工介入时保留临时文件

**禁止**: 跳过验证 | 静默忽略失败 | 占位内容 | 硬编码信息 | **任何臆想内容** | **自定义文件名**

**错误处理**: 无 git→FULL_BUILD | >2000文件无scope→终止 | Serena不可用→降级Grep | 收集失败→跳过依赖任务 | Executor失败→继续其他 | critical问题→自动修复(最多2轮)

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
