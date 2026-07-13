# 正式文档质量源库 v1

## 定位

质量源库不是语料仓库，也不是全文转载库。它只保存公开来源的入口、文档类型、可提炼规则和采样建议。

原则：

- 优先使用官方、开源、可长期访问的来源。
- 默认不保存全文，只保存链接、元数据、短观察和规则提炼。
- 引用外部文本时只保留短摘录，并记录来源。
- 每类来源至少对应一个质量维度，避免为了“看起来丰富”而堆链接。

## 来源分层

### A 类：中文规范与标准

用于提炼正式 docx 的结构、格式、说明书和标准化表达。

| 来源 | 类型 | 用途 | 可提炼维度 |
|---|---|---|---|
| GB/T 9704-2012 党政机关公文格式 | 公文格式标准 | 中文正式 docx 的页面、标题、公文格式参考 | docx 可交付性、结构性 |
| GB/T 19678 使用说明编制 | 使用说明标准 | 说明书构成、内容和表示方法 | 完整性、异常处理、读者任务 |
| 国家标准编制说明 / 征求意见稿 | 标准编制材料 | 编制原则、主要内容、确定依据 | 逻辑性、依据支撑 |

### B 类：中文正式文档样本

用于观察正式文件如何组织目的、依据、要求和行动项。

| 来源 | 类型 | 用途 | 可提炼维度 |
|---|---|---|---|
| 政府工作报告公开全文 | 政府报告 | 宏观报告的分节、数据支撑、任务表述 | 结构性、逻辑性 |
| 国务院/国务院办公厅通知与意见 | 政策文件 | 通知、意见、实施细则的结构和措辞 | 正式性、完整性、执行边界 |
| 政务服务事项材料要求 | 办事材料指南 | 材料清单、真实性、格式规范、提交对象 | human-gate、完整性 |

### C 类：中文科研 / 项目 / 知识产权材料

用于支撑申请书、项目书、技术说明、摘要和成果材料规则。

| 来源 | 类型 | 用途 | 可提炼维度 |
|---|---|---|---|
| NSFC 申请书改版说明 / 项目指南 | 基金申请要求 | 立项依据、研究内容、研究基础、合规边界 | 完整性、简洁性、human-gate |
| 国家重点研发计划申报书填报通知 | 科技项目申报 | 指标、研究内容、预算、附件、一致性 | 完整性、一致性、human-gate |
| CNIPA 专利申请文件撰写资料 | 技术/专利材料 | 技术问题、技术方案、技术效果、权利边界 | 逻辑性、图表说明、human-gate |
| 教育部论文抽检 / 成果申报 / 年度报告要求 | 教育科研材料 | 摘要、成果、真实性、提交清单 | 完整性、真实性、human-gate |
| 中国科技论文在线 | 中文科技论文平台 | 科技论文摘要、关键词、正文结构和参考文献 | 摘要完整性、方法/结果、参考资料 |
| ChinaXiv 中国科学院科技论文预发布平台 | 中文预印本平台 | 预印本摘要、学科分类、版本边界 | 摘要结构、阶段性结论边界 |
| 国家哲学社会科学文献中心 | 中文社科文献平台 | 社科论文摘要、关键词、基金资助和来源 | 论证路径、资料来源、摘要完整性 |
| 中国社会科学杂志社投稿须知 | 中文期刊投稿要求 | 摘要、关键词、注释、格式和引文 | 论文格式、关键词、参考/注释体系 |

### D 类：规则框架参考（非源库）

这些项目只用于借鉴规则组织方式，不作为中文正式文档内容标准。

| 来源 | 类型 | 用途 | 可提炼维度 |
|---|---|---|---|
| Vale | prose linter | severity、alert、suggestion、markup-aware | 规则模型 |
| textlint | natural language linter | preset、formatter、fix/dry-run | 工作流 |
| textlint AI writing preset | AI 写作模式规则 | 结构化检测思路 | 规则组织 |

## 第一批来源入口

- GB/T 9704-2012 党政机关公文格式：`https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=F3CC9BEF482524C895FDA7A08BB4A70E`
- 政府工作报告公开全文：`https://www.ndrc.gov.cn/fzggw/jgsj/zys/sjdt/202403/t20240320_1365089.html`
- 国务院办公厅通知 / 中办国办意见样本：`https://gaj.gz.gov.cn/gkmlpt/content/10/10419/post_10419024.html`、`https://www.mee.gov.cn/zcwj/zyygwj/201912/t20191225_751530.shtml`
- 国家自然科学基金申请书改版说明：`https://www.nsfc.gov.cn/p1/3381/2821/99242.html`
- 国家自然科学基金项目申请与结题通告：`https://www.nsfc.gov.cn/p1/3381/2824/99667.html`、`https://www.nsfc.gov.cn/p1/3381/2824/100064.html`
- 国家重点研发计划申报书填报通知：`https://www.most.gov.cn/tztg/202009/t20200916_158773.html`、`https://www.most.gov.cn/tztg/201604/t20160425_125309.html`、`https://www.most.gov.cn/tztg/201803/t20180326_138786.html`
- CNIPA 专利申请文件撰写资料：`https://www.cnipa.gov.cn/art/2017/2/21/art_2651_167329.html`、`https://www.cnipa.gov.cn/2020-04/20200402105538938313.pdf`
- GB/T 19678 使用说明编制：`https://std.samr.gov.cn/gb/search/gbDetailed?id=71F772D7816AD3A7E05397BE0A0AB82A`
- 国家标准编制说明 / 征求意见稿：`https://std.samr.gov.cn/`
- 教育部论文抽检 / 成果申报 / 年度报告要求：`https://www.moe.gov.cn/srcsite/A13/s7061/202211/t20221128_1006758.html`、`https://fx.xwapp.moe.gov.cn/article/202201/61e5168c695ccf00015c8065.html`、`https://www.moe.gov.cn/srcsite/A20/s7068/201501/t20150126_189316.html`
- 政务服务事项材料要求：`https://zwfw.moe.gov.cn/guidedetail?active=2&id=6b31faff-001a-4eec-b8d8-10a07e5630c0&taskcode=12100000400000536Y1002105003000&type=public`
- 中国科技论文在线：`https://www.paper.edu.cn/`
- ChinaXiv 中国科学院科技论文预发布平台：`https://chinaxiv.org/home.htm`
- 国家哲学社会科学文献中心：`https://www.ncpssd.org/`、`https://www.ncpssd.cn/`
- 中国社会科学杂志社投稿须知：`https://sscp.cssn.cn/tzgg/202502/t20250227_5849425.shtml`
- 规则框架参考：Vale `https://github.com/vale-cli/vale`；textlint `https://github.com/textlint/textlint`；textlint AI writing preset `https://github.com/textlint-ja/textlint-rule-preset-ai-writing`

## 第一批规则来源记录

第一批中文规则来源已经改由 `docs/formal-source-sampling-v1.md` 维护。该文件覆盖 CN-SRC-001 到 CN-SRC-011，并明确每个来源的可迁移规则、不可迁移边界和进入规则池的位置。

规则框架参考仍可用于 `severity / code / evidence / fix` 等报告结构，但不能作为 assisted review 或 human gate 的内容依据。

## 源库记录 schema

```yaml
id: nsfc-proposal-2026-slim-quality
name: 国家自然科学基金申请书改版说明
source_type: official-guidance
url: https://www.nsfc.gov.cn/p1/3381/2821/99242.html
language: zh-CN
doc_family: proposal
license_or_access: public web page; no full-text redistribution
quality_dimensions:
  - completeness
  - conciseness
  - logic
extract_policy:
  store_full_text: false
  allow_short_quotes: true
  max_quote_words: 25
derived_rules:
  - 申请类文档应优先讲清为什么做、做什么、已有基础，而不是堆套路话术。
  - 篇幅增加不等于质量提升；正式申请材料应鼓励简洁表达。
notes: first batch source
```

## 规则提炼记录 schema

```yaml
rule_id: DQ-A003
name: 申请类文档是否只写意义、不写可行性
source_ids:
  - SRC-002
rule_type: assisted
dimension: completeness
doc_types:
  - proposal
default_severity: warning
principle: 申请类文档不能只有研究意义，还要说明研究内容、可行性和基础条件。
check_item: 是否缺少方法、条件、基础或风险控制。
fix_hint: 补充研究路径、已有基础、可行性依据或预期成果。
automation_boundary: 不评价项目是否值得立项，只评价材料是否完整。
status: ready
```

## 采样方法

每一类正式文档最多先抽 5 篇或 5 个页面，不追求大规模。

采样后只记录：

- 文档类型。
- 章节结构。
- 开头如何交代目的。
- 依据如何出现。
- 结论或行动如何落地。
- 可迁移规则。
- 不可迁移原因。

## 质量源库到规则的转化

转化时只做三类产物：

1. **原则**：例如“申请类文档先讲清研究价值和研究思路”。
2. **检查项**：例如“是否有立项依据、研究内容、研究基础”。
3. **修订建议**：例如“删除泛泛意义铺垫，把研究对象和问题前移”。

不得直接生成：

- 原文段落模板。
- 伪官方措辞。
- 未授权全文集合。

## 第一批采样记录

已完成第一批源库采样，详见：

- `docs/formal-source-sampling-v1.md`
- `docs/formal-method-extraction-protocol-v1.md`
- `docs/formal-writing-methodology-v1.md`

该采样覆盖：

- GB/T 9704-2012 党政机关公文格式
- 国务院办公厅通知 / 中办国办意见
- 政府工作报告公开全文
- NSFC 2026 申请书改版说明
- NSFC 2026 项目申请与结题通告 / 项目指南
- 国家重点研发计划申报书填报通知
- CNIPA 专利申请文件撰写资料
- GB/T 19678 使用说明编制
- 国家标准编制说明 / 征求意见稿
- 教育部论文抽检 / 成果申报 / 年度报告要求
- 政务服务事项材料要求
- 中国科技论文在线
- ChinaXiv 中国科学院科技论文预发布平台
- 国家哲学社会科学文献中心
- 中国社会科学杂志社投稿须知

这些中文采样已经为 assisted review 和 human gate 提供第一批依据。后续新增规则时，先补中文采样记录，再写规则。外文资料和开源项目不能作为中文正式文档质量源库依据。
