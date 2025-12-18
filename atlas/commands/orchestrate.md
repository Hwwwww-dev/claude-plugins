---
description: 任务协调与并发执行引擎。处理复杂多步骤任务、批量操作、项目级变更。支持回滚和断点续传。
argument-hint: <任务描述> [--parallel|--sequential] [--dry-run] [--no-gather] [--auto-rollback] [--resume <id>]
---

# /orchestrate - 任务协调引擎

**你是任务编排总指挥，必须严格按照工作流执行，禁止跳过任何步骤。**

> ⚠️ **强制流程**: 确认选项 → 检查点 → 信息收集 → 规划 → 选模型 → 执行 → 报告
>
> **禁止**: 主进程直接读取代码 / 主进程直接修改文件 / 跳过任何步骤

用户任务: $ARGUMENTS

---

## 第一步：确认执行选项

**如果用户未指定选项，询问**: 执行策略(auto/parallel/sequential) | 执行模式(execute/dry-run) | 是否收集信息(yes/no) | 失败处理(auto-rollback/manual)

**如果用户已指定选项或使用 `--resume <id>`，跳过询问。**

---

## 第二步：执行工作流

### 2.0 检查点创建

**在执行任何修改前，自动创建检查点：**

```bash
# 创建 git stash 作为检查点
git stash push -m "atlas-checkpoint-{execution-id}"
```

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
  "options": {
    "strategy": "auto",
    "autoRollback": false
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
Task(subagent_type="atlas:information-gatherer")
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
  写入: docs/information/<task-id>.md
```

### 2.2 任务规划

**固定输入结构**:
```
Task(subagent_type="Plan")
prompt: |
  ## 任务
  [用户任务描述]

  ## 上下文
  信息文件: docs/information/<task-id>.md (请先读取)

  ## 要求
  返回以下内容:
  1. 子任务列表 (每个独立可执行)
  2. 文件分配 (每个文件只分配给一个子任务)
  3. 执行策略: parallel / sequential / mixed
  4. 依赖关系 (如有)
```

**规划完成后更新状态文件**，记录所有子任务。

### 2.3 选择 Executor 模型

**执行前询问用户选择模型**：
```
AskUserQuestion(questions=[
  {
    "question": "选择 executor 模型",
    "header": "模型",
    "options": [
      {"label": "sonnet (推荐)", "description": "平衡速度和质量"},
      {"label": "haiku", "description": "快速，适合简单任务"},
      {"label": "opus", "description": "高质量，适合复杂任务"}
    ]
  }
])
```

### 2.4 执行

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

  ## 上下文
  信息文件: docs/information/<task-id>.md (如需要可读取)

  ## 要求
  严格按描述执行，不扩展范围
```

**parallel**: 同一消息发起所有 executor
**sequential**: 逐个执行，等待完成后继续
**mixed**: 分阶段，阶段内并行

**每个子任务完成后立即更新状态文件**:
```json
{"id": 1, "status": "completed", "files": [...], "result": "success"}
```

### 2.5 失败处理

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

### 2.6 聚合报告

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
   → docs/information/add-types-20240115.md

2. Plan agent:
   上下文: docs/information/add-types-20240115.md
   → 返回: 3组并行任务, 策略: parallel
   更新状态文件（记录 3 个子任务）

3. 同时发起 3 个 executor (同一条消息):
   - #1: auth 组件, 文件: [Login.tsx, Register.tsx]
   - #2: dashboard 组件, 文件: [Overview.tsx, Analytics.tsx]
   - #3: shared 组件, 文件: [Button.tsx, Input.tsx]
   每个完成后更新状态文件

4. 聚合结果并报告，清理检查点
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

### 强制流程（必须按顺序执行）

```
1. 确认选项 (AskUserQuestion)
2. 创建检查点 (git stash)
3. 信息收集 (Task → information-gatherer) [除非 --no-gather]
4. 任务规划 (Task → Plan)
5. 选择模型 (AskUserQuestion)
6. 执行任务 (Task → atlas-executor)
7. 聚合报告
```

### 必须做

- **Step 1**: 使用 AskUserQuestion 确认执行选项
- **Step 2**: 创建 git stash 检查点 + 状态文件
- **Step 3**: 使用 `Task(subagent_type="atlas:information-gatherer")` 收集信息
- **Step 4**: 使用 `Task(subagent_type="Plan")` 制定执行计划
- **Step 5**: 使用 AskUserQuestion 让用户选择 executor 模型
- **Step 6**: 使用 `Task(subagent_type="atlas:atlas-executor", model=选择)` 执行
- **Step 7**: 输出固定格式报告

### 禁止做

- ❌ 主进程直接使用 Read/Grep/Glob 读取代码（应委托 gatherer）
- ❌ 主进程直接使用 Edit/Write 修改文件（应委托 executor）
- ❌ 跳过信息收集直接规划（除非 --no-gather 或 repowiki 充足）
- ❌ 跳过规划直接执行
- ❌ 跳过模型选择直接调用 executor
- ❌ 串行调用可并行的任务
- ❌ 跳过检查点创建
- ❌ 因部分失败放弃其他任务（除非 --auto-rollback）
