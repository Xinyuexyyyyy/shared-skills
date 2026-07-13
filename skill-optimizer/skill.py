#!/usr/bin/env python3
"""
skill-optimizer — 统一入口

整合 critique（锐评）+ rubric（评分）+ optimizer（优化）+ execution_logger（日志）

用法：
  python skill.py score <skill_path>              — 8维评分
  python skill.py critique <skill_path>           — 扫描，落盘 critique/manual，并附带深评 prompt
  python skill.py optimize <skill_path> <dim> <edit_file>  — 应用编辑 + 棘轮
  python skill.py prompt <skill_path> <dim>       — 生成改进 prompt
  python skill.py snapshot <skill_path>           — 打快照
  python skill.py restore <skill_path> <snap_dir> — 从快照恢复
  python skill.py status <skill_name>             — 查看优化状态
  python skill.py clear-critique <skill_path>     — 删除锐评报告
  python skill.py health <skills_root>            — skills 目录健康检查
  python skill.py log <skill> <action> <result>   — 记录执行日志

环境变量：
  SKILL_OPTIMIZER_OUTPUT — 输出目录，默认 ../../output/skill-optimizer/runs
"""
import os
import sys
import json
import re
import hashlib
from pathlib import Path

# 输出目录
DEFAULT_OUTPUT_DIR = (
    Path(__file__).resolve().parents[2] / "output" / "skill-optimizer" / "runs"
)
OUTPUT_DIR = Path(os.environ.get("SKILL_OPTIMIZER_OUTPUT", DEFAULT_OUTPUT_DIR))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(Path(__file__).parent))


def _normalize_skill_target(skill_path: str) -> Path:
    target = Path(skill_path).resolve()
    if target.is_file():
        return target
    return target / "SKILL.md"


def _score_filename(skill_path: str) -> str:
    target = _normalize_skill_target(skill_path)
    stem = target.parent.name if target.name == "SKILL.md" else target.stem
    safe_stem = re.sub(r"[^A-Za-z0-9_-]+", "-", stem).strip("-") or "skill"
    digest = hashlib.sha1(str(target).encode("utf-8")).hexdigest()[:8]
    return f"{safe_stem}-{digest}.json"


def _save_score_result(skill_path: str, result: dict) -> Path:
    scores_dir = OUTPUT_DIR / "scores"
    scores_dir.mkdir(parents=True, exist_ok=True)
    payload = dict(result)
    payload["scored_at"] = payload.get("scored_at") or __import__("datetime").datetime.now().isoformat()
    payload["path"] = str(_normalize_skill_target(skill_path))
    score_file = scores_dir / _score_filename(skill_path)
    score_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return score_file


def cmd_score(args):
    from rubric import score_skill, format_score_report
    skill_path = args[0] if args else "."
    result = score_skill(skill_path)
    score_file = _save_score_result(skill_path, result)
    print(format_score_report(result))
    print(f"\n评分文件: {score_file}")
    return result


def cmd_critique(args):
    from critique import run_critique
    if not args:
        print("Usage: skill.py critique <skill_path>")
        sys.exit(1)
    skill_path = args[0]
    result = run_critique(skill_path, OUTPUT_DIR)
    if "error" in result:
        print(f"Error: {result['error']}")
        sys.exit(1)
    print(f"Skill: {result['skill_name']}")
    print(f"Files: {result['files_count']}")
    print(f"Score: {result.get('score', 'N/A')}")
    print(f"Critique: {result['critique_file']}")
    print(f"Manual: {result['manual_file']}")
    if result.get("score_file"):
        print(f"Score file: {result['score_file']}")
    print(f"\n=== 锐评 Prompt（如需人工深评，可将此 prompt 发给 Claude） ===\n")
    print(result["prompt"])
    return result


def cmd_prompt(args):
    """生成改进 prompt"""
    from optimizer import generate_improvement_prompt
    if len(args) < 2:
        print("Usage: skill.py prompt <skill_path> <dimension>")
        print("Dimensions: frontmatter, workflow, boundary, checkpoint, specificity, resources, architecture")
        sys.exit(1)
    skill_path = args[0]
    dim = args[1]
    prompt = generate_improvement_prompt(skill_path, dim, 0, 10)
    print(prompt)


def cmd_optimize(args):
    """应用编辑 + 棘轮"""
    from optimizer import run_optimization_round
    if len(args) < 3:
        print("Usage: skill.py optimize <skill_path> <dimension> <edit_file>")
        sys.exit(1)
    skill_path = args[0]
    dim = args[1]
    edit_file = args[2]
    edit_content = Path(edit_file).read_text(encoding="utf-8")
    result = run_optimization_round(
        skill_path, dim, edit_content,
        OUTPUT_DIR / "scores",
        OUTPUT_DIR / "snapshots",
        OUTPUT_DIR / "logs",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_snapshot(args):
    from optimizer import snapshot
    if not args:
        print("Usage: skill.py snapshot <skill_path>")
        sys.exit(1)
    skill_path = args[0]
    snap_dir = snapshot(skill_path, OUTPUT_DIR / "snapshots")
    print(f"Snapshot saved: {snap_dir}")


def cmd_restore(args):
    from optimizer import restore_snapshot
    if len(args) < 2:
        print("Usage: skill.py restore <skill_path> <snap_dir>")
        sys.exit(1)
    skill_path = args[0]
    snap_dir = Path(args[1])
    result = restore_snapshot(skill_path, snap_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_status(args):
    from optimizer import get_optimization_status
    if not args:
        print("Usage: skill.py status <skill_name>")
        sys.exit(1)
    skill_name = args[0]
    result = get_optimization_status(skill_name, OUTPUT_DIR / "scores")
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_clear_critique(args):
    from critique import clear_critique
    if not args:
        print("Usage: skill.py clear-critique <skill_path>")
        sys.exit(1)
    result = clear_critique(args[0], OUTPUT_DIR)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_health(args):
    from critique import health_check
    skills_root = args[0] if args else str(Path(__file__).parent.parent)
    result = health_check(skills_root)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_log(args):
    from execution_logger import log
    if len(args) < 3:
        print("Usage: skill.py log <skill> <action> <result> [duration_ms]")
        sys.exit(1)
    skill = args[0]
    action = args[1]
    result = args[2]
    duration_ms = int(args[3]) if len(args) > 3 else 0
    eid = log(OUTPUT_DIR, skill, action, result, duration_ms=duration_ms)
    print(f"Logged: {eid}")


COMMANDS = {
    "score": cmd_score,
    "critique": cmd_critique,
    "prompt": cmd_prompt,
    "optimize": cmd_optimize,
    "snapshot": cmd_snapshot,
    "restore": cmd_restore,
    "status": cmd_status,
    "clear-critique": cmd_clear_critique,
    "health": cmd_health,
    "log": cmd_log,
}


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    handler = COMMANDS.get(cmd)
    if not handler:
        print(f"Unknown command: {cmd}")
        print(f"Available: {', '.join(COMMANDS.keys())}")
        sys.exit(1)

    handler(args)


if __name__ == "__main__":
    main()
