---
description: 依赖管理命令。分析项目依赖,检测安全漏洞、版本冲突、升级建议,支持自动修复。
argument-hint: [--scope path] [--type security|outdated|conflicts|tree|all] [--fix] [--upgrade major|minor|patch]
---

# /deps - 依赖管理

用户输入: $ARGUMENTS

---

## 第一步:确认执行选项

**如果用户未指定选项,使用 AskUserQuestion 询问:**

```
问题1: 分析类型
- security: 安全漏洞检测(CVE、恶意包)
- outdated: 过期依赖分析(版本差距、更新建议)
- conflicts: 版本冲突检测(peer dependency、重复包)
- tree: 依赖树分析(深度、包大小、冗余)
- all: 全部分析(默认)

问题2: 分析范围
- 默认: 项目根目录
- 指定: 输入路径(如 packages/core)

问题3: 修复策略
- report: 仅生成报告(默认)
- fix: 自动修复可修复的问题
- interactive: 交互式选择修复

问题4: 升级策略(仅 outdated 类型)
- patch: 补丁版本(1.0.x)
- minor: 次版本(1.x.0)
- major: 主版本(x.0.0)
```

**如果用户已指定(如 `/deps --type security --fix`),跳过询问。**

---

## 参数

| 参数 | 说明 | 默认值 |
|:-----|:-----|:-------|
| `--scope` | 分析范围(目录/文件) | . (项目根) |
| `--type` | 分析类型 | all |
| `--fix` | 自动修复可修复的问题 | false |
| `--upgrade` | 升级策略(patch/minor/major) | patch |
| `--interactive` | 交互式选择修复项 | false |
| `--no-dev` | 排除开发依赖 | false |

---

## 分析类型

| 类型 | 检查内容 | 输出 |
|:-----|:---------|:-----|
| **security** | CVE 漏洞、恶意包、许可证风险 | 漏洞清单、CVSS 评分、修复建议 |
| **outdated** | 过期依赖、版本差距、破坏性变更 | 当前版本、最新版本、升级建议 |
| **conflicts** | 版本冲突、peer dependency、重复包 | 冲突清单、解决方案、依赖树 |
| **tree** | 依赖深度、包大小、传递依赖、冗余 | 依赖树、大小分析、优化建议 |
| **all** | 以上所有类型 | 综合报告 |

---

## 执行流程

Phase 0 环境检测 → Phase 1 依赖扫描 → Phase 2 问题分析 → Phase 3 报告生成 → Phase 4 自动修复(可选)

### Subagent 分配

| Phase | 功能 | Subagent | 说明 |
|:------|:-----|:---------|:-----|
| 0 | 环境检测 | 主进程 | 检测包管理器、lockfile、配置文件 |
| 1 | 依赖扫描 | `atlas:dependency-analyzer` | 读取依赖清单、构建依赖树 |
| 2 | 问题分析 | `atlas:dependency-analyzer` | 并行执行各类型分析 |
| 3 | 报告生成 | 主进程 | 合并结果、生成统一报告 |
| 4 | 自动修复 | `atlas:atlas-executor` | 执行可自动修复的问题 |

---

## Phase 0: 环境检测

**输入**: --scope 参数

**输出**: 环境配置信息

**检测内容**:

| 检测项 | 说明 |
|:-------|:-----|
| 包管理器 | npm/yarn/pnpm/bun(检测 lockfile) |
| Lockfile | package-lock.json/yarn.lock/pnpm-lock.yaml/bun.lockb |
| 配置文件 | package.json/lerna.json/pnpm-workspace.yaml |
| Monorepo | 检测是否为 monorepo 结构 |
| Node 版本 | 检测 engines 字段和实际版本 |

**操作**:
1. 检测 --scope 指定的目录
2. 识别包管理器类型
3. 读取 package.json 和 lockfile
4. 输出环境信息供后续阶段使用

---

## Phase 1: 依赖扫描

**Subagent**: `atlas:dependency-analyzer`

**输入**: Phase 0 的环境配置

**输出**: `.claude/.meta/dependencies.json`

**扫描内容**:
- dependencies: 生产依赖
- devDependencies: 开发依赖
- peerDependencies: 对等依赖
- optionalDependencies: 可选依赖
- 传递依赖树
- 包元数据(版本、许可证、仓库)

**数据结构**:
```json
{
  "manager": "npm",
  "lockfile": "package-lock.json",
  "dependencies": {
    "react": {
      "version": "18.2.0",
      "type": "dependencies",
      "resolved": "...",
      "license": "MIT",
      "transitives": [...]
    }
  }
}
```

---

## Phase 2: 问题分析

**Subagent**: `atlas:dependency-analyzer` (多个实例并行)

**输入**:
- `.claude/.meta/dependencies.json`
- 分析类型(--type 参数)

**输出**: 各类型分析结果 JSON

**并行策略**:
- --type all: 启动 4 个 analyzer(security、outdated、conflicts、tree)
- --type security: 启动 1 个 analyzer
- 多个类型: 按指定类型启动对应数量

**Subagent Prompt 必须包含**:
1. 分析维度(单一维度)
2. 依赖数据路径
3. 分析规则参考(见下方规则表)
4. 输出格式要求

### 分析规则

#### Security(安全)

| 检查项 | 说明 | 严重性 |
|:-------|:-----|:-------|
| CVE 漏洞 | 已知安全漏洞 | 🔴 critical/high/medium/low |
| 恶意包 | typosquatting、supply chain attack | 🔴 critical |
| 许可证风险 | GPL、AGPL 等传染性许可证 | 🟠 warning |
| 废弃包 | deprecated 标记 | 🟡 info |
| 维护状态 | 长期未更新(>2年) | 🟡 info |

**数据源**:
- npm audit / yarn audit / pnpm audit
- OSV(Open Source Vulnerabilities)
- GitHub Advisory Database

#### Outdated(过期)

| 检查项 | 说明 | 建议 |
|:-------|:-----|:-----|
| 补丁版本 | 1.0.0 → 1.0.5 | 🟢 推荐升级 |
| 次版本 | 1.0.0 → 1.5.0 | 🟡 评估后升级 |
| 主版本 | 1.0.0 → 2.0.0 | 🟠 仔细评估(破坏性变更) |
| 版本差距 | 落后 >10 个小版本 | 🟠 建议分阶段升级 |
| EOL 版本 | React 16.x(已停止支持) | 🔴 尽快升级 |

#### Conflicts(冲突)

| 检查项 | 说明 | 解决方案 |
|:-------|:-----|:---------|
| 版本冲突 | 多个包要求不同版本 | resolutions/overrides |
| Peer Dependency | 未满足的对等依赖 | 安装缺失依赖 |
| 重复包 | 多个版本共存 | dedupe/resolutions |
| 循环依赖 | A→B→C→A | 重构依赖关系 |

#### Tree(依赖树)

| 分析项 | 说明 | 优化建议 |
|:-------|:-----|:---------|
| 依赖深度 | 最大依赖层级 | 减少深度(<5层) |
| 包数量 | 总包数量 | 移除未使用依赖 |
| 包大小 | node_modules 大小 | 寻找更轻量的替代品 |
| 传递依赖 | 间接依赖数量 | 审查必要性 |
| 冗余依赖 | 多个包提供相同功能 | 统一工具链 |

### 输出格式

每个 analyzer 实例输出 JSON,包含:
- `type`: 分析类型
- `timestamp`: 时间戳
- `issues[]`: 问题列表(包含 severity、package、version、message、solution、autoFixable)
- `summary`: 统计信息(critical、warning、info、total)

---

## Phase 3: 报告生成

**执行者**: 主进程

**输入**: Phase 2 各类型的分析结果 JSON

**输出**: `.claude/deps/report-{date}.md`

**报告包含**:
- 概览(包管理器、总依赖数、检测到的问题数)
- 安全报告(漏洞清单、CVSS 评分、影响包、修复命令)
- 过期报告(当前版本、最新版本、版本差距、升级建议)
- 冲突报告(冲突清单、涉及包、解决方案)
- 依赖树分析(深度、大小、优化建议)
- 修复建议(自动修复和手动修复分组)

**报告示例**:

```markdown
# 依赖分析报告

生成时间: 2024-01-15 10:30:00
包管理器: npm 10.2.0
分析范围: /Users/project

## 概览

- 总依赖数: 347 个(直接: 42, 传递: 305)
- 安全漏洞: 3 个(🔴 critical: 1, 🟠 high: 2)
- 过期依赖: 12 个(主版本: 3, 次版本: 9)
- 版本冲突: 2 个
- node_modules 大小: 245 MB

## 🔴 安全漏洞(3)

### [CVE-2024-1234] axios <1.6.0 - SSRF Vulnerability

- **严重性**: 🔴 Critical (CVSS 9.1)
- **当前版本**: 1.4.0
- **修复版本**: ≥1.6.0
- **影响范围**: 直接依赖
- **修复命令**: `npm install axios@^1.6.0`
- **自动修复**: ✅ 可以

...

## 后续建议

1. 优先修复 critical 安全漏洞
2. 使用 `npm dedupe` 消除重复依赖
3. 考虑将 moment.js 替换为 date-fns(减小包大小)
```

---

## Phase 4: 自动修复(可选)

**条件**: 仅当 --fix 或 --interactive 参数存在时执行

**Subagent**: `atlas:atlas-executor`

**输入**: Phase 3 报告中 autoFixable=true 的问题列表

**输出**: 修复后的文件 + 修复报告

**可自动修复的问题**:
- 安全漏洞(版本升级)
- 过期依赖(按 --upgrade 策略升级)
- 重复包(dedupe)
- 缺失的 peer dependency(安装)

**修复策略**:

| 问题类型 | 修复方式 | 命令 |
|:---------|:---------|:-----|
| 安全漏洞 | 升级到修复版本 | `npm install pkg@fixed-version` |
| 过期依赖 | 按策略升级 | `npm update pkg` |
| 重复包 | dedupe | `npm dedupe` |
| Peer Dependency | 安装缺失依赖 | `npm install peer-pkg` |
| 废弃包 | 寻找替代品 | (手动) |

**交互式模式**(--interactive):
```
发现 5 个可自动修复的问题:

1. [CRITICAL] axios 1.4.0 → 1.6.0(修复 CVE-2024-1234)
2. [WARNING] lodash 4.17.15 → 4.17.21(安全更新)
3. [INFO] react 18.2.0 → 18.3.0(功能更新)
4. [INFO] 重复包: webpack 5.88.0 和 5.90.0
5. [WARNING] 缺失 peer: react-dom@^18.0.0

请选择修复项(空格选择,Enter 确认):
[x] 1. axios 升级
[x] 2. lodash 升级
[ ] 3. react 升级
[x] 4. webpack dedupe
[x] 5. 安装 react-dom
```

**修复原则**:
- 优先修复安全漏洞
- 按 --upgrade 策略控制版本跨度
- 保持 lockfile 一致性
- 修复后运行 install 更新 lockfile
- 不自动修复破坏性变更(需人工评估)

**修复报告**包含:修复统计、修复详情、后续建议

---

## 条件执行

| 条件 | 行为 |
|:-----|:-----|
| 无 package.json | 提示不是有效的 Node.js 项目 |
| 无 lockfile | 建议先运行 `npm install` 生成 lockfile |
| --scope 路径无效 | 报错并退出 |
| 无问题检测到 | 报告依赖健康状况良好 |
| --fix 但无可修复项 | 报告无可自动修复的问题 |

---

## 约束

**执行约束**:
- Phase 2 必须使用 `atlas:dependency-analyzer` agent
- Phase 4 必须使用 `atlas:atlas-executor` agent
- 不同分析类型必须并行执行
- 每个 analyzer 只处理单一类型

**分析约束**:
- 只报告问题,不擅自修复(除非 --fix)
- 严格按 CVSS 评分判断漏洞严重性
- 提供可操作的修复命令
- autoFixable 必须谨慎判断

**修复约束**:
- 修复前备份 package.json 和 lockfile
- 修复后验证依赖可安装
- 不跨越主版本(除非 --upgrade major)
- 记录所有修改操作

**报告约束**:
- 问题必须包含包名、版本、严重性
- 必须提供修复命令
- 必须按严重性排序
- 必须说明是否可自动修复

---

## 示例

### 基础用法

```bash
# 全面依赖分析
/deps

# 仅安全检查
/deps --type security

# 检查过期依赖
/deps --type outdated

# 检查并自动修复
/deps --fix

# 交互式修复
/deps --interactive

# 指定范围
/deps --scope packages/core
```

### 高级用法

```bash
# 安全检查并自动修复
/deps --type security --fix

# 升级次版本
/deps --type outdated --upgrade minor --fix

# 排除开发依赖
/deps --no-dev

# 依赖树分析
/deps --type tree

# Monorepo 特定包
/deps --scope packages/api --type security
```

### 配合其他命令

```bash
# 工作流示例
/deps --type security              # 1. 检测安全问题
/deps --type security --fix        # 2. 自动修复
npm test                           # 3. 运行测试验证
/atlas:review --scope package.json # 4. 审查变更
```

---

## 支持的包管理器

| 包管理器 | Lockfile | Audit 命令 | Dedupe |
|:---------|:---------|:-----------|:-------|
| npm | package-lock.json | `npm audit` | `npm dedupe` |
| yarn | yarn.lock | `yarn audit` | `yarn dedupe` |
| pnpm | pnpm-lock.yaml | `pnpm audit` | `pnpm dedupe` |
| bun | bun.lockb | `bun audit` | (内置) |

---

## 注意事项

- 分析需要读取 lockfile,确保已运行过 install
- 安全漏洞数据来自 npm audit 和公开数据库
- 自动修复可能引入破坏性变更,建议先测试
- Monorepo 需要分别分析各包或使用 --scope
- 优先使用项目配置的包管理器
