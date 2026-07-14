---
component_id: runtime-adapter-codex
version: 1.0.0
status: draft
---

# Codex 运行时适配

- 工作区根 `AGENTS.md` 是 Codex 的薄入口，只指向 `harness/HARNESS.md`。
- 共享 skill 的工作区发现入口使用 `.agents/skills/`，其中只保存指向 `harness/skills/` 的薄适配文件。
- 核心规则从 bundle manifest 加载，不在 `AGENTS.md` 或 skill 适配器中复制。
- 若运行环境支持会话 hook，manifest 必须声明 hook 注入了哪些阶段；已由入口加载的阶段不得重复注入。
- 启动烟测至少确认：入口可读、bundle 版本明确、skill 可发现、私有记忆未被预读。
