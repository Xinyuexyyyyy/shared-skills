"""
Harvest Tool - Stage 2: 评估数据准备
输入: 项目列表（discover 结果）
输出: 结构化的项目信息，供 Claude 评估

注：评估本身由 Claude 在对话中完成，不再调用外部 LLM。
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from scripts.utils import fetch_readme, save_json, load_json
from configs.settings import OUTPUT_DIR


def load_projects_for_evaluation(query: str = "") -> list[dict]:
    """
    加载 discover 结果，准备评估材料

    Returns:
        项目列表（含 README 摘要）
    """
    discover_file = os.path.join(OUTPUT_DIR, "discover_results.json")
    if not os.path.exists(discover_file):
        return []

    data = load_json(discover_file)
    repos = data.get("repos", [])

    # 为每个项目抓取 README 摘要（供 Claude 评估用）
    enriched = []
    for repo in repos:
        url = repo.get("url", "")
        readme_data = fetch_readme(url)
        readme_raw = readme_data.get("raw", "")

        enriched.append({
            "index": repo.get("index", 0),
            "name": repo.get("name", ""),
            "description": repo.get("description", ""),
            "url": url,
            "stars": repo.get("stars", 0),
            "stars_str": repo.get("stars_str", ""),
            "language": repo.get("language", ""),
            "last_commit": repo.get("last_commit", ""),
            "readme_preview": readme_raw[:2000] if readme_raw else "",
            "readme_status": "ok" if readme_raw else "missing",
        })

    # 保存
    output_file = os.path.join(OUTPUT_DIR, "evaluate_input.json")
    save_json({"query": query, "projects": enriched}, output_file)

    return enriched


def format_evaluate_input(projects: list[dict]) -> str:
    """
    格式化为 Claude 可直接阅读的评估材料
    """
    if not projects:
        return "未发现项目，请先运行 discover。"

    lines = [f"**待评估项目（共 {len(projects)} 个）：**\n"]

    for p in projects:
        lines.append(f"\n---")
        lines.append(f"**{p['index']}. {p['name']}** {p['stars_str']} | {p['language']}")
        lines.append(f"链接：{p['url']}")
        lines.append(f"描述：{p['description']}")
        if p.get("readme_preview"):
            lines.append(f"\nREADME 摘要：")
            lines.append(f"```")
            lines.append(p["readme_preview"])
            lines.append(f"```")
        else:
            lines.append("\nREADME 摘要：未抓到 README，评估时需更多依赖描述和仓库结构。")

    lines.append(f"\n---")
    lines.append(f"\n请告诉我你的需求背景，我来帮你评估这些项目的匹配度。")
    lines.append(f"或者直接说项目编号（如'1'、'1和3'）来选择要深入的项目。")

    return "\n".join(lines)


if __name__ == "__main__":
    projects = load_projects_for_evaluation()
    print(format_evaluate_input(projects))
