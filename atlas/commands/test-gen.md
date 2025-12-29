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

Phase 0 环境检测 → Phase 1 目标分析 → Phase 2 用例规划 → Phase 3 测试生成 → Phase 4 验证

### Subagent 分配

| Phase | 功能 | Subagent | 说明 |
|:------|:-----|:---------|:-----|
| 0 | 环境检测 | 主进程 | 检测测试框架和现有覆盖率 |
| 1 | 目标分析 | `atlas:information-gatherer` | 分析目标代码 |
| 2 | 用例规划 | `Plan` | 规划测试用例 |
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

## Phase 2: 用例规划

**Subagent**: `Plan`

**核心原则**：Plan agent 必须**优先使用 Phase 1 输出**，最小化额外读取。

**固定输入结构**:
```
Task(subagent_type="Plan")
prompt: |
  ## 任务
  为目标代码生成测试用例规划

  ## ⚠️ 强制信息源（必须先读取）
  **Phase 1 输出**: `.claude/gather/test-gen-<task-id>/`
  - `context.json`: 目标分析数据（函数签名、分支路径、依赖项）

  **你必须**:
  1. 首先读取上述文件
  2. 基于已有签名和分支信息规划用例
  3. 仅在以下情况补充读取:
     - 分支条件不明（需查看具体逻辑）
     - Mock 目标不清（需确认依赖接口）

  ## 信息充足性检查
  - [ ] 函数签名和参数类型
  - [ ] 分支路径列表
  - [ ] 依赖项（Mock 目标）
  - [ ] 现有测试覆盖情况

  如 4 项均已获取 → **禁止额外读取**，直接规划
  如缺失 < 5项 → 针对性补充
  如缺失 5+ 项 → 标记 gatherer 信息不足，建议重新收集

  ## 输出
  每个目标的用例列表:
  - 正常路径测试
  - 边界值测试
  - 异常处理测试
  - Mock 设置说明
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

**生成约束**:
- 只为公开方法/函数生成测试
- 不修改现有测试（除非明确要求）
- 遵循项目现有测试风格
- 使用项目已有的 mock 库

**质量约束**:
- 每个测试必须有 Arrange-Act-Assert 结构
- 测试命名必须描述预期行为
- Mock 设置必须合理（不过度 mock）
- 边界值测试必须覆盖关键边界

**执行约束**:
- Phase 1 必须使用 information-gatherer (model="haiku")
- Phase 2 必须使用 Plan agent
- Phase 3 必须使用 atlas-executor (询问用户选择模型)

---

## 示例

### 基础用法
```bash
# 为全项目生成测试
/atlas:test-gen

# 指定范围
/atlas:test-gen --scope src/services

# 指定框架
/atlas:test-gen --framework vitest

# 生成集成测试
/atlas:test-gen --type integration

# 设置覆盖率目标
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

**部分失败**:
```
⚠️ 测试生成部分完成

生成统计:
- 新增测试文件: 5
- 新增测试用例: 25
- 失败用例: 3

失败详情:
1. user.service.test.ts:45 - TypeError: Cannot read property 'create' of undefined
   建议: 检查 PrismaService mock 配置

2. order.service.test.ts:78 - Expected ConflictException but got InternalServerError
   建议: 检查异常处理逻辑

覆盖率: 75% (未达目标 80%)

建议:
1. 修复失败的测试用例
2. 添加缺失场景的测试
```
