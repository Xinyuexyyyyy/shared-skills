# Reusable Harness Library Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use a reviewed implementation workflow and verify every task before committing.

**Goal:** Build a runtime-neutral harness library, a LiveWithOpenCove-compatible example workspace, and a deterministic layout validator.

**Architecture:** Keep editable rules under `harness/components/`, bundle recipes under `harness/assemblies/`, generated release content under `harness/bundles/`, and runtime discovery in thin adapter files. Private memory remains outside the harness boundary.

**Tech Stack:** Markdown, YAML, Bash, Git.

## Global Constraints

- All reusable harness content lives under `harness/`.
- No credentials, device-specific paths, private memory, or runtime configuration.
- Storage mirrors receive verified Git content only and do not become authority sources.
- The example must support Codex and Claude through separate thin adapters.

---

### Task 1: Define the management contract

**Files:**
- Create: `harness/README.md`
- Create: `harness/METHODOLOGY.md`
- Create: `harness/MANIFEST-SPEC.md`

**Verification:** Review every boundary and confirm that authority, bundles, adapters, private state, and storage mirrors have one owner each.

### Task 2: Build the core components, bundle, and example

**Files:**
- Create: `harness/components/**`
- Create: `harness/assemblies/core-workspace-v1.yaml`
- Create: `harness/bundles/core-workspace-v1/**`
- Create: `harness/examples/livewithopencove-workspace/**`

**Verification:** Compare the canonical bundle and the materialized example bundle byte for byte.

### Task 3: Add mechanical validation

**Files:**
- Create: `harness/scripts/validate-harness.sh`
- Create: `harness/tests/test-validate-harness.sh`
- Modify: `README.md`
- Modify: `ARCHITECTURE.md`

**Verification:** Run the materialization check, validator, regression test, and Git whitespace checks.

### Task 4: Runtime smoke and publish

**Status:** Pending explicit release stage.

**Verification:** Confirm clean Codex and Claude sessions load the same bundle contract, then compare the release commit and checksums with the storage mirror.
