---
id: acceptance-smoke-test-shortest-path
title: Shortest Path Smoke Test
domain: acceptance
problem: A plan says "done" but the user has no concrete way to verify whether the result works.
best_for: MVP PRDs, skill routing changes, local tools, UI workflows, and research-to-implementation handoffs.
not_for: Formal QA plans that require full test matrices or regulated validation.
quality_level: silver
source_level: L2
last_reviewed: 2026-07-03
owner: shared
---

# Shortest Path Smoke Test

## Method Summary

Define the shortest realistic path that proves the core promise works. Smoke tests should verify user-visible behavior, not just internal completion.

## Inputs Needed

- User facts: what success feels like, what failure would be obvious, what the user can inspect.
- Project constraints: local command, UI path, file path, prompt, fixture, or browser target.
- Evidence needed: current acceptance target and known failure modes.

## Steps

1. State the core promise in one sentence.
2. Define the shortest trigger: command, prompt, click path, file, or input.
3. Define expected visible output.
4. Define one negative or downgrade case.
5. Record actual result as pass, partial pass, or fail with failure layer.

## Outputs

- Main artifact insertion: acceptance criteria and shortest test path.
- Appendix / ADR / evidence note: detailed matrix, failure diagnosis, logs.

## Evidence / Sources

- Source family: smoke testing, acceptance criteria, done definition, routing contract tests.
- Cross-check: run at least one real command, prompt, screenshot, or static scan where feasible.

## Adaptation Notes

For skill systems, smoke prompts count as tests only if expected route, actual route, failure layer, and minimum repair file are recorded.

## Failure Modes

- Test checks file existence but not behavior.
- Expected result is vague.
- No downgrade case.
- Failure is recorded without the likely layer.

## Verification

The user can run or read the smoke test and know exactly what passed, what failed, and where to fix next.
