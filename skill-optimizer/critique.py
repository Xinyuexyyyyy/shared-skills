"""
critique.py — Skill 锐评系统

职责：扫描 skill 目录，格式化输出锐评材料，供 Claude 在对话中完成锐评。
产出：保存 critique.md（问题清单）+ manual.md（使用手册）到 ../../output/skill-optimizer/runs/critiques/
"""
import re
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from rubric import load_skill_md


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def _normalize_skill_target(skill_path: str) -> Path:
    target = Path(skill_path).resolve()
    if target.is_file():
        return target
    return target / "SKILL.md"


def _skill_name(skill_path: str) -> str:
    target = Path(skill_path)
    if target.is_file():
        return target.parent.name
    return target.name


def _status_icon(score: Optional[Union[int, float]], max_score: Optional[Union[int, float]]) -> str:
    if score is None or not max_score:
        return "⚪"
    ratio = score / max_score
    if ratio >= 0.8:
        return "✅"
    if ratio >= 0.5:
        return "⚠️"
    return "❌"


def _find_score_payload(skill_path: str, output_dir: Path) -> Optional[dict]:
    scores_dir = output_dir / "scores"
    if not scores_dir.exists():
        return None

    target = _normalize_skill_target(skill_path)
    matches = []
    for file in sorted(scores_dir.glob("*.json")):
        try:
            payload = json.loads(file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        payload_path = payload.get("path")
        if not payload_path:
            continue
        try:
            normalized = Path(payload_path).resolve()
        except OSError:
            normalized = Path(payload_path)
        if normalized == target:
            payload["_file"] = str(file)
            matches.append(payload)

    if not matches:
        return None

    matches.sort(key=lambda item: item.get("scored_at", ""))
    return matches[-1]


def _extract_description(frontmatter: dict, body: str) -> str:
    description = (frontmatter.get("description") or "").strip()
    if description:
        return description
    for line in body.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return stripped
    return "（无描述）"


def _extract_usage_examples(body: str, limit: int = 6) -> List[str]:
    examples = []
    allowed_sections = ("用户入口", "用法", "调试命令", "状态检查")
    current_allowed = False
    allowed_level = 0
    in_code_block = False
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            level = len(stripped) - len(stripped.lstrip("#"))
            current_heading = stripped.lstrip("#").strip()
            if any(section in current_heading for section in allowed_sections):
                current_allowed = True
                allowed_level = level
            elif current_allowed and level > allowed_level:
                current_allowed = True
            else:
                current_allowed = False
                allowed_level = 0
            continue
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if not current_allowed or not stripped:
            continue
        if in_code_block:
            if stripped.startswith(("python ", "python3 ", "/")):
                examples.append(stripped)
            if len(examples) >= limit:
                break
            continue
        if stripped.startswith(("**依赖", "依赖", "相比", "后续会继续补")):
            continue
        inline = re.findall(r"`([^`]+)`", stripped)
        candidate = ""
        if stripped.startswith("- ") and inline:
            candidate = inline[0]
        elif inline and ("用户" in stripped or "直接" in stripped or "可以" in stripped):
            candidate = inline[0]
        if candidate:
            examples.append(candidate)
            if len(examples) >= limit:
                break
    return examples


def _extract_dependencies(body: str) -> List[str]:
    deps = []
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if "依赖" in stripped or stripped.lower().startswith("dependency"):
            deps.append(stripped)
    return deps[:5]


def _select_key_files(scan: dict) -> List[str]:
    files = sorted(scan.get("files", {}).keys())
    prioritized = []
    priority_names = ("SKILL.md", "README.md", "skill.py", "config.json", "package.json")
    for name in priority_names:
        if name in files:
            prioritized.append(name)
    for path in files:
        if path in prioritized:
            continue
        if path.count("/") <= 1:
            prioritized.append(path)
        if len(prioritized) >= 10:
            break
    return prioritized[:10]


def _build_issue_registry(
    skill_path: str, scan: dict, score_payload: Optional[dict]
) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    target = _normalize_skill_target(skill_path)
    body, frontmatter = load_skill_md(str(target))
    issues = []
    observations = []
    score_by_name = {}
    if score_payload:
        score_by_name = {item["name"]: item for item in score_payload.get("dimensions", [])}

    for dimension in score_payload.get("dimensions", []) if score_payload else []:
        if dimension["score"] >= dimension["max"]:
            continue
        observations.append(
            {
                "label": dimension["label"],
                "status": _status_icon(dimension["score"], dimension["max"]),
                "problem": dimension.get("reason") or "待补充",
            }
        )

    def add_issue(severity: str, title: str, file_hint: str, current: str, fix: str):
        issues.append(
            {
                "severity": severity,
                "title": title,
                "file": file_hint,
                "current": current,
                "fix": fix,
            }
        )

    frontmatter_score = score_by_name.get("frontmatter")
    if frontmatter_score and frontmatter_score["score"] < frontmatter_score["max"]:
        add_issue(
            "P1",
            "入口描述还不够像“触发说明”",
            "SKILL.md",
            frontmatter_score.get("reason", "description/metadata 信号偏弱"),
            "把 description 改成“什么时候用 + 能做什么 + 不做什么”一句话；至少补触发场景和边界，不只写能力概述。",
        )

    boundary_score = score_by_name.get("boundary")
    if boundary_score and boundary_score["score"] <= 2:
        add_issue(
            "P1",
            "失败边界说得太少，调用方不知道什么时候该停",
            "SKILL.md",
            boundary_score.get("reason", "边界处理几乎没写"),
            "补 3 类最常见失败：输入不完整、外部工具不可用、结果为空；每类都写“条件/处理/对用户怎么说”。",
        )

    checkpoint_score = score_by_name.get("checkpoint")
    if checkpoint_score and checkpoint_score["score"] <= 2:
        add_issue(
            "P1",
            "用户确认点偏少，容易一口气跑太深",
            "SKILL.md",
            checkpoint_score.get("reason", "关键节点确认不足"),
            "在路线选择、批量抓取、正式落盘前至少加 1 个确认点，写清“先展示什么，再等用户确认什么”。",
        )

    architecture_score = score_by_name.get("architecture")
    if architecture_score and architecture_score["score"] < max(8, architecture_score["max"] * 0.5):
        add_issue(
            "P1",
            "文档结构能读，但主入口和次级资料的优先级还不够收敛",
            "SKILL.md / README.md",
            architecture_score.get("reason", "主次结构不够稳"),
            "把“先看什么、后看什么、调试时再看什么”压成 3 段导航，避免调用方一上来被大段背景淹没。",
        )

    effectiveness_score = score_by_name.get("effectiveness")
    has_tests = any("test" in path.lower() or "spec" in path.lower() for path in scan.get("files", {}))
    if effectiveness_score and effectiveness_score["score"] < 15:
        fix = "补 1 轮最小实跑记录，写明输入、输出路径和是否可复用。"
        if not has_tests:
            fix += " 如果暂时没有自动化测试，至少在 README 或 SKILL.md 里固定 1 个烟雾验收命令。"
        add_issue(
            "P1",
            "实测闭环偏弱，当前更像“写出来了”而不是“用稳了”",
            "README.md / tests / 运行样本",
            effectiveness_score.get("reason", "缺少强实测信号"),
            fix,
        )

    if "README.md" not in scan.get("files", {}):
        add_issue(
            "P1",
            "缺少 README，二次接手成本偏高",
            "README.md",
            "目录里没有 README.md",
            "补一份最小 README：一句话定位、主入口、依赖、验证方式。",
        )

    if not issues and score_payload and score_payload.get("total", 100) < 70:
        add_issue(
            "P1",
            "总分已跌到待修队列，但低分原因还没被压成明确动作",
            "SKILL.md",
            f"当前总分 {score_payload.get('total')}/100",
            "先修最低分的 1 到 2 个维度，再重跑 `python3 skills/skill-optimizer/skill.py score <skill_path>` 看分数是否回升。",
        )

    p0 = [item for item in issues if item["severity"] == "P0"]
    p1 = [item for item in issues if item["severity"] == "P1"]
    return p0, p1, observations


def build_critique_report(skill_path: str, scan: dict, score_payload: Optional[dict]) -> str:
    skill_name = _skill_name(skill_path)
    target = _normalize_skill_target(skill_path)
    p0_issues, p1_issues, observations = _build_issue_registry(skill_path, scan, score_payload)

    rows = []
    for dimension in score_payload.get("dimensions", []) if score_payload else []:
        rows.append(
            "| {label} | {status} | {score}/{max_score} | {reason} |".format(
                label=dimension["label"],
                status=_status_icon(dimension["score"], dimension["max"]),
                score=dimension["score"],
                max_score=dimension["max"],
                reason=dimension.get("reason", "OK"),
            )
        )

    summary_line = "这个 skill 当前不是不能用，而是“可用但不稳”，主要问题集中在低分维度。"
    if score_payload and score_payload.get("total", 100) < 60:
        summary_line = "这个 skill 已经掉进明显待修区，先补文档边界和最小验收，再谈继续复用。"

    def format_issue_block(issue: dict, index: int) -> str:
        return (
            f"### {issue['severity']}-{index}：{issue['title']}\n\n"
            f"**文件**：`{issue['file']}`\n\n"
            f"**当前**：{issue['current']}\n\n"
            f"**修复**：{issue['fix']}\n"
        )

    p0_text = "\n".join(format_issue_block(issue, i) for i, issue in enumerate(p0_issues, 1)) or "无"
    p1_text = "\n".join(format_issue_block(issue, i) for i, issue in enumerate(p1_issues, 1)) or "无"

    observation_lines = "\n".join(
        f"- {item['label']}：{item['status']} {item['problem']}" for item in observations[:6]
    ) or "- 本轮没有额外观察。"

    return f"""# 锐评报告：{skill_name}

**生成时间**：{_now()}
**目标路径**：`{target}`
**综合评分**：{score_payload.get('total', 'N/A') if score_payload else 'N/A'}/100
**评分文件**：`{score_payload.get('_file', '未找到') if score_payload else '未找到'}`

## 结论

{summary_line}

## 检查结果

| 维度 | 状态 | 得分 | 问题 |
|------|------|------|------|
{chr(10).join(rows) if rows else '| 暂无评分 | ⚪ | N/A | 先跑 score |'}

## 观察

{observation_lines}

## P0 问题（必须修复）

{p0_text}

## P1 问题（建议修复）

{p1_text}
"""


def build_manual(skill_path: str, scan: dict, score_payload: Optional[dict]) -> str:
    skill_name = _skill_name(skill_path)
    target = _normalize_skill_target(skill_path)
    body, frontmatter = load_skill_md(str(target))
    description = _extract_description(frontmatter, body)
    usage_examples = _extract_usage_examples(body)
    dependencies = _extract_dependencies(body)
    _, p1_issues, _ = _build_issue_registry(skill_path, scan, score_payload)

    if not usage_examples:
        usage_examples = ["直接用自然语言说明你的目标，由系统在内部决定是否调用这个 skill。"]
    if not dependencies:
        dependencies = ["依赖当前工作区文件系统和该 skill 目录下现有脚本/文档。"]

    usage_rows = []
    for example in usage_examples[:5]:
        if "python " in example or "python3 " in example:
            usage_rows.append(f"| `{example}` | 内部调试/排错入口，不建议普通用户手敲 |")
        else:
            usage_rows.append(f"| `{example}` | 这是更接近真实使用的入口表达 |")

    known_issues = "\n".join(f"- {item['title']}" for item in p1_issues[:5]) or "- 当前没有额外已知问题。"

    key_files = "\n".join(f"- `{path}`" for path in _select_key_files(scan)) or "- （扫描为空）"

    return f"""# {skill_name} 使用手册

## 一句话定位

{description}

## 在系统中的位置

- 主入口文件：`{target}`
- 当前评分：{score_payload.get('total', 'N/A') if score_payload else 'N/A'}/100
- 当前批评产物：`output/skill-optimizer/runs/critiques/{skill_name}/`

## 你能做什么操作

| 你说什么 / 你执行什么 | 系统会怎么用 |
|----------------------|--------------|
{chr(10).join(usage_rows)}

## 它依赖什么

{chr(10).join(f'- {item}' for item in dependencies)}

## 关键文件

{key_files}

## 已知问题

{known_issues}

## 状态检查

| 检查项 | 命令 / 位置 |
|--------|-------------|
| 重新评分 | `python3 skills/skill-optimizer/skill.py score {target.parent}` |
| 重新生成批评 | `python3 skills/skill-optimizer/skill.py critique {target.parent}` |
| 看治理状态 | `python3 skills/skill-governance.py` |
"""


def scan_skill(skill_path: str) -> dict:
    """扫描 skill 目录，返回文件列表和关键内容"""
    skill_dir = Path(skill_path)
    if not skill_dir.exists():
        return {"exists": False}

    # 如果是文件路径，取父目录
    if skill_dir.is_file():
        skill_dir = skill_dir.parent

    files = {}
    for f in skill_dir.rglob("*"):
        if f.is_file() and not f.name.startswith(".") and not "__pycache__" in str(f):
            try:
                rel = f.relative_to(skill_dir)
                files[str(rel)] = f.read_text(encoding="utf-8")[:3000]
            except Exception:
                pass

    return {"exists": True, "skill_dir": str(skill_dir), "files": files}


def build_critique_prompt(skill_name: str, scan: dict) -> str:
    """构建锐评 prompt，供 Claude 使用"""
    file_list = "\n".join(f"- {k}" for k in scan["files"].keys())
    skill_md = scan["files"].get("SKILL.md", "（不存在）")[:3000]
    skill_py = scan["files"].get("skill.py", "（不存在）")[:2000]

    return f"""你是锐评 Agent，独立评价 skill，不美化、不客气。

## 待评价 skill：{skill_name}

### 文件结构
{file_list}

### SKILL.md（前3000字符）
---
{skill_md}
---

### skill.py（前2000字符，如有）
---
{skill_py}
---

## 锐评维度

1. **元数据**：SKILL.md 是否存在、name 是否 kebab-case、description 是否含 capabilities+triggers+context+boundaries
2. **文件结构**：skill.py 是否存在、必要文件是否完整、有无废弃文件
3. **代码质量**：import 是否正确、有无错误处理、有无 graceful fallback
4. **自我感知**：skill 能否报告自己状态、依赖的外部服务是否有健康检查、有无静默失败
5. **边界完整性**：未处理 action 有无友好提示、参数校验是否完整
6. **工作流程**：步骤是否清晰、输入输出是否明确、有无用户确认点

## 输出要求

请输出两部分内容：

### 第一部分：critique.md 内容
格式：
```markdown
# 锐评报告：{skill_name}
评分：/100

## 检查结果
| 维度 | 状态 | 问题 |
|------|------|------|
| 元数据 | ✅/❌ | ... |
...

## P0 问题（必须修复）
1. [问题] 文件：... 当前：... 修复：...

## P1 问题（建议修复）
1. ...
```

### 第二部分：manual.md 内容
格式（给非工程师看的说明书）：
```markdown
# {skill_name} 使用手册

## 一句话定位
## 在系统中的位置
## 你能做什么操作（表格）
## 它依赖什么
## 已知问题
## 状态检查
```

fix 字段给具体可执行的命令或代码片段，不是描述文字。
"""


def write_critique_report(skill_path: str, report_text: str, output_dir: Path) -> str:
    """将锐评报告写入 critique.md"""
    skill_name = _skill_name(skill_path)

    out_dir = output_dir / "critiques" / skill_name
    out_dir.mkdir(parents=True, exist_ok=True)

    report_file = out_dir / "critique.md"
    report_file.write_text(report_text, encoding="utf-8")
    return str(report_file)


def write_manual(skill_path: str, manual_text: str, output_dir: Path) -> str:
    """将使用手册写入 manual.md"""
    skill_name = _skill_name(skill_path)

    out_dir = output_dir / "critiques" / skill_name
    out_dir.mkdir(parents=True, exist_ok=True)

    manual_file = out_dir / "manual.md"
    manual_file.write_text(manual_text, encoding="utf-8")
    return str(manual_file)


def run_critique(skill_path: str, output_dir: Path) -> dict:
    """
    执行锐评流程。

    返回：
    {
        "prompt": "供 Claude 使用的完整锐评 prompt",
        "skill_dir": "skill 目录路径",
        "files_count": "扫描到的文件数",
    }

    使用方式：
    1. 调用 run_critique 获取 prompt
    2. 将 prompt 发给 Claude
    3. Claude 输出 critique.md + manual.md 内容
    4. 调用 write_critique_report 和 write_manual 保存
    """
    scan = scan_skill(skill_path)
    if not scan["exists"]:
        return {"error": f"skill 不存在: {skill_path}"}

    skill_name = _skill_name(skill_path)

    prompt = build_critique_prompt(skill_name, scan)
    score_payload = _find_score_payload(skill_path, output_dir)
    critique_text = build_critique_report(skill_path, scan, score_payload)
    manual_text = build_manual(skill_path, scan, score_payload)
    critique_file = write_critique_report(skill_path, critique_text, output_dir)
    manual_file = write_manual(skill_path, manual_text, output_dir)

    return {
        "prompt": prompt,
        "skill_name": skill_name,
        "skill_dir": scan["skill_dir"],
        "files_count": len(scan["files"]),
        "score_file": score_payload.get("_file") if score_payload else None,
        "score": score_payload.get("total") if score_payload else None,
        "critique_file": critique_file,
        "manual_file": manual_file,
    }


def clear_critique(skill_path: str, output_dir: Path) -> dict:
    """删除锐评报告"""
    skill_name = Path(skill_path).name
    if Path(skill_path).is_file():
        skill_name = Path(skill_path).parent.name

    out_dir = output_dir / "critiques" / skill_name
    removed = []
    for f in ["critique.md", "manual.md"]:
        fp = out_dir / f
        if fp.exists():
            fp.unlink()
            removed.append(f)

    return {"removed": removed, "skill": skill_name}


def health_check(skills_root: str) -> dict:
    """检查 skills 目录健康度"""
    root = Path(skills_root)
    if not root.exists():
        return {"error": f"skills 根目录不存在: {skills_root}"}

    readable = []
    broken = []
    for d in root.iterdir():
        if d.is_dir() and not d.name.startswith("."):
            try:
                list(d.iterdir())
                readable.append(d.name)
            except Exception:
                broken.append(d.name)

    # 统计有 SKILL.md 的比例
    with_skill_md = sum(1 for name in readable if (root / name / "SKILL.md").exists())

    return {
        "total": len(readable) + len(broken),
        "readable": len(readable),
        "with_skill_md": with_skill_md,
        "broken": broken,
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: critique.py <skill_path> [output_dir]")
        sys.exit(1)

    skill_path = sys.argv[1]
    default_output_dir = Path(__file__).resolve().parents[2] / "output" / "skill-optimizer" / "runs"
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else default_output_dir

    result = run_critique(skill_path, output_dir)
    if "error" in result:
        print(f"Error: {result['error']}")
        sys.exit(1)

    print(f"Skill: {result['skill_name']}")
    print(f"Files: {result['files_count']}")
    print(f"\n=== 锐评 Prompt ===\n")
    print(result["prompt"])
