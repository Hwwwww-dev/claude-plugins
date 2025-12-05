---
name: wiki-query
description: 当用户询问"项目有哪些API"、"XXX类有哪些方法"、"查找XXX"、"模块依赖"等项目结构问题时，使用此 skill。优先级高于 Serena。支持模糊搜索，找不到时显示相似结果。
version: 2.1.0
color: blue
---

# Wiki Query - 项目索引查询

从 `.claude/repowiki/` 索引查询项目信息。**优先级 > Serena**。

## 脚本路径

使用 `${CLAUDE_PLUGIN_ROOT}` 环境变量（Claude Code 自动设置）：

```bash
# 脚本位置
${CLAUDE_PLUGIN_ROOT}/skills/wiki-query/scripts/query.py        # 标准查询
${CLAUDE_PLUGIN_ROOT}/skills/wiki-query/scripts/stream_query.py # 流式查询（推荐）
```

**备选**：相对路径 `scripts/query.py`（依赖 Claude 自动解析 base path）

## 前置条件

```bash
# 检查索引是否存在
ls .claude/repowiki/.meta/*.pkg.json 2>/dev/null || echo "❌ 请先运行 /atlas:repo-wiki"

# 流式查询需要 ijson（可选）
pip install ijson
```

## 快速查询

**所有调用必须设置 `WIKI_TARGET_DIR=$PWD`**

```bash
# 流式查询（推荐，大文件友好）
WIKI_TARGET_DIR=$PWD python3 "${CLAUDE_PLUGIN_ROOT}/skills/wiki-query/scripts/stream_query.py" class <ClassName>
WIKI_TARGET_DIR=$PWD python3 "${CLAUDE_PLUGIN_ROOT}/skills/wiki-query/scripts/stream_query.py" api <keyword>

# 标准查询
WIKI_TARGET_DIR=$PWD python3 "${CLAUDE_PLUGIN_ROOT}/skills/wiki-query/scripts/query.py" search <keyword>  # 全局搜索
WIKI_TARGET_DIR=$PWD python3 "${CLAUDE_PLUGIN_ROOT}/skills/wiki-query/scripts/query.py" class <name>     # 类查询
WIKI_TARGET_DIR=$PWD python3 "${CLAUDE_PLUGIN_ROOT}/skills/wiki-query/scripts/query.py" api <keyword>    # API 查询
WIKI_TARGET_DIR=$PWD python3 "${CLAUDE_PLUGIN_ROOT}/skills/wiki-query/scripts/query.py" module <name>    # 模块依赖
WIKI_TARGET_DIR=$PWD python3 "${CLAUDE_PLUGIN_ROOT}/skills/wiki-query/scripts/query.py" stats            # 项目统计

# 跨项目查询
WIKI_TARGET_DIR="/path/to/other-project" python3 "${CLAUDE_PLUGIN_ROOT}/skills/wiki-query/scripts/query.py" class UserService
```

## 内联命令（备用）

当脚本不可用时，可使用内联 Python：

<details>
<summary>全局搜索</summary>

```bash
python3 -c "
import json, sys
q = '$QUERY'.lower()
r = []

# 搜索类
try:
    with open('.claude/repowiki/.meta/symbols.pkg.json') as f:
        d = json.load(f)
        for c in d.get('classes', []):
            if q in c.get('name', '').lower():
                r.append(('类', c['name'], c.get('path', '-'), len(c.get('methods', []))))
except: pass

# 搜索 API
try:
    with open('.claude/repowiki/.meta/api.pkg.json') as f:
        d = json.load(f)
        for e in d.get('endpoints', []):
            if q in e.get('path', '').lower() or q in e.get('handler', '').lower() or q in e.get('controller', '').lower():
                r.append(('API', f\"{e['method']} {e['path']}\", e.get('controller', '-'), 0))
except: pass

# 搜索模块
try:
    with open('.claude/repowiki/.meta/modules.pkg.json') as f:
        d = json.load(f)
        for m in d.get('modules', []):
            if q in m.get('name', '').lower():
                r.append(('模块', m['name'], m.get('path', '-'), 0))
except: pass

if r:
    print(f'搜索 \"{q}\" 找到 {len(r)} 个结果:')
    for t, n, p, c in r[:20]:
        extra = f' ({c} methods)' if c > 0 else ''
        print(f'  [{t}] {n}{extra}')
        print(f'        @ {p}')
else:
    print(f'未找到 \"{q}\"')
"
```
</details>

<details>
<summary>类查询</summary>

```bash
python3 -c "
import json
q = '$QUERY'.lower()
with open('.claude/repowiki/.meta/symbols.pkg.json') as f:
    d = json.load(f)
    matches = [c for c in d.get('classes', []) if q in c.get('name', '').lower()]

    if len(matches) == 0:
        print(f'未找到包含 \"{q}\" 的类')
        all_classes = [c['name'] for c in d.get('classes', [])]
        print(f'\\n项目中的类 ({len(all_classes)} 个):')
        for c in all_classes[:15]:
            print(f'  - {c}')
    elif len(matches) == 1:
        c = matches[0]
        print(f'类: {c[\"name\"]}')
        print(f'路径: {c.get(\"path\", \"-\")}')
        if c.get('extends'): print(f'继承: {c[\"extends\"]}')
        if c.get('implements'): print(f'实现: {c[\"implements\"]}')
        if c.get('methods'):
            print(f'方法 ({len(c[\"methods\"])} 个):')
            for m in c['methods']:
                v = {'public':'🟢','private':'🔴','protected':'🟡'}.get(m.get('visibility',''),'⚪')
                print(f'  {v} {m.get(\"name\", \"-\")}()')
    else:
        print(f'找到 {len(matches)} 个匹配类:')
        for c in matches:
            print(f'  - {c[\"name\"]} ({len(c.get(\"methods\",[]))} methods) @ {c.get(\"path\",\"-\")}')
"
```
</details>

<details>
<summary>API 查询</summary>

```bash
python3 -c "
import json
q = '$QUERY'.lower()
with open('.claude/repowiki/.meta/api.pkg.json') as f:
    d = json.load(f)
    results = [e for e in d.get('endpoints', [])
               if q in e.get('path', '').lower()
               or q in e.get('controller', '').lower()
               or q in e.get('handler', '').lower()]

    if results:
        print(f'API 搜索 \"{q}\" ({len(results)} 个):')
        for e in results[:15]:
            auth = '🔒' if e.get('auth') else '🔓'
            print(f'  {auth} {e[\"method\"]:6} {e[\"path\"]}')
            print(f'       → {e.get(\"controller\",\"-\")}.{e.get(\"handler\",\"-\")}')
    else:
        print(f'未找到包含 \"{q}\" 的 API')
"
```
</details>

<details>
<summary>模块依赖</summary>

```bash
python3 -c "
import json
q = '$QUERY'.lower()
with open('.claude/repowiki/.meta/modules.pkg.json') as f:
    d = json.load(f)
    modules = [m for m in d.get('modules', []) if q in m.get('name', '').lower()]
    deps = [g for g in d.get('graph', []) if q in g.get('from', '').lower() or q in g.get('to', '').lower()]

    if modules:
        print(f'匹配的模块 ({len(modules)} 个):')
        for m in modules:
            print(f'  {m.get(\"name\", \"-\")} @ {m.get(\"path\", \"-\")}')
    if deps:
        print(f'\\n相关依赖 ({len(deps)} 个):')
        for g in deps[:15]:
            print(f'  {g.get(\"from\", \"-\")} → {g.get(\"to\", \"-\")}')
"
```
</details>

<details>
<summary>统计概览</summary>

```bash
python3 -c "
import json
print('=== 项目统计 ===')

try:
    with open('.claude/repowiki/.meta/symbols.pkg.json') as f:
        d = json.load(f)
        print(f'类: {len(d.get(\"classes\", []))} 个')
        print(f'函数: {len(d.get(\"functions\", []))} 个')
        print(f'接口: {len(d.get(\"interfaces\", []))} 个')
except: pass

try:
    with open('.claude/repowiki/.meta/api.pkg.json') as f:
        d = json.load(f)
        print(f'API 端点: {len(d.get(\"endpoints\", []))} 个')
except: pass

try:
    with open('.claude/repowiki/.meta/modules.pkg.json') as f:
        d = json.load(f)
        print(f'模块: {len(d.get(\"modules\", []))} 个')
except: pass
"
```
</details>

## 注意事项

- **支持模糊匹配** - 输入部分名称即可（如 `User` 匹配 `UserService`）
- **找不到时显示相似项** - 帮助定位正确名称
- **流式查询更优** - `stream_query.py` 内存占用低，适合大型项目
- **索引过期？** - 运行 `/atlas:repo-wiki --force` 重建
- **降级方案** - 索引不完整时使用 Serena MCP 直接查询源码
