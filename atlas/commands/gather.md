---
description: 智能信息收集命令。分析项目结构、依赖关系、代码模式,输出结构化报告。
---

# /gather - 信息收集

`/gather` 命令用于快速收集和分析项目信息，输出结构化的分析报告。

## 使用方式

```bash
/gather [mode] [target] [options]
```

## 收集模式

### 1. project-structure - 项目结构分析

分析整个项目的代码组织结构。

```bash
/gather project-structure [--deep] [--cache <name>]
```

**输出内容**:
- 文件和目录统计
- 模块组织结构
- 关键文件清单
- 核心符号列表

### 2. dependencies - 依赖关系梳理

梳理特定符号（类、函数、组件）的依赖关系。

```bash
/gather dependencies <symbol> [--deep] [--cache <name>]
```

**输出内容**:
- 符号定位信息
- 所有引用位置
- 调用上下文分析
- 修改影响评估

### 3. code-patterns - 代码模式搜索

搜索项目中的特定代码模式。

```bash
/gather code-patterns "<pattern>" [--focus <directory>] [--cache <name>]
```

**输出内容**:
- 匹配统计
- 详细清单（文件路径+行号）
- 模式分析
- 使用建议

### 4. impact - 修改影响分析

分析修改特定符号会影响哪些文件和代码。

```bash
/gather impact <symbol> [--cache <name>]
```

**输出内容**:
- 直接引用点
- 间接影响范围
- 风险评估
- 修改建议

## 命令选项

- `--deep`: 深度分析模式，提供更详细的分析结果
- `--focus <dir>`: 限制分析范围到特定目录
- `--cache <name>`: 指定 Memory 缓存文件名，供后续复用

## 示例

```bash
# 项目结构
/gather project-structure
/gather project-structure --deep --cache project-map-v1

# 依赖分析
/gather dependencies UserAPI
/gather dependencies LoginComponent --cache login-deps

# 代码模式
/gather code-patterns "useState"
/gather code-patterns "import.*from.*react" --focus src/components

# 影响分析
/gather impact UserAPI
/gather impact AuthService --cache auth-impact
```

## 执行流程

1. **解析命令参数**: 识别收集模式、目标符号/模式、选项
2. **构建收集任务**: 生成明确的任务描述，包含范围和目标
3. **调用 information-gatherer agent**: 传递完整任务描述，等待分析结果
4. **展示分析报告**: 格式化输出，突出关键发现
5. **缓存结果(可选)**: 如指定 --cache，保存到 Memory 并告知用户

## 输出格式

```markdown
## 统计信息
[数量、文件数等概览]

## 核心发现
[关键的分析结果]

## 详细清单
[具体的文件路径和行号]

## 洞察建议
[模式分析和后续建议]

## 缓存信息 (如适用)
已保存到: [文件名]
```

## 与 /orchestrate 配合

```bash
# 先收集信息
/gather dependencies UserAPI --cache userapi-deps

# 基于分析结果执行批量操作
/orchestrate 更新所有 UserAPI 的调用方式
```

## 注意事项

- `/gather` 只读分析，不会修改任何代码文件
- 大型项目的 `--deep` 分析可能需要较长时间
- 建议为重要分析指定 `--cache` 名称，供后续复用
- 所有输出都包含完整的文件路径和行号
