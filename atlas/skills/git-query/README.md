# Git Query Skill

Git 信息快速查询工具，用于查询提交历史、贡献者、文件变更、分支状态等。

## 功能特性

- 🔍 **提交搜索**: 根据关键词搜索提交信息
- 👤 **作者查询**: 查询特定作者的提交记录
- 📄 **文件历史**: 追踪文件的完整变更历史
- 📊 **贡献统计**: 显示所有贡献者的提交数量
- 🕐 **最近提交**: 快速查看最近的提交记录
- 🌿 **分支状态**: 查看所有本地分支及其状态
- 🏷️ **标签列表**: 列出仓库中的所有标签
- 🔥 **热点文件**: 识别最常修改的文件

## 快速开始

### 使用脚本查询

```bash
# 搜索提交
python3 "${CLAUDE_PLUGIN_ROOT}/skills/git-query/scripts/query.py" search "fix bug"

# 查询作者
python3 "${CLAUDE_PLUGIN_ROOT}/skills/git-query/scripts/query.py" author "Zhang San"

# 文件历史
python3 "${CLAUDE_PLUGIN_ROOT}/skills/git-query/scripts/query.py" file src/main.js

# 贡献统计
python3 "${CLAUDE_PLUGIN_ROOT}/skills/git-query/scripts/query.py" stats

# 最近提交
python3 "${CLAUDE_PLUGIN_ROOT}/skills/git-query/scripts/query.py" recent 10

# 分支状态
python3 "${CLAUDE_PLUGIN_ROOT}/skills/git-query/scripts/query.py" branches

# 标签列表
python3 "${CLAUDE_PLUGIN_ROOT}/skills/git-query/scripts/query.py" tags

# 热点文件
python3 "${CLAUDE_PLUGIN_ROOT}/skills/git-query/scripts/query.py" hotfiles
```

### 直接使用 Git 命令

```bash
# 搜索提交
git log --oneline --grep="keyword" -20

# 贡献者排名
git shortlog -sn --no-merges | head -20

# 热点文件
git log --pretty=format: --name-only --since="3 months ago" | grep -v '^$' | sort | uniq -c | sort -rn | head -20
```

## 输出示例

### 搜索提交

```
🔍 搜索提交信息: "fix bug"

提交哈希 | 日期       | 作者     | 提交信息
--------------------------------------------------------------------------------
a1b2c3d | 2025-12-06 | Zhang San | fix: resolve bug in auth module
e4f5g6h | 2025-12-05 | Li Si | fix: bug in payment flow

✅ 找到 2 条匹配记录（最多显示 20 条）
```

### 热点文件

```
🔥 热点文件（最近 3 months ago）

修改次数 | 文件路径
--------------------------------------------------------------------------------
      48 | src/main.js
      32 | package.json
      28 | README.md

✅ 共 120 个文件被修改（显示前 20 个）
```

## 详细文档

参见 [SKILL.md](./SKILL.md) 获取完整的使用说明和高级功能。

## 依赖

- Python 3.6+
- Git 2.0+

## 许可证

MIT
