---
description: 智能重构命令。识别代码问题并执行特定模式的自动化重构，支持预览和交互式确认。
argument-hint: <pattern> [--scope path] [--dry-run] [--interactive]
---

# 智能重构命令

识别符合特定模式的代码问题，并执行自动化重构。

## 参数

| 参数 | 说明 | 默认值 |
|:-----|:-----|:-------|
| `pattern` | 重构模式（必填） | - |
| `--scope` | 重构范围 | . (全项目) |
| `--dry-run` | 仅预览，不实际修改 | false |
| `--interactive` | 交互式逐个确认 | false |

---

## 重构模式

| 模式 | 说明 | 识别条件 | 示例 |
|:-----|:-----|:---------|:-----|
| `extract-method` | 提取长函数为小函数 | 函数体 >50 行 | 拆分 processOrder 为多个子函数 |
| `extract-component` | 提取大组件为子组件 | JSX/模板 >100 行 | 拆分 Dashboard 为 Header/Content/Sidebar |
| `consolidate-duplicate` | 合并重复代码 | 相似度 >80%，≥3 处 | 提取公共函数 |
| `modernize-js` | JavaScript 现代化 | var/callback/传统语法 | var→const, callback→async/await |
| `add-types` | 添加 TypeScript 类型 | any/缺失类型 | any→具体类型, 添加接口定义 |
| `rename-convention` | 统一命名规范 | 命名不一致 | snake_case→camelCase |
| `simplify-conditions` | 简化条件逻辑 | 复杂 if-else | 提前返回, 三元表达式 |
| `remove-dead-code` | 移除死代码 | 未使用的导出/变量 | 删除无引用代码 |

---

## 执行流程

Phase 0 模式解析 → Phase 1 候选识别 → Phase 2 规划 → Phase 3 执行/预览 → Phase 4 验证

### Subagent 分配

| Phase | 功能 | Subagent | 说明 |
|:------|:-----|:---------|:-----|
| 0 | 模式解析 | 主进程 | 验证模式有效性 |
| 1 | 候选识别 | `atlas:information-gatherer` | 扫描符合模式的代码 |
| 2 | 规划 | `Plan` | 生成重构计划 |
| 3 | 执行 | `atlas:atlas-executor` | 并行执行重构 |
| 4 | 验证 | 主进程 | 运行测试/类型检查 |

---

## Phase 0: 模式解析

**输入**: 命令参数

**操作**:
1. 验证 pattern 是否为支持的模式
2. 解析 --scope 确定范围
3. 记录执行选项（dry-run/interactive）

**失败场景**:
- 未知模式 → 列出支持的模式，终止
- 范围不存在 → 报错，终止

---

## 项目知识库

**优先从 `.claude/repowiki/` 获取项目信息**（如果存在）：

| 文件 | 用途 |
|:-----|:-----|
| `.claude/repowiki/.meta/modules.pkg.json` | 模块结构（用于依赖分析） |
| `.claude/repowiki/.meta/symbols.pkg.json` | 符号索引（加速候选识别） |
| `.claude/repowiki/.meta/quality.pkg.json` | 质量分析（已识别的问题点） |

**使用方式**：Phase 1 识别前先检查这些文件是否存在，可加速候选识别过程。

---

## Phase 1: 候选识别

**Subagent**: `atlas:information-gatherer`

**输入**: 重构模式 + 范围 + `.claude/repowiki/` 现有信息（如果存在）

**输出**: `.claude/refactor/.meta/candidates.pkg.json`

**PKG 结构**:
```json
{
  "pattern": "extract-method",
  "timestamp": "2024-01-15T10:30:00Z",
  "candidates": [
    {
      "id": "candidate-001",
      "file": "src/order/order.service.ts",
      "symbol": "processOrder",
      "line": 45,
      "lines": 85,
      "reason": "函数体 85 行，超过阈值 50 行",
      "complexity": "high",
      "dependencies": ["validateOrder", "calculateTotal", "updateInventory"],
      "suggestedSplits": [
        {"name": "validateOrderData", "lines": "46-65", "description": "订单数据验证"},
        {"name": "processPayment", "lines": "66-90", "description": "支付处理"},
        {"name": "finalizeOrder", "lines": "91-130", "description": "订单完成处理"}
      ]
    }
  ],
  "summary": {
    "totalCandidates": 5,
    "byComplexity": {"high": 2, "medium": 2, "low": 1}
  }
}
```

### 各模式识别规则

#### extract-method
```
条件: 函数体行数 > 50 或 圈复杂度 > 10
输出: 函数位置、建议拆分点、新函数命名建议
```

#### extract-component
```
条件: JSX/模板行数 > 100 或 props > 10
输出: 组件位置、建议拆分的子组件、props 分析
```

#### consolidate-duplicate
```
条件: 代码块相似度 > 80% 且出现 >= 3 次
输出: 重复代码位置列表、相似度百分比、合并建议
```

#### modernize-js
```
条件: 使用 var / callback / arguments / with 等
输出: 旧语法位置、建议的现代替代方案
```

#### add-types
```
条件: 使用 any / 缺失返回类型 / 缺失参数类型
输出: 类型缺失位置、推断的类型建议
```

#### rename-convention
```
条件: 命名不符合项目约定（检测现有命名模式）
输出: 不规范命名列表、建议的新命名
```

#### simplify-conditions
```
条件: if-else > 3 层 或 条件表达式 > 3 个运算符
输出: 复杂条件位置、简化建议（提前返回/策略模式）
```

#### remove-dead-code
```
条件: 未被引用的导出函数/变量/类型
输出: 死代码位置、引用分析结果
```

---

## Phase 2: 规划

**Subagent**: `Plan`

**输入**: `.claude/refactor/.meta/candidates.pkg.json`

**输出**: 重构执行计划 + TodoWrite todos

**规划内容**:
1. 按依赖关系排序候选项
2. 分配子任务（考虑文件冲突）
3. 决定执行策略（parallel/sequential）
4. 生成详细的执行步骤

**执行计划示例**:
```markdown
## 重构计划

### 模式: extract-method
### 候选数: 5
### 执行策略: parallel（无依赖冲突）

### 子任务分配
#1: 重构 processOrder (order.service.ts)
    - 提取 validateOrderData
    - 提取 processPayment
    - 提取 finalizeOrder

#2: 重构 handleUserRegistration (user.service.ts)
    - 提取 validateUserData
    - 提取 createUserAccount

#3: 重构 generateReport (report.service.ts)
    - 提取 collectData
    - 提取 formatReport
```

---

## Phase 3: 执行/预览

### --dry-run 模式

**执行者**: 主进程

**输出**: 预览报告（不修改文件）

```markdown
# 重构预览

## 模式: extract-method
## 候选数: 5

### 变更预览

#### src/order/order.service.ts

**原代码** (85 行):
```typescript
async processOrder(orderId: string) {
  // 85 行代码...
}
```

**重构后** (3 个函数):
```typescript
async processOrder(orderId: string) {
  await this.validateOrderData(orderId);
  await this.processPayment(orderId);
  await this.finalizeOrder(orderId);
}

private async validateOrderData(orderId: string) {
  // 20 行
}

private async processPayment(orderId: string) {
  // 25 行
}

private async finalizeOrder(orderId: string) {
  // 40 行
}
```

### 预计影响
- 修改文件: 3
- 新增函数: 8
- 代码行数: +15 (新函数签名和调用)
```

### --interactive 模式

**执行者**: 主进程 + atlas:atlas-executor

**流程**:
1. 展示第一个候选项的变更预览
2. 询问用户: [执行] [跳过] [终止]
3. 根据选择执行或跳过
4. 继续下一个候选项

### 默认模式（直接执行）

**Subagent**: `atlas:atlas-executor` (并行多个)

**执行策略**:
- 无依赖冲突：并行执行所有子任务
- 有依赖冲突：按依赖顺序串行执行

**子任务 Prompt 必须包含**:
1. 重构模式和规则
2. 目标文件和符号
3. 候选项的详细信息（suggestedSplits 等）
4. 保持代码风格一致的要求

---

## Phase 4: 验证

**执行者**: 主进程

**操作**:
1. 检测项目测试框架
2. 运行相关测试
3. 运行类型检查（如果是 TypeScript）
4. 报告验证结果

**验证命令检测**:
| 检测 | 命令 |
|:-----|:-----|
| package.json test script | `npm test` / `yarn test` |
| TypeScript | `tsc --noEmit` |
| ESLint | `eslint --fix` |

**验证报告**:
```markdown
## 重构验证

### 执行结果
- ✅ 类型检查通过
- ✅ 测试通过 (42/42)
- ⚠️ ESLint 警告 2 个（非阻塞）

### 重构统计
- 修改文件: 3
- 新增函数: 8
- 重构候选: 5/5 完成
```

---

## 约束

**模式约束**:
- 只执行指定模式的重构
- 不"顺便"做其他优化
- 保持现有代码风格

**安全约束**:
- 重构前记录原始代码
- 验证失败时提供回滚建议
- 不修改测试文件（除非明确要求）

**执行约束**:
- Phase 1 必须使用 information-gatherer
- Phase 2 必须使用 Plan agent
- Phase 3 必须使用 atlas-executor（非 dry-run 时）

---

## 示例

### 基础用法
```bash
# 提取长函数
/atlas:refactor extract-method

# 仅预览，不修改
/atlas:refactor extract-method --dry-run

# 交互式确认
/atlas:refactor extract-method --interactive

# 限定范围
/atlas:refactor add-types --scope src/services

# JS 现代化
/atlas:refactor modernize-js --scope src

# 合并重复代码
/atlas:refactor consolidate-duplicate
```

### 输出示例

**预览模式**:
```
📋 重构预览

模式: extract-method
范围: src/services
候选数: 5

变更预览:
1. processOrder (order.service.ts:45) → 拆分为 3 个函数
2. handleRegistration (user.service.ts:23) → 拆分为 2 个函数
3. generateReport (report.service.ts:89) → 拆分为 2 个函数
...

预计影响:
- 修改 3 个文件
- 新增 7 个私有函数

使用 `/atlas:refactor extract-method` 执行重构
```

**执行完成**:
```
✅ 重构完成

模式: extract-method
执行: 5/5 候选项

修改文件:
- src/order/order.service.ts (+3 函数)
- src/user/user.service.ts (+2 函数)
- src/report/report.service.ts (+2 函数)

验证结果:
- ✅ 类型检查通过
- ✅ 测试通过 (42/42)

建议: 检查重构结果，确保业务逻辑正确
```
