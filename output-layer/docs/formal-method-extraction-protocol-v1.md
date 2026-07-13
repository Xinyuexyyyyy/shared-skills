# Formal Method Extraction Protocol v1

## 定位

本协议回答一个问题：如何从中文正式文档源库中提取方法论、lessons 和可执行规则，让 `output-layer` 的正式写作不是靠感觉，而是靠可复核的标准持续进化。

它不负责采集全文，不负责模仿来源文风，不负责生成模板。它只把“源库观察”转成：

- 写作方法论。
- 可复用 lessons。
- deterministic / assisted / human-gate 规则。
- 修订建议。

## 输入

每次提取必须来自 `formal-source-sampling-v1.md` 中的中文来源样本，或先补新的中文 source sample。

输入最少包含：

```yaml
source_id: CN-SRC-004
doc_family: proposal
angle: 基金申请书完整性、简洁性、反套路表达
structure_observations:
  - 申请书从套路化提纲收敛到少数核心部分
  - 核心是为什么做、做什么、已有基础
transferable_rules:
  - proposal 文档必须检查立项依据、研究内容、研究基础或等价信息
not_transferable:
  - 不自动判断创新性和资助可能性
```

## 提取流程

### Step 1：识别文档角色

先判断这个来源在正式写作里提供什么角色。

| 角色 | 说明 | 例子 |
|---|---|---|
| 格式源 | 支撑 docx 可交付性和版式结构 | GB/T 9704 |
| 结构源 | 支撑章节组织和材料完整性 | NSFC、重点研发计划、投稿须知 |
| 逻辑源 | 支撑依据、论证、问题-方案-效果 | 标准编制说明、专利撰写资料 |
| 语体源 | 支撑正式、克制、对象明确 | 政府通知、政府报告 |
| 边界源 | 支撑 human-gate 和不能自动判断的内容 | 政务服务、项目指南、论文抽检 |

一个来源可以有多个角色，但必须标出主角色。

### Step 2：拆成五个观察面

每个来源最多提取这五类观察，不许直接复制原文模板。

1. **结构观察**：章节如何组织，先讲什么，后讲什么。
2. **逻辑观察**：判断如何被依据支撑，行动如何落地。
3. **内容观察**：哪些要素必不可少，哪些是冗余。
4. **用词观察**：哪些词体现正式，哪些词显得空泛或越权。
5. **边界观察**：哪些必须人工确认，不能自动判定。

### Step 3：转成 lesson

lesson 必须写成条件句，不写绝对句。

格式：

```yaml
lesson_id: FML-001
source_ids:
  - CN-SRC-004
scope:
  doc_family: proposal
  dimension: completeness
condition: 当文档是申请类材料
principle: 先说明为什么做、做什么、已有基础，再展开意义和预期成果
anti_pattern: 只写宏大意义和背景，不写研究内容、可行性或基础
check_question: 读者能否在前几节看到立项依据、研究内容和研究基础
fix_action: 删除套路化铺垫，把研究对象、路径和基础前移
automation: assisted
human_gate: 是否符合当年指南和项目类型要求
```

### Step 4：转成规则

根据自动化程度分三类。

#### Deterministic

适合脚本稳定检测。

例子：

- 是否有参考资料区。
- 是否有多个一级标题。
- 是否缺摘要、关键词、研究内容等明显章节。
- 是否有未闭合代码块或裸 HTML。

输出：

```yaml
rule_type: deterministic
code: missing_reference_section
severity: warning
evidence: 正文含多个来源线索但无参考资料区
fix: 增加“参考资料”或“资料来源”章节
```

#### Assisted

需要模型辅助，但必须输出证据。

例子：

- 结论有没有依据支撑。
- 章节是否服务同一主目标。
- 申请书是否只写意义、不写可行性。
- 摘要是否缺对象、方法、结果、意义。

输出：

```yaml
rule_type: assisted
code: unsupported_conclusion
severity: warning
review_question: 重要结论前后是否能找到事实、数据、规则、来源或推理支撑
required_evidence:
  - conclusion_sentence
  - missing_support_type
fix: 补依据、删结论或降级为待验证判断
```

#### Human Gate

必须人工确认。

例子：

- 事实真实性。
- 机构口径。
- 当年申报合规性。
- 专利权利边界。
- 学术不端或伦理问题。

输出：

```yaml
rule_type: human_gate
code: proposal_compliance_gate
trigger: 出现项目申报、预算、合作单位、附件、签章等内容
question: 是否符合当年指南、项目类型和提交系统要求
automation_boundary: 只能提示，不能给合规结论
```

### Step 5：转成修订动作

每条 lesson 或规则必须对应可执行的修订动作。修订动作不能是“优化一下”“更正式一点”。

合格动作：

- 把结论前移到章节开头。
- 删除泛泛背景，把对象和问题放到第一段。
- 将连续列表前补一段分组逻辑，列表后补归纳结论。
- 把“重要意义”改成“问题、对象、影响范围、依据”。
- 给图表补“图/表 + 编号 + 说明”。
- 给引用集中补“参考资料”章节。

不合格动作：

- 润色。
- 更高级。
- 更像正式文件。
- 加强逻辑。

## 方法论提取输出

每次从源库提取后，至少输出四类内容：

```yaml
method:
  name: 申请类三问结构
  source_ids: [CN-SRC-004, CN-SRC-006]
  applies_to: [proposal, project_report]
  structure: 为什么做 -> 做什么 -> 凭什么能做
  content_requirements:
    - 立项依据
    - 研究内容
    - 研究基础或可行性
  anti_patterns:
    - 只写意义，不写研究路径
    - 只写目标，不写已有基础
  checks:
    - 是否能在前半部分找到研究对象、问题和路径
  fixes:
    - 将研究对象和路径前移
    - 删除空泛意义铺垫
```

## Ratchet 机制

`output-layer` 的写作规则必须像棘轮一样只在有证据时升级。

### 可以升级规则的证据

- 至少两个中文来源支持同一个结构原则。
- 一个来源是官方规范或主管部门指南。
- 规则有正例和反例。
- 规则能产生明确修订动作。

### 不允许升级规则的情况

- 只是某篇文章写得好。
- 只是模型觉得更正式。
- 来源是外文写作指南。
- 规则无法验收。
- 规则会诱导伪官方口吻或虚构事实。

### 规则升级记录

```yaml
ratchet_id: ORL-20260622-001
change: 新增“申请类三问结构”
evidence_sources:
  - CN-SRC-004
  - CN-SRC-006
affected_rules:
  - DQ-A003
confidence: medium
rollback_condition: 在真实申请材料中反复误判结构完整性
```

## 输出到 output-layer 的位置

- 方法论：`docs/formal-writing-methodology-v1.md`
- 规则池：`docs/docx-quality-rules-backlog.md`
- 采样证据：`docs/formal-source-sampling-v1.md`
- 脚本规则：`src/docx_quality_checker.py`
- assisted review 后续脚本：`scripts/assist_docx_quality_review.py`

## 禁止事项

- 不从外文来源提炼中文正式文档内容标准。
- 不保存受版权保护的全文。
- 不把单一来源写成普遍规则。
- 不把“像政府文件”当作正式写作目标。
- 不自动生成事实、政策依据、项目基础或论文结论。

