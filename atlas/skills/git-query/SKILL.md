---
name: git-query
description: Git 信息快速查询。查询提交历史、贡献者、文件变更、分支状态等。支持模糊搜索。
version: 1.0.0
color: cyan
---

# Git Query - Git 信息快速查询

从 Git 仓库查询提交历史、贡献者、文件变更等信息。支持实时查询和缓存查询。

## 脚本路径

使用 `${CLAUDE_PLUGIN_ROOT}` 环境变量（Claude Code 自动设置）：

```bash
# 脚本位置
${CLAUDE_PLUGIN_ROOT}/skills/git-query/scripts/query.py        # 标准查询
```

**备选**：相对路径 `scripts/query.py`（依赖 Claude 自动解析 base path）

## 前置条件

```bash
# 检查是否在 git 仓库
git rev-parse --is-inside-work-tree 2>/dev/null || echo "❌ 不是 Git 仓库"

# 可选: 检查缓存文件（运行 /atlas:changelog 后生成）
ls .claude/.meta/commits.pkg.json 2>/dev/null && echo "✅ 缓存可用" || echo "⚠️ 无缓存，使用实时查询"
```

## 查询类型表

| 命令 | 说明 | Git 命令 |
|------|------|----------|
| search <keyword> | 搜索提交信息 | git log --grep |
| author <name> | 作者提交 | git log --author |
| file <path> | 文件历史 | git log --follow |
| stats | 贡献统计 | git shortlog -sn |
| recent [n] | 最近提交 | git log -n |
| changes [ref] | 变更统计 | git diff --stat |
| blame <file> | 行级追溯 | git blame |
| branches | 分支状态 | git branch -vv |
| tags | 标签列表 | git tag -l |
| hotfiles | 热点文件 | git log --name-only |

## 快速查询

**所有调用使用当前项目路径**

```bash
# 使用脚本查询
python3 "${CLAUDE_PLUGIN_ROOT}/skills/git-query/scripts/query.py" search <keyword>  # 搜索提交
python3 "${CLAUDE_PLUGIN_ROOT}/skills/git-query/scripts/query.py" author <name>     # 作者提交
python3 "${CLAUDE_PLUGIN_ROOT}/skills/git-query/scripts/query.py" file <path>       # 文件历史
python3 "${CLAUDE_PLUGIN_ROOT}/skills/git-query/scripts/query.py" stats             # 贡献统计
python3 "${CLAUDE_PLUGIN_ROOT}/skills/git-query/scripts/query.py" recent 10         # 最近10次提交
python3 "${CLAUDE_PLUGIN_ROOT}/skills/git-query/scripts/query.py" branches          # 分支状态
python3 "${CLAUDE_PLUGIN_ROOT}/skills/git-query/scripts/query.py" tags              # 标签列表
python3 "${CLAUDE_PLUGIN_ROOT}/skills/git-query/scripts/query.py" hotfiles          # 热点文件

# 直接使用 git 命令（快速查询）
git log --oneline --grep="$QUERY" -20                            # 搜索提交
git log --author="$AUTHOR" --oneline -20                          # 作者提交
git log --follow --oneline -- "$FILE" -20                         # 文件历史
git shortlog -sn --no-merges | head -20                           # 贡献者排名
git log --oneline -n 10                                           # 最近提交
git diff --stat HEAD~10..HEAD                                     # 最近10次提交的变更统计
git blame -L 1,20 "$FILE"                                         # 文件追溯（前20行）
git branch -vv                                                    # 分支状态
git tag -l                                                        # 标签列表
```

## 内联命令（备用）

当脚本不可用时，可使用内联命令：

<details>
<summary>贡献者排名</summary>

```bash
git shortlog -sn --no-merges | head -20
```

**输出示例**:
```
  150  Zhang San
   87  Li Si
   45  Wang Wu
```
</details>

<details>
<summary>热点文件（最常修改）</summary>

```bash
git log --pretty=format: --name-only --since="3 months ago" | grep -v '^$' | sort | uniq -c | sort -rn | head -20
```

**输出示例**:
```
  45 src/main.js
  32 package.json
  28 README.md
```
</details>

<details>
<summary>每日提交统计</summary>

```bash
git log --pretty=format:'%ad' --date=short | sort | uniq -c | tail -30
```

**输出示例**:
```
   5 2025-12-01
   8 2025-12-02
   3 2025-12-03
```
</details>

<details>
<summary>大文件检测</summary>

```bash
git ls-tree -r -l HEAD | sort -k 4 -n -r | head -20 | awk '{printf "%-10s %-50s %s\n", $4, $5, $4/(1024*1024)" MB"}'
```

**输出示例**:
```
524288     dist/bundle.js                0.5 MB
262144     public/images/banner.jpg      0.25 MB
```
</details>

<details>
<summary>提交频率分析</summary>

```bash
git log --pretty=format:'%h|%an|%ad|%s' --date=short -50
```

**输出示例**:
```
a1b2c3d|Zhang San|2025-12-06|feat: add new feature
e4f5g6h|Li Si|2025-12-05|fix: resolve bug
```
</details>

<details>
<summary>文件类型统计</summary>

```bash
git ls-files | grep -o '\.[^.]*$' | sort | uniq -c | sort -rn | head -15
```

**输出示例**:
```
  120 .js
   85 .py
   45 .md
   30 .json
```
</details>

## 高级查询

### 1. 搜索提交信息

```bash
# 搜索包含关键词的提交
git log --grep="fix" --oneline -20

# 搜索作者的提交
git log --author="Zhang San" --oneline -20

# 组合搜索
git log --grep="feat" --author="Zhang San" --since="2 weeks ago" --oneline
```

### 2. 文件变更追踪

```bash
# 文件完整历史（包含重命名）
git log --follow --oneline -- path/to/file.js

# 文件每次提交的变更统计
git log --follow --stat -- path/to/file.js

# 查看文件在特定提交的内容
git show commit-hash:path/to/file.js
```

### 3. 代码行级追溯

```bash
# 查看每行代码的最后修改者
git blame path/to/file.js

# 查看特定行范围
git blame -L 10,30 path/to/file.js

# 追溯特定提交之前的状态
git blame commit-hash^ -- path/to/file.js
```

### 4. 分支和标签

```bash
# 分支详细状态（包含上游关系）
git branch -vv

# 查看未合并的分支
git branch --no-merged

# 查看已合并的分支
git branch --merged

# 标签列表（带注释）
git tag -n
```

## PKG 数据源（可选）

如果运行过 `/atlas:changelog`，可以使用缓存的提交数据：

```bash
# 检查缓存
ls .claude/.meta/commits.pkg.json

# 快速统计（使用缓存）
python3 -c "
import json
with open('.claude/.meta/commits.pkg.json') as f:
    data = json.load(f)
    print(f'缓存的提交数: {len(data.get(\"commits\", []))}')
    print(f'贡献者数: {len(set(c[\"author\"] for c in data.get(\"commits\", [])))}')
"
```

**缓存优先级**: 实时 Git 查询优先，PKG 缓存仅用于加速大量历史数据分析。

## 注意事项

- **实时查询优先** - 确保获取最新数据
- **支持模糊匹配** - 作者名、提交信息支持部分匹配
- **性能优化** - 大型仓库建议限制查询范围（使用 --since、-n 等参数）
- **缓存加速** - 频繁查询历史数据时使用 PKG 缓存
- **跨平台兼容** - 命令适用于 Linux、macOS、Windows（Git Bash）

## 常见使用场景

1. **代码审查**: 查看文件历史和修改者
2. **Bug 追踪**: 搜索相关提交，定位引入问题的版本
3. **贡献统计**: 生成团队贡献报告
4. **重构规划**: 识别热点文件，优先重构
5. **发布准备**: 查看自上次标签以来的变更
