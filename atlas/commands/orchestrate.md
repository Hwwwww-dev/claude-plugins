---
description: 任务协调与并发执行引擎。处理复杂多步骤任务、批量操作、项目级变更。
argument-hint: <任务描述> [--parallel|--sequential] [--dry-run] [--no-gather]
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
```

**如果用户已指定选项（如 `--parallel --dry-run`），跳过询问。**

---

## 第二步：执行工作流

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

### 2.4 聚合报告

**固定输出结构**:
```markdown
# Atlas 执行报告

## 任务
[描述]

## 统计
- 子任务: X 个
- 成功: Y / 失败: Z

## 修改文件
- file1.ts
- file2.ts

## 失败详情 (如有)
- 子任务#N: [原因] → [建议]

## 后续建议
- [建议1]
- [建议2]
```

---

## 执行示例

### 示例 1: 并行执行

```
用户: /orchestrate 给所有 React 组件添加 TypeScript 类型

1. information-gatherer:
   任务 ID: add-types-20251129
   收集目标: 所有 React 组件位置和现有类型情况
   → docs/information/add-types-20251129.md

2. Plan agent:
   任务: 添加类型
   上下文: docs/information/add-types-20251129.md
   → 返回: 3组并行, 策略: parallel

3. 同时发起 3 个 executor (同一条消息):
   - #1: auth 组件, 文件: [Login.tsx, Register.tsx]
   - #2: dashboard 组件, 文件: [Overview.tsx, Analytics.tsx]
   - #3: shared 组件, 文件: [Button.tsx, Input.tsx]

4. 聚合结果并报告
```

### 示例 2: 串行执行

```
用户: /orchestrate 重构数据库层，先改 schema 再改 repository

1. information-gatherer → 分析数据库层结构

2. Plan agent → 返回: 2个子任务有依赖, 策略: sequential

3. executor #1: 修改 schema → 等待完成
4. executor #2: 修改 repository → 等待完成

5. 聚合结果并报告
```

### 示例 3: 混合执行

```
用户: /orchestrate 重构 auth 模块，先提取公共逻辑再更新各组件

1. information-gatherer → 分析 auth 模块

2. Plan agent → 返回: 策略: mixed

3. 阶段1 (串行):
   executor #1: 提取公共逻辑到 auth-utils.ts
   等待完成...

4. 阶段2 (并行, 同一条消息):
   - executor #2: 更新 Login.tsx
   - executor #3: 更新 Register.tsx
   - executor #4: 更新 Profile.tsx

5. 聚合结果并报告
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
- 使用固定输入结构调用 agents
- 并行任务在同一消息中一次性发起
- 收集结果后使用固定格式报告

**禁止做**:
- 自己直接修改文件
- 串行调用可并行任务
- 因部分失败放弃其他任务
