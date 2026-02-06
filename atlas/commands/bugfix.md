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
| `atlas:task-planner` | 制定修复方案 | inherit | `.claude/plan/bugfix-<ts>/` |
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
task-planner → .claude/plan/bugfix-<ts>/plan.json
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
| 规划器 | **跳过（主进程直接定位）** | 询问 | 询问 | atlas:task-planner |
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
- atlas:task-planner（推荐）: 信任 gatherer 输出，最小化扫描
- 内置 Plan: 会自行探索验证

问题 3: 诊断深度
- 快速（推荐）: 聚焦问题本身
- 深度: 分析影响范围和潜在连锁问题
- 完整: 全面诊断（包括代码质量、安全等）
```

**默认行为**: 见 2.2 表。若用户显式传入 `--quick`，视为已选快速模式，直接进入 2.4。

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
- 仅“执行修复/自动模式”询问修复与测试配置；仅诊断跳过
- quick 跳过所有询问（除非用户未指定 `--quick` 且在 Step 1 手动选择）

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

**入口**: 命令带 `--quick`；或在 Step 1 选择“快速模式”。

**Step Q2: 创建状态文件**
```bash
mkdir -p .claude/bugfix/.state
echo '{
  "executionId": "bugfix-<timestamp>",
  "timestamp": "<ISO-8601>",
  "task": "<用户任务>",
  "status": "in_progress",
  "currentStage": "quick_bugfix",
  "config": {"mode": "quick", "executorModel": "haiku"}
}' > .claude/bugfix/.state/bugfix-<timestamp>.json
```

**Step Q3: 主进程快速定位**
```
主进程允许使用 Grep/Glob/Read 快速定位目标文件（≤5 次工具调用）
分析问题根因
直接构建 executor prompt（不调用 task-planner agent）
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
**状态文件**: .claude/bugfix/.state/bugfix-<timestamp>.json
**问题**: [描述]
**根因**: [定位]
**修改文件**: [文件列表]
**状态**: ✅ 成功 / ❌ 失败

[如果失败] 建议: 使用自动模式重新执行 `/bugfix <问题> --fix`
```

**快速模式风险提示**：
- 跳过深度诊断/检查点：可能遗漏关联问题且无法回滚
- 失败建议改用自动模式重新执行

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
  "config": {"gatherInfo": "<yes/no>", "task-planner": "<atlas:task-planner/Plan>", "diagnosisDepth": "<quick/deep/full>", "executorModel": "<haiku/sonnet/opus>", "testNode": "<after-fix/none>", "testMode": "<compile/unit/both>"},
  "checkpoint": {"stashId": "atlas-checkpoint-bugfix-<timestamp>", "created": false},
  "diagnosis": null,
  "fixApplied": false,
  "iterations": {"planning": 0, "execution": 0},
  "todos": [
    {"id": 1, "description": "子任务描述", "subtaskId": 1, "status": "pending", "completedAt": null, "error": null}
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
完成后更新状态: `.state/bugfix-<timestamp>.json: currentStage="gathering_completed"`

**Step 4: 根因分析与修复规划**（支持循环修改）

**重要：使用统一的 bugfix-<timestamp> ID，所有文件在同一目录操作**

1. **4.1 执行规划（首次）**: `Task(subagent_type="<用户选择的规划器>")` → 输出 `.claude/plan/bugfix-<ts>/plan.json`
2. **4.2 展示诊断结果**: 根因分析（文件:行号）、问题类型和复杂度、修复方案（策略、步骤、风险）

#### Step 4.2.5: 规划完整性验证

读取 `plan.json.completeness`：
- 要求: 根因→修复方案全覆盖，修改点字段完整（覆盖率应为 100%）
- 未通过: 列出未覆盖项 → 询问是否返回重新规划（推荐）

3. **4.3 用户确认**: AskUserQuestion → 继续执行（执行修复模式）/ 修改方案 / 完成诊断（诊断模式）
4. **4.4 重新规划（版本化）**（若用户选择修改）:
   - 使用相同规划器，传入修改意见
   - 输出策略: 简单覆盖 `plan.json`；复杂生成 `plan.v2.json`/`plan.v3.json`…
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

**Step 5: 执行修复**（仅执行修复模式，支持循环）

1. **5.1 执行修复**: `Task(subagent_type="atlas:atlas-executor", model=<用户选择的模型>)`
2. **5.2 展示修复结果**: 修改的文件和位置、修复状态（成功/失败）

#### Step 5.2.5: 执行完成度验证

对比计划与 executor 结果（含 `completionStatus`），输出完成率与未完成项；若未完成则询问重试/回滚/结束保存进度。

3. **5.3 用户决策**: AskUserQuestion → 继续验证（推荐）/ 重新修复 / 回滚变更
4. **5.4 重新执行**（若用户选择重新修复）: 返回 5.1

完成后更新状态:
.state/bugfix-<timestamp>.json: {
  currentStage: "fix_applied",
  fixApplied: true,
  iterations.execution: <循环次数>
}

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

**统一任务 ID**: `bugfix-<timestamp>`（如 `bugfix-20240115-143000`），Step 1-7 全程一致。

**目录结构**:
```
.claude/
├── gather/bugfix-<timestamp>/     # gatherer 输出（不变）
│   └── context.json
├── plan/bugfix-<timestamp>/        # task-planner 输出（版本化）
│   ├── plan.json (或 plan.final.json)
│   ├── plan.v1.json (可选)
│   └── plan.v2.json (可选)
├── bugfix/.state/                  # 状态文件
│   └── bugfix-<timestamp>.json
```

**版本化策略**:
- 简单覆盖 `plan.json`；复杂生成 `plan.v2.json`/`plan.v3.json`…；状态文件用 `planVersion` 指向最终版本。

### 3.2 主进程职责

**允许**: AskUserQuestion、Task、读取 agent 输出、Git 操作。  
**禁止**: 主进程读/改业务代码或自行做深度诊断（交给 subagent）。

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

1. 选择自动模式 → 使用推荐配置 (gatherer + atlas:task-planner + 快速诊断)
2. 创建检查点: git stash push -m "atlas-checkpoint-bugfix-20240115-143000"
3. Gatherer 收集: 搜索 "用户列表" 相关代码 → 定位 api/users.ts, hooks/useUsers.ts
4. Planner 诊断: 根因在 api/users.ts:28 - response.data.users 应为 response.data.list
   → 复杂度: simple | 影响: useUsers hook 的所有调用方
5. 用户确认方案 ✓
6. Executor(sonnet): 修复 api/users.ts 第28行字段映射
7. 测试: tsc --noEmit ✓ | 输出报告: 1文件修改，根因已修复
```

---

## 五、核心约束

### 标准模式必须做

- ✅ Step 1 分阶段确认（模式→诊断→修复/测试）
- ✅ 执行修复/自动模式创建并持续更新 `.claude/bugfix/.state/bugfix-<ts>.json`（`currentStage`）
- ✅ gather → plan（含 `completeness`）→ fix（含 `completionStatus`）→ test → report
- ✅ 使用 TodoWrite 跟踪诊断/修复任务

### 快速模式必须做

- ✅ 创建状态文件；主进程≤5次定位；executor(haiku) 修复；输出简报

### 快速模式允许做

- ✅ 主进程使用 Grep/Glob/Read 快速定位文件（≤5 次）
- ✅ 主进程直接分析根因（不调用 task-planner）
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
  
**原则**: 主进程只编排/确认/汇总；诊断与修改由 subagent 完成（读取流程产物除外）。
