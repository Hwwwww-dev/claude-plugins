---
description: 问题诊断与修复建议。分析问题根因，提供修复方案，可选执行修复。
argument-hint: <问题描述> [--scope path] [--fix]
---

# /bugfix - 问题诊断与修复

## 一、涉及的 Agent 和工具

### 1.1 Agent 说明

| Agent | 职责 | 模型 | 输出位置 |
|-------|------|------|---------|
| `atlas:information-gatherer` | 收集问题相关信息 | haiku | `.claude/gather/bugfix-<ts>/` |
| `atlas:planner` | 制定修复方案 | inherit | `.claude/plan/bugfix-<ts>/` |
| `atlas:atlas-executor` | 执行修复 | 用户选择 | 直接修改文件 |

### 1.2 工具说明

| 工具 | 用途 |
|------|------|
| `AskUserQuestion` | 确认选项 |
| `Task` | 调用 subagent |
| `git stash` | 创建检查点 |

### 1.3 信息传递链

```
gatherer → .claude/gather/bugfix-<ts>/context.json
    ↓
planner → .claude/plan/bugfix-<ts>/plan.json
    ↓
executor → 直接修复（无需重新扫描）
```

---

## 二、编排计划

### 2.1 强制流程

```
问题分析 → 确认选项 → 信息收集 → 根因分析 → 规划 → [--fix] 执行 → 测试 → 报告
```

### 2.2 模式行为定义

| 步骤 | 默认值 | --fix 时 | 可选值 |
|------|--------|---------|--------|
| 信息收集 | 是 | 是 | 是 / 否 |
| 检查点 | - | 询问 | 创建 / 跳过 |
| 规划器 | atlas:planner | 询问 | atlas:planner / 内置 Plan |
| Executor 模型 | - | 询问 | haiku / sonnet / opus |
| 测试节点 | - | 询问 | 修复后 / 不测试 |
| 测试模式 | - | 询问 | 编译测试 / 单元测试 / 编译+单元 |

### 2.3 执行步骤

**Step 1: 问题分析**
- 理解问题现象
- 确定问题类型（运行时/逻辑/配置/依赖）
- 确定搜索范围

**Step 2: (--fix) 确认选项**
```
AskUserQuestion: 确认执行修复？
- 执行修复: 诊断后执行
- 仅诊断: 只输出方案

AskUserQuestion: 是否创建检查点？
- 创建（推荐）: 失败可回滚
- 跳过: 不创建

AskUserQuestion: 选择规划器
- atlas:planner（推荐）: 信任 gatherer 输出
- 内置 Plan: 会自行探索

AskUserQuestion: 选择 Executor 模型
- haiku: 快速，简单修复
- sonnet（推荐）: 平衡
- opus: 复杂修复

AskUserQuestion: 选择测试节点
- 修复后（推荐）: 修复完成后测试
- 不测试: 跳过

AskUserQuestion: 选择测试模式
- 编译测试（推荐）: tsc --noEmit
- 单元测试: npm test
- 编译+单元: 完整验证
```

**Step 3: 信息收集**
```
Task(subagent_type="atlas:information-gatherer", model="haiku")
prompt: |
  任务 ID: bugfix-<timestamp>
  问题描述: [用户问题]
  搜索范围: [scope]
  输出目录: .claude/gather/bugfix-<timestamp>/
```

**Step 4: 根因分析**（基于 gatherer 报告）

**Step 5: 制定修复方案**
```
Task(subagent_type="atlas:planner" 或 "Plan")
prompt: |
  任务: 修复 [问题描述]
  Gatherer 输出: .claude/gather/bugfix-<timestamp>/
  输出目录: .claude/plan/bugfix-<timestamp>/
```

**Step 6: (--fix) 执行修复**
```
Task(subagent_type="atlas:atlas-executor", model=用户选择)
prompt: |
  修复任务: [描述]
  修改点: [从 plan.json 提取]
```

**Step 7: (--fix) 验证测试**（根据 Step 2 选择执行）

**Step 8: 输出报告**

---

## 三、细节要点

### 3.1 主进程职责

**允许**: AskUserQuestion / Task 调用 / 读取 agent 输出 / Git 操作

**禁止**: Read/Grep/Glob 读代码 / Edit/Write 修改文件 / 直接分析代码

### 3.2 根因分析输出格式

```markdown
## 问题诊断
**问题描述**: [用户描述]
**问题类型**: [错误类型]
**复杂度**: simple | moderate | complex

## 根因分析
**定位**: [文件:行号]
**原因**: [具体原因]
**影响**: [影响范围]

## 修复方案
**策略**: [直接修复/防御性修复/重构]
**步骤**: 1. [步骤] - [文件:位置]
**验证**: [验证方法]
**风险**: [潜在风险]
```

---

## 四、示例

### 示例 1: 仅诊断

```
用户: /bugfix 登录按钮点击无反应

1. 问题分析: 事件绑定问题
2. Gatherer: 收集登录组件代码
3. 根因分析: src/components/Login.tsx:45 onClick 未绑定
4. 输出修复方案
```

### 示例 2: 诊断+修复

```
用户: /bugfix 用户数据丢失 --fix

1. 确认选项: 执行 + 创建检查点 + opus + 编译+单元测试
2. Gatherer: 收集 UserService 代码
3. 根因分析: 并发竞态条件
4. Planner: 生成修复计划
5. Executor: 执行修复
6. 测试: tsc --noEmit && npm test ✅
7. 报告
```

---

## 五、核心约束

### 必须做

- ✅ 使用 gatherer 收集信息
- ✅ 基于 gatherer 报告做根因分析
- ✅ --fix 时询问规划器选择
- ✅ --fix 时询问测试选项
- ✅ 使用 planner 输出精确修改点

### 禁止做

- ❌ 主进程直接读取代码
- ❌ 主进程直接修改文件
- ❌ 跳过信息收集直接分析
- ❌ executor 重新扫描文件
