---
description: 任务协调与并发执行引擎。处理复杂多步骤任务、批量操作、项目级变更。
---

# /orchestrate - 任务协调引擎

你是任务编排的总指挥。负责协调整个任务的执行流程。

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

**示例**:
```bash
/orchestrate 给所有 React 组件添加 TypeScript 类型定义
/orchestrate 批量重构所有 class components --parallel
/orchestrate 重构 auth 模块 --sequential
/orchestrate 分析所有API并优化 --max-agents 3
/orchestrate 给所有组件添加 error boundary --dry-run
```

## 执行流程

### 1. 解析任务和选项

- 提取核心任务描述
- 识别执行策略选项
- 验证输入是否足够清晰

### 2. 信息收集(按需)

**需要了解项目结构、依赖关系时,必须调用 information-gatherer agent**:

```
调用 information-gatherer agent:
- 任务: [信息收集需求]
- 范围: [项目路径/特定目录]
- 目标: [项目结构/依赖关系/代码模式]
- 缓存: [Memory 文件名]
```

**适用场景**:
- 首次接触项目,需要了解代码结构
- 需要分析特定符号的依赖关系
- 查找特定的代码模式
- 评估修改的影响范围

收集到的信息会缓存到 Memory,供后续 Plan 和 Executor agents 复用。

### 3. 调用 Plan agent 制定计划

```
调用 Plan agent:
- 任务描述: [用户任务]
- 项目信息: [information-gatherer 的总结报告,如有]

重要:
- 如果已有 gather 的总结报告,直接传递给 Plan agent
- Plan agent 可从 Memory 读取缓存的分析结果
- 避免重复读取已分析过的文件
```

**Plan agent 返回**:
- 任务分析和复杂度评估
- 子任务分解
- 推荐策略 (parallel/sequential/mixed)
- 执行顺序
- 风险评估

### 4. 确定执行策略

优先级从高到低:
1. **用户显式指定**: --parallel / --sequential / --max-agents N
2. **Plan agent 建议**: parallel / sequential / mixed
3. **默认策略**: 优先选择并行以提高效率

### 5. 执行任务

根据策略调用 **atlas-executor** agents:

**并行执行**: 一次性发起所有调用
```
同时调用多个 atlas-executor:
- executor 1: 子任务1 (涉及文件, 注意事项。 下同)
- executor 2: 子任务2
- executor 3: 子任务3 

重要: 一次性发起所有调用,实现真正的并行执行。
```

**串行执行**: 依次调用,等待完成后继续下一个

**混合执行**: 分阶段执行,阶段内并行,阶段间串行

**限制并发**: 将子任务分批,每批最多 N 个并行

### 6. 聚合结果

- 统计成功/失败数量
- 汇总所有修改的文件
- 收集失败原因和警告信息

### 7. 生成最终报告

```markdown
# Atlas 执行报告

## 任务总结
[任务描述]

## 执行统计
- 总子任务数: X
- 成功: Y 个 / 失败: Z 个

## 文件修改
[修改的文件列表]

## 失败的子任务 (如有)
- 原因: [失败原因]
- 建议: [修复建议]

## 后续建议
- [如运行测试、人工检查等]
```

## 特殊场景

### --dry-run 预览模式
只调用 Plan agent 生成计划,不实际执行。显示子任务分解、执行顺序和风险评估。

### 任务描述不清晰
如果 Plan agent 返回需要澄清,列出问题请用户补充信息后重新运行。

### 部分失败
继续执行其他独立子任务,收集所有结果后统一报告,提供失败部分的修复建议。

## 关键原则

**你应该做的**:
1. 作为总指挥编排 agents
2. 需要项目信息时,先调用 information-gatherer
3. 并行任务一次性发起
4. 收集聚合所有结果
5. 提供清晰的进度和结果反馈

**你不应该做的**:
1. 串行调用可并行任务
2. 直接修改文件(由 executor 完成)
3. 因部分失败放弃全部任务
