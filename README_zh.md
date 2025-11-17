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

**适用场景**:
- 批量文件操作
- 项目级代码重构
- 大规模代码修改
- 复杂多步骤任务

**文档**: 查看 [atlas/](./atlas/) 目录

## 安装

### 快速开始

```bash
# 1. 添加 marketplace
/plugin marketplace add Hwwwww-dev/claude-plugins

# 2. 安装 Atlas 插件
/plugin install atlas@claude-code-marketplace

# 3. 重启 Claude Code
```

### 本地开发

```bash
# 添加本地 marketplace
/plugin marketplace add ./claude-code-marketplace

# 本地安装插件
/plugin install atlas@claude-code-marketplace
```

## 使用方法

### Atlas 插件

```bash
# 基本用法
/atlas 给所有 React 组件添加 TypeScript 类型定义

# 强制并行执行
/atlas 批量重构所有 class components --parallel

# 预览模式
/atlas 给所有组件添加 error boundary --dry-run

# 限制并发数
/atlas 优化所有 API --max-agents 3
```

或使用自然语言（自动触发）:
```
"帮我给所有组件添加 props 验证"
"批量重命名所有 API 函数"
"重构整个 authentication 模块"
```

## 插件结构

```
claude-code-marketplace/
├── .claude-plugin/
│   └── marketplace.json       # Marketplace 配置
├── atlas/                      # Atlas 插件
│   ├── .claude-plugin/
│   │   └── plugin.json        # 插件元数据
│   ├── agents/                # 专业化 agents
│   │   ├── atlas-coordinator.md      # 任务协调器
│   │   ├── atlas-executor.md         # 任务执行器
│   │   ├── code-analyzer.md          # 代码质量分析
│   │   ├── architecture-analyzer.md  # 架构分析
│   │   ├── security-scanner.md       # 安全扫描
│   │   └── performance-analyzer.md   # 性能分析
│   ├── commands/
│   │   └── atlas.md           # /atlas 命令
│   ├── skills/                # 智能工作流
│   │   ├── atlas/SKILL.md     # 任务协调
│   │   └── implement/SKILL.md # 功能实现
│   └── examples/              # 可选示例
├── docs/                       # 参考文档
├── README.md                   # 英文文档
└── README_zh.md                # 本文件（中文）
```

## 贡献

欢迎贡献！请随时提交 issue 或 pull request。

### 开发指南

1. 遵循 Claude Code 插件最佳实践
2. 维护清晰的文档
3. 在适用的地方添加测试
4. 遵循现有的代码风格

## 支持

- 📝 报告问题: [GitHub Issues](https://github.com/Hwwwww-dev/claude-plugins/issues)
- 💬 讨论: [GitHub Discussions](https://github.com/Hwwwww-dev/claude-plugins/discussions)

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 致谢

基于 Claude Code 强大的插件系统构建。特别感谢 Anthropic 团队创造了如此可扩展的平台。

---

**用 ❤️ 制作，作者 Hwwwww**
