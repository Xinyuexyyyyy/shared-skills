#!/bin/bash
# 自动为 skills/ 下的所有子目录创建 CLAUDE.md -> SKILL.md 软链接

SKILLS_DIR="$(cd "$(dirname "$0")" && pwd)"

for dir in "$SKILLS_DIR"/*/; do
  [ -d "$dir" ] || continue
  name=$(basename "$dir")
  
  # 跳过非 skill 目录或特殊目录
  [[ "$name" == .* ]] && continue
  
  if [ -f "$dir/SKILL.md" ] && [ ! -e "$dir/CLAUDE.md" ]; then
    ln -sf SKILL.md "$dir/CLAUDE.md"
    echo "✓ $name: CLAUDE.md → SKILL.md"
  fi
done

echo "done"
