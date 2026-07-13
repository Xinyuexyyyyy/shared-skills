# PRD 回滚路由卡

## 什么时候用

当 PRD Quality Gate 判定 `Needs Loopback`，但不确定缺口该回哪一层补时使用。

## 解决什么缺口

避免“发现问题 -> 继续硬写 PRD”。把缺口送回正确位置。

## 先判归属

每个缺口必须先判 `Owner`，再决定问谁或回哪一层。不要把所有缺口都问用户。

| Owner | 什么时候归它 | 回到哪里 | 是否问用户 |
|---|---|---|---|
| `User` | 目标、取舍、优先级、审美偏好、真实场景、不能接受什么只有用户知道 | `grillme` / `prd-grok-loop` | 是 |
| `Evidence` | 外部事实、竞品、API 行为、工具限制、开源成熟度、当前页面行为、平台/账号/价格/权限等外部依赖不足 | `deep-research` Phase 4 / narrowed verification；无法由 agent 解决时转 Stop Condition | 否 |
| `Method` | PRD 写法、前端、后端、API、数据、架构、UX、验收的专业默认值缺失 | `methodology-distiller` | 否 |
| `Spec` | 信息已经够，只是 PRD 没写清步骤、按钮、状态、字段、路径、验收 | PRD detail pass + 对应方法卡 | 否 |
| `Too fuzzy` | 目标、用户、场景或问题本身还不成立 | 降级为 `idea_note` / `discovery_note` 或回 `grillme` | 视情况 |

## 路由规则

| 缺口 | 回到哪里 |
|---|---|
| 用户、场景、优先级、审美偏好、约束不清 | `grillme` |
| MVP、Future、Out of Scope 冲突 | `grillme` + `prd-boundary` |
| 竞品、事实、来源、当前页面行为、平台/账号/价格/权限等外部依赖不足 | `deep-research` Phase 4 / narrowed verification；无法由 agent 解决时转 Stop Condition |
| PRD 写法、前端、后端、API、数据、架构默认方案不清 | `methodology-distiller` |
| 页面、按钮、状态、关键数据位置、验收步骤不清 | PRD detail pass + 对应方法卡 |
| PRD 太长、读不动、像资料堆 | `prd-subtraction` |
| 输入仍太模糊 | 降级为 `idea_note` / `discovery_note` |

## 输出格式

```text
回滚路由：
- 缺口：
- Owner：User / Evidence / Method / Spec / Too fuzzy
- 影响：
- 回到：
- 使用方法卡：
- Ask user：Yes / No
- Agent can resolve without user：Yes / No
- 需要用户回答：
- 系统自己调研 / 蒸馏 / 补规格：
- 补完后重新检查：
```

## 不要做

- 不要为了显得推进快而跳过回滚。
- 不要把技术问题丢给不懂技术的用户。
- 不要把证据不足说成“后续优化”。

## 质量门

每个缺口都应该有明确 Owner 和去处：问用户、补证据、蒸馏方法、补细节、做减法或降级。

## 来源 / 借鉴

- 本地 `deep-research` Phase 5 的降级出口。
- ADR/MADR 的决策归位思想。
