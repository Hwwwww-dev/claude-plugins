---
description: 变更日志命令。分析 git 历史，自动生成结构化的 CHANGELOG.md，支持 conventional commits 和语义化版本。
argument-hint: [--from tag|commit] [--to tag|commit] [--version X.Y.Z] [--format keep-a-changelog|conventional|github] [--output path]
---

# /changelog - 变更日志生成器

用户输入: $ARGUMENTS

---

## 第一步：解析参数与确认选项

### 参数表

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--from` | 起始点（tag 或 commit） | 上一个 tag |
| `--to` | 结束点（tag 或 commit） | HEAD |
| `--version` | 新版本号（X.Y.Z） | 自动推断 |
| `--format` | 输出格式 | keep-a-changelog |
| `--output` | 输出路径 | CHANGELOG.md |
| `--append` | 追加模式（保留旧内容） | true |
| `--dry-run` | 仅预览，不写入文件 | false |

### 版本自动推断规则

| 变更类型 | 版本变化 | 说明 |
|----------|----------|------|
| BREAKING CHANGE / "!" | Major (X.0.0) | 不兼容变更 |
| `feat:` | Minor (x.Y.0) | 新功能 |
| `fix:` / `docs:` / `perf:` | Patch (x.y.Z) | 修复和优化 |

### 分阶段确认选项

**第一个 AskUserQuestion: 执行模式选择**

```
问题: 执行模式
- 自动模式（推荐）: 使用推荐选项，减少交互
- 交互模式: 每个配置选项都需要确认
- dry-run: 仅预览，不写入文件
```

**第二个 AskUserQuestion: 生成配置（仅交互模式和 dry-run）**

如果用户选择了**交互模式**或 **dry-run**，询问生成配置：

```
问题 1: 输出格式
- keep-a-changelog（推荐）: Added/Changed/Fixed/Security
- conventional: Features/Bug Fixes/BREAKING CHANGES
- github: GitHub Release 风格（What's Changed）

问题 2: 版本号
- auto（推荐）: 自动推断（基于提交类型）
- manual: 手动指定（输入 X.Y.Z）

问题 3: 分析范围
- last-tag（推荐）: 从上一个 tag 到 HEAD
- custom: 自定义范围（--from X --to Y）

问题 4: 追加模式
- append（推荐）: 追加到现有 CHANGELOG（保留历史）
- overwrite: 覆盖整个文件
```

**自动模式行为**（跳过第二个 AskUserQuestion）：
- 输出格式: keep-a-changelog
- 版本号: auto（自动推断）
- 分析范围: last-tag（从上一个 tag 到 HEAD）
- 追加模式: append
- 失败处理: 询问用户

**注意**:
- 如果用户已通过参数指定选项（如 `/changelog --version 2.0.0 --format conventional`），跳过所有询问
- dry-run 模式会询问生成配置但不会实际写入文件

---

## 第二步：版本检测与提交分析

### 2.1 检测当前版本

```bash
# 获取最新 tag
git describe --tags --abbrev=0

# 如果没有 tag，使用 0.0.0 作为起点
```

### 2.2 分析提交记录

**调用 atlas:commit-analyzer 子任务**:

```
Task(subagent_type="atlas:commit-analyzer")
prompt: |
  ## 任务
  任务 ID: changelog-analysis-<timestamp>
  分析范围: <from>..<to>

  ## 收集内容
  1. 提交历史（git log --oneline --no-merges）
  2. 提交分类（按 conventional commits 规范）:
     - feat: 新功能
     - fix: 错误修复
     - docs: 文档变更
     - style: 代码格式
     - refactor: 重构
     - perf: 性能优化
     - test: 测试
     - chore: 构建/工具
     - BREAKING: 破坏性变更（包含 "!" 或 `BREAKING CHANGE:` 的提交）
  3. 统计信息（提交总数、文件变更数、贡献者）

  ## 输出
  写入: docs/information/changelog-analysis-<timestamp>.md
  返回: 提交分类结果和版本推断建议
```

**如果提交不规范（无类型前缀）**:
- 尝试根据提交信息内容推断类型（如包含 "add" → feat, "fix" → fix）
- 无法推断的归类为 `Other Changes`

### 2.3 版本号推断

**基于提交分类自动推断**:

```
当前版本: 1.2.3

如果有 BREAKING CHANGE: → 2.0.0 (Major bump)
否则如果有 feat: → 1.3.0 (Minor bump)
否则如果有 fix/docs/perf: → 1.2.4 (Patch bump)
否则: → 保持 1.2.3（无需发布）
```

**如果用户手动指定 `--version`，跳过推断，直接使用指定版本。**

---

## 第三步：变更分类与内容生成

### 3.1 按格式生成内容

#### Format: keep-a-changelog

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- 新功能 1 (commit hash)
- 新功能 2 (commit hash)

### Changed
- 重构项目 A (commit hash)
- 优化性能 B (commit hash)

### Fixed
- 修复 Bug #123 (commit hash)
- 修复内存泄漏 (commit hash)

### Security
- 修复安全漏洞 CVE-XXXX (commit hash)

### Deprecated
- 弃用旧 API X (commit hash)

### Removed
- 移除废弃功能 Y (commit hash)
```

#### Format: conventional

```markdown
## [X.Y.Z] (YYYY-MM-DD)

### Features
- **scope**: 功能描述 (commit hash)
- 功能描述 2 (commit hash)

### Bug Fixes
- **scope**: 修复描述 (commit hash)

### Performance Improvements
- 性能优化描述 (commit hash)

### BREAKING CHANGES
- 破坏性变更描述 (commit hash)
```

#### Format: github

```markdown
## What's Changed

### 🚀 New Features
- 功能描述 by @username in #PR

### 🐛 Bug Fixes
- 修复描述 by @username in #PR

### 📚 Documentation
- 文档更新 by @username in #PR

### 🏗️ Chores
- 依赖更新 by @username in #PR

**Full Changelog**: https://github.com/owner/repo/compare/v1.2.3...v1.3.0
```

### 3.2 包含贡献者列表

```markdown
### Contributors
- @user1 (5 commits)
- @user2 (3 commits)
- @user3 (1 commit)
```

---

## 第四步：文件更新

### 4.1 Dry-run 模式

**如果指定 `--dry-run`**:
```markdown
📄 预览生成的变更日志:

────────────────────────────────────
[生成的内容]
────────────────────────────────────

📊 统计:
- 版本: 1.3.0
- 提交数: 25
- 新功能: 8
- Bug 修复: 12
- 其他: 5

💡 提示: 使用 /changelog 无 --dry-run 参数以实际写入文件
```

**停止执行，不写入文件。**

### 4.2 实际写入

**调用 atlas:atlas-executor 执行文件更新** (询问用户选择模型):

```
Task(subagent_type="atlas:atlas-executor", model=用户选择)
prompt: |
  ## 子任务
  编号: #1
  描述: 更新 CHANGELOG.md 文件

  ## 文件
  - <output-path>

  ## 操作
  模式: <append|overwrite>

  ## 内容
  读取: docs/information/changelog-analysis-<timestamp>.md
  生成格式: <keep-a-changelog|conventional|github>

  ## 要求
  1. 如果是 append 模式:
     - 在文件开头插入新版本内容（在标题下方）
     - 保留所有旧版本记录
  2. 如果是 overwrite 模式:
     - 替换整个文件内容
  3. 确保格式一致性（标题层级、列表格式）
```

---

## 第五步：输出摘要

**固定输出结构**:

```markdown
✅ 变更日志已生成

## 版本信息
- 版本号: X.Y.Z
- 推断依据: [Major/Minor/Patch] bump based on [BREAKING/feat/fix] commits
- 分析范围: vA.B.C..HEAD (25 commits)

## 变更统计
- 🚀 新功能: 8
- 🐛 Bug 修复: 12
- 📚 文档: 3
- ♻️ 重构: 2

## 文件位置
- 输出文件: CHANGELOG.md
- 格式: keep-a-changelog
- 模式: append（旧版本已保留）

## 后续步骤
1. 审查变更内容: `cat CHANGELOG.md | head -50`
2. 提交变更: `git add CHANGELOG.md && git commit -m "docs: update changelog for vX.Y.Z"`
3. 创建 tag: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
4. 推送到远程: `git push origin main --tags`
```

---

## 执行示例

### 示例 1: 自动生成（自动模式）

```
用户: /changelog

1. 第一个 AskUserQuestion - 执行模式:
   - 执行模式: 自动模式（推荐）✓

   [自动使用推荐配置，跳过第二个 AskUserQuestion]
   - 格式: keep-a-changelog
   - 版本: auto (推断为 1.3.0)
   - 范围: last-tag (v1.2.3..HEAD)
   - 模式: append

2. 版本检测:
   git describe --tags → v1.2.3

3. 提交分析:
   git log v1.2.3..HEAD --oneline
   → 25 commits (8 feat, 12 fix, 5 other)
   → 版本推断: 1.3.0 (Minor bump)

4. 内容生成 (keep-a-changelog 格式):
   ## [1.3.0] - 2024-01-15
   ### Added
   - 新增用户认证功能
   ...

5. 文件更新 (append 模式):
   在 CHANGELOG.md 开头插入新版本内容

6. 输出摘要
```

### 示例 2: 交互模式

```
用户: /changelog

1. 第一个 AskUserQuestion - 执行模式:
   - 执行模式: 交互模式 ✓

2. 第二个 AskUserQuestion - 生成配置:
   - 输出格式: conventional ✓
   - 版本号: manual ✓
   - 分析范围: custom ✓
   - 追加模式: append ✓

3. 用户输入:
   - 版本号: 2.0.0
   - 起始点: v1.5.0
   - 结束点: HEAD

4. 提交分析:
   git log v1.5.0..HEAD
   → 发现 BREAKING CHANGE 提交
   → 验证版本号 2.0.0 符合 Major bump 规范

5. 内容生成 (conventional 格式):
   ## [2.0.0] (2024-01-15)
   ### BREAKING CHANGES
   - 移除旧版 API...

6. 文件更新并输出摘要
```

### 示例 3: 指定参数（跳过所有询问）

```
用户: /changelog --version 2.0.0 --format conventional --from v1.5.0

1. 跳过所有询问（已指定参数）

2. 提交分析:
   git log v1.5.0..HEAD
   → 发现 BREAKING CHANGE 提交
   → 验证版本号 2.0.0 符合 Major bump 规范

3. 内容生成 (conventional 格式):
   ## [2.0.0] (2024-01-15)
   ### BREAKING CHANGES
   - 移除旧版 API...

4. 文件更新并输出摘要
```

### 示例 4: Dry-run 预览

```
用户: /changelog --dry-run

1. 第一个 AskUserQuestion - 执行模式:
   - 执行模式: dry-run ✓

2. 第二个 AskUserQuestion - 生成配置:
   - 输出格式: keep-a-changelog ✓
   - 版本号: auto ✓
   - 分析范围: last-tag ✓

3. 执行分析和内容生成

4. 输出预览:
   📄 预览生成的变更日志:
   ────────────────────────────────────
   ## [1.3.0] - 2024-01-15
   ...
   ────────────────────────────────────

3. 停止执行，不写入文件
```

---

## 特殊场景处理

### 首次生成（无现有 CHANGELOG）

```
检测: CHANGELOG.md 不存在
操作: 创建新文件，包含:
  - 标题: # Changelog
  - 说明段落: All notable changes...
  - 新版本内容
```

### 无 Git 标签

```
检测: git describe --tags 失败
操作: 使用 0.0.0 作为起点
  → 分析范围: 初始提交..HEAD
  → 推断版本: 0.1.0（首个版本）
```

### 提交不规范

```
检测: 提交信息无 conventional commits 前缀
操作:
  1. 尝试智能推断（如 "Add feature" → feat）
  2. 无法推断的归入 "Other Changes" 类别
  3. 提示用户使用规范的提交格式
```

### 版本号冲突

```
检测: 指定版本号已存在于 CHANGELOG
操作:
  - 警告用户版本号重复
  - 询问: 覆盖 / 使用新版本号 / 取消
```

---

## 核心约束

### 必须做
- 严格遵循语义化版本规范（Semantic Versioning）
- 分析所有提交，不遗漏任何变更
- 生成的日志格式保持一致性
- append 模式必须保留旧版本内容
- 包含完整的元数据（日期、版本、提交 hash）

### 禁止做
- 篡改提交历史或提交信息
- 在 dry-run 模式下写入文件
- 跳过 BREAKING CHANGES 的警告
- 推断不符合规范的版本号（如 feat → Major bump）
- 覆盖用户手动编辑的自定义内容（识别并保留）

---

## 与其他命令配合

```bash
# 工作流示例

# 1. 生成变更日志
/changelog --version 2.1.0

# 2. 审查内容
cat CHANGELOG.md | head -100

# 3. 批量更新版本号（如需要）
/orchestrate 更新所有 package.json 中的版本号为 2.1.0

# 4. 提交和发布
git add .
git commit -m "chore: release v2.1.0"
git tag -a v2.1.0 -m "Release v2.1.0"
git push origin main --tags
```

---

## 输出文件示例

### Keep-a-Changelog 格式

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2024-01-15

### Added
- User authentication system with JWT support (a1b2c3d)
- Dark mode toggle in settings page (e4f5g6h)
- Export data to CSV functionality (i7j8k9l)

### Changed
- Refactor API client to use axios instead of fetch (m0n1o2p)
- Update UI library to v5.2.0 (q3r4s5t)

### Fixed
- Fix memory leak in WebSocket connection (u6v7w8x)
- Resolve race condition in payment processing (y9z0a1b)

### Security
- Patch XSS vulnerability in comment rendering (c2d3e4f)

## [1.2.3] - 2023-12-10

...
```

### Conventional Commits 格式

```markdown
# Changelog

## [1.3.0] (2024-01-15)

### Features
- **auth**: add JWT-based authentication (a1b2c3d)
- **ui**: implement dark mode toggle (e4f5g6h)
- **export**: support CSV data export (i7j8k9l)

### Bug Fixes
- **websocket**: fix memory leak on disconnect (u6v7w8x)
- **payment**: resolve race condition (y9z0a1b)

### Performance Improvements
- **api**: optimize database query caching (g7h8i9j)

## [1.2.3] (2023-12-10)

...
```

---

## 注意事项

- 生成的日志可能需要人工审校（特别是非规范提交）
- BREAKING CHANGES 务必在版本号和内容中突出显示
- 敏感信息（如安全漏洞细节）应在发布前人工审核
- 支持自定义模板（通过 `.claude/templates/changelog.md` 配置）
- 所有 git 操作只读，不会修改提交历史
