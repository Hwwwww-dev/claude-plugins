#!/usr/bin/env python3
"""
Git Query Script - Git information lookup tool / Git 信息快速查询工具

Usage / 用法:
    python query.py [--lang zh|en] <command> [args]

Commands:
    search <keyword>    # Search commit messages
    author <name>       # Query author commits
    file <path>         # File history
    stats               # Contributor stats
    recent [n]          # Recent commits
    changes [ref]       # Change stats
    branches            # Branch status
    tags [pattern]      # Tag list
    hotfiles            # Hot files

Language:
    Pass --lang zh or --lang en. Default: inferred from $LANG / $LC_ALL
    (zh* -> zh, otherwise en). Also honors $ATLAS_LANG.
"""

import os
import subprocess
import sys
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# i18n
# ---------------------------------------------------------------------------

I18N: Dict[str, Dict[str, str]] = {
    # --- run_git_command ---
    "git_cmd_failed":       {"zh": "❌ Git 命令执行失败: {err}",
                             "en": "❌ Git command failed: {err}"},
    "git_not_found":        {"zh": "❌ 未找到 Git，或 Git 不在 PATH 中",
                             "en": "❌ Git not installed or not in PATH"},

    # --- search_commits ---
    "search_header":        {"zh": '🔍 搜索提交信息: "{kw}"\n',
                             "en": '🔍 Searching commits for: "{kw}"\n'},
    "search_table_head":    {"zh": "提交哈希 | 日期       | 作者     | 提交信息",
                             "en": "Commit   | Date       | Author   | Message"},
    "search_found":         {"zh": "\n✅ 找到 {n} 条匹配记录（最多显示 {limit} 条）",
                             "en": "\n✅ Found {n} matching commits (showing up to {limit})"},
    "search_none":          {"zh": '❌ 未找到包含 "{kw}" 的提交',
                             "en": '❌ No commits found matching "{kw}"'},

    # --- query_author ---
    "author_header":        {"zh": '👤 查询作者: "{name}"\n',
                             "en": '👤 Commits by author: "{name}"\n'},
    "author_table_head":    {"zh": "提交哈希 | 日期       | 提交信息",
                             "en": "Commit   | Date       | Message"},
    "author_found":         {"zh": "\n✅ 找到 {n} 条提交（最多显示 {limit} 条）",
                             "en": "\n✅ Found {n} commits (showing up to {limit})"},
    "author_none":          {"zh": '❌ 未找到作者 "{name}" 的提交',
                             "en": '❌ No commits found for author "{name}"'},

    # --- file_history ---
    "file_header":          {"zh": '📄 文件历史: {path}\n',
                             "en": '📄 File history: {path}\n'},
    "file_found":           {"zh": "\n✅ 找到 {n} 条变更记录（最多显示 {limit} 条）",
                             "en": "\n✅ Found {n} change records (showing up to {limit})"},
    "file_none":            {"zh": '❌ 文件 "{path}" 无历史记录或不存在',
                             "en": '❌ File "{path}" has no history or does not exist'},

    # --- contributor_stats ---
    "stats_header":         {"zh": "📊 贡献者统计\n",
                             "en": "📊 Contributor stats\n"},
    "stats_table_head":     {"zh": "提交数 | 作者",
                             "en": "Commits | Author"},
    "stats_found":          {"zh": "\n✅ 共 {n} 位贡献者（显示前 {limit} 名）",
                             "en": "\n✅ {n} contributors total (showing top {limit})"},
    "stats_none":           {"zh": "❌ 无法获取贡献者统计",
                             "en": "❌ Unable to get contributor stats"},

    # --- recent_commits ---
    "recent_header":        {"zh": "🕐 最近 {count} 次提交\n",
                             "en": "🕐 Last {count} commits\n"},
    "recent_found":         {"zh": "\n✅ 显示最近 {n} 次提交",
                             "en": "\n✅ Showing last {n} commits"},
    "recent_none":          {"zh": "❌ 无法获取提交记录",
                             "en": "❌ Unable to get commit history"},

    # --- change_stats ---
    "changes_header":       {"zh": "📈 变更统计: {ref}\n",
                             "en": "📈 Change stats: {ref}\n"},
    "changes_done":         {"zh": "\n✅ 变更统计完成",
                             "en": "\n✅ Change stats complete"},
    "changes_none":         {"zh": '❌ 无法获取 "{ref}" 的变更统计',
                             "en": '❌ Unable to get change stats for "{ref}"'},

    # --- branch_status ---
    "branches_header":      {"zh": "🌿 分支状态\n",
                             "en": "🌿 Branch status\n"},
    "branches_found":       {"zh": "\n✅ 共 {n} 个本地分支",
                             "en": "\n✅ {n} local branches"},
    "branches_none":        {"zh": "❌ 无法获取分支状态",
                             "en": "❌ Unable to get branch status"},

    # --- list_tags ---
    "tags_header":          {"zh": "🏷️  标签列表: {pattern}\n",
                             "en": "🏷️  Tags: {pattern}\n"},
    "tags_found":           {"zh": "\n✅ 共 {n} 个标签",
                             "en": "\n✅ {n} tags"},
    "tags_none":            {"zh": "ℹ️  仓库中没有标签",
                             "en": "ℹ️  No tags in repository"},

    # --- hot_files ---
    "hot_header":           {"zh": "🔥 热点文件（最近 {since}）\n",
                             "en": "🔥 Hot files (since {since})\n"},
    "hot_table_head":       {"zh": "修改次数 | 文件路径",
                             "en": "Changes  | File path"},
    "hot_found":            {"zh": "\n✅ 共 {n} 个文件被修改（显示前 {limit} 个）",
                             "en": "\n✅ {n} files modified (showing top {limit})"},
    "hot_none":             {"zh": "❌ 无法获取文件变更记录",
                             "en": "❌ Unable to get file change history"},

    # --- help ---
    "help_title":           {"zh": "Git Query - Git 信息快速查询工具",
                             "en": "Git Query - Git information lookup tool"},
    "help_usage_label":     {"zh": "用法:",
                             "en": "Usage:"},
    "help_usage_line":      {"zh": "    python query.py [--lang zh|en] <命令> [参数]",
                             "en": "    python query.py [--lang zh|en] <command> [args]"},
    "help_cmds_label":      {"zh": "命令:",
                             "en": "Commands:"},
    "help_cmd_search":      {"zh": "    search <keyword>        搜索提交信息（支持模糊匹配）",
                             "en": "    search <keyword>        Search commit messages (fuzzy)"},
    "help_cmd_author":      {"zh": "    author <name>           查询作者的提交记录",
                             "en": "    author <name>           Query commits by author"},
    "help_cmd_file":        {"zh": "    file <path>             查询文件的变更历史",
                             "en": "    file <path>             Query file change history"},
    "help_cmd_stats":       {"zh": "    stats                   显示贡献者统计",
                             "en": "    stats                   Show contributor statistics"},
    "help_cmd_recent":      {"zh": "    recent [n]              显示最近 n 次提交（默认 10）",
                             "en": "    recent [n]              Show last n commits (default 10)"},
    "help_cmd_changes":     {"zh": "    changes [ref]           显示变更统计（默认 HEAD~10..HEAD）",
                             "en": "    changes [ref]           Show change stats (default HEAD~10..HEAD)"},
    "help_cmd_branches":    {"zh": "    branches                显示分支状态",
                             "en": "    branches                Show branch status"},
    "help_cmd_tags":        {"zh": "    tags [pattern]          列出标签（可选 glob 模式）",
                             "en": "    tags [pattern]          List tags (optional glob pattern)"},
    "help_cmd_hotfiles":    {"zh": "    hotfiles                显示热点文件（最常修改）",
                             "en": "    hotfiles                Show hot files (most modified)"},
    "help_cmd_help":        {"zh": "    help                    显示此帮助信息",
                             "en": "    help                    Show this help message"},
    "help_examples_label":  {"zh": "示例:",
                             "en": "Examples:"},
    "help_lang_note":       {"zh": "语言:\n    使用 --lang zh 或 --lang en 切换输出语言。\n    默认根据 $LANG / $LC_ALL / $ATLAS_LANG 推断。",
                             "en": "Language:\n    Use --lang zh or --lang en to switch output language.\n    Default is inferred from $LANG / $LC_ALL / $ATLAS_LANG."},

    # --- main ---
    "not_git_repo":         {"zh": "❌ 错误: 当前目录不是 Git 仓库",
                             "en": "❌ Error: current directory is not a Git repository"},
    "need_keyword":         {"zh": "❌ 错误: 请提供搜索关键词",
                             "en": "❌ Error: please provide a search keyword"},
    "need_author":          {"zh": "❌ 错误: 请提供作者名称",
                             "en": "❌ Error: please provide an author name"},
    "need_filepath":        {"zh": "❌ 错误: 请提供文件路径",
                             "en": "❌ Error: please provide a file path"},
    "unknown_command":      {"zh": '❌ 错误: 未知命令 "{cmd}"',
                             "en": '❌ Error: unknown command "{cmd}"'},
    "see_help":             {"zh": "运行 'python query.py help' 查看帮助",
                             "en": "Run 'python query.py help' for usage"},
    "interrupted":          {"zh": "\n\n⚠️  操作已取消",
                             "en": "\n\n⚠️  Operation cancelled"},
    "generic_error":        {"zh": "❌ 错误: {err}",
                             "en": "❌ Error: {err}"},
}

# Module-level active language; set by main()
_LANG = "en"


def detect_lang(default: Optional[str] = None) -> str:
    """Infer language from environment."""
    if default:
        return "zh" if default.lower().startswith("zh") else "en"
    for var in ("ATLAS_LANG", "LC_ALL", "LANG"):
        val = os.environ.get(var, "")
        if val:
            return "zh" if val.lower().startswith("zh") else "en"
    return "en"


def t(key: str, **kwargs) -> str:
    """Translate key into active language."""
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
# Git helpers
# ---------------------------------------------------------------------------

def run_git_command(args: List[str]) -> Optional[str]:
    """Execute a git command."""
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            check=True
        )
        output = result.stdout.strip()
        return output if output else None
    except subprocess.CalledProcessError as e:
        print(t("git_cmd_failed", err=e.stderr.strip()), file=sys.stderr)
        return None
    except FileNotFoundError:
        print(t("git_not_found"), file=sys.stderr)
        return None


def is_git_repo() -> bool:
    """Check if current directory is inside a Git repo."""
    result = run_git_command(["rev-parse", "--is-inside-work-tree"])
    return result == "true"


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def search_commits(keyword: str, limit: int = 20) -> None:
    print(t("search_header", kw=keyword))
    output = run_git_command([
        "log",
        f"--grep={keyword}",
        "--oneline",
        "-n", str(limit),
        "--date=short",
        "--pretty=format:%h | %ad | %an | %s"
    ])

    if output:
        print(t("search_table_head"))
        print("-" * 80)
        for line in output.split('\n'):
            print(line)
        print(t("search_found", n=len(output.split('\n')), limit=limit))
    else:
        print(t("search_none", kw=keyword))


def query_author(author: str, limit: int = 20) -> None:
    print(t("author_header", name=author))
    output = run_git_command([
        "log",
        f"--author={author}",
        "--oneline",
        "-n", str(limit),
        "--date=short",
        "--pretty=format:%h | %ad | %s"
    ])

    if output:
        print(t("author_table_head"))
        print("-" * 80)
        for line in output.split('\n'):
            print(line)
        print(t("author_found", n=len(output.split('\n')), limit=limit))
    else:
        print(t("author_none", name=author))


def file_history(filepath: str, limit: int = 20) -> None:
    print(t("file_header", path=filepath))
    output = run_git_command([
        "log",
        "--follow",
        "--oneline",
        "-n", str(limit),
        "--date=short",
        "--pretty=format:%h | %ad | %an | %s",
        "--", filepath
    ])

    if output:
        print(t("search_table_head"))
        print("-" * 80)
        for line in output.split('\n'):
            print(line)
        print(t("file_found", n=len(output.split('\n')), limit=limit))
    else:
        print(t("file_none", path=filepath))


def contributor_stats(limit: int = 20) -> None:
    print(t("stats_header"))
    output = run_git_command([
        "shortlog",
        "-sn",
        "--no-merges"
    ])

    if output:
        lines = output.split('\n')[:limit]
        print(t("stats_table_head"))
        print("-" * 50)
        for line in lines:
            print(line.strip())
        print(t("stats_found", n=len(output.split('\n')), limit=limit))
    else:
        print(t("stats_none"))


def recent_commits(count: int = 10) -> None:
    print(t("recent_header", count=count))
    output = run_git_command([
        "log",
        "--oneline",
        "-n", str(count),
        "--date=short",
        "--pretty=format:%h | %ad | %an | %s"
    ])

    if output:
        print(t("search_table_head"))
        print("-" * 80)
        for line in output.split('\n'):
            print(line)
        print(t("recent_found", n=len(output.split('\n'))))
    else:
        print(t("recent_none"))


def change_stats(ref: str = "HEAD~10..HEAD") -> None:
    print(t("changes_header", ref=ref))
    output = run_git_command([
        "diff",
        "--stat",
        ref
    ])

    if output:
        print(output)
        print(t("changes_done"))
    else:
        print(t("changes_none", ref=ref))


def branch_status() -> None:
    print(t("branches_header"))
    output = run_git_command([
        "branch",
        "-vv"
    ])

    if output:
        print(output)
        print(t("branches_found", n=len(output.split('\n'))))
    else:
        print(t("branches_none"))


def list_tags(pattern: str = "*") -> None:
    print(t("tags_header", pattern=pattern))
    output = run_git_command([
        "tag",
        "-l",
        pattern
    ])

    if output:
        tags = output.split('\n')
        for tag in tags:
            print(f"  {tag}")
        print(t("tags_found", n=len(tags)))
    else:
        print(t("tags_none"))


def hot_files(limit: int = 20, since: str = "3 months ago") -> None:
    print(t("hot_header", since=since))

    output = run_git_command([
        "log",
        "--pretty=format:",
        "--name-only",
        f"--since={since}"
    ])

    if not output:
        print(t("hot_none"))
        return

    file_counts: Dict[str, int] = {}
    for line in output.split('\n'):
        filepath = line.strip()
        if filepath:
            file_counts[filepath] = file_counts.get(filepath, 0) + 1

    sorted_files = sorted(file_counts.items(), key=lambda x: x[1], reverse=True)
    print(t("hot_table_head"))
    print("-" * 80)
    for filepath, count in sorted_files[:limit]:
        print(f"{count:8} | {filepath}")

    print(t("hot_found", n=len(file_counts), limit=limit))


def show_help() -> None:
    lines = [
        "",
        t("help_title"),
        "",
        t("help_usage_label"),
        t("help_usage_line"),
        "",
        t("help_cmds_label"),
        t("help_cmd_search"),
        t("help_cmd_author"),
        t("help_cmd_file"),
        t("help_cmd_stats"),
        t("help_cmd_recent"),
        t("help_cmd_changes"),
        t("help_cmd_branches"),
        t("help_cmd_tags"),
        t("help_cmd_hotfiles"),
        t("help_cmd_help"),
        "",
        t("help_examples_label"),
        '    python query.py search "fix bug"',
        '    python query.py author "Zhang San"',
        "    python query.py file src/main.js",
        "    python query.py stats",
        "    python query.py recent 20",
        "    python query.py changes HEAD~5..HEAD",
        '    python query.py tags "v1.*"',
        "    python query.py hotfiles",
        "",
        t("help_lang_note"),
        "",
    ]
    print("\n".join(lines))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _parse_lang_arg(argv: List[str]) -> Tuple[Optional[str], List[str]]:
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
    _LANG = "zh" if (lang or "").lower().startswith("zh") else "en"

    if not rest:
        show_help()
        sys.exit(1)

    command = rest[0].lower()
    if command != "help" and not is_git_repo():
        print(t("not_git_repo"), file=sys.stderr)
        sys.exit(1)

    try:
        if command == "search":
            if len(rest) < 2:
                print(t("need_keyword"), file=sys.stderr)
                sys.exit(1)
            search_commits(rest[1])

        elif command == "author":
            if len(rest) < 2:
                print(t("need_author"), file=sys.stderr)
                sys.exit(1)
            query_author(rest[1])

        elif command == "file":
            if len(rest) < 2:
                print(t("need_filepath"), file=sys.stderr)
                sys.exit(1)
            file_history(rest[1])

        elif command == "stats":
            contributor_stats()

        elif command == "recent":
            count = int(rest[1]) if len(rest) > 1 else 10
            recent_commits(count)

        elif command == "changes":
            ref = rest[1] if len(rest) > 1 else "HEAD~10..HEAD"
            change_stats(ref)

        elif command == "branches":
            branch_status()

        elif command == "tags":
            pattern = rest[1] if len(rest) > 1 else "*"
            list_tags(pattern)

        elif command == "hotfiles":
            hot_files()

        elif command == "help":
            show_help()

        else:
            print(t("unknown_command", cmd=command), file=sys.stderr)
            print(t("see_help"), file=sys.stderr)
            sys.exit(1)

    except KeyboardInterrupt:
        print(t("interrupted"), file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(t("generic_error", err=str(e)), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
