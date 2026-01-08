---
description: 智能重构命令。识别代码问题并执行特定模式的自动化重构，支持预览和交互式确认。
argument-hint: <pattern> [--scope path] [--dry-run] [--interactive]
---

# /refactor - 智能重构命令

## 一、涉及的 Agent 和工具

### 1.1 Agent 说明

| Agent | 职责 | 模型 | 输出位置 |
|-------|------|------|---------|
| `atlas:information-gatherer` | 识别符合模式的候选项 | haiku | `.claude/gather/refactor-<ts>/` |
| `atlas:planner` | 制定重构计划 | inherit | `.claude/plan/refactor-<ts>/` |
| `atlas:atlas-executor` | 执行重构 | 用户选择 | 直接修改文件 |

### 1.2 工具说明

| 工具 | 用途 |
|------|------|
| `AskUserQuestion` | 确认选项 |
| `Task` | 调用 subagent |
| `tsc` / `npm test` | 验证结果 |

### 1.3 信息传递链

```
gatherer → .claude/gather/refactor-<ts>/context.json
    ↓
planner → .claude/plan/refactor-<ts>/plan.json
    ↓
executor → 直接重构（无需重新扫描）
```

---

## 二、编排计划

### 2.1 强制流程

```
模式解析 → 确认选项 → 候选识别 → 规划 → 执行/预览 → 测试 → 报告
```

### 2.2 模式行为定义

| 步骤 | 默认值 | --dry-run | --interactive | 可选值 |
|------|--------|-----------|---------------|--------|
| 候选识别 | 是 | 是 | 是 | 是 / 否 |
| 规划器 | 询问 | atlas:planner | 询问 | atlas:planner / 内置 Plan |
| Executor 模型 | 询问 | - | 询问 | haiku / sonnet / opus |
| 测试节点 | 询问 | - | 询问 | 每个候选后 / 统一测试 / 不测试 |
| 测试模式 | 询问 | - | 询问 | 编译测试 / 单元测试 / 编译+单元 |

### 2.3 支持的重构模式

| 模式 | 说明 | 识别条件 |
|------|------|---------|
| `extract-method` | 提取长函数 | 函数体 >50 行 |
| `extract-component` | 提取大组件 | JSX >100 行 |
| `consolidate-duplicate` | 合并重复代码 | 相似度 >80% |
| `modernize-js` | JS 现代化 | var/callback |
| `add-types` | 添加 TS 类型 | any/缺失类型 |
| `rename-convention` | 统一命名 | 命名不一致 |
| `simplify-conditions` | 简化条件 | if-else >3 层 |
| `remove-dead-code` | 移除死代码 | 未使用的导出 |

### 2.4 执行步骤

**Step 1: 模式解析**
- 验证 pattern 是否支持
- 解析 --scope 确定范围

**Step 2: 确认选项**
```
AskUserQuestion: 选择规划器
- atlas:planner（推荐）: 信任 gatherer 输出
- 内置 Plan: 会自行探索

AskUserQuestion: 选择 Executor 模型
- haiku: 快速，简单重构
- sonnet（推荐）: 平衡
- opus: 复杂重构

AskUserQuestion: 选择测试节点
- 每个候选后: 每个重构完成后立即测试
- 统一测试（推荐）: 全部完成后测试
- 不测试: 跳过

AskUserQuestion: 选择测试模式
- 编译测试（推荐）: tsc --noEmit
- 单元测试: npm test
- 编译+单元: 完整验证
```

**Step 3: 候选识别**
```
Task(subagent_type="atlas:information-gatherer", model="haiku")
prompt: |
  任务 ID: refactor-<timestamp>
  重构模式: [pattern]
  范围: [scope]
  输出目录: .claude/gather/refactor-<timestamp>/
```

**Step 4: 规划**
```
Task(subagent_type="atlas:planner" 或 "Plan")
prompt: |
  任务: 重构模式 [pattern]
  Gatherer 输出: .claude/gather/refactor-<timestamp>/
  输出目录: .claude/plan/refactor-<timestamp>/
```

**Step 5: 执行/预览**

| 模式 | 行为 |
|------|------|
| --dry-run | 输出预览报告，不修改 |
| --interactive | 逐个确认后执行 |
| 默认 | 并行执行所有子任务 |

```
Task(subagent_type="atlas:atlas-executor", model=用户选择)
prompt: |
  重构子任务: #N
  修改点: [从 plan.json 提取]
```

**Step 6: 验证测试**（根据 Step 2 选择执行）

**Step 7: 输出报告**

---

## 三、细节要点

### 3.1 主进程职责

**允许**: AskUserQuestion / Task 调用 / 读取 agent 输出 / 运行验证命令

**禁止**: Read/Grep/Glob 读代码 / Edit/Write 修改文件 / 直接分析代码

### 3.2 候选识别输出

gatherer 的 context.json 必须包含：
```json
{
  "candidates": [
    {
      "id": 1,
      "file": "src/services/UserService.ts",
      "symbol": "processOrder",
      "line": 45,
      "reason": "函数体 89 行",
      "codeSnippet": "..."
    }
  ]
}
```

### 3.3 模式约束

- 只执行指定模式的重构
- 不"顺便"做其他优化
- 保持现有代码风格

---

## 四、示例

### 示例 1: 预览模式

```
用户: /refactor extract-method --dry-run

1. 模式解析: extract-method
2. Gatherer: 识别长函数候选项
3. Planner: 生成重构计划
4. 输出预览:
   📋 重构预览
   模式: extract-method | 候选数: 5
   变更预览: processOrder → 拆分为 3 个函数
```

### 示例 2: 交互模式

```
用户: /refactor add-types --scope src/services --interactive

1. 确认选项: atlas:planner + sonnet + 编译测试
2. Gatherer: 识别缺少类型的位置
3. Planner: 生成计划
4. 逐个确认执行
5. 测试: tsc --noEmit ✅
```

### 示例 3: 直接执行

```
用户: /refactor modernize-js --scope src

1. 确认选项: atlas:planner + sonnet + 统一测试 + 编译+单元
2. Gatherer: 识别旧语法
3. Planner: 生成计划
4. Executor: 并行执行
5. 测试: tsc --noEmit && npm test ✅
6. 报告
```

---

## 五、核心约束

### 必须做

- ✅ 询问规划器选择
- ✅ 询问测试选项（节点+模式）
- ✅ 使用 gatherer 识别候选项
- ✅ 使用 planner 输出精确修改点
- ✅ 按选择执行测试

### 禁止做

- ❌ 主进程直接读取代码
- ❌ 主进程直接修改文件
- ❌ 跳过候选识别直接规划
- ❌ executor 重新扫描文件
- ❌ "顺便"做其他优化
