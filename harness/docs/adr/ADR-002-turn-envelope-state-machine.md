# ADR-002：Turn Envelope 与状态机

状态：accepted for draft

v3 在 `workflow.yaml` 声明完整单轮状态机。Turn Envelope 只定义 Schema 和字段契约，本阶段不把真实回合内容落盘。

缺口归属区分 user、evidence、method、spec、execution、authority。没有真实运行时执行点时只能标为 contract-only 或 eval-only；Schema 不伪装成 Hook。
