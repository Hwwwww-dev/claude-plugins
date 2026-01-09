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

**Step 1: 一次性确认所有选项**（开始时全部询问）

使用 `AskUserQuestion` 一次性收集所有配置：

```
问题 1: 执行模式
- 自动模式（推荐）: 全流程使用推荐选项
- 交互模式: 每步确认
- dry-run: 只规划不执行

问题 2: 规划器选择
- atlas:planner（推荐）: 信任 gatherer 输出，最小化扫描
- 内置 Plan: 会自行探索验证

问题 3: Executor 模型
- sonnet（推荐）: 平衡性能与成本
- haiku: 快速简单任务
- opus: 复杂质量要求高

问题 4: 测试节点
- 统一测试（推荐）: 全部执行完成后统一验证
- 每个子任务后: 每个 executor 完成后立即测试
- 不测试: 跳过验证

问题 5: 测试模式
- 编译测试（推荐）: tsc --noEmit 确保语法正确
- 单元测试: npm test 确保功能正常
- 编译+单元: 完整验证
```

**Step 2: 创建执行环境**
```bash
# 创建状态目录
mkdir -p .claude/orchestrate/.state

# 初始化状态文件
echo '{
  "executionId": "<task-id>",
  "timestamp": "<ISO-8601-timestamp>",
  "task": "<用户任务描述>",
  "status": "initializing",
  "currentStage": "initialization",
  "config": {
    "mode": "<auto/interactive/dry-run>",
    "planner": "<atlas:planner/Plan>",
    "executorModel": "<haiku/sonnet/opus>",
    "testNode": "<unified/per-task/none>",
    "testMode": "<compile/unit/both>"
  },
  "checkpoint": {
    "stashId": "atlas-checkpoint-<task-id>",
    "created": false
  },
  "subtasks": [],
  "progress": {
    "total": 0,
    "completed": 0,
    "failed": 0,
    "pending": 0
  },
  "iterations": {
    "planning": 0,
    "execution": 0
  }
}' > .claude/orchestrate/.state/<task-id>.json

# 创建检查点（非 dry-run）
git stash push -m "atlas-checkpoint-{execution-id}"

# 更新状态
更新 .state/<task-id>.json: {
  checkpoint.created: true,
  currentStage: "checkpoint_created"
}
```

**Step 3: 信息收集**
```
Task(subagent_type="atlas:information-gatherer", model="haiku")
prompt: |
  任务 ID: <task-id>
  任务描述: [用户任务]
  收集目标: [范围、关注点]
  输出目录: .claude/gather/<task-id>/

完成后更新状态:
.state/<task-id>.json: currentStage="gathering_completed"
```

**Step 4: 任务规划（支持循环修改）**

**重要：整个流程使用统一的 task-id，所有文件在同一目录下操作**

```
┌─────────────────────────────────────────┐
│ 4.1 执行规划（首次）                     │
│ Task(subagent_type="<用户选择的规划器>") │
│ 输出: .claude/plan/<task-id>/plan.json  │
└─────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│ 4.2 展示规划给用户                       │
│ 读取并格式化输出 plan.json               │
│ 显示: 子任务列表、执行策略、影响范围     │
└─────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│ 4.3 用户确认                             │
│ AskUserQuestion:                        │
│ - 继续执行（推荐）                       │
│ - 修改规划: 用户提出修改意见            │
│ - 取消任务                               │
└─────────────────────────────────────────┘
         ↓
    [用户选择修改]
         ↓
┌─────────────────────────────────────────┐
│ 4.4 重新规划（版本化）                   │
│ 使用相同规划器，传入修改意见             │
│ 输出策略（二选一）:                      │
│ 方案A: 覆盖 plan.json（简单场景）       │
│ 方案B: 创建 plan.v2.json, plan.v3.json  │
│        保留历史版本（复杂场景）          │
│ 返回 4.2（循环直到用户确认）             │
└─────────────────────────────────────────┘

完成后更新状态:
.state/<task-id>.json: {
  currentStage: "planning_approved",
  planVersion: "final" 或 "v3",  # 最终使用的版本
  planHistory: ["v1", "v2", "v3"],  # 可选: 历史版本列表
  subtasks: [
    {"id": 1, "status": "pending", "description": "...", "files": [...]},
    {"id": 2, "status": "pending", "description": "...", "files": [...]},
    ...
  ],
  progress: {
    total: N,
    completed: 0,
    failed: 0,
    pending: N
  },
  iterations.planning: <循环次数>
}

输出文件示例:
.claude/plan/<task-id>/
├── plan.json (或 plan.final.json)  # 最终确认的计划
├── plan.v1.json  # 可选: 第一版（如需保留历史）
├── plan.v2.json  # 可选: 第二版（如需保留历史）
└── ...
```

**Step 5: 任务执行（支持循环修改）**

```
┌─────────────────────────────────────────┐
│ 5.1 并发启动 Executors                   │
│ Task(subagent_type="atlas:atlas-executor")│
│ model=<用户选择的模型>                   │
│ 每个子任务一个 executor                  │
└─────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│ 5.2 收集执行结果                         │
│ 记录成功/失败的子任务                    │
└─────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│ 5.3 展示执行结果                         │
│ - 成功: X 个子任务                       │
│ - 失败: Y 个子任务（含原因）             │
│ - 修改文件列表                           │
└─────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│ 5.4 用户决策                             │
│ AskUserQuestion:                        │
│ - 继续验证（推荐，如果全部成功）         │
│ - 修复失败任务: 针对失败项重新规划执行   │
│ - 调整结果: 用户提出修改意见            │
│ - 回滚变更                               │
└─────────────────────────────────────────┘
         ↓
    [用户选择修复/调整]
         ↓
┌─────────────────────────────────────────┐
│ 5.5 重新执行失败/调整任务                │
│ 返回 5.1（仅针对需要修改的子任务）       │
└─────────────────────────────────────────┘

完成后更新状态:
.state/<task-id>.json: {
  currentStage: "execution_completed",
  subtasks: [更新每个子任务的 status: "completed"/"failed"],
  progress: {
    total: N,
    completed: X,
    failed: Y,
    pending: 0
  },
  iterations.execution: <循环次数>
}
```

**Step 6: 验证测试**（根据 Step 1 选择执行）

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

```bash
# 更新状态
更新 .state/<task-id>.json: currentStage="testing_completed"
```

**Step 7: 清理和报告**

```bash
# 更新最终状态
更新 .state/<task-id>.json: {
  status: "completed",
  currentStage: "finished",
  completedAt: "<ISO-8601-timestamp>",
  checkpoint: {
    stashId: "...",
    created: true,
    cleaned: true  # 如果已清理检查点
  }
}

# 输出报告（见第五章）
```

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

### 3.2 任务 ID 管理原则

**统一任务 ID**:
- 一个任务从 Step 1 到 Step 7 使用**同一个** task-id
- 格式: `<action>-<date>-<time>` (例如: `add-types-20240115-103000`)
- 所有相关文件使用此 ID 关联

**目录结构**:
```
.claude/
├── gather/<task-id>/          # gatherer 输出（不变）
│   └── context.json
├── plan/<task-id>/             # planner 输出（版本化）
│   ├── plan.json (或 plan.final.json)
│   ├── plan.v1.json (可选)
│   └── plan.v2.json (可选)
├── orchestrate/.state/         # 状态文件
│   └── <task-id>.json
```

**版本化策略**:
- **简单场景** (1-2次修改): 直接覆盖 `plan.json`
- **复杂场景** (3+次修改): 创建版本文件 `plan.v2.json`, `plan.v3.json` 等
- 状态文件记录 `planVersion` 字段，指向最终使用的版本

### 3.3 信息传递要求

**gatherer 输出必须包含**:
- `context.json.codeSnippets`: 关键代码片段（含行号）
- `context.json.recommendations`: 给 planner 的建议

**planner 输出必须包含**:
- `plan.json.subtasks[].modifications`: 精确到行号的修改点
- `plan.json.subtasks[].context`: 嵌入的代码片段

**executor 输入必须包含**:
- 从 plan.json (或 plan.final.json) 提取的修改点（直接嵌入 prompt）
- 无需额外读取文件

### 3.4 文件冲突处理

并行 executor 修改同一文件会导致冲突：

1. **按文件分组**: 修改同一文件的操作分给同一个 executor
2. **串行化**: 必须分开的任务改为串行执行
3. **分阶段**: 先完成共享依赖，再并行执行后续

### 3.5 失败处理

**auto-rollback 模式**: 自动 `git stash pop`

**manual 模式**:
```
子任务 #N 失败
选项: 回滚 / 跳过 / 重试 / 终止
```

### 3.6 状态文件完整示例

执行过程中的完整状态文件结构：

```json
{
  "executionId": "add-types-20240115-103000",
  "timestamp": "2024-01-15T10:30:00Z",
  "task": "给所有 React 组件添加 TypeScript 类型",
  "status": "in_progress",
  "currentStage": "execution_completed",
  "config": {
    "mode": "auto",
    "planner": "atlas:planner",
    "executorModel": "sonnet",
    "testNode": "unified",
    "testMode": "compile"
  },
  "checkpoint": {
    "stashId": "atlas-checkpoint-add-types-20240115-103000",
    "created": true,
    "cleaned": false
  },
  "subtasks": [
    {
      "id": 1,
      "status": "completed",
      "description": "为 auth 组件添加类型",
      "files": ["Login.tsx", "Register.tsx"]
    },
    {
      "id": 2,
      "status": "completed",
      "description": "为 dashboard 组件添加类型",
      "files": ["Overview.tsx", "Analytics.tsx"]
    },
    {
      "id": 3,
      "status": "failed",
      "description": "为 shared 组件添加类型",
      "files": ["Button.tsx", "Input.tsx"],
      "error": "类型定义冲突"
    }
  ],
  "progress": {
    "total": 3,
    "completed": 2,
    "failed": 1,
    "pending": 0
  },
  "iterations": {
    "planning": 1,
    "execution": 2
  },
  "completedAt": null
}
```

### 3.7 断点续传

```bash
/orchestrate --resume <task-id>
```

**恢复流程**:
1. 读取 `.claude/orchestrate/.state/<task-id>.json`
2. 检查 `currentStage` 字段确定中断位置
3. 从中断的阶段继续执行（跳过已完成的步骤）
4. 保持用户之前的配置选项
5. 根据 `subtasks` 和 `progress` 恢复执行进度

**状态阶段映射**:
- `initialization` → 从 Step 2 开始
- `checkpoint_created` → 从 Step 3 开始
- `gathering_completed` → 从 Step 4 开始
- `planning_approved` → 从 Step 5 开始
- `execution_completed` → 从 Step 6 开始
- `testing_completed` → 输出报告
- `finished` → 已完成，无需恢复

**续传示例**:
```
读取状态: add-types-20240115-103000.json
发现: currentStage = "execution_completed", 1 个失败子任务

展示进度:
✅ 子任务 #1: 完成
✅ 子任务 #2: 完成
❌ 子任务 #3: 失败 - 类型定义冲突

询问用户:
- 重试失败任务（推荐）
- 跳过失败，继续测试
- 回滚全部变更
- 放弃任务
```

---

## 四、示例

### 示例 1: 完整流程（自动模式）

```
用户: /orchestrate 给所有 React 组件添加 TypeScript 类型

1. 一次性询问所有配置:
   - 执行模式: 自动模式（推荐）✓
   - 规划器: atlas:planner（推荐）✓
   - Executor 模型: sonnet（推荐）✓
   - 测试节点: 统一测试（推荐）✓
   - 测试模式: 编译测试（推荐）✓

2. 创建执行环境:
   - mkdir -p .claude/orchestrate/.state
   - 创建 add-types-20240115.json
   - git stash push -m "atlas-checkpoint-add-types-20240115"

3. Gatherer: 收集所有 React 组件
   → .claude/gather/add-types-20240115/context.json
   → 更新状态: currentStage="gathering_completed"

4. Planner: 生成执行计划
   → .claude/plan/add-types-20240115/plan.json
   → 展示规划给用户
   → 用户确认: 继续执行 ✓
   → 更新状态: currentStage="planning_approved"

5. Executor: 并行执行 3 个子任务
   → 全部成功
   → 用户确认: 继续验证 ✓
   → 更新状态: currentStage="execution_completed"

6. 验证测试: tsc --noEmit
   → 通过 ✓
   → 更新状态: currentStage="testing_completed"

7. 报告: 成功修改 6 个文件
   → 更新状态: status="completed", currentStage="finished"
```

### 示例 2: 带循环修改的流程

```
用户: /orchestrate 重构用户认证模块

1. 一次性询问所有配置:
   - 执行模式: 交互模式 ✓
   - 规划器: atlas:planner ✓
   - Executor 模型: opus ✓
   - 测试节点: 统一测试 ✓
   - 测试模式: 编译+单元 ✓

2-3. 创建环境 + 信息收集
   → .claude/gather/refactor-auth-20240115/

4. Planner: 生成初始计划
   → 展示: 3 个子任务（重构 login, 重构 register, 更新 middleware）
   → 用户: "修改规划 - 需要先重构 middleware，再处理 login/register"

   4.4 重新规划（循环 1）
   → 展示: 调整后的顺序（middleware → login → register）
   → 用户: 继续执行 ✓

5. Executor: 执行 3 个子任务
   → 子任务 1 (middleware): 成功 ✓
   → 子任务 2 (login): 失败 - 类型不匹配
   → 子任务 3 (register): 成功 ✓

   5.4 用户决策
   → 用户: "修复失败任务"

   5.5 重新执行（循环 1）
   → 仅重新执行子任务 2
   → 成功 ✓
   → 用户: 继续验证 ✓

6. 验证测试: tsc --noEmit && npm test
   → 全部通过 ✓

7. 报告: 成功重构用户认证模块
```

### 示例 3: dry-run 模式

```
用户: /orchestrate 批量更新 API 路由 --dry-run

1. 一次性询问所有配置:
   - 执行模式: dry-run ✓
   - 规划器: atlas:planner ✓
   - 其他选项: 使用默认值（dry-run 不执行）

2. 跳过检查点创建
   → 创建状态文件（标记为 dry-run）

3. Gatherer: 收集 API 路由信息
   → .claude/gather/update-routes-20240115/

4. Planner: 生成执行计划
   → .claude/plan/update-routes-20240115/plan.json
   → 展示完整计划给用户

5. 输出预览报告（不执行）:
   - 影响文件: 12 个
   - 子任务: 4 个
   - 执行策略: parallel
   - 预计修改点: [详细列表]

6. 提示: 如需执行，使用 /orchestrate --resume update-routes-20240115
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

## 配置
- 执行模式: [自动/交互/dry-run]
- 规划器: [atlas:planner/Plan]
- Executor 模型: [haiku/sonnet/opus]
- 测试节点: [统一测试/每个子任务后/不测试]
- 测试模式: [编译测试/单元测试/编译+单元]

## 统计
- 子任务: X 个
- 成功: Y / 失败: Z
- 规划循环次数: N
- 执行循环次数: M

## 修改文件
- file1.ts (行 45-60)
- file2.ts (行 120)

## 失败详情（如有）
- 子任务#N: [原因] → [已修复/待处理]

## 状态文件
- 位置: `.claude/orchestrate/.state/task-20240115-103000.json`
- 最终状态: completed
- 当前阶段: finished

## 检查点
- 状态: 已清理 / 可用于回滚
- Stash ID: atlas-checkpoint-{execution-id}
- 恢复命令: `git stash list` 查看, `git stash apply stash@{N}` 恢复

## 断点续传
- 命令: `/orchestrate --resume task-20240115-103000`
- 说明: 如果任务中断，可使用此命令从中断位置继续

## 后续建议
- [建议1]
- [建议2]
```

---

## 六、核心约束

### 必须做

- ✅ **Step 1**: 开始时一次性确认所有配置（执行模式、规划器、模型、测试选项）
- ✅ **Step 2**: 创建状态目录 `.claude/orchestrate/.state/` 和状态文件 `<task-id>.json`
- ✅ **Step 2**: 在每个关键步骤完成后更新状态文件的 `currentStage` 字段
- ✅ **Step 2**: 创建 git 检查点（非 dry-run 模式）
- ✅ **Step 3**: 使用 `Task(subagent_type="atlas:information-gatherer", model="haiku")`
- ✅ **Step 4**: 使用用户选择的规划器，输出到 `.claude/plan/<task-id>/`
- ✅ **Step 4.2-4.4**: 展示规划给用户，支持循环修改直到用户确认
- ✅ **Step 5**: 从 plan.json 提取修改点嵌入 executor prompt
- ✅ **Step 5.3-5.5**: 展示执行结果，支持用户修复失败任务或调整结果
- ✅ **Step 6**: 根据 Step 1 的选择执行验证测试
- ✅ **Step 7**: 更新最终状态为 `completed` 和输出固定格式报告

### 禁止做

- ❌ 主进程直接读取代码（除了 agent 输出的 JSON 文件）
- ❌ 主进程直接修改文件（所有修改必须通过 executor）
- ❌ 跳过信息收集直接规划（除非 --no-gather）
- ❌ 跳过规划直接执行
- ❌ executor 重新扫描文件（应使用 plan.json 的修改点）
- ❌ 在 Step 1 之后还有其他的 AskUserQuestion（除了 Step 4.3 和 5.4 的确认循环）
- ❌ 忘记更新状态文件的 `currentStage`
- ❌ 在用户未确认的情况下继续执行下一步
