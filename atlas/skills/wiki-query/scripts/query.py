#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wiki Query - 项目索引查询工具
支持跨文件模糊搜索
支持跨项目调用
"""

import json
import sys
import os
from pathlib import Path

# 索引目录（相对于项目根目录）
def find_wiki_dir():
    """
    查找 RepoWiki 目录
    支持以下场景:
    1. 当前目录是项目根目录
    2. 当前目录是项目子目录
    3. 从其他项目调用 (通过环境变量 WIKI_TARGET_DIR)
    """
    # 场景 3: 通过环境变量指定目标项目
    if 'WIKI_TARGET_DIR' in os.environ:
        target_dir = Path(os.environ['WIKI_TARGET_DIR'])
        test_path = target_dir / ".claude/repowiki/.meta"
        if test_path.exists():
            return target_dir / ".claude/repowiki", test_path

    # 场景 1: 当前目录
    test_path = Path(".claude/repowiki/.meta")
    if test_path.exists():
        return Path(".claude/repowiki"), test_path

    # 场景 2: 向上查找项目根目录
    for parent in Path.cwd().parents:
        test_path = parent / ".claude/repowiki/.meta"
        if test_path.exists():
            return parent / ".claude/repowiki", test_path

    return Path(".claude/repowiki"), Path(".claude/repowiki/.meta")

WIKI_DIR, META_DIR = find_wiki_dir()

def load_json(filename):
    """加载 JSON 文件"""
    try:
        with open(META_DIR / filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def fuzzy_match(query, text):
    """模糊匹配：支持多关键词"""
    if not query or not text:
        return False
    query = query.lower()
    text = text.lower()
    # 完整匹配
    if query in text:
        return True
    # 分词匹配（所有词都要出现）
    words = query.split()
    return all(w in text for w in words)

def search_all(query):
    """全局搜索：跨所有索引"""
    results = []

    # 搜索类
    symbols = load_json("symbols.pkg.json")
    for c in symbols.get('classes', []):
        name = c.get('name', '')
        if fuzzy_match(query, name):
            results.append({
                'type': '类',
                'name': name,
                'location': c.get('path', '-'),
                'extra': f"{len(c.get('methods', []))} methods"
            })

    # 搜索函数
    for f in symbols.get('functions', []):
        name = f.get('name', '')
        if fuzzy_match(query, name):
            results.append({
                'type': '函数',
                'name': name,
                'location': f.get('module', '-'),
                'extra': ''
            })

    # 搜索接口
    for i in symbols.get('interfaces', []):
        name = i.get('name', '')
        if fuzzy_match(query, name):
            results.append({
                'type': '接口',
                'name': name,
                'location': i.get('module', '-'),
                'extra': ''
            })

    # 搜索 API
    api = load_json("api.pkg.json")
    for e in api.get('endpoints', []):
        path = e.get('path', '')
        handler = e.get('handler', '')
        controller = e.get('controller', '')
        if fuzzy_match(query, path) or fuzzy_match(query, handler) or fuzzy_match(query, controller):
            results.append({
                'type': 'API',
                'name': f"{e.get('method', '')} {path}",
                'location': controller,
                'extra': '🔒' if e.get('auth') else '🔓'
            })

    # 搜索模块
    modules = load_json("modules.pkg.json")
    for m in modules.get('modules', []):
        name = m.get('name', '')
        if fuzzy_match(query, name):
            results.append({
                'type': '模块',
                'name': name,
                'location': m.get('path', '-'),
                'extra': ''
            })

    return results

def search_class(query):
    """搜索类及其方法"""
    symbols = load_json("symbols.pkg.json")
    classes = symbols.get('classes', [])

    matches = [c for c in classes if fuzzy_match(query, c.get('name', ''))]
    return matches, classes

def search_api(query):
    """搜索 API 端点"""
    api = load_json("api.pkg.json")
    endpoints = api.get('endpoints', [])

    results = []
    for e in endpoints:
        if (fuzzy_match(query, e.get('path', '')) or
            fuzzy_match(query, e.get('handler', '')) or
            fuzzy_match(query, e.get('controller', ''))):
            results.append(e)

    controllers = sorted(set(e.get('controller', '') for e in endpoints))
    return results, controllers

def search_module(query):
    """搜索模块和依赖"""
    modules = load_json("modules.pkg.json")

    module_list = [m for m in modules.get('modules', []) if fuzzy_match(query, m.get('name', ''))]
    deps = [g for g in modules.get('graph', [])
            if fuzzy_match(query, g.get('from', '')) or fuzzy_match(query, g.get('to', ''))]

    all_modules = [m.get('name', '') for m in modules.get('modules', [])]
    return module_list, deps, all_modules

def get_similar(query, items):
    """获取相似项（当没有精确匹配时）"""
    query_lower = query.lower()
    words = query_lower.split()

    similar = []
    for item in items:
        item_lower = item.lower()
        # 任意一个词匹配
        if any(w in item_lower for w in words):
            similar.append(item)
        # 或者有公共子串（长度>=3）
        elif len(query_lower) >= 3:
            for i in range(len(query_lower) - 2):
                if query_lower[i:i+3] in item_lower:
                    similar.append(item)
                    break

    return similar[:10]

def print_results(results, query, limit=20):
    """打印搜索结果"""
    if results:
        print(f'搜索 "{query}" 找到 {len(results)} 个结果:')
        for r in results[:limit]:
            extra = f" ({r['extra']})" if r.get('extra') else ''
            print(f"  [{r['type']:4}] {r['name']}{extra}")
            print(f"         @ {r['location']}")
        if len(results) > limit:
            print(f"  ... 还有 {len(results) - limit} 个")
    else:
        print(f'未找到 "{query}"')

def cmd_search(query):
    """命令：全局搜索"""
    results = search_all(query)
    print_results(results, query)

    if not results:
        # 显示相似项
        symbols = load_json("symbols.pkg.json")
        all_names = [c.get('name', '') for c in symbols.get('classes', [])]
        all_names += [f.get('name', '') for f in symbols.get('functions', [])]
        similar = get_similar(query, all_names)
        if similar:
            print("\n相似的符号:")
            for s in similar:
                print(f"  - {s}")

def cmd_class(query):
    """命令：类查询"""
    matches, all_classes = search_class(query)

    if not matches:
        print(f'未找到包含 "{query}" 的类')
        similar = get_similar(query, [c.get('name', '') for c in all_classes])
        if similar:
            print("\n相似的类:")
            for s in similar:
                print(f"  - {s}")
        else:
            print(f"\n项目中的类 ({len(all_classes)} 个):")
            for c in all_classes[:15]:
                print(f"  - {c.get('name', '-')}")
            if len(all_classes) > 15:
                print(f"  ... 还有 {len(all_classes) - 15} 个")
    elif len(matches) == 1:
        c = matches[0]
        print(f"类: {c.get('name', '-')}")
        print(f"路径: {c.get('path', '-')}")
        if c.get('extends'):
            print(f"继承: {c['extends']}")
        if c.get('implements'):
            print(f"实现: {c['implements']}")
        methods = c.get('methods', [])
        if methods:
            print(f"方法 ({len(methods)} 个):")
            for m in methods:
                vis = {'public': '🟢', 'private': '🔴', 'protected': '🟡'}.get(m.get('visibility', ''), '⚪')
                print(f"  {vis} {m.get('name', '-')}()")
    else:
        print(f'找到 {len(matches)} 个匹配的类:')
        for c in matches:
            print(f"  - {c.get('name', '-')} ({len(c.get('methods', []))} methods)")
            print(f"    @ {c.get('path', '-')}")

def cmd_api(query):
    """命令：API 查询"""
    results, controllers = search_api(query)

    if results:
        print(f'API 搜索 "{query}" ({len(results)} 个):')
        for e in results[:15]:
            auth = '🔒' if e.get('auth') else '🔓'
            print(f"  {auth} {e.get('method', ''):6} {e.get('path', '')}")
            print(f"       → {e.get('controller', '-')}.{e.get('handler', '-')}")
        if len(results) > 15:
            print(f"  ... 还有 {len(results) - 15} 个")
    else:
        print(f'未找到包含 "{query}" 的 API')
        similar = get_similar(query, controllers)
        if similar:
            print("\n相似的 Controller:")
            for s in similar:
                print(f"  - {s}")
        else:
            print(f"\n可用的 Controller ({len(controllers)} 个):")
            for c in controllers[:10]:
                print(f"  - {c}")

def cmd_module(query):
    """命令：模块查询"""
    modules, deps, all_modules = search_module(query)

    if modules:
        print(f'匹配的模块 ({len(modules)} 个):')
        for m in modules:
            print(f"  {m.get('name', '-')} @ {m.get('path', '-')}")

    if deps:
        print(f"\n相关依赖 ({len(deps)} 个):")
        for g in deps[:15]:
            print(f"  {g.get('from', '-')} → {g.get('to', '-')}")
        if len(deps) > 15:
            print(f"  ... 还有 {len(deps) - 15} 个")

    if not modules and not deps:
        print(f'未找到包含 "{query}" 的模块')
        similar = get_similar(query, all_modules)
        if similar:
            print("\n相似的模块:")
            for s in similar:
                print(f"  - {s}")
        else:
            print(f"\n可用模块 ({len(all_modules)} 个):")
            for m in all_modules[:10]:
                print(f"  - {m}")

def cmd_stats():
    """命令：统计概览"""
    print("=== 项目统计 ===\n")

    project = load_json("project.pkg.json")
    if project:
        print(f"项目: {project.get('name', '-')}")
        tech = project.get('techStack', {})
        if tech:
            print(f"语言: {', '.join(tech.get('languages', []))}")
            print(f"框架: {', '.join(tech.get('frameworks', []))}")

    symbols = load_json("symbols.pkg.json")
    if symbols:
        print(f"\n符号统计:")
        print(f"  类: {len(symbols.get('classes', []))} 个")
        print(f"  函数: {len(symbols.get('functions', []))} 个")
        print(f"  接口: {len(symbols.get('interfaces', []))} 个")

    api = load_json("api.pkg.json")
    if api:
        endpoints = api.get('endpoints', [])
        print(f"\nAPI 统计:")
        print(f"  端点: {len(endpoints)} 个")
        auth_count = sum(1 for e in endpoints if e.get('auth'))
        print(f"  需认证: {auth_count} 个")

    modules = load_json("modules.pkg.json")
    if modules:
        print(f"\n模块统计:")
        print(f"  模块: {len(modules.get('modules', []))} 个")
        print(f"  依赖关系: {len(modules.get('graph', []))} 个")

def main():
    """主程序"""
    if not META_DIR.exists():
        print("❌ RepoWiki 不存在，请先运行 /atlas:repo-wiki")
        sys.exit(1)

    if len(sys.argv) < 2:
        print("Wiki Query - 项目索引查询工具")
        print("\n用法:")
        print("  python query.py search <keyword>   # 全局搜索（推荐）")
        print("  python query.py class <name>       # 查询类及方法")
        print("  python query.py api <keyword>      # 查询 API 端点")
        print("  python query.py module <name>      # 查询模块依赖")
        print("  python query.py stats              # 项目统计")
        print("\n示例:")
        print("  python query.py search User        # 搜索所有包含 User 的内容")
        print("  python query.py class UserService  # 查看 UserService 类")
        print("  python query.py api login          # 查找登录相关 API")
        print("  python query.py module order       # 查看 order 模块依赖")
        return

    cmd = sys.argv[1].lower()
    query = ' '.join(sys.argv[2:]) if len(sys.argv) > 2 else ''

    if cmd == 'search' and query:
        cmd_search(query)
    elif cmd == 'class' and query:
        cmd_class(query)
    elif cmd == 'api' and query:
        cmd_api(query)
    elif cmd == 'module' and query:
        cmd_module(query)
    elif cmd == 'stats':
        cmd_stats()
    else:
        print(f"未知命令或缺少参数: {cmd}")
        print("使用 'python query.py' 查看帮助")

if __name__ == "__main__":
    main()
