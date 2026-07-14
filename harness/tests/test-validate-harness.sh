#!/usr/bin/env bash
set -euo pipefail

HARNESS_ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"

output="$($HARNESS_ROOT/scripts/validate-harness.sh)"
grep -Fq "harness validation passed" <<<"$output"

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT
cp -R "$HARNESS_ROOT/examples/livewithopencove-workspace" "$tmp_dir/workspace"

sed -i.bak 's#path: bundles/core-workspace-v1#path: /tmp/core-workspace-v1#' \
  "$tmp_dir/workspace/harness/manifest.yaml"
rm "$tmp_dir/workspace/harness/manifest.yaml.bak"
set +e
invalid_output="$($HARNESS_ROOT/scripts/validate-harness.sh --workspace "$tmp_dir/workspace" 2>&1)"
invalid_status=$?
set -e
[[ $invalid_status -ne 0 ]]
grep -Eiq 'absolute|outside|invalid' <<<"$invalid_output"

cp -R "$HARNESS_ROOT/examples/livewithopencove-workspace" "$tmp_dir/version-workspace"
sed -i.bak 's/version: 0.1.0/version: 9.9.9/' \
  "$tmp_dir/version-workspace/harness/manifest.yaml"
rm "$tmp_dir/version-workspace/harness/manifest.yaml.bak"
set +e
version_output="$($HARNESS_ROOT/scripts/validate-harness.sh --workspace "$tmp_dir/version-workspace" 2>&1)"
version_status=$?
set -e
[[ $version_status -ne 0 ]]
grep -Eiq 'version|mismatch|invalid' <<<"$version_output"

cp -R "$HARNESS_ROOT/examples/livewithopencove-workspace" "$tmp_dir/escape-workspace"
sed -i.bak 's#harness_entrypoint: HARNESS.md#harness_entrypoint: ../AGENTS.md#' \
  "$tmp_dir/escape-workspace/harness/manifest.yaml"
rm "$tmp_dir/escape-workspace/harness/manifest.yaml.bak"
set +e
escape_output="$($HARNESS_ROOT/scripts/validate-harness.sh --workspace "$tmp_dir/escape-workspace" 2>&1)"
escape_status=$?
set -e
[[ $escape_status -ne 0 ]]
grep -Eiq 'escape|boundary|invalid' <<<"$escape_output"

cp -R "$HARNESS_ROOT/examples/livewithopencove-workspace" "$tmp_dir/undeclared-workspace"
touch "$tmp_dir/undeclared-workspace/harness/undeclared.md"
set +e
undeclared_output="$($HARNESS_ROOT/scripts/validate-harness.sh --workspace "$tmp_dir/undeclared-workspace" 2>&1)"
undeclared_status=$?
set -e
[[ $undeclared_status -ne 0 ]]
grep -Eiq 'undeclared' <<<"$undeclared_output"

cp -R "$HARNESS_ROOT/examples/livewithopencove-workspace" "$tmp_dir/renamed-workspace"
mv "$tmp_dir/renamed-workspace/harness/bundles/core-workspace-v1" \
  "$tmp_dir/renamed-workspace/harness/bundles/renamed-core"
sed -i.bak 's#path: bundles/core-workspace-v1#path: bundles/renamed-core#' \
  "$tmp_dir/renamed-workspace/harness/manifest.yaml"
rm "$tmp_dir/renamed-workspace/harness/manifest.yaml.bak"
printf '\nchanged\n' >> "$tmp_dir/renamed-workspace/harness/bundles/renamed-core/rules/output-control.md"
set +e
renamed_output="$($HARNESS_ROOT/scripts/validate-harness.sh --workspace "$tmp_dir/renamed-workspace" 2>&1)"
renamed_status=$?
set -e
[[ $renamed_status -ne 0 ]]
grep -Eiq 'differ|mismatch|canonical' <<<"$renamed_output"

cp -R "$HARNESS_ROOT/examples/livewithopencove-workspace" "$tmp_dir/adapter-workspace"
sed -i.bak 's#../.claude/skills/example-status/SKILL.md#../.agents/skills/example-status/SKILL.md#' \
  "$tmp_dir/adapter-workspace/harness/manifest.yaml"
rm "$tmp_dir/adapter-workspace/harness/manifest.yaml.bak"
set +e
adapter_output="$($HARNESS_ROOT/scripts/validate-harness.sh --workspace "$tmp_dir/adapter-workspace" 2>&1)"
adapter_status=$?
set -e
[[ $adapter_status -ne 0 ]]
grep -Eiq 'adapter|runtime|directory' <<<"$adapter_output"

cp -R "$HARNESS_ROOT/examples/livewithopencove-workspace" "$tmp_dir/private-workspace"
sed -i.bak 's#../.claude/memory#..#' "$tmp_dir/private-workspace/harness/manifest.yaml"
rm "$tmp_dir/private-workspace/harness/manifest.yaml.bak"
set +e
private_output="$($HARNESS_ROOT/scripts/validate-harness.sh --workspace "$tmp_dir/private-workspace" 2>&1)"
private_status=$?
set -e
[[ $private_status -ne 0 ]]
grep -Eiq 'private|whole workspace|invalid' <<<"$private_output"

cp -R "$HARNESS_ROOT/examples/livewithopencove-workspace" "$tmp_dir/entry-workspace"
sed -i.bak '\#- ../.claude/CLAUDE.md#d' "$tmp_dir/entry-workspace/harness/manifest.yaml"
rm "$tmp_dir/entry-workspace/harness/manifest.yaml.bak"
set +e
entry_output="$($HARNESS_ROOT/scripts/validate-harness.sh --workspace "$tmp_dir/entry-workspace" 2>&1)"
entry_status=$?
set -e
[[ $entry_status -ne 0 ]]
grep -Eiq 'entrypoint|CLAUDE' <<<"$entry_output"

cp -R "$HARNESS_ROOT/examples/livewithopencove-workspace" "$tmp_dir/coverage-workspace"
mkdir -p "$tmp_dir/coverage-workspace/harness/skills/second-status"
printf '%s\n' \
  '---' \
  'name: second-status' \
  'description: Test-only second skill.' \
  '---' \
  '' \
  '# Second Status' > "$tmp_dir/coverage-workspace/harness/skills/second-status/SKILL.md"
sed -i.bak '/runtime_adapters:/i\
  - id: second-status\
    path: skills/second-status/SKILL.md
' "$tmp_dir/coverage-workspace/harness/manifest.yaml"
rm "$tmp_dir/coverage-workspace/harness/manifest.yaml.bak"
set +e
coverage_output="$($HARNESS_ROOT/scripts/validate-harness.sh --workspace "$tmp_dir/coverage-workspace" 2>&1)"
coverage_status=$?
set -e
[[ $coverage_status -ne 0 ]]
grep -Eiq 'adapter|cover|skill' <<<"$coverage_output"

cp -R "$HARNESS_ROOT/examples/livewithopencove-workspace" "$tmp_dir/path-workspace"
printf '\n路径：%s\n' '/opt/private' >> "$tmp_dir/path-workspace/harness/HARNESS.md"
set +e
path_output="$($HARNESS_ROOT/scripts/validate-harness.sh --workspace "$tmp_dir/path-workspace" 2>&1)"
path_status=$?
set -e
[[ $path_status -ne 0 ]]
grep -Eiq 'absolute|portable|path' <<<"$path_output"

cp -R "$HARNESS_ROOT/examples/livewithopencove-workspace" "$tmp_dir/https-workspace"
printf '\n参考：%s\n' 'https://example.com/docs/runtime-baseline' >> \
  "$tmp_dir/https-workspace/harness/HARNESS.md"
https_output="$($HARNESS_ROOT/scripts/validate-harness.sh --workspace "$tmp_dir/https-workspace")"
grep -Fq "harness validation passed" <<<"$https_output"

cp -R "$HARNESS_ROOT/examples/livewithopencove-workspace" "$tmp_dir/checksum-workspace"
printf '\nchanged\n' >> \
  "$tmp_dir/checksum-workspace/harness/bundles/core-workspace-v1/rules/output-control.md"
set +e
checksum_output="$($HARNESS_ROOT/scripts/validate-harness.sh --workspace "$tmp_dir/checksum-workspace" 2>&1)"
checksum_status=$?
set -e
[[ $checksum_status -ne 0 ]]
grep -Eiq 'sha256|checksum|mismatch' <<<"$checksum_output"

cp -R "$HARNESS_ROOT/examples/livewithopencove-workspace" "$tmp_dir/workflow-workspace"
sed -i.bak 's/^  - digest$/  - verification/' \
  "$tmp_dir/workflow-workspace/harness/bundles/core-workspace-v1/manifest.yaml"
rm "$tmp_dir/workflow-workspace/harness/bundles/core-workspace-v1/manifest.yaml.bak"
set +e
workflow_output="$($HARNESS_ROOT/scripts/validate-harness.sh --workspace "$tmp_dir/workflow-workspace" 2>&1)"
workflow_status=$?
set -e
[[ $workflow_status -ne 0 ]]
grep -Eiq 'workflow|stages|order|contract' <<<"$workflow_output"

python3 "$HARNESS_ROOT/scripts/materialize-bundle.py" \
  --assembly assemblies/core-workspace-v1.yaml \
  --output bundles/core-workspace-v1 \
  --check >/dev/null
python3 "$HARNESS_ROOT/scripts/materialize-bundle.py" \
  --assembly assemblies/core-workspace-v1.yaml \
  --output examples/livewithopencove-workspace/harness/bundles/core-workspace-v1 \
  --check >/dev/null

set +e
unsafe_output="$(python3 "$HARNESS_ROOT/scripts/materialize-bundle.py" \
  --assembly assemblies/core-workspace-v1.yaml \
  --output bundles/not-the-bundle \
  --check 2>&1)"
unsafe_status=$?
set -e
[[ $unsafe_status -ne 0 ]]
grep -Eiq 'output|bundle-id|assembly id' <<<"$unsafe_output"

cp -R "$HARNESS_ROOT/examples/livewithopencove-workspace" "$tmp_dir/credential-workspace"
printf '\n%s: %s\n' 'password' 'hunter2' >> "$tmp_dir/credential-workspace/harness/HARNESS.md"
set +e
credential_output="$($HARNESS_ROOT/scripts/validate-harness.sh --workspace "$tmp_dir/credential-workspace" 2>&1)"
credential_status=$?
set -e
[[ $credential_status -ne 0 ]]
grep -Eiq 'credential|published content' <<<"$credential_output"

echo "validate-harness test passed"
