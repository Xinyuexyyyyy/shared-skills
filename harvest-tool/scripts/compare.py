from __future__ import annotations

"""
Harvest Tool - 批量比较
输入: analysis_results.json 中的一组分析摘要
输出: shortlist 对比材料
"""

import os
import sys
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from scripts.utils import load_json, save_json
from scripts.harvest import harvest_repo
from scripts.analyze import load_harvest_result, save_analysis_summary
from configs.settings import OUTPUT_DIR


def _normalize_repo_names(raw_names: list[str] | None) -> list[str]:
    names = []
    for raw in raw_names or []:
        for item in raw.split(","):
            value = item.strip()
            if value:
                names.append(value)
    return names


def _repo_focus_by_profile(profile_type: str) -> str:
    mapping = {
        "skills-framework": "优先拆 workflow、skills 分层、多端适配和触发机制",
        "docs-heavy": "优先拆方法论、文档结构和信息组织，不下重实现结论",
        "workflow-automation": "优先拆 scripts、hooks、CI 和运行编排",
        "application": "优先拆产品闭环、页面信息架构和任务状态",
        "library": "优先拆核心模块边界、接口设计和数据模型",
        "general-codebase": "优先拆最显眼的核心模块，再决定是否继续深抓",
        "unknown": "先补抓更多材料，再决定拆哪一层",
    }
    return mapping.get(profile_type or "unknown", "先补抓更多材料，再决定拆哪一层")


def _readiness_note(level: str) -> str:
    mapping = {
        "high": "这轮材料足够支撑一轮较强判断",
        "medium": "适合做方向判断，不适合下过重结论",
        "low": "当前只适合记观察，不能直接沉确定方案",
    }
    return mapping.get(level or "medium", "适合做方向判断，不适合下过重结论")


def _profile_priority(profile_type: str) -> int:
    mapping = {
        "application": 30,
        "skills-framework": 28,
        "library": 24,
        "workflow-automation": 22,
        "general-codebase": 18,
        "docs-heavy": 12,
        "unknown": 8,
    }
    return mapping.get(profile_type or "unknown", 8)


def normalize_goal(goal: str | None) -> str | None:
    raw = (goal or "").strip().lower()
    if not raw:
        return None
    aliases = {
        "app": "application",
        "product": "application",
        "workflow": "skills-framework",
        "framework": "skills-framework",
        "skills": "skills-framework",
        "library": "library",
        "lib": "library",
        "automation": "workflow-automation",
        "script": "workflow-automation",
        "docs": "docs-heavy",
        "doc": "docs-heavy",
        "general": "general-codebase",
    }
    return aliases.get(raw, raw)


def _goal_bonus(profile_type: str, goal: str | None) -> tuple[int, str] | None:
    normalized_goal = normalize_goal(goal)
    if not normalized_goal:
        return None

    preferred = {
        "application": {"application": 18, "skills-framework": -4},
        "skills-framework": {"skills-framework": 18, "workflow-automation": 8, "application": -2},
        "library": {"library": 18, "general-codebase": 6},
        "workflow-automation": {"workflow-automation": 18, "skills-framework": 6, "application": -2},
        "docs-heavy": {"docs-heavy": 18, "general-codebase": 4},
        "general-codebase": {"general-codebase": 18, "library": 6},
    }
    goal_map = preferred.get(normalized_goal, {})
    bonus = goal_map.get(profile_type, 0)
    if bonus == 0:
        return None
    sign = "+" if bonus > 0 else ""
    return bonus, f"目标偏好 {normalized_goal} 命中 {profile_type} -> {sign}{bonus}"


def _shortlist_bucket(item: dict) -> str:
    score = int(item.get("score", 0))
    readiness = item.get("readiness_level", "medium")
    warnings = int(item.get("warning_count", 0))

    if readiness == "high" and score >= 78 and warnings <= 1:
        return "priority-deep-dive"
    if readiness in {"high", "medium"} and score >= 52:
        return "worth-reference"
    return "not-priority"


def _bucket_label(bucket: str) -> str:
    return {
        "priority-deep-dive": "优先深拆",
        "worth-reference": "值得参考",
        "not-priority": "暂不主推",
    }.get(bucket, "暂不主推")


def build_shortlist_summary(comparisons: list[dict]) -> dict:
    buckets = {
        "priority-deep-dive": [],
        "worth-reference": [],
        "not-priority": [],
    }

    for item in comparisons:
        bucket = _shortlist_bucket(item)
        item["shortlist_bucket"] = bucket
        item["shortlist_label"] = _bucket_label(bucket)
        buckets[bucket].append(item["project"])

    top_pick = comparisons[0]["project"] if comparisons else ""
    summary = {
        "top_pick": top_pick,
        "priority_deep_dive": buckets["priority-deep-dive"],
        "worth_reference": buckets["worth-reference"],
        "not_priority": buckets["not-priority"],
    }
    return summary


def build_consensus_seed(payload: dict) -> dict:
    shortlist = payload.get("shortlist", {}) or {}
    comparisons = payload.get("comparisons", []) or []
    goal = payload.get("goal")
    repo_names = payload.get("repo_names", []) or []

    top_pick = shortlist.get("top_pick", "")
    direct_use = shortlist.get("priority_deep_dive", [])[:]
    adapt_use = shortlist.get("worth_reference", [])[:]
    reference_only = shortlist.get("not_priority", [])[:]

    if top_pick and top_pick in adapt_use:
        adapt_use.remove(top_pick)
        if top_pick not in direct_use:
            direct_use.insert(0, top_pick)

    why_lines = [
        "这轮比较已经先按材料完整度、仓库类型和警告情况做过排序。",
        "下面这份骨架只负责把 shortlist 收口成可继续讨论的初版共识，不代表最终拍板。",
    ]
    if goal:
        why_lines.append(f"本轮排序额外考虑了目标偏好：`{goal}`。")

    how_lines = [
        "先优先深拆 `直接用` 里的仓库，确认真正要借的模块和工作流。",
        "再从 `改动用` 里挑补充项，决定哪些思路值得吸收但不能整套照搬。",
        "最后把 `借鉴用` 只保留为背景参考，不默认进入 MVP 主线。",
    ]

    comparison_briefs = []
    for item in comparisons:
        comparison_briefs.append(
            {
                "repo": item.get("project", ""),
                "score": item.get("score", 0),
                "bucket": item.get("shortlist_bucket", ""),
                "bucket_label": item.get("shortlist_label", ""),
                "focus": item.get("suggested_focus", ""),
            }
        )

    return {
        "title": f"compare-seed-{'-'.join(name.split('/')[-1] for name in repo_names[:2]) or 'harvest'}",
        "做什么": "基于多仓库 shortlist 结果，生成一份可继续讨论的初版共识骨架。",
        "为什么做": "先把比较结果转成结构化决策输入，避免每次都从排序表手工重写共识。",
        "目标": [
            "明确哪几个仓库优先深拆",
            "区分直接用、改动用、借鉴用三层借法",
            "给后续正式 consensus 落盘提供第一版输入",
        ],
        "从哪里抄": {
            "直接用": direct_use,
            "改动用": adapt_use,
            "借鉴用": reference_only,
        },
        "怎么做": how_lines,
        "实施优先级": [
            "P0: 先深拆直接用里的仓库",
            "P1: 再补改动用里的差异化思路",
            "P2: 借鉴用仅保留背景参考",
        ],
        "不确定性": [
            "当前分组是基于排序和材料置信度的初版判断，仍需人工确认",
            "部分仓库的真正可借模块，仍要看更深一层代码或文档再拍板",
        ],
        "风险": [
            "如果直接把 shortlist 当最终方案，可能会高估排序表的确定性",
            "不同任务目标下，直接用和改动用的分层可能需要再次调整",
        ],
        "candidate_repos": comparison_briefs,
        "sources": repo_names,
    }


def score_comparison_item(item: dict, goal: str | None = None) -> tuple[int, list[str]]:
    profile_type = item.get("profile_type", "unknown")
    readiness_level = item.get("readiness_level", "medium")
    warning_count = int(item.get("warning_count", 0))

    readiness_score = {
        "high": 50,
        "medium": 32,
        "low": 12,
    }.get(readiness_level, 32)
    profile_score = _profile_priority(profile_type)
    warning_penalty = min(warning_count * 8, 24)

    score = readiness_score + profile_score - warning_penalty
    reasons = [
        f"置信度 {readiness_level} -> +{readiness_score}",
        f"仓库类型 {profile_type} -> +{profile_score}",
    ]
    if warning_penalty:
        reasons.append(f"{warning_count} 条警告 -> -{warning_penalty}")
    else:
        reasons.append("无抓取警告 -> -0")
    goal_bonus = _goal_bonus(profile_type, goal)
    if goal_bonus:
        bonus, reason = goal_bonus
        score += bonus
        reasons.append(reason)
    return score, reasons


def load_analysis_summaries() -> list[dict]:
    output_file = os.path.join(OUTPUT_DIR, "analysis_results.json")
    if not os.path.exists(output_file):
        return []
    data = load_json(output_file)
    return data.get("analyses", [])


def _to_project_name(raw: str) -> str:
    value = (raw or "").strip()
    if not value:
        return ""
    if value.startswith("http://") or value.startswith("https://"):
        parts = [part for part in urlparse(value).path.strip("/").split("/") if part]
        if len(parts) >= 2:
            return f"{parts[0]}/{parts[1].replace('.git', '')}"
        return value
    return value.replace("https://github.com/", "").replace("http://github.com/", "").strip("/")


def _has_complete_summary(item: dict) -> bool:
    return bool(item.get("profile")) and bool(item.get("readiness"))


def _summary_project_keys(item: dict) -> set[str]:
    source_context = item.get("source_context", {}) or {}
    keys = {
        _to_project_name(item.get("project", "")),
        _to_project_name(item.get("repo_name", "")),
        _to_project_name(source_context.get("project", "")),
        _to_project_name(source_context.get("repo_name", "")),
    }
    return {key for key in keys if key}


def _summary_matches_project(item: dict, project_name: str) -> bool:
    expected_project = _to_project_name(project_name)
    if not expected_project:
        return False
    if expected_project not in _summary_project_keys(item):
        return False

    source_context = item.get("source_context", {}) or {}
    harvest_file = source_context.get("harvest_file") or item.get("harvest_file", "")
    if harvest_file:
        expected_filename = f"harvest_{expected_project.replace('/', '_').replace(' ', '_')}.json"
        if os.path.basename(harvest_file) != expected_filename:
            return False
    return True


def _pick_reusable_summary(analyses: list[dict], project_name: str) -> tuple[dict | None, str]:
    candidates = [item for item in analyses if project_name in _summary_project_keys(item)]
    reusable = [
        item
        for item in candidates
        if _has_complete_summary(item) and _summary_matches_project(item, project_name)
    ]
    if reusable:
        reusable.sort(key=lambda item: item.get("generated_at", ""))
        return reusable[-1], "ok"
    if candidates:
        return None, "mismatch"
    return None, "missing"


def ensure_analysis_summary_for_repo(repo_name: str) -> tuple[dict | None, str | None]:
    project_name = _to_project_name(repo_name)
    analyses = load_analysis_summaries()
    existing, status = _pick_reusable_summary(analyses, project_name)
    if existing:
        return existing, None

    harvest_result = load_harvest_result(project_name)
    if "error" in harvest_result:
        harvest_result = harvest_repo(project_name, repo_name=project_name)
        if harvest_result.get("errors"):
            message = "; ".join(harvest_result.get("errors", [])) or "自动抓取失败"
            return None, message

    summary = save_analysis_summary(harvest_result)
    if not _summary_matches_project(summary, project_name):
        if status == "mismatch":
            return None, f"已发现旧摘要与 `{project_name}` 的 harvest 来源不一致，且自动回填后仍未修正"
        return None, f"自动生成的摘要与 `{project_name}` 的 harvest 来源不一致"
    return summary, None


def build_comparison(
    repo_names: list[str] | None = None,
    limit: int = 5,
    auto_resolve_missing: bool = True,
    goal: str | None = None,
) -> dict:
    analyses = load_analysis_summaries()
    selected_names = _normalize_repo_names(repo_names)
    auto_resolved: list[str] = []
    resolution_errors: dict[str, str] = {}
    context_mismatch_repo_names: list[str] = []
    normalized_goal = normalize_goal(goal)

    if selected_names:
        selected_projects = [_to_project_name(name) for name in selected_names]
        if auto_resolve_missing:
            for original_name, project_name in zip(selected_names, selected_projects):
                existing, status = _pick_reusable_summary(analyses, project_name)
                if existing:
                    continue
                summary, error = ensure_analysis_summary_for_repo(original_name)
                if summary:
                    auto_resolved.append(project_name)
                elif error:
                    resolution_errors[project_name] = error
                elif status == "mismatch":
                    resolution_errors[project_name] = "已存在项目名命中但来源仓库不一致的旧摘要"
            analyses = load_analysis_summaries()

        selected = []
        found_names: set[str] = set()
        for project_name in selected_projects:
            reusable, status = _pick_reusable_summary(analyses, project_name)
            if reusable:
                selected.append(reusable)
                found_names.add(project_name)
            elif status == "mismatch":
                context_mismatch_repo_names.append(project_name)
        missing = [
            name
            for name in selected_names
            if _to_project_name(name) not in found_names and _to_project_name(name) not in context_mismatch_repo_names
        ]
    else:
        selected = [
            item
            for item in analyses
            if _summary_matches_project(item, item.get("project") or item.get("repo_name", ""))
        ][-limit:]
        missing = []

    comparisons = []
    for item in selected:
        profile = item.get("profile", {})
        readiness = item.get("readiness", {})
        comparison = {
            "project": item.get("project", ""),
            "profile_type": profile.get("type", "unknown"),
            "profile_label": profile.get("label", "类型待定仓库"),
            "readiness_level": readiness.get("level", "medium"),
            "warning_count": len(item.get("warnings", [])),
            "suggested_focus": _repo_focus_by_profile(profile.get("type", "unknown")),
            "readiness_note": _readiness_note(readiness.get("level", "medium")),
        }
        score, score_reasons = score_comparison_item(comparison, normalized_goal)
        comparison["score"] = score
        comparison["score_reasons"] = score_reasons
        comparisons.append(comparison)

    comparisons.sort(
        key=lambda item: (
            item.get("score", 0),
            -item.get("warning_count", 0),
            item.get("project", ""),
        ),
        reverse=True,
    )

    payload = {
        "selected_count": len(comparisons),
        "repo_names": selected_names,
        "goal": normalized_goal,
        "auto_resolved_repo_names": sorted(set(auto_resolved)),
        "missing_repo_names": missing,
        "context_mismatch_repo_names": sorted(set(context_mismatch_repo_names)),
        "resolution_errors": resolution_errors,
        "comparisons": comparisons,
    }
    payload["shortlist"] = build_shortlist_summary(comparisons)
    payload["consensus_seed"] = build_consensus_seed(payload)
    save_json(payload, os.path.join(OUTPUT_DIR, "compare_results.json"))
    return payload


def format_comparison(payload: dict) -> str:
    comparisons = payload.get("comparisons", [])
    if not comparisons:
        return "没有可比较的分析摘要，请先运行 harvest + analyze。"

    lines = ["**批量比较结果：**", ""]
    if payload.get("goal"):
        lines.append(f"本轮排序偏好：`{payload['goal']}`")
        lines.append("")
    lines.append("| 排名 | 仓库 | 类型 | 置信度 | 分数 | 警告 | 建议拆解重点 |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for idx, item in enumerate(comparisons, 1):
        lines.append(
            f"| {idx} | {item['project']} | {item['profile_label']} | {item['readiness_level']} | {item['score']} | {item['warning_count']} | {item['suggested_focus']} |"
        )

    lines.append("")
    lines.append("## 对比备注")
    lines.append("")
    for item in comparisons:
        lines.append(f"- `{item['project']}`：{item['readiness_note']}")
        lines.append(f"  排序依据：{'；'.join(item.get('score_reasons', []))}")

    shortlist = payload.get("shortlist", {})
    if shortlist:
        lines.append("")
        lines.append("## Shortlist")
        lines.append("")
        if shortlist.get("top_pick"):
            lines.append(f"- 当前第一推荐：`{shortlist['top_pick']}`")
        if shortlist.get("priority_deep_dive"):
            lines.append(f"- 优先深拆：{', '.join(f'`{name}`' for name in shortlist['priority_deep_dive'])}")
        if shortlist.get("worth_reference"):
            lines.append(f"- 值得参考：{', '.join(f'`{name}`' for name in shortlist['worth_reference'])}")
        if shortlist.get("not_priority"):
            lines.append(f"- 暂不主推：{', '.join(f'`{name}`' for name in shortlist['not_priority'])}")

    consensus_seed = payload.get("consensus_seed", {}) or {}
    copied_from = consensus_seed.get("从哪里抄", {}) if isinstance(consensus_seed, dict) else {}
    if consensus_seed:
        lines.append("")
        lines.append("## 共识草稿输入")
        lines.append("")
        if copied_from.get("直接用"):
            lines.append(f"- 直接用：{', '.join(f'`{name}`' for name in copied_from.get('直接用', []))}")
        if copied_from.get("改动用"):
            lines.append(f"- 改动用：{', '.join(f'`{name}`' for name in copied_from.get('改动用', []))}")
        if copied_from.get("借鉴用"):
            lines.append(f"- 借鉴用：{', '.join(f'`{name}`' for name in copied_from.get('借鉴用', []))}")
        lines.append("- 这是一份初版骨架，适合直接接正式 `consensus` 落盘前的人工确认。")

    auto_resolved = payload.get("auto_resolved_repo_names", [])
    if auto_resolved:
        lines.append("")
        lines.append("## 自动补齐摘要")
        lines.append("")
        for name in auto_resolved:
            lines.append(f"- `{name}`：本轮已自动补跑摘要，可直接进入比较")

    missing = payload.get("missing_repo_names", [])
    if missing:
        lines.append("")
        lines.append("## 未命中摘要")
        lines.append("")
        for name in missing:
            error = payload.get("resolution_errors", {}).get(_to_project_name(name))
            if error:
                lines.append(f"- `{name}`：自动补摘要失败，原因：{error}")
            else:
                lines.append(f"- `{name}`：还没有现成分析摘要，先跑 `harvest + analyze` 再比较")

    mismatches = payload.get("context_mismatch_repo_names", [])
    if mismatches:
        lines.append("")
        lines.append("## 来源错配")
        lines.append("")
        for name in mismatches:
            error = payload.get("resolution_errors", {}).get(_to_project_name(name))
            if error:
                lines.append(f"- `{name}`：{error}")
            else:
                lines.append(f"- `{name}`：命中了旧摘要，但它的 harvest 来源和当前仓库名对不上，已拒绝复用")

    lines.append("")
    lines.append("这份结果已保存到 `data/compare_results.json`。")
    return "\n".join(lines)


if __name__ == "__main__":
    repo_names = sys.argv[1:]
    payload = build_comparison(repo_names)
    print(format_comparison(payload))
