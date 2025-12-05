#!/usr/bin/env python3
"""
Git Query Script - Git 信息快速查询工具

用法:
    python query.py search <keyword>    # 搜索提交信息
    python query.py author <name>       # 查询作者提交
    python query.py file <path>         # 文件历史
    python query.py stats               # 贡献统计
    python query.py recent [n]          # 最近提交
    python query.py changes [ref]       # 变更统计
    python query.py branches            # 分支状态
    python query.py tags                # 标签列表
    python query.py hotfiles            # 热点文件
"""

import sys
import subprocess
import json
import os
from typing import List, Dict, Optional


def run_git_command(args: List[str]) -> Optional[str]:
    """执行 Git 命令"""
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
        print(f"❌ Git 命令执行失败: {e.stderr.strip()}", file=sys.stderr)
        return None
    except FileNotFoundError:
        print("❌ Git 未安装或不在 PATH 中", file=sys.stderr)
        return None


def is_git_repo() -> bool:
    """检查是否在 Git 仓库中"""
    result = run_git_command(["rev-parse", "--is-inside-work-tree"])
    return result == "true"


def search_commits(keyword: str, limit: int = 20) -> None:
    """搜索提交信息"""
    print(f'🔍 搜索提交信息: "{keyword}"\n')
    output = run_git_command([
        "log",
        f"--grep={keyword}",
        "--oneline",
        "-n", str(limit),
        "--date=short",
        "--pretty=format:%h | %ad | %an | %s"
    ])

    if output:
        print("提交哈希 | 日期       | 作者     | 提交信息")
        print("-" * 80)
        for line in output.split('\n'):
            print(line)
        print(f"\n✅ 找到 {len(output.split(chr(10)))} 条匹配记录（最多显示 {limit} 条）")
    else:
        print(f'❌ 未找到包含 "{keyword}" 的提交')


def query_author(author: str, limit: int = 20) -> None:
    """查询作者的提交"""
    print(f'👤 查询作者: "{author}"\n')
    output = run_git_command([
        "log",
        f"--author={author}",
        "--oneline",
        "-n", str(limit),
        "--date=short",
        "--pretty=format:%h | %ad | %s"
    ])

    if output:
        print("提交哈希 | 日期       | 提交信息")
        print("-" * 80)
        for line in output.split('\n'):
            print(line)
        print(f"\n✅ 找到 {len(output.split(chr(10)))} 条提交（最多显示 {limit} 条）")
    else:
        print(f'❌ 未找到作者 "{author}" 的提交')


def file_history(filepath: str, limit: int = 20) -> None:
    """查询文件历史"""
    print(f'📄 文件历史: {filepath}\n')
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
        print("提交哈希 | 日期       | 作者     | 提交信息")
        print("-" * 80)
        for line in output.split('\n'):
            print(line)
        print(f"\n✅ 找到 {len(output.split(chr(10)))} 条变更记录（最多显示 {limit} 条）")
    else:
        print(f'❌ 文件 "{filepath}" 无历史记录或不存在')


def contributor_stats(limit: int = 20) -> None:
    """贡献者统计"""
    print('📊 贡献者统计\n')
    output = run_git_command([
        "shortlog",
        "-sn",
        "--no-merges"
    ])

    if output:
        lines = output.split('\n')[:limit]
        print("提交数 | 作者")
        print("-" * 50)
        for line in lines:
            print(line.strip())
        print(f"\n✅ 共 {len(output.split(chr(10)))} 位贡献者（显示前 {limit} 名）")
    else:
        print('❌ 无法获取贡献者统计')


def recent_commits(count: int = 10) -> None:
    """最近的提交"""
    print(f'🕐 最近 {count} 次提交\n')
    output = run_git_command([
        "log",
        "--oneline",
        "-n", str(count),
        "--date=short",
        "--pretty=format:%h | %ad | %an | %s"
    ])

    if output:
        print("提交哈希 | 日期       | 作者     | 提交信息")
        print("-" * 80)
        for line in output.split('\n'):
            print(line)
        print(f"\n✅ 显示最近 {len(output.split(chr(10)))} 次提交")
    else:
        print('❌ 无法获取提交记录')


def change_stats(ref: str = "HEAD~10..HEAD") -> None:
    """变更统计"""
    print(f'📈 变更统计: {ref}\n')
    output = run_git_command([
        "diff",
        "--stat",
        ref
    ])

    if output:
        print(output)
        print(f"\n✅ 变更统计完成")
    else:
        print(f'❌ 无法获取 "{ref}" 的变更统计')


def branch_status() -> None:
    """分支状态"""
    print('🌿 分支状态\n')
    output = run_git_command([
        "branch",
        "-vv"
    ])

    if output:
        print(output)
        print(f"\n✅ 共 {len(output.split(chr(10)))} 个本地分支")
    else:
        print('❌ 无法获取分支状态')


def list_tags(pattern: str = "*") -> None:
    """列出标签"""
    print(f'🏷️  标签列表: {pattern}\n')
    output = run_git_command([
        "tag",
        "-l",
        pattern
    ])

    if output:
        tags = output.split('\n')
        for tag in tags:
            print(f"  {tag}")
        print(f"\n✅ 共 {len(tags)} 个标签")
    else:
        print('ℹ️  仓库中没有标签')


def hot_files(limit: int = 20, since: str = "3 months ago") -> None:
    """热点文件（最常修改）"""
    print(f'🔥 热点文件（最近 {since}）\n')

    # 获取所有文件变更
    output = run_git_command([
        "log",
        "--pretty=format:",
        "--name-only",
        f"--since={since}"
    ])

    if not output:
        print('❌ 无法获取文件变更记录')
        return

    # 统计文件修改次数
    file_counts: Dict[str, int] = {}
    for line in output.split('\n'):
        filepath = line.strip()
        if filepath:  # 跳过空行
            file_counts[filepath] = file_counts.get(filepath, 0) + 1

    # 排序并显示
    sorted_files = sorted(file_counts.items(), key=lambda x: x[1], reverse=True)
    print("修改次数 | 文件路径")
    print("-" * 80)
    for filepath, count in sorted_files[:limit]:
        print(f"{count:8} | {filepath}")

    print(f"\n✅ 共 {len(file_counts)} 个文件被修改（显示前 {limit} 个）")


def show_help() -> None:
    """显示帮助信息"""
    help_text = """
Git Query - Git 信息快速查询工具

用法:
    python query.py <命令> [参数]

命令:
    search <keyword>        搜索提交信息（支持模糊匹配）
    author <name>           查询作者的提交记录
    file <path>             查询文件的变更历史
    stats                   显示贡献者统计
    recent [n]              显示最近 n 次提交（默认 10）
    changes [ref]           显示变更统计（默认 HEAD~10..HEAD）
    branches                显示分支状态
    tags [pattern]          列出标签（可选 glob 模式）
    hotfiles                显示热点文件（最常修改）
    help                    显示此帮助信息

示例:
    python query.py search "fix bug"
    python query.py author "Zhang San"
    python query.py file src/main.js
    python query.py stats
    python query.py recent 20
    python query.py changes HEAD~5..HEAD
    python query.py tags "v1.*"
    python query.py hotfiles
"""
    print(help_text)


def main():
    """主函数"""
    if len(sys.argv) < 2:
        show_help()
        sys.exit(1)

    # 检查是否在 Git 仓库中（help 命令除外）
    command = sys.argv[1].lower()
    if command != "help" and not is_git_repo():
        print("❌ 错误: 当前目录不是 Git 仓库", file=sys.stderr)
        sys.exit(1)

    # 执行命令
    try:
        if command == "search":
            if len(sys.argv) < 3:
                print("❌ 错误: 请提供搜索关键词", file=sys.stderr)
                sys.exit(1)
            search_commits(sys.argv[2])

        elif command == "author":
            if len(sys.argv) < 3:
                print("❌ 错误: 请提供作者名称", file=sys.stderr)
                sys.exit(1)
            query_author(sys.argv[2])

        elif command == "file":
            if len(sys.argv) < 3:
                print("❌ 错误: 请提供文件路径", file=sys.stderr)
                sys.exit(1)
            file_history(sys.argv[2])

        elif command == "stats":
            contributor_stats()

        elif command == "recent":
            count = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            recent_commits(count)

        elif command == "changes":
            ref = sys.argv[2] if len(sys.argv) > 2 else "HEAD~10..HEAD"
            change_stats(ref)

        elif command == "branches":
            branch_status()

        elif command == "tags":
            pattern = sys.argv[2] if len(sys.argv) > 2 else "*"
            list_tags(pattern)

        elif command == "hotfiles":
            hot_files()

        elif command == "help":
            show_help()

        else:
            print(f'❌ 错误: 未知命令 "{command}"', file=sys.stderr)
            print("运行 'python query.py help' 查看帮助", file=sys.stderr)
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n⚠️  操作已取消", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"❌ 错误: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
