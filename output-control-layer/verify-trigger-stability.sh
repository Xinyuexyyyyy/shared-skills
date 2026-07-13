#!/usr/bin/env bash
set -u

PASS=0
FAIL=0

SKILL="/Users/sure/shared-skills/output-control-layer/SKILL.md"
TWO_STAGE="/Users/sure/shared-skills/output-control-layer/TWO-STAGE.md"
INDEX="/Users/sure/shared-skills/output-control-layer/INDEX.md"
CODEX_AGENTS="/Users/sure/.codex/AGENTS.md"
DW_AGENTS="/Users/sure/DailyWork2/AGENTS.md"
PRD="/Users/sure/task_draft/consensus/output-control-layer/output-control-layer-trigger-stability-prd-v0.1.md"

ok() {
  PASS=$((PASS + 1))
  printf '✅ %s\n' "$1"
}

bad() {
  FAIL=$((FAIL + 1))
  printf '❌ %s\n' "$1"
}

check_file() {
  if [ -f "$1" ]; then
    ok "file exists: $1"
  else
    bad "missing file: $1"
  fi
}

check_contains() {
  local file="$1"
  local pattern="$2"
  local label="$3"

  if [ -f "$file" ] && grep -q "$pattern" "$file"; then
    ok "$label"
  else
    bad "$label"
  fi
}

check_file "$SKILL"
check_file "$TWO_STAGE"
check_file "$INDEX"
check_file "$CODEX_AGENTS"
check_file "$DW_AGENTS"
check_file "$PRD"

check_contains "$SKILL" "## 7. 触发稳定性" "SKILL.md has trigger-stability section"
check_contains "$SKILL" "Codex 短版输出闸" "SKILL.md has Codex short gate"
check_contains "$SKILL" "工具前二审" "SKILL.md has tool preflight review"
check_contains "$SKILL" "长流程阶段闸" "SKILL.md has long-flow stage gate"
check_contains "$SKILL" "final gate" "SKILL.md has final gate"

check_contains "$TWO_STAGE" "触发稳定性相关修改必须两段制" "TWO-STAGE.md covers trigger-stability two-stage rule"
check_contains "$TWO_STAGE" "/Users/sure/DailyWork2/AGENTS.md" "TWO-STAGE.md includes DailyWork2 AGENTS"
check_contains "$TWO_STAGE" "/Users/sure/DailyWork2/WORKSPACE.md" "TWO-STAGE.md includes DailyWork2 WORKSPACE"
check_contains "$TWO_STAGE" "/Users/sure/shared-skills/output-control-layer/INDEX.md" "TWO-STAGE.md includes output-control INDEX"

check_contains "$CODEX_AGENTS" "## Codex 短版输出闸" "Codex AGENTS has short output gate"
check_contains "$DW_AGENTS" "## DailyWork2 本地输出短闸" "DailyWork2 AGENTS has local output gate"

check_contains "$INDEX" "verify-trigger-stability.sh" "INDEX mentions trigger-stability verifier"
check_contains "$INDEX" "output-control-layer-trigger-stability-prd-v0.1.md" "INDEX mentions trigger-stability PRD"
check_contains "$INDEX" "正式输出 final gate" "INDEX mentions final gate"

printf '\n'
if [ "$FAIL" -eq 0 ]; then
  printf '✅ 共 %d 项,无 ❌。\n' "$PASS"
  exit 0
else
  printf '❌ %d 项失败,✅ %d 项通过。\n' "$FAIL" "$PASS"
  exit 1
fi
