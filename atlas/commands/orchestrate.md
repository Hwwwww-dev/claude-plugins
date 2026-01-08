---
description: 任务协调与并发执行引擎。处理复杂多步骤任务、批量操作、项目级变更。支持回滚和断点续传。
argument-hint: <任务描述> [--parallel|--sequential] [--dry-run] [--no-gather] [--auto-rollback] [--resume <id>]
---

# /orchestrate - 任务协调引擎

## 一、涉及的 Agent 和工具

### 1.1 Agent 说明

| Agent | 职责 | 模型 | 输出位置 |
|-------|------|------|---------|
| `atlas:information-gatherer` | 收集项目信息（结构、依赖、代码片段） | haiku | `.claude/gather/<task-id>/` |
| `atlas:planner` | 基于 gatherer 输出制定执行计划 | inherit | `.claude/plan/<task-id>/` |
| `atlas:atlas-executor` | 执行具体子任务 | 用户选择 | 直接修改文件 |

### 1.2 工具说明

| 工具 | 用途 | 调用方式 |
|------|------|---------|
| `AskUserQuestion` | 与用户交互确认选项 | 主进程直接调用 |
| `Task` | 调用 subagent | `Task(subagent_type="...", model="...")` |
| `git stash` | 创建/恢复检查点 | Bash 执行 |

### 1.3 信息传递链

```
gatherer → .claude/gather/<task-id>/context.json
    ↓
planner → 读取 context.json → 输出 .claude/plan/<task-id>/plan.json
    ↓
主进程 → 读取 plan.json → 嵌入 executor prompt
    ↓
executor → 直接修改文件（无需重新扫描）
```

**核心原则**: planner 输出精确修改点，executor 直接执行。

---

## 二、编排计划

### 2.1 强制流程

```
确认模式+测试 → 检查点 → 信息收集 → 选规划器 → 规划 → 选模型 → 执行 → 统一测试 → 报告
```

**禁止**: 主进程直接读取代码 / 主进程直接修改文件 / 跳过任何步骤

### 2.2 模式行为定义

| 步骤 | 自动模式 | 交互模式 | dry-run | 可选值 |
|------|---------|---------|---------|--------|
| 执行策略 | auto | 询问 | auto | auto / parallel / sequential |
| 信息收集 | 是 | 询问 | 是 | 是 / 否 |
| 检查点 | 创建 | 询问 | 跳过 | 创建 / 跳过 |
| 规划器 | atlas:planner | 询问 | atlas:planner | atlas:planner / 内置 Plan |
| Executor 模型 | sonnet | 询问 | - | haiku / sonnet / opus |
| 测试节点 | 统一测试 | **开始时询问** | - | 每个子任务后 / 统一测试 / 不测试 |
| 测试模式 | 编译测试 | **开始时询问** | - | 编译测试 / 单元测试 / 编译+单元 |
| 失败处理 | **询问** | 询问 | - | 回滚 / 跳过 / 重试 / 终止 |

### 2.3 执行步骤

**Step 1: 确认执行模式和测试选项**
```
AskUserQuestion: 选择执行模式
- 自动模式（推荐）: 全流程使用推荐选项
- 交互模式: 每步确认
- dry-run: 只规划不执行

AskUserQuestion: 选择测试节点（交互模式询问）
- 统一测试（推荐）: 全部执行完成后统一验证
- 每个子任务后: 每个 executor 完成后立即测试
- 不测试: 跳过验证

AskUserQuestion: 选择测试模式（交互模式询问）
- 编译测试（推荐）: tsc --noEmit 确保语法正确
- 单元测试: npm test 确保功能正常
- 编译+单元: 完整验证
```

**Step 2: 创建检查点**（非 dry-run）
```bash
git stash push -m "atlas-checkpoint-{execution-id}"
```

**Step 3: 信息收集**
```
Task(subagent_type="atlas:information-gatherer", model="haiku")
prompt: |
  任务 ID: <task-id>
  任务描述: [用户任务]
  收集目标: [范围、关注点]
  输出目录: .claude/gather/<task-id>/
```

**Step 4: 选择规划器**（交互模式询问）
- atlas:planner（推荐）: 信任 gatherer 输出，最小化扫描
- 内置 Plan: 会自行探索验证

**Step 5: 任务规划**
```
Task(subagent_type="atlas:planner")
prompt: |
  任务: [用户任务描述]
  Gatherer 输出: .claude/gather/<task-id>/
  输出目录: .claude/plan/<task-id>/
```

**Step 6: 选择 Executor 模型**（交互模式询问）
- 跟随主对话（推荐）
- haiku / sonnet / opus

**Step 7: 执行**
```
Task(subagent_type="atlas:atlas-executor", model=用户选择)
prompt: |
  子任务: #N [描述]
  修改点: [从 plan.json 提取的精确修改信息]
  上下文: [嵌入的代码片段]
```

**Step 8: 验证测试**（根据 Step 1 选择执行）

| 测试节点 | 执行时机 |
|---------|---------|
| 每个子任务后 | 每个 executor 完成后立即运行测试 |
| 统一测试 | 所有 executor 完成后运行一次测试 |
| 不测试 | 跳过 |

| 测试模式 | 命令 |
|---------|------|
| 编译测试 | `tsc --noEmit` |
| 单元测试 | `npm test` |
| 编译+单元 | `tsc --noEmit && npm test` |

**Step 9: 聚合报告**

---

## 三、细节要点

### 3.1 主进程职责

**允许**:
- ✅ 使用 AskUserQuestion 与用户交互
- ✅ 使用 Task 调用 agent
- ✅ 读取 agent 输出（`.claude/gather/`, `.claude/plan/`）
- ✅ Git 检查点操作

**禁止**:
- ❌ 使用 Read/Grep/Glob 读取代码文件
- ❌ 使用 Edit/Write 修改代码文件
- ❌ 直接分析代码逻辑

### 3.2 信息传递要求

**gatherer 输出必须包含**:
- `context.json.codeSnippets`: 关键代码片段（含行号）
- `context.json.recommendations`: 给 planner 的建议

**planner 输出必须包含**:
- `plan.json.subtasks[].modifications`: 精确到行号的修改点
- `plan.json.subtasks[].context`: 嵌入的代码片段

**executor 输入必须包含**:
- 从 plan.json 提取的修改点（直接嵌入 prompt）
- 无需额外读取文件

### 3.3 文件冲突处理

并行 executor 修改同一文件会导致冲突：

1. **按文件分组**: 修改同一文件的操作分给同一个 executor
2. **串行化**: 必须分开的任务改为串行执行
3. **分阶段**: 先完成共享依赖，再并行执行后续

### 3.4 失败处理

**auto-rollback 模式**: 自动 `git stash pop`

**manual 模式**:
```
子任务 #N 失败
选项: 回滚 / 跳过 / 重试 / 终止
```

### 3.5 断点续传

```bash
/orchestrate --resume <task-id>
```

读取 `.claude/orchestrate/.state/<task-id>.json` 继续执行。

---

## 四、示例

### 示例 1: 完整流程（自动模式）

```
用户: /orchestrate 给所有 React 组件添加 TypeScript 类型

1. 确认模式: 自动模式
2. 检查点: git stash push -m "atlas-checkpoint-add-types-20240115"
3. Gatherer: 收集所有 React 组件
   → .claude/gather/add-types-20240115/context.json
4. Planner: 读取 context.json → 生成执行计划
   → .claude/plan/add-types-20240115/plan.json
5. Executor: 读取 plan.json → 并行执行 3 个子任务
6. 报告: 成功修改 6 个文件
7. 清理: git stash drop
```

### 示例 2: 交互模式

```
用户: /orchestrate 重构用户模块 --interactive

1. 确认模式: 交互模式
2. 询问: 是否创建检查点? → 是
3. 询问: 是否收集信息? → 是
4. Gatherer: 收集用户模块信息
5. 询问: 选择规划器? → atlas:planner
6. Planner: 生成执行计划
7. 询问: 选择模型? → opus
8. Executor: 执行重构
9. 报告
```

### 示例 3: dry-run 模式

```
用户: /orchestrate 批量更新 API 路由 --dry-run

1. 确认模式: dry-run
2. 跳过检查点
3. Gatherer: 收集 API 路由信息
4. Planner: 生成执行计划
5. 输出: 预览报告（不执行）
   - 影响文件: 12 个
   - 子任务: 4 个
   - 执行策略: parallel
```

---

## 五、输出格式

### 执行报告

```markdown
# Atlas 执行报告

## 任务
[描述]

## 执行 ID
task-20240115-103000

## 统计
- 子任务: X 个
- 成功: Y / 失败: Z

## 修改文件
- file1.ts (行 45-60)
- file2.ts (行 120)

## 失败详情（如有）
- 子任务#N: [原因] → [建议]

## 检查点
- 状态: 已清理 / 可用于回滚
- 命令: /orchestrate --resume task-20240115-103000

## 后续建议
- [建议1]
```

---

## 六、核心约束

### 必须做

- ✅ Step 1: 确认执行模式
- ✅ Step 3: 使用 `Task(subagent_type="atlas:information-gatherer", model="haiku")`
- ✅ Step 4: 询问用户选择规划器（atlas:planner 或 内置 Plan）
- ✅ Step 5: 使用规划器，输出到 `.claude/plan/<task-id>/`
- ✅ Step 7: 从 plan.json 提取修改点嵌入 executor prompt
- ✅ Step 8: 执行完成后询问验证方式
- ✅ Step 9: 输出固定格式报告

### 禁止做

- ❌ 主进程直接读取代码
- ❌ 主进程直接修改文件
- ❌ 跳过信息收集直接规划（除非 --no-gather）
- ❌ 跳过规划直接执行
- ❌ executor 重新扫描文件（应使用 plan.json 的修改点）
