---
description: 问题诊断与修复建议。分析问题根因，提供修复方案，可选执行修复。
argument-hint: <问题描述> [--scope path] [--fix]
---

# /bugfix - 问题诊断与修复

## 一、涉及的 Agent 和工具

### 1.1 Agent 说明

| Agent | 职责 | 模型 | 输出位置 |
|-------|------|------|---------|
| `atlas:information-gatherer` | 收集问题相关信息 | haiku | `.claude/gather/bugfix-<ts>/` |
| `atlas:planner` | 制定修复方案 | inherit | `.claude/plan/bugfix-<ts>/` |
| `atlas:atlas-executor` | 执行修复 | 用户选择 | 直接修改文件 |

### 1.2 工具说明

| 工具 | 用途 |
|------|------|
| `AskUserQuestion` | 确认选项 |
| `Task` | 调用 subagent |
| `git stash` | 创建检查点 |

### 1.3 信息传递链

```
gatherer → .claude/gather/bugfix-<ts>/context.json
    ↓
planner → .claude/plan/bugfix-<ts>/plan.json
    ↓
executor → 直接修复（无需重新扫描）
```

---

## 二、编排计划

### 2.1 强制流程

```
问题分析 → 确认选项 → 信息收集 → 根因分析 → 规划 → [--fix] 执行 → 测试 → 报告
```

### 2.2 模式行为定义

| 步骤 | 默认值 | --fix 时 | 可选值 |
|------|--------|---------|--------|
| 信息收集 | 是 | 是 | 是 / 否 |
| 检查点 | - | 询问 | 创建 / 跳过 |
| 规划器 | atlas:planner | 询问 | atlas:planner / 内置 Plan |
| Executor 模型 | - | 询问 | haiku / sonnet / opus |
| 测试节点 | - | 询问 | 修复后 / 不测试 |
| 测试模式 | - | 询问 | 编译测试 / 单元测试 / 编译+单元 |

### 2.3 执行步骤

**Step 1: 一次性确认所有选项**（开始时全部询问）

使用 `AskUserQuestion` 一次性收集所有配置：

```
问题 1: 执行模式
- 仅诊断（推荐）: 只分析问题，输出修复方案
- 执行修复: 诊断后自动执行修复

问题 2: 是否创建检查点（仅执行修复时）
- 创建（推荐）: 失败可回滚
- 跳过: 不创建

问题 3: 规划器选择
- atlas:planner（推荐）: 信任 gatherer 输出
- 内置 Plan: 会自行探索验证

问题 4: Executor 模型（仅执行修复时）
- sonnet（推荐）: 平衡性能与质量
- haiku: 快速简单修复
- opus: 复杂质量要求高

问题 5: 测试节点（仅执行修复时）
- 修复后（推荐）: 修复完成后测试
- 不测试: 跳过验证

问题 6: 测试模式（仅执行修复时）
- 编译测试（推荐）: tsc --noEmit
- 单元测试: npm test
- 编译+单元: 完整验证
```

**Step 2: 创建执行环境**（仅执行修复时）

```bash
# 创建状态目录
mkdir -p .claude/bugfix/.state

# 初始化状态文件
echo '{
  "executionId": "bugfix-<timestamp>",
  "timestamp": "<ISO-8601-timestamp>",
  "task": "<问题描述>",
  "status": "initializing",
  "currentStage": "initialization",
  "mode": "<diagnose-only/execute-fix>",
  "config": {
    "planner": "<atlas:planner/Plan>",
    "executorModel": "<haiku/sonnet/opus>",
    "testNode": "<after-fix/none>",
    "testMode": "<compile/unit/both>"
  },
  "checkpoint": {
    "stashId": "atlas-checkpoint-bugfix-<timestamp>",
    "created": false
  },
  "diagnosis": null,
  "fixApplied": false,
  "iterations": {
    "planning": 0,
    "execution": 0
  }
}' > .claude/bugfix/.state/bugfix-<timestamp>.json

# 创建检查点（如果选择创建）
git stash push -m "atlas-checkpoint-bugfix-<timestamp>"

# 更新状态
更新 .state/bugfix-<timestamp>.json: {
  checkpoint.created: true,
  currentStage: "checkpoint_created"
}
```

**Step 3: 信息收集**
```
Task(subagent_type="atlas:information-gatherer", model="haiku")
prompt: |
  任务 ID: bugfix-<timestamp>
  问题描述: [用户问题]
  搜索范围: [scope]
  输出目录: .claude/gather/bugfix-<timestamp>/
```

完成后更新状态:
.state/bugfix-<timestamp>.json: currentStage="gathering_completed"
```

**Step 4: 根因分析与修复规划**（支持循环修改）

**重要：使用统一的 bugfix-<timestamp> ID，所有文件在同一目录操作**

```
┌─────────────────────────────────────────┐
│ 4.1 执行规划（首次）                     │
│ Task(subagent_type="<用户选择的规划器>") │
│ 输出: .claude/plan/bugfix-<ts>/plan.json│
└─────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│ 4.2 展示诊断结果                         │
│ - 根因分析（文件:行号）                  │
│ - 问题类型和复杂度                       │
│ - 修复方案（策略、步骤、风险）           │
└─────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│ 4.3 用户确认                             │
│ AskUserQuestion:                        │
│ - 继续执行（如选择执行修复模式）         │
│ - 修改方案: 用户提出调整意见            │
│ - 完成诊断: 仅输出报告（诊断模式）       │
└─────────────────────────────────────────┘
         ↓
    [用户选择修改]
         ↓
┌─────────────────────────────────────────┐
│ 4.4 重新规划（版本化）                   │
│ 使用相同规划器，传入修改意见             │
│ 输出策略:                                │
│ - 简单: 覆盖 plan.json                  │
│ - 复杂: 创建 plan.v2.json, plan.v3.json│
│ 返回 4.2（循环直到用户确认）             │
└─────────────────────────────────────────┘

完成后更新状态:
.state/bugfix-<timestamp>.json: {
  currentStage: "planning_approved",
  planVersion: "final" 或 "v2",
  diagnosis: {
    location: "file:line",
    type: "...",
    complexity: "simple/moderate/complex"
  },
  iterations.planning: <循环次数>
}

输出文件示例:
.claude/plan/bugfix-<timestamp>/
├── plan.json (或 plan.final.json)  # 最终方案
├── plan.v1.json  # 可选: 历史版本
└── plan.v2.json  # 可选: 历史版本
```

**Step 5: 执行修复**（仅执行修复模式，支持循环）

```
┌─────────────────────────────────────────┐
│ 5.1 执行修复                             │
│ Task(subagent_type="atlas:atlas-executor")│
│ model=<用户选择的模型>                   │
└─────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│ 5.2 展示修复结果                         │
│ - 修改的文件和位置                       │
│ - 修复状态（成功/失败）                  │
└─────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│ 5.3 用户决策                             │
│ AskUserQuestion:                        │
│ - 继续验证（推荐，如果成功）             │
│ - 重新修复: 用户不满意，调整修复方案    │
│ - 回滚变更                               │
└─────────────────────────────────────────┘
         ↓
    [用户选择重新修复]
         ↓
┌─────────────────────────────────────────┐
│ 5.4 重新执行                             │
│ 返回 5.1                                 │
└─────────────────────────────────────────┘

完成后更新状态:
.state/bugfix-<timestamp>.json: {
  currentStage: "fix_applied",
  fixApplied: true,
  iterations.execution: <循环次数>
}
```

**Step 6: 验证测试**（根据 Step 1 选择执行）

```bash
# 根据配置执行测试
根据 testMode 执行: tsc --noEmit / npm test / 两者

# 更新状态
更新 .state/bugfix-<timestamp>.json: currentStage="testing_completed"
```

**Step 7: 清理和报告**

```bash
# 更新最终状态
更新 .state/bugfix-<timestamp>.json: {
  status: "completed",
  currentStage: "finished",
  completedAt: "<ISO-8601-timestamp>"
}

# 输出报告（见第四章）
```

---

## 三、细节要点

### 3.1 任务 ID 管理原则

**统一任务 ID**:
- 格式: `bugfix-<timestamp>` (例如: `bugfix-20240115-143000`)
- 从 Step 1 到 Step 7 使用**同一个** ID
- 所有相关文件使用此 ID 关联

**目录结构**:
```
.claude/
├── gather/bugfix-<timestamp>/     # gatherer 输出（不变）
│   └── context.json
├── plan/bugfix-<timestamp>/        # planner 输出（版本化）
│   ├── plan.json (或 plan.final.json)
│   ├── plan.v1.json (可选)
│   └── plan.v2.json (可选)
├── bugfix/.state/                  # 状态文件
│   └── bugfix-<timestamp>.json
```

**版本化策略**:
- **简单场景**: 直接覆盖 `plan.json`
- **复杂场景**: 创建版本文件 `plan.v2.json`, `plan.v3.json` 等
- 状态文件记录 `planVersion` 字段

### 3.2 主进程职责

**允许**: AskUserQuestion / Task 调用 / 读取 agent 输出 / Git 操作

**禁止**: Read/Grep/Glob 读代码 / Edit/Write 修改文件 / 直接分析代码

### 3.3 根因分析输出格式

```markdown
## 问题诊断
**问题描述**: [用户描述]
**问题类型**: [错误类型]
**复杂度**: simple | moderate | complex

## 根因分析
**定位**: [文件:行号]
**原因**: [具体原因]
**影响**: [影响范围]

## 修复方案
**策略**: [直接修复/防御性修复/重构]
**步骤**: 1. [步骤] - [文件:位置]
**验证**: [验证方法]
**风险**: [潜在风险]
```

---

## 四、示例

### 示例 1: 仅诊断

```
用户: /bugfix 登录按钮点击无反应

1. 问题分析: 事件绑定问题
2. Gatherer: 收集登录组件代码
3. 根因分析: src/components/Login.tsx:45 onClick 未绑定
4. 输出修复方案
```

### 示例 2: 诊断+修复

```
用户: /bugfix 用户数据丢失 --fix

1. 确认选项: 执行 + 创建检查点 + opus + 编译+单元测试
2. Gatherer: 收集 UserService 代码
3. 根因分析: 并发竞态条件
4. Planner: 生成修复计划
5. Executor: 执行修复
6. 测试: tsc --noEmit && npm test ✅
7. 报告
```

---

## 五、核心约束

### 必须做

- ✅ **Step 1**: 开始时一次性确认所有配置（模式、规划器、模型、测试选项）
- ✅ **Step 2**: 创建状态目录 `.claude/bugfix/.state/` 和状态文件（执行修复模式）
- ✅ **Step 2**: 在每个关键步骤完成后更新状态文件的 `currentStage` 字段
- ✅ **Step 3**: 使用 `Task(subagent_type="atlas:information-gatherer", model="haiku")`
- ✅ **Step 4**: 使用用户选择的规划器，输出到 `.claude/plan/bugfix-<ts>/`
- ✅ **Step 4.2-4.4**: 展示诊断给用户，支持循环修改直到用户确认
- ✅ **Step 5**: 从 plan.json 提取修改点嵌入 executor prompt（执行修复模式）
- ✅ **Step 5.2-5.4**: 展示修复结果，支持用户重新修复或调整
- ✅ **Step 6**: 根据 Step 1 的选择执行验证测试
- ✅ **Step 7**: 更新最终状态并输出报告

### 禁止做

- ❌ 主进程直接读取代码（除了 agent 输出的 JSON 文件）
- ❌ 主进程直接修改文件（所有修改必须通过 executor）
- ❌ 跳过信息收集直接诊断
- ❌ 跳过规划直接执行修复
- ❌ executor 重新扫描文件（应使用 plan.json 的修改点）
- ❌ 在 Step 1 之后还有其他的 AskUserQuestion（除了 Step 4.3 和 5.3 的确认循环）
- ❌ 忘记更新状态文件的 `currentStage`（执行修复模式）
- ❌ 在用户未确认的情况下继续执行下一步
