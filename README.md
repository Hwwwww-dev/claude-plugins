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
- 🔍 **Intelligent Information Gathering**: Auto-analyze project structure, dependencies, code patterns (v1.3.0 new)

**Use Cases**:
- Batch file operations
- Project-wide refactoring
- Large-scale code modifications
- Multi-step dependency tasks
- Project structure analysis and code exploration (new)

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

#### Task Orchestration (/orchestrate)

```bash
# Basic usage
/orchestrate Add TypeScript types to all React components

# Force parallel execution
/orchestrate Refactor all class components --parallel

# Preview mode
/orchestrate Add error boundaries to all components --dry-run

# Limit concurrency
/orchestrate Optimize all APIs --max-agents 3
```

Or use natural language (automatically triggers):
```
"Help me add props validation to all components"
"Batch rename all API functions"
"Refactor the entire authentication module"
```

#### Information Gathering (/gather) - v1.3.0 new

```bash
# Analyze project structure
/gather project-structure --cache project-map

# Analyze dependencies
/gather dependencies UserAPI

# Search code patterns
/gather code-patterns "useState" --focus src/components

# Assess modification impact
/gather impact AuthService
```

Information gathering also supports auto-triggering:
```
"Analyze this project structure"
"Where is UserAPI called?"
"Find all code using the old API"
```

## Plugin Structure

```
claude-code-marketplace/
├── .claude-plugin/
│   └── marketplace.json            # Marketplace configuration
├── atlas/                           # Atlas plugin (v1.3.0)
│   ├── .claude-plugin/
│   │   └── plugin.json             # Plugin metadata
│   ├── agents/                     # Specialized agents
│   │   ├── atlas-executor.md       # Task executor
│   │   └── information-gatherer.md # Information gatherer (new)
│   ├── commands/
│   │   ├── orchestrate.md          # /orchestrate command (formerly /atlas)
│   │   └── gather.md               # /gather command (new)
│   ├── hooks/
│   │   └── hooks.json              # Hooks configuration (including auto-trigger rules)
│   ├── skills/                     # Intelligent workflows
│   │   ├── task-orchestrator/SKILL.md  # Task orchestration (formerly atlas)
│   │   ├── implement/SKILL.md          # Feature implementation
│   │   └── gather/SKILL.md             # Information gathering workflow (new)
│   └── examples/                   # Optional examples
├── docs/                            # Reference documentation
├── README.md                        # This file (English)
└── README_zh.md                     # Chinese documentation
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
