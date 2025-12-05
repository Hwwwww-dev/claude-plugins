# Dependency Query Skill

依赖快速查询工具 - 从索引快速查询项目依赖信息。

## 功能特性

- 📦 **依赖详情查询** - 查看版本、许可证、描述等信息
- 🔒 **安全漏洞检查** - 按严重性级别查看已知漏洞
- ⚠️  **过期依赖检测** - 对比当前版本与最新版本
- 🌳 **依赖树展示** - 查看包的依赖关系树
- 📍 **使用位置追踪** - 找到包在项目中的引用位置
- 📊 **统计概览** - 整体依赖健康状况统计

## 前置条件

1. 需要先运行 `/atlas:deps` 生成依赖索引
2. 索引文件位置: `.claude/.meta/dependencies.pkg.json`

## 使用方式

### 方法 1: 通过 Skill 调用

```bash
# 在 Claude Code 中
/skill dep-query

# 然后按提示执行查询命令
```

### 方法 2: 直接调用脚本

```bash
# 设置环境变量（可选，默认使用当前目录）
export DEPS_TARGET_DIR=/path/to/your/project

# 查询依赖详情
python3 scripts/query_deps.py pkg lodash

# 查看所有漏洞
python3 scripts/query_deps.py vuln

# 只看严重漏洞
python3 scripts/query_deps.py vuln critical

# 查看过期依赖
python3 scripts/query_deps.py outdated

# 查看依赖树
python3 scripts/query_deps.py tree react

# 查看使用位置
python3 scripts/query_deps.py usage axios

# 统计概览
python3 scripts/query_deps.py stats
```

## 查询命令详解

### pkg - 依赖详情

```bash
python3 scripts/query_deps.py pkg <name>
```

支持模糊匹配，显示：
- 版本信息（当前/最新）
- 依赖类型（生产/开发）
- 许可证信息
- 安全漏洞（如有）
- 包描述和主页

**示例输出**:
```
📦 依赖: lodash
   版本: 4.17.20
   类型: dependencies
   最新: 4.17.21 ⚠️  过期
   许可: MIT

⚠️  漏洞 (1 个):
   🟠 [HIGH] Prototype Pollution
      CVE: CVE-2021-23337
```

### vuln - 漏洞列表

```bash
python3 scripts/query_deps.py vuln [severity]
```

可选的严重性过滤：
- `critical` - 严重漏洞
- `high` - 高危漏洞
- `moderate` - 中危漏洞
- `low` - 低危漏洞

**示例输出**:
```
⚠️  发现 3 个漏洞:

🔴 [CRITICAL] Remote Code Execution
   包: express@4.17.1
   CVE: CVE-2022-24999
   详情: https://...

🟠 [HIGH] Prototype Pollution
   包: lodash@4.17.20
   CVE: CVE-2021-23337
```

### outdated - 过期依赖

```bash
python3 scripts/query_deps.py outdated
```

列出所有版本落后于最新版的依赖包。

**示例输出**:
```
⚠️  发现 5 个过期依赖:

📦 lodash
   当前: 4.17.20
   最新: 4.17.21

🛠️  jest
   当前: 27.0.0
   最新: 29.5.0
```

### tree - 依赖树

```bash
python3 scripts/query_deps.py tree <name>
```

显示包的直接依赖关系树。

**示例输出**:
```
📦 react-dom@18.2.0
├── react
├── scheduler
└── loose-envify
```

### usage - 使用位置

```bash
python3 scripts/query_deps.py usage <name>
```

找出项目中引用该包的文件位置。

**示例输出**:
```
📦 axios 使用于:
   1. 📄 src/api/client.ts
   2. 📄 src/services/user.service.ts
   3. 📄 tests/api.test.ts
  ... 还有 12 个位置
```

### stats - 统计概览

```bash
python3 scripts/query_deps.py stats
```

显示项目依赖的整体健康状况。

**示例输出**:
```
=== 依赖统计 ===

📦 生产依赖: 45 个
🛠️  开发依赖: 23 个
📊 总计: 68 个

⚠️  过期依赖: 5 个

🔒 安全漏洞: 3 个
   🔴 严重 (Critical): 1
   🟠 高危 (High): 2

💾 最大的依赖:
   webpack: 5.23 MB
   typescript: 3.45 MB
   eslint: 2.17 MB
```

## 数据结构

依赖索引文件 (`dependencies.pkg.json`) 预期结构：

```json
{
  "dependencies": [
    {
      "name": "lodash",
      "version": "4.17.20",
      "latest": "4.17.21",
      "type": "dependencies",
      "description": "Lodash modular utilities.",
      "license": "MIT",
      "homepage": "https://lodash.com/",
      "vulnerabilities": [
        {
          "severity": "high",
          "title": "Prototype Pollution",
          "cve": "CVE-2021-23337",
          "url": "https://..."
        }
      ],
      "size": 1048576
    }
  ],
  "dependency_tree": {
    "react-dom@18.2.0": ["react", "scheduler", "loose-envify"]
  },
  "usage_locations": {
    "axios": ["src/api/client.ts", "src/services/user.service.ts"]
  }
}
```

## 注意事项

1. **索引过期** - 如果依赖有更新，需要重新运行 `/atlas:deps` 生成索引
2. **模糊匹配** - 所有查询支持部分名称匹配（如 `react` 匹配 `react-dom`）
3. **跨项目查询** - 通过 `DEPS_TARGET_DIR` 可以查询其他项目的依赖
4. **数据完整性** - 部分功能（如依赖树、使用位置）依赖索引的完整性

## 常见问题

### Q: 提示"依赖索引不存在"？
A: 运行 `/atlas:deps` 生成索引。

### Q: 依赖树或使用位置显示"数据不可用"？
A: 索引可能不完整，重新运行 `/atlas:deps` 并确保包含这些功能。

### Q: 如何查询其他项目的依赖？
A: 设置 `DEPS_TARGET_DIR` 环境变量指向目标项目目录。

### Q: 支持哪些包管理器？
A: 取决于 `/atlas:deps` 命令的实现，通常支持 npm/yarn/pnpm (JS) 和 pip (Python)。
