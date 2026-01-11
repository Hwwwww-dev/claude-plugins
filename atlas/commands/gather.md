---
description: 智能信息收集命令。分析项目结构、依赖关系、代码模式,输出结构化报告。
argument-hint: <分析目标> [--scope path] [--depth N] [--output report|pkg]
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

| 步骤 | 自动模式 | 交互模式 |
|------|---------|---------|
| 收集模式 | 智能推断（默认 project-structure） | 询问用户 |
| 分析深度 | normal | 询问用户 |
| 分析范围 | all | 询问用户 |
| 输出格式 | report | report |

### 2.3 收集模式说明

| 模式 | 收集内容 |
|------|----------|
| `project-structure` | 文件统计、模块结构、关键文件、核心符号 |
| `dependencies` | 符号定位、引用位置、调用上下文、影响评估 |
| `code-patterns` | 匹配统计、详细清单、模式分析、使用建议 |
| `impact` | 直接引用点、间接影响、风险评估、修改建议 |

### 2.4 执行步骤

**Step 1: 分阶段确认选项**

**第一个 AskUserQuestion: 执行模式选择**

```
问题: 执行模式
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

**注意**: 如用户已指定参数（如 `/gather dependencies UserAPI --deep`），跳过所有询问。

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

### 示例 1: 自动模式 - 项目结构分析

```
用户: /gather project-structure

1. 第一个 AskUserQuestion - 执行模式:
   - 执行模式: 自动模式（推荐）✓

   [自动使用推荐配置，跳过第二个 AskUserQuestion]
   - 收集模式: project-structure（从命令参数推断）
   - 分析深度: normal
   - 分析范围: all

2. Gatherer: 分析项目结构
3. 输出:
   📊 信息收集完成
   模式: project-structure
   统计: 156 文件, 45 模块
   核心发现: src/services 包含 12 个服务类
```

### 示例 2: 交互模式 - 依赖分析

```
用户: /gather dependencies UserAPI

1. 第一个 AskUserQuestion - 执行模式:
   - 执行模式: 交互模式 ✓

2. 第二个 AskUserQuestion - 收集配置:
   - 收集模式: dependencies（从命令参数推断）✓
   - 分析深度: deep ✓
   - 分析范围: all ✓

3. Gatherer: 深度分析 UserAPI 依赖
4. 输出:
   📊 信息收集完成
   模式: dependencies
   目标: UserAPI
   统计: 23 个引用点, 8 个文件
```

### 示例 3: 参数完整指定（跳过所有询问）

```
用户: /gather dependencies UserAPI --deep

1. 跳过所有询问（参数已完整指定）
   - 执行模式: auto（默认）
   - 收集模式: dependencies
   - 目标: UserAPI
   - 分析深度: deep
   - 分析范围: all（默认）

2. Gatherer: 深度分析 UserAPI 依赖
3. 输出:
   📊 信息收集完成
   模式: dependencies
   目标: UserAPI
   统计: 23 个引用点, 8 个文件
```

### 示例 4: 与 /orchestrate 配合

```bash
/gather dependencies UserAPI           # 1. 分析引用点（自动模式）
/orchestrate 更新所有 UserAPI 调用    # 2. 基于收集结果批量执行
```

---

## 五、核心约束

### 必须做

- ✅ **Step 1**: 首先确认执行模式（自动/交互）
- ✅ **Step 1**: 自动模式跳过第二个 AskUserQuestion，使用推荐配置
- ✅ **Step 1**: 交互模式需要确认所有收集配置
- ✅ **Step 1**: 参数完整指定时跳过所有询问
- ✅ 使用 gatherer agent 执行收集
- ✅ 输出包含文件路径和行号
- ✅ 结果写入 `.claude/gather/`

### 禁止做

- ❌ 主进程直接读取代码
- ❌ 主进程直接分析
- ❌ 修改任何文件
- ❌ 跳过 gatherer 直接输出
- ❌ 在自动模式下仍然询问收集配置
