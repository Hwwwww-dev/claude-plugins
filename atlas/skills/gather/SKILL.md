---
name: information-gathering-workflow
description: 智能信息收集工作流。当需要分析项目结构、梳理依赖关系、探索代码库时使用。触发词："分析项目"、"梳理依赖"、"代码库探索"、"收集信息"等
color: orange
---

# 信息收集工作流

## 何时使用

- "分析项目结构"
- "梳理所有依赖"
- "探索代码库"
- "收集项目信息"

## 工作流程

### 1. 明确任务

```
任务: [具体收集目标]
范围: 整个项目 / 特定目录
目标: 结构 / 依赖 / 模式
```

### 2. 调用 Information Gatherer

```
Task(subagent_type="atlas:information-gatherer")
prompt: 任务ID, 范围, 目标, 输出要求
```

### 3. 展示结果

将返回的摘要展示给用户，说明：
- 收集范围和主要发现
- 详细报告位置 (`docs/information/<id>.md`)
- 后续建议

## 与其他工具协同

```
信息收集 → 识别修改文件 → /orchestrate 批量执行
Plan agent 需要项目信息 → 调用 Information Gatherer → 基于信息规划
```

## 核心原则

- ✅ 将需求转化为明确收集任务
- ✅ 正确调用 agent，展示并解释结果
- ❌ 不代替 agent 执行收集
- ❌ 不修改代码（Executor 职责）
- ❌ 不嵌套调用其他 Skill
