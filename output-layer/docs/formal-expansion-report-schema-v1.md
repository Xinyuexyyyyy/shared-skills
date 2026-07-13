# Formal Expansion Report Schema v1

## 目标

`formal_expansion_report` 用于说明正式扩写层对原稿做了什么、没有做什么，以及哪些内容因为缺少事实依据而必须留给人工补充。

它不是质量门，也不是事实审核。扩写完成后仍需继续运行：

- `docx_quality_report`
- `assisted_quality_report`

## 状态

| status | 含义 | 下一步 |
|---|---|---|
| `expanded` | 已生成正式扩写稿 | `quality_check` |
| `needs_user_input` | 输入过少，只能生成骨架或待补充标记 | `fill_missing_facts` |
| `skipped` | 扩写关闭 | `render_or_review` |

## 输出文件

```text
output.expanded.md
formal_expansion_report.json
formal_expansion_report.md
```

## JSON 结构

```json
{
  "status": "expanded",
  "doc_type": "formal_report",
  "mode": "structured",
  "summary": "已生成正式扩写稿，缺失事实以待补充或边界说明保留。",
  "actions": [
    {
      "code": "build_formal_skeleton",
      "description": "补齐正式报告骨架。",
      "evidence": "原文缺少正式报告所需的目的、问题、原则和下一步结构。"
    }
  ],
  "blocked_expansions": [
    {
      "reason": "缺少事实依据",
      "placeholder": "待补充：本方案已有验证结果、真实案例或外部依据。"
    }
  ],
  "revision_plan": [
    {
      "action": "补充事实依据",
      "target": "本方案已有验证结果、真实案例或外部依据。",
      "reason": "扩写层不能编造事实、数据、案例或来源。",
      "instruction": "补充可复核的真实样例、抽样结果、验证记录、来源或责任人口径。"
    }
  ],
  "next_action": "quality_check",
  "source_path": "/absolute/path/source.md"
}
```

## 动作码

| code | 含义 |
|---|---|
| `build_formal_skeleton` | 补正式文档骨架 |
| `formalize_colloquial_expression` | 口语转正式表达 |
| `merge_repeated_claims` | 合并重复观点 |
| `add_boundary_placeholders` | 标注待补充和边界 |

## 修订计划

`revision_plan` 用于把扩写报告转成下一轮人工修订动作。它不自动改正文，只说明下一步该补什么、删什么、降级什么。

| action | 触发 | 修订方向 |
|---|---|---|
| `补充事实依据` | 出现 `blocked_expansions.reason=缺少事实依据` | 补真实样例、抽样结果、验证记录、来源或责任人口径 |
| `合并重复表达` | 出现 `merge_repeated_claims` | 保留一次核心判断，删除重复口号 |
| `补齐行动项` | 出现 `complete_action_item_shape` 或行动项待补充 | 补对象、条件、完成标准和验收方式 |
| `降级结论` | 出现 `downgrade_unsupported_claim` | 将确定性结论改为待验证或条件性表述 |
| `人工确认` | 出现 `mark_human_confirmation` 或人工确认待补充 | 由负责人或机构确认，不由扩写层代替判断 |

## CLI

```bash
python3 scripts/expand_formal_markdown.py path/to/source.md --outdir path/to/output
```

可选模式：

```bash
python3 scripts/expand_formal_markdown.py path/to/source.md \
  --mode conservative \
  --outdir path/to/output
```

| mode | 行为 |
|---|---|
| `structured` | 默认，主动补正式结构骨架 |
| `conservative` | 保守改写，适合已有草稿 |
| `off` | 不扩写，只写 skipped 报告 |

## Render 集成模式

`render_markdown_output.py` 默认不启用正式扩写，保证旧流程不受影响。

```bash
python3 scripts/render_markdown_output.py source.md \
  --profile formal-zh \
  --to markdown,docx \
  --formal-expansion structured \
  --docx-quality-check auto \
  --assisted-quality-review auto
```

集成后处理顺序：

```text
style correction
  -> zhlint
  -> formal expansion
  -> deterministic docx quality check
  -> assisted review
  -> markdown/docx/pdf render
```

run 目录新增：

- `formal-expansion-input.md`
- `output.expanded.md`
- `formal_expansion_report.json`
- `formal_expansion_report.md`

`manifest.json` 中新增：

```json
{
  "formal_expansion": {
    "mode": "structured",
    "status": "expanded",
    "path": "formal_expansion_report.json",
    "markdown_path": "formal_expansion_report.md",
    "expanded_path": "output.expanded.md",
    "summary": "已生成正式扩写稿，缺失事实以待补充或边界说明保留。",
    "next_action": "quality_check"
  }
}
```

## 当前边界

- 第一版是规则化扩写，不调用 LLM。
- 当前重点覆盖 `formal_report` 类短稿、口语稿和重复稿。
- 不新增事实、数据、政策、引用、项目基础或研究结果。
- 已可选接入主渲染链，默认关闭。
