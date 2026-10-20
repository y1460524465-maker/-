# Multi-Project Shared Rules Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Make every Windows project use one shared `01-agent-layer`, keep project work and state isolated, and store each Codex review in its own evidence directory.

**Architecture:** The current `E:\多agent协作\01-agent-layer` becomes the shared rule source. A project generator creates independent project roots whose `01-agent-layer` is an NTFS directory junction to that source, while `02-work-items` and `03-session-state` remain local and tracked. `workspace.py` discovers the active project from the working directory, and review evidence moves from flat `artifacts/` files into `reviews/<task>/round-N/`.

**Tech Stack:** Windows PowerShell, Python 3.12, `unittest`, Git.

**Spec:** `01-agent-layer/docs/superpowers/specs/2026-10-20-multi-project-shared-rules-design.md`

## Global Constraints

- Projects are used only on the current Windows computer.
- `01-agent-layer` content has exactly one physical source.
- Project A and Project B must not share `02-work-items` or `03-session-state`.
- The route name remains `review`; the context file becomes `contexts/codex-review.md`.
- Every Codex review is written to `02-work-items/{active,archived}/<item-id>/reviews/<task-id>/round-N/`.
- `artifacts/delegation/` remains the DeepSeek request/event/result store.
- Existing implementation and test code must not be modified.
- Existing review evidence is migrated, not discarded.

## Review Focus

- Running the shared script from a project working directory must never write to the shared repository root.
- A project junction must not be tracked by that project's Git repository.
- Missing or broken `01-agent-layer` links must fail clearly rather than silently using a stale copy.
- Two reviews of the same task must never overwrite each other.
- Existing historical review links must remain resolvable after migration.

---

### Task 1: Project root discovery and project metadata

**Files:**
- Modify: `01-agent-layer/scripts/workspace.py`
- Modify: `01-agent-layer/tests/test_workspace.py`
- Create: `.ai-workspace.json`

**Interfaces:**
- Produces: `discover_project_root(start: Path | None = None) -> Path`
- Produces: `load_project_config(root: Path) -> dict[str, object]`
- Produces: CLI `--root` remains available and overrides discovery.

- [x] Add failing tests for root discovery from a nested project directory, explicit `--root` precedence, and project metadata validation.
- [x] Run tests and confirm the new tests fail.
- [x] Implement upward discovery using `.ai-workspace.json` plus `02-work-items/WORK_INDEX.md` and `03-session-state`.
- [x] Add the repository-root metadata file with `mode: shared-kit`.
- [x] Run the workspace tests and confirm they pass.

### Task 2: Shared project generator

**Files:**
- Create: `01-agent-layer/scripts/New-AiProject.ps1`
- Create: `01-agent-layer/templates/project/**`
- Create: `01-agent-layer/githooks/pre-commit`
- Modify: `01-agent-layer/tests/test_workspace.py`
- Modify: `01-agent-layer/README.md`

**Interfaces:**
- PowerShell: `New-AiProject.ps1 -Path <project-root> [-SharedLayer <agent-layer>]`
- Produces: a project with a junction `01-agent-layer`, local `02-work-items`, local `03-session-state`, adapters, `.ai-workspace.json`, `.gitignore`, and Git hook configuration.

- [x] Add an integration test that creates two temporary projects and verifies both resolve the same guide while their item indices remain separate.
- [x] Run the test and confirm it fails because the generator is absent.
- [x] Implement the generator and templates; refuse non-empty existing targets.
- [x] Ignore `01-agent-layer/` in each project and configure the shared hook path.
- [x] Run the integration test and confirm both projects validate.

### Task 3: Thin guide and Codex review context rename

**Files:**
- Modify: `01-agent-layer/AGENT_GUIDE.md`
- Move: `01-agent-layer/contexts/review.md` to `01-agent-layer/contexts/codex-review.md`
- Modify: `01-agent-layer/router/context-router.md`
- Modify: `01-agent-layer/scripts/workspace.py`
- Modify: `01-agent-layer/tests/test_workspace.py`
- Modify: documentation references

**Interfaces:**
- `--mode review` continues to select the Codex review context.
- The selected path is `01-agent-layer/contexts/codex-review.md`.

- [x] Add a failing test asserting the review mode path.
- [x] Run the test and confirm the old path fails.
- [x] Rename the context and update all operational references.
- [x] Rewrite `AGENT_GUIDE.md` as a thin authoritative entry that points to one owner per detailed rule set.
- [x] Run the workspace tests and confirm they pass.

### Task 4: Per-review evidence directories

**Files:**
- Modify: `01-agent-layer/scripts/workspace.py`
- Modify: `01-agent-layer/tests/test_workspace.py`
- Create: `01-agent-layer/templates/work-item/work/reviews/README.md`
- Create: `01-agent-layer/templates/review/review.md`
- Modify: `01-agent-layer/core/state-contract.md`
- Modify: `01-agent-layer/contexts/codex-review.md`
- Modify: `01-agent-layer/contexts/sync.md`

**Interfaces:**
- Work item layout gains `reviews/`.
- Review evidence layout is `reviews/<task-id>/round-<n>/review.md`.
- Raw evidence files are siblings named `diff.patch` and `test-output.txt`.

- [x] Add failing tests for required `reviews/` creation and validation.
- [x] Run the tests and confirm they fail.
- [x] Add the template directory and validator requirement.
- [x] Document the fixed review package layout and link-only behavior in STATUS/handoff.
- [x] Run the workspace tests and confirm they pass.

### Task 5: Migrate existing review evidence and references

**Files:**
- Migrate: `02-work-items/active/2026-10-19-go-ttl-cache/artifacts/review-task-*.md`
- Migrate: corresponding `task-*-test.txt` and preliminary test outputs
- Modify: current project `STATUS.md`, `handoff.md`, summaries, and indexes containing old review paths
- Create: `reviews/README.md` for every existing item

**Interfaces:**
- Historical review conclusions remain readable.
- New paths resolve from the repository root.

- [x] Create the review skeleton for all active and archived items.
- [x] Move each existing review and its raw output into its task/round package.
- [x] Update every live reference to the new paths.
- [x] Verify no old operational review paths remain.

### Task 6: Full verification

**Files:**
- No new files.

- [x] Run `python 01-agent-layer/scripts/workspace.py validate`.
- [x] Run `python -m unittest discover -s 01-agent-layer/tests -v`.
- [x] Create two temporary projects and verify shared rules plus isolated indexes.
- [x] Run the pre-commit validation path.
- [x] Inspect Git status and report unresolved concurrent changes.
