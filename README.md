# Claude Code Marketplace

> Community marketplace for Claude Code plugins

[中文文档](./README_zh.md)

## Overview

This repository contains a collection of Claude Code plugins focused on enhancing task automation and workflow efficiency.

## Available Plugins

### 🚀 Atlas - Task Orchestration Framework

A powerful task coordination and parallel execution framework for Claude Code.

**Features**:
- 🎯 **Smart Task Decomposition**: Automatically breaks down complex tasks into parallelizable subtasks
- 🚀 **Concurrent Execution**: Runs multiple tasks simultaneously for significant speed improvements
- 🧩 **Flexible Orchestration**: Supports parallel, sequential, and mixed execution strategies
- 📊 **Result Aggregation**: Automatically collects and organizes all subtask execution results

**Use Cases**:
- Batch file operations
- Project-wide refactoring
- Large-scale code modifications
- Multi-step dependency tasks

**Documentation**: See [atlas/](./atlas/) directory

## Installation

### Quick Start

```bash
# 1. Add marketplace
/plugin marketplace add Hwwwww-dev/claude-plugins

# 2. Install Atlas plugin
/plugin install atlas@claude-code-marketplace

# 3. Restart Claude Code
```

### Local Development

```bash
# Add local marketplace
/plugin marketplace add ./claude-code-marketplace

# Install plugin locally
/plugin install atlas@claude-code-marketplace
```

## Usage

### Atlas Plugin

```bash
# Basic usage
/atlas Add TypeScript types to all React components

# Force parallel execution
/atlas Refactor all class components --parallel

# Preview mode
/atlas Add error boundaries to all components --dry-run

# Limit concurrency
/atlas Optimize all APIs --max-agents 3
```

Or use natural language (automatically triggers):
```
"Help me add props validation to all components"
"Batch rename all API functions"
"Refactor the entire authentication module"
```

## Plugin Structure

```
claude-code-marketplace/
├── .claude-plugin/
│   └── marketplace.json       # Marketplace configuration
├── atlas/                      # Atlas plugin
│   ├── .claude-plugin/
│   │   └── plugin.json        # Plugin metadata
│   ├── agents/                # Specialized agents
│   │   ├── atlas-coordinator.md      # Task coordinator
│   │   ├── atlas-executor.md         # Task executor
│   │   ├── code-analyzer.md          # Code quality analysis
│   │   ├── architecture-analyzer.md  # Architecture analysis
│   │   ├── security-scanner.md       # Security scanning
│   │   └── performance-analyzer.md   # Performance analysis
│   ├── commands/
│   │   └── atlas.md           # /atlas command
│   ├── skills/                # Intelligent workflows
│   │   ├── atlas/SKILL.md     # Task orchestration
│   │   └── implement/SKILL.md # Feature implementation
│   └── examples/              # Optional examples
├── docs/                       # Reference documentation
├── README.md                   # This file (English)
└── README_zh.md                # Chinese documentation
```

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

### Development Guidelines

1. Follow Claude Code plugin best practices
2. Maintain clear documentation
3. Add tests where applicable
4. Follow the existing code style

## Support

- 📝 Report Issues: [GitHub Issues](https://github.com/Hwwwww-dev/claude-plugins/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/Hwwwww-dev/claude-plugins/discussions)

## License

MIT License - see [LICENSE](LICENSE) file for details

## Acknowledgments

Built with Claude Code's powerful plugin system. Special thanks to the Anthropic team for creating such an extensible platform.

---

**Made with ❤️ by Hwwwww**
