#!/usr/bin/env python3
from __future__ import annotations

"""
Harvest Tool - 主入口（简化版）

用法：
  python skill.py discover <关键词> [数量]     — 搜索 GitHub 项目
  python skill.py harvest <github-url>          — 抓取仓库内容
  python skill.py evaluate                      — 加载 discover 结果供评估
  python skill.py analyze [repo_name]           — 加载 harvest 结果供分析
  python skill.py compare [repo_name ...] [--goal <type>] — 比较多个已分析仓库
  python skill.py compare-consensus [repo_name ...] [--goal <type>] — 从 compare 结果一键落共识
  python skill.py consensus '<json>'            — 保存共识文档

依赖：gh CLI 已登录（gh auth status）
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(__file__))

from scripts.discover import discover, format_discover_output
from scripts.evaluate import load_projects_for_evaluation, format_evaluate_input
from scripts.harvest import harvest_repo, format_harvest_output
from scripts.analyze import load_harvest_result, format_analysis_input, save_analysis_summary
from scripts.compare import build_comparison, format_comparison
from scripts.consensus import save_consensus, format_consensus_for_review
from scripts.utils import normalize_github_repo_url


def _parse_positive_count(raw: str, default: int = 10) -> int:
    try:
        count = int(raw) if raw else default
    except ValueError:
        raise ValueError("数量必须是整数")
    if count < 1 or count > 30:
        raise ValueError("数量必须在 1 到 30 之间")
    return count


def discover_cmd(query: str, count: int = 10):
    """搜索 GitHub 项目"""
    query = (query or "").strip()
    repos = discover(query, count)
    if not query:
        return 1
    print(format_discover_output(repos))
    return 0


def harvest_cmd(url: str):
    """抓取仓库内容"""
    normalized_url = normalize_github_repo_url(url)
    if not normalized_url:
        print("错误: 仓库链接必须是 https://github.com/<owner>/<repo> 形式")
        return 1
    result = harvest_repo(normalized_url)
    print(format_harvest_output(result))
    return 0 if "error" not in result else 1


def evaluate_cmd():
    """加载 discover 结果，格式化输出供 Claude 评估"""
    projects = load_projects_for_evaluation()
    print(format_evaluate_input(projects))
    return 0


def analyze_cmd(repo_name: str = ""):
    """加载 harvest 结果，格式化输出供 Claude 分析"""
    result = load_harvest_result(repo_name)
    if "error" in result:
        print(f"错误: {result['error']}")
        return 1
    save_analysis_summary(result)
    print(format_analysis_input(result))
    return 0


def _parse_compare_args(args: list[str]) -> tuple[list[str], str | None]:
    repo_names: list[str] = []
    goal: str | None = None
    i = 0
    while i < len(args):
        token = args[i]
        if token == "--goal":
            if i + 1 >= len(args):
                raise ValueError("--goal 需要一个值")
            goal = args[i + 1]
            i += 2
            continue
        repo_names.append(token)
        i += 1
    return repo_names, goal


def compare_cmd(repo_names: list[str] | None = None, goal: str | None = None):
    """比较多个已分析仓库"""
    payload = build_comparison(repo_names or [], goal=goal)
    print(format_comparison(payload))
    return 0 if payload.get("comparisons") else 1


def compare_consensus_cmd(repo_names: list[str] | None = None, goal: str | None = None):
    """从 compare 结果直接生成共识目录"""
    payload = build_comparison(repo_names or [], goal=goal)
    if not payload.get("comparisons"):
        print(format_comparison(payload))
        return 1
    seed = payload.get("consensus_seed", {})
    consensus = save_consensus(seed, title_prefix=seed.get("title", "compare-consensus"))
    print(format_comparison(payload))
    print("")
    print(format_consensus_for_review(consensus))
    return 0 if "error" not in consensus else 1


def consensus_cmd(json_str: str):
    """保存共识文档"""
    try:
        decisions = json.loads(json_str)
    except json.JSONDecodeError as exc:
        print(f"错误: 决策内容不是合法 JSON ({exc})")
        return 1
    if not isinstance(decisions, dict):
        print("错误: 决策内容必须是 JSON object")
        return 1
    consensus = save_consensus(decisions)
    print(format_consensus_for_review(consensus))
    return 0 if "error" not in consensus else 1


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    cmd = sys.argv[1]

    if cmd == "discover" and len(sys.argv) > 2:
        query = sys.argv[2]
        try:
            count = _parse_positive_count(sys.argv[3], 10) if len(sys.argv) > 3 else 10
        except ValueError as exc:
            print(f"错误: {exc}")
            return 1
        return discover_cmd(query, count)
    elif cmd == "harvest" and len(sys.argv) > 2:
        return harvest_cmd(sys.argv[2])
    elif cmd == "evaluate":
        return evaluate_cmd()
    elif cmd == "analyze":
        repo_name = sys.argv[2] if len(sys.argv) > 2 else ""
        return analyze_cmd(repo_name)
    elif cmd == "compare":
        try:
            repo_names, goal = _parse_compare_args(sys.argv[2:] if len(sys.argv) > 2 else [])
        except ValueError as exc:
            print(f"错误: {exc}")
            return 1
        return compare_cmd(repo_names, goal)
    elif cmd == "compare-consensus":
        try:
            repo_names, goal = _parse_compare_args(sys.argv[2:] if len(sys.argv) > 2 else [])
        except ValueError as exc:
            print(f"错误: {exc}")
            return 1
        return compare_consensus_cmd(repo_names, goal)
    elif cmd == "consensus" and len(sys.argv) > 2:
        return consensus_cmd(sys.argv[2])
    else:
        print(f"未知命令: {cmd}")
        print(__doc__)
        return 1


if __name__ == "__main__":
    sys.exit(main())
