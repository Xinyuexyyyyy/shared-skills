---
id: architecture-adr-mvp-tradeoff
title: MVP ADR For Technical Tradeoffs
domain: architecture
problem: A technical choice affects future work, but the main PRD should not carry a long engineering debate.
best_for: Backend, frontend, storage, workflow, or integration decisions with 2-4 realistic options.
not_for: Obvious local implementation details that do not affect behavior, reversibility, or cost.
quality_level: silver
source_level: L2
last_reviewed: 2026-07-03
owner: shared
---

# MVP ADR For Technical Tradeoffs

## Method Summary

Use a compact Architecture Decision Record when a choice has meaningful consequences. Keep the main artifact to "decision + impact"; store options and consequences in ADR.

## Inputs Needed

- User facts: tolerance for complexity, speed, maintainability, data risk, budget.
- Project constraints: current stack, deploy path, local files vs service, privacy, rollback needs.
- Evidence needed: examples from local codebase, official docs, mature practice, or comparable tools.

## Steps

1. State the decision in one sentence.
2. List 2-4 options, including "defer" when realistic.
3. Compare by user impact, build effort, reversibility, risk, and future path.
4. Choose a default for the current MVP.
5. Record consequences and revisit trigger.

## Outputs

- Main artifact insertion: `Decision: use X because Y. Revisit when Z.`
- Appendix / ADR / evidence note: options table and consequences.

## Evidence / Sources

- Source family: ADR / MADR style decision records, local project patterns, official stack docs.
- Cross-check: one local compatibility check or one mature public pattern.

## Adaptation Notes

Do not write ADRs for everything. Use this only when changing the choice later would cost real time or confuse the PRD.

## Failure Modes

- ADR becomes a research essay.
- Options ignore user-facing impact.
- Decision is technically elegant but too heavy for the MVP.

## Verification

The ADR passes when the user can understand the tradeoff and the implementer can act without reopening the entire debate.
