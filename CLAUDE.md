# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个 Claude Code 插件市场仓库,包含多个专业插件:

- **Atlas**: 任务协调框架插件,通过智能协调器和执行器实现项目级批量操作,支持项目分析、依赖梳理、代码探索
- **Ideation**: 多角色头脑风暴框架,通过苏格拉底式对话和专家辩论深度探索问题本质
- **Mnemosyne**: 上下文记忆管理插件,支持保存、加载、搜索会话上下文,实现跨会话知识延续

## 项目架构

### 目录结构

```
cc-plugins/
├── .claude-plugin/
│   └── marketplace.json          # 市场配置,定义插件列表和元数据
├── atlas/                         # Atlas 任务协调框架插件
│   ├── .claude-plugin/
│   │   └── plugin.json           # 插件元数据(名称、版本、描述等)
│   ├── agents/                   # 专业化 agents (8个)
│   │   ├── atlas-executor.md     # 任务执行器: 执行具体的子任务
│   │   ├── code-reviewer.md      # 代码审查: 多维度代码质量分析
│   │   ├── commit-analyzer.md    # 提交分析: Git 提交历史分析
│   │   ├── dependency-analyzer.md # 依赖分析: 依赖关系与安全检查
│   │   ├── information-gatherer.md # 信息收集: 收集和分析项目信息
│   │   ├── task-planner.md            # 规划器: 任务规划与分解
│   │   ├── repo-context-indexer.md # 仓库索引: 项目上下文建立
│   │   └── repo-semantic-analyzer.md # 语义分析: 代码语义理解
│   ├── hooks/                    # Hooks 配置
│   │   └── hooks.json            # PreToolUse hooks: 防止嵌套调用
│   └── skills/                   # Skills (13个)
│       ├── orchestrate/          # 任务协调与并发执行引擎
│       ├── gather/               # 智能信息收集
│       ├── review/               # 多维度代码审查
│       ├── refactor/             # 智能重构
│       ├── bugfix/               # 问题诊断与修复
│       ├── test-gen/             # 自动化测试生成
│       ├── deps/                 # 依赖管理
│       ├── health/               # 项目健康检查
│       ├── changelog/            # 变更日志生成
│       ├── repo-wiki/            # 仓库文档编排
│       ├── dep-query/            # 依赖查询: 版本、漏洞、使用位置
│       ├── git-query/            # Git 查询: 提交、贡献者、分支
│       └── wiki-query/           # Wiki 查询: 项目结构、API、模块
├── ideation/                      # Ideation 多角色头脑风暴插件
│   ├── .claude-plugin/
│   │   └── plugin.json           # 插件元数据
│   ├── agents/                   # 专家角色 agents (14个)
│   │   ├── debate-moderator.md   # 辩论主持人: 协调专家讨论
│   │   ├── product-manager.md    # 产品经理: 需求与用户价值
│   │   ├── architect.md          # 架构师: 系统设计与技术选型
│   │   ├── tech-lead.md          # 技术负责人: 工程实践与团队协调
│   │   ├── frontend-engineer.md  # 前端工程师: UI/UX 实现
│   │   ├── backend-engineer.md   # 后端工程师: 服务端逻辑
│   │   ├── database-expert.md    # 数据库专家: 数据建模与优化
│   │   ├── devops-engineer.md    # DevOps 工程师: 部署与运维
│   │   ├── security-expert.md    # 安全专家: 安全评估与防护
│   │   ├── performance-expert.md # 性能专家: 性能优化
│   │   ├── ux-designer.md        # UX 设计师: 用户体验
│   │   ├── data-analyst.md       # 数据分析师: 数据驱动决策
│   │   ├── legal-advisor.md      # 法务顾问: 合规与隐私
│   │   └── market-analyst.md     # 市场分析师: 市场与竞争
│   ├── commands/
│   │   └── brainstorm.md         # /brainstorm 命令定义
│   └── skills/
│       └── brainstorm/           # 头脑风暴工作流 skill
├── mnemosyne/                     # Mnemosyne 上下文记忆插件
│   ├── .claude-plugin/
│   │   └── plugin.json           # 插件元数据
│   └── commands/                 # 记忆管理命令 (7个)
│       ├── save.md               # /save 保存当前会话上下文
│       ├── load.md               # /load 加载历史上下文
│       ├── list.md               # /list 查看保存的上下文列表
│       ├── search.md             # /search 搜索历史上下文
│       ├── delete.md             # /delete 删除指定上下文
│       ├── clean.md              # /clean 清理过期上下文
│       └── stats.md              # /stats 显示存储统计
├── docs/                         # Claude Code 插件系统参考文档
└── README.md / README_zh.md      # 项目说明文档
```

### 核心概念

1. **Marketplace**: 通过 `.claude-plugin/marketplace.json` 定义,包含插件列表和市场元数据
2. **Plugin**: 每个插件有独立目录,通过 `.claude-plugin/plugin.json` 定义元数据
3. **Agents**: 专业化的子代理,用 markdown 文件定义,包含 frontmatter (name, description, model, color) 和提示词
4. **Skills**: 可复用的工作流,包含 SKILL.md 定义和必要的资源文件,通过 Skill tool 调用
5. **Hooks**: 系统级约束机制,通过 `hooks/hooks.json` 定义,用于强制执行规则（如防止嵌套调用）

### Atlas 工作流程

1. 用户通过 `atlas:orchestrate` skill 或触发词("批量"、"所有"、"项目级"等)触发
2. (可选) Information Gatherer agent 收集项目信息并缓存到 Memory
3. Plan agent 分析任务并生成详细的执行计划
4. 根据计划并发启动多个 atlas-executor agents
5. 各执行器独立完成子任务
6. 收集和汇总所有执行结果

### Ideation 工作流程

1. 用户通过 `/brainstorm <话题>` 触发多角色头脑风暴
2. 主持人(debate-moderator)分析话题,智能推荐相关专家组合
3. 用户确认或自定义专家阵容
4. 苏格拉底式对话阶段: 通过提问引导深入思考
5. 专家辩论阶段: 各领域专家从不同角度分析和讨论
6. 主持人总结共识、分歧和行动建议

## 版本管理指南

### 版本号规范

项目遵循语义化版本 (Semantic Versioning 2.0.0):
- **MAJOR.MINOR.PATCH** (例如: 2.21.0)
  - MAJOR: 不兼容的 API 变更
  - MINOR: 向后兼容的功能新增
  - PATCH: 向后兼容的问题修正

### 版本同步规则

**核心原则**: marketplace 版本 = atlas 插件版本（主插件）

| 文件 | 字段 | 说明 |
|------|------|------|
| `.claude-plugin/marketplace.json` | `metadata.version` | 市场版本，与主插件同步 |
| `.claude-plugin/marketplace.json` | `plugins[atlas].version` | atlas 在市场中的版本 |
| `atlas/.claude-plugin/plugin.json` | `version` | atlas 插件实际版本 |
| `ideation/.claude-plugin/plugin.json` | `version` | ideation 独立版本 |
| `mnemosyne/.claude-plugin/plugin.json` | `version` | mnemosyne 独立版本 |

**更新时机**:
- 修改 atlas 插件 → 同步更新 marketplace + atlas 三处版本
- 修改 ideation/mnemosyne → 仅更新对应插件版本
- Agent/Skill frontmatter 版本仅在该组件有重大变更时更新

### 修改版本号的步骤

**Step 1**: 确定新版本号（基于变更类型）

**Step 2**: 更新以下文件（atlas 变更时）

```
.claude-plugin/marketplace.json     → metadata.version + plugins[atlas].version
atlas/.claude-plugin/plugin.json    → version
```

**Step 3**: 验证版本一致性

```bash
grep -E '"version"' .claude-plugin/marketplace.json atlas/.claude-plugin/plugin.json
```

### 版本更新检查清单

发布新版本前务必检查:

- [ ] `marketplace.json` 中 `metadata.version` 已更新
- [ ] `marketplace.json` 中对应插件的 `version` 已更新
- [ ] 对应插件的 `plugin.json` 中 `version` 已更新
- [ ] 三处版本号一致（atlas 变更时）
- [ ] README 已更新（如有文档变更）

## 开发工作流

### 本地测试插件

```bash
# 1. 添加本地市场
/plugin marketplace add ./cc-plugins

# 2. 安装插件
/plugin install atlas@cc-plugins

# 3. 测试命令
/atlas 测试任务

# 4. 修改后需要重新加载
/plugin uninstall atlas@cc-plugins
/plugin install atlas@cc-plugins
```

### 添加新的 Agent

1. 在 `atlas/agents/` 创建 `<agent-name>.md` 文件
2. 添加 frontmatter:
   ```yaml
   ---
   name: agent-name
   description: agent 的功能描述
   version: 1.0.0
   model: sonnet  # 或 haiku, opus
   color: pink    # 可选: blue, green, purple, pink, orange
   ---
   ```
3. 编写 agent 的提示词和工作流程说明
4. 在相关 skill 或 command 中引用该 agent

### 添加新的 Skill

1. 在 `atlas/skills/` 创建目录 `<skill-name>/`
2. 创建 `SKILL.md` 文件,添加 frontmatter:
   ```yaml
   ---
   name: skill-name
   description: skill 的功能描述
   version: 1.0.0
   color: pink
   ---
   ```
3. 编写 skill 的使用指南和工作流程
4. 通过 `/skill skill-name` 或在代码中通过 Skill tool 调用

### 修改现有组件

- **修改 Agent**: 直接编辑对应的 `.md` 文件,更新提示词或流程
- **修改 Skill**: 编辑 `skills/` 目录下的 `SKILL.md`
- 注意: 修改后需要卸载并重新安装插件才能生效

## 注意事项

1. **Frontmatter 必须有效**: agents 和 skills 的 frontmatter 必须是有效的 YAML 格式
2. **描述清晰**: description 应该简洁明确,说明组件的用途和触发场景
3. **版本同步**: 发布时确保所有版本号保持同步
4. **不要使用 tree 命令**: 项目规则禁止使用 tree 命令
5. **遵循 Linus 精神**: 代码应该简洁、高效、直接
6. **中文优先**: 所有交互和文档优先使用简体中文
7. **Hooks 机制**: 嵌套调用约束通过 `atlas/hooks/hooks.json` 中的 PreToolUse hooks 强制执行,无需在文档中重复说明

## 参考文档

详细的技术规范请参考 `docs/` 目录:
- `plugins.md`: 插件系统完整说明
- `subagents.md`: Agents 系统详解
- `skills.md`: Skills 系统详解
- `plugin-marketplaces.md`: 市场管理指南
- `hooks.md`: Hooks 系统使用指南
- `hook-reference.md`: Hooks API 参考文档
