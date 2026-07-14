#!/usr/bin/env bash
set -euo pipefail

HARNESS_ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
BUNDLE="$HARNESS_ROOT/bundles/core-workspace-v2"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

WS="$TMP/workspace"
MEM="$WS/.claude/memory"
mkdir -p "$MEM/tasks" "$WS/project-one" "$WS/output/output-layer"
cp -R "$BUNDLE/templates/memory/." "$MEM/"

cat >> "$MEM/timeline.md" <<'EOF'
## 2026-07-03 10:00
- third
## 2026-07-02 10:00
- second
## 2026-07-01 10:00
- first
EOF

before_timeline="$(shasum -a 256 "$MEM/timeline.md" | cut -d' ' -f1)"
python3 "$BUNDLE/tools/memory/memory_gc.py" --keep 2 --dry-run "$WS" >/dev/null
after_dry_timeline="$(shasum -a 256 "$MEM/timeline.md" | cut -d' ' -f1)"
[[ "$before_timeline" == "$after_dry_timeline" ]]
python3 "$BUNDLE/tools/memory/memory_gc.py" --keep 2 "$WS" >/dev/null
[[ "$(grep -c '^## 2026-' "$MEM/timeline.md")" -eq 2 ]]
grep -Fq '2026-07-01' "$MEM/timeline-archive.md"

cat >> "$MEM/lessons.md" <<'EOF'

## 2020-01-01: 当旧规则长期未用 -> 建议退役
<!-- meta: id=L001 | scope=test | applied=0 | helpful=0 | harmful=0 | last=2020-01-01 -->
**场景：** 合成测试
**观察：** 长期未用
**做法：** 报告候选
**效果：** 可验证
**置信度：** 高
**建议：** 归档
EOF

before_lessons="$(shasum -a 256 "$MEM/lessons.md" | cut -d' ' -f1)"
python3 "$BUNDLE/tools/memory/lessons_gc.py" --stale-days 1 --dry-run "$WS" >/dev/null
after_dry_lessons="$(shasum -a 256 "$MEM/lessons.md" | cut -d' ' -f1)"
[[ "$before_lessons" == "$after_dry_lessons" ]]
python3 "$BUNDLE/tools/memory/lessons_gc.py" --stale-days 1 --apply "$WS" >/dev/null
grep -Fq 'L001' "$MEM/lessons-archive.md"

map_output="$(python3 "$BUNDLE/tools/memory/check_map.py" "$WS")"
grep -Fq 'project-one' <<<"$map_output"
grep -Fq '未登记目录' <<<"$map_output"

mkdir -p \
  "$WS/output/output-layer/20260701-100000-topic" \
  "$WS/output/output-layer/20260702-100000-topic"
python3 "$BUNDLE/tools/memory/organize.py" --dir "$WS/output/output-layer" >/dev/null
[[ -d "$WS/output/output-layer/20260702-100000-topic" ]]
python3 "$BUNDLE/tools/memory/organize.py" --dir "$WS/output/output-layer" --apply >/dev/null
[[ -f "$WS/output/output-layer/topic/.source_ts" ]]
[[ -d "$WS/output/output-layer/_archive/topic/20260701-100000" ]]

echo "memory tool behavior passed"
