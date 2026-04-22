# Claude Code Marketplace

> Claude Code 插件社区市场

[English Documentation](./README.md)

## 概述

这个仓库包含了一系列专注于提升任务自动化和工作流效率的 Claude Code 插件。

## 可用插件

### 🚀 Atlas - 任务协调框架

强大的任务协调与并发执行框架，专为 Claude Code 设计。

**核心功能**:
- 🎯 **智能任务分解**: 自动将复杂任务拆分为可并行执行的子任务
- 🚀 **并发执行**: 同时运行多个任务，显著提升处理速度
- 🧩 **灵活编排**: 支持并行、串行、混合等多种执行策略
- 📊 **结果聚合**: 自动收集和整理所有子任务的执行结果
- 🔍 **智能信息收集**: 自动分析项目结构、依赖关系、代码模式
- 🔧 **代码审查与重构**: 专业的代码质量检查和智能重构
- 📦 **依赖管理**: 安全漏洞检测、版本冲突分析、升级建议
- 🏥 **项目健康检查**: 一键诊断项目健康度，输出综合评分
- 🐛 **问题诊断与修复**: 根因分析、修复方案、可选自动执行

**适用场景**:
- 批量文件操作和项目级代码重构
- 大规模代码修改和复杂多步骤任务
- 项目结构分析和代码探索
- 代码审查和质量保障
- 依赖管理和安全审计
- 问题诊断与自动修复

**文档**: 查看 [atlas/](./atlas/) 目录

### 💡 Ideation - 多角色头脑风暴框架

通过苏格拉底式对话和专家辩论深度探索问题本质。

**核心功能**:
- 🎭 **13位专业专家**: 产品经理、架构师、前后端工程师、UX设计师、安全/性能专家等
- 💬 **苏格拉底式对话**: 通过提问引导思考，追问假设，暴露矛盾
- ⚔️ **多角色辩论**: 专家间建设性冲突，碰撞产生新洞见
- 📊 **预设专家组**: product/tech/quality/business/all 五种组合
- 🎯 **智能推荐**: 根据话题关键词自动推荐相关专家

**适用场景**:
- 模糊产品想法的系统化探索
- 技术方案多角度评估
- 重大决策全面风险评估
- 复杂问题跨领域专家碰撞

**文档**: 查看 [ideation/](./ideation/) 目录

### 🧠 Mnemosyne - 上下文记忆管理

希腊记忆女神命名的会话上下文管理插件，让你的工作进度永不丢失。

**核心功能**:
- 💾 **一键保存**: 智能提取当前会话的关键信息（需求、决策、代码变更、进度等）
- 📥 **快速恢复**: 在新会话中加载历史上下文，无缝继续工作
- 🔍 **全文搜索**: 按标题、标签、内容搜索历史会话
- 🏷️ **自动标签**: 根据内容自动生成技术栈、任务类型等标签
- ✅ **质量检查**: 内置完整性检查，确保上下文可恢复

**适用场景**:
- 长期项目的进度保存与恢复
- 跨会话的复杂任务延续
- 团队知识传递与交接
- 工作日志与决策记录

**文档**: 查看 [mnemosyne/](./mnemosyne/) 目录

## 安装

### 快速开始

```bash
# 1. 添加 marketplace
/plugin marketplace add Hwwwww-dev/cc-plugins

# 2. 安装插件
/plugin install atlas@cc-plugins
/plugin install ideation@cc-plugins
/plugin install mnemosyne@cc-plugins

# 3. 重启 Claude Code
```

### 本地开发

```bash
# 添加本地 marketplace
/plugin marketplace add ./cc-plugins

# 本地安装插件
/plugin install atlas@cc-plugins
/plugin install ideation@cc-plugins
/plugin install mnemosyne@cc-plugins
```

## 使用方法

### Atlas 插件

Atlas 提供 7 个编排/分析 Skill 与 2 个只读查询 Skill，加上 5 个专业化 agent：

#### 编排 / 分析类 Skill

| Skill | 用途 |
|-------|------|
| `atlas:orchestrate` | 任务编排与并发执行引擎 |
| `atlas:gather` | 智能信息收集 |
| `atlas:review` | 多维度代码审查（security / performance / style / architecture） |
| `atlas:refactor` | 智能重构（模式识别 + 自动化改写） |
| `atlas:bugfix` | 问题诊断与修复建议 |
| `atlas:deps` | 依赖管理（漏洞、冲突、升级建议，支持自动修复） |
| `atlas:health` | 项目健康检查（5 维度综合评分） |

#### 查询 Skill（只读，低成本）

| Skill | 用途 | 示例 |
|-------|------|------|
| `atlas:dep-query` | 依赖版本、漏洞、使用位置查询 | "axios 有什么漏洞？" |
| `atlas:git-query` | 提交历史、贡献者、分支状态查询 | "最近谁改了 auth 模块？" |

> 💡 项目级 API / 类方法 / 模块依赖查询建议直接使用 LSP 的 `workspaceSymbol` / `documentSymbol` 或 Serena MCP。

#### 使用示例

```bash
# 任务编排（触发词：批量、所有、项目级 …）
/skill atlas:orchestrate
→ "给所有 React 组件添加 TypeScript 类型定义"

# 代码审查
/skill atlas:review
→ scope=src/ type=security,performance

# 问题诊断与修复
/skill atlas:bugfix
→ "登录后 token 有时丢失，定位根因并给出修复方案"

# 智能重构
/skill atlas:refactor
→ "extract-duplicates scope=src/"

# 依赖管理
/skill atlas:deps
→ --type security --fix

# 项目健康检查
/skill atlas:health
```

信息收集也支持自动触发：
```
"分析一下这个项目的结构"
"UserAPI 被哪些地方调用了"
"找出所有使用旧版 API 的代码"
```

### Ideation 插件

#### 多角色头脑风暴 (/ideation:brainstorm)

```bash
# 产品探索
/ideation:brainstorm "电商平台增加社交功能" --group product --depth normal

# 技术方案评估
/ideation:brainstorm "设计高并发秒杀系统" --group tech --depth deep

# 商业决策
/ideation:brainstorm "是否进入海外市场" --group business

# 全面评估（13位专家参与）
/ideation:brainstorm "是否采用微服务架构" --group all --depth deep
```

**预设专家组**:
| 组名 | 包含专家 | 适用场景 |
|-----|---------|---------|
| product | 产品经理、UX设计师、市场分析师 | 产品需求、用户体验 |
| tech | 架构师、前后端工程师、数据库专家、DevOps | 技术方案、架构设计 |
| quality | 安全专家、性能专家、技术负责人 | 质量保障、安全评审 |
| business | 产品经理、市场分析师、法务、数据分析师 | 商业可行性、合规 |
| all | 全部13位专家 | 复杂决策、全面评估 |

### Mnemosyne 插件

Mnemosyne 提供 7 个命令用于会话上下文管理：

#### 命令列表

| 命令 | 描述 |
|------|------|
| `/mnemosyne:save` | 保存当前会话上下文 |
| `/mnemosyne:load` | 加载历史上下文 |
| `/mnemosyne:list` | 查看所有保存的会话 |
| `/mnemosyne:search` | 搜索历史会话 |
| `/mnemosyne:delete` | 删除指定上下文 |
| `/mnemosyne:stats` | 显示存储统计信息 |
| `/mnemosyne:clean` | 清理过期上下文 |

#### 使用示例

```bash
# 保存当前会话（自动提取关键信息）
/mnemosyne:save

# 带标签保存
/mnemosyne:save --tags feature,auth,React

# 加载最近的上下文
/mnemosyne:load --latest

# 按 ID 加载
/mnemosyne:load 20241225-103000

# 查看所有保存的会话
/mnemosyne:list

# 搜索历史会话
/mnemosyne:search auth
/mnemosyne:search --tag feature --after 2024-12-01

# 查看统计信息
/mnemosyne:stats

# 清理 30 天前的上下文
/mnemosyne:clean --before 30d
```

## 插件结构

```
cc-plugins/
├── .claude-plugin/
│   └── marketplace.json            # Marketplace 配置
├── atlas/                           # Atlas 插件 (v3.0.0)
│   ├── .claude-plugin/
│   │   └── plugin.json             # 插件元数据
│   ├── agents/                     # 专业化 agents (5个)
│   │   ├── atlas-executor.md       # 任务执行器
│   │   ├── code-reviewer.md        # 代码审查
│   │   ├── dependency-analyzer.md  # 依赖分析
│   │   ├── information-gatherer.md # 信息收集
│   │   └── task-planner.md         # 任务规划
│   ├── hooks/
│   │   └── hooks.json              # Hooks 配置
│   └── skills/                     # Skills (9个)
│       ├── orchestrate/            # 任务协调与并发执行
│       ├── gather/                 # 智能信息收集
│       ├── review/                 # 代码审查
│       ├── refactor/               # 智能重构
│       ├── bugfix/                 # 问题诊断与修复
│       ├── deps/                   # 依赖管理
│       ├── health/                 # 健康检查
│       ├── dep-query/              # 依赖查询
│       └── git-query/              # Git 查询
├── ideation/                        # Ideation 插件
│   ├── .claude-plugin/
│   │   └── plugin.json             # 插件元数据
│   ├── agents/                     # 14 位专家 agent
│   ├── commands/
│   │   └── brainstorm.md           # /ideation:brainstorm 命令
│   └── skills/
│       └── brainstorm/             # 头脑风暴工作流
├── mnemosyne/                       # Mnemosyne 插件 (v2.1.0)
│   ├── .claude-plugin/
│   │   └── plugin.json             # 插件元数据
│   ├── commands/                   # 命令 (7个)
│   │   ├── save.md                 # /mnemosyne:save
│   │   ├── load.md                 # /mnemosyne:load
│   │   ├── list.md                 # /mnemosyne:list
│   │   ├── search.md               # /mnemosyne:search
│   │   ├── delete.md               # /mnemosyne:delete
│   │   ├── stats.md                # /mnemosyne:stats
│   │   └── clean.md                # /mnemosyne:clean
│   └── skills/                     # 实现引擎 (3个)
│       ├── context-save/
│       ├── context-load/
│       └── context-search/
├── docs/                            # 参考文档
├── README.md                        # 英文文档
└── README_zh.md                     # 本文件（中文）
```

## 贡献

欢迎贡献！请随时提交 issue 或 pull request。

### 开发指南

1. 遵循 Claude Code 插件最佳实践
2. 维护清晰的文档
3. 在适用的地方添加测试
4. 遵循现有的代码风格

## 支持

- 📝 报告问题: [GitHub Issues](https://github.com/Hwwwww-dev/cc-plugins/issues)
- 💬 讨论: [GitHub Discussions](https://github.com/Hwwwww-dev/cc-plugins/discussions)

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 致谢

基于 Claude Code 强大的插件系统构建。特别感谢 Anthropic 团队创造了如此可扩展的平台。

---

**用 ❤️ 制作，作者 Hwwwww**
