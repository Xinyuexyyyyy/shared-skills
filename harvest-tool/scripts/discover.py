from __future__ import annotations

"""
Harvest Tool - Stage 1: 发现
输入: 主题/关键词
输出: 项目列表，每项附选择理由
"""

import sys
import os
import subprocess
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from scripts.utils import save_json, check_gh_cli_ready
from configs.settings import OUTPUT_DIR, DEFAULT_REPO_COUNT


def _build_discover_payload(
    query: str,
    count: int,
    repos: list[dict],
    *,
    status: str,
    errors: list[str] | None = None,
    warnings: list[str] | None = None,
) -> dict:
    return {
        "status": status,
        "errors": errors or [],
        "warnings": warnings or [],
        "meta": {
            "query": query,
            "requested_count": count,
            "returned_count": len(repos),
        },
        "query": query,
        "repos": repos,
    }


def discover(query: str, count: int = DEFAULT_REPO_COUNT) -> list[dict]:
    """
    使用 gh CLI 发现 GitHub 项目

    Args:
        query: 搜索关键词
        count: 返回数量

    Returns:
        项目列表
    """
    query = (query or "").strip()
    if not query:
        print("[Error] 搜索关键词不能为空")
        output_file = os.path.join(OUTPUT_DIR, "discover_results.json")
        save_json(
            _build_discover_payload(
                query,
                count,
                [],
                status="invalid-input",
                errors=["搜索关键词不能为空"],
            ),
            output_file,
        )
        return []

    if count < 1:
        print("[Error] 搜索数量必须大于 0")
        output_file = os.path.join(OUTPUT_DIR, "discover_results.json")
        save_json(
            _build_discover_payload(
                query,
                count,
                [],
                status="invalid-input",
                errors=["搜索数量必须大于 0"],
            ),
            output_file,
        )
        return []

    print(f"[Stage 1] 搜索关键词: {query}")

    search_result = search_github_repos(query, count)
    repos = search_result["repos"]

    # 格式化输出
    formatted = []
    for i, repo in enumerate(repos, 1):
        stars = repo.get("stars", 0)
        stars_str = f"★{stars:,}" if stars else "★未知"

        formatted.append({
            "index": i,
            "name": repo.get("name", ""),
            "full_name": repo.get("name", ""),
            "description": repo.get("description", ""),
            "url": repo.get("url", ""),
            "stars": stars,
            "stars_str": stars_str,
            "language": repo.get("language", ""),
            "last_commit": repo.get("last_commit", ""),
            "topics": [],
        })

    # 保存结果
    output_file = os.path.join(OUTPUT_DIR, "discover_results.json")
    payload = _build_discover_payload(
        query,
        count,
        formatted,
        status=search_result["status"],
        errors=search_result.get("errors", []),
        warnings=search_result.get("warnings", []),
    )
    save_json(payload, output_file)

    print(f"[Stage 1] 完成，找到 {len(formatted)} 个项目")
    return formatted


def search_github_repos(query: str, count: int = 10) -> dict:
    """
    使用 gh search repos 搜索仓库
    依赖: gh CLI 已登录（gh auth status）
    """
    query = (query or "").strip()
    if not query:
        return {"status": "invalid-input", "errors": ["搜索关键词不能为空"], "warnings": [], "repos": []}

    if count < 1:
        return {"status": "invalid-input", "errors": ["搜索数量必须大于 0"], "warnings": [], "repos": []}

    ready, message = check_gh_cli_ready()
    if not ready:
        print(f"[Error] {message}")
        return {"status": "blocked", "errors": [message], "warnings": [], "repos": []}

    cmd = [
        "gh", "search", "repos", query,
        "--limit", str(min(count, 30)),
        "--json", "fullName,description,stargazersCount,language,pushedAt,isArchived",
    ]

    # 如果有关键词过滤，加 stars 过滤
    if count <= 10:
        cmd += ["--sort", "stars", "--order", "desc"]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        result.check_returncode()
        items = json.loads(result.stdout)
    except FileNotFoundError:
        print("[Error] gh CLI 未安装或不可用")
        return {"status": "blocked", "errors": ["gh CLI 未安装或不可用"], "warnings": [], "repos": []}
    except subprocess.CalledProcessError as e:
        print(f"[Error] gh search failed: {e.stderr}")
        message = (e.stderr or "").strip() or "gh search 执行失败"
        return {"status": "blocked", "errors": [message], "warnings": [], "repos": []}
    except json.JSONDecodeError:
        print(f"[Error] Failed to parse gh output")
        return {"status": "parse-error", "errors": ["gh search 输出不是合法 JSON"], "warnings": [], "repos": []}
    except Exception as e:
        print(f"[Error] {e}")
        return {"status": "error", "errors": [str(e)], "warnings": [], "repos": []}

    results = []
    for item in items:
        # 过滤 archived 项目
        if item.get("isArchived", False):
            continue

        pushed_at = item.get("pushedAt", "")
        last_commit = pushed_at[:10] if pushed_at else ""

        results.append({
            "name": item.get("fullName", ""),
            "description": item.get("description", "") or "",
            "url": f"https://github.com/{item.get('fullName', '')}",
            "stars": item.get("stargazersCount", 0),
            "language": item.get("language", "") or "",
            "last_commit": last_commit,
        })

    warnings = []
    status = "ok"
    if not results:
        status = "empty"
        warnings.append("未找到可用仓库，请尝试更换关键词。")
    return {"status": status, "errors": [], "warnings": warnings, "repos": results}


def format_discover_output(repos: list[dict]) -> str:
    """格式化输出给用户"""
    if not repos:
        return "未找到相关项目，请尝试其他关键词。"

    lines = [f"**找到 {len(repos)} 个相关项目：**\n"]

    for repo in repos:
        lines.append(f"**{repo['index']}. {repo['name']}**（{repo['stars_str']}）")
        lines.append(f"   描述：{repo['description'][:100]}..." if len(repo['description']) > 100 else f"   描述：{repo['description']}")
        if repo['language']:
            lines.append(f"   语言：{repo['language']}")
        lines.append(f"   链接：{repo['url']}")
        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = sys.argv[1]
        count = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_REPO_COUNT
        repos = discover(query, count)
        print(format_discover_output(repos))
    else:
        print("用法: python discover.py <关键词> [数量]")
