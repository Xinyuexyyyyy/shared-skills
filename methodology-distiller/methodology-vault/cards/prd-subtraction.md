# PRD 减法卡

## 什么时候用

当 PRD 变成调研报告、方法论文档、聊天记录或技术争论合集时使用。

## 解决什么缺口

提升 PRD 可读性，避免 Evidence 和方法论淹没 Boundary / Detail / Acceptance。

## 操作步骤

1. 标出正文里每一段的作用：决策、细节、证据、方法论、备选方案、背景。
2. 主 PRD 只保留产品判断和用户可见的可执行细节。
3. 证据表、来源、长引用移动到 evidence brief。
4. API、数据库、目录、组件层级、详细技术选型、迁移策略和详细错误状态移动到 ADR / implementation note。
5. 方法论来源移动到 appendix 或 review。
6. 被放弃方案只在正文保留一句理由，详细内容移到附录。

## 保留 / 移出规则

| 内容 | 放哪里 |
|---|---|
| 目标、用户、场景、痛点、MVP、Non-goals、核心流程、关键需求、验收、Stop Conditions、证据摘要 | 主 PRD |
| 来源、证据表、竞品长对比 | evidence brief |
| API、数据库、目录、组件层级、详细技术选型、迁移策略、详细错误状态 | ADR / implementation note |
| 方法论来源、开源方案筛选 | appendix / reviews |
| 被放弃方案 | 主 PRD 一句话 + 附录详情 |

## 输出格式

```text
PRD 减法结果：
- 正文保留：
- 移到 evidence brief：
- 移到 ADR：
- 移到 appendix / reviews：
- 删除或合并：
```

## 质量门

主 PRD 应该让用户和下游执行者更快判断第一版做什么、不做什么、怎么算成功、什么情况下必须停下来问人，而不是让读者先读完一篇调研报告或半份技术规格书。

## 来源 / 借鉴

- ADR / MADR 的决策记录分离思想。
- Open Practice Library 的实践卡和来源分层思想。
