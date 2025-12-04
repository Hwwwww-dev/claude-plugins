---
name: wiki-query
description: 当用户询问"项目有哪些API"、"XXX类有哪些方法"、"查找XXX"、"模块依赖"等项目结构问题时，使用此 skill。优先级高于 Serena。支持模糊搜索，找不到时显示相似结果。
version: 2.0.1
color: blue
---

# Wiki Query - 项目索引查询

**`.claude/repowiki/`** 为项目级，在调用脚本时请正确使用路径！

从 `.claude/repowiki/` 索引中查询项目信息。**优先级 > Serena**。

## 核心原则

1. **优先使用流式脚本** - `stream_query.py` 避免读取完整 JSON
2. **相对路径调用** - 使用 `scripts/query.py`，Claude 自动处理 Skill 目录
3. **跨项目支持** - 通过 `WIKI_TARGET_DIR` 环境变量查询其他项目

## 前置检查

```bash
ls .claude/repowiki/.meta/*.pkg.json 2>/dev/null || echo "❌ RepoWiki 不存在，请先运行 /atlas:repo-wiki"
```

## 依赖安装

流式查询需要 ijson 库：
```bash
pip install ijson
```

如果无法安装，可使用标准查询（会读取完整 JSON）。

## 快速开始

流式查询（推荐 - 避免读取完整 JSON）：
```python
# 查询类方法
python3 scripts/stream_query.py class <ClassName>

# 查询 API
python3 scripts/stream_query.py api <keyword>
```

标准查询：
```python
# 全局搜索
python3 scripts/query.py search <keyword>

# 查询类
python3 scripts/query.py class <ClassName>

# 查询 API
python3 scripts/query.py api <keyword>

# 查询模块
python3 scripts/query.py module <ModuleName>

# 项目统计
python3 scripts/query.py stats
```

---

## 查询方式

### 方式一：使用查询脚本（推荐 - 避免读取完整 JSON）

**标准查询脚本**：

```bash
# 全局搜索（推荐首选）
python3 scripts/query.py search <keyword>

# 类查询（查看类的方法、继承关系）
python3 scripts/query.py class <name>

# API 查询（端点、控制器、认证信息）
python3 scripts/query.py api <keyword>

# 模块依赖（模块及其依赖关系）
python3 scripts/query.py module <name>

# 项目统计概览
python3 scripts/query.py stats
```

**流式查询脚本**（推荐 - 避免读取完整 JSON，需要 ijson 库）：

```bash
# 安装依赖（仅首次）
pip install ijson

# 流式类查询（大文件友好）
python3 scripts/stream_query.py class <name>

# 流式 API 查询（大文件友好）
python3 scripts/stream_query.py api <keyword>
```

### 跨项目查询

如果你在一个项目（A）中，想查询另一个项目（B）的 RepoWiki：

```bash
# 设置环境变量指向目标项目
export WIKI_TARGET_DIR="/path/to/project-B"

# 然后正常调用查询脚本
python3 scripts/query.py class UserService
```

### 方式二：内联命令

#### 1. 全局搜索

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
    print(f'未找到 \"{q}\"，尝试显示相似项...')
    try:
        with open('.claude/repowiki/.meta/symbols.pkg.json') as f:
            d = json.load(f)
            classes = [c['name'] for c in d.get('classes', [])]
            similar = [c for c in classes if any(w in c.lower() for w in q.split())]
            if similar:
                print('相似的类:')
                for c in similar[:10]:
                    print(f'  - {c}')
    except: pass
"
```

#### 2. 类查询

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

#### 3. API 查询

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
        controllers = set(e.get('controller','') for e in d.get('endpoints',[]))
        print(f'\\n可用的 Controller ({len(controllers)} 个):')
        for c in sorted(controllers)[:10]:
            print(f'  - {c}')
"
```

#### 4. 模块依赖

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
    if not modules and not deps:
        print(f'未找到包含 \"{q}\" 的模块')
        all_modules = [m['name'] for m in d.get('modules', [])]
        print(f'\\n可用模块 ({len(all_modules)} 个):')
        for m in all_modules[:10]:
            print(f'  - {m}')
"
```

#### 5. 统计概览

```bash
python3 -c "
import json
print('=== 项目统计 ===')

try:
    with open('.claude/repowiki/.meta/project.pkg.json') as f:
        d = json.load(f)
        print(f'项目: {d.get(\"name\", \"-\")}')
        print(f'技术栈: {d.get(\"techStack\", {})}')
except: pass

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

---

## 使用示例

| 用户问题 | 推荐命令 |
|:---------|:---------|
| "XXX 类有哪些方法？" | `python3 scripts/stream_query.py class XXX` |
| "项目有哪些 XXX 相关 API？" | `python3 scripts/stream_query.py api XXX` |
| "找一下 XXX 相关的类" | `python3 scripts/query.py search XXX` |
| "XXX 模块依赖哪些？" | `python3 scripts/query.py module XXX` |
| "项目有多少个类和 API？" | `python3 scripts/query.py stats` |

## 性能对比

| 脚本 | JSON 读取方式 | 内存占用 | 适用场景 |
|:-----|:-------------|:---------|:---------|
| `query.py` | 完整读取 | 高 | 小型项目（<100 类） |
| `stream_query.py` | 流式增量 | 低 | 大型项目（>=100 类） |

**推荐策略**：
- 优先使用 `stream_query.py`（需要 `pip install ijson`）
- 如果无法安装 ijson，降级使用 `query.py`

---

## 注意事项

1. **优先使用流式查询** - `stream_query.py` 避免读取完整 JSON，内存占用低
2. **支持模糊匹配** - 输入部分名称即可（如 `XXX` 可匹配 `XXXController`）
3. **找不到时显示相似项** - 帮助定位正确名称
4. **跨项目查询** - 通过环境变量 `WIKI_TARGET_DIR` 查询其他项目的 RepoWiki
5. **依赖说明** - 流式查询需要 `pip install ijson`，如无法安装则使用标准查询

## 索引数据不完整的解决方案

如果查询不到预期的类或 API：

1. **检查 RepoWiki 是否最新**：
   ```bash
   ls -lh .claude/repowiki/.meta/symbols.pkg.json
   ```

2. **重新生成索引**（强制全量构建）：
   ```bash
   /atlas:repo-wiki --force
   ```

3. **使用 Serena MCP 直接查询**（作为降级方案）：
   - Serena 直接分析源代码，不依赖索引
   - 但 Serena 消耗更多 Token

## 性能建议

| 场景 | 推荐工具 | 理由 |
|:-----|:---------|:-----|
| 快速查询类/API | `stream_query.py` | 流式解析，内存占用低 |
| 小型项目 | `query.py` | 简单直接，无需额外依赖 |
| 大型项目（>100类） | `stream_query.py` | 避免 OOM，查询速度快 |
| 索引不完整 | Serena MCP | 直接分析源码，100% 准确 |
