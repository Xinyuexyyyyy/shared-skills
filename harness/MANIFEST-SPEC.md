# Harness Manifest Spec

## 1. 基本规则

- 文件格式为 YAML。
- `schema_version` 当前固定为 `"1"`。
- 所有路径相对于 manifest 所在目录。
- 路径必须使用 `/`。
- 禁止绝对路径和 `~`。
- manifest 必须显式列出入口、bundles、skills 和私有状态边界。
- 未列入 manifest 的文件不能视为发布内容。
- Bundle 内每个文件必须记录 SHA-256，内容变化后必须重新物化。

## 2. Assembly

Assembly 位于 `assemblies/`，是源组件到可发布 bundle 的组装配方：

```yaml
schema_version: "1"
kind: bundle-source
id: core-workspace-v2
version: 0.1.0
status: draft
runtime: neutral
entrypoint: rules/workflow.md
files:
  - source: components/workflow/WORKFLOW.md
    path: rules/workflow.md
    role: workflow-contract
    component_id: workflow
```

`source` 相对于 harness 根目录，`path` 相对于生成的 bundle。两者都不得越出各自边界。Assembly 只用于维护和物化，不随工作区运行时加载。

## 3. Bundle Manifest

```yaml
schema_version: "1"
kind: bundle
id: runtime-baseline
version: 1.0.0
status: stable
description: Runtime-neutral operating baseline
runtime: neutral
entrypoint: rules/operating.md
files:
  - path: rules/operating.md
    role: operating-rules
    sha256: 0000000000000000000000000000000000000000000000000000000000000000
```

必填字段：`schema_version`、`kind`、`id`、`version`、`status`、`runtime`、`entrypoint` 和 `files`。`status` 只能是 `draft`、`stable` 或 `deprecated`。

核心工作区 bundle 还必须声明：

- `workflow.id`、`workflow.version` 和固定顺序的 `workflow.stages`。
- `memory_policy.private_root`、延迟读取和写入确认策略。
- `input_capture.enabled`，核心 bundle 中默认必须为 `false`。
- `capability_map`，并与 bundle ID、版本一致。
- `hooks.catalog` 与两个运行时注册模板；catalog 中每个实现都必须进入 `files`。
- `runtime_adapters.codex` 与 `runtime_adapters.claude`。
- `checks.structure` 和 `checks.negative_tests`。

`files` 中每项必须有 `path`、`role` 和 `sha256`；属于具名组件时增加 `component_id`。Manifest 中的适配器和入口必须同时出现在 `files` 中。

可选字段 `excludes` 用于声明明确不进入 bundle 的内容类别，例如 `memory`、`credentials` 和 `runtime-config`。它只表达发布边界，不能代替文件级 `files` 清单。

## 4. Workspace Manifest

```yaml
schema_version: "1"
kind: workspace
id: example-workspace
version: 1.0.0
locale: zh-CN
entrypoints:
  - ../AGENTS.md
  - ../.claude/CLAUDE.md
harness_entrypoint: HARNESS.md
bundles:
  - id: runtime-baseline
    version: 1.0.0
    path: bundles/runtime-baseline
skills:
  - id: example-status
    path: skills/example-status/SKILL.md
private_state:
  excluded_paths:
    - ../.claude/memory
runtime_adapters:
  codex:
    - ../.agents/skills/example-status/SKILL.md
  claude:
    - ../.claude/skills/example-status/SKILL.md
```

`private_state.excluded_paths` 只声明隔离边界，不把这些目录纳入 harness。

Workspace manifest 必须包含 `harness_entrypoint`、`entrypoints`、`bundles`、`skills`、`runtime_adapters` 和 `private_state`。`runtime_adapters` 当前必须同时声明 `codex` 与 `claude`，每项使用列表并指向对应运行时目录内的薄适配文件。

## 5. 校验要求

有效 manifest 必须满足：

- 所有引用路径存在。
- bundle ID 和版本与子 manifest 一致。
- bundle status、workflow 阶段和顺序有效。
- 每个文件的实际 SHA-256 与 manifest 一致。
- Assembly 源组件与 canonical bundle 逐字节一致。
- bundle 内没有主机绝对路径。
- bundle 不包含私有 memory 内容。
- `harness_entrypoint` 存在且位于工作区 harness 内。
- `runtime_adapters` 必须同时声明 Codex 和 Claude。
- 两个运行时入口均指向同一 `HARNESS.md`。
- 示例工作区内的 bundle 与权威 bundle 内容一致。

最低校验命令：

```bash
bash scripts/validate-harness.sh
bash tests/test-validate-harness.sh
python3 scripts/materialize-bundle.py \
  --assembly assemblies/core-workspace-v2.yaml \
  --output bundles/core-workspace-v2 \
  --check
```
