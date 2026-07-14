# Workspace Harness

当前工作区的 harness 由 `manifest.yaml` 声明。

加载顺序：

1. 读取 `manifest.yaml`。
2. 按顺序读取每个 bundle 的 manifest。
3. 从 bundle 的 `entrypoint` 开始，并按 `files` 顺序应用工作流、输出控制、路由、记忆和 closeout 规则。
4. 仅在任务命中时读取对应 skill。
5. 只有用户要求接续已有任务时，才按需读取 `../.claude/memory/`。

边界：

- `harness/` 保存共享工作方式、清单和 skills 权威内容。
- `.agents/skills/` 与 `.claude/skills/` 只保存运行时薄适配器。
- `.claude/memory/` 保存工作区私有状态。
- 私有状态不得进入 bundle 或存储镜像。
- Bundle 中的 memory 文件只是空模板，不是当前工作区状态。
- 任一 manifest 引用缺失时，报告缺口，不猜测替代文件。
