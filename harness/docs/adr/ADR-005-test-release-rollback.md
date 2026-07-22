# ADR-005：测试、发布、候选晋升与回滚

状态：accepted for draft

`validate`、`assemble`、`health` 和 `doctor` 构成静态治理主链；行为用例放在 `tests/behavior/`，runtime 证据放在 `tests/runtime/`，两者不读取真实 memory、历史、凭证或设备状态。静态通过不等于运行时通过。

Draft 到 Candidate 需要 Schema、assembly、manifest、预算、静态负向测试和隔离行为测试；Candidate 到 Stable 还需要 Codex 与 Claude 新会话证据、SHA 可复查、真实工作区回滚演练和所有 blocker 关闭。当前回滚目标固定为 `core-workspace-v2@0.1.0+draft`。
