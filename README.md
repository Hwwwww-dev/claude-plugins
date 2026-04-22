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
- 🔍 **Intelligent Information Gathering**: Auto-analyze project structure, dependencies, code patterns
- 🔧 **Code Quality Tools**: Code review and intelligent refactoring
- 📦 **Dependency Management**: Security scanning, version analysis, conflict detection
- 🏥 **Project Health Check**: One-click diagnosis with comprehensive scoring

**Use Cases**:
- Batch file operations and project-wide refactoring
- Code review and quality assurance
- Dependency security audit and updates
- Project health monitoring
- Bug diagnosis and automated fixes

**Documentation**: See [atlas/](./atlas/) directory

### 🧠 Ideation - Multi-Role Brainstorming Framework

A multi-expert brainstorming framework that explores problems through Socratic dialogue and expert debates.

**Features**:
- 🎭 **13 Professional Experts**: Product Manager, Architect, UX Designer, Security Expert, etc.
- 💬 **Socratic Dialogue**: Uncover hidden assumptions through questioning
- ⚔️ **Expert Debates**: Multi-perspective discussions with constructive conflicts
- 🎯 **Preset Expert Groups**: product, tech, quality, business, all
- 📋 **Structured Output**: Consensus, disagreements, and actionable recommendations

**Use Cases**:
- Vague product ideas requiring systematic exploration
- Technical solutions needing multi-angle evaluation
- Major decisions requiring comprehensive risk assessment
- Complex problems needing cross-domain expert collision

**Documentation**: See [ideation/](./ideation/) directory

### 🧠 Mnemosyne - Context Memory Management

Named after the Greek goddess of memory, this plugin manages session context so your work progress is never lost.

**Features**:
- 💾 **One-Click Save**: Intelligently extract key information from current session (requirements, decisions, code changes, progress)
- 📥 **Quick Restore**: Load historical context in new sessions, seamlessly continue work
- 🔍 **Full-Text Search**: Search historical sessions by title, tags, or content
- 🏷️ **Auto Tagging**: Automatically generate tags for tech stack, task type, etc.
- ✅ **Quality Check**: Built-in completeness check ensures context is recoverable

**Use Cases**:
- Save and restore progress for long-term projects
- Continue complex tasks across sessions
- Team knowledge transfer and handover
- Work logs and decision records

**Documentation**: See [mnemosyne/](./mnemosyne/) directory

## Installation

### Quick Start

```bash
# 1. Add marketplace
/plugin marketplace add Hwwwww-dev/cc-plugins

# 2. Install plugins
/plugin install atlas@cc-plugins
/plugin install ideation@cc-plugins
/plugin install mnemosyne@cc-plugins

# 3. Restart Claude Code
```

### Local Development

```bash
# Add local marketplace
/plugin marketplace add ./cc-plugins

# Install plugins locally
/plugin install atlas@cc-plugins
/plugin install ideation@cc-plugins
/plugin install mnemosyne@cc-plugins
```

## Usage

### Atlas Plugin

Atlas provides 7 orchestration/analysis skills, 2 query skills, and 5 specialized agents:

#### Orchestration & Analysis Skills

| Skill | Description |
|-------|-------------|
| `atlas:orchestrate` | Task coordination and parallel execution |
| `atlas:gather` | Intelligent information gathering |
| `atlas:review` | Multi-dimensional code review |
| `atlas:refactor` | Intelligent code refactoring |
| `atlas:bugfix` | Bug diagnosis and fix suggestions |
| `atlas:deps` | Dependency management and security |
| `atlas:health` | Project health diagnostics |

#### Query Skills (Read-only)

| Skill | Description | Example |
|-------|-------------|---------|
| `atlas:dep-query` | Dependency version, vulnerability, usage | "axios version", "outdated deps" |
| `atlas:git-query` | Commit history, contributors, changes | "recent commits", "who modified auth" |

#### Example Usage

```bash
# Task orchestration
/skill atlas:orchestrate  # then: Add TypeScript types to all React components

# Code review
/skill atlas:review  # then: scope=src/ type=security,performance

# Bug fix
/skill atlas:bugfix  # then: describe the bug symptom

# Intelligent refactoring
/skill atlas:refactor  # then: extract-method scope=src/utils

# Dependency management
/skill atlas:deps  # then: --type security --fix

# Project health check
/skill atlas:health
```

### Ideation Plugin

#### Multi-Role Brainstorming (/ideation:brainstorm)

```bash
# Product exploration
/ideation:brainstorm "Add social features to e-commerce platform" --group product --depth normal

# Technical solution
/ideation:brainstorm "Design high-concurrency flash sale system" --group tech --depth deep

# Business decision
/ideation:brainstorm "Should we enter overseas market" --group business

# Comprehensive evaluation (all 13 experts)
/ideation:brainstorm "Should we adopt microservice architecture" --group all --depth deep
```

**Available Expert Groups**:
| Group | Experts | Use Case |
|-------|---------|----------|
| product | Product Manager, UX Designer, Market Analyst | Product requirements, user experience |
| tech | Architect, Frontend, Backend, DB, DevOps | Technical solutions, architecture design |
| quality | Security, Performance, Tech Lead | Quality assurance, security review |
| business | PM, Market Analyst, Legal, Data Analyst | Business feasibility, compliance |
| all | All 13 experts | Complex decisions, full evaluation |

### Mnemosyne Plugin

Mnemosyne provides 7 commands for session context management:

#### Commands

| Command | Description |
|---------|-------------|
| `/mnemosyne:save` | Save current session context |
| `/mnemosyne:load` | Load historical context |
| `/mnemosyne:list` | View all saved sessions |
| `/mnemosyne:search` | Search historical sessions |
| `/mnemosyne:delete` | Delete specified context |
| `/mnemosyne:stats` | Display storage statistics |
| `/mnemosyne:clean` | Clean up expired contexts |

#### Example Usage

```bash
# Save current session (auto-extract key info)
/mnemosyne:save

# Save with tags
/mnemosyne:save --tags feature,auth,React

# Load most recent context
/mnemosyne:load --latest

# Load by ID
/mnemosyne:load 20241225-103000

# View all saved sessions
/mnemosyne:list

# Search historical sessions
/mnemosyne:search auth
/mnemosyne:search --tag feature --after 2024-12-01

# View statistics
/mnemosyne:stats

# Clean contexts older than 30 days
/mnemosyne:clean --before 30d
```

## Plugin Structure

```
cc-plugins/
├── .claude-plugin/
│   └── marketplace.json            # Marketplace configuration
├── atlas/                           # Atlas plugin (v3.0.0)
│   ├── .claude-plugin/
│   │   └── plugin.json             # Plugin metadata
│   ├── agents/                     # Specialized agents (5)
│   │   ├── atlas-executor.md       # Task executor
│   │   ├── code-reviewer.md        # Code review expert
│   │   ├── dependency-analyzer.md  # Dependency analysis
│   │   ├── information-gatherer.md # Information gatherer
│   │   └── task-planner.md         # Task planner
│   ├── hooks/
│   │   └── hooks.json              # Hooks configuration
│   └── skills/                     # Skills (9)
│       ├── orchestrate/            # Task orchestration
│       ├── gather/                 # Information gathering
│       ├── review/                 # Code review
│       ├── refactor/               # Intelligent refactoring
│       ├── bugfix/                 # Bug diagnosis & fix
│       ├── deps/                   # Dependency management
│       ├── health/                 # Health diagnostics
│       ├── dep-query/              # Dependency query
│       └── git-query/              # Git query
├── ideation/                        # Ideation plugin
│   ├── .claude-plugin/
│   │   └── plugin.json             # Plugin metadata
│   ├── agents/                     # 14 expert agents
│   ├── commands/
│   │   └── brainstorm.md           # /ideation:brainstorm command
│   └── skills/
│       └── brainstorm/             # Brainstorming workflow
├── mnemosyne/                       # Mnemosyne plugin (v2.1.0)
│   ├── .claude-plugin/
│   │   └── plugin.json             # Plugin metadata
│   ├── commands/                   # Commands (7)
│   │   ├── save.md                 # /mnemosyne:save
│   │   ├── load.md                 # /mnemosyne:load
│   │   ├── list.md                 # /mnemosyne:list
│   │   ├── search.md               # /mnemosyne:search
│   │   ├── delete.md               # /mnemosyne:delete
│   │   ├── stats.md                # /mnemosyne:stats
│   │   └── clean.md                # /mnemosyne:clean
│   └── skills/                     # Implementation engine (3)
│       ├── context-save/
│       ├── context-load/
│       └── context-search/
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

- 📝 Report Issues: [GitHub Issues](https://github.com/Hwwwww-dev/cc-plugins/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/Hwwwww-dev/cc-plugins/discussions)

## License

MIT License - see [LICENSE](LICENSE) file for details

## Acknowledgments

Built with Claude Code's powerful plugin system. Special thanks to the Anthropic team for creating such an extensible platform.

---

**Made with ❤️ by Hwwwww**
