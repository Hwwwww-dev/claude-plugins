---
description: 问题诊断与修复建议。分析问题根因，提供修复方案，可选执行修复。
argument-hint: <问题描述> [--quick] [--scope path] [--fix] [--auto]
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

| 步骤 | 快速模式 | 仅诊断 | 执行修复（交互） | 自动模式 |
|------|---------|--------|------------------|----------|
| 执行策略 | auto | 不执行 | 手动确认 | auto |
| 信息收集 | **跳过** | 询问 | 询问 | 是 |
| 诊断深度 | **跳过** | 询问 | 询问 | 快速 |
| 检查点 | **跳过** | - | 询问 | 创建 |
| 规划器 | **跳过（主进程直接定位）** | 询问 | 询问 | atlas:planner |
| Executor 模型 | **haiku** | - | 询问 | sonnet |
| 测试节点 | **不测试** | - | 询问 | 修复后 |
| 测试模式 | - | - | 询问 | 编译测试 |
| 失败处理 | 询问用户 | - | 询问用户 | 询问用户 |
| 状态文件 | **创建** | - | 创建 | 创建 |

### 2.3 执行步骤

**Step 1: 分阶段确认选项**

**第一个 AskUserQuestion: 执行模式选择**

```
问题: 执行模式
- 快速模式: 跳过信息收集，直接修复（适合明确的单点 bug，~3分钟）
- 仅诊断（推荐）: 只分析问题，输出修复方案
- 执行修复: 诊断后自动执行修复
- 自动模式: 使用推荐选项，减少交互
```

**第二个 AskUserQuestion: 诊断配置**

```
问题 1: 信息收集
- 是（推荐）: 使用 gatherer 收集问题相关信息
- 否: 跳过信息收集（适用于问题范围明确的情况）

问题 2: 规划器选择
- atlas:planner（推荐）: 信任 gatherer 输出，最小化扫描
- 内置 Plan: 会自行探索验证

问题 3: 诊断深度
- 快速（推荐）: 聚焦问题本身
- 深度: 分析影响范围和潜在连锁问题
- 完整: 全面诊断（包括代码质量、安全等）
```

**自动模式行为**（跳过第二个 AskUserQuestion）：
- 信息收集: 是
- 规划器: atlas:planner
- 诊断深度: 快速
- 失败处理: 询问用户

**快速模式行为**（跳过第二、三个 AskUserQuestion）：
- 信息收集: 跳过
- 检查点: 跳过
- 规划器: 跳过（主进程直接定位）
- Executor 模型: haiku
- 测试: 不测试
- 状态文件: 创建

**第三个 AskUserQuestion: 修复和测试配置**（仅执行修复模式和自动模式）

如果用户选择了**执行修复**或**自动模式**，询问修复和测试配置：

```
问题 1: 是否创建检查点
- 创建（推荐）: 失败可回滚
- 跳过: 不创建

问题 2: Executor 模型
- sonnet（推荐）: 平衡性能与质量
- haiku: 快速简单修复
- opus: 复杂质量要求高

问题 3: 测试节点
- 修复后（推荐）: 修复完成后测试
- 不测试: 跳过验证

问题 4: 测试模式
- 编译测试（推荐）: tsc --noEmit
- 单元测试: npm test
- 编译+单元: 完整验证
```

**注意**:
- 仅诊断模式跳过第三个 AskUserQuestion
- 自动模式和执行修复模式都需要第三个 AskUserQuestion
- **快速模式跳过所有询问，直接进入执行**

---

### 2.4 快速模式流程（--quick）

**适用场景**：
- 修复 1-3 个文件中的明确 bug
- 用户已经定位到问题位置
- 简单的语法错误、类型错误、拼写错误

**流程**：
```
确认模式 → 主进程快速定位 → 直接修复 → 简化报告
```

**Step Q1: 确认快速模式**
```
AskUserQuestion:
问题: 执行模式
- 快速模式 ✓
```

**Step Q2: 创建状态文件**
```bash
# 创建状态目录
mkdir -p .claude/orchestrate/.state

# 初始化状态文件
echo '{
  "executionId": "bugfix-<timestamp>",
  "timestamp": "<ISO-8601>",
  "task": "<用户任务>",
  "status": "in_progress",
  "currentStage": "quick_bugfix",
  "config": { "mode": "quick", "executorModel": "haiku" }
}' > .claude/orchestrate/.state/bugfix-<timestamp>.json
```

**Step Q3: 主进程快速定位**
```
主进程允许使用 Grep/Glob/Read 快速定位目标文件（≤5 次工具调用）
分析问题根因
直接构建 executor prompt（不调用 planner agent）
```

**Step Q4: 直接修复**
```
Task(subagent_type="atlas:atlas-executor", model="haiku")
prompt: |
  子任务 #1
  描述: [问题修复]
  文件: [主进程定位的文件]
  问题: [根因分析]
  修改点: [主进程分析的修改点]
  注意: 快速模式，只做明确提及的修复
```

**Step Q5: 简化报告**
```markdown
# 快速修复完成

**执行 ID**: bugfix-<timestamp>
**状态文件**: .claude/orchestrate/.state/bugfix-<timestamp>.json
**问题**: [描述]
**根因**: [定位]
**修改文件**: [文件列表]
**状态**: ✅ 成功 / ❌ 失败

[如果失败] 建议: 使用自动模式重新执行 `/bugfix <问题> --fix`
```

**快速模式风险提示**：
- 跳过深度诊断，可能遗漏关联问题
- 跳过检查点，无法回滚
- 如果 executor 失败，建议用户切换到自动模式

---

### 2.5 标准模式执行步骤

**Step 2: 创建执行环境**（仅执行修复和自动模式时）

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
  "mode": "<diagnose-only/execute-fix/auto>",
  "config": {
    "gatherInfo": "<yes/no>",
    "planner": "<atlas:planner/Plan>",
    "diagnosisDepth": "<quick/deep/full>",
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
  },
  "todos": [
    {
      "id": 1,
      "description": "子任务描述",
      "subtaskId": 1,
      "status": "pending",
      "completedAt": null,
      "error": null
    }
  ]
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

1. **4.1 执行规划（首次）**: `Task(subagent_type="<用户选择的规划器>")` → 输出 `.claude/plan/bugfix-<ts>/plan.json`
2. **4.2 展示诊断结果**: 根因分析（文件:行号）、问题类型和复杂度、修复方案（策略、步骤、风险）

#### Step 4.2.5: 规划完整性验证

读取诊断计划的 `completeness` 字段：

1. 验证所有问题根因都有对应修复方案
2. 验证修复方案的修改点完整

**输出**:
- 通过: `✅ 诊断规划验证通过 (覆盖: 100%)`
- 未通过: `⚠️ 部分问题未覆盖`

3. **4.3 用户确认**: AskUserQuestion → 继续执行（执行修复模式）/ 修改方案 / 完成诊断（诊断模式）
4. **4.4 重新规划（版本化）**（若用户选择修改）:
   - 使用相同规划器，传入修改意见
   - 输出策略: 简单场景覆盖 plan.json / 复杂场景创建 plan.v2.json 等
   - 返回 4.2 循环直到用户确认

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

1. **5.1 执行修复**: `Task(subagent_type="atlas:atlas-executor", model=<用户选择的模型>)`
2. **5.2 展示修复结果**: 修改的文件和位置、修复状态（成功/失败）

#### Step 5.2.5: 执行完成度验证

验证修复执行完成度：

1. 检查所有修复任务是否完成
2. 更新 todos 状态

**输出**:
- 全部完成: `✅ 修复执行完成 (100%)`
- 部分完成: `⚠️ 部分修复未完成`，询问是否重试

3. **5.3 用户决策**: AskUserQuestion → 继续验证（推荐）/ 重新修复 / 回滚变更
4. **5.4 重新执行**（若用户选择重新修复）: 返回 5.1

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

### 示例 1: 快速修复（~3分钟）- 明确的单点 bug

```
用户: /bugfix Login.tsx 第45行 onClick 未绑定 --quick

1. 选择快速模式 → 跳过所有后续询问
2. 主进程定位: Grep "onClick" src/components/Login.tsx
   → 发现第45行: <button onClick={handleLogin}>
   → Read 上下文: handleLogin 定义在第12行，但未绑定 this
3. 根因确认: 类组件中 handleLogin 未在 constructor 中绑定
4. Executor(haiku): 在 constructor 添加 this.handleLogin = this.handleLogin.bind(this)
5. 修复完成: src/components/Login.tsx (1处修改)
6. 输出: ✅ 快速修复成功 | 建议: 考虑使用箭头函数避免绑定问题
```

### 示例 2: 自动模式 - 需要诊断的 bug

```
用户: /bugfix 用户列表接口返回 undefined --auto

1. 选择自动模式 → 使用推荐配置 (gatherer + atlas:planner + 快速诊断)
2. 创建检查点: git stash push -m "atlas-checkpoint-bugfix-20240115-143000"
3. Gatherer 收集: 搜索 "用户列表" 相关代码 → 定位 api/users.ts, hooks/useUsers.ts
4. Planner 诊断: 根因在 api/users.ts:28 - response.data.users 应为 response.data.list
   → 复杂度: simple | 影响: useUsers hook 的所有调用方
5. 用户确认方案 ✓
6. Executor(sonnet): 修复 api/users.ts 第28行字段映射
7. 测试: tsc --noEmit ✓ | 输出报告: 1文件修改，根因已修复
```

### 示例 3: 交互模式 - 复杂 bug 修复

```
用户: /bugfix 订单提交后状态不更新 --fix

1. 选择执行修复 → 配置: 深度诊断 + opus + 编译+单元测试
2. 创建检查点 + Gatherer 收集: 订单相关文件 (5个) + 状态管理 (3个)
3. Planner 深度诊断:
   → 根因1: store/order.ts:45 - 异步 action 未 await
   → 根因2: api/order.ts:67 - 缺少错误处理导致静默失败
   → 复杂度: moderate | 关联影响: 购物车、支付流程
4. 用户审查方案 → 要求: "保留原有错误处理逻辑"
5. Planner 重新规划 (v2): 调整修复策略，保留 try-catch 结构
6. 用户确认 ✓ → Executor(opus): 修复 2 个文件
7. 测试: tsc ✓ + npm test ✓ (订单相关用例全部通过)
8. 报告: 2文件修改 | 迭代: 规划2次，执行1次 | 检查点可回滚
```

---

## 五、核心约束

### 标准模式必须做

- ✅ **Step 1**: 分阶段确认配置（第一个询问执行模式，第二个询问诊断配置，第三个询问修复和测试配置）
- ✅ **Step 2**: 创建状态目录 `.claude/bugfix/.state/` 和状态文件（执行修复模式和自动模式）
- ✅ **Step 2**: 在每个关键步骤完成后更新状态文件的 `currentStage` 字段
- ✅ **Step 3**: 使用 `Task(subagent_type="atlas:information-gatherer", model="haiku")`
- ✅ **Step 4**: 使用用户选择的规划器，输出到 `.claude/plan/bugfix-<ts>/`
- ✅ **Step 4.2-4.4**: 展示诊断给用户，支持循环修改直到用户确认
- ✅ **Step 5**: 从 plan.json 提取修改点嵌入 executor prompt（执行修复模式和自动模式）
- ✅ **Step 5.2-5.4**: 展示修复结果，支持用户重新修复或调整
- ✅ **Step 6**: 根据 Step 1 的选择执行验证测试
- ✅ **Step 7**: 更新最终状态并输出报告
- ✅ **Todos**: 必须使用 TodoWrite 工具生成详细的任务清单，包含每个诊断/修复任务的描述和状态，确保任务执行过程可追踪

### 快速模式必须做

- ✅ **Step Q1**: 确认用户选择快速模式
- ✅ **Step Q2**: 创建状态文件 `.claude/orchestrate/.state/bugfix-<timestamp>.json`
- ✅ **Step Q3**: 主进程快速定位目标文件（≤5 次工具调用）
- ✅ **Step Q4**: 使用 `Task(subagent_type="atlas:atlas-executor", model="haiku")`
- ✅ **Step Q5**: 输出简化报告（包含执行 ID 和状态文件路径）
- ✅ 失败时建议用户切换到自动模式

### 快速模式允许做

- ✅ 主进程使用 Grep/Glob/Read 快速定位文件（≤5 次）
- ✅ 主进程直接分析根因（不调用 planner）
- ✅ 跳过信息收集、检查点

### 禁止做

- ❌ 主进程直接修改文件（所有修改必须通过 executor）
- ❌ 标准模式跳过信息收集直接诊断（除非快速模式）
- ❌ 标准模式跳过规划直接执行修复
- ❌ executor 重新扫描文件（应使用 plan.json 或主进程提供的修改点）
- ❌ 在 Step 1 之后还有其他的 AskUserQuestion（除了 Step 4.3 和 5.3 的确认循环）
- ❌ 标准模式忘记更新状态文件的 `currentStage`
- ❌ 在用户未确认的情况下继续执行下一步
- ❌ 快速模式用于复杂问题（>3 个文件或涉及依赖分析）


** 在本命令中，做任何事情都需要在 Subagent 中完成，主对话只负责调用 Subagent 和输出报告。不可在主对话中直接执行任何操作。（读取流程中的文档除外）**