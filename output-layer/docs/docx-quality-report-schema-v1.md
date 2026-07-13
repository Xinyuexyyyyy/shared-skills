# Docx Quality Report Schema v1

## 目标

`docx_quality_report` 用于回答：一份 Markdown 现在是否适合作为正式 docx 输出。

它不是评分表，不替代事实审核，也不自动补充内容。它只把阻断问题、草稿问题和优化建议分清楚，让用户知道下一步应该渲染还是先修正文。

## 状态

| status | 含义 | 下一步 |
|---|---|---|
| `pass` | 未发现阻断或警告问题，可以进入 docx 渲染 | `render_docx` |
| `draft_only` | 可以作为草稿检查，但不建议正式交付 | `revise_text` |
| `blocked` | 存在阻断问题，不适合进入正式 docx 输出 | `revise_text` |

## 问题级别

| severity | 含义 |
|---|---|
| `blocker` | 必须修复，否则不应作为正式 docx 输出 |
| `warning` | 可生成草稿，但不建议正式交付 |
| `suggestion` | 不阻断交付，但建议优化 |

## JSON 结构

```json
{
  "status": "draft_only",
  "doc_type": "proposal",
  "summary": "当前可作为草稿检查，但不建议直接作为正式 docx 交付。",
  "blockers": [],
  "warnings": [
    {
      "dimension": "completeness",
      "severity": "warning",
      "code": "missing_required_section",
      "location": "document",
      "issue": "proposal 文档缺少必要要素：研究基础。",
      "evidence": "研究基础",
      "fix": "补充“研究基础”相关章节或内容。"
    }
  ],
  "suggestions": [],
  "render_notes": [],
  "next_action": "revise_text",
  "source_path": "/absolute/path/source.md"
}
```

## 字段说明

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `status` | string | 是 | `pass / draft_only / blocked` |
| `doc_type` | string | 是 | 文档类型，默认 `formal_report` |
| `summary` | string | 是 | 面向用户的一句话结论 |
| `blockers` | array | 是 | 阻断问题列表 |
| `warnings` | array | 是 | 警告问题列表 |
| `suggestions` | array | 是 | 优化建议列表 |
| `render_notes` | array | 是 | docx 渲染相关备注，第一版可为空 |
| `next_action` | string | 是 | `render_docx / revise_text / ask_user` |
| `source_path` | string | 是 | 输入文件绝对路径 |

## Finding 结构

| 字段 | 类型 | 说明 |
|---|---|---|
| `dimension` | string | `formality / logic / structure / completeness / docx_readiness` |
| `severity` | string | `blocker / warning / suggestion` |
| `code` | string | 稳定规则码，供测试和后续集成使用 |
| `location` | string | 问题位置，第一版可用章节名或 `document` |
| `issue` | string | 问题描述 |
| `evidence` | string | 可复核的短证据 |
| `fix` | string | 修订建议 |

## Markdown 报告结构

Markdown 报告给人看，JSON 给程序接。

```markdown
# Docx Quality Report

- Status: draft_only
- Doc type: proposal
- Summary: 当前可作为草稿检查，但不建议直接作为正式 docx 交付。
- Next action: revise_text

## Blockers

- None

## Warnings

### 1. missing_required_section

- Dimension: completeness
- Severity: warning
- Location: document
- Issue: proposal 文档缺少必要要素：研究基础。
- Evidence: 研究基础
- Fix: 补充“研究基础”相关章节或内容。
```

## 第一版规则码

| code | 维度 | 默认级别 |
|---|---|---|
| `missing_h1` | structure | blocker |
| `multiple_h1` | structure | blocker |
| `heading_level_jump` | structure | blocker |
| `unclosed_code_fence` | docx_readiness | blocker |
| `raw_html` | docx_readiness | blocker |
| `emoji` | formality | warning |
| `bare_url` | docx_readiness | warning |
| `weak_opener` | formality | warning |
| `repeated_template_phrase` | formality | warning |
| `missing_required_section` | completeness | warning |
| `long_sentence` | formality | suggestion |
| `empty_section_after_heading` | structure | warning |
| `mixed_subject_terms` | formality | warning |
| `figure_or_table_missing_caption` | docx_readiness | warning |
| `missing_reference_section` | completeness | warning |

## CLI

```bash
python3 scripts/check_docx_quality.py path/to/source.md --outdir path/to/output
```

输出：

- `docx_quality_report.json`
- `docx_quality_report.md`

## Render 集成模式

`render_markdown_output.py` 默认不启用质量检查，保证旧流程不受影响。

```bash
python3 scripts/render_markdown_output.py source.md \
  --profile formal-zh \
  --to markdown,obsidian,docx \
  --docx-quality-check auto
```

| 模式 | 行为 |
|---|---|
| `off` | 默认值，不运行 docx 质量检查 |
| `auto` | 写入质量报告，但不阻断 docx 渲染 |
| `strict` | 写入质量报告；如果状态为 `blocked`，跳过 docx 渲染 |

集成模式会在 run 目录额外写入：

- `docx_quality_report.json`
- `docx_quality_report.md`

并在 `manifest.json` 中写入：

```json
{
  "docx_quality_check": {
    "mode": "auto",
    "status": "draft_only",
    "path": "docx_quality_report.json",
    "markdown_path": "docx_quality_report.md",
    "summary": "当前可作为草稿检查，但不建议直接作为正式 docx 交付。",
    "next_action": "revise_text"
  }
}
```

## 与 Assisted Review 联用

deterministic 质量检查负责标题层级、裸 HTML、参考资料区等稳定规则；assisted review 负责中文正式写作方法论里的结构链条、逻辑链条和内容完整性。

两个检查可以同时打开：

```bash
python3 scripts/render_markdown_output.py source.md \
  --profile formal-zh \
  --to markdown,docx \
  --docx-quality-check auto \
  --assisted-quality-review auto
```

默认推荐：

- 草稿阶段：两个都用 `auto`，先看报告再修。
- 交付前：`--docx-quality-check strict --assisted-quality-review strict`。
- 若文档含事实、合规、机构口径事项，assisted review 只提示 human-gate，不替代人工确认。
