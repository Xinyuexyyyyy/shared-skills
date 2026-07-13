# Docx Quality Rules Backlog

## 定位

本文件是 `docx-quality-layer` 的规则池。它把待开发规则分成三类：

- `deterministic`：可以用脚本稳定检测。
- `assisted`：需要模型或人工阅读辅助判断，但必须输出证据。
- `human-gate`：必须由用户或负责人口径确认，不能自动判定。

规则进入实现前，必须有来源、适用文档类型和误判边界。

## 状态定义

| status | 含义 |
|---|---|
| `ready` | 可进入实现 |
| `draft` | 规则方向成立，但还要补样例 |
| `blocked` | 缺少可靠来源或误判风险太高 |
| `done` | 已实现并有测试 |

## 已实现规则

| code | type | dimension | status | 来源 | 说明 |
|---|---|---|---|---|---|
| `missing_h1` | deterministic | structure | done | docx-quality-layer v1 | 缺少总标题时阻断 |
| `multiple_h1` | deterministic | structure | done | docx-quality-layer v1 | 多个总标题时阻断 |
| `heading_level_jump` | deterministic | structure | done | docx-quality-layer v1 | 标题层级跳跃时阻断 |
| `unclosed_code_fence` | deterministic | docx_readiness | done | Markdown 渲染经验 | 未闭合代码块会破坏后续样式 |
| `raw_html` | deterministic | docx_readiness | done | docx 渲染经验 | 裸 HTML 可能泄漏到 docx 正文 |
| `emoji` | deterministic | formality | done | 中文正式文档源库 / 规则框架参考 | 正式 docx 中默认警告 |
| `bare_url` | deterministic | docx_readiness | done | 正式文档引用习惯 | 裸 URL 默认警告 |
| `weak_opener` | deterministic | formality | done | AI writing preset / 正式文档观察 | 开头套话默认警告 |
| `repeated_template_phrase` | deterministic | formality | done | textlint / Vale 规则模型 | 模板词重复默认警告 |
| `missing_required_section` | deterministic | completeness | done | NSFC / 中文说明书结构 | 按文档类型检查必要要素 |
| `long_sentence` | deterministic | formality | done | textlint technical writing | 长句作为建议 |
| `empty_section_after_heading` | deterministic | structure | done | GB/T 9704 / docx 编辑经验 | 标题后无正文时警告 |
| `mixed_subject_terms` | deterministic | formality | done | 中文正式文件一致性 | 主体称谓混用时警告 |
| `figure_or_table_missing_caption` | deterministic | docx_readiness | done | 论文式报告 / docx 可交付经验 | 图表缺少相邻说明时警告 |
| `missing_reference_section` | deterministic | completeness | done | 中文项目申报 / 标准编制说明 / 论文式报告引用习惯 | 正文含多个来源线索但缺参考资料区时警告 |
| `proposal_three_questions_incomplete` | assisted | completeness | done | CN-SRC-004 / CN-SRC-006 | 申请类材料缺“为什么做 / 做什么 / 研究基础或可行性”时警告 |
| `technical_chain_incomplete` | assisted | logic | done | CN-SRC-007 / CN-SRC-009 | 技术说明缺问题-方案-效果-边界链条时警告 |
| `abstract_four_elements_incomplete` | assisted | completeness | done | CN-SRC-010 / CN-SRC-012 / CN-SRC-013 / CN-SRC-014 / CN-SRC-015 | 摘要缺对象、方法、结果、意义/边界时警告 |
| `action_item_incomplete` | assisted | logic | done | CN-SRC-002 / CN-SRC-003 / CN-SRC-006 | 行动项只有弱动作、缺对象条件结果时警告 |
| `manual_task_chain_incomplete` | assisted | completeness | done | CN-SRC-008 / CN-SRC-011 | 说明书缺适用对象、前置条件、步骤、注意事项或异常处理时警告 |

## Deterministic Backlog

### DQ-D001：标题后无正文

- **status：** done
- **dimension：** structure
- **severity：** warning
- **source：** GB/T 9704、政府正式文件样本、docx 编辑经验
- **doc types：** all
- **rule：** 标题后直接出现同级或更高级标题，且中间没有正文、列表、表格或引用。
- **implemented code：** `empty_section_after_heading`
- **why：** 这类结构在 docx 里看起来像空章节，正式文档审阅体验差。
- **false positive：** 目录页、附件清单、纯提纲草稿。
- **suggested fix：** 补一段说明，或删除空章节。

### DQ-D002：连续列表缺少解释段

- **status：** draft
- **dimension：** structure
- **severity：** warning
- **source：** 政府报告样本、申请书完整性要求
- **doc types：** formal_report, proposal, policy
- **rule：** 连续 8 个以上列表项，前后没有解释段或结论段。
- **why：** 正式报告不应只堆要点，至少要交代分组逻辑或结论。
- **false positive：** 任务清单、检查表、附录。
- **suggested fix：** 在列表前补分组目的，在列表后补归纳结论。

### DQ-D003：主体称谓混用

- **status：** done
- **dimension：** formality
- **severity：** warning
- **source：** 中文正式文件一致性要求
- **doc types：** all
- **rule：** 同一文档混用“我/我们/本人/本项目/该项目/本报告”等主体称谓。
- **implemented code：** `mixed_subject_terms`
- **why：** 主体称谓不稳会造成责任边界不清。
- **false positive：** 引用原文、访谈材料、对比说明。
- **suggested fix：** 按文档类型统一为“本报告 / 本项目 / 本文 / 申请人”。

### DQ-D004：图表缺少标题或说明

- **status：** done
- **dimension：** docx_readiness
- **severity：** warning
- **source：** 论文式报告、说明书、正式 docx 可交付经验
- **doc types：** formal_report, paper_like, manual, proposal
- **rule：** 图片 Markdown 或表格前后缺少“图/表”说明。
- **implemented code：** `figure_or_table_missing_caption`
- **why：** docx 中图表脱离上下文后难以审阅。
- **false positive：** 装饰图、logo、临时草稿。
- **suggested fix：** 补图题、表题或一段用途说明。

### DQ-D005：参考资料区缺失但正文含外部来源

- **status：** done
- **dimension：** completeness
- **severity：** warning
- **source：** 中文项目申报、标准编制说明、论文式报告引用习惯
- **doc types：** proposal, paper_like, formal_report
- **rule：** 正文含多个链接、标准号或文献线索，但没有“参考资料/参考文献/来源”章节。
- **implemented code：** `missing_reference_section`
- **why：** 正式文档需要集中说明来源，方便审阅。
- **false positive：** 内部备忘、短说明。
- **suggested fix：** 增加参考资料章节或脚注说明。

## Assisted Backlog

### DQ-A001：结论是否有依据支撑

- **status：** ready
- **dimension：** logic
- **severity：** blocker 或 warning，按文档用途决定
- **source：** 政府报告、NSFC 申请说明、标准编制说明、专利撰写资料
- **doc types：** formal_report, proposal, paper_like
- **review question：** 重要结论前后是否能找到事实、数据、规则、来源或推理支撑。
- **required evidence：** 指出“结论句”和“缺失的依据类型”。
- **human boundary：** 不判断事实真假，只判断文内是否提供支撑。

### DQ-A002：章节是否围绕同一个主目标

- **status：** draft
- **dimension：** structure
- **severity：** warning
- **source：** 政府工作报告、正式说明书结构
- **doc types：** all
- **review question：** 一级章节是否都服务于文档目的，是否有游离段落。
- **required evidence：** 指出游离章节标题和为什么偏离主目标。
- **human boundary：** 创意稿、访谈稿不适用。

### DQ-A003：申请类文档是否只写意义、不写可行性

- **status：** done
- **dimension：** completeness
- **severity：** warning
- **source：** NSFC 申请书改版说明、国家重点研发计划填报通知
- **doc types：** proposal
- **review question：** 是否只有研究意义和目标，没有方法、条件、基础或风险控制。
- **required evidence：** 指出缺少的申请要素。
- **human boundary：** 不评价项目能不能立项，只评价材料是否完整。
- **implemented code：** `proposal_three_questions_incomplete`

### DQ-A004：说明书是否缺少异常处理

- **status：** done
- **dimension：** completeness
- **severity：** warning
- **source：** GB/T 19678 使用说明编制、CNIPA 说明书撰写资料
- **doc types：** manual
- **review question：** 是否只有正常步骤，没有失败、异常、注意事项或边界条件。
- **required evidence：** 指出步骤段和缺失的异常处理类型。
- **human boundary：** 简短快速指南可降级为 suggestion。
- **implemented code：** `manual_task_chain_incomplete`

### DQ-A005：摘要是否同时交代对象、方法、结果和意义

- **status：** done
- **dimension：** completeness
- **severity：** warning
- **source：** 教育部论文/成果材料、CNIPA 摘要/说明书要求、中国科技论文在线、ChinaXiv、国家哲学社会科学文献中心、中文期刊投稿须知
- **doc types：** abstract, paper_like
- **review question：** 摘要是否缺对象、方法、结果、意义或边界中的关键项。
- **required evidence：** 标出已有要素和缺失要素。
- **human boundary：** 不要求所有摘要都固定四段式。
- **implemented code：** `abstract_four_elements_incomplete`

### DQ-A006：技术说明是否形成问题-方案-效果链

- **status：** done
- **dimension：** logic
- **severity：** warning
- **source：** CNIPA 专利申请文件撰写资料、标准编制说明
- **doc types：** technical_disclosure, patent_like
- **review question：** 技术说明是否交代技术问题、技术方案、技术效果和边界条件。
- **required evidence：** 标出已有要素和缺失要素。
- **human boundary：** 不判断技术先进性、专利新颖性或侵权边界。
- **implemented code：** `technical_chain_incomplete`

### DQ-A007：行动项是否具备对象、动作、条件、结果

- **status：** done
- **dimension：** logic
- **severity：** warning
- **source：** 国务院办公厅通知、政府工作报告、国家重点研发计划申报通知
- **doc types：** all
- **review question：** 建议、措施或任务是否只有“加强/推动/完善/提升”等弱动作。
- **required evidence：** 标出弱行动项示例和缺失要素。
- **human boundary：** 不判断组织分工真实性，只提示表达和执行要素缺口。
- **implemented code：** `action_item_incomplete`

## Human Gate Backlog

### DQ-H001：事实真实性

- **status：** ready
- **dimension：** logic
- **severity：** human-gate
- **source：** 所有正式文档来源
- **doc types：** all
- **gate：** 涉及数据、政策、标准、论文结论、项目经历时，必须由用户确认或提供来源。
- **automation boundary：** 脚本只能提示“需要来源”，不能判真伪。

### DQ-H002：机构口径和敏感措辞

- **status：** ready
- **dimension：** formality
- **severity：** human-gate
- **source：** 政府文件、基金申请、制度文件
- **doc types：** proposal, policy, formal_report
- **gate：** 是否符合机构、学校、评审、甲方或公开发布口径。
- **automation boundary：** 模型只能标出可能敏感措辞，最终由人确认。

### DQ-H003：申请材料合规性

- **status：** ready
- **dimension：** completeness
- **severity：** human-gate
- **source：** NSFC 指南、国家重点研发计划通知、教育部成果申报、政务服务指南
- **doc types：** proposal
- **gate：** 页数、附件、伦理、预算、格式、匿名要求等合规项。
- **automation boundary：** 需要以具体当年指南为准，不能靠通用规则猜。

## 进入实现的门槛

一条规则从 backlog 进入脚本前，必须满足：

1. 有明确 `code`。
2. 有至少 1 个正例和 1 个反例。
3. 能说明误判场景。
4. 有 `severity` 默认值。
5. 有测试 fixture。

Assisted 规则进入实现前，额外要求：

1. 输出必须带 evidence。
2. 不允许只输出分数。
3. 不自动改正文。
4. 需要人工确认的内容必须写入 `human-gate`，不能伪装成自动判断。
