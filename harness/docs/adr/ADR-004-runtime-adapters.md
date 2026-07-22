# ADR-004：Codex/Claude Runtime Adapter 与能力降级

状态：accepted for draft

Codex 和 Claude 共享 v3 config、manifest 和 bundle 语义资产，只保留各自的薄入口模板。运行时事件、Hook 注册点和行为证据分开声明；没有等价执行点的能力必须标为 contract-only、eval-only 或 unverified。

本阶段没有真实新会话证据，因此 `codex-turn-protocol` 与 `claude-turn-protocol` 均保持 contract-only，双端行为证据保持 unverified。
