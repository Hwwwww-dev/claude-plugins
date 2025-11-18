# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个 Claude Code 插件市场仓库,包含 Atlas 任务协调框架插件。Atlas 是一个强大的任务分解和并发执行框架,通过智能协调器和执行器实现项目级批量操作。v1.3.0 新增智能信息收集系统,支持项目分析、依赖梳理、代码探索。

## 项目架构

### 目录结构

```
claude-code-marketplace/
├── .claude-plugin/
│   └── marketplace.json          # 市场配置,定义插件列表和元数据
├── atlas/                         # Atlas 插件目录
│   ├── .claude-plugin/
│   │   └── plugin.json           # 插件元数据(名称、版本、描述等)
│   ├── agents/                   # 专业化 agents
│   │   ├── atlas-executor.md     # 任务执行器: 执行具体的子任务
│   │   └── information-gatherer.md  # 信息收集器: 收集和分析项目信息
│   ├── commands/
│   │   ├── orchestrate.md        # /orchestrate 命令定义
│   │   └── gather.md             # /gather 命令定义
│   ├── hooks/                    # Hooks 配置
│   │   └── hooks.json            # PreToolUse hooks: 防止嵌套调用
│   └── skills/
│       ├── task-orchestrator/SKILL.md  # 任务协调 skill
│       ├── implement/SKILL.md          # 功能实现工作流 skill
│       └── gather/SKILL.md             # 信息收集工作流 skill
├── docs/                         # Claude Code 插件系统参考文档
└── README.md / README_zh.md      # 项目说明文档
```

### 核心概念

1. **Marketplace**: 通过 `.claude-plugin/marketplace.json` 定义,包含插件列表和市场元数据
2. **Plugin**: 每个插件有独立目录,通过 `.claude-plugin/plugin.json` 定义元数据
3. **Agents**: 专业化的子代理,用 markdown 文件定义,包含 frontmatter (name, description, model, color) 和提示词
4. **Commands**: 斜杠命令,用 markdown 文件定义,通过 `/command-name` 调用
5. **Skills**: 可复用的工作流,包含 SKILL.md 定义和必要的资源文件
6. **Hooks**: 系统级约束机制,通过 `hooks/hooks.json` 定义,用于强制执行规则（如防止嵌套调用）

### Atlas 工作流程

1. 用户通过 `/orchestrate <任务>` 或触发词("批量"、"所有"、"项目级"等)触发
2. (可选) Information Gatherer agent 收集项目信息并缓存到 Memory
3. Plan agent 分析任务并生成详细的执行计划
4. 根据计划并发启动多个 atlas-executor agents
5. 各执行器独立完成子任务
6. 收集和汇总所有执行结果

## 版本管理指南

### 版本号规范

项目遵循语义化版本 (Semantic Versioning 2.0.0):
- **MAJOR.MINOR.PATCH** (例如: 1.0.0)
  - MAJOR: 不兼容的 API 变更
  - MINOR: 向后兼容的功能新增
  - PATCH: 向后兼容的问题修正

### 修改版本号的步骤

当需要发布新版本时,**必须同步更新以下文件**:

1. **市场配置文件** (根级别)
   ```bash
   # 文件: .claude-plugin/marketplace.json
   # 位置: 第 9 行
   "version": "1.0.0"  # 修改此处
   ```

2. **插件元数据** (每个插件独立版本)
   ```bash
   # 文件: atlas/.claude-plugin/plugin.json
   # 位置: 第 4 行
   "version": "1.0.0"  # 修改此处
   ```

3. **市场配置中的插件版本**
   ```bash
   # 文件: .claude-plugin/marketplace.json
   # 位置: plugins 数组中对应插件的 version 字段 (第 16 行)
   "version": "1.0.0"  # 修改此处
   ```

4. **Agent frontmatter** (如果 agent 有重大变更)
   ```bash
   # 示例: atlas/agents/atlas-executor.md
   # 位置: 第 4 行
   version: 1.0.0  # 修改此处
   ```

5. **Skill frontmatter** (如果 skill 有重大变更)
   ```bash
   # 示例: atlas/skills/atlas/SKILL.md
   # 位置: 第 4 行
   version: 1.0.0  # 修改此处
   ```

### 版本更新命令

```bash
# 1. 修改版本号 (按上述步骤)
# 2. 提交变更
git add .
git commit -m "chore: bump version to x.y.z"

# 3. 创建 git tag
git tag -a vx.y.z -m "Release version x.y.z"

# 4. 推送到远程仓库
git push origin main
git push origin vx.y.z
```

### 版本更新示例

假设要从 1.0.0 升级到 1.1.0 (新增功能):

```bash
# 使用 sed 批量修改 (macOS 用户注意 -i 后需要 '')
sed -i '' 's/"version": "1.0.0"/"version": "1.1.0"/g' .claude-plugin/marketplace.json
sed -i '' 's/"version": "1.0.0"/"version": "1.1.0"/g' atlas/.claude-plugin/plugin.json
sed -i '' 's/version: 1.0.0/version: 1.1.0/g' atlas/skills/atlas/SKILL.md

# 验证修改
grep -r "1.1.0" .claude-plugin/ atlas/.claude-plugin/ atlas/agents/ atlas/skills/

# 提交
git add .
git commit -m "chore: bump version to 1.1.0"
git tag -a v1.1.0 -m "Release version 1.1.0"
git push origin main --tags
```

### 版本更新检查清单

发布新版本前务必检查:

- [ ] marketplace.json 中的 metadata.version 已更新
- [ ] marketplace.json 中对应插件的 version 已更新
- [ ] atlas/.claude-plugin/plugin.json 中的 version 已更新
- [ ] 相关 agents 的 version frontmatter 已更新 (如有变更)
- [ ] 相关 skills 的 version frontmatter 已更新 (如有变更)
- [ ] README.md 和 README_zh.md 已更新 (如有文档变更)
- [ ] 所有版本号一致
- [ ] git tag 已创建
- [ ] 变更已推送到远程仓库

## 开发工作流

### 本地测试插件

```bash
# 1. 添加本地市场
/plugin marketplace add ./claude-code-marketplace

# 2. 安装插件
/plugin install atlas@claude-code-marketplace

# 3. 测试命令
/atlas 测试任务

# 4. 修改后需要重新加载
/plugin uninstall atlas@claude-code-marketplace
/plugin install atlas@claude-code-marketplace
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
- **修改 Command**: 编辑 `commands/` 目录下的对应文件
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
