---
id: ux-task-flow-ui-state-inventory
title: Task Flow And UI State Inventory
domain: ux
problem: A feature sounds clear, but screens, buttons, empty/loading/error/success states, and user recovery paths are missing.
best_for: PRD detail passes, frontend planning, light-code apps, and workflow tools.
not_for: Pure backend jobs with no user-facing interaction.
quality_level: silver
source_level: L2
last_reviewed: 2026-07-03
owner: shared
---

# Task Flow And UI State Inventory

## Method Summary

Turn a user goal into a step-by-step flow and inventory every state the UI must represent. This prevents "beautiful but unusable" specs.

## Inputs Needed

- User facts: goal, starting point, expected finish, taste, tolerance for friction.
- Project constraints: device, viewport, existing UI conventions, accessibility needs.
- Evidence needed: comparable workflows, existing app patterns, design system rules.

## Steps

1. Write the happy path as user steps.
2. For each step, list screen/section, primary action, secondary action, and cancel/back path.
3. Add states: empty, loading, success, error, disabled, partial, conflict, and done.
4. Add copy requirements only where the user needs guidance or feedback.
5. Mark unclear states as PRD loopback items.

## Outputs

- Main artifact insertion: flow table and UI state inventory.
- Appendix / ADR / evidence note: alternative flows and deferred states.

## Evidence / Sources

- Source family: task analysis, journey mapping, component-state practice, accessibility/control guidelines.
- Cross-check: one comparable product or existing local UI flow.

## Adaptation Notes

Do not invent decorative UI. For tools, prioritize scanability, predictable controls, and clear recovery.

## Failure Modes

- Buttons are named but behavior is unclear.
- Error and empty states are missing.
- UI states are too abstract for implementation.
- Visual taste replaces task clarity.

## Verification

Walk through the flow as a first-time user. Every click should have a visible result, and every failure should tell the user what they can do next.
