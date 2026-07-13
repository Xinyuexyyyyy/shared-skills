---
name: drawio-diagram-agent
description: Create compact, readable draw.io diagrams from user descriptions, especially workflow maps, learning paths, project architecture, agent processes, and concept routes. Use the drawio MCP server when available, export .drawio files, and prioritize clean layout with minimal crossing lines and no large feedback loops.
status: stable
---

# Draw.io Diagram Agent

## Purpose

Turn user descriptions into clean `.drawio` diagrams that are useful in real work documents.

This skill is for visualizing structure: workflows, routes, learning paths, project modules, system architecture, agent loops, decision gates, and output pipelines.

The priority is not decoration. The priority is: clear route, compact layout, low line noise, and easy editing in draw.io / diagrams.net.

## When to use this skill

Use this skill when the user asks to:

- 画图、画流程图、画路线图、画架构图、画关系图、画概念图
- Turn a text explanation into a draw.io diagram.
- Visualize a workflow, learning process, project structure, research pipeline, or agent process.
- Export a `.drawio` file.
- Open a diagram in a temporary browser preview.
- Improve a diagram that feels messy, too line-heavy, or hard to read.

Trigger examples:

- "把这个流程画成 draw.io 图"
- "做个路线图"
- "这个架构帮我可视化一下"
- "线太乱，重新排一下"
- "用更少空间画清楚"

## When not to use this skill

Do not use this skill for:

- Generating bitmap images, illustrations, photos, or artistic assets.
- Making slide decks.
- Designing a full UI mockup.
- Doing broad research before diagramming unless the user asks.
- Installing or reconfiguring MCP servers unless explicitly requested.
- Deploying `next-ai-draw-io` or cloning its source project.

If the user needs a raster image, use an image-generation workflow instead. If the user needs a web UI, use the frontend workflow.

## Tool requirements

Preferred tool:

```bash
drawio MCP: npx @next-ai-drawio/mcp-server@latest
```

Expected MCP capabilities:

- `start_session` opens a temporary browser preview.
- `create_new_diagram` creates a diagram from draw.io XML.
- `edit_diagram` edits an existing diagram.
- `get_diagram` reads current XML.
- `export_diagram` writes a `.drawio` file.

If the drawio MCP is not available:

1. Do not pretend the MCP was used.
2. Generate a valid `.drawio` XML file directly if the task is simple.
3. Tell the user that live preview was not available.

## Default output location

Unless the user gives another path, write generated diagrams to:

```text
task-draft/drawio-samples/
```

Use clear filenames:

```text
<topic>-flow.drawio
<topic>-architecture.drawio
<topic>-route-map.drawio
```

Do not overwrite an existing diagram unless the user clearly asks for an update. Prefer `-v2`, `-clean`, or a timestamp suffix.

## Layout rules

Always optimize for readable routing.

Use this default layout prompt internally:

```text
画紧凑 draw.io 流程图：主线左到右，3-5 个主节点；不要交叉线和大回环线；反馈/判断单独放到底部或右侧；回流关系用文字说明代替长箭头；输出物放下方或右侧，用短虚线连接；整体 16:9，少空间，清晰优先。
```

Concrete rules:

- Main flow should have one obvious reading direction, usually left to right.
- Keep main nodes to 3-5 unless the user asks for detail.
- Use thick arrows only for the main route.
- Avoid crossing arrows.
- Avoid long feedback loops.
- Put feedback, decisions, and branches in a separate bottom or right-side zone.
- Express "return to previous step", "next round", or "repeat" with short text anchors instead of long arrows.
- Put outputs below or to the right of the main flow.
- Use short dashed arrows for outputs.
- Use light color bands for grouping, but do not let color carry the meaning by itself.
- Keep node text to one title line plus one optional small explanation line.
- Prefer a compact 16:9 or wide-card ratio.
- Make the diagram understandable without heavy zooming.

## Diagram types

### Workflow or route map

Use when the user describes a process.

Structure:

- Title at top left.
- Main route in one horizontal band.
- Decision or feedback area below or right.
- Outputs below or right.
- Short labels on branches.

### Architecture diagram

Use when the user describes a system.

Structure:

- Group by responsibility, not by technology first.
- Keep data flow direction stable.
- Put external actors on the left.
- Put outputs or storage on the right.
- Avoid drawing every integration line if a grouped boundary can explain it.

### Learning path or knowledge map

Use when the user describes learning content.

Structure:

- Use stages or modules as the main route.
- Put practice, feedback, and review as separate secondary zones.
- Put notes, glossary, or artifacts as outputs.
- Use "next chapter" and "return to current chapter" as text anchors unless the user needs a formal state machine.

### Decision flow

Use when the user describes choices.

Structure:

- Main question near the left or top.
- Decision nodes should be few.
- Branches should be short.
- Consequences should be adjacent to the branch, not far away.

## Workflow

### Step 1. Clarify the diagram goal only if necessary

Do not ask if the user has already given enough material.

Ask only when:

- The target diagram type is unclear and affects structure.
- The user asks for exact style, audience, or export location but does not provide it.
- The task requires opening, overwriting, or editing an existing file.

Otherwise infer the diagram type and proceed.

### Step 2. Reduce the content before drawing

Before drawing, silently compress the material into:

- Main route: 3-5 nodes.
- Secondary zones: feedback, decisions, outputs, risks, or notes.
- Branch labels: short words.
- Output artifacts: files, reports, notes, logs, or next actions.

If the source has too many nodes, choose clarity over completeness.

### Step 3. Create the diagram

Use drawio MCP if available:

1. Start a session when a browser preview is useful.
2. Create a new diagram with clean draw.io XML.
3. Export the diagram to a `.drawio` file.

If MCP cannot be used, create a `.drawio` file directly and report that live preview was skipped.

### Step 4. Check layout quality

Before final response, check:

- Is the main route visible in 2 seconds?
- Are there crossing lines?
- Are there long loop arrows?
- Are outputs separated from process nodes?
- Is the diagram compact enough?
- Are labels short?
- Can the user open it in diagrams.net without extra conversion?

If line noise is high, make a cleaner version before finalizing.

### Step 5. Report result

Final response must include:

- `.drawio` file path.
- Whether MCP preview/export succeeded.
- One short note about layout choices.
- How to open it if needed.

## Browser preview

When the user asks to "临时跳到浏览器", "打开看看", or "preview":

Preferred:

- Use the drawio MCP browser preview if the session is active.

Fallback:

- Open the `.drawio` file through diagrams.net viewer with encoded diagram data.
- If that is not practical, tell the user to open `https://app.diagrams.net/` and import the `.drawio` file.

Remember: `localhost:6002/?mcp=...` links are temporary. The `.drawio` file is the durable output.

## Editing an existing diagram

When improving an existing diagram:

1. Preserve the original unless the user asks to overwrite.
2. Create `-v2`, `-clean`, or another clear variant.
3. Reduce lines first.
4. Move feedback and branches into separate zones.
5. Replace long return arrows with short text anchors.
6. Keep the user's working structure if it is already understandable.

## Safety rules

- Do not install or reconfigure MCP servers unless the user explicitly asks.
- Do not clone or deploy `next-ai-draw-io` for ordinary diagram tasks.
- Do not overwrite `.drawio` files without confirmation.
- Do not claim a browser preview is running if only a file was created.
- Do not claim MCP was used if the file was hand-generated.
- Do not expose or request API keys for diagram tasks.

## Quality checklist

Before finalizing:

- [ ] Main route has one clear direction.
- [ ] Main nodes are limited and readable.
- [ ] No crossed arrows unless unavoidable.
- [ ] No large feedback loop arrows.
- [ ] Feedback or decision logic is separated.
- [ ] Outputs are visually secondary.
- [ ] Text is short and readable.
- [ ] File exports as `.drawio`.
- [ ] Final response includes the file path.
- [ ] Any preview limitation is stated honestly.

## Examples

### Example 1: Learning engine flow

User:

```text
把笔记驱动学习引擎 MVP 三步闭环画成路线图，少空间，线不要乱。
```

Good structure:

```text
资料输入 -> 资料消化 -> 章节骨架 -> 学习主循环

Bottom feedback zone:
用户反馈 -> 切章闸门 -> 下一章 / 回到当前章

Outputs:
学习笔记, _glossary.md
```

Use short text anchors for "next chapter continues from chapter skeleton" and "return to learning loop".

### Example 2: Agent workflow

User:

```text
画一下 research -> output -> closeout 的 agent 工作流。
```

Good structure:

```text
输入问题 -> research 收集证据 -> output 生成产物 -> closeout 收尾
```

Put "风险 / 待确认 / 记忆建议" in a bottom secondary zone instead of drawing lines back into every step.

### Example 3: Clean up messy diagram

User:

```text
这张图线太乱，重排。
```

Action:

- Keep the same core nodes.
- Remove long loops.
- Split main route and feedback zone.
- Replace return arrows with text anchors.
- Export a `-v2-clean.drawio` file.
