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
- 🔧 **Code Quality Tools**: Code review, intelligent refactoring, test generation
- 📦 **Dependency Management**: Security scanning, version analysis, conflict detection
- 📝 **Documentation Generation**: Auto-generate repo wiki, changelog, health reports

**Use Cases**:
- Batch file operations and project-wide refactoring
- Code review and quality assurance
- Test generation and coverage improvement
- Dependency security audit and updates
- Project health monitoring
- Changelog and documentation generation

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
- ✅ **Quality Check**: Built-in 8-section completeness check ensures context is recoverable

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

Atlas provides 9 commands, 7 specialized agents, and 3 query skills:

#### Commands

| Command | Description |
|---------|-------------|
| `/atlas:orchestrate` | Task coordination and parallel execution |
| `/atlas:gather` | Intelligent information gathering |
| `/atlas:review` | Multi-dimensional code review |
| `/atlas:refactor` | Intelligent code refactoring |
| `/atlas:test-gen` | Automated test generation |
| `/atlas:deps` | Dependency management and security |
| `/atlas:health` | Project health diagnostics |
| `/atlas:changelog` | Auto-generate changelog |
| `/atlas:repo-wiki` | Repository documentation generation |

#### Example Usage

```bash
# Task orchestration
/atlas:orchestrate Add TypeScript types to all React components --parallel

# Code review
/atlas:review --scope src/ --type security,performance

# Intelligent refactoring
/atlas:refactor extract-method --scope src/utils --dry-run

# Test generation
/atlas:test-gen --scope src/services --framework jest --coverage-target 80

# Dependency management
/atlas:deps --type security --fix

# Project health check
/atlas:health --export html

# Generate changelog
/atlas:changelog --from v1.0.0 --version 2.0.0

# Generate repo wiki
/atlas:repo-wiki --lang en --depth 3
```

#### Skills (Quick Query)

| Skill | Description | Example |
|-------|-------------|---------|
| `dep-query` | Dependency version, vulnerability, usage | "axios version", "outdated deps" |
| `git-query` | Commit history, contributors, changes | "recent commits", "who modified auth" |
| `wiki-query` | Project structure, API, module info | "what APIs exist", "find UserService" |

```bash
# Invoke skills
/skill atlas:dep-query
/skill atlas:git-query
/skill atlas:wiki-query
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

#### Context Structure (15 Sections)

Saved context includes the following sections to ensure complete recoverability:

| Section | Content |
|---------|---------|
| 1. Origin | User intent, core goals, constraints |
| 2. Process | Key decisions, reasoning |
| 3. Output | Code changes, new/modified files |
| 4. Status | Task progress, completion rate |
| 5. Obstacles | Problems encountered and solutions |
| 6. Environment | Tech stack, project info |
| 7. Map | Core files, dependencies |
| 8. Signpost | Continuation guide, next steps |
| 9. Session Stats | Conversation size, tool usage, session duration |
| 10. Code Quality | Code metrics, quality checks, style assessment |
| 11. Code Snippets | Core functions/classes, important changes |
| 12. Timeline | Key events, milestone moments |
| 13. Learning Notes | New knowledge, pitfalls, best practices |
| 14. Related Resources | Documentation links, references, search keywords |
| 15. Impact Analysis | Scope of impact, risk assessment, testing suggestions |

## Plugin Structure

```
cc-plugins/
├── .claude-plugin/
│   └── marketplace.json            # Marketplace configuration
├── atlas/                           # Atlas plugin (v2.9.1)
│   ├── .claude-plugin/
│   │   └── plugin.json             # Plugin metadata
│   ├── agents/                     # Specialized agents (7)
│   │   ├── atlas-executor.md       # Task executor
│   │   ├── code-reviewer.md        # Code review expert
│   │   ├── commit-analyzer.md      # Commit analysis
│   │   ├── dependency-analyzer.md  # Dependency analysis
│   │   ├── information-gatherer.md # Information gatherer
│   │   ├── repo-context-indexer.md # Repository context indexer
│   │   └── repo-semantic-analyzer.md # Semantic analyzer
│   ├── commands/                   # Commands (9)
│   │   ├── orchestrate.md          # Task orchestration
│   │   ├── gather.md               # Information gathering
│   │   ├── review.md               # Code review
│   │   ├── refactor.md             # Intelligent refactoring
│   │   ├── test-gen.md             # Test generation
│   │   ├── deps.md                 # Dependency management
│   │   ├── health.md               # Health diagnostics
│   │   ├── changelog.md            # Changelog generation
│   │   └── repo-wiki.md            # Repo documentation
│   ├── hooks/
│   │   └── hooks.json              # Hooks configuration
│   └── skills/                     # Query skills (3)
│       ├── dep-query/SKILL.md      # Dependency query
│       ├── git-query/SKILL.md      # Git query
│       └── wiki-query/SKILL.md     # Wiki query
├── ideation/                        # Ideation plugin (v1.0.1)
│   ├── .claude-plugin/
│   │   └── plugin.json             # Plugin metadata
│   ├── agents/
│   │   └── debate-moderator.md     # Debate moderator agent
│   └── commands/
│       └── brainstorm.md           # /ideation:brainstorm command
├── mnemosyne/                       # Mnemosyne plugin (v1.0.0)
│   ├── .claude-plugin/
│   │   └── plugin.json             # Plugin metadata
│   └── commands/                   # Commands (7)
│       ├── save.md                 # /mnemosyne:save - Save context
│       ├── load.md                 # /mnemosyne:load - Load context
│       ├── list.md                 # /mnemosyne:list - List sessions
│       ├── search.md               # /mnemosyne:search - Search
│       ├── delete.md               # /mnemosyne:delete - Delete
│       ├── stats.md                # /mnemosyne:stats - Statistics
│       └── clean.md                # /mnemosyne:clean - Cleanup
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
