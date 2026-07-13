# Formal Expansion Replay 2026-06-25

## 目标

用真实短稿验证 `formal-expansion -> quality gate -> docx` 是否能解决“太短、太口语、太简单”的问题，并检查扩写是否跑题。

## 样本

| case | source |
|---|---|
| `meeting-note` | `samples/meeting-note.md` |

原稿是短会议纪要，只有讨论结果和后续动作。

## 第一轮结果

开启：

```bash
--formal-expansion structured
--docx-quality-check auto
--assisted-quality-review auto
```

发现问题：

- 扩写后通过了部分质量检查，但扩写主题跑偏。
- 原稿标题是“会议纪要样例”，扩写稿变成了“输出层正式写作质量关建设说明”。
- 根因：扩写器只根据正文关键词判断场景，没有优先保留原稿标题和已有章节职责。

## 修正

新增主题保持规则：

- 如果原稿已有明确标题，且标题不是“输入/草稿/原文”等占位标题，则保留原标题。
- 如果原稿已有两个以上标题结构，则优先按原稿主题扩写。
- 扩写只补文档目的、依据边界和结论下一步，不把原稿改写成 output-layer 自身说明。

新增回归：

- `test_existing_meeting_note_keeps_original_topic_when_structured`
- `test_formal_report_required_sections_accept_equivalent_headings`

同时放宽 formal_report 必要要素的等价标题：

| 要素 | 等价标题 |
|---|---|
| 背景 | 背景、问题、现有问题、原始内容、现状 |
| 目的 | 目的、目标、文档目的、建设目的 |
| 方案 | 方案、处理方案、核心内容、处理原则、后续动作、措施 |
| 依据 | 依据、边界、依据与边界、资料来源、说明 |
| 结论 | 结论、下一步、结论与下一步、建议 |

## 最终结果

`meeting-note` 扩写后：

- 保留标题“会议纪要样例”。
- 保留讨论结果和后续动作。
- 补充文档目的、依据与边界、结论与下一步。
- 不新增未提供的事实、数据、责任人或完成期限。

质量门结果：

| gate | status |
|---|---|
| `docx_quality_check` | `pass` |
| `assisted_quality_review` | `pass` |
| `docx` | `written` |

## 结论

正式扩写层现在对真实短稿有实际提升：

- 不再只把短稿原样送入 docx。
- 不再把有主题的短稿改写成系统自我说明。
- 扩写后能通过两道质量门。

下一步应继续收真实样本，重点观察：

- `structured` 是否会过度扩写。
- `conservative` 是否足够克制。
- 质量门报告是否能直接驱动修订动作。

## 5 样本回放补充

回放目录：

`/Users/sure/Daily Work/output/output-layer-quality-replay-20260625-final/`

回放命令统一开启：

```bash
--formal-expansion structured
--docx-quality-check auto
--assisted-quality-review auto
```

| 样本 | Delivery | docx 质量门 | 辅助审查 | 扩写修订项 | 判断 |
|---|---|---|---|---:|---|
| `gt-power-doc-replica` | `needs_content_revision` | `draft_only` | `needs_human_review` | 0 | 合理：存在空章节/运行事实需人工复核。 |
| `fluent-automation-stability` | `needs_content_revision` | `draft_only` | `pass` | 1 | 合理：多外部来源缺参考资料区，且存在抽象行动项。 |
| `product-research-final` | `needs_content_revision` | `draft_only` | `pass` | 0 | 合理：原稿过短，作为正式 docx 需要补结构。 |
| `openclaw-system-overview` | `deliverable_with_review` | `pass` | `needs_human_review` | 0 | 合理：结构可交付，但版本、端口、PID 等事实需人工复核。 |
| `content-article` | `deliverable` | `pass` | `pass` | 0 | 合理：内容稿不再被 formal_report 规则误伤；内容发布质量后续应走内容稿专用质量门。 |

本轮校准：

- `docx_quality_check` 不再因表格缺说明、裸 URL 等低风险 warning 自动判为 `draft_only`。
- `missing_reference_section` 仍保留为修订项；多个外部来源没有资料区不适合作为正式交付。
- `formal_report` 的“背景”要素新增“概况/系统概况/运行记录”等等价标题，避免运行记录类文档误判。
- 正式扩写层在原稿已有明确标题和章节时，不再自动添加默认事实占位，避免对内容稿和系统报告造成“待补充事实”误伤。
- `needs_human_review` 已进入 `Delivery Recommendation`，以“人工复核事实、版本、端口、PID、政策或机构口径后再正式交付”的中文动作呈现。

## 广泛样本回放 2026-06-26

回放目录：

`/Users/sure/Daily Work/output/output-layer-broad-replay-20260626/`

占位缺项修复后的边界回放目录：

`/Users/sure/Daily Work/output/output-layer-broad-replay-20260626-after-placeholder-fix/`

覆盖类型：

- 真实正式报告：`gt-power-doc-replica`
- 真实运行记录：`openclaw-system-overview`
- 真实内容稿：`content-article`
- 会议纪要：`meeting-note`
- 申请类：`proposal`
- 技术说明：`technical`
- 摘要：完整摘要、不完整摘要
- 说明书：`manual`
- 极短输入：`too-short-input`

结果：

| 样本 | 文档类型 | docx 质量门 | 辅助审查 | Delivery | 判断 |
|---|---|---|---|---|---|
| `01-real-gt-doc` | `formal_report` | `draft_only` | `needs_human_review` | `needs_content_revision` | 正式报告仍需修订结构，并人工复核运行事实。 |
| `02-real-runtime-openclaw` | `runtime_record` | `pass` | `needs_human_review` | `deliverable_with_review` | 结构可交付，只需事实口径复核。 |
| `03-real-content-article` | `content_article` | `pass` | `pass` | `deliverable` | 未被正式报告规则误伤。 |
| `04-sample-meeting-note` | `meeting_note` | `pass` | `pass` | `deliverable` | 保留短会议纪要结构。 |
| `05-fixture-proposal` | `proposal` | `pass` | `needs_human_review` | `needs_content_revision` | 申请材料涉及预算、附件和行动项，需复核并修订。 |
| `06-fixture-technical` | `technical` | `pass` | `pass` | `needs_input` | 技术效果缺验证数据，扩写层正确提示补事实。 |
| `07-fixture-abstract-pass` | `abstract` | `pass` | `pass` | `deliverable` | 完整摘要通过。 |
| `08-fixture-abstract-incomplete` | `abstract` | `pass` | `needs_revision` | `needs_content_revision` | 空占位修复后，不完整摘要不再误判为可交付。 |
| `09-fixture-manual` | `manual` | `pass` | `needs_revision` | `needs_input` | 说明书缺前置条件、异常处理和事实边界。 |
| `10-fixture-short-input` | `formal_report` | `pass` | `needs_human_review` | `needs_input` | 极短输入只能形成骨架，需补事实和人工确认项。 |

本轮校准：

- `Delivery Recommendation` 已稳定使用 5 档状态：`deliverable`、`deliverable_with_review`、`needs_content_revision`、`needs_input`、`blocked`。
- `runtime_record` 不因正式报告章节规则被打回，但版本、端口、PID、运行数据仍进入人工复核。
- `content_article` 和 `meeting_note` 不再套 formal_report 全量规则。
- 扩写层生成的 `None`、`待补充`、`未提供` 等占位不再被辅助审查当作真实内容；避免空壳摘要或说明书被误判为 `deliverable`。
- 当前不建议让 `formal_revision` 消费 `assisted_quality_report` 和 `formal_expansion.revision_plan` 作为默认行为；这会从“结构占位修订”升级为“报告驱动二次改稿”，应单独拆一版 PRD。
