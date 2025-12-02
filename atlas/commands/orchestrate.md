---
description: 任务协调与并发执行引擎。处理复杂多步骤任务、批量操作、项目级变更。支持回滚和断点续传。
argument-hint: <任务描述> [--parallel|--sequential] [--dry-run] [--no-gather] [--auto-rollback] [--resume <id>]
---

# /orchestrate - 任务协调引擎

**你是任务编排总指挥，必须通过 Task tool 调用 subagents 执行任务。**

用户任务: $ARGUMENTS

---

## 第一步：确认执行选项

**如果用户未在命令中指定选项，使用 AskUserQuestion 询问：**

```
问题1: 执行策略
- auto (推荐): 由 Plan agent 智能决定
- parallel: 强制并行
- sequential: 强制串行

问题2: 执行模式
- execute (默认): 正常执行
- dry-run: 只生成计划，不执行

问题3: 是否先收集信息
- yes (推荐): 先调用 information-gatherer
- no: 直接规划执行

问题4: 失败处理
- auto-rollback: 失败时自动回滚
- manual: 失败时询问处理方式（默认）
```

**如果用户已指定选项（如 `--parallel --dry-run`），跳过询问。**

**如果用户指定 `--resume <id>`，跳到断点续传流程。**

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

**固定输入结构**:
```
Task(subagent_type="atlas:information-gatherer")
prompt: |
  ## 任务
  任务 ID: <task-id>
  任务描述: [用户要做什么]

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

### 2.3 执行

**固定输入结构**:
```
Task(subagent_type="atlas:atlas-executor")
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

### 2.4 失败处理

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

### 2.5 聚合报告

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

### 示例 1: 并行执行（带检查点）

```
用户: /orchestrate 给所有 React 组件添加 TypeScript 类型

0. 创建检查点:
   git stash push -m "atlas-checkpoint-add-types-20240115"
   写入状态文件到 .claude/orchestrate/.state/add-types-20240115.json

1. information-gatherer:
   任务 ID: add-types-20240115
   收集目标: 所有 React 组件位置和现有类型情况
   → docs/information/add-types-20240115.md

2. Plan agent:
   任务: 添加类型
   上下文: docs/information/add-types-20240115.md
   → 返回: 3组并行, 策略: parallel
   更新状态文件（记录 3 个子任务）

3. 同时发起 3 个 executor (同一条消息):
   - #1: auth 组件, 文件: [Login.tsx, Register.tsx]
   - #2: dashboard 组件, 文件: [Overview.tsx, Analytics.tsx]
   - #3: shared 组件, 文件: [Button.tsx, Input.tsx]
   每个完成后更新状态文件

4. 聚合结果并报告
   清理检查点
```

### 示例 2: 失败回滚

```
用户: /orchestrate 重构 API 层 --auto-rollback

1. 创建检查点
2. 执行子任务 #1 ✅
3. 执行子任务 #2 ❌ 失败

自动回滚:
git stash pop
清理状态文件

输出:
⚠️ 子任务 #2 失败，已自动回滚所有修改
修改的文件已恢复到执行前状态
建议: 检查 api/order.ts:45 的类型错误后重试
```

### 示例 3: 断点续传

```
用户: /orchestrate --resume add-types-20240115

读取状态:
- 子任务 #1: 完成
- 子任务 #2: 失败
- 子任务 #3: 待执行

用户选择: 跳过失败

继续执行:
- 执行子任务 #3 ✅

最终报告:
- 完成: 2/3
- 跳过: 1 (子任务 #2)
```

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

**必须做**:
- 执行前创建检查点（git stash）
- 维护状态文件（支持断点续传）
- 使用固定输入结构调用 agents
- 并行任务在同一消息中一次性发起
- 收集结果后使用固定格式报告
- 每个子任务完成后更新状态文件

**禁止做**:
- 自己直接修改文件
- 串行调用可并行任务
- 因部分失败放弃其他任务（除非 --auto-rollback）
- 跳过检查点创建步骤
