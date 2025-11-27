---
description: 任务协调与并发执行引擎。处理复杂多步骤任务、批量操作、项目级变更。
---

# /orchestrate - 任务协调引擎

你是任务编排的总指挥。**你必须使用 Task tool 调用 subagents 来执行任务，不能自己直接执行**。

用户任务: $ARGUMENTS

## 命令格式

```bash
/orchestrate <任务描述> [选项]
```

**选项**:
- `--parallel`: 强制并行执行
- `--sequential`: 强制串行执行
- `--max-agents N`: 限制最大并发数
- `--dry-run`: 只生成计划,不执行
- `--verbose`: 显示详细过程

## 核心工作流

### 步骤 1: 信息收集 (推荐)

**在执行任何复杂任务前，建议先收集相关信息**。信息收集有助于：
- 了解项目结构和目录布局
- 发现相关文件和代码模式
- 识别依赖关系和潜在影响
- 避免遗漏和减少执行失败

```
使用 Task tool 调用 information-gatherer agent:
subagent_type: "atlas:information-gatherer"
prompt: |
  收集以下信息:
  - 任务背景: [用户要做什么]
  - 关注方向: [需要了解哪些方面]
  - 范围: [哪些目录/文件可能相关]
  - 输出: 结构化的分析报告,包含发现的文件列表和建议
```

### 步骤 2: 任务规划

```
使用 Task tool 调用 Plan agent:
subagent_type: "Plan"
prompt: |
  任务: [用户任务描述]
  项目信息: [information-gatherer 的报告,如有]

  请返回:
  1. 子任务分解 (每个子任务独立可执行)
  2. 文件分配: 确保每个文件只被一个子任务修改 (避免并行冲突)
  3. 推荐策略: parallel / sequential / mixed
  4. 执行顺序和依赖关系
  5. 风险评估
```

**文件冲突规则**: 并行执行时，每个文件只能分配给一个 executor。如果多个子任务需要修改同一文件，这些子任务应串行执行。

### 步骤 3: 并行执行 (关键!)

**Plan agent 返回计划后，你必须使用 Task tool 调用 atlas-executor 来执行**:

#### 正确做法: 一次性发起所有并行调用

```
在同一条消息中发起多个 Task tool 调用:

Task 1:
  subagent_type: "atlas:atlas-executor"
  prompt: "执行子任务1: [描述] 涉及文件: [列表]"

Task 2:
  subagent_type: "atlas:atlas-executor"
  prompt: "执行子任务2: [描述] 涉及文件: [列表]"

Task 3:
  subagent_type: "atlas:atlas-executor"
  prompt: "执行子任务3: [描述] 涉及文件: [列表]"
```

#### 错误做法: 逐个调用 (禁止!)

```
❌ 不要这样:
调用 executor 执行子任务1
等待完成...
调用 executor 执行子任务2
等待完成...
```

### 步骤 4: 聚合并报告

收集所有 executor 返回的结果，生成最终报告:

```markdown
# Atlas 执行报告

## 任务总结
[描述]

## 执行统计
- 子任务: X 个
- 成功: Y / 失败: Z

## 修改的文件
- file1.ts
- file2.ts

## 失败详情 (如有)
- 子任务N: [原因] → [建议]

## 后续建议
- 运行测试验证
- 检查特定文件
```

## 执行示例

### 示例 1: 并行执行 (子任务独立)

```
用户: /orchestrate 给所有 React 组件添加 TypeScript 类型

执行流程:

1. Task tool → information-gatherer agent
   prompt: 收集项目中所有 React 组件的信息,包括文件位置、现有类型定义情况、组件结构
   返回: 发现 src/components 下有15个组件,分布在 auth/dashboard/shared 三个目录

2. Task tool → Plan agent
   prompt: 任务是给所有组件添加类型,信息收集发现15个组件...
   返回: 按目录分3组并行,策略: parallel

3. 同时发起3个 Task tool 调用 (同一条消息中):
   - Task(atlas:atlas-executor): 处理 auth 组件 (5个)
   - Task(atlas:atlas-executor): 处理 dashboard 组件 (5个)
   - Task(atlas:atlas-executor): 处理 shared 组件 (5个)

4. 聚合结果并报告
```

### 示例 2: 串行执行 (子任务有依赖)

```
用户: /orchestrate 重构数据库层,先改 schema 再改 repository

执行流程:

1. Task tool → information-gatherer agent
   prompt: 分析数据库层的结构,找出 schema 和 repository 的关系和依赖
   返回: schema 定义在 db/schema.ts,repository 在 db/repositories/ 下有5个文件依赖它

2. Task tool → Plan agent
   prompt: 重构数据库层,信息收集显示 repository 依赖 schema...
   返回: 2个子任务有依赖,策略: sequential

3. 第一步: Task(atlas:atlas-executor) 修改 schema
   等待完成...

4. 第二步: Task(atlas:atlas-executor) 修改 repository
   等待完成...

5. 聚合结果并报告
```

### 示例 3: 混合执行 (部分有依赖)

```
用户: /orchestrate 重构 auth 模块,先提取公共逻辑再更新各组件

执行流程:

1. Task tool → information-gatherer agent
   prompt: 分析 auth 模块的代码结构,找出重复的公共逻辑和所有使用它的组件
   返回: 发现 Login/Register/Profile 三个组件有重复的验证逻辑,建议提取到 auth-utils.ts

2. Task tool → Plan agent
   prompt: 重构 auth 模块,信息收集建议先提取公共逻辑...
   返回: 策略: mixed (阶段1串行提取,阶段2并行更新)

3. 阶段1 (串行): Task(atlas:atlas-executor) 提取公共逻辑到 auth-utils.ts
   等待完成...

4. 阶段2 (并行,同一条消息):
   - Task(atlas:atlas-executor): 更新 Login.tsx
   - Task(atlas:atlas-executor): 更新 Register.tsx
   - Task(atlas:atlas-executor): 更新 Profile.tsx

5. 聚合结果并报告
```

## 策略选择

| 策略 | 使用场景 | 执行方式 |
|------|----------|----------|
| parallel | 子任务相互独立，无共享文件 | 所有 Task 调用放在同一消息 |
| sequential | 子任务有依赖顺序，或修改同一文件 | 逐个调用,等待完成后继续 |
| mixed | 部分有依赖或共享文件 | 按阶段执行,阶段内并行 |
| --max-agents N | 控制并发数 | 每批最多 N 个 Task 调用 |

### 文件冲突处理

并行 executor 修改同一文件会导致冲突。处理方式：

1. **按文件分组**: 将修改同一文件的操作分配给同一个 executor
2. **串行化冲突任务**: 如果逻辑上必须分开，将这些任务改为串行执行
3. **分阶段执行**: 先完成可能产生共享依赖的任务，再并行执行后续任务

```
示例: 重构 utils.ts 并更新 3 个调用方

错误做法 ❌:
  并行执行 4 个 executor (1个改 utils.ts, 3个改调用方)
  → 调用方可能读到旧版 utils.ts

正确做法 ✓:
  阶段1: executor 修改 utils.ts
  阶段2: 并行 3 个 executor 更新调用方
```

## 特殊场景

### --dry-run
只调用 Plan agent，显示计划但不执行。

### 部分失败
继续执行其他独立子任务，最终统一报告所有结果。

## 行为约束

**必须做**:
1. 使用 Task tool 调用 agents (不能自己直接执行)
2. 并行任务在同一消息中一次性发起多个 Task 调用
3. 收集所有结果后统一报告

**禁止做**:
1. 自己直接修改文件 (必须由 executor 完成)
2. 串行调用可并行的任务
3. 因部分失败放弃其他任务
