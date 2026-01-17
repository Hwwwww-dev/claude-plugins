---
description: 依赖管理命令。分析项目依赖,检测安全漏洞、版本冲突、升级建议,支持自动修复。
argument-hint: [--scope path] [--type security|outdated|conflicts|tree|all] [--fix] [--upgrade major|minor|patch]
---

# /deps - 依赖管理

用户输入: $ARGUMENTS

---

## 第一步:确认执行选项

**分阶段确认选项**

**第一个 AskUserQuestion: 执行模式与分析范围**

如果用户未指定选项,询问:

```
问题1: 分析类型
- security: 安全漏洞检测(CVE、恶意包)
- outdated: 过期依赖分析(版本差距、更新建议)
- conflicts: 版本冲突检测(peer dependency、重复包)
- tree: 依赖树分析(深度、包大小、冗余)
- all: 全部分析(默认推荐)

问题2: 分析范围
- 项目根目录(默认推荐)
- 指定路径: 输入具体路径(如 packages/core)
```

**第二个 AskUserQuestion: 分析配置**

询问分析深度和修复策略:

```
问题1: 修复策略
- report: 仅生成报告(默认推荐)
- fix: 自动修复可修复的问题
- interactive: 交互式选择修复项

问题2: 升级策略(仅当分析类型包含 outdated 时询问)
- patch: 仅补丁版本(1.0.x, 默认推荐)
- minor: 次版本升级(1.x.0)
- major: 主版本升级(x.0.0, 可能有破坏性变更)

问题3: 依赖范围
- 包含开发依赖(默认推荐)
- 仅生产依赖(排除 devDependencies)
```

**自动模式行为**(用户指定了 `--fix` 或完整参数时):
- 用户参数优先；未指定则 `type=all`、`scope=.`、`upgrade=patch`；修复策略由 `--fix/--interactive` 决定；依赖范围由 `--no-dev` 控制

**如果用户已指定(如 `/deps --type security --fix`),跳过相关询问。**

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

**报告包含**: 概览 / security / outdated / conflicts / tree / 修复建议（按严重性排序）。

```markdown
# 依赖分析报告

生成时间: <ISO-8601>
包管理器: <npm|yarn|pnpm|bun> <version>
分析范围: <scope>

## 概览
- 总依赖数: X（direct: A, transitive: B）
- 安全漏洞: critical/high/medium/low/total
- 过期依赖: major/minor/patch/total
- 冲突: N | 依赖深度: D | 体积: S

## 关键问题（按严重性）
- [CRITICAL] <pkg>@<version> → <fixedIn> | CVE/CVSS | 命令: <cmd> | autoFixable: true/false

## 后续建议
- 先修复 critical/high，再做 minor/major 升级
- 修复后执行 install + 测试验证
```

---

## Phase 4: 自动修复(可选)

**条件**: 仅当 --fix 或 --interactive 参数存在时执行

**Subagent**: `atlas:atlas-executor`

**输入**: Phase 3 报告中 autoFixable=true 的问题列表

**输出**: 修复后的文件 + 修复报告

**可自动修复**: 安全漏洞升级 / outdated（按 `--upgrade`）/ dedupe / 缺失 peer 安装。

**修复策略**:

| 问题类型 | 修复方式 | 命令 |
|:---------|:---------|:-----|
| 安全漏洞 | 升级到修复版本 | `npm install pkg@fixed-version` |
| 过期依赖 | 按策略升级 | `npm update pkg` |
| 重复包 | dedupe | `npm dedupe` |
| Peer Dependency | 安装缺失依赖 | `npm install peer-pkg` |
| 废弃包 | 寻找替代品 | (手动) |

**修复原则**: 先安全后更新；不跨 major（除非显式允许）；修改 `package.json/lockfile` 后必须 install + 测试；记录所有修改。

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

**执行**: Phase2 仅 `atlas:dependency-analyzer`；Phase4 仅 `atlas:atlas-executor`；按类型并行（单实例单维度）。  
**分析/报告**: 只报告不修复（除非 `--fix`/`--interactive`）；CVSS 严格分级；每条问题给命令+autoFixable；按严重性排序。  
**修复**: 备份 `package.json/lockfile`；不跨 major（除非 `--upgrade major`）；修复后 install + 验证；记录修改。

---

## 示例

```bash
/deps                               # 全量分析（默认 all）
/deps --type security               # 仅安全
/deps --type outdated --upgrade minor
/deps --type security --fix         # 安全 + 自动修复
/deps --interactive --scope packages/core
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
