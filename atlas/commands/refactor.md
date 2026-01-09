---
description: 智能重构命令。识别代码问题并执行特定模式的自动化重构，支持预览和交互式确认。
argument-hint: <pattern> [--scope path] [--dry-run] [--interactive]
---

# /refactor - 智能重构命令

## 一、涉及的 Agent 和工具

### 1.1 Agent 说明

| Agent | 职责 | 模型 | 输出位置 |
|-------|------|------|---------|
| `atlas:information-gatherer` | 识别符合模式的候选项 | haiku | `.claude/gather/refactor-<ts>/` |
| `atlas:planner` | 制定重构计划 | inherit | `.claude/plan/refactor-<ts>/` |
| `atlas:atlas-executor` | 执行重构 | 用户选择 | 直接修改文件 |

### 1.2 工具说明

| 工具 | 用途 |
|------|------|
| `AskUserQuestion` | 确认选项 |
| `Task` | 调用 subagent |
| `tsc` / `npm test` | 验证结果 |

### 1.3 信息传递链

```
gatherer → .claude/gather/refactor-<ts>/context.json
    ↓
planner → .claude/plan/refactor-<ts>/plan.json
    ↓
executor → 直接重构（无需重新扫描）
```

---

## 二、编排计划

### 2.1 强制流程

```
模式解析 → 确认选项 → 候选识别 → 规划 → 执行/预览 → 测试 → 报告
```

### 2.2 模式行为定义

| 步骤 | 默认值 | --dry-run | --interactive | 可选值 |
|------|--------|-----------|---------------|--------|
| 候选识别 | 是 | 是 | 是 | 是 / 否 |
| 规划器 | 询问 | atlas:planner | 询问 | atlas:planner / 内置 Plan |
| Executor 模型 | 询问 | - | 询问 | haiku / sonnet / opus |
| 测试节点 | 询问 | - | 询问 | 每个候选后 / 统一测试 / 不测试 |
| 测试模式 | 询问 | - | 询问 | 编译测试 / 单元测试 / 编译+单元 |

### 2.3 支持的重构模式

| 模式 | 说明 | 识别条件 |
|------|------|---------|
| `extract-method` | 提取长函数 | 函数体 >50 行 |
| `extract-component` | 提取大组件 | JSX >100 行 |
| `consolidate-duplicate` | 合并重复代码 | 相似度 >80% |
| `modernize-js` | JS 现代化 | var/callback |
| `add-types` | 添加 TS 类型 | any/缺失类型 |
| `rename-convention` | 统一命名 | 命名不一致 |
| `simplify-conditions` | 简化条件 | if-else >3 层 |
| `remove-dead-code` | 移除死代码 | 未使用的导出 |

### 2.4 执行步骤

**Step 1: 一次性确认所有选项**（开始时全部询问）

使用 `AskUserQuestion` 一次性收集所有配置：

```
问题 1: 执行模式
- 执行重构: 识别候选并执行重构
- 预览模式 (dry-run): 只识别候选，不执行

问题 2: 是否创建检查点（执行重构时）
- 创建（推荐）: 失败可回滚
- 跳过: 不创建

问题 3: 规划器选择
- atlas:planner（推荐）: 信任 gatherer 输出
- 内置 Plan: 会自行探索

问题 4: Executor 模型（执行重构时）
- sonnet（推荐）: 平衡性能与质量
- haiku: 快速简单重构
- opus: 复杂质量要求高

问题 5: 测试节点
- 统一测试（推荐）: 全部完成后测试
- 每个候选后: 每个重构完成后立即测试
- 不测试: 跳过

问题 6: 测试模式
- 编译测试（推荐）: tsc --noEmit
- 单元测试: npm test
- 编译+单元: 完整验证
```

**Step 2: 创建执行环境**（执行重构时）

```bash
# 创建状态目录
mkdir -p .claude/refactor/.state

# 初始化状态文件
echo '{
  "executionId": "refactor-<timestamp>",
  "timestamp": "<ISO-8601-timestamp>",
  "task": "<重构模式>",
  "pattern": "<pattern>",
  "scope": "<scope>",
  "status": "initializing",
  "currentStage": "initialization",
  "mode": "<execute/dry-run>",
  "config": {
    "planner": "<atlas:planner/Plan>",
    "executorModel": "<haiku/sonnet/opus>",
    "testNode": "<unified/per-candidate/none>",
    "testMode": "<compile/unit/both>"
  },
  "checkpoint": {
    "stashId": "atlas-checkpoint-refactor-<timestamp>",
    "created": false
  },
  "candidates": [],
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
}' > .claude/refactor/.state/refactor-<timestamp>.json

# 创建检查点（如果选择创建）
git stash push -m "atlas-checkpoint-refactor-<timestamp>"

# 更新状态
更新 .state/refactor-<timestamp>.json: {
  checkpoint.created: true,
  currentStage: "checkpoint_created"
}
```

**Step 3: 候选识别**
```
Task(subagent_type="atlas:information-gatherer", model="haiku")
prompt: |
  任务 ID: refactor-<timestamp>
  重构模式: [pattern]
  范围: [scope]
  输出目录: .claude/gather/refactor-<timestamp>/
```

完成后更新状态:
.state/refactor-<timestamp>.json: currentStage="candidates_identified"
```

**Step 4: 重构规划**（支持循环修改）

**重要：使用统一的 refactor-<timestamp> ID，所有文件在同一目录操作**

```
┌─────────────────────────────────────────┐
│ 4.1 执行规划（首次）                     │
│ Task(subagent_type="<用户选择的规划器>") │
│ 输出: .claude/plan/refactor-<ts>/plan.json│
└─────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│ 4.2 展示重构计划                         │
│ - 识别的候选项（文件:行号）              │
│ - 重构策略和步骤                         │
│ - 风险评估                               │
└─────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│ 4.3 用户确认                             │
│ AskUserQuestion:                        │
│ - 继续执行（执行重构模式）               │
│ - 修改计划: 用户提出调整意见            │
│ - 完成预览: 仅输出报告（预览模式）       │
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
.state/refactor-<timestamp>.json: {
  currentStage: "planning_approved",
  planVersion: "final" 或 "v3",
  candidates: [
    {"id": 1, "status": "pending", "file": "...", "description": "..."},
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
.claude/plan/refactor-<timestamp>/
├── plan.json (或 plan.final.json)  # 最终计划
├── plan.v1.json  # 可选: 历史版本
└── plan.v2.json  # 可选: 历史版本
```

**Step 5: 执行重构**（执行重构模式，支持循环）

```
┌─────────────────────────────────────────┐
│ 5.1 并发/串行执行重构                    │
│ Task(subagent_type="atlas:atlas-executor")│
│ model=<用户选择的模型>                   │
│ 根据测试节点决定并发/串行                │
└─────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│ 5.2 收集重构结果                         │
│ - 成功的候选项                           │
│ - 失败的候选项及原因                     │
└─────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│ 5.3 展示结果                             │
│ - 成功: X 个候选                         │
│ - 失败: Y 个候选                         │
│ - 修改文件列表                           │
└─────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│ 5.4 用户决策                             │
│ AskUserQuestion:                        │
│ - 继续验证（推荐，如果全部成功）         │
│ - 修复失败: 重新重构失败的候选          │
│ - 调整结果: 用户提出修改意见            │
│ - 回滚变更                               │
└─────────────────────────────────────────┘
         ↓
    [用户选择修复/调整]
         ↓
┌─────────────────────────────────────────┐
│ 5.5 重新执行                             │
│ 返回 5.1（仅针对失败/需调整的候选）     │
└─────────────────────────────────────────┘

完成后更新状态:
.state/refactor-<timestamp>.json: {
  currentStage: "refactoring_completed",
  candidates: [更新每个候选的 status],
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
| 每个候选后 | 每个重构完成后立即测试 |
| 统一测试 | 全部完成后测试一次 |
| 不测试 | 跳过 |

| 测试模式 | 命令 |
|---------|------|
| 编译测试 | `tsc --noEmit` |
| 单元测试 | `npm test` |
| 编译+单元 | `tsc --noEmit && npm test` |

```bash
# 更新状态
更新 .state/refactor-<timestamp>.json: currentStage="testing_completed"
```

**Step 7: 清理和报告**

```bash
# 更新最终状态
更新 .state/refactor-<timestamp>.json: {
  status: "completed",
  currentStage: "finished",
  completedAt: "<ISO-8601-timestamp>",
  checkpoint: {
    stashId: "...",
    created: true,
    cleaned: true  # 如果已清理检查点
  }
}

# 输出报告（见第四章）
```

---

## 三、细节要点

### 3.1 任务 ID 管理原则

**统一任务 ID**:
- 格式: `refactor-<timestamp>` (例如: `refactor-20240115-153000`)
- 从 Step 1 到 Step 7 使用**同一个** ID
- 所有相关文件使用此 ID 关联

**目录结构**:
```
.claude/
├── gather/refactor-<timestamp>/    # gatherer 输出（不变）
│   └── context.json
├── plan/refactor-<timestamp>/      # planner 输出（版本化）
│   ├── plan.json (或 plan.final.json)
│   ├── plan.v1.json (可选)
│   └── plan.v2.json (可选)
├── refactor/.state/                # 状态文件
│   └── refactor-<timestamp>.json
```

**版本化策略**:
- **简单场景**: 直接覆盖 `plan.json`
- **复杂场景**: 创建版本文件 `plan.v2.json`, `plan.v3.json` 等
- 状态文件记录 `planVersion` 字段

### 3.2 主进程职责

**允许**: AskUserQuestion / Task 调用 / 读取 agent 输出 / 运行验证命令

**禁止**: Read/Grep/Glob 读代码 / Edit/Write 修改文件 / 直接分析代码

### 3.3 候选识别输出

gatherer 的 context.json 必须包含：
```json
{
  "candidates": [
    {
      "id": 1,
      "file": "src/services/UserService.ts",
      "symbol": "processOrder",
      "line": 45,
      "reason": "函数体 89 行",
      "codeSnippet": "..."
    }
  ]
}
```

### 3.4 模式约束

- 只执行指定模式的重构
- 不"顺便"做其他优化
- 保持现有代码风格

---

## 四、示例

### 示例 1: 预览模式

```
用户: /refactor extract-method --dry-run

1. 模式解析: extract-method
2. Gatherer: 识别长函数候选项
3. Planner: 生成重构计划
4. 输出预览:
   📋 重构预览
   模式: extract-method | 候选数: 5
   变更预览: processOrder → 拆分为 3 个函数
```

### 示例 2: 交互模式

```
用户: /refactor add-types --scope src/services --interactive

1. 确认选项: atlas:planner + sonnet + 编译测试
2. Gatherer: 识别缺少类型的位置
3. Planner: 生成计划
4. 逐个确认执行
5. 测试: tsc --noEmit ✅
```

### 示例 3: 直接执行

```
用户: /refactor modernize-js --scope src

1. 确认选项: atlas:planner + sonnet + 统一测试 + 编译+单元
2. Gatherer: 识别旧语法
3. Planner: 生成计划
4. Executor: 并行执行
5. 测试: tsc --noEmit && npm test ✅
6. 报告
```

---

## 五、核心约束

### 必须做

- ✅ **Step 1**: 开始时一次性确认所有配置（模式、规划器、模型、测试选项）
- ✅ **Step 2**: 创建状态目录 `.claude/refactor/.state/` 和状态文件（执行重构时）
- ✅ **Step 2**: 在每个关键步骤完成后更新状态文件的 `currentStage` 字段
- ✅ **Step 3**: 使用 `Task(subagent_type="atlas:information-gatherer", model="haiku")`
- ✅ **Step 4**: 使用用户选择的规划器，输出到 `.claude/plan/refactor-<ts>/`
- ✅ **Step 4.2-4.4**: 展示重构计划给用户，支持循环修改直到用户确认
- ✅ **Step 5**: 从 plan.json 提取修改点嵌入 executor prompt（执行重构时）
- ✅ **Step 5.2-5.5**: 展示重构结果，支持用户修复失败或调整结果
- ✅ **Step 6**: 根据 Step 1 的选择执行验证测试
- ✅ **Step 7**: 更新最终状态并输出报告

### 禁止做

- ❌ 主进程直接读取代码（除了 agent 输出的 JSON 文件）
- ❌ 主进程直接修改文件（所有修改必须通过 executor）
- ❌ 跳过候选识别直接规划
- ❌ 跳过规划直接执行
- ❌ executor 重新扫描文件（应使用 plan.json 的修改点）
- ❌ 在 Step 1 之后还有其他的 AskUserQuestion（除了 Step 4.3 和 5.4 的确认循环）
- ❌ 忘记更新状态文件的 `currentStage`（执行重构时）
- ❌ 在用户未确认的情况下继续执行下一步
- ❌ "顺便"做其他优化（只执行指定模式的重构）
