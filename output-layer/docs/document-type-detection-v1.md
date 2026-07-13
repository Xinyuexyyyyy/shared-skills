# Document Type Detection v1

## 目标

把 `output-layer` 的正式 docx 质量链路从“默认全部当 formal_report”改为“先识别文档类型，再套对应质量门”。

第一版只解决真实回放中最明显的误伤：

- 公众号/内容稿不应被正式报告规则要求补背景、目的、依据、结论。
- 运行记录/系统扫描不应被申请书或正式报告结构误伤，但版本、端口、PID 等事实仍需人工复核。
- 会议纪要应保留短结构，不强制扩成完整报告。

## 识别顺序

1. frontmatter 显式 `doc_type` / `type` 优先。
2. 标题和章节信号次之。
3. 正文中的运行事实信号辅助判断。
4. 无明确信号时回落到 `formal_report`。

## 当前类型

| 类型 | 典型信号 | 当前处理 |
|---|---|---|
| `formal_report` | 背景、目的、方案、依据、结论等 | 走正式报告质量门 |
| `proposal` | 立项依据、研究目标、研究内容、预期成果 | 走申请类三问结构 |
| `technical` / `technical_disclosure` | 技术问题、技术方案、技术效果、实施方式 | 走技术问题-方案-效果-边界链 |
| `abstract` | 对象、方法、结果、意义 | 走摘要四要素 |
| `manual` | 适用对象、前置条件、操作步骤、异常处理 | 走说明书任务链 |
| `runtime_record` | 系统概况、运行记录、全景扫描 + 版本/端口/PID/IP | 不强制 formal_report 全要素；保留人工事实复核 |
| `meeting_note` | 会议纪要、讨论结果、后续动作 | 不强制正式报告全要素 |
| `content_article` | 标题备选、核心命题、正文 | 不触发正式报告主体称谓和必要章节检查 |

## 类型化质量门配置

| 类型 | 必查项 | 不强制项 |
|---|---|---|
| `formal_report` | 单一总标题、标题层级、背景/目的/方案/依据/结论、参考资料区、主体称谓一致性、图表说明 | 无 |
| `runtime_record` | 单一总标题、标题层级、运行概况、验证结果、后续处理、运行事实人工复核 | 参考资料区、主体称谓一致性 |
| `meeting_note` | 单一总标题、讨论结果、后续动作 | 参考资料区、主体称谓一致性、图表说明 |
| `content_article` | 单一总标题、明显套话、重复模板表达、渲染阻断项 | formal_report 必要章节、参考资料区、主体称谓一致性、图表说明 |

`runtime_record` 的专用规则：

- 如果只有版本、端口、PID、IP 等运行事实，但没有验证结果或后续处理，会触发 `runtime_record_missing_verification`。
- 运行事实本身不由质量门判断真伪；由辅助审查输出 `needs_human_review`，最终进入 `Delivery Recommendation`。

## 接入点

- `src/document_classifier.py`
- `src/docx_quality_checker.py`
- `src/formal_assisted_reviewer.py`
- `src/formal_expander.py`

## 回放结果

回放目录：

`/Users/sure/Daily Work/output/output-layer-doc-type-replay-20260625/`

| 样本 | 识别类型 | Delivery | 判断 |
|---|---|---|---|
| OpenClaw 系统扫描 | `runtime_record` | `deliverable_with_review` | 结构通过，版本/端口/PID 等运行事实需人工复核 |
| 孝顺内容稿 | `content_article` | `deliverable` | 不再被 formal_report 必要章节和主体称谓规则误伤 |
| 会议纪要样例 | `meeting_note` | `deliverable` | 保留短会议纪要结构，质量门通过 |

类型化配置回放目录：

`/Users/sure/Daily Work/output/output-layer-type-config-replay-20260625/`

| 样本 | 识别类型 | docx 质量门 | 辅助审查 | Delivery |
|---|---|---|---|---|
| OpenClaw 系统扫描 | `runtime_record` | `pass` | `needs_human_review` | `deliverable_with_review` |
| 孝顺内容稿 | `content_article` | `pass` | `pass` | `deliverable` |
| 会议纪要样例 | `meeting_note` | `pass` | `pass` | `deliverable` |

Delivery Recommendation 细分回放目录：

`/Users/sure/Daily Work/output/output-layer-delivery-recommendation-replay-20260625/`

| 样本 | 状态 | 含义 |
|---|---|---|
| OpenClaw 系统扫描 | `deliverable_with_review` | 文件结构可交付，但版本、端口、PID 等事实口径需人工复核 |
| 产品调研短报告 | `needs_content_revision` | 文件已生成，但结构和内容密度不足，需修正文稿 |
| 短输入扩写样本 | `needs_input` | 文件已生成，但缺事实依据、行动项或人工确认项 |

当前 `Delivery Recommendation` 状态：

| 状态 | 使用场景 |
|---|---|
| `deliverable` | 未发现阻断项，可作为当前版本交付 |
| `deliverable_with_review` | 结构可交付，但存在版本、端口、PID、政策、机构口径等需人工复核事项 |
| `needs_content_revision` | 正文结构、表达、参考资料区、行动项形态等需要修订 |
| `needs_input` | 缺事实、依据、样例、验证记录或人工确认项，扩写层不能安全补齐 |
| `blocked` | docx 未生成或 strict 质量门阻断 |

## 边界

- 第一版不是 LLM 分类器，不做语义深判。
- 分类只影响质量门和扩写策略，不改变原文事实。
- `content_article` 的“可交付”只表示不适合用 formal_report 规则继续拦截，不代表文章质量已经达到发布标准；内容稿后续应接内容稿专用质量门。
