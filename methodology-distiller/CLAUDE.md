---
name: methodology-distiller
description: Use when an active grillme, deep-research, PRD, product planning, architecture, frontend, backend, data, UX, brainstorm, or acceptance workflow has specialist-method gaps the user cannot reasonably answer and needs distilled expert practice, option comparison, recommended defaults, or an appendix-ready decision note. Also use for PRD method-card route smoke such as PRD vs brief, MVP/Future boundary conflicts, missing buttons/states/data/acceptance, PRD too long, PRD Gate loopback, or Grok-style PRD gap questioning.
---

# Methodology Distiller

Internal helper for turning "the user should not have to know this" into a compact, usable method decision.

Use this skill when `grillme` or `deep-research` finds a specialist gap: PRD writing, UX flow, frontend structure, backend/API design, data modeling, architecture tradeoff, brainstorm method, or acceptance strategy. Do not use it as the default public research entry; formal research still enters through `deep-research`.

## Core Rule

Ask the user for lived facts, priorities, constraints, and taste. Distill specialist methods yourself.

The output must help the next artifact, not show off methodology. Put only decisions and executable detail into the main PRD/brief. Put sources, alternatives, and rejected options into an appendix, ADR, evidence brief, or assumptions log.

## Shared Method Vault First

Before ad-hoc method research, check the shared local method vault:

```text
/Users/sure/shared-skills/methodology-vault/
```

Runtime lookup order:

```text
shared method cards
-> current workspace channel
-> personal channel
-> external research pool
-> Method Quality Gate
```

For PRD-specific gaps in this workspace, the current workspace channel is:

```text
/Users/sure/DailyWork2/skills/methodology-distiller/methodology-vault/INDEX.md
```

Read the index first, then select the smallest matching Chinese card. Do not paste a card wholesale into the PRD; use it to produce compact decisions, missing questions, default recommendations, and PRD insertions.

Use local cards when they fit the gap. If local coverage is weak, stale, or missing, inspect external methods and pass them through the Method Quality Gate before treating them as reusable. L4 sources such as Xiaohongshu, blogs, forums, and single experience posts can supply language, examples, pain points, and candidate tactics, but cannot become a default method unless upgraded by cross-check against stronger sources.

When a local method card is used, include its `id` or path in `Method used`. When no trusted method exists, downgrade the answer to an assumption, validation task, candidate note, or appendix-only comparison.

For PRD method-card route smoke, the final user-visible answer must cite the exact card path, not only a semantic pass name or an internal tool-read trace. Use this quick map before answering:

| PRD smoke prompt | Must cite |
|---|---|
| PRD vs brief / unsure whether to write full PRD | `/Users/sure/DailyWork2/skills/methodology-distiller/methodology-vault/cards/prd-type-selector.md` |
| MVP, Future, Out of Scope, or Non-goals boundary conflict | `/Users/sure/DailyWork2/skills/methodology-distiller/methodology-vault/cards/prd-boundary.md` |
| Missing buttons, steps, implementation detail | `/Users/sure/DailyWork2/skills/methodology-distiller/methodology-vault/cards/prd-detail.md` |
| Missing UI states or text sketch | `/Users/sure/DailyWork2/skills/methodology-distiller/methodology-vault/cards/prd-ui-state.md` |
| Missing data fields, storage location, or directory layout | `/Users/sure/DailyWork2/skills/methodology-distiller/methodology-vault/cards/prd-data-storage.md` |
| Missing acceptance path | `/Users/sure/DailyWork2/skills/methodology-distiller/methodology-vault/cards/prd-acceptance-path.md` |
| PRD too long, too scattered, or mixed with research/methodology | `/Users/sure/DailyWork2/skills/methodology-distiller/methodology-vault/cards/prd-subtraction.md` |
| Unsure where a failed PRD gate should loop back | `/Users/sure/DailyWork2/skills/methodology-distiller/methodology-vault/cards/prd-loopback-routing.md` |
| PRD Gate found gaps and the user needs repeat questioning instead of rewriting | `/Users/sure/DailyWork2/skills/methodology-distiller/methodology-vault/cards/prd-grok-loop.md` |

## Inputs

```text
Domain:
User goal:
Unresolved question:
Why not ask the user:
Next artifact:
Constraints:
Known evidence:
```

## Domain Playbook

| Domain | Distill from | Output |
|---|---|---|
| Product / PRD | PRD conventions, user stories, release criteria | Product requirement slice |
| Architecture | ADR / MADR style decision records | Context, options, decision, consequences |
| Backend / API | REST/API guidelines, OpenAPI-shaped contracts | Resources, endpoints, errors, jobs, permissions |
| Frontend | Thinking in React, component-driven states | Page/component/state map |
| Interaction / UX | Task analysis, journey mapping, UI controls and states | Flow, screens, buttons, empty/error/loading states |
| Data | Entity/access-pattern/lifecycle modeling | Fields, storage location, directory layout, retention |
| Brainstorm | Double Diamond, design-thinking ideation, cross-domain analogies | Divergent ideas, collisions, hybrids, convergence |
| Acceptance | QA patterns, smoke tests, measurable success | Shortest test path and done criteria |

## Workflow

1. **Frame the gap:** State the specialist question in plain language.
2. **Search the method vault:** Prefer a fitting local card before new research.
3. **Choose method family:** Pick the smallest method that answers the gap.
4. **Check fit:** State applicability, non-applicability, prerequisites, common misuse, and expected output granularity before recommending a method.
5. **Inspect evidence if needed:** Use `deep-research`, official docs, open-source examples, competitors, or local project patterns when the answer depends on current or external facts.
6. **Quality-gate external methods:** Any new reusable method candidate must be labeled by source level and verdict before runtime use.
7. **Compare options:** Usually 2-4 options. Include "do nothing / defer" when realistic.
8. **Recommend a default:** Choose one option for the current user and scope.
9. **Name the falsifier:** Say what condition would make the recommendation wrong or require revisiting it.
10. **Place the decision:** Decide what enters the main artifact and what goes to appendix / ADR / evidence brief.
11. **Record verification:** Say how to test, revisit, or replace the default.

## Distillation Card

```text
Distillation:
- Domain:
- Gap:
- Method used:
- Source level / verdict:
- Applicability:
- Not suitable when:
- Options:
- Recommendation:
- Falsifier / revisit when:
- Main artifact insertion:
- Appendix / ADR / evidence note:
- Assumptions:
- Risks:
- Verification:
```

## PRD Subtraction Rule

When feeding a PRD, reduce instead of accumulating:

- Main PRD keeps: goal, user, scenario, problem, MVP, non-goals, core flow, key requirements, acceptance, Stop Conditions, evidence summary.
- Appendix keeps: methodology rationale, source notes, long option comparisons, rejected alternatives, detailed evidence tables.
- ADR / implementation note keeps: API design, database structure, file directory, component hierarchy, concrete technical choices, migration strategy, detailed error states.
- Evidence brief keeps: source table and confidence labels.

Only move technical details into the main PRD when they change product judgment, scope, acceptance, permissions, data risk, or Stop Conditions. If the PRD becomes hard to read, move explanation out and leave a decision plus link/path.

## PRD Quality Gate

Use this gate when a PRD, product spec, or PRD-ready brief looks complete but may still be too vague to execute.

PRD is not an execution handoff and not a product-idea essay. Treat it as a product judgment document: it must let the user and downstream executor judge what V1 does, what it does not do, what success looks like, and when work must stop for clarification.

Core formula:

```text
Ready PRD = Boundary x Detail x Evidence x Acceptance x Stop Conditions
```

`Boundary` and `Detail` are hard indicators:

- **Boundary:** target user, scenario, MVP, non-goals, future, out-of-scope, assumptions, constraints, unresolved risks.
- **Detail:** main PRD must contain user-visible flows, screens/areas, key buttons/commands, core states, inputs/outputs, and data-location decisions that affect product judgment. API design, database structure, file directory, component hierarchy, concrete technical choices, and detailed error taxonomies belong in appendix / ADR / implementation note unless they change scope, acceptance, permissions, data risk, or Stop Conditions.
- **Acceptance:** shortest acceptance path, success criteria, failure criteria, and at least one edge case.
- **Stop Conditions:** unclear target, boundary, evidence, acceptance, account/payment/external-service/data-migration risk, or missing user confirmation must stop PRD finalization or execution.

Key expression rules:

- Write MVP as user-visible outcomes, not feature names.
- Keep current facts, current change/V1, and future possibilities separate.
- For core behavior, add `Requirement / Scenario`; use `Given / When / Then` when a behavior must be verifiable.
- Keep technical plan and task breakdown out of the PRD body unless they are product-facing constraints or data-location decisions.

The gate is independent. Do not mark a PRD `Ready` only because `grillme` finished or because a distillation card exists. Re-read the draft as if an implementer must build from it without extra context.

### Gate Outcomes

| Outcome | Meaning | Next action |
|---|---|---|
| `Ready` | Boundary, detail, evidence, acceptance, and Stop Conditions are all executable enough for the current scope. | Write or finalize PRD. |
| `Needs Loopback` | The PRD is promising, but one or more missing pieces would change behavior, scope, implementation, data, or verification. | Route the gap back before finalizing. |
| `Downgrade` | The input cannot support a PRD yet. | Produce `idea_note`, `discovery_note`, `decision_brief`, `reader_brief`, or `evidence_brief`. |

### PRD Gap Triage

Before asking the user, classify every gap by owner. Do not turn all missing PRD detail into user questions.

| Owner | Use when | Route | Ask user? | Agent can resolve? |
|---|---|---|---|---|
| `User` | Only the user knows the goal, tradeoff, taste, real scenario, priority, or unacceptable outcome. | `grillme` / `prd-grok-loop` | Yes | No |
| `Evidence` | External fact, competitor claim, API behavior, tool limit, current UI/product behavior, open-source maturity, platform/account/pricing/permission dependency, or data-rights constraint is missing. | `deep-research` / narrowed verification | No | Yes, by research; if the dependency cannot be resolved by the agent, convert it to a Stop Condition |
| `Method` | Specialist default is missing: PRD writing, frontend/backend/API/data/architecture/UX/acceptance method. | `methodology-distiller` | No | Yes, by distillation |
| `Spec` | Facts are enough, but the PRD lacks steps, states, fields, paths, scenarios, or acceptance wording. | PRD detail / UI state / data / acceptance / subtraction pass | No | Yes, by spec pass |
| `Too fuzzy` | Target, user, scenario, or problem is still not valid enough for a PRD. | Downgrade or return to discovery / `grillme` | Maybe | No |

For each failed gate item, output:

```text
Gap:
Owner: User / Evidence / Method / Spec / Too fuzzy
Route:
Ask user: Yes / No
Agent can resolve without user: Yes / No
Minimal next action:
```

### Loopback Routing

| Missing piece | Route to |
|---|---|
| User, scenario, priority, taste, constraint, boundary conflict | `grillme` |
| External facts, competitor claims, source confidence, current product behavior, platform/account/pricing/permission constraints | `deep-research` / narrowed verification; unresolved constraints become Stop Conditions |
| PRD writing method, frontend/backend/API/data/UX/architecture default | `methodology-distiller` |
| Screen flow, button behavior, UI states, data fields, file paths, acceptance steps | PRD detail pass, with domain distillation if needed |
| Too much explanation, weak readability, mixed rationale and spec | PRD subtraction pass |

### PRD Gate Card

```text
PRD Quality Gate:
- Boundary: Pass / Gap
- Detail: Pass / Gap
- Evidence: Pass / Gap
- Acceptance: Pass / Gap
- Stop Conditions: Pass / Gap
- Verdict: Ready / Needs Loopback / Downgrade
- Loopback target:
- Gap triage:
  - Gap:
  - Owner: User / Evidence / Method / Spec / Too fuzzy
  - Route:
  - Ask user: Yes / No
  - Agent can resolve without user: Yes / No
  - Minimal next action:
- Minimal missing facts:
- Minimal missing decisions:
- What can stay in main PRD:
- What should move to appendix / ADR / evidence brief:
```

## Brainstorm Collision Rule

For weak brainstorms, do not only list directions. Create collisions:

```text
Base idea:
Adjacent solution:
Borrowed method:
Collision:
New option:
Why it is better / worse:
Evidence needed:
```

Use this when the user asks for ideas with more creative force, when Phase 2 feels like a list, or when adjacent fields may solve the same problem differently.

## Method Sources To Prefer

Prefer the local vault first:

- `/Users/sure/DailyWork2/skills/methodology-distiller/methodology-vault/INDEX.md` for PRD type selection, executable spec, boundary, detail, UI state, data storage, acceptance path, subtraction, loopback routing, and Grok-style question rollback.
- `/Users/sure/shared-skills/methodology-vault/cards/prd/executable-prd-subtraction.md`
- `/Users/sure/shared-skills/methodology-vault/cards/architecture/adr-mvp-tradeoff.md`
- `/Users/sure/shared-skills/methodology-vault/cards/backend-api/backend-api-mvp-slice.md`
- `/Users/sure/shared-skills/methodology-vault/cards/data/lightweight-data-storage-lifecycle.md`
- `/Users/sure/shared-skills/methodology-vault/cards/ux/task-flow-ui-state-inventory.md`
- `/Users/sure/shared-skills/methodology-vault/cards/brainstorm/idea-collision.md`
- `/Users/sure/shared-skills/methodology-vault/cards/acceptance/smoke-test-shortest-path.md`

If these do not fit, research or compare against:

- PRD/product: Atlassian-style PRD, user stories, release criteria, open questions.
- Architecture: ADR / MADR.
- API/backend: Microsoft REST API Guidelines, Zalando RESTful API Guidelines, Google AIP, OpenAPI.
- Frontend/UI: React "Thinking in React", Storybook component states, Material Design controls, WCAG.
- Data: Prisma data modeling, PostgreSQL constraints, MongoDB schema design process.
- UX: NN/g task analysis and journey mapping.
- Brainstorm: Double Diamond and design-thinking ideation.

Use these as patterns, not as copied templates.

## When To Stop

Stop when the gap has a destination:

- decision made,
- assumption recorded,
- validation task created,
- or artifact downgraded because evidence is insufficient.

Do not keep researching methods after a reasonable default is enough for the current MVP.

## Smoke Prompts

- `我想做一个简历成长系统，但我不懂后端和数据怎么设计，帮我问透。`
- `PRD 我不太会写，你去找成熟写法，再按我们项目特点改。`
- `帮我把这个产品想法压成 PRD，前端、后端、数据层都别漏。`
- `头脑风暴别只列方向，要把相邻方案碰一碰。`
