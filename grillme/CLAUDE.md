---
name: grillme
description: Use for layered diagnostic questioning and knowledge distillation before committing to a complex idea, product plan, PRD, architecture, workflow, implementation plan, retrospective conclusion, or high-rework-risk task. Trigger when the user asks to be grilled, questioned, pressure-tested, or when a task needs product, interaction, frontend, backend, data, evidence, or acceptance details before execution. If the user cannot answer a technical/domain question, route it to methodology research or expert-practice comparison instead of forcing an answer.
---

# Grillme

Use Socratic questioning plus domain diagnosis to turn a vague idea into an executable handoff.

Core source: `Jekudy/grillme-skill` (`https://github.com/Jekudy/grillme-skill`, MIT). DailyWork2 adapts it for Chinese conversation, Codex, product discovery, research, PRD, and task-first work.

In `deep-research`, grillme sits after visible brainstorm and before narrowed verification / PRD readiness. Its job is not merely to ask a few boundary questions. Its job is to identify what is known, what must be asked from the user, what the user cannot reasonably answer, and what must be distilled from expert practice, methodology, or external evidence.

## Core Rule

Ask one important question at a time. Do not dump a questionnaire.

Do not cap grillme at a fixed number of rounds. Continue or stop based on whether the next artifact has enough product, interaction, implementation, data, evidence, and acceptance detail to be useful.

Use a question budget. In one visible wave, ask **at most 3 questions**, and prefer 1 when the next decision is obvious. A question is allowed only if the answer can change scope, core workflow, acceptance, data, permissions, business boundary, risk, or Stop Conditions.

The goal is not to interrogate the user. The goal is to put every missing detail in the right place:

- If the user knows it, ask the user.
- If the user cannot reasonably know it, do not force an answer; route it to distillation.
- If it is a judgment call, compare options and recommend one.
- If it is still uncertain, record it as a risk or validation task.

## Question Classes

Every question has both a **strength** and a **domain**.

### Strength

**Strong questions** affect whether the next artifact can be correct. They can change:

- goal
- target user or audience
- product scope
- research object
- decision standard
- evidence/source strategy
- interaction flow
- frontend/backend/data design
- MVP boundary
- acceptance criteria
- permissions, data rights, business boundary, or Stop Conditions

**Weak questions** improve fit but do not block progress. They affect tone, format, wording, ordering, or optional polish.

Unanswered strong questions affect readiness. Weak questions can be skipped with explicit defaults.

Do not ask implementation-detail questions merely because the PRD or plan has a blank. Routine UX/API/data/modeling defaults should be distilled or proposed by the agent first, then only escalated to the user if they change product judgment.

### Domains

Use these diagnostic domains when the task is complex enough. Not every task needs every domain.

| Domain | Ask the user when they can know | Distill when they cannot know |
|---|---|---|
| Product | user, pain, scenario, job-to-be-done, priority, non-goals | product patterns, wedge choice, MVP shape, tradeoff frameworks |
| Interaction / UX | user steps, states, buttons, empty/error/loading states, acceptance feel | UX patterns, wireframe conventions, task-flow best practices |
| Frontend | pages, components, UI states, responsive needs, accessibility expectations | frontend architecture patterns, component boundaries, UI library conventions |
| Backend | business rules, permissions, workflow, integrations, async jobs | backend architecture patterns, API design, queue/task patterns, failure handling |
| Data | what is stored, fields, file paths, directory layout, lifecycle, privacy | schema patterns, storage options, retention, backup, migration practices |
| Evidence | what the user knows firsthand, existing material, constraints | methodology research, expert practice, competitor/open-source comparison |
| Acceptance | who verifies, shortest test path, measurable done criteria | QA patterns, smoke tests, instrumentation, success metrics |

## Diagnostic Loop

Run this loop instead of a fixed questionnaire:

1. **Map domains:** Decide which domains matter for the next artifact.
2. **Classify gaps:** For each domain, mark gaps as ask-user / distill / assume / defer.
3. **Ask within budget:** Choose the highest-leverage ask-user gap, or up to 3 only when all answers are needed for the next decision.
4. **Route non-user gaps:** For questions the user cannot answer, create a distillation task instead of asking.
5. **Summarize after each wave:** Show what is known, what remains, and where each unknown will go.
6. **Stop only when readiness is real:** Enough detail exists for the next artifact, or the output is downgraded.

## Knowledge Distillation Rule

When the user cannot answer a technical or specialist question, do not ask them to pretend. Create a concrete `methodology-distiller` task when that skill is available; otherwise use `deep-research` evidence backends to perform the same method/expert-practice comparison.

Examples:

- User cannot design backend APIs → distill common backend/API patterns and recommend one.
- User cannot decide frontend component structure → distill UI implementation patterns and propose a component map.
- User cannot define data schema → infer a candidate schema from product behavior and mark it for verification.
- User does not know PRD conventions → research PRD methods, compare examples, and keep only useful parts.
- User does not know how competitors solve it → route to evidence collection.

For PRD-specific gaps in DailyWork2, do not invent generic method-card names. Route the gap to `methodology-distiller` and use the PRD workspace overlay first:

```text
/Users/sure/DailyWork2/skills/methodology-distiller/methodology-vault/INDEX.md
```

Common PRD gap mapping:

| Gap | Use card |
|---|---|
| Unsure whether to write full PRD or brief | `cards/prd-type-selector.md` |
| MVP, Future, Out of Scope, or Non-goals boundary conflict | `cards/prd-boundary.md` |
| Buttons, steps, or implementation detail unclear | `cards/prd-detail.md` |
| UI states or text sketch missing | `cards/prd-ui-state.md` |
| Data fields, storage location, or directory layout unclear | `cards/prd-data-storage.md` |
| Acceptance path unclear | `cards/prd-acceptance-path.md` |
| PRD is too long or mixed with research/methodology | `cards/prd-subtraction.md` |
| Unsure which layer should handle a failed PRD gate | `cards/prd-loopback-routing.md` |
| PRD Gate found gaps and they need repeat questioning instead of rewriting | `cards/prd-grok-loop.md` |

When doing a route smoke or PRD gap-routing answer, cite the exact local card path or card id. A semantic label such as "state matrix method" is not enough.

Distillation tasks should be compact:

```text
Distillation needed:
- Domain:
- Question:
- Why user should not be forced to answer:
- Sources/method to inspect:
- Expected decision:
- How it will feed the next artifact:
```

Expected distillation result:

```text
Distillation:
- Domain:
- Gap:
- Method used:
- Options:
- Recommendation:
- Main artifact insertion:
- Appendix / ADR / evidence note:
- Assumptions:
- Risks:
- Verification:
```

Do not mark readiness as `Ready` merely because a distillation task exists. Readiness requires either a returned distillation result, an explicit assumption, a validation task, or a user-accepted unresolved risk.

## Question Waves

### Wave 1: Product And Success

Clarify target user, pain, success, non-goals, and priority.

Examples:

- "Who is the primary user we should optimize for first?"
- "What would make this useful enough for the first version?"
- "What should this explicitly not become?"

### Wave 2: Workflow And Interaction

Clarify how the user moves through the product or process.

Examples:

- "What is the first action the user takes?"
- "What states must exist: empty, loading, error, saved, exported?"
- "Which button or command would the user expect at the moment of decision?"

### Wave 3: Implementation Surface

Clarify frontend/backend/data implications only at the level the user can answer and only when they affect product judgment.

Examples:

- "Do you know where the data should live, or should I propose a storage layout?"
- "Should this be local-first, cloud-backed, or just file-based for MVP?"
- "Which part needs to be reliable first: UI editing, background processing, or export?"

If the user cannot answer, convert the gap to distillation:

```text
你不需要现在懂后端。我会把这个变成后端方案对比：本地文件、轻量数据库、云端服务三种，按你的 MVP 目标给推荐。
```

If the gap is broad, split it by domain before distilling:

- Backend/API: resources, permissions, errors, async jobs.
- Data: entities, fields, storage location, lifecycle, backup.
- Frontend/UI: pages, components, states, buttons.
- PRD: what stays in the main PRD vs appendix / ADR / evidence brief.

### Wave 4: Evidence And Risk

Clarify what must be verified before writing the next artifact.

Examples:

- "Which claim would be most dangerous if we guessed wrong?"
- "Do we have first-hand material, or should this be verified through market/product research?"
- "What would make you later say: technically it worked, but it still cannot be used?"

## Between Waves

After each wave, summarize briefly:

```text
Understood:
- ...

Domain gaps:
- Product:
- Interaction:
- Frontend:
- Backend:
- Data:
- Evidence:
- Acceptance:

Ask-user next:
- ...

Distill instead of asking:
- ...

Risk if we execute now:
- ...
```

## How To Ask

- Ask in the user's language unless they request otherwise.
- Ask one important question per user turn.
- In one visible wave, ask at most 3 questions. If more are tempting, rank them and ask only those that change scope, core workflow, acceptance, data, permissions, business boundary, risk, or Stop Conditions.
- Prefer a choice question with a recommended default when it lowers burden.
- Explain when a question is technical and the user does not need to answer it.
- Do not mix many weak preference questions into a strong-question turn.
- Do not turn small clear tasks into a workshop.
- Do not ask light-code users to choose API schema, database tables, component trees, queue systems, error code taxonomies, or storage internals unless the choice changes a user-visible boundary or risk.
- If the user says "you decide" on a weak question, choose a default and continue.
- If the user says "you decide" on a strong domain question, either state the assumption and risk or route it to distillation.
- If a domain is irrelevant, mark it out of scope instead of asking about it.

## Readiness

Readiness is not "all questions answered." Readiness means every important detail has a destination.

Use this readiness scale:

- **Ready:** Strong ask-user questions are answered; non-user gaps have distillation outputs or clear defaults; acceptance is testable.
- **Partially ready:** Some strong gaps remain but can be handled as assumptions or validation tasks.
- **Not ready:** The next artifact would be misleading because goal, user, scope, workflow, implementation surface, data, or acceptance is unclear.

## Output At Close

When the grill is done, produce a compact handoff:

```text
Goal:
Non-goals:
Key decisions:

Domain decisions:
- Product:
- Interaction / UX:
- Frontend:
- Backend:
- Data:
- Evidence:
- Acceptance:

Ask-user answered:
- ...

Distillation needed:
- ...

Assumptions:
- ...

Risks:
- ...

Acceptance:
- ...

Readiness: Ready / Partially ready / Not ready
Next step:
Where to record:
```

If the result becomes a DailyWork2 task, record the handoff in the task's `TASK.md`, `context.md`, or `state.md`.
