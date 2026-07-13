---
name: skill-reforge
status: draft
description: >
  Transform an existing third-party Agent Skill into a customized SKILL.md aligned
  with the user's workflow, tools, output preferences, safety boundaries, and
  validation rules. Trigger when the user hands you a Skill (GitHub link, pasted
  SKILL.md, folder, or reference) and asks to adapt, rewrite, or customize it
  for their own use. Do NOT trigger for creating a brand-new skill from scratch,
  for trivial formatting fixes, or when the user only wants a summary of what
  the skill does.
---

# Skill Reforge

## Purpose

Take a working Skill built for someone else's environment and reshape it into
one that fits the current user's tools, habits, and safety constraints.

This is diagnostic surgery, not cosmetic makeup. Preserve the functional skeleton.
Strip the scene-specific skin. Add the user's own context.

## When to use this skill

- User provides a GitHub URL, SKILL.md text, or folder and says "adapt this for
  me", "make this fit my workflow", "rewrite this skill", or similar.
- User references an existing Skill and wants it tuned for Claude Code, OpenClaw,
  or another agent system they actually use.
- User wants a third-party Skill simplified, hardened, or retargeted to their
  personal or team context.

## When not to use this skill

- User describes a workflow from scratch and wants a new Skill created. Route
  that to a skill-creation flow instead.
- User only wants a review, summary, or critique of a Skill without changing it.
- User wants a one-line formatting tweak or typo fix.
- The provided source is not a Skill at all (e.g., a generic blog post, a
  requirements doc).

## User defaults

Unless the user explicitly overrides:

1. Output format: Markdown, Obsidian-friendly.
2. Target runtime: Claude Code / OpenClaw / comparable agent system.
3. Skill output: a single `SKILL.md` file. Drafts go under `~/DailyWork2/task_draft/skill-reforge/`; installation into `~/DailyWork2/skills/` requires confirmation.
4. All rules must be executable actions, not abstract principles.
5. Every flow must include a self-check step.
6. Every important task must include failure handling.
7. Prefer making reasonable assumptions over asking scattered questions.
8. Questions that must be asked should be batched, not dribbled out turn by turn.
9. If information is missing, generate a usable version with a `待确认项` label.
10. Never inherit the original author's tool paths, credentials, or environment
    assumptions without re-confirmation or parameterization.

## Required inputs

| Input | Why required | What to do if missing |
|---|---|---|
| Original Skill content or access path | Cannot diagnose without the patient | If a GitHub URL is given, fetch `SKILL.md`, `README.md`, and key scripts. If that fails, ask the user to paste the content. |
| At least one signal of the user's intent | Need to know what "fit my workflow" means | Infer from context. If still unclear, ask the single most impactful clarification question. |

## Optional inputs

| Input | Used for |
|---|---|
| User's tool environment (OS, CLI tools, MCP servers) | Replacing or parameterizing tool dependencies. |
| User's project rules or conventions | Aligning output style and directory layout. |
| User's output preferences beyond defaults | Customizing tone, structure, or artifact types. |
| Target directory for the new Skill | Determining where to write the output. Default: `~/DailyWork2/task_draft/skill-reforge/`. |

## Boundary analysis

### Use boundary

| Scenario | Action |
|---|---|
| Transform a third-party Skill into a personal/team Skill | YES — core purpose. |
| Create a Skill from a raw workflow note | NO — route to skill-creation. |
| Summarize or critique without rewriting | NO — just answer directly. |
| Fix a typo or reformat | NO — too small, handle inline. |
| Involves destructive file operations (overwrite, delete) | YES — but enter safety confirmation sub-flow first. |

### Input boundary

| Item | Required? | Missing handling | Ask user? |
|---|---|---|---|
| Original Skill content | Yes | Fetch or request paste | Only if fetch fails |
| User goal | Yes | Infer from context | Only if ambiguous |
| Environment | No | Default to Claude Code / OpenClaw | No |
| Output format | No | Default Markdown / Obsidian | No |
| Target directory | No | Default `~/DailyWork2/task_draft/skill-reforge/` | No |
| Permissions (script execution, file overwrite) | No | Default deny | No |
| Internet access | No | Only for fetching source | No |

### Tool boundary

| Check | Rule |
|---|---|
| Original Skill depends on specific CLI tools | Parameterize or replace with generic equivalents. |
| Original Skill depends on Python / Node / Shell scripts | Assess if the script is essential. If yes, convert to instructions the agent can execute. If no, delete. |
| Original Skill depends on external APIs or network | Flag as `待确认项`. Remove hardcoded keys. |
| Original Skill assumes specific OS | Remove OS-specific paths; use generic instructions. |
| Dangerous operations (rm, mv, deploy, sudo) | Require explicit user confirmation before including. |
| Suitable for Claude Code | Yes — output is pure Markdown with executable rules. |
| Suitable for OpenClaw | Yes — same reasoning. |

### Output boundary

| Output | Required? | Notes |
|---|---|---|
| Complete SKILL.md | Yes | Single file, frontmatter + executable rules. |
| Transformation report | Yes | Brief markdown doc summarizing what changed and why. |
| File tree analysis | Only if original Skill has complex nested structure. |
| Risk report | Yes | List of `待确认项` and any safety concerns. |
| Next-step suggestions | Yes | 3 concrete next iteration directions. |
| Code/scripts | No | Unless user explicitly asks, do not generate new scripts. |
| HTML / visual reports | No | User prefers Markdown. |

### Safety boundary

1. Never overwrite an existing file without checking first. If a file exists,
   write to a new path (e.g., append `-v2`) and warn the user.
2. Never execute or instruct execution of destructive commands without explicit
   user confirmation.
3. Never fabricate test results or evaluation scores.
4. Never assume a file exists at a hardcoded path.
5. Never hide uncertainty. Label all unverified assumptions as `待确认项`.
6. Never migrate secrets, API keys, personal paths, or account info from the
   original Skill.
7. Never write one-time configuration as a permanent rule.
8. Never strip safety warnings just to make the Skill shorter.

## Clarification rules

### Must ask the user

Batch these into one message. Do not ask more than 5. If more than 5 are
needed, ask the top 5 and park the rest in `待确认项`.

1. **Target purpose is completely unclear.** Example: user says "fix this" but
   does not say whether they want a writing Skill, a coding Skill, or a
   project-management Skill.
2. **The request involves overwriting existing project files or system config.**
3. **The request involves secrets, credentials, private data, or commercial info.**
4. **Two mutually exclusive directions are equally valid.** Example: "make it a
   writing Skill" vs "make it a execution Skill".
5. **Original Skill content is so minimal that core function cannot be determined.**
6. **User's stated goal directly conflicts with the original Skill's design.**
   Example: user wants a "one-line quick skill" but the source is a 2000-line
   governed governance system.
7. **The result would affect multiple projects or shared directories.**

### Do not ask the user

Just decide and proceed. Note the assumption in the output.

| Situation | Default decision |
|---|---|
| Output format unspecified | Markdown, Obsidian-compatible |
| Self-check unspecified | Include a `Quality checklist` section |
| Failure handling unspecified | Include a `Failure handling` section |
| Example count unspecified | Provide 3 examples |
| Skill name unspecified | Rename; do not keep original author's name |
| Claude Code compatibility unspecified | Assume yes |
| Obsidian readability unspecified | Assume yes |
| Logging unspecified | Include a brief `Transformation report` |
| Internet dependency unspecified | Assume no external network needed |
| Script execution unspecified | Scripts optional, not required |

## Transformation modes

Choose the mode before writing anything. Announce the choice in the first line
of output.

| Mode | When to choose | What happens |
|---|---|---|
| **A. Conservative** | Original Skill is high quality; user's needs are close to it. | Keep original structure. Replace output format, trigger wording, and a few rules. Low risk, fast. |
| **B. Workflow-fit** (default) | Original Skill has value but does not fully fit. User wants their habits, tools, and safety rules woven in. | Keep core capability and proven methodology. Rewrite scene rules, tool assumptions, and output contracts. Add user's self-check and failure-handling style. This is the default mode. |
| **C. Deep refactor** | Original Skill is only inspirational. Structure is wrong for user's context. User needs a new system component. | Borrow ideas only. Rebuild structure from scratch. Higher risk, highest fit. |

**Default**: B. Workflow-fit.

## Workflow

### Phase 1 — Ingest

1. Fetch or read the original Skill.
2. List every file or section found.
3. Classify each item as:
   - `skeleton` (functional logic, worth keeping)
   - `skin` (scene-specific, must replace)
   - `author_preference` (original author's taste, do not inherit)
   - `tool_env` (tool path, OS assumption, credential — must reconfirm or parameterize)
   - `unknown` (cannot tell — flag as `待确认项`)

### Phase 2 — Diagnose

4. State the original Skill's core purpose in one sentence.
5. State what problem it solves.
6. List its trigger scenarios.
7. List its inputs and outputs.
8. List its main workflow steps.
9. Identify hidden assumptions:
   - Who was the implied user?
   - What environment did it assume?
   - What tools did it require?
   - What quality checks did it rely on?
10. Identify high-risk parts (destructive ops, hardcoded paths, heavy dependencies).

### Phase 3 — Select mode

11. Announce the chosen mode (A / B / C) with one-line justification.
12. If mode is unclear, default to B and note why.

### Phase 4 — Map

13. Produce a mapping table:

    | Original module | Original purpose | Value | Keep? | Transformation | Maps to user need |
    |---|---|---|---|---|---|

    Value levels: `high` / `medium` / `low` / `risk` / `unrelated`
    Keep: `yes` / `no`
    Transformation: `keep` / `rewrite` / `parameterize` / `simplify` / `delete` / `merge`

### Phase 5 — Design

14. Draft the new Skill's architecture:
    - Name
    - One-line purpose
    - Trigger description (specific enough to route correctly)
    - In-scope tasks
    - Out-of-scope tasks
    - Required inputs
    - Output format
    - Self-check mechanism
    - Failure handling

### Phase 6 — Generate

15. Write the complete new `SKILL.md`.
16. Include frontmatter with `name` and `description`.
17. Ensure `description` is specific enough that an agent can decide whether to
    load this Skill.
18. Body must be executable rules, not an essay.
19. Include at least 3 examples covering:
    - a complete-information transformation
    - an incomplete-information transformation
    - a transformation involving a dangerous operation
20. Include `Quality checklist` and `Failure handling` sections.

### Phase 7 — Report

21. Write a concise `Transformation report`:
    - Mode chosen
    - What was kept
    - What was deleted
    - What was rebuilt
    - Boundary conditions
    - `待确认项` list
    - Current risks
    - Next-step suggestions

### Phase 8 — Validate

22. Run the self-check:
    - [ ] Did not copy the original Skill verbatim.
    - [ ] Identified hidden assumptions.
    - [ ] Added boundary conditions.
    - [ ] Defined when to ask the user.
    - [ ] Defined when not to ask the user.
    - [ ] Trigger description is specific.
    - [ ] Input requirements are explicit.
    - [ ] Output format is explicit.
    - [ ] File and tool rules exist.
    - [ ] Safety rules exist.
    - [ ] Failure handling exists.
    - [ ] Quality checklist exists.
    - [ ] Fits user's workflow.
    - [ ] Can be saved directly as `SKILL.md`.
23. If any check fails, fix it before delivering.

## Output format

Two artifacts:

1. **New `SKILL.md`** — single file, ready to save.
2. **Transformation report** — short Markdown with the sections listed in
   Phase 7.

Both must be Obsidian-friendly: use standard Markdown, avoid HTML-heavy layouts,
use headings for structure, keep tables simple.

## File and directory rules

- Write the new `SKILL.md` to the path the user specifies. Default:
  `~/DailyWork2/task_draft/skill-reforge/<skill-name>/SKILL.md`.
- Install into `~/DailyWork2/skills/<skill-name>/SKILL.md` only after the user confirms the draft should become an active DailyWork2 skill.
- If the target path already exists, do not overwrite. Append a version suffix
  (e.g., `-v2`) and notify the user.
- Do not create nested `references/`, `scripts/`, `evals/`, or `reports/`
  directories unless the user explicitly asks. The default output is a single
  `SKILL.md`.
- If the original Skill had essential assets (templates, fixture files) that are
  still relevant, copy them into the same directory as `SKILL.md` and reference
  them by relative path.

## Tool rules

- Do not require Python, Node, Make, or any local toolchain to validate the
  output. Validation is done via the self-check list in the SKILL.md itself.
- If the original Skill included runnable scripts, assess whether the agent can
  perform the same work inline. If yes, convert to text rules. If no, flag as
  `待确认项`.
- Network use is limited to fetching the original Skill content. Do not require
  online APIs during the transformed Skill's normal execution.

## Safety rules

- Before any write operation, check if the target path exists.
- Before including any destructive instruction (delete, overwrite, move,
  remote deploy), require a user confirmation step in the Skill text itself.
- Do not port secrets, keys, or personal paths from the original Skill.
- Label every unverified assumption as `待确认项`.
- Never claim a check passed if you did not actually perform it.

## Quality checklist

Use this before delivering the transformed Skill:

- [ ] Original Skill was fully ingested and classified.
- [ ] Skeleton vs skin was correctly separated.
- [ ] Mode was explicitly chosen and justified.
- [ ] Mapping table is complete.
- [ ] New `description` is specific and routeable.
- [ ] Body contains only executable rules, not exposition.
- [ ] Trigger scenarios are explicit.
- [ ] Exclusion scenarios are explicit.
- [ ] Input requirements are listed.
- [ ] Output format is fixed.
- [ ] Self-check mechanism is included.
- [ ] Failure handling is included.
- [ ] At least 3 examples are included.
- [ ] `待确认项` are listed.
- [ ] Safety rules are present.
- [ ] File write rules are present.
- [ ] No hardcoded secrets or paths were inherited.
- [ ] No destructive operations are hidden.
- [ ] Report is included.

## Failure handling

| Failure mode | Response |
|---|---|
| Original Skill content cannot be fetched or is incomplete | Ask user to paste it. If unavailable, generate a skeletal version with a large `待确认项` block. |
| Original Skill is so large it exceeds context budget | Summarize the top-level structure first, ask user which sections matter most, then focus. |
| User's goal conflicts with original Skill design | Pause, present the conflict, recommend mode C (deep refactor), and ask for confirmation. |
| Mode selection is ambiguous | Default to B, explain why, and note what would change under A or C. |
| Self-check finds unresolved issues | Fix them. If a fix requires user input, batch the questions and park the rest. |
| Target file already exists | Write to a versioned path. Notify user. Do not overwrite. |

## Examples

### Example 1 — Complete information

**User input:**
> Here is the SKILL.md from `github.com/someone/data-cleaning-skill`. I want it
> adapted for my Claude Code setup. I only clean CSVs locally, I don't use their
> cloud pipeline, and I want the output in Markdown tables.

**Agent action:**
1. Fetch the repo's `SKILL.md`, `README.md`, and any visible scripts.
2. Classify: cloud-pipeline steps = `tool_env` to delete; CSV cleaning logic =
   `skeleton` to keep; output format = `skin` to replace.
3. Select mode B (workflow-fit).
4. Map table shows cloud dependency deleted, local CLI commands parameterized,
   output switched to Markdown tables.
5. Generate new `SKILL.md` with local-file-only boundary, Markdown table output
   contract, and a self-check for CSV schema assumptions.
6. Deliver to `~/DailyWork2/task_draft/skill-reforge/csv-clean/SKILL.md`.

### Example 2 — Incomplete information

**User input:**
> I found this skill online. Make it work for me. [GitHub URL]

**Agent action:**
1. Fetch the Skill.
2. No user environment or preferences given.
3. Apply defaults: Claude Code compatible, Markdown output, `~/DailyWork2/task_draft/skill-reforge/` target.
4. Select mode B.
5. Generate usable version.
6. Label `待确认项`:
   - Whether local or remote file operations are preferred.
   - Whether the user has any CLI tools the original Skill assumed.
   - Whether the original Skill's output format should be preserved or switched.
7. Deliver and ask the user to confirm or refine the 3 flagged items.

### Example 3 — Dangerous operation

**User input:**
> Adapt this deployment Skill for my server. It currently deploys to AWS; I want
> it to deploy to my VPS at 100.113.27.115. Keep the rollback logic.

**Agent action:**
1. Fetch the Skill. Identify rollback scripts and deployment commands.
2. Classify: AWS-specific commands = `tool_env` to replace; rollback logic =
   `skeleton` to keep.
3. Detect dangerous operations: remote SSH commands, service restarts, potential
   downtime.
4. Before generating, insert a safety sub-flow: the new SKILL.md must require
   explicit user confirmation before executing any remote command.
5. Replace AWS paths with parameterized `<REMOTE_HOST>` and `<SSH_KEY_PATH>`.
6. Add a `Safety rules` section that mandates dry-run confirmation.
7. Label `待确认项`: actual SSH key location, sudo requirements, backup policy.
8. Deliver and warn user to review the safety section before use.
