# ADR-001：配置分离与规则所有权

状态：accepted for draft

v3 将 Agent 行为倾向、单轮 workflow、memory 政策、确定性 policy、runtime capability 分成五份 YAML。每条机器可判断规则只在一个配置域声明 `owned_rules`，assembly 只负责组合，bundle 只负责发布副本。

配置比 Markdown 更容易做 Schema、预算和差异检查；运行时仍需要少量 Markdown 入口，但入口不得复制配置正文。v1/v2 保留原路径和 draft 状态，不在本 ADR 中迁移业务 skills。
