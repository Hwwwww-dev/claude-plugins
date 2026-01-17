---
description: 测试生成命令。分析代码逻辑，自动生成单元测试和集成测试，支持多种测试框架。
argument-hint: [--scope path] [--framework jest|vitest|pytest|go] [--type unit|integration] [--coverage-target N]
---

# 测试生成命令

分析代码逻辑和边界条件，自动生成高质量的测试用例。

## 参数

| 参数 | 说明 | 默认值 |
|:-----|:-----|:-------|
| `--scope` | 生成范围 | . (全项目) |
| `--framework` | 测试框架 | 自动检测 |
| `--type` | 测试类型 | unit |
| `--coverage-target` | 目标覆盖率 | 80 |

---

## 支持的测试框架

| 框架 | 语言 | 检测方式 |
|:-----|:-----|:---------|
| Jest | JavaScript/TypeScript | package.json 依赖 |
| Vitest | JavaScript/TypeScript | vite.config / vitest.config |
| Mocha | JavaScript/TypeScript | package.json 依赖 |
| Pytest | Python | pytest.ini / pyproject.toml |
| Go Test | Go | go.mod 存在 |
| JUnit | Java | pom.xml / build.gradle |

---

## 执行流程

Phase 0 环境检测 → Phase 1 目标分析 → Phase 1.5 配置选择 → Phase 2 用例规划 → Phase 3 测试生成 → Phase 4 验证

### Subagent 分配

| Phase | 功能 | Subagent | 说明 |
|:------|:-----|:---------|:-----|
| 0 | 环境检测 | 主进程 | 检测测试框架和现有覆盖率 |
| 1 | 目标分析 | `atlas:information-gatherer` | 分析目标代码 |
| 1.5 | 配置选择 | 用户选择 | 第一次询问执行模式+测试范围，第二次询问测试配置（仅交互模式） |
| 2 | 用例规划 | `atlas:planner` 或 `Plan` | 规划测试用例 |
| 3 | 测试生成 | `atlas:atlas-executor` | 并行生成测试文件 |
| 4 | 验证 | 主进程 | 运行测试，报告覆盖率 |

---

## Phase 0: 环境检测

**检测内容**: 测试框架类型、命名约定、目录结构、Mock 库、现有覆盖率

---

## 项目知识库

**优先从 `.claude/repowiki/` 获取项目信息**（如果存在）：

| 文件 | 用途 |
|:-----|:-----|
| `.claude/repowiki/.meta/project.pkg.json` | 项目配置、测试框架信息 |
| `.claude/repowiki/.meta/modules.pkg.json` | 模块结构（确定测试范围） |
| `.claude/repowiki/.meta/symbols.pkg.json` | 符号索引（函数签名、参数类型） |
| `.claude/repowiki/.meta/api.pkg.json` | API 端点（用于集成测试） |

**使用方式**：Phase 1 分析前先检查这些文件是否存在，可获取函数签名和依赖信息。

---

## Phase 1: 目标分析

**Subagent**: `atlas:information-gatherer`

**分析内容**: 函数签名、参数类型、分支路径、依赖项、现有测试覆盖

**PKG 结构**:
```json
{
  "targets": [
    {
      "file": "src/user/user.service.ts",
      "symbol": "UserService",
      "methods": [
        {
          "name": "create",
          "signature": "create(data: CreateUserDto): Promise<User>",
          "branches": [
            {"condition": "email exists", "outcome": "throw ConflictException"},
            {"condition": "validation fails", "outcome": "throw BadRequestException"}
          ],
          "dependencies": ["PrismaService", "HashService"],
          "hasExistingTest": false
        }
      ]
    }
  ],
  "summary": {
    "totalTargets": 15,
    "withoutTests": 7,
    "estimatedNewTests": 25
  }
}
```

---

## Phase 1.5: 配置选择

**分阶段询问用户配置**:

**第一个 AskUserQuestion: 执行模式和测试范围**
```
AskUserQuestion(questions=[
  {
    "question": "执行模式",
    "header": "Mode",
    "options": [
      {"label": "自动模式（推荐）", "description": "使用推荐选项，减少交互"},
      {"label": "交互模式", "description": "每个关键步骤都需要确认"}
    ]
  },
  {
    "question": "测试范围",
    "header": "Scope",
    "options": [
      {"label": "全项目", "description": "为所有代码生成测试"},
      {"label": "指定目录", "description": "仅为指定目录生成测试"}
    ]
  }
])
```

**第二个 AskUserQuestion: 测试配置（仅交互模式）**

如果用户选择了**交互模式**，询问测试配置：

```
AskUserQuestion(questions=[
  {
    "question": "测试类型",
    "header": "Type",
    "options": [
      {"label": "单元测试（推荐）", "description": "测试独立函数和类"},
      {"label": "集成测试", "description": "测试模块间交互"}
    ]
  },
  {
    "question": "测试框架",
    "header": "Framework",
    "options": [
      {"label": "自动检测（推荐）", "description": "根据项目配置自动选择"},
      {"label": "Jest", "description": "JavaScript/TypeScript"},
      {"label": "Vitest", "description": "JavaScript/TypeScript (Vite)"},
      {"label": "Pytest", "description": "Python"},
      {"label": "Go Test", "description": "Go"}
    ]
  },
  {
    "question": "覆盖率目标",
    "header": "Coverage",
    "options": [
      {"label": "80%（推荐）", "description": "标准覆盖率目标"},
      {"label": "90%", "description": "高覆盖率目标"},
      {"label": "100%", "description": "完全覆盖"}
    ]
  },
  {
    "question": "选择用例规划器",
    "header": "Planner",
    "options": [
      {"label": "atlas:planner（推荐）", "description": "信任 gatherer 输出，最小化额外扫描，高效规划"},
      {"label": "内置 Plan", "description": "Claude Code 内置规划器，会自行探索验证"}
    ]
  }
])
```

**自动模式行为**（跳过第二个 AskUserQuestion）：
- `type=unit`、框架自动检测、覆盖率目标 80%、规划器 `atlas:planner`

---

## Phase 2: 用例规划

**Subagent**: 根据用户选择调用对应的规划器

**核心原则**：优先使用 Phase 1 输出，最小化额外读取。

### 选项 A: atlas:planner（推荐）

**特点**: 信任 gatherer 输出，基于已有信息直接规划，≤3 次补充读取

```
Task(subagent_type="atlas:planner")
prompt: |
  ## 任务
  为目标代码生成测试用例规划

  ## Gatherer 输出位置
  `.claude/gather/test-gen-<task-id>/`
  - `context.json`: 目标分析数据（函数签名、分支路径、依赖项）

  ## 输出要求
  按照 planner agent 定义的固定格式输出用例规划
```

### 选项 B: 内置 Plan

**特点**: 会自行探索代码，适合 gatherer 信息不足场景（但仍需先用 Phase 1 产物）。

```
Task(subagent_type="Plan")
prompt: |
  ## 任务
  为目标代码生成测试用例规划

  ## 强制信息源（先读）
  `.claude/gather/test-gen-<task-id>/context.json`

  ## 规则
  - 优先用已给出的签名/分支/依赖规划；仅在信息缺失时补充读取（精确、少量）
  - 输出每个目标的用例清单（正常/边界/异常）+ Mock 设置说明
```

**用例规划示例**:
```markdown
### UserService.create
- [ ] 应该成功创建用户并返回 User 对象
- [ ] email 为空时应该抛出 BadRequestException
- [ ] password 长度 < 8 时应该抛出 BadRequestException
- [ ] email 已存在时应该抛出 ConflictException
- Mock: PrismaService.user.{create,findUnique}, HashService.hash
```

---

## Phase 3: 测试生成

**Subagent**: `atlas:atlas-executor` (并行多个)

**生成策略**: 按文件分组并行生成，遵循项目现有测试风格

**文件命名规则**:
| 框架 | 源文件 | 测试文件 |
|:-----|:-------|:---------|
| Jest/Vitest | src/user.service.ts | src/user.service.test.ts 或 __tests__/user.service.test.ts |
| Pytest | src/user_service.py | tests/test_user_service.py |
| Go | src/user/service.go | src/user/service_test.go |

**测试结构要求**:
- Arrange-Act-Assert 三段式
- 描述性测试命名（should/when/then）
- 合理 Mock 设置（不过度 mock）
- 覆盖关键边界值

---

## Phase 4: 验证

**操作**: 运行测试 → 收集覆盖率 → 对比目标

**验证命令**:
| 框架 | 命令 |
|:-----|:-----|
| Jest | `npx jest --coverage --testPathPattern=<生成的测试>` |
| Vitest | `npx vitest run --coverage <生成的测试>` |
| Pytest | `pytest --cov=src <生成的测试>` |
| Go | `go test -cover ./...` |

**报告示例**:
```markdown
### 执行结果
- ✅ 测试通过: 25/25
- ⏱️ 执行时间: 3.2s

### 覆盖率变化
| 指标 | 之前 | 之后 | 变化 |
|:-----|:-----|:-----|:-----|
| 行覆盖 | 65% | 82% | +17% |
| 分支覆盖 | 58% | 75% | +17% |

### 目标达成
- 目标: 80% | 当前: 82% | ✅ 已达成
```

---

## 约束

**生成/质量**: 只为公开方法/函数生成；不改既有测试（除非明确要求）；遵循项目风格与 mock 库；AAA 三段式+边界覆盖。  
**执行**: Phase1=gatherer(haiku)；Phase1.5 必问模式+范围（交互再问 type/framework/coverage/planner）；Phase2 用选定规划器；Phase3=executor（交互询问模型，自动用 sonnet）。

---

## 示例

### 基础用法
```bash
/atlas:test-gen

/atlas:test-gen --scope src/services
/atlas:test-gen --framework vitest
/atlas:test-gen --type integration
/atlas:test-gen --coverage-target 90
```

### 输出示例

**生成完成**:
```
✅ 测试生成完成

生成统计:
- 新增测试文件: 5
- 新增测试用例: 25
- 覆盖方法: 15

测试文件:
- __tests__/user.service.test.ts (8 用例)
- __tests__/order.service.test.ts (6 用例)
- __tests__/auth.service.test.ts (5 用例)
- __tests__/payment.service.test.ts (4 用例)
- __tests__/notification.service.test.ts (2 用例)

覆盖率变化:
- 行覆盖: 65% → 82% (+17%)
- 目标 80% ✅ 已达成

建议:
1. 检查生成的测试是否符合业务逻辑
2. 考虑添加更多边界情况测试
3. 运行 `npm test` 确保所有测试通过
```
