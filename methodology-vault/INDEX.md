# Methodology Vault

共享方法论库。它给 `methodology-distiller`、`grillme`、`deep-research` 和其他工作区提供可复用的方法卡。

## Core Rule

先查本地方法卡，再查工作区 channel，再查个人偏好；外部材料必须过质量门，才能从候选变成默认方法。

```text
shared cards
-> current workspace channel
-> personal channel
-> external research pool
-> Method Quality Gate
```

## Directory Map

```text
methodology-vault/
├── INDEX.md
├── cards/
│   ├── common/
│   ├── prd/
│   ├── ux/
│   ├── frontend/
│   ├── backend-api/
│   ├── data/
│   ├── architecture/
│   ├── brainstorm/
│   ├── resume-career/
│   └── acceptance/
├── channels/
│   ├── dailywork2/
│   ├── study-research/
│   ├── content-work/
│   └── personal/
├── candidates/
├── reviews/
└── deprecated/
```

## Card Status

| Verdict | Meaning | Runtime Use |
|---|---|---|
| `gold` | Strong source, strong fit, operational, cross-checked. | Can be a default method. |
| `silver` | Strong enough for common use, but context assumptions remain. | Recommend with assumptions. |
| `bronze` | Useful partial method. | Supplement a stronger method. |
| `candidate` | Promising but not reviewed enough. | Store for review, do not default. |
| `inspiration` | Good language, pain signal, example, or trick. | Brainstorm/example only. |
| `rejected` | Vague, stale, too heavy, misleading, or untraceable. | Do not use. |

## Source Levels

| Level | Meaning | Can Support Default? |
|---|---|---|
| `L1` | Canonical, official, standard, or classic method. | Yes. |
| `L2` | Mature public practice, large-company guideline, mature open-source pattern. | Yes, after fit check. |
| `L3` | Expert/community practice, repeated case study, practitioner consensus. | Sometimes, with cross-check. |
| `L4` | Xiaohongshu, blog/forum/anecdote/search snippet, single experience post. | No, unless upgraded by verification. |

L4 material is valuable for pain language, examples, tactics, and edge cases. It cannot alone define a reusable default method.

## How To Use

1. Identify the specialist gap: PRD, UX, frontend, backend/API, data, brainstorm, architecture, resume-career, or acceptance.
2. Search the matching `cards/` folder first.
3. If a card fits, use its `Steps`, `Inputs Needed`, `Outputs`, and `Verification`.
4. If no card fits, create a quality-gate review in `reviews/` or a raw candidate note in `candidates/`.
5. Put only the decision and executable details in the main artifact. Put method rationale, source notes, and rejected options in appendix, ADR, or evidence brief.

## Current Seed Cards

- `cards/prd/executable-prd-subtraction.md`
- `cards/architecture/adr-mvp-tradeoff.md`
- `cards/backend-api/backend-api-mvp-slice.md`
- `cards/data/lightweight-data-storage-lifecycle.md`
- `cards/ux/task-flow-ui-state-inventory.md`
- `cards/brainstorm/idea-collision.md`
- `cards/acceptance/smoke-test-shortest-path.md`

## Intake Rule For Community Sources

```text
raw post
-> extract practice / pain / phrase / example
-> remove private details
-> tag domain
-> mark L4
-> cross-check against L1/L2/L3
-> upgrade only if repeated or supported
```

Do not crawl or batch-import community sources from this vault alone. Store reviewed notes only.
