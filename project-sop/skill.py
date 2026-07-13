"""Project SOP Skill — 项目全流程管理"""
import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

WORKSPACE = Path.home() / "DailyWork2"
BLUEPRINTS = WORKSPACE / "task_draft" / "project-sop"
MEMORY_FILE = WORKSPACE / ".claude" / "memory" / "project-sop-index.md"


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _date() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


# ─────────────────────────────────────────────────────────────
# 辅助：读 state.yaml
# ─────────────────────────────────────────────────────────────

def _read_state(project: str) -> dict:
    """读取项目 state.yaml"""
    state_path = BLUEPRINTS / project / "state" / "state.yaml"
    if not state_path.exists():
        return {}
    content = state_path.read_text(encoding="utf-8")
    state = {}
    for line in content.splitlines():
        if ":" in line and not line.startswith(" "):
            key, val = line.split(":", 1)
            state[key.strip()] = val.strip()
    return state


def _write_state(project: str, state: dict):
    """写入 state.yaml"""
    state_path = BLUEPRINTS / project / "state" / "state.yaml"
    lines = [f"{k}: {v}" for k, v in state.items()]
    state_path.write_text("\n".join(lines), encoding="utf-8")


def _advance_node(project: str, target_node: str):
    """推进到指定节点"""
    state = _read_state(project)
    state["current_node"] = target_node
    _write_state(project, state)


def _ensure_dir(project: str, subdir: str) -> Path:
    p = BLUEPRINTS / project / subdir
    p.mkdir(parents=True, exist_ok=True)
    return p


# ─────────────────────────────────────────────────────────────
# Action: new — 建立项目
# ─────────────────────────────────────────────────────────────

def _update_registry(project: str, action: str, **kwargs):
    """DailyWork2 does not update the legacy OpenClaw registry."""
    return


# ─────────────────────────────────────────────────────────────
# Action: new — 建立项目（含 registry 自动登记）
# ─────────────────────────────────────────────────────────────

def _do_new(name: str, description: str = "") -> dict:
    project_dir = BLUEPRINTS / name
    if project_dir.exists():
        return {"reply": f"❌ 项目已存在：{name}"}

    # 创建目录结构
    (project_dir / "blueprint").mkdir(parents=True)
    (project_dir / "logs").mkdir(parents=True)
    (project_dir / "state").mkdir(parents=True)

    # overview.md
    overview = project_dir / "blueprint" / "overview.md"
    overview.write_text(
        f"# {name}\n\n**创建时间**：{_now()}\n**描述**：{description}\n\n",
        encoding="utf-8",
    )

    # progress.md
    progress = project_dir / "blueprint" / "progress.md"
    progress.write_text(
        f"# {name} — 进度\n\n**状态**：🟡 进行中\n**创建时间**：{_now()}\n\n",
        encoding="utf-8",
    )

    # state.yaml
    state = project_dir / "state" / "state.yaml"
    state.write_text(
        f"project: {name}\n"
        f"description: {description}\n"
        f"created_at: {_now()}\n"
        f"current_node: ①\n",
        encoding="utf-8",
    )

    # 更新 MEMORY.md 项目索引
    _add_to_memory_index(name, description)

    # 🆕 自动登记到 registry
    _update_registry(name, "new")

    return {
        "reply": (
            f"✅ 项目已建立：{name}\n"
            f"📁 {project_dir}/\n"
            f"描述：{description}\n\n"
            f"输入 `brainstorm` 或 `聊聊想法` 进入节点②头脑风暴。"
        ),
        "project": name,
    }


# ─────────────────────────────────────────────────────────────
# Action: brainstorm — 头脑风暴
# ─────────────────────────────────────────────────────────────

def _do_brainstorm(project: str, content: str = "") -> dict:
    if not (BLUEPRINTS / project).exists():
        return {"reply": f"❌ 项目不存在：{project}"}

    log_path = _ensure_dir(project, "logs") / f"brainstorm-{_date()}.md"
    text = (
        f"# 头脑风暴 — {project}\n\n"
        f"**时间**：{_now()}\n\n"
        "## 用户想法\n\n"
        f"{content or '（用户口述）'}\n\n"
        "## 轮1 — 高温暖场（发散）\n\n"
        "列出3个以上不同方向，每条方向包含：\n"
        "- 方案名称\n"
        "- 核心思路\n"
        "- 潜在风险或分歧点\n\n"
        "（AI 在此不发评估，只扩边）\n\n"
        "## 轮2 — 低温收缩（整合）\n\n"
        "（AI 整合分歧，给出推荐方向，说明理由）\n\n"
        "## 质量自评\n"
        "- 总分：X/10\n"
        "- 风险点：（2-3条）\n"
        '- 能不能过：（>=6分写"能过，进入 plan"，<6分写"不过，需重跑"）\n'
    )
    log_path.write_text(text, encoding="utf-8")
    # 注意：不自动推进节点，等用户确认质量 >= 6 才推进

    return {
        "reply": (
            "✅ 头脑风暴已记录\n"
            f"📄 {log_path.name}\n\n"
            "请填写末尾的【质量自评】：几分？风险点？能不能过？\n"
            "评分 >= 6 才能继续（输入 `quality OK` 或直接给分）。\n"
            "评分 < 6 则重跑 brainstorm。"
        ),
        "log": str(log_path),
    }


# ─────────────────────────────────────────────────────────────
# Action: quality — 质量确认，推进节点
# ─────────────────────────────────────────────────────────────

def _do_quality(project: str, score: float = 0) -> dict:
    """用户确认 brainstorm 质量后调用。"""
    if not (BLUEPRINTS / project).exists():
        return {"reply": f"❌ 项目不存在：{project}"}
    if score < 6:
        return {"reply": f"❌ 质量评分 {score} < 6，不满足门槛。请先改进 brainstorm 内容，再评。"}
    _advance_node(project, "②")
    return {"reply": f"✅ 质量确认（{score}/10），节点已推进到②。\n输入 `plan` 或 `拆任务` 进入节点③。"}


# Action: plan — 落实任务
# ─────────────────────────────────────────────────────────────

def _do_plan(project: str, content: str = "") -> dict:
    if not (BLUEPRINTS / project).exists():
        return {"reply": f"❌ 项目不存在：{project}"}

    progress_path = BLUEPRINTS / project / "blueprint" / "progress.md"
    existing = progress_path.read_text(encoding="utf-8") if progress_path.exists() else ""

    new_section = f"\n## 任务清单\n\n**时间**：{_now()}\n\n{content or '（任务待填充）'}\n"
    progress_path.write_text(existing + new_section, encoding="utf-8")
    _advance_node(project, "③")

    return {
        "reply": (
            f"✅ 任务清单已写入 progress.md\n"
            f"输入 `blueprint` 或 `定方案` 进入节点④。"
        ),
    }


# ─────────────────────────────────────────────────────────────
# Action: blueprint — 写蓝图
# ─────────────────────────────────────────────────────────────

def _do_blueprint(project: str, content: str = "") -> dict:
    if not (BLUEPRINTS / project).exists():
        return {"reply": f"❌ 项目不存在：{project}"}

    progress_path = BLUEPRINTS / project / "blueprint" / "progress.md"
    existing = progress_path.read_text(encoding="utf-8") if progress_path.exists() else ""

    new_section = f"\n## 验收标准\n\n**时间**：{_now()}\n\n{content or '（验收标准待填充）'}\n"
    progress_path.write_text(existing + new_section, encoding="utf-8")
    _advance_node(project, "④")

    return {
        "reply": (
            f"✅ 蓝图验收标准已补充 progress.md\n"
            f"输入 `develop` 或 `开始干活` 进入节点⑤。"
        ),
    }


# ─────────────────────────────────────────────────────────────
# Action: develop — 开始开发
# ─────────────────────────────────────────────────────────────

def _do_develop(project: str, note: str = "") -> dict:
    if not (BLUEPRINTS / project).exists():
        return {"reply": f"❌ 项目不存在：{project}"}

    log_path = _ensure_dir(project, "logs") / f"round-{_date()}.md"
    text = f"# 开发日志 — {project}\n\n**时间**：{_now()}\n\n## 本轮说明\n\n{note or '（开发中）'}\n\n## 关键决策\n\n（记录开发过程中的决策）\n\n## 遇到的问题\n\n（记录问题及解决方案）\n"
    log_path.write_text(text, encoding="utf-8")
    _advance_node(project, "⑤")

    # 🆕 更新 registry 活跃状态
    _update_registry(project, "develop")

    return {
        "reply": (
            f"✅ 开发日志已创建\n"
            f"📄 {log_path.name}\n\n"
            f"输入 `test` 或 `结束开发` 进入节点⑥。"
        ),
        "log": str(log_path),
    }


# ─────────────────────────────────────────────────────────────
# Action: test — 测试debug
# ─────────────────────────────────────────────────────────────

def _do_test(project: str, content: str, debug: bool = False) -> dict:
    if not (BLUEPRINTS / project).exists():
        return {"reply": f"❌ 项目不存在：{project}"}

    prefix = "debug" if debug else "test"
    log_path = _ensure_dir(project, "logs") / f"{prefix}-{_date()}.md"
    text = f"# {prefix.title()} — {project}\n\n**时间**：{_now()}\n\n## 内容\n\n{content}\n"
    log_path.write_text(text, encoding="utf-8")
    _advance_node(project, "⑥")

    return {
        "reply": (
            f"✅ {'调试' if debug else '测试'}记录已写入\n"
            f"📄 {log_path.name}\n\n"
            f"输入 `close` 或 `项目结束` 进入节点⑦收尾。"
        ),
        "log": str(log_path),
    }


# ─────────────────────────────────────────────────────────────
# Action: close — 收尾（不含归档，归档由用户单独触发）
# ─────────────────────────────────────────────────────────────

def _do_close(project: str) -> dict:
    if not (BLUEPRINTS / project).exists():
        return {"reply": f"❌ 项目不存在：{project}"}

    # 锁定 progress.md
    progress_path = BLUEPRINTS / project / "blueprint" / "progress.md"
    if progress_path.exists():
        existing = progress_path.read_text(encoding="utf-8")
        if "## 🔒 已锁定" not in existing:
            progress_path.write_text(existing + "\n\n## 🔒 已锁定\n**锁定时间**："
                                      + _now() + "\n", encoding="utf-8")

    # 更新 state
    _advance_node(project, "⑦")

    # 更新 MEMORY.md 状态
    _update_memory_status(project, "✅ 已完成")

    # 🆕 更新 registry 为完成状态
    _update_registry(project, "close")

    return {
        "reply": (
            f"✅ 项目 {project} 已收尾\n"
            f"🔒 progress.md 已锁定\n"
            f"📊 MEMORY.md 状态已更新为已完成\n\n"
            f"建议运行 `归档项目日志` 将 logs 归并到 progress.md。"
        ),
    }


# ─────────────────────────────────────────────────────────────
# Action: archive — 调用 project-archiver 归档日志
# ─────────────────────────────────────────────────────────────

def _do_archive(project: str) -> dict:
    if not (BLUEPRINTS / project).exists():
        return {"reply": f"❌ 项目不存在：{project}"}

    try:
        import subprocess, json
        archiver_script = Path(__file__).parent.parent / "project-archiver" / "skill.py"
        result = subprocess.run(
            ["python3", str(archiver_script), "archive", project],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            return {"reply": result.stdout.strip()}
        else:
            return {"reply": f"❌ 归档失败：{result.stderr.strip() or result.stdout.strip()}"}
    except Exception as e:
        return {"reply": f"❌ project-archiver 调用失败：{e}，请手动归档。"}


# ─────────────────────────────────────────────────────────────
# Action: status — 查询状态
# ─────────────────────────────────────────────────────────────

def _do_status(project: str) -> dict:
    if not (BLUEPRINTS / project).exists():
        return {"reply": f"❌ 项目不存在：{project}"}

    state = _read_state(project)
    current = state.get("current_node", "①")
    description = state.get("description", "")

    # 统计 logs
    logs_dir = BLUEPRINTS / project / "logs"
    log_count = len(list(logs_dir.glob("*.md"))) if logs_dir.is_dir() else 0

    lines = [
        f"**项目**：{project}",
        f"**描述**：{description}",
        f"**当前节点**：{current}",
        f"**日志数**：{log_count} 条",
    ]

    return {"reply": "\n".join(lines)}


# ─────────────────────────────────────────────────────────────
# 辅助：MEMORY.md 操作
# ─────────────────────────────────────────────────────────────

def _add_to_memory_index(name: str, description: str):
    """在 DailyWork2 project-sop 索引加一条"""
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not MEMORY_FILE.exists():
        MEMORY_FILE.write_text(
            "# Project SOP Index\n\n"
            "| Project | Status | Home |\n"
            "|---|---|---|\n",
            encoding="utf-8",
        )
    text = MEMORY_FILE.read_text(encoding="utf-8")
    new_line = f"| {name} | in-progress | `task_draft/project-sop/{name}/` |"
    marker = "|---|---|---|"
    if new_line not in text:
        text = text.replace(marker, f"{marker}\n{new_line}")
        MEMORY_FILE.write_text(text, encoding="utf-8")


def _update_memory_status(name: str, status: str):
    """更新 project-sop 索引项目状态"""
    if not MEMORY_FILE.exists():
        return
    import re
    text = MEMORY_FILE.read_text(encoding="utf-8")
    pattern = rf"(\|\s*{re.escape(name)}\s*\|\s*)[^\|]+(\s*\|)"
    new_text = re.sub(pattern, rf"\g<1>{status}\g<2>", text)
    MEMORY_FILE.write_text(new_text, encoding="utf-8")


# ─────────────────────────────────────────────────────────────
# 触发词检测
# ─────────────────────────────────────────────────────────────

NODE_SIGNALS = {
    "new": ["新项目", "建个项目", "new project", "创建项目", "开个新项目"],
    "brainstorm": ["brainstorm", "头脑风暴", "聊聊想法", "聊聊这个项目", "说说想法"],
    "plan": ["拆任务", "落实", "写计划", "任务清单", "plan", "做计划"],
    "blueprint": ["蓝图", "写蓝图", "写个蓝图", "定方案", "blueprint", "设计方案", "写方案"],
    "develop": ["开始开发", "develop", "开始干活", "干活", "写代码"],
    "test": ["测试", "debug", "调试", "test", "跑一下"],
    "close": ["close", "项目结束", "收尾", "项目结束了", "完工"],
    "archive": ["归档", "归档项目", "日志归档"],
    "status": ["项目状态", "进度", "status", "当前情况"],
}


def detect_action(text: str) -> str:
    """从文本检测应该触发哪个 action"""
    t = text.lower()
    for action, signals in NODE_SIGNALS.items():
        for sig in signals:
            if sig.lower() in t:
                return action
    return "unknown"


# ─────────────────────────────────────────────────────────────
# Skill 操作路由
# ─────────────────────────────────────────────────────────────

def handle(action: str, params: dict) -> dict:
    """统一路由入口"""
    # 路由分发
    if action == "new":
        return _do_new(params.get("name", ""), params.get("description", ""))
    elif action == "brainstorm":
        return _do_brainstorm(params.get("project", ""), params.get("content", ""))
    elif action == "plan":
        return _do_plan(params.get("project", ""), params.get("content", ""))
    elif action == "blueprint":
        return _do_blueprint(params.get("project", ""), params.get("content", ""))
    elif action == "develop":
        return _do_develop(params.get("project", ""), params.get("note", ""))
    elif action == "test":
        return _do_test(params.get("project", ""), params.get("content", ""), params.get("debug", False))
    elif action == "close":
        return _do_close(params.get("project", ""))
    elif action == "status":
        return _do_status(params.get("project", ""))
    elif action == "archive":
        return _do_archive(params.get("project", ""))
    elif action == "quality":
        return _do_quality(params.get("project", ""), params.get("score", 0))
    elif action == "detect":
        detected = detect_action(params.get("text", ""))
        return {"action": detected}
    else:
        return {"reply": f"未知操作：{action}，支持的：new / brainstorm / plan / blueprint / develop / test / close / archive / status"}
