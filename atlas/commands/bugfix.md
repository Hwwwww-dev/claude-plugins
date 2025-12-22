---
description: 问题诊断与修复建议。分析问题根因，提供修复方案，可选执行修复。
argument-hint: <问题描述> [--scope path] [--fix]
---

# /bugfix - 问题诊断与修复建议

用户问题: $ARGUMENTS

---

## 诊断流程

### 1. 问题分析
- 理解用户描述的问题现象
- 确定问题类型（运行时错误/逻辑错误/配置问题/依赖问题等）
- 确定搜索范围（--scope 指定或根据问题推断）

### 2. 信息收集

**调用 `information-gatherer` 收集信息**：

```
Task(
  subagent_type="atlas:information-gatherer",
  model="haiku",
  prompt="问题诊断信息收集：

  问题描述: [用户问题]
  搜索范围: [scope 或推断范围]

  收集目标:
  1. 相关代码文件和函数定位
  2. 错误相关的代码逻辑
  3. 依赖关系和调用链
  4. 相关配置文件
  5. git blame 最近修改历史

  输出要求:
  - 问题相关的关键代码片段
  - 可能的问题位置列表
  - 相关依赖和版本信息"
)
```

等待 gatherer 返回信息后，基于收集的信息继续分析。

### 3. 根因分析
- 定位问题根本原因
- 分析影响范围
- 评估复杂度（simple/moderate/complex）

### 4. 修复方案
提供具体的修复建议：
- 修复策略（直接修复/防御性修复/重构）
- 修改位置和内容
- 验证方法
- 潜在风险

---

## 输出格式

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

**策略**: [修复策略]

**步骤**:
1. [步骤1] - [文件:位置]
2. [步骤2] - [文件:位置]

**验证**:
- [验证方法]

**风险**:
- [潜在风险及应对]
```

---

## --fix 执行修复

当用户指定 `--fix` 时，诊断完成后询问是否执行：

```
AskUserQuestion(questions=[
  {
    "question": "确认执行修复？",
    "header": "确认",
    "options": [
      {"label": "执行修复", "description": "按方案执行"},
      {"label": "仅查看方案", "description": "不执行"}
    ]
  }
])
```

**用户确认执行后**，在调用 `atlas:atlas-executor` 前选择模型：

```
AskUserQuestion(questions=[
  {
    "question": "选择 executor 模型",
    "header": "模型",
    "options": [
      {"label": "sonnet (推荐)", "description": "平衡速度和质量"},
      {"label": "haiku", "description": "快速，适合简单修复"},
      {"label": "opus", "description": "高质量，适合复杂修复"}
    ]
  }
])
```

执行流程：
```
1. 创建检查点: git stash push -m "bugfix-checkpoint-{timestamp}"
2. Task(subagent_type="atlas:atlas-executor", model=用户选择的模型)
3. 报告结果，提供回滚命令: git stash pop
```

---

## 示例

### 示例 1: 简单问题诊断

```
用户: /bugfix 登录按钮点击无反应

## 问题诊断
**问题描述**: 登录按钮点击无反应
**问题类型**: 事件绑定问题
**复杂度**: simple

## 根因分析
**定位**: src/components/Login.tsx:45
**原因**: onClick 事件处理函数未正确绑定 this
**影响**: 登录功能完全不可用

## 修复方案
**策略**: 直接修复

**步骤**:
1. 将 `onClick={this.handleLogin}` 改为 `onClick={() => this.handleLogin()}`
   或使用箭头函数定义 handleLogin

**验证**:
- 点击登录按钮，确认触发登录逻辑

**风险**:
- 低风险，仅影响事件绑定
```

### 示例 2: 复杂问题诊断 + 执行

```
用户: /bugfix 用户数据偶发性丢失 --fix

## 问题诊断
**问题描述**: 用户数据偶发性丢失
**问题类型**: 并发/竞态条件
**复杂度**: complex

## 根因分析
**定位**: src/services/UserService.ts:120-145
**原因**: 多个异步操作同时写入，缺少锁机制
**影响**: 数据完整性受损，影响所有用户

## 修复方案
**策略**: 防御性修复 + 重构

**步骤**:
1. 添加乐观锁字段 - src/models/User.ts
2. 修改更新逻辑添加版本检查 - src/services/UserService.ts
3. 添加重试机制 - src/utils/retry.ts

**验证**:
- 并发写入测试
- 压力测试验证数据一致性

**风险**:
- 中等风险，需要数据库迁移添加版本字段

---
[AskUserQuestion: 确认执行? 选择模型?]
→ 用户选择: 执行 + opus
→ 创建检查点: git stash
→ 执行修复
→ 报告结果，提供回滚命令
```

### 示例 3: 指定范围诊断

```
用户: /bugfix API 返回 500 --scope src/api

## 问题诊断
**问题描述**: API 返回 500 错误
**问题类型**: 服务端异常
**复杂度**: moderate

## 根因分析
**定位**: src/api/handlers/order.ts:89
**原因**: 数据库查询未处理 null 情况，导致 NPE
**影响**: 订单相关 API 全部不可用

## 修复方案
**策略**: 防御性修复

**步骤**:
1. 添加 null 检查 - src/api/handlers/order.ts:89
2. 添加错误边界处理 - src/api/middleware/error.ts

**验证**:
- 测试空数据场景
- 检查错误日志格式

**风险**:
- 低风险，添加防御性代码
```

---

## 流程总结

**标准流程**：

```
1. 问题分析 → 确定问题类型和范围
2. Task(subagent_type="atlas:information-gatherer", model="haiku") → 信息收集
3. 根因分析 → 基于收集的信息分析
4. 输出修复方案
5. [可选] --fix 时询问确认和模型选择
6. [可选] Task(subagent_type="atlas:atlas-executor") → 执行修复
```
