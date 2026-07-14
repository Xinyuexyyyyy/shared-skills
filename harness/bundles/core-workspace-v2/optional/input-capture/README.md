# 输入捕获组件

输入捕获默认关闭，也不是核心 bundle 的依赖。

启用前必须在独立 bundle 中声明捕获目的、数据范围、保存位置、保留期限、清理方式和用户可见的启停方法。不得捕获凭证，不得把原始输入自动写入长期记忆。

v2 随 bundle 提供完整可选实现：

- `capture_layer/adapters.py`：把 Codex、Claude hook payload 归一化。
- `scripts/bridge_user_prompt_to_capture.py`：运行时桥接；只有环境变量 `HARNESS_INPUT_CAPTURE_ENABLED=1` 时才工作。
- `scripts/capture_user_input.py`：工作区本地 JSONL 与候选卡写入器，明显敏感输入不保存原文。
- `scripts/capture_runtime_prompt.py`：手工和烟测入口。

默认目标是当前工作区 `.claude/capture/`。它不是长期记忆，不能自动建任务、开调研或修改 `.claude/memory/`。
