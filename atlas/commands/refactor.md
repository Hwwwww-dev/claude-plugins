---
description: 智能重构命令。识别代码问题并执行特定模式的自动化重构，支持预览和交互式确认。
argument-hint: <pattern> [--quick] [--scope path] [--dry-run] [--interactive]
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

| 步骤 | 快速模式 | 自动模式 | 交互模式 | dry-run |
|------|---------|---------|---------|---------|
| 执行策略 | auto | auto | 询问用户 | auto |
| 候选识别 | **跳过** | 是 | 是 | 是 |
| 检查点 | **跳过** | 创建 | 询问用户 | 跳过 |
| 规划器选择 | **跳过（主进程直接规划）** | atlas:planner | 询问用户 | atlas:planner |
| Executor 模型 | **haiku** | sonnet | 询问用户 | - |
| 测试节点 | **不测试** | 统一测试 | 询问用户 | - |
| 测试模式 | - | 编译测试 | 询问用户 | - |
| 状态文件 | **创建** | 创建 | 创建 | 创建 |

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

**Step 1: 分阶段确认选项**

**第一个 AskUserQuestion: 执行模式选择**

```
问题: 执行模式
- 快速模式: 跳过候选识别和规划，直接重构（适合单文件小重构，~3分钟）
- 自动模式（推荐）: 使用推荐选项，减少交互
- 交互模式: 每个关键步骤都需要确认
- dry-run: 只规划不执行
```

**第二个 AskUserQuestion: 重构配置（仅交互模式和 dry-run）**

如果用户选择了**交互模式**或 **dry-run**，询问重构配置：

```
问题 1: 检查点
- 创建（推荐）: 创建 git stash 检查点，支持回滚
- 跳过: 不创建检查点（dry-run 默认跳过）

问题 2: 规划器选择
- atlas:planner（推荐）: 信任 gatherer 输出，最小化扫描
- 内置 Plan: 会自行探索验证

问题 3: Executor 模型（仅执行模式）
- sonnet（推荐）: 平衡性能与质量
- haiku: 快速简单重构
- opus: 复杂质量要求高
```

**自动模式行为**（跳过第二个 AskUserQuestion）：
- 检查点: 创建
- 规划器: atlas:planner
- Executor 模型: sonnet

**快速模式行为**（跳过第二、三个 AskUserQuestion）：
- 候选识别: 跳过
- 检查点: 跳过
- 规划器: 跳过（主进程直接规划）
- Executor 模型: haiku
- 测试: 不测试
- 状态文件: 创建

**第三个 AskUserQuestion: 测试配置**

询问测试配置：

```
问题 1: 测试节点
- 统一测试（推荐）: 全部执行完成后统一验证
- 每个候选后: 每个重构完成后立即测试
- 不测试: 跳过验证

问题 2: 测试模式
- 编译测试（推荐）: tsc --noEmit 确保语法正确
- 单元测试: npm test 确保功能正常
- 编译+单元: 完整验证
```

**注意**:
- 自动模式和交互模式都会询问测试配置
- 仅 dry-run 模式跳过测试配置询问
- **快速模式跳过所有询问，直接进入执行**

---

### 2.5 快速模式流程（--quick）

**适用场景**：
- 重构 1-3 个文件
- 简单的重命名、提取方法等

**流程**：
```
确认模式 → 主进程快速定位 → 直接执行 → 简化报告
```

**Step Q1: 确认快速模式**
```
AskUserQuestion:
问题: 执行模式
- 快速模式 ✓
```

**Step Q2: 创建状态文件**
```bash
mkdir -p .claude/refactor/.state
echo '{
  "executionId": "refactor-<timestamp>",
  "timestamp": "<ISO-8601>",
  "task": "<用户任务>",
  "status": "in_progress",
  "currentStage": "quick_refactor",
  "config": { "mode": "quick", "executorModel": "haiku" }
}' > .claude/refactor/.state/refactor-<timestamp>.json
```

**Step Q3: 主进程快速定位**
```
主进程允许使用 Grep/Glob/Read 快速定位目标文件（≤5 次工具调用）
生成简单的修改计划（不调用 planner agent）
直接构建 executor prompt
```

**Step Q4: 直接执行**
```
Task(subagent_type="atlas:atlas-executor", model="haiku")
prompt: |
  子任务 #1
  描述: [重构模式] - [用户任务]
  文件: [主进程定位的文件]
  修改点: [主进程分析的修改点]
  注意: 快速模式，只做明确提及的重构
```

**Step Q5: 简化报告**
```markdown
# 快速重构完成

**执行 ID**: refactor-<timestamp>
**状态文件**: .claude/refactor/.state/refactor-<timestamp>.json
**模式**: [重构模式]
**修改文件**: [文件列表]
**状态**: ✅ 成功 / ❌ 失败

[如果失败] 建议: 使用自动模式重新执行 `/refactor <pattern>`
```

**风险提示**：
- 跳过候选识别，可能遗漏重构点
- 跳过检查点，无法回滚
- 如果 executor 失败，建议用户切换到自动模式

---

### 2.6 标准模式执行步骤

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
  "config": {
    "mode": "<auto/interactive/dry-run>",
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

1. **4.1 执行规划（首次）**: `Task(subagent_type="<用户选择的规划器>")` → 输出 `.claude/plan/refactor-<ts>/plan.json`
2. **4.2 展示重构计划**: 识别的候选项（文件:行号）、重构策略和步骤、风险评估
3. **4.3 用户确认**: AskUserQuestion → 继续执行（执行重构模式）/ 修改计划 / 完成预览（预览模式）
4. **4.4 重新规划（版本化）**（若用户选择修改）:
   - 使用相同规划器，传入修改意见
   - 输出策略: 简单场景覆盖 plan.json / 复杂场景创建 plan.v2.json 等
   - 返回 4.2 循环直到用户确认

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

1. **5.1 并发/串行执行重构**: `Task(subagent_type="atlas:atlas-executor", model=<用户选择的模型>)`，根据测试节点决定并发/串行
2. **5.2 收集重构结果**: 成功的候选项、失败的候选项及原因
3. **5.3 展示结果**: 成功 X 个 / 失败 Y 个 / 修改文件列表
4. **5.4 用户决策**: AskUserQuestion → 继续验证（推荐）/ 修复失败 / 调整结果 / 回滚变更
5. **5.5 重新执行**（若用户选择修复/调整）: 返回 5.1 仅针对失败/需调整的候选

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

### 示例 1: 快速模式（~3分钟）- 单文件小重构

```
用户: /refactor extract-method --scope src/utils/helper.ts --quick

1. AskUserQuestion → 用户选择「快速模式」→ 跳过所有后续询问
2. 主进程快速定位: Grep "function.*{" → 发现 processData() 89行
3. 主进程分析: 识别可提取片段 L45-L78 (数据验证逻辑)
4. Executor(haiku): 提取为 validateUserData() 独立函数
5. 影响范围: 1 文件 | 修改: +15行 -34行 (净减 19行)
6. 输出简化报告 → 建议: 如需更多重构点，使用自动模式
```

### 示例 2: 自动模式（~15分钟）- 标准重构流程

```
用户: /refactor extract-method --scope src/services

1. AskUserQuestion → 用户选择「自动模式」→ 使用推荐配置
2. 创建检查点: git stash push -m "atlas-checkpoint-refactor-20240115"
3. Gatherer(haiku): 扫描 src/services/ → 识别 5 个候选 (函数体>50行)
   - UserService.processOrder (89行) | PaymentService.validate (67行) | ...
4. Planner: 生成 plan.json → 用户确认执行 ✓
5. Executor(sonnet): 并行执行 5 个 extract-method 重构
   - 成功: 5/5 | 新增函数: 8 个 | 修改文件: 4 个
6. 测试: tsc --noEmit ✓ → 输出完整报告 (含回滚命令)
```

### 示例 3: 交互模式（带循环修改）

```
用户: /refactor add-types --scope src/services --interactive

1. AskUserQuestion → 用户选择「交互模式」→ 逐项确认配置
   - 检查点: 创建 | 规划器: atlas:planner | 模型: sonnet | 测试: 编译+单元
2. Gatherer: 识别 12 个缺失类型的函数 → Planner 生成计划
3. 用户审查: "排除 legacy/ 目录" → 重新规划 → 剩余 8 个候选 ✓
4. Executor 第一轮: 7 成功 / 1 失败 (PaymentService.process 类型冲突)
5. 用户选择「修复失败」→ Executor 重试: 调整泛型约束 → 成功 ✓
6. 测试: tsc --noEmit ✓ + npm test ✓ → 8/8 完成
7. 输出报告: 修改 6 文件 | 新增类型定义 23 个 | iterations: planning=2, execution=2
```

### 示例 4: dry-run 模式 - 预览不执行

```
用户: /refactor modernize-js --scope src --dry-run

1. AskUserQuestion → 用户选择「dry-run」→ 跳过检查点和测试配置
2. Gatherer(haiku): 扫描 src/ → 识别 15 个现代化候选
   - var 声明: 8 处 | callback 模式: 5 处 | 旧式循环: 2 处
3. Planner: 生成详细重构计划 (不执行)
4. 输出预览报告:
   - 预计修改: 9 文件 | 预计变更: +45行 -62行
   - 风险评估: 低 (无破坏性变更)
5. 提示: 确认后执行 `/refactor modernize-js --scope src`
```

---

## 五、核心约束

### 标准模式必须做

- ✅ **Step 1**: 分阶段确认配置（执行模式 → 重构配置 → 测试配置）
- ✅ **Step 1**: 自动模式跳过第二个 AskUserQuestion，直接使用推荐配置
- ✅ **Step 1**: dry-run 模式跳过第三个 AskUserQuestion，不需要测试配置
- ✅ **Step 2**: 创建状态目录 `.claude/refactor/.state/` 和状态文件（执行重构时）
- ✅ **Step 2**: 在每个关键步骤完成后更新状态文件的 `currentStage` 字段
- ✅ **Step 3**: 使用 `Task(subagent_type="atlas:information-gatherer", model="haiku")`
- ✅ **Step 4**: 使用用户选择的规划器，输出到 `.claude/plan/refactor-<ts>/`
- ✅ **Step 4.2-4.4**: 展示重构计划给用户，支持循环修改直到用户确认
- ✅ **Step 5**: 从 plan.json 提取修改点嵌入 executor prompt（执行重构时）
- ✅ **Step 5.2-5.5**: 展示重构结果，支持用户修复失败或调整结果
- ✅ **Step 6**: 根据 Step 1 的选择执行验证测试
- ✅ **Step 7**: 更新最终状态并输出报告

### 快速模式必须做

- ✅ **Step Q1**: 确认用户选择快速模式
- ✅ **Step Q2**: 创建状态文件 `.claude/refactor/.state/refactor-<timestamp>.json`
- ✅ **Step Q3**: 主进程快速定位目标文件（≤5 次工具调用）
- ✅ **Step Q4**: 使用 `Task(subagent_type="atlas:atlas-executor", model="haiku")`
- ✅ **Step Q5**: 输出简化报告（含执行 ID 和状态文件路径）
- ✅ 失败时建议用户切换到自动模式

### 快速模式允许做

- ✅ 主进程使用 Grep/Glob/Read 快速定位文件（≤5 次）
- ✅ 主进程直接生成简单修改计划（不调用 planner）
- ✅ 跳过候选识别、检查点

### 禁止做

- ❌ 主进程直接修改文件（所有修改必须通过 executor）
- ❌ 标准模式跳过候选识别直接规划（除非快速模式）
- ❌ 标准模式跳过规划直接执行
- ❌ executor 重新扫描文件（应使用 plan.json 或主进程提供的修改点）
- ❌ 在 Step 1 之后还有其他的 AskUserQuestion（除了 Step 4.3 和 5.4 的确认循环）
- ❌ 标准模式忘记更新状态文件的 `currentStage`
- ❌ 在用户未确认的情况下继续执行下一步
- ❌ "顺便"做其他优化（只执行指定模式的重构）
- ❌ 快速模式用于复杂任务（>3 个文件或涉及依赖分析）
