#!/usr/bin/env python3
"""
自动检查点 (auto-checkpoint hook)

解决痛点: 长任务做着做着没保存就丢了。让 hook 用确定性代码自己抓
"改了哪些文件 / 跑了哪些命令 / 当前在做什么", 定期落盘成一份可读的
检查点文件 —— 无需人工确认。崩了或忘了存, 也能从检查点恢复进度。

借鉴: autopilot-cc 的核心思想 —— hook 自己写文件, 不依赖 AI 配合。

挂三个事件 (settings.json 里注册):
  - UserPromptSubmit : 记录"当前在做什么"(最近一条指令)
  - PostToolUse      : 累积改动的文件/命令; 每 N 次工具调用写一次检查点(防崩)
  - Stop             : 每轮结束写一次干净检查点

存储 (全部自动, 不碰用户的 6 个记忆文件):
  - 累积器:系统临时目录中的会话 JSON(临时,边干边攒)
  - 检查点:工作区内的 `.claude/checkpoints/checkpoint-latest.md`(覆盖式,git 里有备份)

钩子永不阻断工具 (始终退出 0); 任何异常都吞掉, 绝不影响正常使用。
"""
import sys
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

WRITE_EVERY = 10          # 每 N 次工具调用写一次检查点 (防崩)
TRIVIAL = {"ls", "cat", "echo", "pwd", "cd", "head", "tail", "which", "true"}


def _read_input():
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except Exception:
        return {}


def _accum_path(session_id):
    return Path(tempfile.gettempdir()) / f"ap-checkpoint-accum-{session_id or 'unknown'}.json"


def _load_accum(session_id):
    p = _accum_path(session_id)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"started": datetime.now().isoformat(), "task": "", "files": {},
            "commands": [], "tool_count": 0, "cwd": ""}


def _save_accum(session_id, accum):
    try:
        _accum_path(session_id).write_text(
            json.dumps(accum, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def _checkpoint_dir(cwd):
    d = Path(cwd) / ".claude" / "checkpoints"
    try:
        d.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return d


def _write_checkpoint(accum, cwd, reason):
    """把累积的状态渲染成一份人能读懂的 markdown 检查点 (覆盖式)。"""
    files = accum.get("files", {})
    cmds = accum.get("commands", [])
    task = accum.get("task", "").strip()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        "# 自动检查点 (auto-checkpoint)",
        "",
        f"> 自动生成, 无需确认。覆盖式, git 里有历史。本文件不影响你的 6 个记忆文件。",
        "",
        f"- **更新时间:** {now}",
        f"- **触发原因:** {reason}",
        f"- **本轮起于:** {accum.get('started', '?')[:19].replace('T', ' ')}",
        f"- **工作目录:** {cwd}",
        f"- **工具调用数:** {accum.get('tool_count', 0)}",
        "",
        "## 当前在做什么 (最近一条指令)",
        "",
        task if task else "_(本轮还没捕获到用户指令)_",
        "",
        f"## 改动过的文件 ({len(files)})",
        "",
    ]
    if files:
        for f, n in sorted(files.items(), key=lambda x: -x[1])[:30]:
            lines.append(f"- `{f}` ({n} 次)")
    else:
        lines.append("_(本轮还没改文件)_")

    lines += ["", f"## 跑过的关键命令 (最近 {min(len(cmds), 15)} 条)", ""]
    if cmds:
        for c in cmds[-15:]:
            lines.append(f"- `{c[:120]}`")
    else:
        lines.append("_(本轮还没跑关键命令)_")

    lines += ["", "## 恢复提示", "",
              "中断后想继续: 让我读这个文件, 我就能接上'在做什么/改了哪些文件/跑了啥'。", ""]

    content = "\n".join(lines)
    d = _checkpoint_dir(cwd)
    try:
        (d / "checkpoint-latest.md").write_text(content, encoding="utf-8")
    except Exception:
        pass


def main():
    data = _read_input()
    event = data.get("hook_event_name") or data.get("hook_event_type") or ""
    session_id = data.get("session_id") or ""
    cwd = data.get("cwd") or os.getcwd()

    accum = _load_accum(session_id)
    accum["cwd"] = cwd

    if event == "UserPromptSubmit":
        prompt = data.get("prompt") or ""
        if isinstance(prompt, str) and prompt.strip():
            accum["task"] = prompt.strip()[:500]
        _save_accum(session_id, accum)

    elif event == "PostToolUse":
        accum["tool_count"] = accum.get("tool_count", 0) + 1
        ti = data.get("tool_input") or {}
        tool = data.get("tool_name") or ""
        # 抓文件改动
        for key in ("file_path", "notebook_path"):
            fp = ti.get(key)
            if fp:
                accum.setdefault("files", {})
                accum["files"][fp] = accum["files"].get(fp, 0) + 1
        # 抓非 trivial 命令
        if tool == "Bash":
            cmd = (ti.get("command") or "").strip()
            head = cmd.split()[0] if cmd else ""
            if cmd and head not in TRIVIAL:
                accum.setdefault("commands", []).append(cmd[:200])
        _save_accum(session_id, accum)
        # 每 N 次写一份检查点 (防崩)
        if accum["tool_count"] % WRITE_EVERY == 0:
            _write_checkpoint(accum, cwd, f"每 {WRITE_EVERY} 次工具调用自动存")

    elif event == "Stop":
        _write_checkpoint(accum, cwd, "每轮结束自动存")
        _save_accum(session_id, accum)


if __name__ == "__main__":
    try:
        main()
    finally:
        sys.exit(0)  # 永不阻断工具
