---
description: 代码审查命令。对指定范围的代码进行多维度自动化审查（安全、性能、风格、架构），支持自动修复。
argument-hint: [--scope path] [--type security|performance|style|architecture|all] [--fix] [--severity critical|warning|all]
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

| 步骤 | 默认值 | --fix 时 | 可选值 |
|------|--------|---------|--------|
| 审查类型 | all | all | security / performance / style / architecture / all |
| 严重性过滤 | all | all | critical / warning / all |
| 规划器 | - | 询问 | atlas:planner / 内置 Plan |
| Reviewer 模型 | 询问 | 询问 | haiku / sonnet / opus |
| Executor 模型 | - | 询问 | haiku / sonnet / opus |
| 测试节点 | - | 询问 | 修复后 / 不测试 |
| 测试模式 | - | 询问 | 编译测试 / 单元测试 / 编译+单元 |

### 2.3 审查类型

| 类型 | 检查项 |
|------|--------|
| `security` | SQL 注入、XSS、硬编码密钥、敏感信息泄露 |
| `performance` | N+1 查询、内存泄漏、不必要重渲染 |
| `style` | 命名规范、代码结构、一致性 |
| `architecture` | 分层违规、循环依赖、耦合度 |

### 2.4 执行步骤

**Step 1: 范围确定**
- 无 --scope: git diff（未提交变更）
- --scope .: 全项目
- --scope src: 指定目录

**Step 2: 确认选项**
```
AskUserQuestion: 选择 Reviewer 模型
- haiku: 快速审查
- sonnet（推荐）: 平衡
- opus: 深度审查

AskUserQuestion: (--fix) 选择规划器
- atlas:planner（推荐）: 信任 gatherer 输出
- 内置 Plan: 会自行探索

AskUserQuestion: (--fix) 选择 Executor 模型
- haiku / sonnet / opus

AskUserQuestion: (--fix) 选择测试节点
- 修复后（推荐）: 修复完成后测试
- 不测试: 跳过

AskUserQuestion: (--fix) 选择测试模式
- 编译测试 / 单元测试 / 编译+单元
```

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

### 示例 1: 基础审查

```
用户: /review --scope src/services

1. 范围确定: src/services (12 文件)
2. 确认选项: sonnet
3. Gatherer: 收集代码信息
4. 并行审查: 4 个 code-reviewer
5. 报告: 发现 3 critical, 5 warning
```

### 示例 2: 安全审查+修复

```
用户: /review --type security --fix

1. 范围确定: git diff (5 文件)
2. 确认选项: opus + 创建检查点 + 编译测试
3. Gatherer: 收集代码信息
4. 审查: 1 个 security reviewer
5. 报告: 2 个可自动修复的问题
6. Executor: 执行修复
7. 测试: tsc --noEmit ✅
```

---

## 五、核心约束

### 必须做

- ✅ 询问 Reviewer 模型选择
- ✅ --fix 时询问规划器和测试选项
- ✅ 使用 gatherer 收集代码信息
- ✅ 不同维度并行审查
- ✅ 问题包含文件路径和行号

### 禁止做

- ❌ 主进程直接读取代码
- ❌ 主进程直接修改文件
- ❌ 不使用 --fix 时自动修复
- ❌ autoFixable 判断不谨慎
