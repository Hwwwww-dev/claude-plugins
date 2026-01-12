---
description: 智能信息收集命令。分析项目结构、依赖关系、代码模式,输出结构化报告。
argument-hint: <分析目标> [--quick] [--scope path] [--depth N] [--output report|pkg]
---

# /gather - 信息收集

## 一、涉及的 Agent 和工具

### 1.1 Agent 说明

| Agent | 职责 | 模型 | 输出位置 |
|-------|------|------|---------|
| `atlas:information-gatherer` | 执行信息收集 | haiku | `.claude/gather/<task-id>/` |

### 1.2 工具说明

| 工具 | 用途 |
|------|------|
| `AskUserQuestion` | 确认收集选项 |
| `Task` | 调用 subagent |

### 1.3 信息传递链

```
gatherer → .claude/gather/<task-id>/
    ├── report.md      # 人类可读报告
    └── context.json   # 结构化数据（供后续命令使用）
```

---

## 二、编排计划

### 2.1 强制流程

```
确认执行模式 → 确认收集配置（交互模式） → 调用 gatherer → 输出摘要
```

### 2.2 模式行为定义

| 步骤 | 快速模式 | 自动模式 | 交互模式 |
|------|---------|---------|---------|
| 收集模式 | 智能推断 | 智能推断（默认 project-structure） | 询问用户 |
| 分析深度 | normal | normal | 询问用户 |
| 分析范围 | all | all | 询问用户 |
| 信息收集 | **主进程直接分析** | gatherer agent | gatherer agent |
| 状态文件 | 创建 | 创建 | 创建 |
| 输出格式 | 简化报告 | report | report |

### 2.3 收集模式说明

| 模式 | 收集内容 |
|------|----------|
| `project-structure` | 文件统计、模块结构、关键文件、核心符号 |
| `dependencies` | 符号定位、引用位置、调用上下文、影响评估 |
| `code-patterns` | 匹配统计、详细清单、模式分析、使用建议 |
| `impact` | 直接引用点、间接影响、风险评估、修改建议 |

### 2.4 执行模式选择

**第一个 AskUserQuestion: 执行模式选择**

```
问题: 执行模式
- 快速模式: 主进程直接收集，不调用 agent（适合单文件或小范围分析，~2分钟）
- 自动模式（推荐）: 使用推荐选项，减少交互
- 交互模式: 每个选项都需要确认
```

**第二个 AskUserQuestion: 收集配置（仅交互模式）**

如果用户选择了**交互模式**，询问收集配置：

```
问题 1: 收集模式
- project-structure: 项目结构分析
- dependencies: 依赖关系梳理
- code-patterns: 代码模式搜索
- impact: 修改影响分析

问题 2: 分析深度
- normal（推荐）: 标准分析
- deep: 深度分析，更详细

问题 3: 分析范围
- all（推荐）: 整个项目
- specific: 指定目录/文件
```

**自动模式行为**（跳过第二个 AskUserQuestion）：
- 收集模式: 根据用户任务描述智能推断（如未明确，默认 project-structure）
- 分析深度: normal
- 分析范围: all

**快速模式行为**（跳过第二个 AskUserQuestion）：
- 收集模式: 根据用户任务描述智能推断
- 分析深度: normal
- 分析范围: all
- 信息收集: 主进程直接分析（不调用 gatherer agent）
- 状态文件: 创建

**注意**: 如用户已指定参数（如 `/gather dependencies UserAPI --deep`），跳过所有询问。

---

### 2.5 快速模式流程（--quick）

**适用场景**：
- 分析 1-3 个文件
- 快速了解特定符号或模式

**流程**：
```
确认模式 → 创建状态文件 → 主进程直接分析 → 更新状态 → 简化报告
```

**Step Q1: 确认快速模式**
```
AskUserQuestion:
问题: 执行模式
- 快速模式 ✓
```

**Step Q2: 创建状态文件**
```bash
mkdir -p .claude/orchestrate/.state
echo '{
  "executionId": "<task-id>",
  "timestamp": "<ISO-8601>",
  "task": "<用户任务>",
  "status": "in_progress",
  "currentStage": "quick_gather",
  "config": { "mode": "quick" }
}' > .claude/orchestrate/.state/<task-id>.json
```

**Step Q3: 主进程直接分析**
```
主进程允许使用 Grep/Glob/Read/LSP 直接分析（≤5 次工具调用）
直接收集目标信息，不调用 gatherer agent
```

**Step Q4: 输出简化报告**
```markdown
# 快速收集完成

**执行 ID**: <task-id>
**状态文件**: .claude/orchestrate/.state/<task-id>.json
**模式**: [收集模式]
**目标**: [目标符号/模式]
**统计**: [关键数字]

**核心发现**:
- [发现1]
- [发现2]

[如需深度分析] 建议: 使用自动模式 `/gather <目标>`
```

**快速模式风险提示**：
- 跳过深度依赖分析，可能遗漏间接引用
- 如果分析不充分，建议用户切换到自动模式

---

### 2.6 标准模式执行步骤

**Step 1: 分阶段确认选项**

（见 2.4 执行模式选择）

**Step 2: 调用 information-gatherer**
```
Task(subagent_type="atlas:information-gatherer", model="haiku")
prompt: |
  任务 ID: <mode>-<target>-<date>
  收集模式: [选择的模式]
  目标: [符号名/模式/目录]
  范围: [all/指定路径]
  深度: [normal/deep]
  输出目录: .claude/gather/<task-id>/
```

**Step 3: 输出摘要**

---

## 三、细节要点

### 3.1 主进程职责

**允许**: AskUserQuestion / Task 调用 / 输出摘要

**禁止**: Read/Grep/Glob 读代码 / 直接分析 / 修改文件

### 3.2 项目知识库

优先从 `.claude/repowiki/` 获取已有信息：

| 文件 | 用途 |
|------|------|
| `project.pkg.json` | 项目元数据、技术栈 |
| `modules.pkg.json` | 模块结构、依赖关系 |
| `symbols.pkg.json` | 符号索引 |

gatherer 会自动检查并复用这些文件。

### 3.3 输出格式

```markdown
📊 信息收集完成

**模式**: [收集模式]
**目标**: [目标符号/模式]
**统计**: [关键数字]

**核心发现**:
- [发现1]
- [发现2]

💾 **详细报告**: .claude/gather/<task-id>/report.md

🔜 **后续建议**: 如需批量修改可使用 /orchestrate
```

---

## 四、示例

### 示例 1: 快速模式（~2分钟）

```
用户: /gather dependencies UserAPI --quick

1. 选择快速模式 → 跳过所有后续询问
2. 主进程快速定位:
   - LSP findReferences "UserAPI" → 定位 src/api/UserAPI.ts
   - Grep "UserAPI" → 扫描引用点
   - 分析调用上下文（≤5 次工具调用）
3. 输出简化报告: 23 个引用点, 8 个文件
4. 提示: 如需深度分析，使用 `/gather dependencies UserAPI`
```

### 示例 2: 自动模式 - 项目结构分析

```
用户: /gather project-structure

1. 选择自动模式 → 使用推荐配置（normal 深度 + all 范围）
2. Gatherer(haiku): 执行项目结构分析
   - Glob "**/*.{ts,tsx}" → 统计文件分布
   - LSP documentSymbol → 提取核心符号
   - 分析模块依赖关系
3. 输出: .claude/gather/project-structure-20240115/
   - report.md: 156 文件, 45 模块, 12 入口点
   - context.json: 结构化数据（供后续命令使用）
```

### 示例 3: 交互模式 - 依赖分析

```
用户: /gather dependencies UserAPI

1. 选择交互模式 → 确认配置:
   - 收集模式: dependencies | 深度: deep | 范围: all
2. Gatherer(haiku): 深度分析 UserAPI 依赖
   - LSP findReferences → 23 个直接引用
   - LSP incomingCalls → 追踪调用链
   - 分析影响范围和风险等级
3. 输出: .claude/gather/dependencies-UserAPI-20240115/
   - report.md: 23 引用点, 8 文件, 3 高风险调用
   - context.json: 引用详情（文件路径 + 行号）
```

### 示例 4: 与 /orchestrate 配合

```
用户: /gather dependencies UserAPI
      /orchestrate 更新所有 UserAPI 调用

1. /gather 输出: .claude/gather/dependencies-UserAPI-20240115/context.json
2. /orchestrate 自动读取 context.json → 跳过重复收集
3. Planner 基于已有数据生成计划 → 节省 ~5 分钟
```

---

## 五、核心约束

### 标准模式必须做

- ✅ **Step 1**: 首先确认执行模式（快速/自动/交互）
- ✅ **Step 1**: 自动模式跳过第二个 AskUserQuestion，使用推荐配置
- ✅ **Step 1**: 交互模式需要确认所有收集配置
- ✅ **Step 1**: 参数完整指定时跳过所有询问
- ✅ 使用 gatherer agent 执行收集
- ✅ 输出包含文件路径和行号
- ✅ 结果写入 `.claude/gather/`

### 快速模式必须做

- ✅ **Step Q1**: 确认用户选择快速模式
- ✅ **Step Q2**: 创建状态文件
- ✅ **Step Q3**: 主进程直接分析（≤5 次工具调用）
- ✅ **Step Q4**: 输出简化报告（包含执行 ID 和状态文件路径）
- ✅ 分析不充分时建议用户切换到自动模式

### 快速模式允许做

- ✅ 主进程使用 Grep/Glob/Read/LSP 直接分析（≤5 次）
- ✅ 跳过 gatherer agent 调用

### 禁止做

- ❌ 标准模式主进程直接读取代码
- ❌ 标准模式主进程直接分析
- ❌ 修改任何文件
- ❌ 标准模式跳过 gatherer 直接输出
- ❌ 在自动模式下仍然询问收集配置
- ❌ 快速模式用于复杂任务（>3 个文件或需要深度依赖分析）
