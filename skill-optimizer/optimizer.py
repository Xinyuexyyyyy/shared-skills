"""
optimizer.py — Skill 优化循环 + 棘轮机制

设计：Claude 负责编排优化流程，Python 提供工具函数：
  - 快照/恢复
  - 生成改进 prompt
  - 应用编辑
  - 重评 + 棘轮决策

存储结构（相对于 skill-optimizer 目录）：
  ../../output/skill-optimizer/runs/snapshots/{skill_name}/{ts}/SKILL.md
  ../../output/skill-optimizer/runs/scores/{skill_name}.json
  ../../output/skill-optimizer/runs/logs/round-{ts}.md
"""
import os
import re
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional


def get_skill_md_path(skill_path: str) -> Path:
    """定位 SKILL.md"""
    p = Path(skill_path)
    if p.is_file() and p.name == "SKILL.md":
        return p
    if p.is_dir():
        md = p / "SKILL.md"
        if md.exists():
            return md
    raise FileNotFoundError(f"SKILL.md not found: {skill_path}")


def get_skill_dir(skill_path: str) -> Path:
    """定位 skill 目录"""
    p = Path(skill_path)
    if p.is_file():
        return p.parent
    if p.is_dir():
        return p
    raise FileNotFoundError(f"Skill dir not found: {skill_path}")


def snapshot(skill_path: str, snapshots_dir: Path) -> Path:
    """对 skill 当前版本打快照，返回快照目录"""
    skill_dir = get_skill_dir(skill_path)
    skill_md = get_skill_md_path(skill_path)
    skill_name = skill_dir.name

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    snap_dir = snapshots_dir / skill_name / ts
    snap_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy2(skill_md, snap_dir / "SKILL.md")

    for fname in ["skill.py", "skill.js", "index.js"]:
        src = skill_dir / fname
        if src.exists():
            shutil.copy2(src, snap_dir / fname)

    return snap_dir


def restore_snapshot(skill_path: str, snap_dir: Path) -> dict:
    """从快照恢复"""
    skill_md = get_skill_md_path(skill_path)
    snap_md = snap_dir / "SKILL.md"
    if not snap_md.exists():
        return {"error": f"Snapshot SKILL.md not found: {snap_dir}"}

    shutil.copy2(snap_md, skill_md)
    return {"ok": True, "restored_from": str(snap_dir)}


def load_scores(skill_name: str, scores_dir: Path) -> dict:
    """加载评分历史"""
    f = scores_dir / f"{skill_name}.json"
    if f.exists():
        return json.loads(f.read_text())
    return {
        "skill": skill_name,
        "baseline": None,
        "rounds": [],
        "current_score": 0,
        "current_dimensions": {},
    }


def save_scores(skill_name: str, data: dict, scores_dir: Path):
    """保存评分历史"""
    f = scores_dir / f"{skill_name}.json"
    f.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def load_skill_md(skill_path: str) -> str:
    """读取 SKILL.md 内容"""
    return get_skill_md_path(skill_path).read_text(encoding="utf-8")


def write_skill_md(skill_path: str, content: str):
    """写入 SKILL.md"""
    get_skill_md_path(skill_path).write_text(content, encoding="utf-8")


# ── 改进 Prompt 生成 ─────────────────────────────────────

IMPROVEMENT_PROMPTS = {
    "frontmatter": """你是一个 SKILL.md frontmatter 专家。

请根据以下原则生成改进后的 frontmatter。

【重要】你只能输出一段纯文本，必须以 --- 开头，以 --- 结束。不要加任何解释、前言、后记。直接输出可以贴进文件的 frontmatter。

原则：
- name: 必须是规范的 kebab-case（小写+连字符），如 "skill-scorer"
- description: 必须包含三部分：(1)做什么 (2)何时用 (3)触发词（如 "当用户说...时使用"）
- 长度: description ≤ 1024 字符

当前 SKILL.md 的 name 是 "{name}"（如果不符合规范也要改正）。

输出格式（严格按照）：
---
name: xxx
description: xxx
---
""",

    "boundary": """你是一个 SKILL.md 错误处理设计专家。

评分标准（10分）：
- 包含 ≥4 个异常/边界关键词（timeout/error/limit/如果/失败/fallback）
- 有明确的"如果X失败，则Y"错误处理
- 有超时/限制说明

请生成一个 ## 边界条件 章节，包含：
1. 常见错误场景及处理方式（至少3个）
2. 每个场景：条件 → 处理方式
3. 超时和限制说明

格式要求：
- 用 ### 错误场景 作为小标题
- 每个场景格式：### 场景名\n**条件**：\n**处理**：
- 总字数 150-400 字

请直接输出完整的 ## 边界条件 章节内容，可以直接插入 SKILL.md。""",

    "checkpoint": """你是一个 SKILL.md 安全设计专家。

评分标准（7分）：
- ≥2 个用户确认点
- 关键决策前有确认提示

请生成一个 ## 检查点 章节，说明：
1. 在哪些操作前需要用户确认（至少2个）
2. 确认的格式和措辞

格式要求：
- 用编号列表，每个确认点一行
- 确认措辞要具体
- 总字数 80-200 字

请直接输出完整的 ## 检查点 章节内容，可以直接插入 SKILL.md。""",

    "workflow": """你是一个 SKILL.md 工作流设计专家。

评分标准（15分）：
- 有序号步骤（≥3步）
- 每步有明确的输入/输出说明
- 有 action 路由表

请生成一个完整的 ## 工作流 章节，包含：
1. 概述（一句话说明整体流程）
2. 步骤列表（用 1. 2. 3. 格式），每步：
   - 步骤名称
   - 输入：xxx
   - 输出：xxx
3. action 路由表（如有多个 action）

总字数 200-400 字。

请直接输出完整的 ## 工作流 章节内容，可以直接插入 SKILL.md。""",

    "specificity": """你是一个 SKILL.md 写作专家。

评分标准（15分）：
- 有代码示例（≥2个 ``` 块）
- 有具体参数/路径/格式说明
- 无模糊词（无"等等"/"之类"/"若干"）

请检查现有内容，补充：
1. 更具体的 action 参数说明
2. 一个额外的代码示例
3. 路径规范说明

请直接输出改进后的相关章节内容，不要输出整篇文档。""",

    "architecture": """你是一个 SKILL.md 架构设计专家。

评分标准（15分）：
- ≥4 个 ## 标题
- 结构层次清晰（## > ###）
- 无重复内容
- 20-500 行

请输出需要补充/修改的核心章节（每个章节输出完整内容）。
如果某个关键章节缺失（如无 ## 概述 / ## 约束 等），请生成该章节。
总字数 300-600 字。

请直接输出完整的章节内容，可以直接插入 SKILL.md。""",

    "resources": """你是一个 SKILL.md 资源整合专家。

评分标准（5分）：
- 引用路径正确
- 依赖外部服务/工具/API 有明确声明
- 引用充分（至少 3 处）

请生成一个 ## 资源 / ## 依赖 / ## 相关文件 章节，包含：
1. 核心依赖文件
2. 外部依赖（如 API key、端口号、服务地址）
3. 参考文档/链接

格式要求：
- 用表格或列表，每项注明路径和作用
- 外部依赖需注明如何获取/配置
- 总字数 80-200 字

请直接输出完整的 ## 资源 章节内容，可以直接插入 SKILL.md。""",

    "effectiveness": """实测表现维度（25分）无法通过文字改进来提升，因为它需要实际运行测试。

建议：
1. 提供 test_prompts 进行实测
2. 当前阶段先优化其他维度（结构分），实测留到运行时再做

请输出一句话说明这个维度需要实测验证，不要修改 SKILL.md。""",
}


def generate_improvement_prompt(skill_path: str, dimension_name: str, current_score: int, max_score: int) -> str:
    """
    针对最低分维度生成改进 prompt。

    返回的 prompt 可以直接发给 Claude，Claude 根据 prompt 生成改进内容。
    """
    body = load_skill_md(skill_path)

    # 解析 frontmatter 提取 name
    fm_match = re.match(r"^---\n(.*?)\n---\n", body, re.DOTALL)
    current_name = "unknown-skill"
    if fm_match:
        fm_text = fm_match.group(1)
        name_match = re.search(r"^name:\s*(.+)$", fm_text, re.MULTILINE)
        if name_match:
            current_name = name_match.group(1).strip()

    template = IMPROVEMENT_PROMPTS.get(dimension_name, "")
    if not template:
        return f"未找到维度 {dimension_name} 的改进模板。"

    prompt = template.format(name=current_name)

    # 在 prompt 前加上上下文
    full_prompt = f"""你是 SKILL.md 优化专家。

当前 skill：{current_name}
目标维度：{dimension_name}（当前得分 {current_score}/{max_score}）

## 当前 SKILL.md 内容

{body[:4000]}

---

{prompt}
"""
    return full_prompt


def apply_edit(skill_path: str, edit_content: str, dimension_name: str) -> tuple[str, str]:
    """
    将 Claude 生成的改进内容应用到 SKILL.md。

    Args:
        edit_content: Claude 生成的改进内容
        dimension_name: 目标维度名称

    Returns:
        (new_body, change_summary)
    """
    body = load_skill_md(skill_path)

    if dimension_name == "frontmatter":
        # 替换 frontmatter 块
        fm_match = re.search(r"(---.*?---\n)", edit_content, re.DOTALL)
        if fm_match:
            new_body = re.sub(r"^---\n.*?\n---\n", fm_match.group(1), body, count=1, flags=re.DOTALL)
            return new_body, "frontmatter 已更新"
        return body, "frontmatter 替换失败（内容不含 --- 块）"

    elif dimension_name == "boundary":
        return _replace_or_append_section(body, "边界条件", edit_content)

    elif dimension_name == "checkpoint":
        return _replace_or_append_section(body, "检查点", edit_content)

    elif dimension_name == "workflow":
        return _replace_or_append_section(body, "工作流", edit_content)

    elif dimension_name == "architecture":
        # architecture 增强：检查缺失章节并补充
        if "## 概述" not in body and "## 概览" not in body and "概述" in edit_content:
            body = "## 概述\n\n" + edit_content + "\n\n" + body
            return body, "architecture: 已补充概述章节并增强"
        return _replace_or_append_section(body, "架构", edit_content)

    elif dimension_name == "resources":
        return _replace_or_append_section(body, "资源", edit_content)

    elif dimension_name == "specificity":
        # specificity 是增强现有内容，直接追加
        new_body = body.strip() + "\n\n" + edit_content.strip()
        return new_body, "specificity 内容已追加"

    else:
        new_body = body.strip() + "\n\n" + edit_content.strip()
        return new_body, f"{dimension_name} 内容已追加"


def _replace_or_append_section(body: str, section_keyword: str, new_content: str) -> tuple[str, str]:
    """替换或追加章节"""
    pattern = re.compile(rf"##\s*{re.escape(section_keyword)}.*?(?=\n## |\Z)", re.IGNORECASE | re.DOTALL)
    if pattern.search(body):
        new_body = pattern.sub(new_content.strip(), body, count=1)
        return new_body, f"{section_keyword} 章节已更新"
    else:
        new_body = body.strip() + "\n\n" + new_content.strip()
        return new_body, f"{section_keyword} 章节已追加"


def run_optimization_round(
    skill_path: str,
    dimension_name: str,
    edit_content: str,
    scores_dir: Path,
    snapshots_dir: Path,
    logs_dir: Path,
) -> dict:
    """
    执行一轮优化：应用编辑 → 重评 → 棘轮决策。

    调用方（Claude）需要：
    1. 先调用 snapshot() 打快照
    2. 调用 generate_improvement_prompt() 获取 prompt
    3. 根据 prompt 生成 edit_content
    4. 调用本函数应用编辑并重评

    Returns:
        {
            "old_score": float,
            "new_score": float,
            "improvement": "keep" | "revert",
            "change_summary": str,
        }
    """
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from rubric import score_skill

    skill_dir = get_skill_dir(skill_path)
    skill_name = skill_dir.name

    # 加载当前评分
    results = load_scores(skill_name, scores_dir)
    old_score = results.get("current_score", 0)

    # 应用编辑
    new_body, change_summary = apply_edit(skill_path, edit_content, dimension_name)
    write_skill_md(skill_path, new_body)

    # 重评
    new_result = score_skill(skill_path)
    new_score = new_result["total"]

    # 棘轮决策
    if new_score > old_score:
        improvement = "keep"
        results["current_score"] = new_score
        results["current_dimensions"] = {
            d["name"]: d["score"] for d in new_result["dimensions"]
        }
    else:
        improvement = "revert"

    # 记录
    round_record = {
        "round": len(results.get("rounds", [])) + 1,
        "at": datetime.now().isoformat(),
        "target_dimension": dimension_name,
        "old_score": old_score,
        "new_score": new_score,
        "change_summary": change_summary,
        "improvement": improvement,
    }
    results["rounds"].append(round_record)
    save_scores(skill_name, results, scores_dir)

    # 日志
    log_file = logs_dir / f"round-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
    log_file.write_text(
        f"# Round {round_record['round']} | {skill_name}\n\n"
        f"**目标维度**: {dimension_name}\n"
        f"**改动**: {change_summary}\n"
        f"**分数变化**: {old_score} → {new_score}\n"
        f"**结果**: {'保留' if improvement == 'keep' else '回滚'}\n",
        encoding="utf-8"
    )

    return {
        "old_score": old_score,
        "new_score": new_score,
        "improvement": improvement,
        "change_summary": change_summary,
        "skill": skill_name,
    }


def get_optimization_status(skill_name: str, scores_dir: Path) -> dict:
    """查看优化状态"""
    results = load_scores(skill_name, scores_dir)
    return {
        "skill": skill_name,
        "has_baseline": results.get("baseline") is not None,
        "current_score": results.get("current_score", 0),
        "rounds_count": len(results.get("rounds", [])),
    }


if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    output_dir = Path(__file__).resolve().parents[2] / "output" / "skill-optimizer" / "runs"

    if not args:
        print("Usage:")
        print("  optimizer.py prompt <skill_path> <dimension>")
        print("  optimizer.py apply <skill_path> <dimension> <edit_file>")
        sys.exit(1)

    cmd = args[0]

    if cmd == "prompt" and len(args) >= 3:
        skill_path = args[1]
        dim = args[2]
        prompt = generate_improvement_prompt(skill_path, dim, 0, 10)
        print(prompt)

    elif cmd == "apply" and len(args) >= 4:
        skill_path = args[1]
        dim = args[2]
        edit_file = args[3]
        edit_content = Path(edit_file).read_text(encoding="utf-8")
        result = run_optimization_round(
            skill_path, dim, edit_content,
            output_dir / "scores",
            output_dir / "snapshots",
            output_dir / "logs",
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))

    else:
        print(f"Unknown command: {cmd}")
