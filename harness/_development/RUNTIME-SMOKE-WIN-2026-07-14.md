# Win 运行时 Harness 烟测

日期：2026-07-14

## 范围

- 使用 `examples/livewithopencove-workspace/` 的独立副本。
- 测试目录位于公共用户目录，不继承 Win 用户根的外部协调入口。
- 只验证运行时能否按工作区入口消费 Harness，不修改 Win 全局规则。
- 测试前后工作区均为 32 个文件，bundle 的 16 个文件校验值不变，未生成会话、日志或工作区配置文件。

## Codex

- Codex 版本：`0.144.3`。
- `read-only` 沙箱因 Windows DPAPI 报 `CryptUnprotectData` 失败，agent 未能读取文件；这是运行时沙箱问题，不是 Harness 入口问题。
- 在隔离测试目录中改用 `danger-full-access`，同时保持任务提示只读后，agent 成功读取工作区入口、Harness manifest 和全部核心规则。
- 正确回报 bundle、十阶段顺序、真实记忆不进 bundle、按需读取和 closeout 最小规则。

## Claude

- 使用 `plan` 权限模式和不持久化会话。
- 成功通过 `.claude/CLAUDE.md` 读取同一 Harness 入口和 bundle。
- 正确回报与 Codex 一致的 bundle、十阶段顺序、记忆边界和输出规则。

## 结论

LiveWithOpenCove 风格示例工作区可被 Win 上的 Codex 与 Claude 消费，且两者读取到相同的阶段语义。当前 Win 用户根全局入口仍未接入本 Harness；若要全局启用，必须单独设计不与外部协调入口混淆的薄指针，并再次执行新会话烟测。
