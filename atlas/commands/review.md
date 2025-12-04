---
description: 代码审查命令。对指定范围的代码进行多维度自动化审查（安全、性能、风格、架构），支持自动修复。
argument-hint: [--scope path] [--type security|performance|style|architecture|all] [--fix] [--severity critical|warning|all]
---

# 代码审查命令

对代码进行多维度自动化审查，发现潜在问题并提供修复建议。

## 参数

| 参数 | 说明 | 默认值 |
|:-----|:-----|:-------|
| `--scope` | 审查范围（目录/文件/git diff） | git diff（未提交变更） |
| `--type` | 审查类型 | all |
| `--fix` | 自动修复可修复的问题 | false |
| `--severity` | 报告的最低严重性级别 | all |

---

## 审查类型

| 类型 | 说明 | 检查项 |
|:-----|:-----|:-------|
| `security` | 安全审查 | SQL 注入、XSS、硬编码密钥、敏感信息泄露、不安全的依赖 |
| `performance` | 性能审查 | N+1 查询、内存泄漏、不必要的重渲染、复杂度过高 |
| `style` | 风格审查 | 命名规范、代码结构、一致性、注释质量 |
| `architecture` | 架构审查 | 分层违规、循环依赖、耦合度、模块边界 |
| `all` | 全部审查 | 以上所有类型 |

---

## 执行流程

Phase 0 范围确定 → Phase 1 代码分析 → Phase 2 并行审查 → Phase 3 报告聚合 → Phase 4 自动修复（可选）

### Subagent 分配

| Phase | 功能 | Subagent | 说明 |
|:------|:-----|:---------|:-----|
| 0 | 范围确定 | 主进程 | 解析参数，确定审查范围 |
| 1 | 代码分析 | `atlas:information-gatherer` | 收集目标代码信息 |
| 2 | 并行审查 | `atlas:code-reviewer` | 多个实例并行审查不同维度 |
| 3 | 报告聚合 | 主进程 | 合并结果，生成统一报告 |
| 4 | 自动修复 | `atlas:atlas-executor` | 执行可自动修复的问题 |

---

## Phase 0: 范围确定

**输入**: 命令参数

**输出**: 审查目标列表

**范围确定规则**:
| 场景 | 范围 |
|:-----|:-----|
| 无 --scope | git diff（未提交的变更文件） |
| --scope . | 全项目（排除 node_modules、.git 等） |
| --scope src | 指定目录 |
| --scope src/user.ts | 指定文件 |

**操作**:
1. 解析 --scope 参数
2. 如果未指定，获取 git diff 变更文件列表
3. 过滤非代码文件
4. 输出目标文件列表

---

## 项目知识库

**优先从 `.claude/repowiki/` 获取项目信息**（如果存在）：

| 文件 | 用途 |
|:-----|:-----|
| `.claude/repowiki/.meta/modules.pkg.json` | 模块结构、依赖关系（用于架构审查） |
| `.claude/repowiki/.meta/api.pkg.json` | API 端点信息（用于安全审查） |
| `.claude/repowiki/.meta/symbols.pkg.json` | 符号索引（加速代码定位） |

**使用方式**：Phase 1 分析前先检查这些文件是否存在，优先利用现有信息。

---

## Phase 1: 代码分析

**Subagent**: `atlas:information-gatherer`

**输入**: Phase 0 的目标文件列表 + `.claude/repowiki/` 现有信息（如果存在）

**输出**: `.claude/review/.meta/targets.pkg.json`

**PKG 结构**:
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "scope": "git diff",
  "files": [
    {
      "path": "src/user.service.ts",
      "language": "typescript",
      "lines": 150,
      "symbols": ["UserService", "createUser", "validateUser"],
      "imports": ["@nestjs/common", "prisma"],
      "exports": ["UserService"]
    }
  ],
  "summary": {
    "totalFiles": 5,
    "totalLines": 420,
    "languages": {"typescript": 4, "javascript": 1}
  }
}
```

---

## Phase 2: 并行审查

**Subagent**: `atlas:code-reviewer` (多个实例并行)

**输入**:
- `.claude/review/.meta/targets.pkg.json`
- 审查类型（--type 参数）

**输出**: 各维度审查结果 JSON

**并行策略**:
- --type all: 启动 4 个 code-reviewer（security、performance、style、architecture）
- --type security: 启动 1 个 code-reviewer
- 多个类型: 按指定类型启动对应数量

**Subagent Prompt 必须包含**:
1. 审查维度（单一维度）
2. 目标文件路径列表
3. 审查规则参考（见下方规则表）
4. 输出格式要求

### 审查规则

#### Security（安全）

| 规则 ID | 检查项 | 严重性 | 示例 |
|:--------|:-------|:-------|:-----|
| SEC001 | SQL 注入 | 🔴 critical | 字符串拼接 SQL |
| SEC002 | XSS 漏洞 | 🔴 critical | 未转义用户输入 |
| SEC003 | 硬编码密钥 | 🔴 critical | API key 写死在代码 |
| SEC004 | 敏感信息日志 | 🟠 warning | 打印密码/token |
| SEC005 | 不安全的随机数 | 🟡 info | 使用 Math.random() 做安全用途 |
| SEC006 | eval/Function 使用 | 🟠 warning | 动态执行代码 |
| SEC007 | 路径遍历 | 🔴 critical | 未验证文件路径 |
| SEC008 | CORS 配置 | 🟠 warning | 允许所有来源 |

#### Performance（性能）

| 规则 ID | 检查项 | 严重性 | 示例 |
|:--------|:-------|:-------|:-----|
| PERF001 | N+1 查询 | 🟠 warning | 循环内 DB 查询 |
| PERF002 | 未优化循环 | 🟡 info | 嵌套循环可优化 |
| PERF003 | 内存泄漏风险 | 🟠 warning | 未清理事件监听 |
| PERF004 | 不必要的重渲染 | 🟡 info | React 组件无 memo |
| PERF005 | 同步阻塞 | 🟠 warning | 同步读写大文件 |
| PERF006 | 正则回溯 | 🟠 warning | 可能导致 ReDoS |
| PERF007 | 大对象拷贝 | 🟡 info | 深拷贝大数组/对象 |

#### Style（风格）

| 规则 ID | 检查项 | 严重性 | 示例 |
|:--------|:-------|:-------|:-----|
| STYLE001 | 函数过长 | 🟠 warning | >50 行 |
| STYLE002 | 嵌套过深 | 🟠 warning | >4 层 |
| STYLE003 | 命名不规范 | 🟡 info | 不符合项目约定 |
| STYLE004 | 魔法数字 | 🟡 info | 硬编码数字无说明 |
| STYLE005 | 重复代码 | 🟠 warning | 相似度 >80% |
| STYLE006 | TODO/FIXME | 🟡 info | 未处理的标记 |
| STYLE007 | 无用代码 | 🟡 info | 注释掉的代码块 |
| STYLE008 | 参数过多 | 🟡 info | 函数参数 >5 个 |

#### Architecture（架构）

| 规则 ID | 检查项 | 严重性 | 示例 |
|:--------|:-------|:-------|:-----|
| ARCH001 | 循环依赖 | 🟠 warning | A→B→C→A |
| ARCH002 | 分层违规 | 🟠 warning | Controller 直接访问 DB |
| ARCH003 | 模块边界 | 🟡 info | 跨模块直接导入内部实现 |
| ARCH004 | 耦合度高 | 🟡 info | 单文件依赖过多外部模块 |
| ARCH005 | 缺少抽象 | 🟡 info | 重复的 if-else 结构 |
| ARCH006 | 单例滥用 | 🟡 info | 全局状态过多 |

### 输出格式

每个 code-reviewer 实例输出：
```json
{
  "dimension": "security",
  "timestamp": "2024-01-15T10:30:00Z",
  "issues": [
    {
      "ruleId": "SEC001",
      "severity": "critical",
      "file": "src/user.service.ts",
      "line": 45,
      "column": 12,
      "code": "db.query(`SELECT * FROM users WHERE id = ${id}`)",
      "message": "SQL 注入风险：用户输入直接拼接到 SQL 语句",
      "suggestion": "使用参数化查询: db.query('SELECT * FROM users WHERE id = ?', [id])",
      "autoFixable": true,
      "fixedCode": "db.query('SELECT * FROM users WHERE id = ?', [id])"
    }
  ],
  "summary": {
    "critical": 1,
    "warning": 3,
    "info": 5,
    "total": 9
  }
}
```

---

## Phase 3: 报告聚合

**执行者**: 主进程

**输入**: Phase 2 各维度的审查结果 JSON

**输出**: `.claude/review/report-{date}.md`

**报告格式**:
```markdown
# 代码审查报告

> 生成于 2024-01-15 10:30:00

## 概览

| 指标 | 值 |
|:-----|:---|
| 审查范围 | git diff (5 files) |
| 审查类型 | all |
| 总问题数 | 15 |
| 严重问题 | 2 |
| 警告 | 8 |
| 提示 | 5 |

## 问题分布

| 维度 | 🔴 严重 | 🟠 警告 | 🟡 提示 |
|:-----|:--------|:--------|:--------|
| Security | 1 | 2 | 1 |
| Performance | 0 | 3 | 2 |
| Style | 0 | 2 | 2 |
| Architecture | 1 | 1 | 0 |

## 严重问题（需立即修复）

### [SEC001] SQL 注入风险
- **文件**: src/user.service.ts:45
- **代码**: `db.query(\`SELECT * FROM users WHERE id = ${id}\`)`
- **建议**: 使用参数化查询
- **可自动修复**: ✅

### [ARCH001] 循环依赖
- **文件**: src/order/order.service.ts
- **问题**: order → user → order 形成循环
- **建议**: 提取共享逻辑到 common 模块
- **可自动修复**: ❌

## 警告问题

[列出所有警告级别问题...]

## 提示问题

[列出所有提示级别问题...]

## 修复建议

### 自动修复
以下问题可通过 `--fix` 参数自动修复：
- SEC001: SQL 注入 (1 处)
- STYLE001: 函数过长 (需要手动拆分)

### 手动修复
以下问题需要手动处理：
- ARCH001: 循环依赖 - 建议重构模块结构

---
*使用 `/atlas:review --fix` 自动修复可修复的问题*
```

---

## Phase 4: 自动修复（可选）

**条件**: 仅当 --fix 参数存在时执行

**Subagent**: `atlas:atlas-executor`

**输入**: Phase 3 报告中 autoFixable=true 的问题列表

**输出**: 修复后的文件 + 修复报告

**执行策略**:
1. 按文件分组，每个文件一个子任务
2. 并行执行各子任务
3. 每个修复保持原有代码风格

**修复原则**:
- 只修复 autoFixable=true 的问题
- 保持代码格式一致
- 不引入新问题
- 修复后验证语法正确性

**修复报告**:
```markdown
## 自动修复完成

### 修复统计
| 指标 | 值 |
|:-----|:---|
| 已修复 | 5 |
| 跳过 | 3 |
| 失败 | 0 |

### 修复详情
1. ✅ src/user.service.ts:45 - SEC001 SQL 注入已修复
2. ✅ src/order.service.ts:23 - SEC004 敏感信息日志已修复
3. ⏭️ src/auth.service.ts:67 - STYLE001 函数过长（需手动拆分）

### 后续建议
1. 运行测试确保修复正确: `npm test`
2. 检查跳过的问题，考虑手动修复
```

---

## 条件执行

| 条件 | 行为 |
|:-----|:-----|
| 无变更文件 | 提示无需审查，退出 |
| 目标文件 >100 | 建议使用 --scope 缩小范围 |
| --fix 但无可修复问题 | 报告无可自动修复的问题 |
| 审查类型无问题 | 报告该维度通过 |

---

## 约束

**执行约束**:
- Phase 2 必须使用 `atlas:code-reviewer` agent
- Phase 4 必须使用 `atlas:atlas-executor` agent
- 不同审查维度必须并行执行
- 每个 code-reviewer 只处理单一维度

**审查约束**:
- 只报告问题，不擅自修复（除非 --fix）
- 严格按规则判断严重性
- 提供可操作的修复建议
- autoFixable 必须谨慎判断

**报告约束**:
- 问题必须包含文件路径和行号
- 必须提供代码片段上下文
- 必须按严重性排序
- 必须说明是否可自动修复

---

## 示例

### 基础用法
```bash
# 审查未提交的变更
/atlas:review

# 审查指定目录
/atlas:review --scope src/services

# 仅安全审查
/atlas:review --type security

# 审查并自动修复
/atlas:review --fix

# 只看严重问题
/atlas:review --severity critical
```

### 输出示例

**无问题**:
```
✅ 代码审查完成

审查范围: git diff (3 files)
审查类型: all

🎉 恭喜！未发现任何问题
```

**有问题**:
```
⚠️ 代码审查完成

审查范围: src/services (12 files)
审查类型: all

发现 15 个问题:
- 🔴 严重: 2
- 🟠 警告: 8
- 🟡 提示: 5

详细报告: .claude/review/report-20240115.md

建议:
1. 立即修复 2 个严重问题
2. 使用 `/atlas:review --fix` 自动修复 5 个可修复问题
```
