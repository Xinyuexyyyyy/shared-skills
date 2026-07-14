#!/usr/bin/env python3
"""Optional UserPromptSubmit bridge for workspace-local input capture.

Reads hook JSON from stdin and forwards the prompt to capture_user_input.py.
The bridge is disabled unless HARNESS_INPUT_CAPTURE_ENABLED=1. It is intentionally
silent and non-blocking: any failure exits 0.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys


TASK_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TASK_ROOT))

from capture_layer.adapters import capture_command_for, normalize_hook_payload


def load_payload() -> dict:
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except Exception:
        return {}


def main() -> int:
    if os.environ.get("HARNESS_INPUT_CAPTURE_ENABLED") != "1":
        return 0
    payload = load_payload()
    request = normalize_hook_payload(payload)
    if not request.text:
        return 0

    try:
        subprocess.run(capture_command_for(request), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2, check=False)
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
