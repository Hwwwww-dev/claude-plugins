---
name: dep-query
description: 快速依赖查询。查询依赖版本、漏洞、使用位置、更新历史等。支持模糊搜索。
version: 1.0.0
color: orange
---

# Dependency Query - 依赖快速查询

从 `.claude/.meta/dependencies.pkg.json` 索引查询项目依赖信息。

## 脚本路径

使用 `${CLAUDE_PLUGIN_ROOT}` 环境变量（Claude Code 自动设置）：

```bash
# 脚本位置
${CLAUDE_PLUGIN_ROOT}/skills/dep-query/scripts/query_deps.py
```

**备选**：相对路径 `scripts/query_deps.py`（依赖 Claude 自动解析 base path）

## 前置条件

```bash
# 检查依赖索引是否存在
ls .claude/.meta/dependencies.pkg.json 2>/dev/null || echo "❌ 请先运行 /atlas:deps"
```

## 查询类型

| 命令 | 说明 | 示例 |
|------|------|------|
| `pkg <name>` | 查询依赖详情 | dep-query pkg lodash |
| `vuln [severity]` | 列出漏洞 | dep-query vuln critical |
| `outdated` | 过期依赖 | dep-query outdated |
| `tree <name>` | 依赖树 | dep-query tree react |
| `usage <name>` | 使用位置 | dep-query usage axios |
| `stats` | 统计概览 | dep-query stats |

## 快速查询

**所有调用必须设置 `DEPS_TARGET_DIR=$PWD`**

```bash
# 依赖详情
DEPS_TARGET_DIR=$PWD python3 "${CLAUDE_PLUGIN_ROOT}/skills/dep-query/scripts/query_deps.py" pkg <name>

# 漏洞查询
DEPS_TARGET_DIR=$PWD python3 "${CLAUDE_PLUGIN_ROOT}/skills/dep-query/scripts/query_deps.py" vuln          # 所有漏洞
DEPS_TARGET_DIR=$PWD python3 "${CLAUDE_PLUGIN_ROOT}/skills/dep-query/scripts/query_deps.py" vuln critical # 仅严重漏洞

# 过期依赖
DEPS_TARGET_DIR=$PWD python3 "${CLAUDE_PLUGIN_ROOT}/skills/dep-query/scripts/query_deps.py" outdated

# 依赖树
DEPS_TARGET_DIR=$PWD python3 "${CLAUDE_PLUGIN_ROOT}/skills/dep-query/scripts/query_deps.py" tree <name>

# 使用位置
DEPS_TARGET_DIR=$PWD python3 "${CLAUDE_PLUGIN_ROOT}/skills/dep-query/scripts/query_deps.py" usage <name>

# 统计概览
DEPS_TARGET_DIR=$PWD python3 "${CLAUDE_PLUGIN_ROOT}/skills/dep-query/scripts/query_deps.py" stats

# 跨项目查询
DEPS_TARGET_DIR="/path/to/other-project" python3 "${CLAUDE_PLUGIN_ROOT}/skills/dep-query/scripts/query_deps.py" pkg express
```

## 内联命令（备用）

当脚本不可用时，可使用内联 Python：

<details>
<summary>依赖详情查询</summary>

```bash
python3 -c "
import json, sys
pkg_name = '$QUERY'.lower()

try:
    with open('.claude/.meta/dependencies.pkg.json') as f:
        data = json.load(f)
        deps = data.get('dependencies', [])

        # 模糊匹配
        matches = [d for d in deps if pkg_name in d.get('name', '').lower()]

        if not matches:
            print(f'未找到包含 \"{pkg_name}\" 的依赖')
            print(f'\\n项目依赖 ({len(deps)} 个):')
            for d in deps[:15]:
                print(f'  - {d.get(\"name\", \"-\")} @ {d.get(\"version\", \"-\")}')
        elif len(matches) == 1:
            d = matches[0]
            print(f'依赖: {d.get(\"name\", \"-\")}')
            print(f'版本: {d.get(\"version\", \"-\")}')
            print(f'类型: {d.get(\"type\", \"-\")}')  # dependencies/devDependencies
            if d.get('latest'):
                print(f'最新: {d[\"latest\"]}')
            if d.get('description'):
                print(f'描述: {d[\"description\"]}')
            if d.get('license'):
                print(f'许可: {d[\"license\"]}')
            if d.get('vulnerabilities'):
                vulns = d['vulnerabilities']
                print(f'漏洞: {len(vulns)} 个')
                for v in vulns:
                    print(f'  ⚠️  [{v.get(\"severity\",\"unknown\").upper()}] {v.get(\"title\",\"-\")}')
        else:
            print(f'找到 {len(matches)} 个匹配依赖:')
            for d in matches:
                vuln_count = len(d.get('vulnerabilities', []))
                vuln_mark = f' ⚠️ {vuln_count} vulns' if vuln_count > 0 else ''
                print(f'  - {d.get(\"name\", \"-\")} @ {d.get(\"version\", \"-\")}{vuln_mark}')
except FileNotFoundError:
    print('❌ 依赖索引不存在，请先运行 /atlas:deps')
except Exception as e:
    print(f'❌ 查询失败: {e}')
"
```
</details>

<details>
<summary>漏洞列表</summary>

```bash
python3 -c "
import json
severity_filter = '$SEVERITY'.lower() if '$SEVERITY' else None

try:
    with open('.claude/.meta/dependencies.pkg.json') as f:
        data = json.load(f)
        deps = data.get('dependencies', [])

        # 收集所有漏洞
        all_vulns = []
        for d in deps:
            for v in d.get('vulnerabilities', []):
                all_vulns.append({
                    'package': d.get('name', '-'),
                    'version': d.get('version', '-'),
                    'severity': v.get('severity', 'unknown'),
                    'title': v.get('title', '-'),
                    'cve': v.get('cve', '-')
                })

        # 过滤严重性
        if severity_filter:
            all_vulns = [v for v in all_vulns if v['severity'].lower() == severity_filter]

        if not all_vulns:
            msg = f' ({severity_filter})' if severity_filter else ''
            print(f'未发现漏洞{msg}')
        else:
            # 按严重性排序
            severity_order = {'critical': 0, 'high': 1, 'moderate': 2, 'low': 3, 'unknown': 4}
            all_vulns.sort(key=lambda x: severity_order.get(x['severity'].lower(), 5))

            print(f'发现 {len(all_vulns)} 个漏洞:')
            for v in all_vulns:
                icon = {'critical':'🔴','high':'🟠','moderate':'🟡','low':'🟢'}.get(v['severity'].lower(),'⚪')
                print(f'\\n{icon} [{v[\"severity\"].upper()}] {v[\"title\"]}')
                print(f'   包: {v[\"package\"]}@{v[\"version\"]}')
                if v['cve'] != '-':
                    print(f'   CVE: {v[\"cve\"]}')
except FileNotFoundError:
    print('❌ 依赖索引不存在，请先运行 /atlas:deps')
except Exception as e:
    print(f'❌ 查询失败: {e}')
"
```
</details>

<details>
<summary>过期依赖</summary>

```bash
python3 -c "
import json

try:
    with open('.claude/.meta/dependencies.pkg.json') as f:
        data = json.load(f)
        deps = data.get('dependencies', [])

        # 找出过期的依赖
        outdated = []
        for d in deps:
            current = d.get('version', '')
            latest = d.get('latest', '')
            if latest and current != latest:
                outdated.append({
                    'name': d.get('name', '-'),
                    'current': current,
                    'latest': latest,
                    'type': d.get('type', '-')
                })

        if not outdated:
            print('所有依赖都是最新版本！')
        else:
            print(f'发现 {len(outdated)} 个过期依赖:')
            for d in outdated:
                type_mark = '📦' if d['type'] == 'dependencies' else '🛠️'
                print(f'  {type_mark} {d[\"name\"]}')
                print(f'      当前: {d[\"current\"]}')
                print(f'      最新: {d[\"latest\"]}')
except FileNotFoundError:
    print('❌ 依赖索引不存在，请先运行 /atlas:deps')
except Exception as e:
    print(f'❌ 查询失败: {e}')
"
```
</details>

<details>
<summary>依赖树</summary>

```bash
python3 -c "
import json
pkg_name = '$QUERY'.lower()

try:
    with open('.claude/.meta/dependencies.pkg.json') as f:
        data = json.load(f)
        tree = data.get('dependency_tree', {})

        # 查找包的依赖树
        matches = {k: v for k, v in tree.items() if pkg_name in k.lower()}

        if not matches:
            print(f'未找到 \"{pkg_name}\" 的依赖树')
        else:
            for pkg, children in matches.items():
                print(f'{pkg}')
                if children:
                    for i, child in enumerate(children):
                        is_last = i == len(children) - 1
                        prefix = '└── ' if is_last else '├── '
                        print(f'{prefix}{child}')
                else:
                    print('  (无依赖)')
except FileNotFoundError:
    print('❌ 依赖索引不存在，请先运行 /atlas:deps')
except KeyError:
    print('⚠️  依赖树数据不完整，请重新运行 /atlas:deps')
except Exception as e:
    print(f'❌ 查询失败: {e}')
"
```
</details>

<details>
<summary>使用位置</summary>

```bash
python3 -c "
import json
pkg_name = '$QUERY'.lower()

try:
    with open('.claude/.meta/dependencies.pkg.json') as f:
        data = json.load(f)
        usage = data.get('usage_locations', {})

        # 查找包的使用位置
        matches = {k: v for k, v in usage.items() if pkg_name in k.lower()}

        if not matches:
            print(f'未找到 \"{pkg_name}\" 的使用位置')
        else:
            for pkg, locations in matches.items():
                print(f'{pkg} 使用于:')
                if locations:
                    for loc in locations[:20]:  # 限制显示数量
                        print(f'  📄 {loc}')
                    if len(locations) > 20:
                        print(f'  ... 还有 {len(locations) - 20} 个位置')
                else:
                    print('  (未检测到直接引用)')
except FileNotFoundError:
    print('❌ 依赖索引不存在，请先运行 /atlas:deps')
except KeyError:
    print('⚠️  使用位置数据不完整，请重新运行 /atlas:deps')
except Exception as e:
    print(f'❌ 查询失败: {e}')
"
```
</details>

<details>
<summary>统计概览</summary>

```bash
python3 -c "
import json

try:
    with open('.claude/.meta/dependencies.pkg.json') as f:
        data = json.load(f)

        deps = data.get('dependencies', [])
        prod_deps = [d for d in deps if d.get('type') == 'dependencies']
        dev_deps = [d for d in deps if d.get('type') == 'devDependencies']

        # 统计漏洞
        vuln_count = sum(len(d.get('vulnerabilities', [])) for d in deps)
        critical = sum(1 for d in deps for v in d.get('vulnerabilities', []) if v.get('severity') == 'critical')
        high = sum(1 for d in deps for v in d.get('vulnerabilities', []) if v.get('severity') == 'high')

        # 统计过期
        outdated = sum(1 for d in deps if d.get('latest') and d.get('version') != d.get('latest'))

        print('=== 依赖统计 ===')
        print(f'生产依赖: {len(prod_deps)} 个')
        print(f'开发依赖: {len(dev_deps)} 个')
        print(f'总计: {len(deps)} 个')
        print(f'\\n过期依赖: {outdated} 个')
        print(f'\\n安全漏洞: {vuln_count} 个')
        if critical > 0:
            print(f'  🔴 严重: {critical}')
        if high > 0:
            print(f'  🟠 高危: {high}')

        # 最大的依赖包（如果有大小信息）
        if any(d.get('size') for d in deps):
            largest = sorted([d for d in deps if d.get('size')],
                           key=lambda x: x.get('size', 0), reverse=True)[:5]
            print(f'\\n最大的依赖:')
            for d in largest:
                size_mb = d.get('size', 0) / 1024 / 1024
                print(f'  {d.get(\"name\", \"-\")}: {size_mb:.2f} MB')
except FileNotFoundError:
    print('❌ 依赖索引不存在，请先运行 /atlas:deps')
except Exception as e:
    print(f'❌ 查询失败: {e}')
"
```
</details>

## 注意事项

- **支持模糊匹配** - 输入部分名称即可（如 `react` 匹配 `react-dom`、`react-router` 等）
- **索引过期？** - 运行 `/atlas:deps` 重新生成索引
- **数据源** - 所有数据来自 `.claude/.meta/dependencies.pkg.json`
- **漏洞严重性级别** - critical > high > moderate > low
- **降级方案** - 索引不存在时直接读取 `package.json` 或 `requirements.txt`
