#!/usr/bin/env python3
"""
Dependency Query Script - 依赖快速查询工具

从 .claude/.meta/dependencies.pkg.json 查询依赖信息。
支持：pkg 详情、漏洞、过期依赖、依赖树、使用位置、统计等。
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional


def get_deps_file_path() -> Path:
    """获取依赖索引文件路径"""
    target_dir = os.environ.get('DEPS_TARGET_DIR', os.getcwd())
    return Path(target_dir) / '.claude' / 'deps' / '.meta' / 'dependencies.pkg.json'


def load_deps_data() -> Optional[Dict[str, Any]]:
    """加载依赖数据"""
    deps_file = get_deps_file_path()

    if not deps_file.exists():
        print(f'❌ 依赖索引不存在: {deps_file}')
        print('   请先运行: /atlas:deps')
        return None

    try:
        with open(deps_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f'❌ JSON 解析失败: {e}')
        return None
    except Exception as e:
        print(f'❌ 读取文件失败: {e}')
        return None


def query_package(data: Dict[str, Any], pkg_name: str):
    """查询依赖包详情"""
    deps = data.get('dependencies', [])
    pkg_name_lower = pkg_name.lower()

    # 模糊匹配
    matches = [d for d in deps if pkg_name_lower in d.get('name', '').lower()]

    if not matches:
        print(f'未找到包含 "{pkg_name}" 的依赖')
        print(f'\n项目依赖 ({len(deps)} 个):')
        for d in deps[:15]:
            print(f'  - {d.get("name", "-")} @ {d.get("version", "-")}')
        if len(deps) > 15:
            print(f'  ... 还有 {len(deps) - 15} 个依赖')
    elif len(matches) == 1:
        d = matches[0]
        print(f'📦 依赖: {d.get("name", "-")}')
        print(f'   版本: {d.get("version", "-")}')
        print(f'   类型: {d.get("type", "-")}')

        if d.get('latest'):
            is_outdated = d['version'] != d['latest']
            status = '⚠️  过期' if is_outdated else '✅ 最新'
            print(f'   最新: {d["latest"]} {status}')

        if d.get('description'):
            print(f'   描述: {d["description"]}')

        if d.get('license'):
            print(f'   许可: {d["license"]}')

        if d.get('homepage'):
            print(f'   主页: {d["homepage"]}')

        # 漏洞信息
        vulns = d.get('vulnerabilities', [])
        if vulns:
            print(f'\n⚠️  漏洞 ({len(vulns)} 个):')
            for v in vulns:
                severity = v.get('severity', 'unknown').upper()
                icon = {'CRITICAL':'🔴','HIGH':'🟠','MODERATE':'🟡','LOW':'🟢'}.get(severity,'⚪')
                print(f'   {icon} [{severity}] {v.get("title", "-")}')
                if v.get('cve'):
                    print(f'      CVE: {v["cve"]}')
        else:
            print('\n✅ 无已知漏洞')
    else:
        print(f'找到 {len(matches)} 个匹配依赖:')
        for d in matches:
            vuln_count = len(d.get('vulnerabilities', []))
            vuln_mark = f' ⚠️  {vuln_count} vulns' if vuln_count > 0 else ''
            outdated = '⚠️ ' if d.get('latest') and d['version'] != d['latest'] else ''
            print(f'  - {outdated}{d.get("name", "-")} @ {d.get("version", "-")}{vuln_mark}')


def query_vulnerabilities(data: Dict[str, Any], severity_filter: Optional[str] = None):
    """查询漏洞列表"""
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
                'cve': v.get('cve', '-'),
                'url': v.get('url', '-')
            })

    # 过滤严重性
    if severity_filter:
        all_vulns = [v for v in all_vulns if v['severity'].lower() == severity_filter.lower()]

    if not all_vulns:
        msg = f' ({severity_filter})' if severity_filter else ''
        print(f'✅ 未发现漏洞{msg}')
        return

    # 按严重性排序
    severity_order = {'critical': 0, 'high': 1, 'moderate': 2, 'low': 3, 'unknown': 4}
    all_vulns.sort(key=lambda x: severity_order.get(x['severity'].lower(), 5))

    print(f'⚠️  发现 {len(all_vulns)} 个漏洞:')
    for v in all_vulns:
        icon = {'critical':'🔴','high':'🟠','moderate':'🟡','low':'🟢'}.get(v['severity'].lower(),'⚪')
        print(f'\n{icon} [{v["severity"].upper()}] {v["title"]}')
        print(f'   包: {v["package"]}@{v["version"]}')
        if v['cve'] != '-':
            print(f'   CVE: {v["cve"]}')
        if v['url'] != '-':
            print(f'   详情: {v["url"]}')


def query_outdated(data: Dict[str, Any]):
    """查询过期依赖"""
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
        print('✅ 所有依赖都是最新版本！')
        return

    print(f'⚠️  发现 {len(outdated)} 个过期依赖:')
    for d in outdated:
        type_mark = '📦' if d['type'] == 'dependencies' else '🛠️ '
        print(f'\n{type_mark} {d["name"]}')
        print(f'   当前: {d["current"]}')
        print(f'   最新: {d["latest"]}')


def query_tree(data: Dict[str, Any], pkg_name: str):
    """查询依赖树"""
    tree = data.get('dependency_tree', {})

    if not tree:
        print('⚠️  依赖树数据不可用，请重新运行 /atlas:deps')
        return

    pkg_name_lower = pkg_name.lower()
    matches = {k: v for k, v in tree.items() if pkg_name_lower in k.lower()}

    if not matches:
        print(f'未找到 "{pkg_name}" 的依赖树')
        print(f'\n可用的包 ({len(tree)} 个):')
        for pkg in list(tree.keys())[:15]:
            print(f'  - {pkg}')
        return

    for pkg, children in matches.items():
        print(f'📦 {pkg}')
        if children:
            for i, child in enumerate(children):
                is_last = i == len(children) - 1
                prefix = '└── ' if is_last else '├── '
                print(f'{prefix}{child}')
        else:
            print('  └── (无依赖)')


def query_usage(data: Dict[str, Any], pkg_name: str):
    """查询使用位置"""
    usage = data.get('usage_locations', {})

    if not usage:
        print('⚠️  使用位置数据不可用，请重新运行 /atlas:deps')
        return

    pkg_name_lower = pkg_name.lower()
    matches = {k: v for k, v in usage.items() if pkg_name_lower in k.lower()}

    if not matches:
        print(f'未找到 "{pkg_name}" 的使用位置')
        return

    for pkg, locations in matches.items():
        print(f'📦 {pkg} 使用于:')
        if locations:
            for i, loc in enumerate(locations[:30], 1):
                print(f'  {i:2}. 📄 {loc}')
            if len(locations) > 30:
                print(f'  ... 还有 {len(locations) - 30} 个位置')
        else:
            print('  (未检测到直接引用)')


def query_stats(data: Dict[str, Any]):
    """统计概览"""
    deps = data.get('dependencies', [])
    prod_deps = [d for d in deps if d.get('type') == 'dependencies']
    dev_deps = [d for d in deps if d.get('type') == 'devDependencies']

    # 统计漏洞
    vuln_count = sum(len(d.get('vulnerabilities', [])) for d in deps)
    critical = sum(1 for d in deps for v in d.get('vulnerabilities', []) if v.get('severity') == 'critical')
    high = sum(1 for d in deps for v in d.get('vulnerabilities', []) if v.get('severity') == 'high')
    moderate = sum(1 for d in deps for v in d.get('vulnerabilities', []) if v.get('severity') == 'moderate')
    low = sum(1 for d in deps for v in d.get('vulnerabilities', []) if v.get('severity') == 'low')

    # 统计过期
    outdated = sum(1 for d in deps if d.get('latest') and d.get('version') != d.get('latest'))

    print('=== 依赖统计 ===\n')
    print(f'📦 生产依赖: {len(prod_deps)} 个')
    print(f'🛠️  开发依赖: {len(dev_deps)} 个')
    print(f'📊 总计: {len(deps)} 个')

    print(f'\n⚠️  过期依赖: {outdated} 个')

    print(f'\n🔒 安全漏洞: {vuln_count} 个')
    if critical > 0:
        print(f'   🔴 严重 (Critical): {critical}')
    if high > 0:
        print(f'   🟠 高危 (High): {high}')
    if moderate > 0:
        print(f'   🟡 中危 (Moderate): {moderate}')
    if low > 0:
        print(f'   🟢 低危 (Low): {low}')

    # 最大的依赖包（如果有大小信息）
    deps_with_size = [d for d in deps if d.get('size')]
    if deps_with_size:
        largest = sorted(deps_with_size, key=lambda x: x.get('size', 0), reverse=True)[:5]
        print(f'\n💾 最大的依赖:')
        for d in largest:
            size_mb = d.get('size', 0) / 1024 / 1024
            print(f'   {d.get("name", "-")}: {size_mb:.2f} MB')


def print_usage():
    """打印使用说明"""
    print("""
依赖查询工具 (Dependency Query)

用法:
  python query_deps.py <命令> [参数]

命令:
  pkg <name>         查询依赖包详情（支持模糊匹配）
  vuln [severity]    列出漏洞（可选：critical/high/moderate/low）
  outdated           列出过期依赖
  tree <name>        显示依赖树
  usage <name>       显示使用位置
  stats              统计概览

环境变量:
  DEPS_TARGET_DIR    目标项目目录（默认：当前目录）

示例:
  python query_deps.py pkg lodash
  python query_deps.py vuln critical
  python query_deps.py outdated
  python query_deps.py tree react
  python query_deps.py usage axios
  python query_deps.py stats
""")


def main():
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    command = sys.argv[1].lower()

    # 加载数据
    data = load_deps_data()
    if data is None:
        sys.exit(1)

    # 执行查询
    if command == 'pkg':
        if len(sys.argv) < 3:
            print('❌ 请提供包名')
            print('   用法: python query_deps.py pkg <name>')
            sys.exit(1)
        query_package(data, sys.argv[2])

    elif command == 'vuln':
        severity = sys.argv[2] if len(sys.argv) > 2 else None
        query_vulnerabilities(data, severity)

    elif command == 'outdated':
        query_outdated(data)

    elif command == 'tree':
        if len(sys.argv) < 3:
            print('❌ 请提供包名')
            print('   用法: python query_deps.py tree <name>')
            sys.exit(1)
        query_tree(data, sys.argv[2])

    elif command == 'usage':
        if len(sys.argv) < 3:
            print('❌ 请提供包名')
            print('   用法: python query_deps.py usage <name>')
            sys.exit(1)
        query_usage(data, sys.argv[2])

    elif command == 'stats':
        query_stats(data)

    else:
        print(f'❌ 未知命令: {command}')
        print_usage()
        sys.exit(1)


if __name__ == '__main__':
    main()
