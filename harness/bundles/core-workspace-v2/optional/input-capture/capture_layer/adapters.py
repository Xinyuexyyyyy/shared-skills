from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import sys


CAPTURE_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "capture_user_input.py"


@dataclass(frozen=True)
class RuntimeCaptureRequest:
    text: str
    source: str
    workspace: str
    session_id: str | None
    cwd: str | None
    runtime: str
    capture_root: str | None


def event_name(payload: dict) -> str:
    raw = payload.get("hook_event_name") or payload.get("hookEventName") or payload.get("hook_event") or ""
    return str(raw).lower()


def runtime_for(payload: dict) -> str:
    agent = str(payload.get("agent") or payload.get("runtime") or payload.get("source") or "").lower()
    if "codex" in agent:
        return "codex"
    if "claude" in agent:
        return "claude-code"
    if payload.get("turn_id") is not None:
        return "codex"
    if payload.get("transcript_path") is not None:
        return "claude-code"
    if event_name(payload) == "userpromptsubmit":
        return "codex"
    return "manual"


def source_for(runtime: str, cwd: str | None) -> str:
    if runtime == "codex":
        return "codex"
    if runtime == "claude-code":
        return "claude-code"
    return "manual"


def workspace_for(cwd: str | None) -> str:
    configured = os.environ.get("HARNESS_WORKSPACE_ID", "").strip()
    if configured:
        return configured
    if cwd:
        return Path(cwd).expanduser().resolve().name or "workspace"
    return "workspace"


def session_id_for(payload: dict) -> str | None:
    value = payload.get("session_id") or payload.get("turn_id") or payload.get("conversation_id")
    return str(value) if value is not None else None


def cwd_for(payload: dict) -> str | None:
    value = payload.get("cwd") or payload.get("workspace") or payload.get("project_dir") or payload.get("root")
    return str(value) if value is not None and str(value).strip() else None


def normalize_hook_payload(payload: dict) -> RuntimeCaptureRequest:
    prompt = payload.get("prompt") or payload.get("text") or payload.get("user_input") or ""
    text = str(prompt).strip()
    cwd = cwd_for(payload)
    runtime = runtime_for(payload)
    return RuntimeCaptureRequest(
        text=text,
        source=source_for(runtime, cwd),
        workspace=workspace_for(cwd),
        session_id=session_id_for(payload),
        cwd=cwd,
        runtime=runtime,
        capture_root=str(Path(cwd).expanduser().resolve() / ".claude" / "capture") if cwd else None,
    )


def capture_command_for(request: RuntimeCaptureRequest) -> list[str]:
    command = [
        sys.executable,
        str(CAPTURE_SCRIPT),
        "--text",
        request.text,
        "--source",
        request.source,
        "--workspace",
        request.workspace,
    ]
    if request.session_id:
        command.extend(["--session-id", request.session_id])
    if request.cwd:
        command.extend(["--cwd", request.cwd])
    if request.capture_root:
        command.extend(["--inbox-root", request.capture_root])
    return command
