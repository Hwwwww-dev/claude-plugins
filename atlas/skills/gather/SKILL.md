---
name: information-gathering-workflow
description: 智能信息收集工作流。当需要分析项目结构、梳理依赖关系、探索代码库时使用。触发词："分析项目"、"梳理依赖"、"代码库探索"、"收集信息"等
color: orange
---

# 信息收集工作流

## 何时使用

当用户需要快速理解代码库时自动触发：
- "分析项目结构"
- "梳理所有依赖"
- "探索代码库"
- "收集项目信息"
- "生成项目文档"

## 工作流程

### 第 1 步：明确收集任务

将用户的需求转化为明确的信息收集指令，包括：
- **分析范围**：整个项目 / 特定目录 / 特定模块
- **收集目标**：结构分析 / 依赖关系 / 代码模式 / 影响范围
- **输出要求**：详细程度、是否需要缓存

示例任务描述：
```
任务: 分析项目代码结构
范围: 整个项目
目标:
  - 文件和目录组织
  - 核心模块清单
  - 关键符号列表
输出: 结构化 Markdown 报告
缓存: 保存到 Memory (project-structure-v1.md)
```

### 第 2 步：调用 Information Gatherer

使用 Task tool 调用 `atlas-information-gatherer` agent：

```python
Task(
    subagent_type="atlas-information-gatherer",
    description="收集项目信息",
    prompt="""
任务: [明确的收集任务]
范围: [具体的路径或范围]
目标: [列出具体的收集目标]
输出要求: [详细程度、格式]
缓存: [是否需要保存到 Memory，以及文件名]

请按照以上要求收集信息并生成报告。
"""
)
```

### 第 3 步：展示分析结果

将 Information Gatherer 返回的报告展示给用户，并说明：
- 收集的信息范围
- 主要发现和洞察
- 缓存位置（如果已保存到 Memory）
- 如何使用这些信息进行后续操作

### 第 4 步：后续建议

基于收集到的信息，为用户提供后续行动建议：

**如果是项目结构分析**：
- 建议关注的核心模块
- 可能的修改影响范围
- 是否需要进一步深度分析

**如果是依赖关系梳理**：
- 关键的调用链
- 修改某个符号的影响范围
- 是否需要使用 `/orchestrate` 进行批量修改

**如果是代码模式探索**：
- 识别出的设计模式
- 代码组织的最佳实践
- 潜在的改进机会

## 典型使用场景

### 场景 1：初次接触项目

**用户**：我刚接手这个项目，帮我分析一下项目结构

**执行**：
```
1. 明确任务：全面分析项目代码结构
2. 调用 Information Gatherer
3. 展示结构化报告（目录组织、模块清单、文件统计）
4. 建议：关注 src/components/ 和 src/services/ 核心模块
```

### 场景 2：准备重构

**用户**：我要重构 UserAPI，先帮我梳理一下它的依赖关系

**执行**：
```
1. 明确任务：分析 UserAPI 的所有引用点
2. 调用 Information Gatherer
3. 展示依赖报告（5 个引用位置、调用方式、影响分析）
4. 建议：使用 /orchestrate 命令批量更新这 5 个引用点
```

### 场景 3：技术债务评估

**用户**：找出所有使用旧版 API 的代码

**执行**：
```
1. 明确任务：搜索特定的代码模式（旧版 API 调用）
2. 调用 Information Gatherer
3. 展示匹配清单（15 个使用旧版 API 的位置）
4. 建议：制定迁移计划，使用 /orchestrate 进行批量更新
```

## 与其他工具的协同

### 与 /orchestrate 命令配合

```
信息收集工作流 → 识别需要修改的文件
  ↓
用户决策
  ↓
/orchestrate 命令 → 批量执行修改
```

### 与 Plan agent 配合

```
Plan agent 分析任务
  ↓
需要了解项目结构
  ↓
调用 Information Gatherer → 收集项目信息
  ↓
Plan agent 基于信息制定计划
```

### 与 Executor 配合

```
Information Gatherer → 分析并缓存项目结构到 Memory
  ↓
Plan agent → 分解任务
  ↓
多个 Executor agents → 从 Memory 读取缓存，快速执行
```

## 输出示例

Information Gatherer 会返回类似这样的报告：

```markdown
# 项目代码结构分析

## 📊 统计信息
- 总文件数: 45
- TypeScript 文件: 35
- React 组件: 12

## 📁 模块结构
### Components (12 files)
- Auth: Login, Register, Profile
- Dashboard: Overview, Analytics, Reports
- Shared: Button, Input, Modal

### Services (8 files)
- UserAPI, AuthAPI, DataAPI

## 💾 缓存信息
已保存到: project-structure-v1.md
```

你可以将这个报告展示给用户，并提供后续建议。

## 关键原则

✅ **必须做到**：
- 将用户需求转化为明确的收集任务
- 正确调用 Information Gatherer agent
- 展示和解释收集到的信息
- 提供有价值的后续建议

❌ **严格禁止**：
- 不代替 Information Gatherer 执行收集工作
- 不修改代码文件（这是 Executor 的职责）
- 不嵌套调用其他 Skill（Hooks 限制）

## 成本优化

通过 Memory 缓存实现成本最优：

```
第一次分析项目：成本 $10
  ↓
保存到 Memory
  ↓
后续 5 个任务复用缓存：成本 $0
  ↓
实际人均成本：$10 / 6 = $1.67
```

鼓励用户在项目初期进行一次全面的信息收集，后续任务都能复用这些缓存。
