# P0 优化分析报告

**任务 ID**: p0-optimization-20251202
**分析时间**: 2025-12-02
**范围**: atlas/commands/repo-wiki.md 及相关实现

---

## 执行摘要

本报告深入分析了现有 repo-wiki 命令的实现，为语义级增量更新和 Wiki 作为 AI 上下文源的 P0 优化做准备。

关键发现：
1. **变更检测机制不完整** - 仅基于 git status，缺乏语义级变更检测
2. **PKG 结构设计完备** - symbols.pkg.json 包含完整的签名信息，足以支持对比
3. **文档输出不适合作为 AI 上下文** - 文档粒度过大，需要索引化处理
4. **增量更新框架缺失** - repo-wiki 命令无增量更新机制

---

## 问题 1: 现有变更检测机制分析

### 1.1 当前实现

**位置**: `atlas/commands/repo-wiki.md` 第 55-73 行（Phase 0）

```markdown
## Phase 0: 环境检测

**操作**:
- 创建目录 `.claude/repowiki/{.meta,architecture,api,guides,decisions,symbols,quality,features}`
- 检测构建模式: FULL_BUILD (Wiki不存在/--force/配置变更) | INCREMENTAL (仅代码变更)
- 判断规模: <100 全量 | 100-500 采样 | 500-2000 分片 | >2000 需 --scope
```

### 1.2 问题诊断

#### 问题 1a: 变更检测过于粗粒度

现有检测逻辑：
```
FULL_BUILD 条件:
  ✓ Wiki不存在
  ✓ --force 参数
  ✓ 配置变更

INCREMENTAL 条件:
  ✓ 仅代码变更 (基于 git status)
```

**缺陷**：
- 依赖 git status 的文件级变更，无法区分语义变更和格式变更
- 无法检测函数签名变更、类定义变更、API 端点变更
- 无法区分临时变更和永久变更

**示例场景**：
```typescript
// 仅改变了变量名，不改变功能
export class UserService {
  async getUser(id: string) {  // 签名未变
    const userId = id;  // ← 只改了变量名
    return this.findById(userId);
  }
}
```
当前检测会认为需要完整重新扫描符号，但实际上 API 签名未变。

#### 问题 1b: 缺乏语义级对比机制

**预期能力**（P0 优化目标）：
```
变更检测链条：
  git diff file1.ts
    ↓ [文件级]
  检查是否包含语义变更点（函数签名、类定义、导出）
    ↓ [语义级]
  对比旧 symbols.pkg.json 中的签名
    ↓ [增量级]
  仅收集改动过的符号
    ↓ [效率级]
  增量更新 wiki
```

**当前实现**：
```
git status
  ↓ [仅文件级]
FULL_BUILD 或 INCREMENTAL 二选一
  ↓ [粗粒度]
全量扫描所有符号或跳过
```

### 1.3 扩展点分析

**在 Phase 0 中添加语义级检测的位置**：

**文件**: `atlas/commands/repo-wiki.md` 第 69 行后可添加

```markdown
## Phase 0.5: 语义变更检测（新增）

**前置条件**: 存在旧的 .meta/symbols.pkg.json

**操作流程**:
1. 获取 git diff 的文件列表
2. 对每个改动的文件执行语义扫描：
   - 提取新的函数/类签名
   - 对比旧 PKG 中的签名
   - 记录哪些符号发生了变更
3. 输出变更类型：
   - SIGNATURE_CHANGED: 签名变更（参数/返回值/可见性）
   - DEFINITION_CHANGED: 定义体变更（不影响签名）
   - NEW_SYMBOL: 新增符号
   - DELETED_SYMBOL: 删除符号
   - FORMAT_ONLY: 仅格式变更（如注释、变量名）
4. 根据变更类型决定：
   - SIGNATURE_CHANGED → 需要重新扫描该文件的符号
   - DEFINITION_CHANGED → 标记该符号需要重新生成文档
   - NEW_SYMBOL / DELETED_SYMBOL → 更新符号索引
   - FORMAT_ONLY → 跳过符号扫描
```

**实现建议**:
1. Phase 2 (information-gatherer) 中扩展 symbols 收集器
2. 添加 `--compare-with-pkg` 参数，指定要对比的旧 PKG
3. 实现 `_getSemanticChanges()` 函数检测签名变更

---

## 问题 2: symbols.pkg.json 结构完整性分析

### 2.1 当前结构

**位置**: `atlas/agents/information-gatherer.md` 第 118-168 行

```json
{
  "modules": {
    "ModuleName": {
      "classes": [{
        "name": "ClassName",
        "visibility": "public",
        "extends": "BaseClass",
        "implements": ["Interface1"],
        "generics": ["T", "K"],
        "properties": [{
          "name": "prop",
          "type": "string",
          "visibility": "public"
        }],
        "methods": [{
          "name": "method",
          "visibility": "public",
          "params": [{"name": "arg", "type": "number"}],
          "returns": "void",
          "description": "JSDoc 说明"
        }]
      }],
      "interfaces": [...],
      "functions": [...],
      "types": [...]
    }
  },
  "apiEndpoints": [{
    "method": "GET",
    "path": "/api/users",
    "handler": "UserController.list",
    "auth": true,
    "params": [],
    "response": "User[]"
  }],
  "stats": {
    "total": 156,
    "documented": 142,
    "coverage": 0.91
  }
}
```

### 2.2 对比能力评估

#### 优点：
✅ **签名信息完整** - 包含所有影响 API 的字段
  - 参数列表（params）
  - 返回类型（returns）
  - 可见性（visibility）
  - 泛型（generics）
  - 继承关系（extends, implements）

✅ **扩展点充分** - 可添加变更时间戳、哈希值等

✅ **层级清晰** - 按模块分组便于增量处理

#### 不足之处：
⚠️ **缺少签名哈希值** - 无法快速判断是否变更

**建议添加**:
```json
{
  "methods": [{
    "name": "method",
    "signature": "(arg: number) => void",
    "signatureHash": "sha256:abc123...",  // ← 新增
    "changeTimestamp": "2025-12-02T10:30:00Z",  // ← 新增
    "params": [...]
  }]
}
```

⚠️ **缺少文件位置信息** - 不知道符号在源代码的具体行号

**建议添加**:
```json
{
  "classes": [{
    "name": "ClassName",
    "location": {
      "file": "src/user.ts",
      "line": 45,
      "column": 0
    },
    "methods": [...]
  }]
}
```

### 2.3 对比算法框架

**建议的增量对比算法**（在 Plan agent 或新的 Executor 中实现）:

```python
def compare_symbols(old_pkg: dict, new_pkg: dict) -> dict:
    """
    对比两个 PKG 文件的语义变更
    """
    changes = {
        "signature_changes": [],      # 签名改变的符号
        "new_symbols": [],             # 新增符号
        "deleted_symbols": [],         # 删除符号
        "documentation_changes": []    # 仅文档变更
    }

    # 遍历每个模块
    for module_name in new_pkg.modules:
        old_module = old_pkg.modules.get(module_name, {})
        new_module = new_pkg.modules[module_name]

        # 对比类
        for cls in new_module.classes:
            old_cls = find_by_name(old_module.classes, cls.name)
            if not old_cls:
                changes["new_symbols"].append(cls)
            elif _has_signature_changed(old_cls, cls):
                changes["signature_changes"].append({
                    "symbol": cls.name,
                    "changes": _diff_signatures(old_cls, cls)
                })
            elif _has_doc_changed(old_cls, cls):
                changes["documentation_changes"].append(cls.name)

    return changes

def _has_signature_changed(old, new) -> bool:
    """检查签名是否变更"""
    return (
        old.visibility != new.visibility or
        old.extends != new.extends or
        old.implements != new.implements or
        _methods_changed(old.methods, new.methods) or
        _properties_changed(old.properties, new.properties)
    )
```

### 2.4 结论

✅ **symbols.pkg.json 足以支持签名变更对比**

关键改进点：
1. 添加 `signatureHash` 字段用于快速对比
2. 添加 `location` 字段用于精确定位
3. 实现增量对比算法（计划中）

---

## 问题 3: 文档结构作为 AI 上下文的适配性分析

### 3.1 当前文档生成流程

**位置**: `atlas/commands/repo-wiki.md` 第 209-259 行（Phase 3）

输出目录结构：
```
.claude/repowiki/
├── index.md
├── architecture/
│   ├── overview.md
│   ├── structure.md
│   ├── dependencies.md
│   ├── modules.md
│   ├── module-graph.md
│   ├── layers.md
│   └── patterns.md
├── api/
│   ├── endpoints.md
│   └── types.md
├── guides/
│   ├── development.md
│   ├── build.md
├── decisions/
│   └── adr-log.md
├── quality/
│   └── complexity.md
├── symbols/
│   ├── index.md
│   ├── user-module.md
│   └── order-module.md
└── features/
    └── authentication.md
```

### 3.2 问题诊断：文档粒度不适合 AI 上下文

#### 问题 3a: 文档过大或信息不可快速查询

**示例问题**：
```
AI 需要快速查询：
  Q1: "UserService 类的所有公开方法签名是什么？"
  Q2: "POST /api/users 端点需要哪些认证权限？"
  Q3: "哪些文件导入了 UserService？"

当前文档格式：
  ✗ 需要逐一打开 symbols/*.md 查找
  ✗ 需要在 api/endpoints.md 中全文搜索
  ✗ 无法快速获取引用关系
```

#### 问题 3b: 缺乏上下文索引机制

**AI 上下文集成流程**（P0 目标）：
```
用户任务
  ↓
Claude 分析需要哪些信息
  ↓
读取 .claude/repowiki/.index/symbols-index.json
  ↓ [快速查找]
定位 UserService 的位置
  ↓
读取 .claude/repowiki/.meta/symbols.pkg.json 的详细定义
  ↓
根据需要读取 symbols/user-module.md 的完整说明
```

**当前流程**：
```
用户任务
  ↓
Claude 扫描整个 .claude/repowiki/ 目录
  ↓ [低效]
逐个打开所有 *.md 文件
  ↓
汇总信息
```

#### 问题 3c: 文档格式未优化查询

**当前 api/endpoints.md 格式**（示例）:
```markdown
# API 端点

## 概览
| 指标 | 值 |
|:-----|:---|
| 总端点 | 12 |

## 端点列表
| Method | Path | Handler | Auth | Description |
|:-------|:-----|:--------|:----:|:------------|
| GET | /users | UserController.list | ✓ | 用户列表 |
```

**AI 友好的格式**（建议）:
```markdown
## GET /users

| 字段 | 值 |
|:-----|:---|
| Handler | UserController.list |
| Auth | Required |
| Path Params | - |
| Query Params | page, limit, filter |
| Request Body | - |
| Response | User[] |
| Status Codes | 200, 400, 401, 404 |
```

### 3.3 建议的改进方案

#### 方案 A: 添加索引文件（推荐）

**新增输出**:
```
.claude/repowiki/
├── .meta/
│   ├── project.pkg.json
│   ├── modules.pkg.json
│   ├── symbols.pkg.json
│   └── quality.pkg.json
├── .index/  # ← 新增
│   ├── symbols-quick-ref.json
│   ├── endpoints-quick-ref.json
│   └── file-map.json
└── [其他文档目录]
```

**symbols-quick-ref.json 结构**:
```json
{
  "symbols": [
    {
      "name": "UserService",
      "kind": "class",
      "module": "user",
      "file": "src/user/user.service.ts",
      "line": 45,
      "public_methods": [
        {
          "name": "getUser",
          "signature": "(id: string) => User",
          "docs": "获取用户信息"
        }
      ],
      "related_docs": [
        ".claude/repowiki/symbols/user-module.md",
        ".claude/repowiki/architecture/layers.md"
      ]
    }
  ]
}
```

**endpoints-quick-ref.json 结构**:
```json
{
  "endpoints": [
    {
      "method": "GET",
      "path": "/users/:id",
      "handler": "UserController.getUser",
      "auth": true,
      "params": {
        "path": ["id"],
        "query": []
      },
      "response": "User",
      "docs": ".claude/repowiki/api/endpoints.md#get-usersid"
    }
  ]
}
```

#### 方案 B: 优化文档格式

在现有 Phase 3 输出基础上：
1. 使用 YAML frontmatter 添加元数据
2. 按功能分组而非按类型分组
3. 添加快速导航链接

**优化后的 api/endpoints.md**:
```markdown
---
kind: api-reference
total_endpoints: 12
auth_required: 10
updated_at: 2025-12-02T10:30:00Z
---

# API 端点

## 用户管理

### GET /users/:id
**Handler**: UserController.getUser
**Auth**: Required
**Params**: id (path)
**Response**: User
[详细说明...]

### POST /users
[详细说明...]
```

### 3.4 集成到 AI 上下文的流程

**建议在 repo-wiki 命令中添加新的 Phase**:

```markdown
## Phase 3.5: 生成 AI 上下文索引（新增）

**输入**: Phase 3 生成的所有 *.md 文档 + .meta/*.pkg.json

**操作**:
1. 生成 .claude/repowiki/.index/symbols-quick-ref.json
2. 生成 .claude/repowiki/.index/endpoints-quick-ref.json
3. 生成 .claude/repowiki/.index/file-map.json
4. 生成 .claude/repowiki/.index/README.md（说明如何使用索引）

**输出**: AI 友好的查询索引
```

**在 claude.ai/code 中集成**:
```markdown
Claude Code 可在以下场景自动加载 Wiki 索引：
1. 用户输入包含项目特定的类/函数名
   → 自动查询 symbols-quick-ref.json

2. 用户询问 API 相关问题
   → 自动查询 endpoints-quick-ref.json

3. 显示修改影响范围
   → 查询 file-map.json 的引用关系
```

### 3.5 结论

⚠️ **文档结构不适合直接作为 AI 上下文，需要增强**

必要的改进：
1. ✅ 生成快速查询索引（.index/*.json）
2. ✅ 优化文档格式，添加 YAML frontmatter
3. ✅ 建立文件到文档的映射关系
4. ⭐ 关键：需要在 Phase 3 后添加 Phase 3.5

---

## 问题 4: 增量更新和上下文集成的架构缺口

### 4.1 缺失的文件和目录

**当前结构**:
```
.claude/repowiki/
├── .meta/
│   ├── project.pkg.json
│   ├── modules.pkg.json
│   ├── quality.pkg.json
│   └── symbols.pkg.json
├── architecture/
├── api/
├── guides/
├── decisions/
├── symbols/
├── quality/
└── features/
```

**P0 优化需要的新增结构**:
```
.claude/repowiki/
├── .meta/
│   ├── project.pkg.json
│   ├── modules.pkg.json
│   ├── quality.pkg.json
│   └── symbols.pkg.json
├── .index/  # ← 新增（问题 3）
│   ├── symbols-quick-ref.json
│   ├── endpoints-quick-ref.json
│   ├── file-map.json
│   └── README.md
├── .changelog/  # ← 新增（问题 1）
│   ├── changes-20251202.json
│   └── history.md
├── .cache/  # ← 新增（优化用）
│   ├── signature-hashes.json
│   └── file-mtimes.json
├── architecture/
├── api/
├── guides/
├── decisions/
├── symbols/
├── quality/
└── features/
```

### 4.2 增量更新工作流

**需要的新 Phase 或改进**:

**Phase 0 → Phase 0.5（新增语义检测）**:
```markdown
## Phase 0.5: 语义变更检测

**输入**:
- git diff 文件列表
- 旧的 .meta/symbols.pkg.json（如果存在）

**输出**:
```json
{
  "changeType": "INCREMENTAL",
  "changedFiles": ["src/user.ts", "src/order.ts"],
  "semanticChanges": [
    {
      "file": "src/user.ts",
      "symbols": [
        {
          "name": "UserService.getUser",
          "type": "SIGNATURE_CHANGED",
          "oldSignature": "(id: string) => User",
          "newSignature": "(id: string, includeProfile?: boolean) => User"
        }
      ]
    }
  ]
}
```

**Phase 2 → 改进（支持增量收集）**:
```markdown
## Phase 2.5: 增量符号收集

**输入**: Phase 0.5 的语义变更信息

**操作**:
- 仅扫描有语义变更的符号
- 合并到旧的 .meta/symbols.pkg.json
- 生成变更记录 .changelog/changes-{date}.json
```

**Phase 4 → 改进（验证增量完整性）**:
```markdown
## Phase 4.5: 增量验证

**检查项**:
- 所有有语义变更的符号都已更新
- 文档链接仍然有效
- 索引文件（.index/）已更新
```

### 4.3 AI 上下文集成点

**建议添加新的 phase**:

**Phase 5: AI 上下文优化（新增）**

```markdown
## Phase 5: AI 上下文优化

**输入**:
- .meta/*.pkg.json（结构化数据）
- .index/*.json（快速查询索引）

**操作**:
1. 生成 .claude/wiki-context.json
   - 项目概览
   - 核心 API
   - 关键类和接口
   - 模块依赖图

2. 在 .claude/claude.json 中集成
   - 配置 Wiki 自动加载
   - 定义快速查询规则

**输出**:
```json
{
  "wikiPath": ".claude/repowiki",
  "autoLoad": true,
  "indexFiles": [
    ".index/symbols-quick-ref.json",
    ".index/endpoints-quick-ref.json"
  ],
  "contextSize": "compact",  // compact | standard | full
  "updateFrequency": "on-change"  // on-change | daily | manual
}
```

**在 claude.ai/code 工作流中**:
1. 启动时自动加载 .claude/wiki-context.json
2. 用户输入时智能查询相关索引
3. 在修改代码时显示相关 API 和依赖
```

### 4.4 需要的新工具或 Agent

**建议新增**:

1. **AI Context Generator Agent**（新增 Agent）
   - 职责：生成 AI 友好的上下文索引
   - 触发：Phase 3 完成后
   - 输出：.index/*.json + .claude/wiki-context.json

2. **Incremental Scanner Agent**（改进现有）
   - 职责：执行语义级变更检测
   - 触发：Phase 0.5
   - 输出：变更报告 JSON

3. **Index Updater Executor**（新增 Executor）
   - 职责：更新快速查询索引
   - 触发：符号信息变更时
   - 并行性：可与文档生成并行

### 4.5 repo-wiki 命令的完整改进方案

**新的 Phase 结构**（当前是 Phase 0-4，改为 Phase 0-5）:

```
Phase 0: 环境检测 (现有)
  ↓
Phase 0.5: 语义变更检测 (新增)
  ↓
Phase 1: 规划 (现有，改进 todos 生成)
  ↓
Phase 2: 信息收集 (现有)
  ↓
Phase 2.5: 增量合并 (新增，可选)
  ↓
Phase 3: 文档生成 (现有)
  ↓
Phase 3.5: 生成 AI 索引 (新增)
  ↓
Phase 4: 验证 (现有，改进)
  ↓
Phase 4.5: 增量验证 (新增，可选)
  ↓
Phase 5: AI 上下文优化 (新增)
```

---

## 关键发现总结

| 问题 | 现状 | P0 优化需求 | 优先级 | 工作量 |
|:-----|:-----|:----------|:------|:------|
| 变更检测 | 仅基于 git status | 语义级检测 + 签名对比 | 高 | 中 |
| PKG 结构 | 已完备，缺哈希值 | 添加 signatureHash + location | 中 | 小 |
| 文档结构 | 不适合 AI 上下文 | 添加快速查询索引（.index/） | 高 | 中 |
| 增量更新 | 完全缺失 | 新增 Phase 0.5 → Phase 5 | 高 | 大 |
| AI 集成 | 无专门机制 | 生成 .claude/wiki-context.json | 高 | 中 |

---

## 建议的实现路线图

### 第 1 阶段：基础增强（短期，1-2 周）
- ✅ 优化 PKG 结构：添加 signatureHash 和 location
- ✅ 实现快速查询索引生成（Phase 3.5）
- ✅ 添加 YAML frontmatter 到 markdown 文档

### 第 2 阶段：增量支持（中期，2-3 周）
- ✅ 实现语义变更检测（Phase 0.5）
- ✅ 实现增量符号合并（Phase 2.5）
- ✅ 改进验证（Phase 4.5）

### 第 3 阶段：AI 集成（中期，2-3 周）
- ✅ 实现 AI 上下文生成（Phase 5）
- ✅ 实现 AI Context Generator Agent
- ✅ 集成到 .claude/claude.json

### 第 4 阶段：优化和测试（长期，1-2 周）
- ✅ 性能优化（缓存 hash、文件 mtime）
- ✅ 完整测试
- ✅ 文档更新

---

## 关键技术决策

### 1. 签名变更检测算法

**推荐方案**：使用规范化的签名字符串 + SHA256 哈希

```typescript
// 规范化函数签名
function normalizeSignature(method: MethodSymbol): string {
  const params = method.params
    .map(p => `${p.name}:${p.type}`)
    .join(',');
  return `${method.visibility} ${method.name}(${params}):${method.returns}`;
}

// 生成 hash
const signature = normalizeSignature(method);
const hash = sha256(signature);
```

**优点**：
- 快速对比：O(1) hash 对比 vs O(n) 逐字段对比
- 可追踪：保存 hash 历史便于生成 changelog
- 易于集成：现有 PKG 结构可直接添加 hash 字段

### 2. 增量更新策略

**推荐方案**：积分制 + 阈值判断

```
增量评分：
- 新文件数 / 总文件数 → 权重 30%
- 有语义变更的符号 / 总符号数 → 权重 50%
- 新/删除模块数 → 权重 20%

如果分数 < 20% → INCREMENTAL
如果分数 >= 20% → SMART_REBUILD（仅重建受影响的文档）
```

### 3. AI 上下文加载策略

**推荐方案**：三层索引 + 智能预加载

```
第 1 层（快速）: .index/symbols-quick-ref.json（<100KB）
  用于快速查询符号位置和签名

第 2 层（标准）: .meta/symbols.pkg.json（<1MB）
  用于获取完整的符号定义和关系

第 3 层（完整）: .claude/repowiki/symbols/*.md（<10MB）
  用于阅读详细文档
```

---

## 文件修改清单

**需要修改的文件**：

1. **atlas/commands/repo-wiki.md**
   - 第 55-73 行：扩展 Phase 0 → Phase 0.5
   - 第 75-130 行：改进 Phase 1 的 todos 生成
   - 第 209-259 行：改进 Phase 3
   - 新增：Phase 3.5, 4.5, 5

2. **atlas/agents/information-gatherer.md**
   - 第 39-46 行：添加 .index/ 目录
   - 第 118-168 行：增强 symbols PKG 结构（添加 hash、location）
   - 新增：AI 上下文生成的说明

3. **atlas/agents/atlas-executor.md**（可选）
   - 新增 executor 类型：index-generator, context-generator

4. **atlas/skills/gather/** （可选）
   - 添加专门的语义变更检测 skill

5. **新增文件**（如需要）
   - `atlas/agents/context-generator.md` - AI 上下文生成专家
   - `docs/p0-optimization-guide.md` - P0 优化实现指南

---

## 测试验证点

### 变更检测测试
```
场景 1: 仅修改注释
  预期: 检测为 FORMAT_ONLY, 不重新扫描符号

场景 2: 修改函数参数
  预期: 检测为 SIGNATURE_CHANGED, 重新扫描并生成新文档

场景 3: 添加新方法
  预期: 检测为 NEW_SYMBOL, 生成新的符号文档

场景 4: 删除导出类
  预期: 检测为 DELETED_SYMBOL, 更新索引
```

### AI 上下文加载测试
```
测试 1: 快速查询符号
  输入: 查询 "UserService" 的所有公开方法
  验证: < 100ms 从索引返回结果

测试 2: 获取 API 签名
  输入: 查询 "POST /api/users" 的参数和响应
  验证: 正确返回完整定义

测试 3: 链接有效性
  输入: 验证文档中的相对链接
  验证: 100% 链接有效
```

---

## 参考资源

- **现有实现**：`atlas/commands/repo-wiki.md`（主规范）
- **Agent 定义**：`atlas/agents/information-gatherer.md`、`atlas-executor.md`
- **项目 CLAUDE.md**：`.` 目录根的 CLAUDE.md（版本管理指南）

---

**报告完成日期**: 2025-12-02
**作者**: Information Gatherer Agent
**下一步**: 根据本报告制定详细的实现计划和代码改动
