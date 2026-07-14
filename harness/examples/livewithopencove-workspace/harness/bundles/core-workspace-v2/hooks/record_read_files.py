#!/usr/bin/env python3
"""PostToolUse hook: 记录本会话 Read 过的文件路径。

配套 guard_edit_needs_read.py 使用:Read 一个文件后,把它的绝对路径
追加进系统临时状态。改文件守卫据此判断"读过没"。

遵循 HOOKS-RESPONSIBILITY.md:只写自己的临时状态、出错静默 exit 0。
"""
import json
import os
import sys
import tempfile
from pathlib import Path


def _read_state_path(session_id):
    return Path(tempfile.gettempdir()) / f"read-files-{session_id or 'unknown'}.json"


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    if data.get("tool_name", "") != "Read":
        sys.exit(0)

    tin = data.get("tool_input", {}) or {}
    fpath = tin.get("file_path") or tin.get("path") or ""
    if not fpath:
        sys.exit(0)

    abspath = os.path.abspath(os.path.expanduser(fpath))
    session_id = data.get("session_id") or ""
    p = _read_state_path(session_id)

    try:
        existing = set()
        if p.exists():
            existing = set(json.loads(p.read_text(encoding="utf-8")))
        existing.add(abspath)
        p.write_text(json.dumps(sorted(existing)), encoding="utf-8")
    except Exception:
        pass

    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)
