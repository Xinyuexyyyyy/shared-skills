#!/usr/bin/env bash
set -u

HARNESS_ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
BUNDLE="$HARNESS_ROOT/bundles/core-workspace-v2"
FAIL=0

require_file() {
  local path="$1"
  if [[ ! -f "$BUNDLE/$path" ]]; then
    printf 'MISSING %s\n' "$path"
    FAIL=$((FAIL + 1))
  fi
}

require_marker() {
  local path="$1"
  local marker="$2"
  if [[ -f "$BUNDLE/$path" ]] && ! grep -Fq "$marker" "$BUNDLE/$path"; then
    printf 'MISSING_MARKER %s :: %s\n' "$path" "$marker"
    FAIL=$((FAIL + 1))
  fi
}

required_files=(
  "manifest.yaml"
  "CAPABILITY-MAP.yaml"
  "rules/workflow.md"
  "rules/ROUTING.md"
  "rules/CONTEXT-SPEC.md"
  "skills/output-control-layer/SKILL.md"
  "skills/output-control-layer/TWO-STAGE.md"
  "skills/closeout/SKILL.md"
  "skills/closeout/README.md"
  "templates/memory/MEMORY.md"
  "templates/memory/workspace-brief.md"
  "templates/memory/workspace-map.md"
  "templates/memory/current-position.md"
  "templates/memory/timeline.md"
  "templates/memory/timeline-archive.md"
  "templates/memory/decisions.md"
  "templates/memory/lessons.md"
  "templates/memory/lessons-archive.md"
  "templates/memory/tasks/INDEX.md"
  "tools/memory/check_map.py"
  "tools/memory/memory_gc.py"
  "tools/memory/lessons_gc.py"
  "tools/memory/organize.py"
  "hooks/inject_output_control.py"
  "hooks/inject_output_control_codex.py"
  "hooks/guard_dangerous_bash.py"
  "hooks/guard_edit_needs_read.py"
  "hooks/guard_overexecute.py"
  "hooks/record_read_files.py"
  "hooks/record_user_prompt.py"
  "hooks/nudge_subagent_dispatch.py"
  "hooks/auto_checkpoint.py"
  "hooks/memory_nudge.py"
  "runtime/codex/AGENTS.md.tmpl"
  "runtime/codex/hooks.json.tmpl"
  "runtime/claude/CLAUDE.md.tmpl"
  "runtime/claude/settings.hooks.json.tmpl"
  "runtime/common/HARNESS.md.tmpl"
  "optional/input-capture/README.md"
  "optional/input-capture/capture_layer/adapters.py"
  "optional/input-capture/scripts/bridge_user_prompt_to_capture.py"
  "optional/input-capture/scripts/capture_runtime_prompt.py"
  "optional/input-capture/scripts/capture_user_input.py"
)

for path in "${required_files[@]}"; do
  require_file "$path"
done

require_marker "skills/output-control-layer/SKILL.md" "## 5.1 文档产物渲染验收规则"
require_marker "skills/output-control-layer/SKILL.md" "## 7. 触发稳定性"
require_marker "skills/output-control-layer/TWO-STAGE.md" "路径硬触发"
require_marker "rules/ROUTING.md" "规则表"
require_marker "rules/CONTEXT-SPEC.md" "规则先行，记忆按需"
require_marker "skills/closeout/SKILL.md" "## 状态处理"
require_marker "templates/memory/lessons.md" "<!-- meta:"
require_marker "manifest.yaml" "input_capture:"
require_marker "manifest.yaml" "enabled: false"

if [[ $FAIL -ne 0 ]]; then
  printf 'full capability parity failed: %d gap(s)\n' "$FAIL"
  exit 1
fi

printf 'full capability parity passed\n'
