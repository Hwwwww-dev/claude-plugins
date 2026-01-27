---
description: 任务协调与并发执行引擎。处理复杂多步骤任务、批量操作、项目级变更。支持回滚和断点续传。
argument-hint: <任务描述> [--quick] [--parallel|--sequential] [--dry-run] [--no-gather] [--auto-rollback] [--resume <id>]
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
| `TaskCreate` | 创建子任务（Task 系统） | 主进程直接调用 |
| `TaskUpdate` | 更新任务状态/依赖（Task 系统） | 主进程直接调用 |
| `TaskList` | 查看所有任务进度（Task 系统） | 主进程直接调用 |
| `TaskGet` | 获取任务详情（Task 系统） | 主进程直接调用 |

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

**禁止**: 主进程直接读/改代码；标准流程不允许跳步（除非 quick 或显式参数允许）。

### 2.2 模式行为定义

| 步骤 | 快速模式 | 自动模式 | 交互模式 | dry-run |
|------|---------|---------|---------|---------|
| 执行策略 | auto | auto | 询问用户 | auto |
| **进度管理** | **无** | **Task 系统** | 询问用户 | 文件状态 |
| 信息收集 | **跳过** | 是（除非 repowiki 充足） | 询问用户 | 是 |
| 检查点 | **跳过** | 创建 | 询问用户 | 跳过 |
| 规划器选择 | **跳过（主进程直接规划）** | atlas:planner | 询问用户 | atlas:planner |
| Executor 模型 | **haiku** | sonnet | 询问用户 | - |
| 测试节点 | **不测试** | 统一测试 | 询问用户 | - |
| 测试模式 | - | 编译测试 | 询问用户 | - |
| 失败处理 | 询问用户 | 询问用户 | 询问用户 | - |

#### 进度管理方式说明

| 方式 | 工具 | 特点 | 适用场景 |
|------|------|------|---------|
| **Task 系统** | TaskCreate/TaskList/TaskUpdate/TaskGet | 依赖追踪 `blockedBy/blocks`、可视化 `/todos`、实时状态 | 单会话、需要依赖管理 |
| **文件状态** | `.claude/orchestrate/.state/<task-id>.json` | 持久化、断点续传 `--resume <id>` | 跨会话、长时间任务 |
| **无** | - | 不追踪进度 | 快速模式简单任务 |

### 2.3 执行步骤

**Step 1: 分阶段确认选项**

**第一个 AskUserQuestion: 执行模式选择**

```
问题: 执行模式
- 快速模式: 跳过信息收集/规划，直接执行（适合 1-3 文件的明确小改）
- 自动模式（推荐）: 使用推荐选项，减少交互
- 交互模式: 每个关键步骤都需要确认
- dry-run: 只规划不执行
```

**第二个 AskUserQuestion: 基础配置（仅交互模式和 dry-run）**

如果用户选择了**交互模式**或 **dry-run**，询问基础配置：

```
问题 1: 进度管理
- Task 系统（推荐）: 使用 Claude Code 任务系统，依赖追踪，`/todos` 可视化
- 文件状态: 持久化到 .claude/orchestrate/.state/，支持 `--resume` 断点续传

问题 2: 信息收集
- 是（推荐）: 使用 gatherer 收集项目信息
- 否: 跳过信息收集（适用于 repowiki 已充足的情况）

问题 3: 检查点
- 创建（推荐）: 创建 git stash 检查点，支持回滚
- 跳过: 不创建检查点（dry-run 默认跳过）

问题 4: 规划器选择
- atlas:planner（推荐）: 信任 gatherer 输出，最小化扫描
- 内置 Plan: 会自行探索验证

问题 5: Executor 模型
- sonnet（推荐）: 平衡性能与成本
- haiku: 快速简单任务
- opus: 复杂质量要求高
```

**默认行为**: 见 2.2 表（auto/interactive/dry-run/quick）。若用户显式传入 `--quick`，视为已选快速模式，直接进入 2.4。

**自动模式行为**（跳过第二个 AskUserQuestion）：
- 进度管理: Task 系统
- 信息收集: 是（除非 repowiki 充足）
- 检查点: 创建
- 规划器: atlas:planner
- Executor 模型: sonnet
- 失败处理: 询问用户

**快速模式行为**（跳过第二、三个 AskUserQuestion）：
- 进度管理: 无（任务太简单，不需要追踪）
- 信息收集: 跳过
- 检查点: 跳过
- 规划器: 跳过（主进程直接规划）
- Executor 模型: haiku
- 测试: 不测试

**第三个 AskUserQuestion: 测试配置**

询问测试配置：

```
问题 1: 测试节点
- 统一测试（推荐）: 全部执行完成后统一验证
- 每个子任务后: 每个 executor 完成后立即测试
- 不测试: 跳过验证

问题 2: 测试模式
- 编译测试（推荐）: tsc --noEmit 确保语法正确
- 单元测试: npm test 确保功能正常
- 编译+单元: 完整验证
```

**注意**:
- 仅 auto/interactive 询问测试配置；dry-run/quick 跳过
- quick 会跳过所有确认步骤（除非用户未指定 `--quick` 且在 Step 1 手动选择）

---

### 2.4 快速模式流程（--quick）

**适用**: 1-3 文件、目标明确、无需依赖分析/规划循环。

**流程**：
```
确认模式 → 主进程快速定位 → 直接执行 → 报告
```

**入口**: 命令带 `--quick`；或在 Step 1 选择“快速模式”。

**Step Q2: 创建状态文件**
```bash
mkdir -p .claude/orchestrate/.state
echo '{
  "executionId": "<task-id>",
  "timestamp": "<ISO-8601>",
  "task": "<用户任务>",
  "status": "in_progress",
  "currentStage": "quick_mode",
  "config": {"mode": "quick", "executorModel": "haiku"},
  "subtasks": [],
  "progress": {"total": 1, "completed": 0, "failed": 0, "pending": 1}
}' > .claude/orchestrate/.state/<task-id>.json
```

**Step Q3: 主进程快速定位**
```
主进程允许使用 Grep/Glob/Read 快速定位目标文件（≤5 次工具调用）
生成最小修改计划（不调用 planner），直接构建 executor prompt
```

**Step Q3: 直接执行**
```
Task(subagent_type="atlas:atlas-executor", model="haiku")
prompt: |
  子任务 #1
  描述: [用户任务]
  文件: [主进程定位的文件]
  修改点: [主进程分析的修改点]
  注意: 快速模式，只做明确提及的修改
```

**Step Q4: 更新状态并报告**
```bash
更新 .state/<task-id>.json: {
  status: "completed",
  currentStage: "finished",
  completedAt: "<ISO-8601>",
  progress: { total: 1, completed: 1, failed: 0, pending: 0 }
}
```

```markdown
# 快速执行完成

**任务**: [描述]
**修改文件**: [文件列表]
**状态**: ✅ 成功 / ❌ 失败

[如果失败] 建议: 使用自动模式重新执行 `/orchestrate <任务>`
```

**⚠️ 快速模式风险提示**：
- 跳过依赖分析/检查点，可能遗漏影响点且无法回滚
- 失败建议改用自动模式重新执行

---

### 2.5 标准模式执行步骤

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
  "config": {"mode": "<auto/interactive/dry-run>", "planner": "<atlas:planner/Plan>", "executorModel": "<haiku/sonnet/opus>", "testNode": "<unified/per-task/none>", "testMode": "<compile/unit/both>"},
  "checkpoint": {"stashId": "atlas-checkpoint-<task-id>", "created": false},
  "subtasks": [],
  "progress": {"total": 0, "completed": 0, "failed": 0, "pending": 0},
  "iterations": {"planning": 0, "execution": 0}
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
- Task 系统: TaskUpdate(taskId="gather", status="completed")
- 文件状态模式: .state/<task-id>.json: currentStage="gathering_completed"
```

**Step 4: 任务规划（支持循环修改）**

**重要**: 全流程使用同一个 task-id（同目录、可续传、可版本化）。

**4.0 创建子任务（Task 系统）**

规划完成后，根据 plan.json 创建子任务：
```
# 为每个子任务创建 Task 项，设置依赖关系
TaskCreate(
  subject="子任务 #1: [描述]",
  description="[详细修改内容]",
  activeForm="执行子任务 #1"
)
TaskCreate(
  subject="子任务 #2: [描述]",
  description="[详细修改内容]",
  activeForm="执行子任务 #2"
)
# 设置依赖（如有）
TaskUpdate(taskId="2", addBlockedBy=["1"])
```

1. **4.1 执行规划（首次）**: `Task(subagent_type="<用户选择的规划器>")` → 输出 `.claude/plan/<task-id>/plan.json`
2. **4.2 展示规划给用户**: 读取并格式化 plan.json，显示子任务列表、执行策略、影响范围

#### Step 4.2.5: 规划完整性验证

读取 `plan.json.completeness`：
- 要求: `coverage=100%`、`uncovered=[]`、`validation` 全 true
- 未通过: 明确列出缺失点 → 询问是否返回重新规划（推荐）

3. **4.3 用户确认**: AskUserQuestion → 继续执行（推荐）/ 修改规划 / 取消任务
4. **4.4 重新规划（版本化）**（若用户选择修改）:
   - 使用相同规划器，传入修改意见
   - 输出策略: 简单覆盖 `plan.json`；复杂场景生成 `plan.v2.json`/`plan.v3.json`…
   - 返回 4.2 循环直到用户确认

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
```

**Step 5: 任务执行（支持循环修改）**

1. **5.1 并发启动 Executors**: `Task(subagent_type="atlas:atlas-executor", model=<用户选择的模型>)`，每个子任务一个 executor
2. **5.2 收集执行结果**: 记录成功/失败的子任务

#### Step 5.2.5: 执行完成度验证

对比 `plan.json` 与各 executor 的 `completionStatus`：
- 输出总体完成率 + 未完成项列表（todos）
- 询问用户: 继续/重试失败/回滚/结束保存进度

3. **5.3 展示执行结果**: 成功 X 个 / 失败 Y 个（含原因）/ 修改文件列表
4. **5.4 用户决策**: AskUserQuestion → 继续验证（推荐）/ 修复失败任务 / 调整结果 / 回滚变更
5. **5.5 重新执行**（若用户选择修复/调整）: 返回 5.1 仅针对需要修改的子任务

完成后更新状态:

**Task 系统:**
```
# 每个子任务执行前
TaskUpdate(taskId="<subtask-id>", status="in_progress")

# 每个子任务执行后
TaskUpdate(taskId="<subtask-id>", status="completed")  # 或保持 in_progress（失败时）

# 查看进度
TaskList()  # 或用户使用 /todos
```

**文件状态模式:**
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

**允许**: AskUserQuestion、Task、读取 `.claude/gather/`/`.claude/plan/`、git 检查点。  
**禁止**: 主进程读/改业务代码、做深度分析（交给 subagent）。

### 3.2 任务 ID 管理原则

**统一 task-id**: Step 1-7 全程一致；格式 `<action>-<date>-<time>`（如 `add-types-20240115-103000`）。

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
- 简单覆盖 `plan.json`；复杂生成 `plan.v2.json`/`plan.v3.json`…，状态文件用 `planVersion` 指向最终版本。

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
  "config": {"mode": "auto", "planner": "atlas:planner", "executorModel": "sonnet", "testNode": "unified", "testMode": "compile"},
  "checkpoint": {"stashId": "atlas-checkpoint-add-types-20240115-103000", "created": true, "cleaned": false},
  "subtasks": [
    {"id": 1, "status": "completed", "description": "为 auth 组件添加类型", "files": ["Login.tsx", "Register.tsx"]},
    {"id": 2, "status": "completed", "description": "为 dashboard 组件添加类型", "files": ["Overview.tsx", "Analytics.tsx"]},
    {"id": 3, "status": "failed", "description": "为 shared 组件添加类型", "files": ["Button.tsx", "Input.tsx"], "error": "类型定义冲突"}
  ],
  "progress": {"total": 3, "completed": 2, "failed": 1, "pending": 0},
  "iterations": {"planning": 1, "execution": 2},
  "todos": [
    {"id": 1, "description": "为 auth 组件添加类型", "subtaskId": 1, "status": "completed", "completedAt": "2024-01-15T10:45:00Z", "error": null},
    {"id": 2, "description": "为 dashboard 组件添加类型", "subtaskId": 2, "status": "completed", "completedAt": "2024-01-15T10:50:00Z", "error": null},
    {"id": 3, "description": "为 shared 组件添加类型", "subtaskId": 3, "status": "failed", "completedAt": null, "error": "类型定义冲突"}
  ],
  "completedAt": null
}
```

### 3.7 断点续传（仅文件状态模式）

> **注意**: 断点续传功能仅在选择「文件状态」进度管理方式时可用。Task 系统的任务状态随会话结束而清除。

```bash
/orchestrate --resume <task-id>
```

**恢复要点**: 读状态文件 → 根据 `currentStage` 定位阶段 → 跳过已完成步骤 → 沿用原配置 → 依据 `subtasks/progress` 恢复进度。

**阶段映射**: `initialization→Step2` | `checkpoint_created→Step3` | `gathering_completed→Step4` | `planning_approved→Step5` | `execution_completed→Step6` | `testing_completed→报告` | `finished→结束`

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

### 示例 1: 快速模式（~3分钟）

```
用户: /orchestrate 修改 UserAPI.login 的返回类型 --quick

1. 选择快速模式 → 跳过所有后续询问
2. 主进程快速定位:
   - Grep "UserAPI" → 找到 src/api/UserAPI.ts
   - Read 文件 → 定位 login 方法
   - 生成修改计划（不调用 planner）
3. Executor(haiku): 修改 src/api/UserAPI.ts → 成功 ✓
4. 简化报告: 任务完成，修改 1 个文件
```

### 示例 2: 自动模式（~20分钟）

```
用户: /orchestrate 给所有 React 组件添加 TypeScript 类型

1. 选择自动模式 → 使用推荐配置
   - gatherer + planner + sonnet + 编译测试
2. 创建检查点: git stash push -m "atlas-checkpoint-..."
3. Gatherer: 收集组件信息 → .claude/gather/<id>/context.json
4. Planner: 生成计划 → .claude/plan/<id>/plan.json
   → 展示: 3 个子任务 → 用户确认 ✓
5. Executor: 并行执行 3 个子任务 → 全部成功 ✓
6. 测试: tsc --noEmit → 通过 ✓
7. 报告: 成功修改 6 个文件
```

---

## 五、输出格式

### 快速模式报告

```markdown
# 快速执行完成

**任务**: [描述]
**修改文件**: [文件列表]
**状态**: ✅ 成功 / ❌ 失败

[如果失败]
**失败原因**: [原因]
**建议**: 使用自动模式重新执行 `/orchestrate <任务>`
```

### 标准模式执行报告

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

### 标准模式必须做

- ✅ Step 1 一次性确认配置（执行模式、进度管理、规划器、模型、测试选项）
- ✅ 根据进度管理选择初始化：
  - Task 系统: 使用 TaskCreate 创建主任务
  - 文件状态模式: 创建 `.claude/orchestrate/.state/<task-id>.json`
- ✅ 非 quick/dry-run 创建检查点；按需 `gather → plan → execute → test → report`
- ✅ 规划必须可验证（`completeness`）；执行必须可对账（`completionStatus`）
- ✅ Task 系统下，根据 plan.json 使用 TaskCreate 创建子任务并设置依赖
- ✅ Task 系统下，执行前后使用 TaskUpdate 更新状态

### 快速模式必须做

- ✅ 创建状态文件；主进程≤5次工具定位；executor(haiku) 执行；更新状态并简报
- ✅ 失败时建议用户切换到自动模式

### 快速模式允许做

- ✅ 主进程使用 Grep/Glob/Read 快速定位文件（≤5 次）
- ✅ 主进程直接生成简单修改计划（不调用 planner）
- ✅ 跳过信息收集、检查点和进度追踪

### 禁止做

- ❌ 主进程直接修改文件（所有修改必须通过 executor）
- ❌ 标准模式跳过信息收集直接规划（除非 --no-gather 或快速模式）
- ❌ 标准模式跳过规划直接执行
- ❌ executor 重新扫描文件（应使用 plan.json 或主进程提供的修改点）
- ❌ 在 Step 1 之后还有其他的 AskUserQuestion（除了 Step 4.3 和 5.4 的确认循环）
- ❌ Task 系统忘记使用 TaskUpdate 更新任务状态
- ❌ 文件状态模式忘记更新状态文件的 `currentStage`
- ❌ 在用户未确认的情况下继续执行下一步
- ❌ 快速模式用于复杂任务（>3 个文件或涉及依赖分析）
  
**原则**: 能交给 subagent 的都交给 subagent；主进程只负责编排/确认/读取产物/汇总报告。
