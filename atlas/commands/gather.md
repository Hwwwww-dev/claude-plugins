---
description: 智能信息收集命令。分析项目结构、依赖关系、代码模式,输出结构化报告。
---

# /gather - 信息收集

用户输入: $ARGUMENTS

---

## 第一步：确认收集选项

**如果用户未指定模式，使用 AskUserQuestion 询问：**

```
问题1: 收集模式
- project-structure: 项目结构分析
- dependencies: 依赖关系梳理
- code-patterns: 代码模式搜索
- impact: 修改影响分析

问题2: 分析深度
- normal (默认): 标准分析
- deep: 深度分析，更详细

问题3: 分析范围
- all: 整个项目
- specific: 指定目录/文件
```

**如果用户已指定（如 `/gather dependencies UserAPI --deep`），跳过询问。**

---

## 第二步：调用 information-gatherer

**固定输入结构**:
```
Task(subagent_type="atlas:information-gatherer")
prompt: |
  ## 任务
  任务 ID: <mode>-<target>-<date>
  收集模式: [project-structure / dependencies / code-patterns / impact]

  ## 目标
  - 目标: [符号名 / 模式 / 目录]
  - 范围: [整个项目 / 指定路径]
  - 深度: [normal / deep]

  ## 收集内容
  [根据模式列出具体收集项]

  ## 输出
  写入: docs/information/<task-id>.md
  返回: 简洁摘要给主对话
```

---

## 收集模式详情

### project-structure

```
## 收集内容
- 文件和目录统计
- 模块组织结构
- 关键文件清单
- 核心符号列表
```

### dependencies

```
## 收集内容
- 符号定位信息
- 所有引用位置 (文件:行号)
- 调用上下文
- 修改影响评估
```

### code-patterns

```
## 收集内容
- 匹配统计
- 详细清单 (文件:行号)
- 模式分析
- 使用建议
```

### impact

```
## 收集内容
- 直接引用点
- 间接影响范围
- 风险评估
- 修改建议
```

---

## 输出格式

**固定输出结构**:
```markdown
📊 信息收集完成

## 模式: [收集模式]
## 目标: [目标符号/模式]
## 统计: [关键数字]

## 核心发现
- [发现1]
- [发现2]

💾 详细报告: docs/information/<task-id>.md

🔜 后续建议: [如需批量修改可使用 /orchestrate]
```

---

## 示例

### 项目结构
```
/gather project-structure
/gather project-structure --deep
```

### 依赖分析
```
/gather dependencies UserAPI
/gather dependencies LoginComponent --deep
```

### 代码模式
```
/gather code-patterns "useState"
/gather code-patterns "import.*react" --focus src/components
```

### 影响分析
```
/gather impact UserAPI
/gather impact AuthService
```

---

## 与 /orchestrate 配合

```
1. /gather dependencies UserAPI
   → 分析 UserAPI 的所有引用点

2. /orchestrate 更新所有 UserAPI 调用
   → 基于收集结果批量执行
```

---

## 注意事项

- `/gather` 只读分析，不修改代码
- 结果写入 `docs/information/`，供后续复用
- 所有输出包含完整文件路径和行号
