---
name: external-skill-adoption
description: Use after harvest-tool identifies an external open-source skill or plugin that might be adopted into DailyWork2. Decides whether to import, trial, localize, reject, or keep as reference; records source, license, coverage, local changes, owner, and status. Use when the user asks to bring in an existing skill, says a tool can be directly used, asks how to design skill adoption, or wants grillme-like tools landed without reinventing them.
---

# External Skill Adoption

This is the post-harvest workflow for external skills.

It does not replace `harvest-tool`. Use `harvest-tool` first to discover and inspect repositories. Use this skill after there is at least one concrete source skill to evaluate.

## Principle

If an external skill covers 70% or more of the need, import and trial before rewriting.

Do not turn every useful prompt into a new DailyWork2-owned skill. Prefer this order:

```text
reference only -> candidate -> trial -> adopted -> localized
```

Reject when license, dependency, trigger behavior, or maintenance burden is unclear.

## Inputs

Gather these from harvest output or repository files:

- source repo URL
- skill path
- license
- original trigger description
- required dependencies or tools
- expected coverage of the DailyWork2 need
- risks: global behavior, destructive actions, credentials, remote services

## Decision States

| State | Meaning |
|---|---|
| `reference` | Worth reading, not imported. |
| `candidate` | Looks useful, not installed yet. |
| `trial` | Imported for real use, still under observation. |
| `adopted` | Kept as a DailyWork2-visible skill. |
| `localized` | Adapted to local language, paths, task rules, or tools. |
| `rejected` | Explicitly not used. |

## Workflow

1. **Check fit**
   - What problem does the external skill solve?
   - Does it cover at least 70% of the user need?
   - Is it narrower, broader, or different from the current DailyWork2 gap?

2. **Check safety**
   - Does it run commands, edit files, use credentials, call remote services, or alter global behavior?
   - If yes, trial it only after the user confirms the risk.

3. **Check ownership**
   - `dailywork2-owned`: copied or localized into `/Users/sure/DailyWork2/skills/<skill>`.
   - `shared-skill`: symlinked or kept under `/Users/sure/shared-skills` when useful across workspaces.
   - `external-reference`: harvested but not installed.

4. **Import lightly**
   - Preserve source and license in `SKILL.md` or registry notes.
   - Keep local changes small.
   - Avoid creating a marketplace, CLI, or hook unless separately approved.

5. **Record**
   - Update `skills/SKILL-REGISTRY.md` when the skill becomes visible under DailyWork2.
   - Update the relevant task `artifacts.md` if the adoption came from a task.
   - Update `scripts/verify-workspace.sh` only for adopted skills that should be structurally required.

## Adoption Record

Use this compact record in registry notes or task artifacts:

```text
skill_name:
source_repo:
source_path:
license:
coverage_estimate:
local_changes:
status: reference / candidate / trial / adopted / localized / rejected
owner:
next_review:
```

## Lessons From References

- `majiayu000/claude-skill-registry`: borrow source/provenance, license awareness, deduplication, and generated-vs-owned separation.
- `nextlevelbuilder/skillx`: borrow search -> use -> feedback, but do not build a marketplace for DailyWork2 now.
- `sydgren/skills`: borrow one canonical `skills/<name>/SKILL.md` source and plugin wrapping without content duplication.
- `Jekudy/grillme-skill`: a good first adoption example; localize language and Codex interaction, keep the interview-wave idea.

## Exit

End with one of:

- Import now.
- Keep as harvested reference.
- Trial for one task.
- Localize before use.
- Reject and explain why.
