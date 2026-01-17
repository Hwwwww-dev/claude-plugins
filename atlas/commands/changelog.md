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
- 使用推荐默认值：`format=keep-a-changelog`、`version=auto`、`range=last-tag`、`mode=append`；失败询问用户

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

### 示例 2: Dry-run 预览

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

- 首次生成: 无 `CHANGELOG.md` → 创建新文件（标题/说明/新版本内容）
- 无 Git 标签: 起点视为 `0.0.0`（初始提交..HEAD）
- 提交不规范: 尝试推断；无法推断归入 `Other Changes` 并提示规范化
- 版本号冲突: 警告并询问 覆盖/换版本/取消

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

/changelog --version 2.1.0
cat CHANGELOG.md | head -80
git add CHANGELOG.md && git commit -m "docs: update changelog for v2.1.0"
```

---

## 输出文件示例

（各格式模板见「第三步：变更分类与内容生成」）

```markdown
# Changelog

## [X.Y.Z] - YYYY-MM-DD

### Added
- feat summary (commit)

### Fixed
- fix summary (commit)
```

---

## 注意事项

- 生成的日志可能需要人工审校（特别是非规范提交）
- BREAKING CHANGES 务必在版本号和内容中突出显示
- 敏感信息（如安全漏洞细节）应在发布前人工审核
- 支持自定义模板（通过 `.claude/templates/changelog.md` 配置）
- 所有 git 操作只读，不会修改提交历史
