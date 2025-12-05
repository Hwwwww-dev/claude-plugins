#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
流式 JSON 查询工具 - 避免读取完整 JSON 文件
使用 ijson 库实现增量解析
支持跨项目调用
"""

import sys
import os
from pathlib import Path

try:
    import ijson
except ImportError:
    print("❌ 缺少依赖: pip install ijson")
    sys.exit(1)

def find_wiki_dir():
    """
    查找 RepoWiki 目录
    支持以下场景:
    1. 通过环境变量 WIKI_TARGET_DIR 指定项目目录（推荐，解决 skill 调用路径问题）
    2. 当前目录是项目根目录
    3. 当前目录是项目子目录（向上查找）
    """
    # 场景 1: 通过 WIKI_TARGET_DIR 环境变量指定（推荐）
    if 'WIKI_TARGET_DIR' in os.environ:
        target_dir = Path(os.environ['WIKI_TARGET_DIR'])
        test_path = target_dir / ".claude/repowiki/.meta"
        if test_path.exists():
            return target_dir / ".claude/repowiki", test_path

    # 场景 2: 当前目录
    test_path = Path(".claude/repowiki/.meta")
    if test_path.exists():
        return Path(".claude/repowiki"), test_path

    # 场景 3: 向上查找项目根目录
    for parent in Path.cwd().parents:
        test_path = parent / ".claude/repowiki/.meta"
        if test_path.exists():
            return parent / ".claude/repowiki", test_path

    return Path(".claude/repowiki"), Path(".claude/repowiki/.meta")

WIKI_DIR, META_DIR = find_wiki_dir()

def fuzzy_match(query, text):
    """模糊匹配"""
    if not query or not text:
        return False
    query = query.lower()
    text = text.lower()
    if query in text:
        return True
    words = query.split()
    return all(w in text for w in words)

def stream_search_classes(query, limit=20):
    """流式搜索类（避免读取整个文件）"""
    pkg_file = META_DIR / "symbols.pkg.json"
    if not pkg_file.exists():
        return []

    results = []
    try:
        with open(pkg_file, 'rb') as f:
            # 先尝试扁平结构: {"classes": [...]}
            parser = ijson.items(f, 'classes.item')
            for cls in parser:
                name = cls.get('name', '')
                if fuzzy_match(query, name):
                    results.append(cls)
                    if len(results) >= limit:
                        break

        # 如果扁平结构没找到，尝试嵌套结构: {"modules": {"name": {"classes": [...]}}}
        if not results:
            with open(pkg_file, 'rb') as f:
                # 使用 kvitems 遍历 modules dict
                for module_name, module_data in ijson.kvitems(f, 'modules'):
                    if isinstance(module_data, dict):
                        classes = module_data.get('classes', [])
                        for cls in classes:
                            name = cls.get('name', '')
                            if fuzzy_match(query, name):
                                results.append(cls)
                                if len(results) >= limit:
                                    break
                    if len(results) >= limit:
                        break
    except Exception as e:
        print(f"⚠️  流式解析失败: {e}")
        return []

    return results

def stream_search_api(query, limit=20):
    """流式搜索 API（避免读取整个文件）"""
    pkg_file = META_DIR / "api.pkg.json"
    if not pkg_file.exists():
        return []

    results = []
    try:
        with open(pkg_file, 'rb') as f:
            parser = ijson.items(f, 'endpoints.item')
            for endpoint in parser:
                path = endpoint.get('path', '')
                handler = endpoint.get('handler', '')
                controller = endpoint.get('controller', '')
                if fuzzy_match(query, path) or fuzzy_match(query, handler) or fuzzy_match(query, controller):
                    results.append(endpoint)
                    if len(results) >= limit:
                        break
    except Exception as e:
        print(f"⚠️  流式解析失败: {e}")
        return []

    return results

def cmd_class_stream(query):
    """流式类查询"""
    matches = stream_search_classes(query, limit=50)

    if not matches:
        print(f'未找到包含 "{query}" 的类')
        return

    if len(matches) == 1:
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
        for c in matches[:20]:
            print(f"  - {c.get('name', '-')} ({len(c.get('methods', []))} methods)")
            print(f"    @ {c.get('path', '-')}")
        if len(matches) > 20:
            print(f"  ... 还有 {len(matches) - 20} 个")

def cmd_api_stream(query):
    """流式 API 查询"""
    results = stream_search_api(query, limit=50)

    if not results:
        print(f'未找到包含 "{query}" 的 API')
        return

    print(f'API 搜索 "{query}" ({len(results)} 个):')
    for e in results[:15]:
        auth = '🔒' if e.get('auth') else '🔓'
        print(f"  {auth} {e.get('method', ''):6} {e.get('path', '')}")
        print(f"       → {e.get('controller', '-')}.{e.get('handler', '-')}")
    if len(results) > 15:
        print(f"  ... 还有 {len(results) - 15} 个")

def main():
    """主程序"""
    if not META_DIR.exists():
        print("❌ RepoWiki 不存在，请先运行 /atlas:repo-wiki")
        sys.exit(1)

    if len(sys.argv) < 3:
        print("流式 JSON 查询工具 - 避免读取完整文件")
        print("\n用法:")
        print("  python stream_query.py class <name>    # 流式类查询")
        print("  python stream_query.py api <keyword>   # 流式 API 查询")
        print("\n优势:")
        print("  ✓ 不读取整个 JSON 文件")
        print("  ✓ 内存占用低")
        print("  ✓ 查询速度快")
        return

    cmd = sys.argv[1].lower()
    query = ' '.join(sys.argv[2:])

    if cmd == 'class':
        cmd_class_stream(query)
    elif cmd == 'api':
        cmd_api_stream(query)
    else:
        print(f"未知命令: {cmd}")
        print("支持的命令: class, api")

if __name__ == "__main__":
    main()
