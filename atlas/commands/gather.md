---
description: 智能信息收集命令。快速分析项目结构、依赖关系、代码模式等，支持多种收集模式和输出格式
---

# /gather - 快速信息收集

## 命令简介

`/gather` 命令用于快速收集和分析项目信息，支持多种收集模式，输出结构化的分析报告。

## 使用方式

```bash
/gather [mode] [options]

# 基础用法
/gather project-structure           # 分析项目结构
/gather dependencies [symbol]       # 梳理依赖关系
/gather code-patterns [pattern]     # 搜索代码模式
/gather impact [symbol]             # 分析修改影响

# 带选项
/gather project-structure --deep    # 深度分析
/gather dependencies UserAPI --cache deps-analysis  # 指定缓存名
/gather code-patterns "useState" --focus components  # 关注特定目录
```

## 收集模式

### 1. project-structure - 项目结构分析

分析整个项目的代码组织结构。

**用法**：
```bash
/gather project-structure [--deep] [--cache <name>]
```

**输出内容**：
- 文件和目录统计
- 模块组织结构
- 关键文件清单
- 核心符号列表

**示例**：
```bash
/gather project-structure
/gather project-structure --deep --cache project-map-v1
```

### 2. dependencies - 依赖关系梳理

梳理特定符号（类、函数、组件）的依赖关系。

**用法**：
```bash
/gather dependencies <symbol> [--deep] [--cache <name>]
```

**输出内容**：
- 符号定位信息
- 所有引用位置
- 调用上下文分析
- 修改影响评估

**示例**：
```bash
/gather dependencies UserAPI
/gather dependencies LoginComponent --cache login-deps
```

### 3. code-patterns - 代码模式搜索

搜索项目中的特定代码模式（如 React Hooks、API 调用等）。

**用法**：
```bash
/gather code-patterns "<pattern>" [--focus <directory>] [--cache <name>]
```

**输出内容**：
- 匹配统计
- 详细清单（文件路径+行号）
- 模式分析
- 使用建议

**示例**：
```bash
/gather code-patterns "useState"
/gather code-patterns "import.*from.*react" --focus src/components
/gather code-patterns "useEffect" --cache hooks-usage
```

### 4. impact - 修改影响分析

分析修改特定符号会影响哪些文件和代码。

**用法**：
```bash
/gather impact <symbol> [--cache <name>]
```

**输出内容**：
- 直接引用点
- 间接影响范围
- 风险评估
- 修改建议

**示例**：
```bash
/gather impact UserAPI
/gather impact AuthService --cache auth-impact
```

## 命令选项

### --deep
深度分析模式，提供更详细的分析结果。

```bash
/gather project-structure --deep
```

### --focus <directory>
限制分析范围到特定目录。

```bash
/gather code-patterns "API" --focus src/services
```

### --cache <name>
指定 Memory 缓存文件名，供后续复用。

```bash
/gather dependencies UserAPI --cache userapi-deps-v1
```

## 执行流程

1. **解析命令参数**
   - 识别收集模式
   - 提取目标符号或模式
   - 解析命令选项

2. **构建收集任务**
   - 根据模式生成明确的任务描述
   - 包含分析范围、收集目标、输出要求
   - 确定是否需要缓存

3. **调用 Information Gatherer**
   - 使用 Task tool 调用 `atlas-information-gatherer` agent
   - 传递完整的任务描述
   - 等待分析结果

4. **展示分析报告**
   - 格式化输出报告
   - 突出关键发现
   - 提供后续建议

5. **缓存结果（可选）**
   - 如果指定了 --cache 选项
   - 将结果保存到 Memory
   - 告知用户缓存位置

## 使用示例

### 示例 1：初次接触项目

```bash
# 用户执行
/gather project-structure --deep --cache project-overview-v1

# 系统响应
正在分析项目结构...

# 输出报告
# 项目代码结构分析

## 📊 统计信息
- 总文件数: 45
- TypeScript 文件: 35
- React 组件: 12
- Service 模块: 8

## 📁 模块结构
### Components (12 files)
- Auth: Login, Register, Profile (3)
- Dashboard: Overview, Analytics, Reports (5)
- Shared: Button, Input, Modal (4)

### Services (8 files)
- UserAPI, AuthAPI, DataAPI

## 💾 缓存信息
已保存到: project-overview-v1.md
```

### 示例 2：准备重构

```bash
# 用户执行
/gather dependencies UserAPI --cache userapi-analysis

# 系统响应
正在分析 UserAPI 的依赖关系...

# 输出报告
# UserAPI 依赖关系分析

## 🎯 符号定位
- 文件: src/services/UserAPI.ts
- 类型: Service Class

## 🔗 被引用的地方（5处）
1. Dashboard.tsx:42 - 获取用户列表
2. Profile.tsx:18 - 加载用户资料
3. Settings.tsx:67 - 更新用户设置
4. AuthFlow.ts:23 - 认证流程
5. AdminPanel.tsx:101 - 管理员查看

## ⚠️ 影响分析
修改 UserAPI 需要更新 5 个文件

## 💾 缓存信息
已保存到: userapi-analysis.md

---

💡 **后续建议**:
如需批量更新这些引用，可以使用:
`/orchestrate 更新所有 UserAPI 的引用`
```

### 示例 3：代码模式探索

```bash
# 用户执行
/gather code-patterns "useState" --focus src/components

# 系统响应
正在搜索 useState 的使用情况...

# 输出报告
# React Hooks 使用分析 (useState)

## 📊 统计
- 使用 useState 的组件: 12 个
- 总使用次数: 18 次

## 🎯 详细清单
1. Dashboard.tsx:15 - 用户列表状态
2. Login.tsx:8 - 表单输入状态
3. Profile.tsx:12 - 编辑模式状态
... (共 18 处)

## 💡 模式分析
- 主要用于表单和 UI 状态管理
- 部分组件存在多个 useState，可考虑使用 useReducer
```

### 示例 4：影响范围评估

```bash
# 用户执行
/gather impact AuthService

# 系统响应
正在分析 AuthService 的修改影响...

# 输出报告
# AuthService 修改影响分析

## 直接影响（3个文件）
1. Login.tsx - 登录逻辑
2. Register.tsx - 注册流程
3. AuthFlow.ts - 认证状态管理

## 间接影响（8个文件）
- Dashboard、Profile 等组件依赖 AuthFlow
- 修改 AuthService 可能影响所有需要认证的页面

## ⚠️ 风险评估
- 高风险: 认证流程变更可能导致全局登录失败
- 中风险: 接口变更需要更新多个调用点
- 低风险: 内部实现优化不影响外部接口

## 💡 修改建议
1. 优先保持接口向后兼容
2. 充分测试认证流程
3. 考虑渐进式迁移策略
```

## 与其他命令的协同

### 与 /orchestrate 配合

```bash
# 先收集信息
/gather dependencies UserAPI

# 基于分析结果执行批量操作
/orchestrate 更新所有 UserAPI 的调用方式
```

### 连续分析

```bash
# 全面分析项目
/gather project-structure --cache project-v1

# 针对性分析关键模块
/gather dependencies AuthService --cache auth-v1
/gather dependencies UserAPI --cache user-v1

# 后续任务可以直接使用这些缓存
```

## 输出格式

所有 `/gather` 命令都输出结构化的 Markdown 报告，包含：

1. **📊 统计信息**：数量、文件数等概览
2. **🎯 核心发现**：关键的分析结果
3. **📁 详细清单**：具体的文件路径和行号
4. **💡 洞察建议**：模式分析和后续建议
5. **💾 缓存信息**：Memory 保存位置（如适用）

## 注意事项

1. **只读分析**：`/gather` 不会修改任何代码文件
2. **性能考虑**：大型项目的 `--deep` 分析可能需要较长时间
3. **缓存复用**：建议为重要分析指定 `--cache` 名称，供后续复用
4. **路径准确性**：所有输出都包含完整的文件路径和行号

## 典型工作流

```bash
# 第 1 步：了解项目
/gather project-structure --cache project-overview

# 第 2 步：深入分析关键模块
/gather dependencies UserAPI --cache user-api-deps
/gather dependencies AuthService --cache auth-service-deps

# 第 3 步：识别代码模式
/gather code-patterns "useEffect" --focus src/components

# 第 4 步：评估修改影响
/gather impact UserAPI

# 第 5 步：执行批量操作（如需要）
/orchestrate 根据分析结果更新代码
```

## 成本优化

通过 Memory 缓存实现成本最优：

```
第一次分析项目：成本 C
  ↓
保存到 Memory (--cache)
  ↓
后续 N 个任务复用缓存：成本 0
  ↓
实际人均成本：C / (N+1)
```

**最佳实践**：
- 项目初期进行一次全面的 `project-structure` 分析并缓存
- 为关键模块创建专门的依赖分析缓存
- 后续任务可以直接复用这些缓存，大幅降低成本
