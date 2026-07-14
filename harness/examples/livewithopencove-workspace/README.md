# Harness Example Workspace

这是一个自包含示例，用来展示 LiveWithOpenCove 风格工作区如何接入可复用 harness。

## 结构

- `AGENTS.md`：Codex 薄入口。
- `.claude/CLAUDE.md`：Claude 薄入口。
- `.agents/skills/` 与 `.claude/skills/`：运行时 skill 薄适配器。
- `harness/`：当前工作区使用的规则、manifest 和规范化 skills。
- `.claude/memory/`：私有状态边界，不属于 harness。

## 验收预期

读取本示例后，agent 应能说明：

1. 当前启用了完整迁移草稿 `core-workspace-v2@0.1.0`。
2. 核心入口是 `harness/HARNESS.md`。
3. `output-control-layer` 与 `closeout` 可被 Codex、Claude 的 skill 入口发现；`example-status` 只在用户询问 harness 状态时加载。
4. `.claude/memory/` 不属于 bundle。
5. 单次输入固定经过工作流、验证、输出控制和 closeout，灵感旁路只允许人工触发。
6. Bundle 提供 hook 注册模板和记忆维护工具，但不会自动改写用户级配置。

本示例不要求修改全局 agent 配置。
