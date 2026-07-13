---
id: backend-api-mvp-slice
title: Backend API MVP Slice
domain: backend-api
problem: The user knows the desired product effect but should not have to invent backend resources, endpoints, jobs, or error behavior.
best_for: Light-code products that need enough backend shape for a PRD or implementation plan.
not_for: High-scale distributed systems, security-critical systems, or regulated infrastructure without specialist review.
quality_level: silver
source_level: L2
last_reviewed: 2026-07-03
owner: shared
---

# Backend API MVP Slice

## Method Summary

Translate product actions into resources, commands, background jobs, permissions, and errors. Prefer a small, explicit backend surface over abstract "backend support".

## Inputs Needed

- User facts: main user actions, saved objects, import/export needs, privacy sensitivity.
- Project constraints: local-only vs server, authentication needs, file paths, expected volume.
- Evidence needed: local stack conventions, REST/OpenAPI-shaped contracts, comparable product flows.

## Steps

1. Convert each core user action into a backend capability: create, read, update, delete, import, export, analyze, generate, sync, or search.
2. Name resources in product language, not database language.
3. For each capability, specify input, output, success state, error state, and permission assumption.
4. Separate synchronous actions from background jobs.
5. Mark unknowns as assumptions or validation tasks.

## Outputs

- Main artifact insertion: resource/action table, error states, permission assumptions.
- Appendix / ADR / evidence note: endpoint style, alternative backend options, rejected complexity.

## Evidence / Sources

- Source family: REST API guidelines, OpenAPI-style contracts, local project conventions.
- Cross-check: one example endpoint/resource pattern from the current stack or mature reference.

## Adaptation Notes

For local MVPs, a "backend" may be a file writer, script, or local service. Still describe inputs, outputs, errors, and storage.

## Failure Modes

- Backend section only says "store data" or "call AI".
- Error states are missing.
- Background jobs block the UI.
- Permissions and privacy assumptions are invisible.

## Verification

Pick the top 3 user actions and confirm each has an input, output, stored result, failure behavior, and shortest manual test.
