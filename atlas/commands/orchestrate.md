---
description: 任务协调与并发执行引擎。处理复杂多步骤任务、批量操作、项目级变更。支持回滚和断点续传。
argument-hint: <任务描述> [--parallel|--sequential] [--dry-run] [--no-gather] [--auto-rollback] [--resume <id>]
---

# /orchestrate - 任务协调引擎

**你是任务编排总指挥，必须严格按照工作流执行，禁止跳过任何步骤。**

> ⚠️ **强制流程**: 确认选项 → 检查点 → 信息收集 → 选规划器 → 规划 → 选模型 → 执行 → 报告
>
> **禁止**: 主进程直接读取代码 / 主进程直接修改文件 / 跳过任何步骤

用户任务: $ARGUMENTS

---

## 第一步：确认执行选项

**如果用户未指定选项，首先询问执行模式**:

```
AskUserQuestion(questions=[
  {
    "header": "执行模式",
    "question": "选择执行模式",
    "options": [
      {"label": "自动模式（推荐）", "description": "全流程使用推荐选项，不再询问确认"},
      {"label": "交互模式", "description": "每步确认，控制更精细"},
      {"label": "dry-run", "description": "只规划不执行，先看计划"}
    ]
  }
])
```

### 模式行为定义

| 步骤 | 自动模式 | 交互模式 | dry-run |
|------|---------|---------|---------|
| 执行策略 | auto | 询问用户 | auto |
| 信息收集 | 是（除非 repowiki 充足） | 询问用户 | 是 |
| 检查点 | 创建 | 询问用户 | 跳过 |
| 规划器选择 | atlas:planner | 询问用户 | atlas:planner |
| Executor 模型 | sonnet | 询问用户 | - |
| 失败处理 | **询问用户** | 询问用户 | - |

**自动模式默认值**:
- 执行策略: auto（由 planner 决定并行/串行）
- 规划器: atlas:planner
- Executor 模型: 跟随主对话，或按任务复杂度选择（简单-haiku / 中等-sonnet / 复杂-opus）
- 信息收集: 是（除非 repowiki 充足）
- 检查点: 创建
- 失败处理: **仍然询问用户**（危险操作不自动决策）

**交互模式详细选项**（仅交互模式时询问）:

```
AskUserQuestion(questions=[
  {
    "header": "执行策略",
    "question": "选择执行策略",
    "options": [
      {"label": "auto（推荐）", "description": "根据任务特性自动选择并行或串行"},
      {"label": "parallel", "description": "强制并行执行所有子任务"},
      {"label": "sequential", "description": "强制串行执行所有子任务"}
    ]
  },
  {
    "header": "信息收集",
    "question": "是否收集项目信息？",
    "options": [
      {"label": "是（推荐）", "description": "调用 gatherer 收集项目上下文"},
      {"label": "否", "description": "跳过信息收集，直接规划"}
    ]
  },
  {
    "header": "失败处理",
    "question": "子任务失败时如何处理？",
    "options": [
      {"label": "manual（推荐）", "description": "失败时询问处理方式"},
      {"label": "auto-rollback", "description": "失败时自动回滚所有修改"}
    ]
  },
  {
    "header": "检查点",
    "question": "是否创建 Git 检查点？",
    "options": [
      {"label": "创建（推荐）", "description": "失败可回滚，更安全"},
      {"label": "跳过", "description": "不创建检查点"}
    ]
  }
])
```

**如果用户已指定选项或使用 `--resume <id>`，跳过询问。**

---

## 第二步：执行工作流

### 2.0 检查点创建（根据用户选择）

**如果用户选择"创建"检查点**：

```bash
# 创建 git stash 作为检查点
git stash push -m "atlas-checkpoint-{execution-id}"
```

**如果用户选择"跳过"检查点**：
- 跳过 git stash 步骤
- 状态文件中记录 `"checkpoint": {"created": false}`
- 失败时无法自动回滚，需手动处理

**初始化执行状态文件：**
```
写入: .claude/orchestrate/.state/{execution-id}.json
```

**状态文件结构**:
```json
{
  "executionId": "task-20240115-103000",
  "timestamp": "2024-01-15T10:30:00Z",
  "task": "给所有 React 组件添加 TypeScript 类型",
  "mode": "auto",
  "options": {
    "strategy": "auto",
    "autoRollback": false,
    "checkpoint": true
  },
  "checkpoint": {
    "stashId": "atlas-checkpoint-task-20240115-103000",
    "created": true
  },
  "subtasks": [
    {"id": 1, "status": "pending", "files": ["Login.tsx", "Register.tsx"]},
    {"id": 2, "status": "pending", "files": ["Overview.tsx", "Analytics.tsx"]},
    {"id": 3, "status": "pending", "files": ["Button.tsx", "Input.tsx"]}
  ],
  "progress": {
    "total": 3,
    "completed": 0,
    "failed": 0,
    "pending": 3
  }
}
```

### 2.1 信息收集（如选择）

**优先从 `.claude/repowiki/` 获取项目信息**（如存在）:
- `project.pkg.json`: 项目元数据、技术栈
- `modules.pkg.json`: 模块结构、依赖关系
- `api.pkg.json`: API 端点
- `symbols.pkg.json`: 符号索引
- `quick-lookup.json`: 快速查询

**如 repowiki 信息充足，可跳过信息收集直接规划。**

**固定输入结构**:
```
Task(subagent_type="atlas:information-gatherer", model="haiku")
prompt: |
  ## 任务
  任务 ID: <task-id>
  任务描述: [用户要做什么]

  ## 已有信息
  检查 `.claude/repowiki/` 是否存在，优先使用现有 PKG 文件

  ## 收集目标
  - 范围: [哪些目录/文件]
  - 关注点: [结构/依赖/模式]

  ## 输出
  写入目录: .claude/gather/<task-id>/
  - report.md: 完整报告
  - context.json: 结构化数据（含代码片段）
```

### 2.2 选择规划器

**根据执行模式决定**:
- **自动模式/dry-run**: 直接使用 atlas:planner（跳过询问）
- **交互模式**: 询问用户选择规划器类型

```
AskUserQuestion(questions=[
  {
    "question": "选择任务规划器",
    "header": "Planner",
    "options": [
      {"label": "atlas:planner (推荐)", "description": "信任 gatherer 输出，最小化额外扫描，高效规划"},
      {"label": "内置 Plan", "description": "Claude Code 内置规划器，会自行探索验证"}
    ]
  }
])
```

### 2.3 任务规划

**根据用户选择调用对应的规划器**:

#### 选项 A: atlas:planner（推荐）

**特点**: 信任 gatherer 输出，基于已有信息直接规划，≤3 次补充读取

```
Task(subagent_type="atlas:planner")
prompt: |
  ## 任务
  [用户任务描述]

  ## Gatherer 输出位置
  `.claude/gather/<task-id>/`
  - `report.md`: 完整分析报告
  - `context.json`: 结构化数据

  ## 输出要求
  按照 planner agent 定义的固定格式输出执行计划
```

#### 选项 B: 内置 Plan

**特点**: 会自行探索代码库，适合 gatherer 信息不足或需要深度验证的场景

```
Task(subagent_type="Plan")
prompt: |
  ## 任务
  [用户任务描述]

  ## ⚠️ 强制信息源（必须先读取）
  **gatherer 已收集的信息保存在**: `.claude/gather/<task-id>/`
  - `report.md`: 完整分析报告
  - `context.json`: 结构化数据（含代码片段、文件列表、依赖关系）

  **你必须**:
  1. 首先读取上述文件
  2. 基于已有信息制定规划
  3. 仅在以下情况补充读取（需说明理由）:
     - 关键文件路径缺失（无法分配任务）
     - 依赖关系不明确（无法确定执行顺序）
     - 代码模式信息不足（无法制定修改策略）

  ## 信息充足性检查清单
  在规划前确认以下信息是否已从 gatherer 获取:
  - [ ] 目标文件完整列表
  - [ ] 文件间依赖关系
  - [ ] 代码模式/风格示例
  - [ ] 技术栈信息

  如 4 项均已获取 → **禁止额外读取**，直接规划
  如缺失 < 5项 → 针对性补充
  如缺失 5+ 项 → 标记 gatherer 信息不足，建议重新收集

  ## 输出要求
  1. **信息来源声明**: 说明规划基于哪些信息（gatherer 输出 / 补充读取）
  2. 子任务列表 (每个独立可执行)
  3. 文件分配 (每个文件只分配给一个子任务)
  4. 执行策略: parallel / sequential / mixed
  5. 依赖关系 (如有)
```

**备份文件**：gatherer 输出保存在 `.claude/gather/<task-id>/`，用于断点续传。

**规划完成后更新状态文件**，记录所有子任务。

### 2.4 选择 Executor 模型

**根据执行模式决定**:
- **自动模式**: 直接使用 sonnet（跳过询问）
- **交互模式**: 询问用户选择模型
- **dry-run**: 跳过此步骤（不执行）

```
AskUserQuestion(questions=[
  {
    "question": "选择 executor 模型",
    "header": "模型",
    "options": [
      {"label": "跟随主对话（推荐）", "description": "使用当前对话的模型"},
      {"label": "haiku", "description": "快速，适合简单任务"},
      {"label": "sonnet", "description": "平衡速度和质量"},
      {"label": "opus", "description": "高质量，适合复杂任务"}
    ]
  }
])
```

### 2.5 执行

**信息传递原则**：Plan 阶段的规划结果 + gatherer 的关键信息**直接嵌入** executor prompt。

**固定输入结构**:
```
Task(subagent_type="atlas:atlas-executor", model=用户选择)
prompt: |
  ## 子任务
  编号: #N
  描述: [具体任务]

  ## 文件
  - path/to/file1.ts
  - path/to/file2.ts

  ## 关键上下文（来自 gatherer）
  <context>
  [嵌入与此子任务相关的 gatherer 信息片段]
  </context>

  ## 要求
  严格按描述执行，不扩展范围
  如上下文信息充足，无需额外读取文件
```

**parallel**: 同一消息发起所有 executor
**sequential**: 逐个执行，等待完成后继续
**mixed**: 分阶段，阶段内并行

**每个子任务完成后立即更新状态文件**:
```json
{"id": 1, "status": "completed", "files": [...], "result": "success"}
```

### 2.6 失败处理

**子任务失败时**:

#### --auto-rollback 模式
```bash
# 自动回滚所有修改
git stash pop

# 输出
⚠️ 子任务 #N 失败，已自动回滚所有修改
原因: [失败原因]
建议: [修复建议]
```

#### 默认模式（手动处理）
```
子任务 #N 失败

选项:
1. 回滚: 恢复到检查点状态
2. 跳过: 继续执行其他子任务
3. 重试: 重新执行失败的子任务
4. 终止: 保留已完成的修改，终止执行

请选择处理方式:
```

**用户选择回滚时**:
```bash
git stash pop
echo "已回滚到检查点"
```

### 2.7 聚合报告

**固定输出结构**:
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
- file1.ts
- file2.ts

## 失败详情 (如有)
- 子任务#N: [原因] → [建议]

## 检查点
- 状态: 已清理 / 可用于回滚
- 命令: `/orchestrate --resume task-20240115-103000`

## 后续建议
- [建议1]
- [建议2]
```

**成功完成后清理检查点**:
```bash
git stash drop "atlas-checkpoint-{execution-id}"
```

---

## 断点续传

### 触发方式

```bash
/orchestrate --resume task-20240115-103000
```

### 续传流程

1. **读取状态文件**:
   ```
   读取: .claude/orchestrate/.state/{execution-id}.json
   ```

2. **显示执行状态**:
   ```markdown
   ## 断点续传

   执行 ID: task-20240115-103000
   原始任务: 给所有 React 组件添加 TypeScript 类型

   进度:
   - ✅ 子任务 #1: 完成
   - ❌ 子任务 #2: 失败
   - ⏸️ 子任务 #3: 待执行

   继续选项:
   1. 重试失败: 重新执行 #2，然后执行 #3
   2. 跳过失败: 直接执行 #3
   3. 全部重新执行: 回滚并重新开始
   4. 放弃: 清理状态，保留当前修改
   ```

3. **根据选择执行**:
   - 重试失败：从失败点重新执行
   - 跳过失败：继续执行待执行任务
   - 全部重新执行：回滚检查点，重新开始
   - 放弃：清理状态文件和检查点

4. **更新状态文件**直到完成

---

## 执行示例

### 示例: 并行执行（完整流程）

```
用户: /orchestrate 给所有 React 组件添加 TypeScript 类型

0. 创建检查点 + 状态文件:
   git stash push -m "atlas-checkpoint-add-types-20240115"
   写入: .claude/orchestrate/.state/add-types-20240115.json

1. information-gatherer:
   收集目标: 所有 React 组件位置和现有类型情况
   → .claude/gather/add-types-20240115/
   (模型: haiku - 固定)

2. 选择规划器:
   用户选择 atlas:planner (推荐，最小化扫描)

3. planner:
   读取: .claude/gather/add-types-20240115/context.json
   → 返回: 3组并行任务, 策略: parallel
   更新状态文件（记录 3 个子任务）

4. 同时发起 3 个 executor (同一条消息):
   - #1: auth 组件, 文件: [Login.tsx, Register.tsx]
   - #2: dashboard 组件, 文件: [Overview.tsx, Analytics.tsx]
   - #3: shared 组件, 文件: [Button.tsx, Input.tsx]
   每个完成后更新状态文件

5. 聚合结果并报告，清理检查点
```

### 失败场景

**auto-rollback 模式**: 子任务失败 → 自动 `git stash pop` → 输出失败原因和建议

**manual 模式**: 提供选项（回滚/跳过/重试/终止），等待用户选择

**断点续传**: `/orchestrate --resume <id>` → 读取状态 → 显示进度 → 继续执行

---

## 文件冲突处理

并行 executor 修改同一文件会导致冲突：

1. **按文件分组**: 修改同一文件的操作分给同一个 executor
2. **串行化**: 必须分开的任务改为串行执行
3. **分阶段**: 先完成共享依赖，再并行执行后续

```
示例: 重构 utils.ts 并更新 3 个调用方

❌ 错误: 并行 4 个 executor → 调用方可能读到旧版

✓ 正确:
  阶段1: executor 修改 utils.ts
  阶段2: 并行 3 个 executor 更新调用方
```

---

## 核心约束

### 主进程职责（严格限制）

**主进程只做协调，不做实际工作。**

**允许的操作**:
- ✅ 使用 AskUserQuestion 与用户交互
- ✅ 使用 Task 工具调用 agent
- ✅ 读取 agent 输出结果
- ✅ 聚合报告并展示给用户
- ✅ 简单的状态文件读写（`.claude/orchestrate/.state/`）
- ✅ Git 检查点操作（stash/pop）

**禁止的操作**:
- ❌ 使用 Read/Grep/Glob 读取代码文件
- ❌ 使用 Edit/Write 修改代码文件
- ❌ 直接分析代码逻辑
- ❌ 直接执行修复或重构

### Agent 调用规范

**信息收集阶段**:
```
Task(subagent_type="atlas:information-gatherer", model="haiku")
```
→ 输出位置: `.claude/gather/<task-id>/`

**任务规划阶段**:
```
Task(subagent_type="atlas:planner")  # 推荐
# 或
Task(subagent_type="Plan")  # 内置规划器
```
→ 输入: gatherer 输出位置
→ 输出: 结构化执行计划

**执行阶段**:
```
Task(subagent_type="atlas:atlas-executor", model=用户选择)
```
→ 输入: 子任务描述 + 相关 gatherer 信息片段（直接嵌入 prompt）
→ 输出: 执行报告

### 信息传递链

```
gatherer → 文件输出 → planner 读取
                   ↓
          planner → 提取关键信息 → 嵌入 executor prompt
```

**原则**：每个阶段的输出是下一阶段的输入，主进程负责传递位置/内容。

### 强制流程（必须按顺序执行）

```
1. 确认执行模式 (AskUserQuestion) - 自动/交互/dry-run
2. [交互模式] 确认详细选项 (AskUserQuestion)
3. 创建检查点 (git stash) [除非 dry-run 或选择跳过]
4. 信息收集 (Task → information-gatherer) [除非 --no-gather 或 repowiki 充足]
5. 选择规划器 [交互模式询问，自动/dry-run 使用 atlas:planner]
6. 任务规划 (Task → 选择的规划器)
7. [非 dry-run] 选择模型 [交互模式询问，自动模式使用 sonnet]
8. [非 dry-run] 执行任务 (Task → atlas-executor)
9. 聚合报告
```

### 必须做

- **Step 1**: 使用 AskUserQuestion 确认执行模式（自动/交互/dry-run）
- **Step 2**: 交互模式时询问详细选项；自动/dry-run 使用默认值
- **Step 3**: 根据模式创建 git stash 检查点 + 状态文件
- **Step 4**: 使用 `Task(subagent_type="atlas:information-gatherer", model="haiku")` 收集信息
- **Step 5**: 交互模式询问规划器；自动/dry-run 直接用 atlas:planner
- **Step 6**: 使用选择的规划器制定执行计划
- **Step 7**: 交互模式询问模型；自动模式直接用主对话默认模型
- **Step 8**: 使用 `Task(subagent_type="atlas:atlas-executor", model=选择)` 执行
- **Step 9**: 输出固定格式报告

### 禁止做

- ❌ 主进程直接使用 Read/Grep/Glob 读取代码（应委托 gatherer）
- ❌ 主进程直接使用 Edit/Write 修改文件（应委托 executor）
- ❌ 跳过信息收集直接规划（除非 --no-gather 或 repowiki 充足）
- ❌ 跳过规划直接执行
- ❌ 自动模式下询问规划器/模型选择（应使用默认值）
- ❌ 串行调用可并行的任务
- ❌ 用户选择创建检查点时跳过检查点创建
- ❌ 因部分失败放弃其他任务（除非 --auto-rollback）
