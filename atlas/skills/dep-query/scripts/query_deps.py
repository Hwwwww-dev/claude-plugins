#!/usr/bin/env python3
"""
Dependency Query Script - 依赖快速查询工具

Reads .claude/deps/.meta/dependencies.pkg.json and answers lookup questions:
  package details, vulnerabilities, outdated deps, trees, usage locations, stats.

Language:
    --lang zh|en   (default: inferred from $ATLAS_LANG / $LC_ALL / $LANG)
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# i18n
# ---------------------------------------------------------------------------

I18N: Dict[str, Dict[str, str]] = {
    # --- load ---
    "idx_missing":           {"zh": "❌ 依赖索引不存在: {path}",
                              "en": "❌ Dependency index not found: {path}"},
    "idx_run_deps":          {"zh": "   请先运行: /atlas:deps",
                              "en": "   Please run /atlas:deps first"},
    "json_parse_failed":     {"zh": "❌ JSON 解析失败: {err}",
                              "en": "❌ JSON parse failed: {err}"},
    "read_failed":           {"zh": "❌ 读取文件失败: {err}",
                              "en": "❌ Failed to read file: {err}"},

    # --- query_package ---
    "pkg_none":              {"zh": '未找到包含 "{name}" 的依赖',
                              "en": 'No dependency matching "{name}" found'},
    "pkg_project_header":    {"zh": "\n项目依赖 ({n} 个):",
                              "en": "\nProject dependencies ({n} total):"},
    "pkg_more":              {"zh": "  ... 还有 {n} 个依赖",
                              "en": "  ... and {n} more dependencies"},
    "pkg_label":             {"zh": "📦 依赖: {name}",
                              "en": "📦 Package: {name}"},
    "pkg_version":           {"zh": "   版本: {ver}",
                              "en": "   Version: {ver}"},
    "pkg_type":              {"zh": "   类型: {type}",
                              "en": "   Type: {type}"},
    "pkg_latest":            {"zh": "   最新: {latest} {status}",
                              "en": "   Latest: {latest} {status}"},
    "pkg_outdated_tag":      {"zh": "⚠️  过期",
                              "en": "⚠️  outdated"},
    "pkg_uptodate_tag":      {"zh": "✅ 最新",
                              "en": "✅ up to date"},
    "pkg_description":       {"zh": "   描述: {desc}",
                              "en": "   Description: {desc}"},
    "pkg_license":           {"zh": "   许可: {license}",
                              "en": "   License: {license}"},
    "pkg_homepage":          {"zh": "   主页: {url}",
                              "en": "   Homepage: {url}"},
    "pkg_vulns_header":      {"zh": "\n⚠️  漏洞 ({n} 个):",
                              "en": "\n⚠️  Vulnerabilities ({n}):"},
    "pkg_vuln_cve":          {"zh": "      CVE: {cve}",
                              "en": "      CVE: {cve}"},
    "pkg_no_vulns":          {"zh": "\n✅ 无已知漏洞",
                              "en": "\n✅ No known vulnerabilities"},
    "pkg_multi_header":      {"zh": "找到 {n} 个匹配依赖:",
                              "en": "Found {n} matching dependencies:"},
    "pkg_vuln_count":        {"zh": " ⚠️  {n} 个漏洞",
                              "en": " ⚠️  {n} vulns"},

    # --- query_vulnerabilities ---
    "vuln_none":             {"zh": "✅ 未发现漏洞{suffix}",
                              "en": "✅ No vulnerabilities found{suffix}"},
    "vuln_header":           {"zh": "⚠️  发现 {n} 个漏洞:",
                              "en": "⚠️  Found {n} vulnerabilities:"},
    "vuln_package":          {"zh": "   包: {pkg}@{ver}",
                              "en": "   Package: {pkg}@{ver}"},
    "vuln_cve":              {"zh": "   CVE: {cve}",
                              "en": "   CVE: {cve}"},
    "vuln_url":              {"zh": "   详情: {url}",
                              "en": "   Details: {url}"},

    # --- query_outdated ---
    "outdated_none":         {"zh": "✅ 所有依赖都是最新版本！",
                              "en": "✅ All dependencies are up to date!"},
    "outdated_header":       {"zh": "⚠️  发现 {n} 个过期依赖:",
                              "en": "⚠️  Found {n} outdated dependencies:"},
    "outdated_current":      {"zh": "   当前: {ver}",
                              "en": "   Current: {ver}"},
    "outdated_latest":       {"zh": "   最新: {ver}",
                              "en": "   Latest:  {ver}"},

    # --- query_tree ---
    "tree_missing_data":     {"zh": "⚠️  依赖树数据不可用，请重新运行 /atlas:deps",
                              "en": "⚠️  Dependency tree data unavailable, please re-run /atlas:deps"},
    "tree_none":             {"zh": '未找到 "{name}" 的依赖树',
                              "en": 'No dependency tree found for "{name}"'},
    "tree_available":        {"zh": "\n可用的包 ({n} 个):",
                              "en": "\nAvailable packages ({n}):"},
    "tree_empty":            {"zh": "  └── (无依赖)",
                              "en": "  └── (no dependencies)"},

    # --- query_usage ---
    "usage_missing_data":    {"zh": "⚠️  使用位置数据不可用，请重新运行 /atlas:deps",
                              "en": "⚠️  Usage location data unavailable, please re-run /atlas:deps"},
    "usage_none":            {"zh": '未找到 "{name}" 的使用位置',
                              "en": 'No usage locations found for "{name}"'},
    "usage_header":          {"zh": "📦 {pkg} 使用于:",
                              "en": "📦 {pkg} used in:"},
    "usage_more":            {"zh": "  ... 还有 {n} 个位置",
                              "en": "  ... and {n} more locations"},
    "usage_no_refs":         {"zh": "  (未检测到直接引用)",
                              "en": "  (no direct references detected)"},

    # --- query_stats ---
    "stats_title":           {"zh": "=== 依赖统计 ===\n",
                              "en": "=== Dependency Statistics ===\n"},
    "stats_prod":            {"zh": "📦 生产依赖: {n} 个",
                              "en": "📦 Production deps: {n}"},
    "stats_dev":             {"zh": "🛠️  开发依赖: {n} 个",
                              "en": "🛠️  Dev deps: {n}"},
    "stats_total":           {"zh": "📊 总计: {n} 个",
                              "en": "📊 Total: {n}"},
    "stats_outdated":        {"zh": "\n⚠️  过期依赖: {n} 个",
                              "en": "\n⚠️  Outdated: {n}"},
    "stats_vuln_total":      {"zh": "\n🔒 安全漏洞: {n} 个",
                              "en": "\n🔒 Security vulnerabilities: {n}"},
    "stats_critical":        {"zh": "   🔴 严重 (Critical): {n}",
                              "en": "   🔴 Critical: {n}"},
    "stats_high":            {"zh": "   🟠 高危 (High): {n}",
                              "en": "   🟠 High: {n}"},
    "stats_moderate":        {"zh": "   🟡 中危 (Moderate): {n}",
                              "en": "   🟡 Moderate: {n}"},
    "stats_low":             {"zh": "   🟢 低危 (Low): {n}",
                              "en": "   🟢 Low: {n}"},
    "stats_largest":         {"zh": "\n💾 最大的依赖:",
                              "en": "\n💾 Largest dependencies:"},

    # --- usage / main ---
    "usage_title":           {"zh": "依赖查询工具 (Dependency Query)",
                              "en": "Dependency Query Tool"},
    "usage_usage_label":     {"zh": "用法:",
                              "en": "Usage:"},
    "usage_usage_line":      {"zh": "  python query_deps.py [--lang zh|en] <命令> [参数]",
                              "en": "  python query_deps.py [--lang zh|en] <command> [args]"},
    "usage_cmds_label":      {"zh": "命令:",
                              "en": "Commands:"},
    "usage_cmd_pkg":         {"zh": "  pkg <name>         查询依赖包详情（支持模糊匹配）",
                              "en": "  pkg <name>         Query package details (fuzzy match)"},
    "usage_cmd_vuln":        {"zh": "  vuln [severity]    列出漏洞（可选：critical/high/moderate/low）",
                              "en": "  vuln [severity]    List vulnerabilities (critical/high/moderate/low)"},
    "usage_cmd_outdated":    {"zh": "  outdated           列出过期依赖",
                              "en": "  outdated           List outdated dependencies"},
    "usage_cmd_tree":        {"zh": "  tree <name>        显示依赖树",
                              "en": "  tree <name>        Show dependency tree"},
    "usage_cmd_usage":       {"zh": "  usage <name>       显示使用位置",
                              "en": "  usage <name>       Show usage locations"},
    "usage_cmd_stats":       {"zh": "  stats              统计概览",
                              "en": "  stats              Statistics overview"},
    "usage_env_label":       {"zh": "环境变量:",
                              "en": "Environment variables:"},
    "usage_env_target":      {"zh": "  DEPS_TARGET_DIR    目标项目目录（默认：当前目录）",
                              "en": "  DEPS_TARGET_DIR    Target project directory (default: cwd)"},
    "usage_env_lang":        {"zh": "  ATLAS_LANG/LANG    默认输出语言",
                              "en": "  ATLAS_LANG/LANG    Default output language"},
    "usage_examples_label":  {"zh": "示例:",
                              "en": "Examples:"},

    "need_pkg_name":         {"zh": "❌ 请提供包名",
                              "en": "❌ Please provide a package name"},
    "usage_pkg_hint":        {"zh": "   用法: python query_deps.py pkg <name>",
                              "en": "   Usage: python query_deps.py pkg <name>"},
    "usage_tree_hint":       {"zh": "   用法: python query_deps.py tree <name>",
                              "en": "   Usage: python query_deps.py tree <name>"},
    "usage_usage_hint":      {"zh": "   用法: python query_deps.py usage <name>",
                              "en": "   Usage: python query_deps.py usage <name>"},
    "unknown_command":       {"zh": "❌ 未知命令: {cmd}",
                              "en": "❌ Unknown command: {cmd}"},
}

_LANG = "en"


def detect_lang(default: Optional[str] = None) -> str:
    if default:
        return "zh" if default.lower().startswith("zh") else "en"
    for var in ("ATLAS_LANG", "LC_ALL", "LANG"):
        val = os.environ.get(var, "")
        if val:
            return "zh" if val.lower().startswith("zh") else "en"
    return "en"


def t(key: str, **kwargs) -> str:
    entry = I18N.get(key)
    if not entry:
        return key
    text = entry.get(_LANG) or entry.get("en") or key
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text


# ---------------------------------------------------------------------------
# Data access
# ---------------------------------------------------------------------------

def get_deps_file_path() -> Path:
    """Return the dependency index path."""
    target_dir = os.environ.get('DEPS_TARGET_DIR', os.getcwd())
    return Path(target_dir) / '.claude' / 'deps' / '.meta' / 'dependencies.pkg.json'


def load_deps_data() -> Optional[Dict[str, Any]]:
    deps_file = get_deps_file_path()

    if not deps_file.exists():
        print(t("idx_missing", path=deps_file))
        print(t("idx_run_deps"))
        return None

    try:
        with open(deps_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(t("json_parse_failed", err=e))
        return None
    except Exception as e:
        print(t("read_failed", err=e))
        return None


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------

def query_package(data: Dict[str, Any], pkg_name: str):
    deps = data.get('dependencies', [])
    pkg_name_lower = pkg_name.lower()

    matches = [d for d in deps if pkg_name_lower in d.get('name', '').lower()]

    if not matches:
        print(t("pkg_none", name=pkg_name))
        print(t("pkg_project_header", n=len(deps)))
        for d in deps[:15]:
            print(f'  - {d.get("name", "-")} @ {d.get("version", "-")}')
        if len(deps) > 15:
            print(t("pkg_more", n=len(deps) - 15))
    elif len(matches) == 1:
        d = matches[0]
        print(t("pkg_label", name=d.get("name", "-")))
        print(t("pkg_version", ver=d.get("version", "-")))
        print(t("pkg_type", type=d.get("type", "-")))

        if d.get('latest'):
            is_outdated = d['version'] != d['latest']
            status = t("pkg_outdated_tag") if is_outdated else t("pkg_uptodate_tag")
            print(t("pkg_latest", latest=d["latest"], status=status))

        if d.get('description'):
            print(t("pkg_description", desc=d["description"]))

        if d.get('license'):
            print(t("pkg_license", license=d["license"]))

        if d.get('homepage'):
            print(t("pkg_homepage", url=d["homepage"]))

        vulns = d.get('vulnerabilities', [])
        if vulns:
            print(t("pkg_vulns_header", n=len(vulns)))
            for v in vulns:
                severity = v.get('severity', 'unknown').upper()
                icon = {'CRITICAL': '🔴', 'HIGH': '🟠', 'MODERATE': '🟡', 'LOW': '🟢'}.get(severity, '⚪')
                print(f'   {icon} [{severity}] {v.get("title", "-")}')
                if v.get('cve'):
                    print(t("pkg_vuln_cve", cve=v["cve"]))
        else:
            print(t("pkg_no_vulns"))
    else:
        print(t("pkg_multi_header", n=len(matches)))
        for d in matches:
            vuln_count = len(d.get('vulnerabilities', []))
            vuln_mark = t("pkg_vuln_count", n=vuln_count) if vuln_count > 0 else ''
            outdated = '⚠️ ' if d.get('latest') and d['version'] != d['latest'] else ''
            print(f'  - {outdated}{d.get("name", "-")} @ {d.get("version", "-")}{vuln_mark}')


def query_vulnerabilities(data: Dict[str, Any], severity_filter: Optional[str] = None):
    deps = data.get('dependencies', [])

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

    if severity_filter:
        all_vulns = [v for v in all_vulns if v['severity'].lower() == severity_filter.lower()]

    if not all_vulns:
        suffix = f' ({severity_filter})' if severity_filter else ''
        print(t("vuln_none", suffix=suffix))
        return

    severity_order = {'critical': 0, 'high': 1, 'moderate': 2, 'low': 3, 'unknown': 4}
    all_vulns.sort(key=lambda x: severity_order.get(x['severity'].lower(), 5))

    print(t("vuln_header", n=len(all_vulns)))
    for v in all_vulns:
        icon = {'critical': '🔴', 'high': '🟠', 'moderate': '🟡', 'low': '🟢'}.get(v['severity'].lower(), '⚪')
        print(f'\n{icon} [{v["severity"].upper()}] {v["title"]}')
        print(t("vuln_package", pkg=v["package"], ver=v["version"]))
        if v['cve'] != '-':
            print(t("vuln_cve", cve=v["cve"]))
        if v['url'] != '-':
            print(t("vuln_url", url=v["url"]))


def query_outdated(data: Dict[str, Any]):
    deps = data.get('dependencies', [])

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
        print(t("outdated_none"))
        return

    print(t("outdated_header", n=len(outdated)))
    for d in outdated:
        type_mark = '📦' if d['type'] == 'dependencies' else '🛠️ '
        print(f'\n{type_mark} {d["name"]}')
        print(t("outdated_current", ver=d["current"]))
        print(t("outdated_latest", ver=d["latest"]))


def query_tree(data: Dict[str, Any], pkg_name: str):
    tree = data.get('dependency_tree', {})

    if not tree:
        print(t("tree_missing_data"))
        return

    pkg_name_lower = pkg_name.lower()
    matches = {k: v for k, v in tree.items() if pkg_name_lower in k.lower()}

    if not matches:
        print(t("tree_none", name=pkg_name))
        print(t("tree_available", n=len(tree)))
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
            print(t("tree_empty"))


def query_usage(data: Dict[str, Any], pkg_name: str):
    usage = data.get('usage_locations', {})

    if not usage:
        print(t("usage_missing_data"))
        return

    pkg_name_lower = pkg_name.lower()
    matches = {k: v for k, v in usage.items() if pkg_name_lower in k.lower()}

    if not matches:
        print(t("usage_none", name=pkg_name))
        return

    for pkg, locations in matches.items():
        print(t("usage_header", pkg=pkg))
        if locations:
            for i, loc in enumerate(locations[:30], 1):
                print(f'  {i:2}. 📄 {loc}')
            if len(locations) > 30:
                print(t("usage_more", n=len(locations) - 30))
        else:
            print(t("usage_no_refs"))


def query_stats(data: Dict[str, Any]):
    deps = data.get('dependencies', [])
    prod_deps = [d for d in deps if d.get('type') == 'dependencies']
    dev_deps = [d for d in deps if d.get('type') == 'devDependencies']

    vuln_count = sum(len(d.get('vulnerabilities', [])) for d in deps)
    critical = sum(1 for d in deps for v in d.get('vulnerabilities', []) if v.get('severity') == 'critical')
    high = sum(1 for d in deps for v in d.get('vulnerabilities', []) if v.get('severity') == 'high')
    moderate = sum(1 for d in deps for v in d.get('vulnerabilities', []) if v.get('severity') == 'moderate')
    low = sum(1 for d in deps for v in d.get('vulnerabilities', []) if v.get('severity') == 'low')

    outdated = sum(1 for d in deps if d.get('latest') and d.get('version') != d.get('latest'))

    print(t("stats_title"))
    print(t("stats_prod", n=len(prod_deps)))
    print(t("stats_dev", n=len(dev_deps)))
    print(t("stats_total", n=len(deps)))

    print(t("stats_outdated", n=outdated))

    print(t("stats_vuln_total", n=vuln_count))
    if critical > 0:
        print(t("stats_critical", n=critical))
    if high > 0:
        print(t("stats_high", n=high))
    if moderate > 0:
        print(t("stats_moderate", n=moderate))
    if low > 0:
        print(t("stats_low", n=low))

    deps_with_size = [d for d in deps if d.get('size')]
    if deps_with_size:
        largest = sorted(deps_with_size, key=lambda x: x.get('size', 0), reverse=True)[:5]
        print(t("stats_largest"))
        for d in largest:
            size_mb = d.get('size', 0) / 1024 / 1024
            print(f'   {d.get("name", "-")}: {size_mb:.2f} MB')


def print_usage():
    lines = [
        "",
        t("usage_title"),
        "",
        t("usage_usage_label"),
        t("usage_usage_line"),
        "",
        t("usage_cmds_label"),
        t("usage_cmd_pkg"),
        t("usage_cmd_vuln"),
        t("usage_cmd_outdated"),
        t("usage_cmd_tree"),
        t("usage_cmd_usage"),
        t("usage_cmd_stats"),
        "",
        t("usage_env_label"),
        t("usage_env_target"),
        t("usage_env_lang"),
        "",
        t("usage_examples_label"),
        "  python query_deps.py pkg lodash",
        "  python query_deps.py vuln critical",
        "  python query_deps.py outdated",
        "  python query_deps.py tree react",
        "  python query_deps.py usage axios",
        "  python query_deps.py stats",
        "  python query_deps.py --lang en stats",
        "",
    ]
    print("\n".join(lines))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _parse_lang_arg(argv: List[str]):
    """Strip --lang/--lang=XX from argv; return (lang, remaining argv)."""
    lang = None
    remaining: List[str] = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--lang" and i + 1 < len(argv):
            lang = argv[i + 1]
            i += 2
            continue
        if a.startswith("--lang="):
            lang = a.split("=", 1)[1]
            i += 1
            continue
        remaining.append(a)
        i += 1
    return (lang or detect_lang()), remaining


def main():
    global _LANG
    lang, rest = _parse_lang_arg(sys.argv[1:])
    _LANG = "zh" if lang.lower().startswith("zh") else "en"

    if not rest:
        print_usage()
        sys.exit(1)

    command = rest[0].lower()

    data = load_deps_data()
    if data is None:
        sys.exit(1)

    if command == 'pkg':
        if len(rest) < 2:
            print(t("need_pkg_name"))
            print(t("usage_pkg_hint"))
            sys.exit(1)
        query_package(data, rest[1])

    elif command == 'vuln':
        severity = rest[1] if len(rest) > 1 else None
        query_vulnerabilities(data, severity)

    elif command == 'outdated':
        query_outdated(data)

    elif command == 'tree':
        if len(rest) < 2:
            print(t("need_pkg_name"))
            print(t("usage_tree_hint"))
            sys.exit(1)
        query_tree(data, rest[1])

    elif command == 'usage':
        if len(rest) < 2:
            print(t("need_pkg_name"))
            print(t("usage_usage_hint"))
            sys.exit(1)
        query_usage(data, rest[1])

    elif command == 'stats':
        query_stats(data)

    else:
        print(t("unknown_command", cmd=command))
        print_usage()
        sys.exit(1)


if __name__ == '__main__':
    main()
