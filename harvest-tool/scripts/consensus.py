"""
Harvest Tool - Stage 6: 共识文档生成
输入: 用户确认的决策内容
输出: 结构化共识文档（JSON）

注：共识内容由 Claude 在对话中生成，此脚本负责保存和格式化。
"""

import sys
import os
import json
import re
from datetime import datetime
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from scripts.utils import save_json, load_json
from configs.settings import OUTPUT_DIR, CONSENSUS_OUTPUT_DIR


def _ensure_list(value) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _ensure_dict(value) -> dict:
    if isinstance(value, dict):
        return value
    return {}


def _slugify(value: str) -> str:
    text = re.sub(r"[^A-Za-z0-9._-]+", "-", (value or "").strip())
    text = text.strip("-._")
    return text or "harvest-consensus"


def _normalize_repo_name(value: str) -> str:
    text = (value or "").strip()
    if not text:
        return ""

    if text.startswith("git@github.com:"):
        text = text[len("git@github.com:") :]

    if text.startswith("http://") or text.startswith("https://"):
        parsed = urlparse(text)
        if "github.com" not in (parsed.netloc or ""):
            return ""
        parts = [part for part in parsed.path.strip("/").split("/") if part]
        if len(parts) >= 2:
            return f"{parts[0]}/{parts[1].replace('.git', '')}"
        return ""

    normalized = text.replace("https://github.com/", "").replace("http://github.com/", "")
    normalized = normalized.strip("/").replace(".git", "")
    if normalized.count("/") >= 1:
        owner, repo, *_ = [part for part in normalized.split("/") if part]
        return f"{owner}/{repo}"
    return normalized


def _append_unique(items: list[str], value: str) -> None:
    text = (value or "").strip()
    if text and text not in items:
        items.append(text)


def _extract_source_context(user_decisions: dict) -> dict:
    repo_names: list[str] = []
    source_urls: list[str] = []
    harvest_files: list[str] = []

    def add_repo(raw: str) -> None:
        repo = _normalize_repo_name(raw)
        if repo:
            _append_unique(repo_names, repo)

    def add_url(raw: str) -> None:
        url = (raw or "").strip()
        if not url:
            return
        _append_unique(source_urls, url)
        add_repo(url)

    def add_harvest_file(raw: str) -> None:
        path = (raw or "").strip()
        if path and "harvest_" in os.path.basename(path):
            _append_unique(harvest_files, path)

    add_repo(user_decisions.get("repo_name", ""))
    add_repo(user_decisions.get("project", ""))
    add_url(user_decisions.get("url", ""))

    harvest_target = _ensure_dict(user_decisions.get("harvest_target"))
    add_repo(harvest_target.get("repo", ""))
    add_url(harvest_target.get("url", ""))

    source_repo = _ensure_dict(user_decisions.get("source_repo"))
    add_repo(source_repo.get("full_name", ""))
    add_url(source_repo.get("url", ""))

    for item in _ensure_list(user_decisions.get("candidate_repos")):
        if not isinstance(item, dict):
            continue
        add_repo(item.get("repo", ""))
        add_url(item.get("url", ""))

    for item in _ensure_list(user_decisions.get("sources")):
        if not isinstance(item, str):
            continue
        add_url(item)
        add_harvest_file(item)

    for item in _ensure_list(user_decisions.get("harvest_files")):
        if isinstance(item, str):
            add_harvest_file(item)

    primary_repo = repo_names[0] if repo_names else ""
    return {
        "primary_repo": primary_repo,
        "repo_names": repo_names,
        "source_urls": source_urls,
        "harvest_files": harvest_files,
    }


def _render_consensus_markdown(consensus: dict) -> str:
    source_context = _ensure_dict(consensus.get("source_context"))
    lines = [
        "# 共识草稿",
        "",
        f"> 生成时间：{consensus.get('generated_at', '')}",
        f"> 输出位置：`{consensus.get('output_dir', '')}`",
        "",
        "## 做什么",
        "",
        consensus.get("做什么", "") or "未填写",
        "",
        "## 为什么做",
        "",
        consensus.get("为什么做", "") or "未填写",
        "",
    ]

    goals = consensus.get("目标", [])
    if goals:
        lines.extend(["## 目标", ""])
        for item in goals:
            lines.append(f"- {item}")
        lines.append("")

    copied_from = consensus.get("从哪里抄", {})
    lines.extend(["## 从哪里抄", ""])
    for heading in ["直接用", "改动用", "借鉴用"]:
        items = copied_from.get(heading, [])
        if not items:
            continue
        lines.append(f"### {heading}")
        lines.append("")
        for item in items:
            lines.append(f"- {item}")
        lines.append("")

    how_to = consensus.get("怎么做", "")
    lines.extend(["## 怎么做", ""])
    if isinstance(how_to, list):
        for item in how_to:
            lines.append(f"- {item}")
    else:
        lines.append(how_to or "未填写")
    lines.append("")

    for section in ["实施优先级", "不确定性", "风险"]:
        items = consensus.get(section, [])
        if not items:
            continue
        lines.extend([f"## {section}", ""])
        for item in items:
            lines.append(f"- {item}")
        lines.append("")

    if source_context.get("repo_names"):
        lines.extend(["## 来源仓库", ""])
        for repo_name in source_context.get("repo_names", []):
            lines.append(f"- {repo_name}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _render_readme(consensus: dict) -> str:
    output_dir = consensus.get("output_dir", "")
    repo_hint = consensus.get("title", "")
    source_context = _ensure_dict(consensus.get("source_context"))
    lines = [
        f"# {repo_hint}",
        "",
        "## 这是什么",
        "",
        "这是一次 harvest 共识落盘结果。这里保存的是可继续讨论和复用的阶段产物，不是临时命令输出。",
        "",
        "## 目录说明",
        "",
        "- `consensus.md`：可直接阅读的共识草稿",
        "- `consensus.json`：结构化版本，便于脚本或后续流程继续消费",
        "",
        "## 位置",
        "",
        f"- 输出目录：`{output_dir}`",
        "",
    ]
    if source_context.get("repo_names"):
        lines.extend(["## 来源仓库", ""])
        for repo_name in source_context.get("repo_names", []):
            lines.append(f"- `{repo_name}`")
        lines.append("")
    return "\n".join(lines)


def save_consensus(user_decisions: dict, title_prefix: str = "") -> dict:
    """
    保存用户确认的共识文档

    Args:
        user_decisions: 用户/Claude 确认的决策内容
        title_prefix: 共识文档标题前缀

    Returns:
        共识文档
    """
    if not isinstance(user_decisions, dict):
        return {"error": "共识输入必须是 JSON object"}

    copied_from = _ensure_dict(user_decisions.get("从哪里抄"))
    now = datetime.now()
    source_context = _extract_source_context(user_decisions)
    title = user_decisions.get("title") or title_prefix or f"Harvest 共识 - {now.strftime('%Y-%m-%d')}"
    slug_seed = title_prefix or user_decisions.get("title") or source_context.get("primary_repo") or "harvest-consensus"
    slug_prefix = _slugify(slug_seed)
    dir_name = f"{slug_prefix}-{now.strftime('%Y%m%d-%H%M%S')}"
    output_dir = os.path.join(CONSENSUS_OUTPUT_DIR, dir_name)

    consensus = {
        "title": title,
        "generated_at": now.strftime("%Y-%m-%d %H:%M:%S"),
        "做什么": user_decisions.get("做什么", ""),
        "为什么做": user_decisions.get("为什么做", ""),
        "目标": _ensure_list(user_decisions.get("目标")),
        "从哪里抄": {
            "直接用": _ensure_list(copied_from.get("直接用")),
            "改动用": _ensure_list(copied_from.get("改动用")),
            "借鉴用": _ensure_list(copied_from.get("借鉴用") or copied_from.get("只参考")),
        },
        "怎么做": user_decisions.get("怎么做", ""),
        "实施优先级": _ensure_list(user_decisions.get("实施优先级")),
        "不确定性": _ensure_list(user_decisions.get("不确定性")),
        "风险": _ensure_list(user_decisions.get("风险")),
        "source_context": source_context,
        "output_dir": output_dir,
    }
    for key, value in user_decisions.items():
        if key not in consensus:
            consensus[key] = value

    # 保存
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "consensus.json")
    markdown_file = os.path.join(output_dir, "consensus.md")
    readme_file = os.path.join(output_dir, "README.md")

    save_json(consensus, output_file)
    with open(markdown_file, "w", encoding="utf-8") as f:
        f.write(_render_consensus_markdown(consensus))
    with open(readme_file, "w", encoding="utf-8") as f:
        f.write(_render_readme(consensus))

    consensus["files"] = {
        "json": output_file,
        "markdown": markdown_file,
        "readme": readme_file,
    }
    # latest 保存一份
    latest_file = os.path.join(CONSENSUS_OUTPUT_DIR, "latest_consensus.json")
    save_json(consensus, latest_file)

    print(f"[Stage 6] 共识文档已保存: {output_dir}")
    return consensus


def format_consensus_for_review(consensus: dict) -> str:
    """格式化共识文档，用于用户确认"""

    if "error" in consensus:
        return f"生成失败：{consensus['error']}"

    lines = [
        "**【项目共识文档】**\n",
        f"标题：{consensus.get('title', '')}",
        f"生成时间：{consensus.get('generated_at', '')}\n",
        "---",
        f"**做什么：**\n{consensus.get('做什么', '')}\n",
        f"**为什么做：**\n{consensus.get('为什么做', '')}\n",
    ]

    source_context = _ensure_dict(consensus.get("source_context"))
    if source_context.get("repo_names"):
        lines.append(f"来源仓库：{', '.join(source_context.get('repo_names', []))}\n")

    # 目标
    目标 = consensus.get("目标", [])
    if 目标:
        lines.append("**目标：**")
        for g in 目标:
            lines.append(f"  - {g}")
        lines.append("")

    # 从哪里抄
    lines.append("**从哪里抄：**\n")
    从哪里抄 = consensus.get("从哪里抄", {})
    直接用 = 从哪里抄.get("直接用", [])
    改动用 = 从哪里抄.get("改动用", [])
    借鉴用 = 从哪里抄.get("借鉴用", [])

    if 直接用:
        lines.append(f"  直接用：{', '.join(直接用)}")
    if 改动用:
        lines.append(f"  改动用：{', '.join(改动用)}")
    if 借鉴用:
        lines.append(f"  借鉴用：{', '.join(借鉴用)}")
    lines.append("")

    lines.append(f"**怎么做：**\n{consensus.get('怎么做', '')}\n")

    # 优先级
    优先级 = consensus.get("实施优先级", [])
    if 优先级:
        lines.append("**实施优先级：**")
        for p in 优先级:
            lines.append(f"  - {p}")
        lines.append("")

    # 不确定性
    不确定性 = consensus.get("不确定性", [])
    if 不确定性:
        lines.append("**不确定性：**")
        for u in 不确定性:
            lines.append(f"  - {u}")
        lines.append("")

    # 风险
    风险 = consensus.get("风险", [])
    if 风险:
        lines.append("**风险：**")
        for r in 风险:
            lines.append(f"  - {r}")
        lines.append("")

    lines.append("---")
    lines.append(f"共识文档已保存到：{consensus.get('output_dir', CONSENSUS_OUTPUT_DIR)}")

    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            decisions = json.loads(sys.argv[1])
        except json.JSONDecodeError as exc:
            print(f"用法错误: 决策内容不是合法 JSON ({exc})")
            sys.exit(1)
        consensus = save_consensus(decisions)
        print(format_consensus_for_review(consensus))
    else:
        print("用法: python consensus.py '<json决策内容>'")
