"""
Harvest Tool - Stage 5: 分析数据准备
输入: 已抓取的仓库内容（harvest 结果）
输出: 结构化的抓取内容，供 Claude 分析

注：分析本身由 Claude 在对话中完成，不再调用外部 LLM。
"""

import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from scripts.utils import save_json, load_json
from configs.settings import OUTPUT_DIR


def _safe_repo_name(value: str) -> str:
    return (value or "").replace("/", "_").replace(" ", "_")


def _build_analysis_source_context(data: dict) -> dict:
    project = data.get("project", "")
    repo_name = data.get("repo_name", "")
    repo_key = repo_name or project
    harvest_file = os.path.join(OUTPUT_DIR, f"harvest_{_safe_repo_name(repo_key)}.json") if repo_key else ""
    return {
        "project": project,
        "repo_name": repo_name,
        "url": data.get("url") or data.get("meta", {}).get("url", ""),
        "harvest_file": harvest_file,
    }


def infer_repo_profile(data: dict) -> dict:
    """基于抓取材料给仓库做一个轻量画像。"""
    structure = data.get("structure", {})
    directories = set(structure.get("directories", []))
    root_files = set(structure.get("root_files", []))
    code_files = data.get("code_files", {}).get("files", [])
    readme = data.get("readme", {}).get("raw", "")

    signals: list[str] = []

    if "skills" in directories and (
        ".claude-plugin" in directories
        or ".codex-plugin" in directories
        or "AGENTS.md" in root_files
        or "CLAUDE.md" in root_files
    ):
        signals.append("存在 skills 目录和多端 agent/plugin 入口")
        return {"type": "skills-framework", "label": "技能/方法论框架仓库", "signals": signals}

    if "docs" in directories and len(code_files) <= 2 and len(readme) > 1000:
        signals.append("README/文档占比较高，代码样本较少")
        return {"type": "docs-heavy", "label": "文档/知识仓库", "signals": signals}

    if {"scripts", "hooks"} & directories and not ({"src", "lib", "core"} & directories):
        signals.append("以 scripts/hooks 为主，没有明显应用源码目录")
        return {"type": "workflow-automation", "label": "工作流/自动化仓库", "signals": signals}

    if {"src", "app", "frontend", "backend"} & directories:
        signals.append("存在典型应用源码目录")
        return {"type": "application", "label": "应用型仓库", "signals": signals}

    if {"lib", "pkg", "internal", "core"} & directories:
        signals.append("存在典型库/模块目录")
        return {"type": "library", "label": "库/框架仓库", "signals": signals}

    if code_files:
        signals.append("抓到了可读代码样本，但目录信号不够强")
        return {"type": "general-codebase", "label": "通用代码仓库", "signals": signals}

    signals.append("主要依赖 README 和目录结构判断")
    return {"type": "unknown", "label": "类型待定仓库", "signals": signals}


def assess_analysis_readiness(data: dict) -> dict:
    """评估当前抓取材料是否足够支撑较强结论。"""
    warnings = data.get("warnings", [])
    readme = data.get("readme", {}).get("raw", "")
    code_files = data.get("code_files", {}).get("files", [])
    status = data.get("status", "")

    reasons: list[str] = []
    level = "high"

    if not readme:
        level = "low"
        reasons.append("未抓到 README，背景信息不足")

    if not code_files:
        level = "low"
        reasons.append("没有核心文件样本，结论只能停留在目录层")
    elif len(code_files) < 3 and level != "low":
        level = "medium"
        reasons.append("核心文件样本较少，适合做方向判断，不适合下重结论")

    if warnings and level == "high":
        level = "medium"
        reasons.append("抓取过程中有警告，分析时要降低确定性")

    if status == "partial" and level != "low":
        level = "medium"
        reasons.append("抓取状态为 partial，说明仍有信息盲区")

    if not reasons:
        reasons.append("README、目录结构和核心文件样本都已具备，可支持一轮较强分析")

    return {"level": level, "reasons": reasons}


def load_harvest_result(repo_name: str = "") -> dict:
    """
    加载已抓取的仓库内容，准备分析材料
    """
    harvest_file = None

    if repo_name:
        safe_name = repo_name.replace("/", "_").replace(" ", "_")
        harvest_file = os.path.join(OUTPUT_DIR, f"harvest_{safe_name}.json")
        if not os.path.exists(harvest_file):
            return {"error": f"未找到指定抓取结果: {repo_name}"}

    if not harvest_file:
        # 找最新的
        files = [f for f in os.listdir(OUTPUT_DIR) if f.startswith("harvest_") and f.endswith(".json")]
        if files:
            files.sort(key=lambda x: os.path.getmtime(os.path.join(OUTPUT_DIR, x)))
            harvest_file = os.path.join(OUTPUT_DIR, files[-1])

    if not harvest_file or not os.path.exists(harvest_file):
        return {"error": "未找到抓取结果，请先运行 harvest.py"}

    return load_json(harvest_file)


def format_analysis_input(data: dict) -> str:
    """
    格式化为 Claude 可直接阅读的分析材料
    """
    if "error" in data:
        return f"加载失败：{data['error']}"

    project = data.get("project", "")
    readme = data.get("readme", {}).get("raw", "")
    structure = data.get("structure", {})
    code_files = data.get("code_files", {}).get("files", [])
    skill_samples = data.get("code_files", {}).get("skill_samples", [])
    skill_sample_paths = {item.get("path") or item.get("name") for item in skill_samples}
    core_files = [
        item
        for item in code_files
        if (item.get("path") or item.get("name")) not in skill_sample_paths
    ]
    warnings = data.get("warnings", [])
    issues = data.get("issues", [])
    profile = infer_repo_profile(data)
    readiness = assess_analysis_readiness(data)

    lines = [f"**【分析材料】{project}**\n"]

    lines.append("## 仓库画像\n")
    lines.append(f"- 类型判断：{profile.get('label', '')}")
    for signal in profile.get("signals", []):
        lines.append(f"- 依据：{signal}")
    lines.append("")

    lines.append("## 材料置信度\n")
    lines.append(f"- 当前等级：{readiness.get('level', '')}")
    for reason in readiness.get("reasons", []):
        lines.append(f"- 原因：{reason}")
    lines.append("")

    if warnings:
        lines.append("## 抓取警告\n")
        for warning in warnings:
            lines.append(f"- {warning}")
        lines.append("")

    if issues:
        lines.append("## 结构化告警\n")
        for issue in issues:
            target = f"（{issue.get('target', '')}）" if issue.get("target") else ""
            lines.append(
                f"- [{issue.get('stage', '')}/{issue.get('code', '')}] {issue.get('message', '')}{target}"
            )
        lines.append("")

    # README
    lines.append(f"## README\n")
    if readme:
        lines.append(readme[:4000])
    else:
        lines.append("未找到 README")
    lines.append("")

    # 目录结构
    lines.append(f"## 目录结构\n")
    root_files = structure.get("root_files", [])
    directories = structure.get("directories", [])
    lines.append(f"根目录文件：{', '.join(root_files[:15])}")
    lines.append(f"子目录：{', '.join(directories[:15])}")
    lines.append("")

    # Skill samples
    if skill_samples:
        lines.append(f"## Skill 样本文件（共 {len(skill_samples)} 个）\n")
        for f in skill_samples:
            lines.append(f"### {f.get('name', '')}")
            lines.append("```")
            content = f.get("content", "")
            lines.append(content[:1800])
            lines.append("```")
            lines.append("")

    # 核心代码文件
    lines.append(f"## 核心代码文件（共 {len(core_files)} 个）\n")
    for f in core_files:
        lines.append(f"### {f.get('name', '')}")
        lines.append(f"```")
        content = f.get("content", "")
        lines.append(content[:1500])
        lines.append(f"```")
        lines.append("")

    lines.append("---")
    lines.append("\n请分析以上材料，输出：")
    lines.append("1. 整体架构（怎么组织的）")
    lines.append("2. 核心亮点")
    lines.append("3. 哪些可以直接用")
    lines.append("4. 哪些需要改动")
    lines.append("5. 哪些思路可以借鉴")
    lines.append("6. 风险/问题")
    lines.append("7. 整体评价（值得拆吗？适合什么场景？）")
    lines.append("8. 结合仓库类型和材料置信度，哪些判断只能算推测，哪些判断相对稳")

    return "\n".join(lines)


def build_analysis_summary(data: dict) -> dict:
    """把仓库画像和置信度沉成结构化摘要，方便后续流程复用。"""
    project = data.get("project", "")
    repo_name = data.get("repo_name", "")
    profile = infer_repo_profile(data)
    readiness = assess_analysis_readiness(data)
    warnings = data.get("warnings", [])
    issues = data.get("issues", [])
    coverage = data.get("code_files", {}).get("coverage", {})
    source_context = _build_analysis_source_context(data)

    return {
        "project": project,
        "repo_name": repo_name,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "harvest_file": source_context.get("harvest_file", ""),
        "source_context": source_context,
        "status": data.get("status", ""),
        "profile": profile,
        "readiness": readiness,
        "warnings": warnings,
        "issues": issues,
        "coverage": coverage,
    }


def save_analysis_summary(data: dict) -> dict:
    summary = build_analysis_summary(data)
    output_file = os.path.join(OUTPUT_DIR, "analysis_results.json")

    payload = {"analyses": []}
    if os.path.exists(output_file):
        try:
            payload = load_json(output_file)
        except Exception:
            payload = {"analyses": []}

    analyses = payload.get("analyses", [])
    analyses = [item for item in analyses if item.get("project") != summary.get("project")]
    analyses.append(summary)
    payload["analyses"] = analyses
    save_json(payload, output_file)
    return summary


if __name__ == "__main__":
    result = load_harvest_result()
    if "error" in result:
        print(f"错误: {result['error']}")
    else:
        save_analysis_summary(result)
        print(format_analysis_input(result))
