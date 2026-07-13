# Formal Source Sampling v1（中文源库版）

## 定位

本文件是 `docx-quality-layer` 的第一批中文源库采样记录。

新约束：源库只从中文语境获取。外文写作指南、国外基金指南、arXiv 等不再作为正式文档质量源库依据。开源项目如 Vale/textlint 只能作为“规则组织方式参考”，不能作为中文正式文档内容标准。

本文件不保存全文，只记录：

- 来源入口。
- 文档类型。
- 结构观察。
- 可迁移规则。
- 不可迁移边界。
- 对 deterministic / assisted / human-gate 的影响。

## 采样规则

- 只选中文语境来源，优先官方、标准、公共服务平台、教育/科研主管部门、知识产权机构。
- 每个来源只记录结构观察和规则提炼，不搬运长段原文。
- 能脚本化的规则进入 deterministic backlog。
- 需要理解上下文的规则进入 assisted backlog。
- 需要用户、机构、当年指南或具体场景确认的规则进入 human-gate。

## 中文来源矩阵

| 角度 | 样本类型 | 主要价值 |
|---|---|---|
| 公文/政策 | 国务院办公厅通知、意见、实施方案 | 正式语体、对象、行动项、执行边界 |
| 政府报告 | 政府工作报告 | 大型正式报告的章节组织和论证递进 |
| 科研基金 | NSFC 申请通告、申请书改版说明、项目指南 | 申请类完整性、简洁性、合规边界 |
| 科技项目 | 国家重点研发计划填报通知、申报系统说明 | 项目申报材料一致性、指标、预算、附件 |
| 专利文件 | CNIPA 专利申请文件撰写资料 | 技术问题、技术方案、技术效果、权利边界 |
| 标准/规范 | 国家标准、标准编制说明 | 术语、范围、规范性结构、依据说明 |
| 使用说明 | GB/T 19678 使用说明编制 | 说明书结构、前置条件、步骤、警告、异常 |
| 教育/论文 | 教育部论文抽检、成果申报、年度报告要求 | 摘要/论文/报告规范、真实性和学术行为 |
| 政务服务 | 教育部政务服务事项材料要求 | 材料真实性、格式规范、提交清单 |
| 中文论文 | 中国科技论文在线、ChinaXiv、国家哲学社会科学文献中心、中文期刊投稿须知 | 摘要、关键词、研究问题、方法、结果、参考文献 |

## Sample 1：GB/T 9704-2012 党政机关公文格式

- **source id：** CN-SRC-001
- **source type：** official-standard
- **url：** `https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=F3CC9BEF482524C895FDA7A08BB4A70E`
- **doc family：** policy, formal_report
- **angle：** docx 格式与正式文件结构

### 结构观察

- 该来源适合支撑 docx 可交付性，而不是内容论证规则。
- 对 output-layer 的价值在“标题、正文、附件、页眉页脚、版式要服务正式审阅”。
- 不能把党政机关公文格式强套到论文、说明书或申请材料。

### 可迁移规则

- Markdown 或 HTML 控制符不得泄漏到正式 docx 正文。
- 标题层级必须稳定，不能让 docx 渲染后看不出结构。
- 正式 docx 应避免空章节、混乱标题和不可审阅的附件/图表。

### 进入规则池

- deterministic：`missing_h1`, `multiple_h1`, `heading_level_jump`, `raw_html`, `unclosed_code_fence`, `empty_section_after_heading`
- human-gate：机构格式、页眉页脚、公文专用格式是否符合具体要求

## Sample 2：国务院办公厅通知 / 中办国办意见

- **source id：** CN-SRC-002
- **source type：** official-policy-sample
- **url examples：**
  - `https://gaj.gz.gov.cn/gkmlpt/content/10/10419/post_10419024.html`
  - `https://www.mee.gov.cn/zcwj/zyygwj/201912/t20191225_751530.shtml`
- **doc family：** policy
- **angle：** 正式语体、执行对象、实施要求

### 结构观察

- 通知类文件通常包含发文对象、文件名称、贯彻要求、发布日期和公开属性。
- 意见/实施细则类文件通常先说明背景和总体要求，再分条列出任务、机制、责任或保障。
- 正式政策文本强调“谁执行、执行什么、按什么原则、如何落实”。

### 可迁移规则

- policy 文档应检查适用对象、职责、流程、例外和执行机制。
- 行动项不能只写原则，应尽量包含对象、动作、条件或结果。
- 章节标题应承担组织职责，不应只是口号。

### 不可迁移边界

- 不模仿政府口吻生成伪官方文本。
- 不把政策文件的宏观语体套到技术说明书。

### 进入规则池

- assisted：`DQ-A002`
- human-gate：`DQ-H002`

## Sample 3：政府工作报告公开全文

- **source id：** CN-SRC-003
- **source type：** official-report-sample
- **url：** `https://www.ndrc.gov.cn/fzggw/jgsj/zys/sjdt/202403/t20240320_1365089.html`
- **doc family：** formal_report
- **angle：** 大型正式报告结构、措施群、目标递进

### 结构观察

- 文档采用大章节编号，每个章节通常先给总判断，再展开分项措施。
- 段落中常见“动作 + 对象 + 政策/机制 + 目标效果”的组合。
- 这类正式报告不是短句堆叠，而是“方向句 + 措施群 + 责任/边界”的结构。

### 可迁移规则

- formal_report 的 assisted review 应检查一级章节是否服务同一个主目标。
- 行动建议应尽量包含对象、动作、条件或目标效果。
- 连续列表或措施堆叠后，需要有分组逻辑或归纳说明。

### 不可迁移边界

- 不把宏观政策报告的长段结构套到短说明书或摘要。
- 不把政策话语当成所有正式文档的默认风格。

### 进入规则池

- deterministic：`empty_section_after_heading`, `mixed_subject_terms`
- assisted：`DQ-A002`

## Sample 4：NSFC 2026 申请书改版说明

- **source id：** CN-SRC-004
- **source type：** official-guidance
- **url：** `https://www.nsfc.gov.cn/p1/3381/2821/99242.html`
- **doc family：** proposal
- **angle：** 基金申请书完整性、简洁性、反套路表达

### 结构观察

- 该来源把申请书从“套路化提纲”收敛到少数核心部分：为什么做、做什么、已有基础。
- 它强调简洁表达，反对用篇幅堆质量。
- 对 output-layer 的关键价值是：申请类文档完整性不是“章节越多越好”，而是核心问题是否说清。

### 可迁移规则

- proposal 文档必须检查立项依据、研究内容、研究基础或等价信息。
- assisted review 应检查“只写意义、不写可行性或基础”的问题。
- 修订建议应鼓励删除套路化铺垫，把研究对象、价值、内容和基础前移。

### 不可迁移边界

- 不把具体年度页数、系统表格和申报口径写死进通用规则。
- 不自动判断创新性和资助可能性。

### 进入规则池

- deterministic：`missing_required_section`
- assisted：`DQ-A003`
- human-gate：`DQ-H003`

## Sample 5：NSFC 2026 项目申请与结题通告 / 项目指南

- **source id：** CN-SRC-005
- **source type：** official-guidance
- **url examples：**
  - `https://www.nsfc.gov.cn/p1/3381/2824/99667.html`
  - `https://www.nsfc.gov.cn/p1/3381/2824/100064.html`
- **doc family：** proposal
- **angle：** 申请属性、预算、合作研究、附件和提交合规

### 结构观察

- 申请材料不仅是正文质量，还包括研究属性、资金管理方式、合作分工、预算和附件材料。
- 指南类文本的关键是“适用项目类型 + 填报要求 + 提交流程 + 附件/签章边界”。

### 可迁移规则

- proposal human-gate 必须提示“以当年指南和项目类型为准”。
- 出现预算、合作单位、附件、签章等关键词时，不应自动给出合规结论，只能提示人工确认。
- 申请类文档若含合作研究，应检查分工、协议或责任边界是否出现。

### 不可迁移边界

- 不用通用规则替代当年项目指南。
- 不自动判断预算合理性或申报资格。

### 进入规则池

- assisted：申请材料边界检查
- human-gate：`DQ-H003`

## Sample 6：国家重点研发计划申报书填报通知

- **source id：** CN-SRC-006
- **source type：** official-project-notice
- **url examples：**
  - `https://www.most.gov.cn/tztg/202009/t20200916_158773.html`
  - `https://www.most.gov.cn/tztg/201604/t20160425_125309.html`
  - `https://www.most.gov.cn/tztg/201803/t20180326_138786.html`
- **doc family：** proposal, project_report
- **angle：** 项目申报一致性、指标、预算、材料提交

### 结构观察

- 国家重点研发计划填报通知强调预申报书与正式申报书的一致性。
- 常见要求包括：负责人、单位、专项方向、任务数、考核指标、研究内容、配套条件、预算、纸质材料或系统提交。
- 这类来源能补足 NSFC 之外的“工程/任务型项目申报”语境。

### 可迁移规则

- 项目申报文档要检查指标、研究内容、参与单位、预算和附件之间的一致性。
- 若文档出现“指标、预算、任务、课题、单位”等词，应进入 human-gate 合规确认。
- assisted review 可检查“目标/指标是否有对应研究内容”。

### 不可迁移边界

- 不自动判断指标是否能达成。
- 不把某个专项要求套到所有项目书。

### 进入规则池

- assisted：目标-内容-指标一致性
- human-gate：项目申报合规

## Sample 7：CNIPA 专利申请文件撰写资料

- **source id：** CN-SRC-007
- **source type：** official-ip-guidance
- **url examples：**
  - `https://www.cnipa.gov.cn/art/2017/2/21/art_2651_167329.html`
  - `https://www.cnipa.gov.cn/2020-04/20200402105538938313.pdf`
  - `https://www.cnipa.gov.cn/jact/front/mailpubdetail.do?sysid=6&transactId=496136`
- **doc family：** technical_disclosure, patent_like, manual
- **angle：** 技术问题、技术方案、技术效果、权利边界

### 结构观察

- 专利申请文件强调说明书、权利要求书、摘要和附图的职责不同。
- 技术说明必须围绕技术问题、技术方案和技术效果展开。
- 权利要求具有边界功能，不能用营销式表达替代技术特征。

### 可迁移规则

- 技术方案类文档应检查“问题-方案-效果”链条是否完整。
- 说明书/技术报告应避免广告式宣传用语。
- 图表和附图应有说明，不能只放图不解释。

### 不可迁移边界

- 不自动撰写权利要求。
- 不判断专利的新颖性、创造性或侵权边界。

### 进入规则池

- deterministic：`figure_or_table_missing_caption`
- assisted：技术问题-方案-效果链条
- human-gate：知识产权边界

## Sample 8：GB/T 19678 使用说明编制

- **source id：** CN-SRC-008
- **source type：** national-standard
- **url：** `https://std.samr.gov.cn/gb/search/gbDetailed?id=71F772D7816AD3A7E05397BE0A0AB82A`
- **doc family：** manual
- **angle：** 使用说明书构成、内容、表示方法

### 结构观察

- 该入口显示 GB/T 19678-2005 已废止，并被 GB/T 19678.1-2018 替代。
- 虽然旧标准不再作为当前要求，但它说明“说明书的构成、内容、表示方法”本身是标准化对象。
- 对 output-layer 的价值在于说明书不能只有步骤，还要有适用对象、条件、警告、限制和异常。

### 可迁移规则

- manual 文档应检查适用对象、前置条件、步骤、注意事项、异常处理。
- assisted review 应检查是否只有正常步骤，没有边界或失败处理。

### 不可迁移边界

- 不引用废止标准作为现行合规依据。
- 不把电气/工业说明书规范直接套到所有用户手册。

### 进入规则池

- deterministic：`missing_required_section`
- assisted：`DQ-A004`

## Sample 9：标准编制说明 / 征求意见稿

- **source id：** CN-SRC-009
- **source type：** standard-drafting-material
- **url examples：**
  - `https://std.samr.gov.cn/dcpspTools/gbPlan/download?path=%2Fzxd%2F2024006409%2F20_%E6%A0%87%E5%87%86%E8%B5%B7%E8%8D%89%2F20_DI_2024006409_%E5%AE%89%E5%85%A8%E4%B8%8E%E5%BA%94%E6%80%A5%E5%AE%A3%E4%BC%A0%E6%95%99%E8%82%B2%E4%BD%93%E9%AA%8C%E5%9F%BA%E5%9C%B0%E9%80%9A%E7%94%A8%E8%A6%81%E6%B1%82.pdf`
  - `https://std.samr.gov.cn/dcpspTools/gbPlan/download?path=%2Fzxd%2F2024001885%2F20_%E6%A0%87%E5%87%86%E8%B5%B7%E8%8D%89%2F20_DI_2024001885_%E8%B0%83%E5%BA%A6%E7%BB%9E%E8%BD%A6.pdf`
- **doc family：** standard, formal_report
- **angle：** 编制原则、主要内容、确定依据

### 结构观察

- 标准编制说明通常强调任务来源、编制原则、主要技术内容、确定依据、意见处理等。
- 这类文档非常适合支撑“结论/条款必须有依据”的 assisted review。

### 可迁移规则

- 规范/标准类文档应检查范围、术语、技术内容和依据。
- 重要条款或结论应能找到确定依据。
- 如果正文大量给出规则但没有依据说明，应进入 warning。

### 不可迁移边界

- 不自动判断标准条款科学性。
- 不把征求意见稿当作最终标准依据。

### 进入规则池

- assisted：`DQ-A001`
- human-gate：事实和标准现行性确认

## Sample 10：教育部成果申报 / 论文抽检 / 年度报告要求

- **source id：** CN-SRC-010
- **source type：** education-official-guidance
- **url examples：**
  - `https://www.moe.gov.cn/srcsite/A13/s7061/202211/t20221128_1006758.html`
  - `https://fx.xwapp.moe.gov.cn/article/202201/61e5168c695ccf00015c8065.html`
  - `https://www.moe.gov.cn/srcsite/A20/s7068/201501/t20150126_189316.html`
- **doc family：** paper_like, annual_report, application_material
- **angle：** 学术材料真实性、格式、提交清单、年度报告

### 结构观察

- 教育类材料常把“成果范围、资格要求、申报材料、报送方式、格式要求”分开。
- 论文抽检和成果申报强调真实性、规范性、材料完整性。
- 年度报告要求说明“固定格式 + 截止时间 + 报送对象”是管理类文档的重要结构。

### 可迁移规则

- paper_like / annual_report 文档应检查摘要、方法、结果、材料真实性和提交清单。
- 出现“申报、评审、抽检、报送、附件”等场景时，应进入 human-gate。
- 论文式文档的 assisted review 应检查是否缺对象、方法、结果、讨论或局限。

### 不可迁移边界

- 不自动判断学术不端。
- 不替代学校或主管部门的具体格式要求。

### 进入规则池

- assisted：`DQ-A005`
- human-gate：`DQ-H001`, `DQ-H003`

## Sample 11：政务服务材料要求

- **source id：** CN-SRC-011
- **source type：** public-service-guidance
- **url：** `https://zwfw.moe.gov.cn/guidedetail?active=2&id=6b31faff-001a-4eec-b8d8-10a07e5630c0&taskcode=12100000400000536Y1002105003000&type=public`
- **doc family：** application_material, checklist
- **angle：** 材料真实性、格式规范、提交清单

### 结构观察

- 政务服务材料强调内容真实、格式规范、材料清单、办理流程和条件。
- 这类来源适合支撑 human-gate：材料是否真实、是否符合办理事项要求，不能自动判。

### 可迁移规则

- 申请材料类文档应检查是否有提交对象、材料清单、格式要求和真实性声明。
- 出现证件、证明、认证、办理等场景时，应提示人工确认材料合规。

### 不可迁移边界

- 不判断材料真伪。
- 不替代政务平台当次办事指南。

### 进入规则池

- human-gate：`DQ-H001`, `DQ-H003`

## Sample 12：中国科技论文在线

- **source id：** CN-SRC-012
- **source type：** chinese-open-paper-platform
- **url examples：**
  - `https://www.paper.edu.cn/`
  - `https://www.moe.gov.cn/jyb_xwfb/xw_ft/moe_46/moe_1055/tnull_12806.html`
  - `https://www.edu.cn/rd/gai_kuang/xin_wen_gong_gao/200604/t20060428_176540.shtml`
- **doc family：** paper_like, abstract, technical_report
- **angle：** 中文科技论文摘要、关键词、正文结构和稿件格式

### 结构观察

- 该平台由教育部相关机构主办，定位是科技论文在线发表和学术交流。
- 适合抽样中文科技论文的题名、摘要、关键词、学科分类和参考文献线索。
- 稿件格式资料可以支撑“摘要、关键词、正文、参考文献”等基本论文结构要求。

### 可迁移规则

- paper_like 文档应检查摘要、关键词、研究对象、方法、结果和参考资料区。
- 技术论文类文档如果只有背景和意义，没有方法或结果，应进入 assisted warning。
- 正文出现多处外部文献、标准或链接时，应有参考资料/参考文献区。

### 不可迁移边界

- 不抓取或保存全文。
- 不把平台上的单篇论文质量当作质量标准，只用作结构观察。
- 不判断论文是否通过同行评议。

### 进入规则池

- deterministic：`missing_reference_section`
- assisted：`DQ-A001`, `DQ-A005`
- human-gate：`DQ-H001`

## Sample 13：ChinaXiv 中国科学院科技论文预发布平台

- **source id：** CN-SRC-013
- **source type：** chinese-preprint-platform
- **url examples：**
  - `https://chinaxiv.org/home.htm`
  - `https://chinaxiv.org/newsletter/newsletter20170321.html`
  - `https://lib.tsinghua.edu.cn/info/1375/6060.htm`
  - `https://library.usts.edu.cn/info/1208/3423.htm`
- **doc family：** paper_like, abstract, preprint
- **angle：** 中文/中英预印本摘要、学科分类、开放获取论文元数据

### 结构观察

- ChinaXiv 是中国科学院体系建设的科技论文预发布平台，覆盖文理工多个学科。
- 它适合观察预印本摘要如何交代研究对象、方法、结果和结论边界。
- 预印本强调快速交流，不等同于同行评议后的最终论文。

### 可迁移规则

- abstract / paper_like 文档应检查是否交代对象、方法、结果和结论边界。
- 如果是预印本或阶段性成果，应提示标明版本状态或研究边界。
- 论文式报告应区分“已验证结果”和“待验证假设”。

### 不可迁移边界

- 不把预印本当作最终事实依据。
- 不用预印本样本文风替代正式申请书或政府报告文风。
- 不保存全文，只记录元数据和结构观察。

### 进入规则池

- assisted：`DQ-A001`, `DQ-A005`
- human-gate：`DQ-H001`

## Sample 14：国家哲学社会科学文献中心

- **source id：** CN-SRC-014
- **source type：** chinese-social-science-literature-platform
- **url examples：**
  - `https://www.ncpssd.org/`
  - `https://www.ncpssd.cn/`
- **doc family：** paper_like, abstract, social_science_article
- **angle：** 中文社科论文题名、摘要、关键词、期刊来源、基金资助

### 结构观察

- 该平台面向哲学社会科学中文期刊、集刊和相关学术资源。
- 检索字段包含题名、作者、关键词、摘要、出版物名称、机构、基金资助等。
- 它适合补足自然科学/工程论文之外的社科论文摘要结构。

### 可迁移规则

- 社科论文式文档应检查问题意识、研究对象、论证路径、核心观点和资料来源。
- 如果正文出现基金资助、机构、期刊、作者等学术元数据，应保证引用和来源区完整。
- assisted review 应识别“只有观点、没有论证路径”的问题。

### 不可迁移边界

- 不默认下载全文。
- 不把社科论文的论述风格套到说明书或项目申报书。
- 不判断观点正确性，只判断文内论证是否完整。

### 进入规则池

- deterministic：`missing_reference_section`
- assisted：`DQ-A001`, `DQ-A005`
- human-gate：`DQ-H001`

## Sample 15：中国社会科学杂志社投稿须知

- **source id：** CN-SRC-015
- **source type：** chinese-journal-submission-guidance
- **url：** `https://sscp.cssn.cn/tzgg/202502/t20250227_5849425.shtml`
- **doc family：** paper_like, abstract, journal_submission
- **angle：** 中文论文摘要、关键词、注释、格式和投稿材料要求

### 结构观察

- 投稿须知明确涉及摘要、关键词、标题、正文格式、注释和引文规范等要求。
- 它比单篇论文更适合作为“论文类输出格式要求”的来源。
- 对 output-layer 的价值是：论文式 docx 不仅要有正文，还要有摘要、关键词和参考/注释体系。

### 可迁移规则

- paper_like 文档应检查摘要和关键词是否存在。
- 论文式文档若有引用、注释或资料来源，应集中说明。
- 论文类输出的格式和引文要求属于 human-gate，需要按目标期刊/单位确认。

### 不可迁移边界

- 不把某一刊物的字数、版式和注释格式套到所有论文。
- 不自动判断是否符合投稿要求。

### 进入规则池

- deterministic：`missing_required_section`, `missing_reference_section`
- assisted：`DQ-A005`
- human-gate：`DQ-H001`, `DQ-H003`

## 第一批规则提炼结果

### Assisted Review 的中文来源支撑

| assisted rule | 中文来源支撑 | 证据要求 |
|---|---|---|
| `DQ-A001` 结论是否有依据支撑 | 政府工作报告、标准编制说明、专利撰写资料 | 标出结论句和缺少的依据类型 |
| `DQ-A002` 章节是否围绕同一主目标 | 政府工作报告、国务院通知/意见 | 标出游离章节和偏离原因 |
| `DQ-A003` 申请类是否只写意义不写可行性 | NSFC 申请书改版说明、国家重点研发计划填报通知 | 标出已有意义表述和缺失的内容/基础/方法/指标 |
| `DQ-A004` 说明书是否缺异常处理 | GB/T 19678 使用说明编制、CNIPA 说明书撰写资料 | 标出步骤段和缺失的异常/边界 |
| `DQ-A005` 摘要/论文式文档是否缺对象/方法/结果/意义 | 教育部论文/成果材料、CNIPA 摘要/说明书要求、中国科技论文在线、ChinaXiv、国家哲学社会科学文献中心、中国社会科学杂志社投稿须知 | 标出已有要素和缺失要素 |

### Human Gate 的中文来源支撑

| human gate | 中文来源支撑 | 人工确认原因 |
|---|---|---|
| `DQ-H001` 事实真实性 | 政务服务、教育论文抽检、标准编制说明、项目申报材料 | 脚本不能判断事实真假 |
| `DQ-H002` 机构口径和敏感措辞 | 国务院通知/意见、政策文件、基金申请指南 | 是否合适取决于发布对象和机构口径 |
| `DQ-H003` 申请材料合规性 | NSFC 指南、国家重点研发计划通知、教育部成果申报、政务服务指南 | 版本、项目类型、事项要求会改变材料清单 |

## 下一步

1. assisted review 只能基于本文件中的中文来源支撑。
2. 每新增一个 assisted rule，必须在本文件补至少一个中文 source sample。
3. 后续如果做真实采样脚本，只保存 metadata 和观察，不保存全文。
