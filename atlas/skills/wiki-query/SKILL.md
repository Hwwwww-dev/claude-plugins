---
name: wiki-query
description: 当用户询问"项目有哪些API"、"XXX类有哪些方法"、"模块依赖关系"等项目结构问题时，使用此 skill 从 .claude/repowiki 索引中精确检索，避免读取完整JSON。触发词：查询API、查找符号、模块依赖、项目结构、类方法、端点列表。
version: 1.0.0
color: blue
---

# Wiki Query - 索引查询工具

从 `.claude/repowiki/` 索引中精确检索信息，只返回需要的数据。

## 使用场景

**前提条件**：`.claude/repowiki/` 目录存在（已运行过 `/atlas:repo-wiki`）

## 检查前置条件

**首先检查 `.claude/repowiki/` 是否存在：**

```bash
ls -la .claude/repowiki/.meta/ 2>/dev/null || echo "repowiki 不存在，请先运行 /atlas:repo-wiki"
```

如果不存在，提示用户先运行 `/atlas:repo-wiki` 生成索引。

---

## 查询命令

### 1. 项目概览

```bash
# 快速获取项目基本信息
python3 -c "
import json
with open('.claude/repowiki/.meta/project.pkg.json') as f:
    d = json.load(f)
    print(f\"项目: {d.get('name', 'unknown')}\")
    print(f\"版本: {d.get('version', '-')}\")
    print(f\"技术栈: {', '.join(d.get('techStack', {}).get('languages', []))}\")
    print(f\"框架: {', '.join(d.get('techStack', {}).get('frameworks', []))}\")
    print(f\"依赖数: {len(d.get('dependencies', {}).get('production', []))}\")
"
```

### 2. API 端点查询

#### 按路径搜索
```bash
python3 -c "
import json, sys
keyword = '$QUERY'
with open('.claude/repowiki/.meta/api.pkg.json') as f:
    d = json.load(f)
    results = [e for e in d.get('endpoints', []) if keyword.lower() in e.get('path', '').lower()]
    print(f'找到 {len(results)} 个匹配端点:')
    for e in results[:10]:
        auth = '🔒' if e.get('auth') else '🔓'
        print(f\"  {auth} {e['method']:6} {e['path']}\")
        print(f\"     → {e.get('controller', '-')}.{e.get('handler', '-')}\")
    if len(results) > 10:
        print(f'  ... 还有 {len(results)-10} 个')
"
```

#### 按 Controller 搜索
```bash
python3 -c "
import json
name = '$QUERY'
with open('.claude/repowiki/.meta/api.pkg.json') as f:
    d = json.load(f)
    results = [e for e in d.get('endpoints', []) if name.lower() in e.get('controller', '').lower()]
    print(f'Controller \"{name}\" 的端点 ({len(results)}个):')
    for e in results:
        auth = '🔒' if e.get('auth') else '🔓'
        print(f\"  {auth} {e['method']:6} {e['path']}\")
"
```

#### 按 HTTP 方法统计
```bash
python3 -c "
import json
from collections import Counter
with open('.claude/repowiki/.meta/api.pkg.json') as f:
    d = json.load(f)
    methods = Counter(e['method'] for e in d.get('endpoints', []))
    print('HTTP 方法分布:')
    for m, c in sorted(methods.items()):
        print(f'  {m:7} {c:3} 个')
    print(f'总计: {sum(methods.values())} 个端点')
"
```

### 3. 符号查询

#### 按名称搜索符号
```bash
python3 -c "
import json
name = '$QUERY'
with open('.claude/repowiki/.meta/symbols.pkg.json') as f:
    d = json.load(f)
    # 搜索类
    classes = [c for c in d.get('classes', []) if name.lower() in c.get('name', '').lower()]
    # 搜索函数
    funcs = [f for f in d.get('functions', []) if name.lower() in f.get('name', '').lower()]
    # 搜索接口
    interfaces = [i for i in d.get('interfaces', []) if name.lower() in i.get('name', '').lower()]

    if classes:
        print(f'类 ({len(classes)}个):')
        for c in classes[:5]:
            print(f\"  {c['name']} @ {c.get('path', '-')}\")
    if funcs:
        print(f'函数 ({len(funcs)}个):')
        for f in funcs[:5]:
            print(f\"  {f['name']}({', '.join(p.get('name','') for p in f.get('params', []))}) @ {f.get('module', '-')}\")
    if interfaces:
        print(f'接口 ({len(interfaces)}个):')
        for i in interfaces[:5]:
            print(f\"  {i['name']} @ {i.get('module', '-')}\")
"
```

#### 获取类的详细信息
```bash
python3 -c "
import json
name = '$QUERY'
with open('.claude/repowiki/.meta/symbols.pkg.json') as f:
    d = json.load(f)
    for c in d.get('classes', []):
        if c.get('name', '').lower() == name.lower():
            print(f\"类: {c['name']}\")
            print(f\"路径: {c.get('path', '-')}\")
            print(f\"模块: {c.get('module', '-')}\")
            if c.get('extends'): print(f\"继承: {c['extends']}\")
            if c.get('implements'): print(f\"实现: {', '.join(c['implements'])}\")
            if c.get('methods'):
                print(f\"方法 ({len(c['methods'])}个):\")
                for m in c['methods'][:10]:
                    vis = {'public':'🟢','private':'🔴','protected':'🟡'}.get(m.get('visibility',''),'⚪')
                    print(f\"  {vis} {m.get('name', '-')}()\")
            break
    else:
        print(f'未找到类: {name}')
"
```

### 4. 模块查询

#### 列出所有模块
```bash
python3 -c "
import json
with open('.claude/repowiki/.meta/modules.pkg.json') as f:
    d = json.load(f)
    modules = d.get('modules', [])
    print(f'模块列表 ({len(modules)}个):')
    for m in modules:
        exports = len(m.get('exports', []))
        print(f\"  {m.get('name', '-'):20} {m.get('path', '-'):30} ({exports} exports)\")
"
```

#### 查询模块依赖
```bash
python3 -c "
import json
name = '$QUERY'
with open('.claude/repowiki/.meta/modules.pkg.json') as f:
    d = json.load(f)
    graph = d.get('graph', [])
    deps = [g for g in graph if g.get('from', '').lower() == name.lower() or name.lower() in g.get('from', '').lower()]
    if deps:
        print(f'模块 \"{name}\" 的依赖:')
        for dep in deps:
            print(f\"  {dep.get('from', '-')} → {dep.get('to', '-')}\")
    else:
        print(f'未找到模块依赖: {name}')
"
```

### 5. 快速查找

#### 符号快速定位
```bash
python3 -c "
import json
keyword = '$QUERY'
with open('.claude/repowiki/.index/quick-lookup.json') as f:
    d = json.load(f)
    results = {k:v for k,v in d.get('quickSearch', {}).items() if keyword.lower() in k.lower()}
    if results:
        print(f'快速查找结果 ({len(results)}个):')
        for k, v in list(results.items())[:10]:
            print(f\"  {k}: {v.get('type', '-')} @ {v.get('file', v.get('doc', '-'))}\")
    else:
        print(f'未找到: {keyword}')
"
```

### 6. 质量统计

```bash
python3 -c "
import json
with open('.claude/repowiki/.meta/quality.pkg.json') as f:
    d = json.load(f)
    stats = d.get('stats', {})
    print('代码统计:')
    print(f\"  总文件数: {stats.get('totalFiles', '-')}\")
    print(f\"  总行数: {stats.get('totalLines', '-')}\")
    print(f\"  平均行数: {stats.get('avgLines', '-')}\")

    warnings = d.get('warnings', {})
    if warnings.get('largeFunctions'):
        print(f\"\\n大函数警告 ({len(warnings['largeFunctions'])}个):\")
        for w in warnings['largeFunctions'][:5]:
            print(f\"  {w.get('name', '-')} @ {w.get('file', '-')} ({w.get('lines', '-')}行)\")
"
```

---

## 使用示例

用户问: "项目有哪些 API 端点与用户相关?"

```bash
# 执行查询
python3 -c "
import json
with open('.claude/repowiki/.meta/api.pkg.json') as f:
    d = json.load(f)
    results = [e for e in d.get('endpoints', []) if 'user' in e.get('path', '').lower()]
    print(f'用户相关 API ({len(results)}个):')
    for e in results:
        auth = '🔒' if e.get('auth') else '🔓'
        print(f\"  {auth} {e['method']:6} {e['path']}\")
"
```

用户问: "UserService 类有哪些方法?"

```bash
python3 -c "
import json
with open('.claude/repowiki/.meta/symbols.pkg.json') as f:
    d = json.load(f)
    for c in d.get('classes', []):
        if 'UserService' in c.get('name', ''):
            print(f\"类: {c['name']}\")
            for m in c.get('methods', []):
                print(f\"  - {m.get('name', '-')}()\")
            break
"
```

---

## 注意事项

1. **所有查询都是只读的**，不会修改任何文件
2. **按需查询**，只返回需要的数据，节省上下文
3. **如果索引不存在**，提示用户先运行 `/atlas:repo-wiki`
4. **查询结果有限制**，默认显示前 10 条，避免输出过多
5. **替换 `$QUERY`** 为实际的查询关键词

---

## 与其他命令配合

```bash
# 1. 先用 wiki-query 了解项目结构
/skill wiki-query → 查询 UserService

# 2. 找到文件后用 gather 深入分析
/gather dependencies UserService

# 3. 基于分析结果执行任务
/orchestrate 重构 UserService
```
