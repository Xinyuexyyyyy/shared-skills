#!/usr/bin/env python3
"""Behavior tests for the portable hook bundle."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOKS = ROOT / "bundles" / "core-workspace-v2" / "hooks"


def run_hook(name: str, payload: dict) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(HOOKS / name)],
        input=json.dumps(payload, ensure_ascii=False),
        text=True,
        capture_output=True,
        check=False,
    )


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_injection() -> None:
    result = run_hook("inject_output_control.py", {"hook_event_name": "UserPromptSubmit"})
    require(result.returncode == 0, "inject hook must not block")
    payload = json.loads(result.stdout)
    context = payload["hookSpecificOutput"]["additionalContext"]
    require("## 5.1 文档产物渲染验收规则" in context, "full output-control skill was not injected")
    require("## 7. 触发稳定性" in context, "trigger-stability rules were not injected")


def test_overexecute_guard() -> None:
    session = f"harness-{uuid.uuid4()}"
    record = run_hook(
        "record_user_prompt.py",
        {"session_id": session, "prompt": "这个方案可以吗？"},
    )
    require(record.returncode == 0, "prompt recorder failed")
    blocked = run_hook(
        "guard_overexecute.py",
        {
            "session_id": session,
            "tool_name": "Write",
            "tool_input": {"file_path": "proposal.md"},
        },
    )
    require("deny" in blocked.stdout, "question-only write was not denied")

    run_hook(
        "record_user_prompt.py",
        {"session_id": session, "prompt": "把这个方案写入 proposal.md"},
    )
    allowed = run_hook(
        "guard_overexecute.py",
        {
            "session_id": session,
            "tool_name": "Write",
            "tool_input": {"file_path": "proposal.md"},
        },
    )
    require(not allowed.stdout.strip(), "explicit write intent should be allowed")


def test_read_before_edit_guard() -> None:
    session = f"harness-{uuid.uuid4()}"
    with tempfile.TemporaryDirectory() as temporary:
        target = Path(temporary) / "existing.md"
        target.write_text("existing\n", encoding="utf-8")
        blocked = run_hook(
            "guard_edit_needs_read.py",
            {
                "session_id": session,
                "tool_name": "Edit",
                "tool_input": {"file_path": str(target)},
            },
        )
        require("deny" in blocked.stdout, "unread existing file was not denied")
        run_hook(
            "record_read_files.py",
            {
                "session_id": session,
                "tool_name": "Read",
                "tool_input": {"file_path": str(target)},
            },
        )
        allowed = run_hook(
            "guard_edit_needs_read.py",
            {
                "session_id": session,
                "tool_name": "Edit",
                "tool_input": {"file_path": str(target)},
            },
        )
        require(not allowed.stdout.strip(), "read existing file should be editable")


def test_dangerous_command_guard() -> None:
    result = run_hook(
        "guard_dangerous_bash.py",
        {"tool_name": "Bash", "tool_input": {"command": "git reset --hard HEAD~1"}},
    )
    require("deny" in result.stdout, "dangerous command was not denied")


def test_checkpoint_and_memory_nudge() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        workspace = Path(temporary)
        checkpoint = run_hook(
            "auto_checkpoint.py",
            {"hook_event_name": "Stop", "session_id": str(uuid.uuid4()), "cwd": str(workspace)},
        )
        require(checkpoint.returncode == 0, "checkpoint hook blocked")
        require(
            (workspace / ".claude" / "checkpoints" / "checkpoint-latest.md").is_file(),
            "checkpoint was not created",
        )

        index = workspace / ".claude" / "memory" / "tasks" / "INDEX.md"
        output = workspace / "output"
        index.parent.mkdir(parents=True, exist_ok=True)
        output.mkdir(parents=True, exist_ok=True)
        index.write_text("# Task Index\n", encoding="utf-8")
        time.sleep(0.02)
        (output / "artifact.md").write_text("result\n", encoding="utf-8")
        nudge = run_hook("memory_nudge.py", {"cwd": str(workspace)})
        require("记忆提醒" in nudge.stdout, "stale task index did not produce a memory reminder")


def test_input_capture_default_off() -> None:
    bridge = ROOT / "bundles" / "core-workspace-v2" / "optional" / "input-capture" / "scripts" / "bridge_user_prompt_to_capture.py"
    with tempfile.TemporaryDirectory() as temporary:
        workspace = Path(temporary)
        payload = {
            "hook_event_name": "UserPromptSubmit",
            "agent": "claude-code",
            "session_id": "capture-test",
            "cwd": str(workspace),
            "prompt": "这是一个可以整理成灵感卡片的产品想法",
        }
        disabled = subprocess.run(
            [sys.executable, str(bridge)],
            input=json.dumps(payload, ensure_ascii=False),
            text=True,
            capture_output=True,
            check=False,
            env={key: value for key, value in os.environ.items() if key != "HARNESS_INPUT_CAPTURE_ENABLED"},
        )
        require(disabled.returncode == 0, "disabled input capture blocked the session")
        require(not (workspace / ".claude" / "capture").exists(), "disabled input capture wrote files")

        enabled_env = os.environ.copy()
        enabled_env["HARNESS_INPUT_CAPTURE_ENABLED"] = "1"
        enabled = subprocess.run(
            [sys.executable, str(bridge)],
            input=json.dumps(payload, ensure_ascii=False),
            text=True,
            capture_output=True,
            check=False,
            env=enabled_env,
        )
        require(enabled.returncode == 0, "enabled input capture blocked the session")
        records = list((workspace / ".claude" / "capture" / "user-input").glob("*.jsonl"))
        require(len(records) == 1, "enabled input capture did not write one workspace-local record")
        record = json.loads(records[0].read_text(encoding="utf-8").splitlines()[-1])
        require(record["workspace"] == workspace.name, "capture workspace identity was not portable")


def main() -> int:
    tests = (
        test_injection,
        test_overexecute_guard,
        test_read_before_edit_guard,
        test_dangerous_command_guard,
        test_checkpoint_and_memory_nudge,
        test_input_capture_default_off,
    )
    for test in tests:
        test()
    print(f"runtime hook behavior passed: {len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
