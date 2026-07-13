---
name: output-layer
description: 公共输出路由层。用于处理已有内容的输出需求：表达改造（润色、去 AI 味、改得像用户、收紧表达）、clean/Obsidian/docx/pdf 成品化、PPT bridge 上游包，或通过 drawio-diagram-agent 输出紧凑 draw.io 流程图、路线图、架构图。触发词：润一下、去 AI 味、改得像我、像人话、保留意思、收紧表达、收紧这段、顺一点、改语气、改文案、输出成品、Obsidian、docx、pdf、PPT、draw.io。
status: draft
---

# Output Layer

## Purpose

`output-layer` is the final delivery router. It takes content that is already understood and mostly confirmed, then routes it to expression rewrite, style checking, packaging, export, PPT bridge, or diagram output.

It is not the place for research, source intake, or new content discovery.

`write-polish` is not a separate skill for now. Treat it as an `output-layer` mode for existing text:

```text
existing text
  -> output-style-checker when the user asks for diagnosis
  -> rewrite-polish mode when the user asks to improve expression
  -> output-polisher when the user asks for Obsidian/export formatting
```

## Use This Skill When

- The user asks to make a finished output from existing Markdown or structured notes.
- The user asks to polish existing text, remove AI tone, make it sound more like the user, tighten expression, or adjust voice without changing the core meaning.
- The user asks for Obsidian-ready output, clean Markdown, docx, pdf, or a run manifest.
- The user asks for a PPT upstream package from an already scoped topic.
- The user asks to visualize confirmed structure as a draw.io flowchart, route map, architecture diagram, or concept map.
- Another skill has finished its core work and needs a final packaging step.

## Do Not Use This Skill When

- The source material still needs research, extraction, or evidence gathering.
- The user wants raw PDF/DOCX/XLSX ingestion.
- The user wants new material, research, argument development, or a full article from scratch.
- The user wants image generation or UI design instead of document/diagram output.
- The output target is unclear and choosing it would change the work.

## Default Deliverables

> **出口断言(输出层验证,交付前必过)**:成品交给用户前确认——文件**真生成**(路径存在)、**能打开**(格式有效)、**素材可溯源**(锚点/来源不凭空)。硬断言:声明"已导出/已生成"必须 `ls` 确认文件在、非空;软建议:表达是否更顺,提醒可继续。详见全局 `~/.claude/CLAUDE.md`「验证层」。

Default document package:

- `output.clean.md`
- `output.obsidian.md`
- `output.docx`
- `manifest.json`

Optional deliverables:

- `output.pdf` when PDF tooling is ready.
- `output.corrected.md` and `style_correction_report.json` when style correction is enabled.
- PPT bridge package: `consensus.md / research.md / storyboard.md / handoff.md / bridge_manifest.json`.
- Draw.io diagram: `*.drawio`, defaulting to `task-draft/drawio-samples/`.

## Mandatory Version Archiving

Output Layer must keep output directories readable.

Whenever this skill or an output-generation subroute creates a new versioned file (`v1`, `v2`, `v15`, date-versioned names, etc.) in an existing output directory, archive older files with the same stable basename immediately after generation.

Rules:

- Output filenames must contain only one main version token. Do not create names like `script-v4-ppt-v11.pdf` or `report-v10-v11fixed.docx`.
- If an output needs to mention which PPT/report/source version it corresponds to, put that relationship in `manifest.json`, `index.md`, or the file body, not in the filename.
- Main directories keep only the latest same-basename version plus active source files/scripts.
- Same-basename comparison crosses formats: if `script-v5.md` is newest, older `script-v4.html` / `script-v4.pdf` are old versions too.
- Older same-basename versions move into the same directory's `_archive/` subdirectory.
- Archiving is a move, never deletion.
- Existing `_archive/` contents are not reorganized, overwritten, or deleted.
- For Daily Work, use `/Users/sure/Daily Work/scripts/archive_old_versions.py <directory>` after writing generated files, unless a Claude hook has already done it.
- If a user asks for dry-run first, run with `--dry-run` and wait before moving.
- Do not ask the user to run the archive command manually as part of normal output-layer delivery.

## Output Routes

| Need | Route | Output |
|---|---|---|
| Expression rewrite / 改得像用户 / 收紧 | `rewrite-polish` mode | revised text in chat by default |
| 去 AI 味 / humanize / 太像 AI 了 | `humanizer` skill (独立引擎) | 30 条 AI 模式审计 + 定向改写 |
| Style diagnosis only | `output-style-checker` | issues + pass/fail + suggested next step |
| Formal Markdown/docx/pdf package | `scripts/render_markdown_output.py` | clean / obsidian / docx / pdf / manifest |
| Formal expansion for short/informal drafts | `scripts/expand_formal_markdown.py` | `output.expanded.md` + expansion report |
| Quick smoke run | `scripts/render_quick.py` | sample formal output |
| PPT upstream handoff | `scripts/render_ppt_output.py` | PPT bridge package |
| Compact diagram | `drawio-diagram-agent` | `.drawio` flowchart / route map / architecture map |
| Output inventory | `scripts/output-inventory.py` | output index |

For route implementation details, read `docs/core-reference.md`.

## Route Rules

### Rewrite-Polish Mode

Use when the user gives existing text and asks to improve expression.

This mode belongs to `output-layer`; do not create a separate `write-polish` skill unless usage later proves it needs an independent workflow.

Trigger examples:

- "这段太 AI 了，改得像我一点"
- "润一下这段"
- "收紧表达"
- "改得更像人话"
- "保留意思，换个说法"
- "这段公众号开头不够有劲"
- "别像报告，像我自己说的"

Rules:

- Default output is revised text directly in the chat.
- Do not create files unless the user asks.
- Preserve the user's core meaning, facts, stance, and information order unless the user asks for structural rewrite.
- Remove AI tone, template phrasing, filler, vague transitions, and report-like padding.
- Tighten sentences and paragraphs.
- Adjust voice toward the user's style: direct, concrete, with clear judgment.
- Do not invent facts, examples, citations, or personal experiences.
- If the source text is too weak or unclear, say the problem first and ask for the missing intent before rewriting heavily.

Workflow:

1. **Classify the edit depth.**

   | User request | Mode | Handling |
   |---|---|---|
   | "润一下 / 顺一点" | light polish | Keep paragraph structure; improve wording and rhythm. |
   | "去 AI 味 / humanize / 太像 AI 了" | **→ humanizer skill** | 路由到独立 humanizer 引擎，30 条 AI 模式审计+定向改写。 |
   | "像我一点 / 改得像我" | voice polish | Match user's voice; make judgments sharper and more concrete. |
   | "收紧 / 太散" | tighten | Cut filler, merge repeated points, strengthen transitions. |
   | "重写这段开头 / 文案" | rewrite | Rewrite the section, but keep stated facts and intent. |
   | "帮我看看哪里不好" | diagnosis | Diagnose only; route to `output-style-checker` if formal checking is needed. |

2. **Check whether the text can be safely rewritten.**

   Rewrite directly when:

   - The source text is present.
   - The user gives a clear goal.
   - The task is expression-level, not fact-finding.

   Ask or diagnose first when:

   - The user asks "改得像我" but there is no style sample and the target tone is ambiguous.
   - The text contains claims that look unsupported or risky.
   - Rewriting would require adding missing facts, examples, data, quotes, or personal stories.
   - The text is so rough that changing wording would hide a structural problem.

3. **Rewrite with a stable edit contract.**

   - Keep the original claim unless the user asks to change it.
   - Keep concrete details; remove generic cushioning.
   - Prefer specific verbs and plain nouns.
   - Replace meta commentary like "这一段主要围绕" with direct statements.
   - Remove over-formal connective tissue: "综上所述", "值得注意的是", "从某种意义上说" unless it truly helps.
   - Avoid adding slogans, exaggerated certainty, inspirational tone, or fake emotional texture.
   - Preserve Markdown headings, lists, links, code blocks, and quoted text unless the user asks to restructure.

4. **Return the result in chat.**

   Default response shape:

   ```markdown
   改写版：

   [revised text]
   ```

   If useful, add at most 3 short notes:

   ```markdown
   我主要改了：
   - [change 1]
   - [change 2]
   ```

   Do not include a long critique unless the user asks.

5. **Offer variants only when useful.**

   Use 2 variants only when the user asks for tone exploration, headline/opening options, or platform-specific alternatives.

   Variant labels:

   - `更直接`
   - `更克制`
   - `更有表达力`
   - `更像说明文`

   Do not produce 5+ variants by default.

Output rules:

- Default: revised text in chat.
- No files by default.
- No run directory by default.
- No docx/pdf/Obsidian export until wording is approved or user asks for export.
- If the user gives a long document and asks for full rewrite, first propose a small sample rewrite of 1-2 sections before changing the whole piece.

Quality checklist:

- [ ] Meaning, facts, and stance are preserved.
- [ ] AI/template phrasing is removed.
- [ ] Wording is tighter and more concrete.
- [ ] No new facts, citations, stories, or claims were invented.
- [ ] User-visible output is the rewritten text, not a process report.
- [ ] Files were not created unless requested.

Boundary:

| Need | Owner |
|---|---|
| Find bad writing patterns | `output-style-checker` |
| Rewrite expression in existing text | `output-layer` rewrite-polish mode |
| Format/export after wording is approved | `output-polisher` or document route |

### Document Route

Use for confirmed Markdown that should become formal files.

Rules:

- Default profile is `formal-zh`.
- Default package is clean + Obsidian + docx + manifest.
- PDF is optional and may be skipped if tooling is missing.
- Style correction is optional; show the preset before applying it.
- For formal `docx`, quality layers are optional and default off:
  - `--docx-quality-check off|auto|strict` writes deterministic readiness reports.
  - `--assisted-quality-review off|auto|strict` writes methodology-grounded review reports.
  - Use `auto` for drafts; use `strict` before formal handoff when the user wants quality gates.
- Quality layers first infer document type. `content_article`, `meeting_note`, and `runtime_record` avoid the full `formal_report` rule set; explicit `doc_type` in frontmatter still wins.
- If the source is too short, oral, or repetitive, use `--formal-expansion conservative|structured` or run `scripts/expand_formal_markdown.py` first. It writes `output.expanded.md` plus `formal_expansion_report.json/md`; it does not invent facts or replace the quality gates.
- If the user wants the quality report to drive the next draft, use `--formal-revision auto`. It writes `output.revised.md` plus `formal_revision_report.json/md`; it only adds structural placeholders and reference placeholders, never facts or citations.
- For formal handoff, check `index.md` first. Its `Delivery Recommendation` summarizes whether the output is `deliverable`, `deliverable_with_review`, `needs_content_revision`, `needs_input`, or `blocked`, and lists priority actions before the detailed reports.
- Keep facts and conclusions unchanged during style correction.
- After exporting versioned document files into an existing directory, archive older same-basename versions before final response.

### PPT Route

Use when the user wants slides or a PPT handoff.

Rules:

- Default to `stage=upstream` unless the downstream PPT project is already prepared.
- Use presets only to fill defaults; explicit user values win.
- Read `docs/ppt-output-protocol.md` or `docs/ppt-output-quickstart.md` before changing PPT behavior.
- After exporting versioned PPT or handoff files into an existing directory, archive older same-basename versions before final response.

### Draw.io Route

Use when the user wants visualization.

Rules:

- Route to `drawio-diagram-agent`.
- Make diagrams compact, not decorative.
- Default layout: main route left to right, 3-5 main nodes, no crossed lines, no large feedback loop arrows.
- Put feedback or decisions in a bottom/right zone.
- Use text anchors instead of long return arrows.
- Outputs go below or right with short dashed arrows.
- A `.drawio` file is the durable output; `localhost:6002/?mcp=...` is temporary preview only.

## Checkpoints

Before generating:

1. **Choose outputs** — list the intended outputs if not obvious. Ask only if the choice changes scope.
2. **Expression rewrite** — if the user asks for tone/wording changes, keep it in chat by default and do not trigger file export.
3. **Style correction** — show preset name and one-line purpose before applying it.
4. **Existing run directory** — if a target run exists, ask whether to overwrite, rename, or skip.
5. **Diagram output** — for draw.io, prioritize clear routing over complete node coverage.

## Failure Handling

| Failure | Handling |
|---|---|
| Input file missing or empty | Stop; report the missing/empty path; do not generate output. |
| PDF engine unavailable | Generate other formats; report PDF skipped and why. |
| Style preset missing | Fall back to `plain-explainer-zh-v1`; report available preset direction. |
| Output path not writable | Stop; report path and likely permission/disk issue. |
| Python package missing | Report missing package and install command; do not fake output. |
| Draw.io MCP unavailable | Use direct `.drawio` XML only for simple diagrams; report no live preview. |
| PPT bridge blocked | Write manifest/status if possible; state the blocking reason. |

## File Rules

- Generated document runs go under `output/output-layer/<run_id>/`.
- Draw.io samples default to `task-draft/drawio-samples/`.
- Do not overwrite existing outputs without confirmation.
- Do not leave old same-basename version files in the main output directory; move them to `_archive/`.
- Always report generated paths in the final response.
- Do not move or delete old runs unless the user asks for cleanup.

### Auto-tidy after generating (mandatory)

`<run_id>` 用 `时间戳-主题` 形式（如 `20260520-192132-openclaw-system-overview`）。
同一主题反复生成会在 `output/output-layer/` 下堆几十个时间戳文件夹，用户找最新得用眼睛扫——这是必须防的乱。

所以**每次 document/PPT 路由生成完产物后，自动跑一次目录整理**（不删任何文件，只把旧份移进 `_archive/`，可逆）：

```bash
python3 skills/output-layer/scripts/organize.py --apply
```

整理后目录恒为：每个主题一个干净文件夹（打开就是最新成品）+ `README.md`（各主题最新时间）+ `_archive/<主题>/<时间戳>/`（历史份）。

规则：
- 这是生产流程的收尾步骤，不是事后补救——谁生成谁负责整理。
- `rewrite-polish` 模式（默认只在 chat 回改写，不落文件）**不触发**整理。
- 整理只搬动不删除；用户要彻底清掉 `_archive/` 时才删，且需明确确认。

## References

Read only when needed:

- `docs/core-reference.md` — scripts, dependencies, formal-zh rules, tests.
- `docs/style-correction-v1.md` — style correction rules.
- `docs/style-adapt-spec.md` — broader style adaptation design.
- `docs/ppt-output-protocol.md` — PPT bridge protocol.
- `docs/ppt-output-quickstart.md` — common PPT commands.
- `docs/consistency-check.md` — current script/document consistency status.

## Minimum Validation

For document route changes:

```bash
python3.11 -m unittest discover -s skills/output-layer/tests -p 'test_*.py'
```

For PPT route changes:

```bash
python3.11 -m unittest skills/output-layer/tests/test_render_ppt_output_smoke.py
```

For draw.io route changes:

- Confirm `drawio-diagram-agent` exists.
- Confirm output `.drawio` file exists and is not empty.
- If browser preview was used, state whether it was MCP preview or diagrams.net viewer fallback.

## Final Response

Always tell the user:

- What outputs were generated.
- Where the files are.
- What was skipped and why.
- How to verify the result.
- 目录已自动整理：指向整理后的干净主题夹路径（如 `output/output-layer/<主题>/`），而不是带时间戳的原始 run 目录。

---

## 产出去向

产出物落盘与命名遵循全局规范 `~/shared-skills/STORAGE-SPEC.md`：产出可存任何位置，但每件正式产出须在所属任务 `tasks/<任务>/artifacts.md` 登记坐标；用语义名不用纯时间戳；同主题反复生成覆盖或归档旧版。
