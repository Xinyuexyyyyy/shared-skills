# Output Quality Replay 2026-06-23

## 目标

用历史 `output-layer` 生成结果回放新建的 docx 质量门，检查两件事：

1. 质量门是否能抓到真实影响正式交付的问题。
2. 质量门是否会误伤 `output-layer` 自己生成的正常结构。

## 回放样本

| case | source |
|---|---|
| `formal-report` | `/Users/sure/shared-skills/output-layer/output/output-layer/formal-report/output.clean.md` |
| `openclaw-system-overview` | `/Users/sure/Daily Work/output/output-layer/openclaw-system-overview/output.clean.md` |
| `source-sample` | `/Users/sure/Daily Work/output/output-layer/source/output.clean.md` |

## 最终结果

| case | deterministic | assisted | 主要发现 |
|---|---|---|---|
| `formal-report` | `draft_only` | `pass` | 表格缺少表题；正式报告必要要素缺“目的/方案/依据/结论”等明确章节或等价信息 |
| `openclaw-system-overview` | `draft_only` | `needs_human_review` | 多张表缺表题；正式报告缺背景/目的/方案/依据/结论等明确结构；版本号、端口/IP、PID、运行数据需要人工确认 |
| `source-sample` | `draft_only` | `pass` | 示例稿缺正式报告必要要素；不再误触发 human-gate |

## 发现的误判与修正

### 1. 中文编号 H1 被误判为多个总标题

旧输出常见结构：

```markdown
# OpenClaw 全景扫描报告
# 一、系统概况
# 二、Agents
```

原规则把所有 `#` 都当作总标题，导致 `multiple_h1` 阻断。已修正为：

- 第一条 H1 视为文档总标题。
- 后续 `# 一、...` / `# 1....` 视为一级章节。
- 其他多个非编号 H1 仍触发 `multiple_h1`。

### 2. 表格/引用块被拼成超长句

原长句检测会把引用块、表格和正文拼接，导致结构块被误报为 `long_sentence`。已修正为长句检测跳过：

- 标题。
- 引用块。
- 表格行。
- 列表项。
- 代码块。

### 3. “标准化 Markdown”误触发人工确认

原 human-gate 只要出现“标准”就触发，导致普通“标准化”表达被误报。已收紧为更具体的事实/合规线索：

- 政策/规定/办法/通知/意见/指南。
- GB/T、GB、ISO、IEC、IEEE、RFC 等标准编号。
- 版本号、端口/IP、PID、运行时间、预算、附件等。

## 结论

质量门已经对旧输出产生实际提升：

- 能把“能生成 docx”区分为“可作为草稿”和“适合正式交付”。
- 能发现过去正式报告缺少目的、依据、结论等结构职责的问题。
- 能提示 OpenClaw 报告里的运行数据需要人工确认。
- 已修掉三类会降低可用性的误判。

当前仍不自动改写正文。下一步如果要继续提升，应做“报告驱动修订”：

1. 先用质量门生成报告。
2. 根据报告只改结构、图表说明和缺项提示。
3. 不补事实、不补来源、不替用户下结论。
