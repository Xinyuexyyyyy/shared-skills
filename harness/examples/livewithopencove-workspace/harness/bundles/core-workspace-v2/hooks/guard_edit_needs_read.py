#!/usr/bin/env python3
"""PreToolUse hook: 改已存在的文件前,必须本会话 Read 过(宽松版)。

宽松版规则:
- 目标文件【不存在】(新建) → 放行(新建合法,没法先读)。
- 目标文件【已存在】但本会话没 Read 过 → 拦(防"没看就改坏")。
- 已 Read 过 → 放行。

会话内"读过哪些文件"由配套的 record_read_files.py(PostToolUse on Read)记录到
系统临时目录。本 hook 只查不写。

遵循 HOOKS-RESPONSIBILITY.md:出错静默 exit 0,绝不阻断会话。
"""
import json
import os
import sys
import tempfile
from pathlib import Path


def _read_state_path(session_id):
    return Path(tempfile.gettempdir()) / f"read-files-{session_id or 'unknown'}.json"


def _loaded_reads(session_id):
    p = _read_state_path(session_id)
    try:
        if p.exists():
            return set(json.loads(p.read_text(encoding="utf-8")))
    except Exception:
        pass
    return set()


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool = data.get("tool_name", "")
    if tool not in ("Edit", "Write", "MultiEdit"):
        sys.exit(0)

    tin = data.get("tool_input", {}) or {}
    fpath = tin.get("file_path") or tin.get("path") or ""
    if not fpath:
        sys.exit(0)

    abspath = os.path.abspath(os.path.expanduser(fpath))

    # 文件不存在 = 新建,放行
    if not os.path.exists(abspath):
        sys.exit(0)

    session_id = data.get("session_id") or ""
    reads = _loaded_reads(session_id)

    # 本会话读过(按绝对路径比对)→ 放行
    if abspath in reads or fpath in reads:
        sys.exit(0)

    # 已存在 + 没读过 → 拦
    reason = (
        f"⚠️ 改文件前先看内容:`{fpath}` 已存在,但本会话还没 Read 过它。"
        f"按红线「删改用户文件前不先看内容」,请先用 Read 工具读这个文件,确认内容后再改。"
    )
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)
