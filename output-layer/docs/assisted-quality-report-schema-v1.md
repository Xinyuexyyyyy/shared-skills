# Assisted Quality Report Schema v1

## 目标

`assisted_quality_report` 用于回答：一份 Markdown 在进入正式 docx 输出前，是否符合中文正式写作方法论里的结构、逻辑、内容和用词要求。

它不自动改写，不补事实，不替代人工合规审核。它只把中文源库提炼出的 `FWM-001` 到 `FWM-005` 变成可复核的审阅证据。

## 与 deterministic report 的区别

| 报告 | 作用 | 例子 |
|---|---|---|
| `docx_quality_report` | 稳定脚本检查，偏渲染前硬问题和明显缺项 | 标题层级跳跃、裸 HTML、缺参考资料区 |
| `assisted_quality_report` | 方法论辅助审阅，偏结构链条、逻辑链条和内容完整性 | 申请书缺研究基础、技术说明缺效果、行动项只有口号 |

## 状态

| status | 含义 | 下一步 |
|---|---|---|
| `pass` | 当前方法论覆盖范围内未发现明显缺项 | `render_or_deterministic_check` |
| `needs_revision` | 发现结构、逻辑或内容完整性问题 | `revise_text` |
| `needs_human_review` | 未发现方法论缺项，但存在事实、合规或机构口径事项 | `human_review` |

## JSON 结构

```json
{
  "status": "needs_revision",
  "doc_type": "proposal",
  "summary": "辅助审阅发现结构、逻辑或内容完整性问题，建议先修正文稿。",
  "methodology_version": "formal-writing-methodology-v1",
  "findings": [
    {
      "rule_type": "assisted",
      "code": "proposal_three_questions_incomplete",
      "severity": "warning",
      "dimension": "completeness",
      "lesson_id": "FWM-001",
      "lesson_name": "申请类三问结构",
      "source_ids": ["CN-SRC-004", "CN-SRC-006"],
      "review_question": "申请类材料是否说明为什么做、做什么、凭什么能做。",
      "evidence": {
        "present_elements": ["为什么做", "做什么"],
        "missing_elements": ["研究基础/可行性"]
      },
      "fix": "删除套路化铺垫，把研究对象、路径和基础前移；补齐立项依据、研究内容、研究基础/可行性。"
    }
  ],
  "human_gates": [],
  "next_action": "revise_text",
  "source_path": "/absolute/path/source.md"
}
```

## 第一批 assisted 规则码

| code | lesson | 适用类型 | 检查问题 |
|---|---|---|---|
| `proposal_three_questions_incomplete` | `FWM-001` | `proposal` | 是否缺“为什么做 / 做什么 / 研究基础或可行性” |
| `technical_chain_incomplete` | `FWM-002` | `technical_disclosure` | 是否缺“技术问题 / 技术方案 / 技术效果 / 边界条件” |
| `abstract_four_elements_incomplete` | `FWM-003` | `abstract`, `paper_like` | 是否缺“对象、方法、结果、意义/边界” |
| `action_item_incomplete` | `FWM-004` | all | 行动项是否只写“加强、推动、完善、提升”等弱动作 |
| `manual_task_chain_incomplete` | `FWM-005` | `manual` | 是否缺“适用对象、前置条件、步骤、注意事项、异常处理” |

## 第一批 human-gate 规则码

| code | 触发 | 边界 |
|---|---|---|
| `proposal_compliance_gate` | 申请类文档出现预算、附件、签章、合作单位、伦理、申报等线索 | 只能提示人工核对当年指南和提交系统要求 |
| `fact_and_institution_gate` | 出现政策、标准、数据、预算、附件、签章等线索 | 不能判断事实真伪或机构口径 |

## CLI

```bash
python3 scripts/assist_docx_quality_review.py path/to/source.md --outdir path/to/output
```

输出：

- `assisted_quality_report.json`
- `assisted_quality_report.md`

## Render 集成模式

`render_markdown_output.py` 默认不启用 assisted review，保证旧流程不受影响。

```bash
python3 scripts/render_markdown_output.py source.md \
  --profile formal-zh \
  --to markdown,docx \
  --assisted-quality-review auto
```

| 模式 | 行为 |
|---|---|
| `off` | 默认值，不运行 assisted review |
| `auto` | 写入 assisted 报告，但不阻断 docx 渲染 |
| `strict` | 写入 assisted 报告；如果状态为 `needs_revision`，跳过 docx 渲染 |

集成模式会在 run 目录额外写入：

- `assisted_quality_report.json`
- `assisted_quality_report.md`

并在 `manifest.json` 中写入：

```json
{
  "assisted_quality_review": {
    "mode": "auto",
    "status": "needs_revision",
    "path": "assisted_quality_report.json",
    "markdown_path": "assisted_quality_report.md",
    "summary": "辅助审阅发现结构、逻辑或内容完整性问题，建议先修正文稿。",
    "next_action": "revise_text"
  }
}
```

## 当前边界

- 第一版是规则化辅助审阅，不调用 LLM。
- 检查依据只来自中文源库和 `formal-writing-methodology-v1`。
- 不自动改写正文。
- 不判断事实真实性、政策现行性、项目合规性、论文创新性或专利权利边界。
