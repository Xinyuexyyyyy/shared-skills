#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys


TASK_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TASK_ROOT))

from capture_layer.adapters import capture_command_for, normalize_hook_payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Capture a runtime prompt through the portable harness adapter.")
    parser.add_argument("--text", help="User prompt text.")
    parser.add_argument("--payload-file", help="Hook-style JSON payload file.")
    parser.add_argument("--runtime", choices=("codex", "claude-code"), default="codex", help="Runtime surface.")
    parser.add_argument("--cwd", default=None, help="Workspace cwd where the prompt was submitted.")
    parser.add_argument("--session-id", default=None, help="Runtime session or turn id.")
    parser.add_argument("--inbox-root", default=None, help="Optional inbox root for test isolation.")
    return parser.parse_args()


def payload_from_args(args: argparse.Namespace) -> dict:
    if args.payload_file:
        return json.loads(Path(args.payload_file).read_text(encoding="utf-8"))
    text = args.text or (sys.stdin.read() if not sys.stdin.isatty() else "")
    payload = {
        "hook_event_name": "UserPromptSubmit",
        "agent": args.runtime,
        "prompt": text.strip(),
        "cwd": args.cwd,
    }
    if args.runtime == "codex":
        payload["turn_id"] = args.session_id
    else:
        payload["session_id"] = args.session_id
        payload["transcript_path"] = "manual-runtime-capture"
    return payload


def main() -> int:
    args = parse_args()
    request = normalize_hook_payload(payload_from_args(args))
    if not request.text:
        raise SystemExit("Provide --text, --payload-file, or stdin input.")

    command = capture_command_for(request)
    if args.inbox_root:
        command = [item for item in command if item not in ("--inbox-root", request.capture_root)]
        command.extend(["--inbox-root", args.inbox_root])

    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.stdout:
        print(result.stdout.strip())
    if result.returncode != 0 and result.stderr:
        print(result.stderr.strip(), file=sys.stderr)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
