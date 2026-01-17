---
description: 代码审查命令。对指定范围的代码进行多维度自动化审查（安全、性能、风格、架构），支持自动修复。
argument-hint: [--scope path] [--type security|performance|style|architecture|all] [--fix] [--quick] [--severity critical|warning|all]
---

# /review - 代码审查

## 一、涉及的 Agent 和工具

### 1.1 Agent 说明

| Agent | 职责 | 模型 | 输出位置 |
|-------|------|------|---------|
| `atlas:information-gatherer` | 收集目标代码信息 | haiku | `.claude/gather/review-<ts>/` |
| `atlas:code-reviewer` | 执行单维度审查 | 用户选择 | 返回审查结果 JSON |
| `atlas:atlas-executor` | 执行自动修复 | 用户选择 | 直接修改文件 |

### 1.2 工具说明

| 工具 | 用途 |
|------|------|
| `AskUserQuestion` | 确认选项 |
| `Task` | 调用 subagent |
| `tsc` / `npm test` | 验证结果 |

### 1.3 信息传递链

```
gatherer → .claude/gather/review-<ts>/context.json
    ↓
code-reviewer → 读取 context.json → 输出审查结果 JSON
    ↓
主进程 → 聚合报告 → .claude/review/report-<date>.md
    ↓
[--fix] executor → 修复 autoFixable 问题
```

---

## 二、编排计划

### 2.1 强制流程

```
范围确定 → 确认选项 → 代码分析 → 并行审查 → 报告聚合 → [--fix] 修复 → 测试 → 输出
```

### 2.2 模式行为定义

| 步骤 | 快速模式 | 默认值 | --fix 时 | 可选值 |
|------|---------|--------|---------|--------|
| 信息收集 | **跳过** | 是 | 是 | 是 / 否 |
| 审查类型 | 用户指定 | all | all | security / performance / style / architecture / all |
| 严重性过滤 | all | all | all | critical / warning / all |
| 规划器 | **跳过** | - | 询问 | atlas:planner / 内置 Plan |
| Reviewer 模型 | **haiku** | 询问 | 询问 | haiku / sonnet / opus |
| Executor 模型 | - | - | 询问 | haiku / sonnet / opus |
| 测试节点 | **跳过** | - | 询问 | 修复后 / 不测试 |
| 测试模式 | - | - | 询问 | 编译测试 / 单元测试 / 编译+单元 |
| 状态文件 | **创建** | 创建 | 创建 | - |

### 2.3 审查类型

| 类型 | 检查项 |
|------|--------|
| `security` | SQL 注入、XSS、硬编码密钥、敏感信息泄露 |
| `performance` | N+1 查询、内存泄漏、不必要重渲染 |
| `style` | 命名规范、代码结构、一致性 |
| `architecture` | 分层违规、循环依赖、耦合度 |

### 2.4 执行模式选择

**第一个 AskUserQuestion: 执行模式选择**

```
问题: 执行模式
- 快速模式: 跳过信息收集，直接审查（适合单文件或小范围审查，~3分钟）
- 标准模式（推荐）: 使用 gatherer 收集信息后审查
```

### 2.5 执行步骤

**Step 1: 范围确定**
- 无 --scope: git diff（未提交变更）
- --scope .: 全项目
- --scope src: 指定目录

**Step 2: 分阶段确认选项**

**第二个 AskUserQuestion: Reviewer 模型选择（仅标准模式）**

```
问题: Reviewer 模型
- haiku: 快速审查，适合简单检查
- sonnet（推荐）: 平衡性能与成本
- opus: 深度审查，复杂代码质量要求高
```

**第二个 AskUserQuestion: 修复配置（仅 --fix 时）**

如果用户使用了 **--fix** 参数，询问修复配置：

```
问题 1: 规划器选择
- atlas:planner（推荐）: 信任 gatherer 输出，最小化扫描
- 内置 Plan: 会自行探索验证

问题 2: Executor 模型
- haiku: 快速简单修复
- sonnet（推荐）: 平衡性能与成本
- opus: 复杂修复质量要求高
```

**第三个 AskUserQuestion: 测试配置（仅 --fix 时）**

如果用户使用了 **--fix** 参数，询问测试配置：

```
问题 1: 测试节点
- 修复后（推荐）: 修复完成后测试
- 不测试: 跳过验证

问题 2: 测试模式
- 编译测试（推荐）: tsc --noEmit 确保语法正确
- 单元测试: npm test 确保功能正常
- 编译+单元: 完整验证
```

**注意**:
- 快速模式跳过所有询问，直接进入审查流程
- 只有标准模式使用 --fix 时才会询问第三个和第四个 AskUserQuestion
- 如果不使用 --fix，只询问 Reviewer 模型，直接进入审查流程

---

### 2.6 快速模式流程（--quick）

**适用场景**：
- 审查 1-3 个文件
- 快速检查特定代码片段

**流程**：
```
确认模式 → 主进程快速定位 → 直接审查 → 简化报告
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
  "currentStage": "quick_review",
  "config": {"mode": "quick", "reviewerModel": "haiku"}
}' > .claude/orchestrate/.state/<task-id>.json
```

**Step Q3: 主进程快速定位**
```
主进程允许使用 Grep/Glob/Read 快速定位目标文件（≤5 次工具调用）
直接构建 code-reviewer prompt
```

**Step Q4: 直接审查**
```
Task(subagent_type="atlas:code-reviewer", model="haiku")
prompt: |
  审查维度: [用户指定或 all]
  目标文件: [主进程定位的文件]
  代码片段: [主进程读取的代码]
  注意: 快速模式，输出简化报告
```

**Step Q5: 简化报告**
```markdown
# 快速审查完成

**执行 ID**: <task-id>
**状态文件**: .claude/orchestrate/.state/<task-id>.json
**范围**: [文件列表]
**审查类型**: [security/performance/style/architecture/all]
**发现问题**: X critical, Y warning

[问题列表]

[如果有 autoFixable] 建议: 使用 `/review --fix` 自动修复
```

**快速模式风险提示**：
- 跳过 gatherer：可能遗漏上下文依赖；且不支持 `--fix`（需标准模式）
- 失败建议切换标准模式重新执行

---

### 2.7 标准模式执行步骤

**Step 3: 代码分析**
```
Task(subagent_type="atlas:information-gatherer", model="haiku")
prompt: |
  任务 ID: review-<timestamp>
  目标文件: [文件列表]
  输出目录: .claude/gather/review-<timestamp>/
```

**Step 4: 并行审查**
```
Task(subagent_type="atlas:code-reviewer", model=用户选择)
prompt: |
  审查维度: [security/performance/style/architecture]
  Gatherer 输出: .claude/gather/review-<timestamp>/
```

--type all: 并行启动 4 个 code-reviewer

**Step 5: 报告聚合**
- 合并各维度结果
- 按严重性排序
- 输出 `.claude/review/report-<date>.md`

**Step 6: (--fix) 自动修复**
```
Task(subagent_type="atlas:atlas-executor", model=用户选择)
prompt: |
  修复任务: autoFixable=true 的问题
  修改点: [从审查结果提取]
```

**Step 7: (--fix) 验证测试**（根据 Step 2 选择执行）

**Step 8: 输出报告**

---

## 三、细节要点

### 3.1 主进程职责

**允许**: AskUserQuestion / Task 调用 / 读取 agent 输出 / 聚合报告

**禁止**: Read/Grep/Glob 读代码 / Edit/Write 修改文件 / 直接分析代码

### 3.2 审查结果格式

每个 code-reviewer 输出：
```json
{
  "dimension": "security",
  "issues": [
    {
      "ruleId": "SEC001",
      "severity": "critical",
      "file": "src/api.ts",
      "line": 45,
      "message": "SQL 注入风险",
      "suggestion": "使用参数化查询",
      "autoFixable": true,
      "fixedCode": "..."
    }
  ],
  "summary": {"critical": 1, "warning": 2, "info": 0}
}
```

---

## 四、示例

### 示例 1: 快速审查（~3分钟）

```
用户: /review --scope src/api/user.ts --quick
1. AskUserQuestion: 执行模式 → 用户选择"快速模式"
2. 主进程定位: Glob 匹配 → Read 读取 user.ts (156 行)
3. Task(code-reviewer, haiku): 审查维度 all
4. 审查结果: security=0, performance=1, style=2, architecture=0
5. 输出简化报告 → warning: 1 (N+1 查询风险 L45-52)
6. 建议: 使用 `/review --fix` 自动修复
```

### 示例 2: 安全审查+修复

```
用户: /review --type security --fix
1. AskUserQuestion: 执行模式 → 用户选择"标准模式"
2. AskUserQuestion: Reviewer 模型 → opus (深度安全审查)
3. AskUserQuestion: 规划器 → atlas:planner / Executor 模型 → sonnet
4. AskUserQuestion: 测试配置 → 修复后 + 编译测试
5. Task(gatherer): 收集 → Task(code-reviewer, opus): 发现 2 critical (autoFixable)
6. Task(executor, sonnet): 修复 SQL 注入(L45) + XSS 漏洞(L89)
7. 验证: tsc --noEmit ✓ → 输出报告 → critical: 0, fixed: 2
```

---

## 五、核心约束

### 标准模式必须做

- ✅ 确认模式与 reviewer 模型；`--fix` 时确认规划器/测试
- ✅ gatherer 收集 → 多维度 reviewer 并行 → 聚合报告
- ✅ 问题必须包含文件路径与行号（autoFixable 慎标）

### 快速模式必须做

- ✅ 创建状态文件；主进程≤5次定位；reviewer(haiku) 审查；输出简报

### 快速模式允许做

- ✅ 主进程使用 Grep/Glob/Read 快速定位文件（≤5 次）
- ✅ 主进程直接构建 code-reviewer prompt（不调用 gatherer）
- ✅ 跳过检查点

### 禁止做

- ❌ 主进程直接读取代码（标准模式）
- ❌ 主进程直接修改文件
- ❌ 不使用 --fix 时自动修复
- ❌ autoFixable 判断不谨慎
- ❌ 快速模式使用 --fix（需切换到标准模式）
- ❌ 快速模式用于复杂审查（>3 个文件或需要依赖分析）
