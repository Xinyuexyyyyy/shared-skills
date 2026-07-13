# Formal Revision Layer v1/v2

## 目标

把质量报告里的问题转成下一版 Markdown 修订稿，让质量门不只“报错”，也能推动文稿进入下一轮。

第一版只做确定性修订：

- 为缺失必要章节追加 `待补充：...` 占位。
- 为缺少参考资料区的文稿追加 `参考资料` 占位。
- 遇到阻断项时不改正文，只写修订报告。

v2 在保持“不编造事实”的前提下，继续消费：

- `assisted_quality_report.findings[].evidence.missing_elements`
- `formal_expansion_report.revision_plan`

并将它们转为：

- 缺失方法论要素的 `## 待补充：...` 占位。
- `## 人工修订清单`，集中列出补事实、补行动项、人工确认等动作。

## 边界

修订器不得：

- 编造事实、数据、政策、文献、案例。
- 替用户判断合规、真实性、技术正确性。
- 自动补责任人、日期、预算、指标。

修订器可以：

- 补结构占位。
- 保留原文事实。
- 把质量门发现转成可执行修订清单。
- 把辅助审查缺项和扩写修订计划转成下一稿中的人工待办。

## CLI

```bash
python3 scripts/revise_formal_markdown.py source.md --outdir /tmp/revision-demo
```

输出：

- `output.revised.md`
- `formal_revision_report.json`
- `formal_revision_report.md`

## 主链集成

```bash
python3 scripts/render_markdown_output.py source.md \
  --profile formal-zh \
  --to markdown,docx \
  --formal-expansion structured \
  --docx-quality-check auto \
  --assisted-quality-review auto \
  --formal-revision auto
```

处理顺序：

```text
style correction
  -> zhlint
  -> formal expansion
  -> docx quality check
  -> assisted review
  -> formal revision
  -> markdown/docx/pdf render
```

## 回放结果

回放目录：

`/Users/sure/Daily Work/output/output-layer-formal-revision-replay-20260625/`

样本：产品调研短报告。

结果：

- 原稿缺少正式报告的目的、方案、依据等结构职责。
- 修订器追加：
  - `## 待补充：目的`
  - `## 待补充：方案`
  - `## 待补充：依据`
- 未新增事实、数据、政策、来源或结论。

## v2 回放结果

验证样本：`assisted-manual-incomplete.md`

主链参数：

```bash
--formal-expansion structured
--docx-quality-check auto
--assisted-quality-review auto
--formal-revision auto
```

结果：

- `formal_expansion_report.revision_plan` 中的“补充事实依据”进入 `## 人工修订清单`。
- `assisted_quality_report` 中缺失的“前置条件、异常处理”进入独立待补充章节。
- `output.revised.md` 不新增版本号、环境、报错样例、数据或结论。
- 回归测试：`test_formal_revision_auto_consumes_assisted_and_expansion_reports`。

## 当前状态

这是确定性修订器，不是自动写作器。它解决“报告指出问题但没人知道下一稿怎么改”的第一步：把质量门、辅助审查和扩写报告里的问题集中落进下一版 Markdown。真正补事实、补数据、补政策依据、补机构口径，仍由用户或上游材料完成。
