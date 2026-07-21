# Stage 2 mission brief — write the implementation plan for the der auto-research loop (for GPT 5.6 Sol Pro)

You are a principal engineer writing a **comprehensive implementation plan** from an approved architecture. You are not implementing anything and you are not redesigning anything — Stage 1 is approved. Your output is the plan another agent executes.

Announce at start: "I'm writing the Stage 2 implementation plan from the approved draft_v4 architecture."

## Who will execute your plan

Assume the implementing engineer/agent has **zero context for this codebase and questionable taste**. They are a skilled developer, but they know almost nothing about the toolset (Pier, AHE, Qwen Code, DeepSWE, dotenvx) or the problem domain (agent-harness evaluation loops), and they don't know good test design very well. Document everything they need: which files to touch for each task, the actual code, the tests, the docs to check, the exact commands, and how to verify. They see one task at a time and may read tasks out of order.

## Deliverable

**ONE markdown file, offered to the owner as a downloadable file**, named:

```
2026-07-XX-der-auto-research-loop-stage2.md     (date at generation)
```

It will be committed to `research-plan/plans/` in the repo and executed task-by-task. Everything must be in this single file — no companion documents.

## Setup — read before writing anything

Clone the repo:

```
git clone https://github.com/keyclaw6/-der.git
```

Reading order:
1. `research-plan/draft_v4.md` — **THE SPEC. Authoritative.** Decisions D1–D12, build order §4 (milestones 0–8), verification list §8 (V1–V10), disposition §9.
2. `research-plan/context.md` — project constraints and source-verified facts.
3. `research-plan/reviews/round4_solpro.md` and `round5_sentry.md` — the rationale behind v4 and the source-verified claims (Pier flags, AHE internals, archive mechanics) you can rely on.
4. `VISION.md` — the North Star (context only; the spec governs).

Primary sources — verify every signature, flag, path, and format against source **before** writing it into a step; never from memory:
- AHE: https://github.com/china-qijizhifeng/agentic-harness-engineering (`evolve.py`, `configs/base.yaml`, `agents/`, the bundled ADB `_source`)
- Pier: https://github.com/datacurve-ai/pier — **pin `datacurve-pier==0.3.0`** (`src/pier/cli/jobs.py` for the CLI surface; agent base class; environments)
- DeepSWE v1.1: https://github.com/datacurve-ai/deep-swe (task format, `pre_artifacts.sh`, verifier layout)
- Qwen Code: https://github.com/QwenLM/qwen-code + https://qwenlm.github.io/qwen-code-docs/ (standalone `--archive` install, project config paths, headless flags, session JSONL)

## Global constraints (copy these verbatim into the plan's Global Constraints section)

- DeepSeek v4 pro is the pinned rollout model, always; trial containers hold no provider key; all rollout traffic goes through the host pinning proxy, which injects the key, hard-pins the model, enforces RunBudget, and logs observed models.
- `datacurve-pier==0.3.0` is the sole scored evaluator; DeepSWE v1.1 (pinned repo revision) is the primary suite; terminal-bench is unscored smoke only.
- One evaluator seam: `EvalRunner.run(EvalSpec) -> EvalResult`; both doors (owner CLI, AHE optimizer) call it synchronously; one finalizer writes scorecard + lifecycle record + README block atomically. Fail closed on missing/incomplete result paths — no recovery by directory recency, anywhere.
- Every AHE modification lands in `PATCHES.md` with rationale; expected patch set: harbor command construction → EvalRunner; reward-text parsing → EvalResult; delete recency recovery; all-k task attribution → per-task pass fractions.
- `harness/` is a runtime-shaped Qwen project (QWEN.md, `.qwen/settings.json`, `.qwen/skills/`); staging is a transparent copy/overlay; overlay-injected keys win; the evolvable namespace must not set request-shaping fields (model, endpoint, keys, temperature, top_p, max_tokens) or host-executable configuration (hooks, MCP server commands) — those are owner-only at V1.
- Identity: source commit + git tree OID of `harness/` + runtime-manifest digest. Scorecards (`scorecard.json`) are immutable once written. One lifecycle record per experiment (`experiments/EXP-####-slug.md`, machine-readable front matter, created before execution). The current baseline is derived (most recent adopted scorecard whose tree OID matches `main:harness`) — no baseline pointer file.
- Gates: `der experiment adopt` refuses when `main:harness` moved past the experiment's baseline tree OID (offer `--rebase-and-reeval`) and renders executable-key diffs under a top-most "EXECUTES ON YOUR MACHINE" section; daily sync refuses an unevaluated `main:harness` tree (`--force` escape); the unattended loop never writes to `harness/`.
- Experiments: preregistered contract (one primary metric, minimum effect, guardrails, falsifier, suite version, k, RunBudget) before execution; promotion judged on the confirmation set; validity taxonomy: agent/context timeout = failed, provider/network/infra/malformed verifier = invalid, never imputed; comparability only within same suite version + same k, CONFOUNDED flag on runtime-manifest mismatch.
- Suites: frozen membership per version; development (~16) / confirmation (~8, disjoint, aggregate-only publication, excluded from ADB views and critic evidence) / spine (4–6, reporting-only); pairwise-disjointness test in preflight + CI.
- Publication: one generated README block (hero progression chart of adopted-baseline macro pass@1, per-adoption annotations, series break + bridge points at suite-version changes, full experiment ledger including rejected/inconclusive/invalid, resource strips). No DASHBOARD.md, no second chart, no badges, no hand-maintained tables.
- Model roles: ADB + Evolve Agent pinned DeepSeek at V1; premium critic = owner-triggered local `codex exec` (GPT-5.6 Sol, subscription login, read-only sandbox, schema-constrained output, full provenance recording); never in the measured path; never unattended; no OpenAI-compatible shim over subscription credentials.
- Ops: Python ≥ 3.13 + uv; systemd units (evolve service, watchdog with `COST_CEILING_REACHED` flag + `ExecStartPre` gate, pinning proxy); one process lock; dedicated worktree for autonomous runs; provider-side prepaid cap is the hard wall; overlay defaults `max_iterations: 10`, finite timeouts, best_of_n off, explore off; secret scrub before any commit of artifacts; MIT repo — ADB partial-open disclosure stands.
- One-person operation, self-hosted single server, ~$300–1,500/month ceiling.

## Plan structure requirements

**Phases = the spec's build order.** Milestones 0–8 from draft_v4 §4 are your phases, in that order. Each phase must end with working, independently testable software; milestone 5 (runtime-shaped harness + hand-authored A/B end to end) is the owner-value gate. If you believe a phase should be split or reordered, say so in a short preamble note — but the scoring spine (0→5) order is fixed.

**File structure first.** Before defining tasks, map every file the plan creates or modifies and its single responsibility (the `research/der/` package layout, the DerQwenAgent module, schemas, CLI entry points, systemd units, templates, fixtures, PATCHES.md entries). Prefer small focused files; split by responsibility, not by technical layer. This map locks the decomposition — every task references it.

**Task right-sizing.** A task is the smallest unit that carries its own test cycle and is worth a fresh reviewer's gate. Fold setup/configuration/scaffolding/docs into the task whose deliverable needs them; split only where a reviewer could reject one task while approving its neighbor. Each task ends with an independently testable deliverable.

**Bite-sized steps.** Each step is one action (2–5 minutes): write the failing test → run it to see it fail (exact command, expected failure text) → minimal implementation → run to pass → commit (exact `git add` paths + commit message). Checkbox (`- [ ]`) syntax on every step.

**TDD where a unit boundary exists.** The normalizer (Pier artifacts → scorecard), the EvalSpec→Pier-flag translation, the staging-overlay merge policy (request-shaping + executable-key rejection), tree-OID/runtime-manifest computation, lifecycle-record front-matter parsing and status transitions, the derived-baseline resolver, the comparability/CONFOUNDED check, and the README generator are all unit-testable with committed golden fixtures — write real test code for them in the plan. Integration/live steps (Pier runs, proxy routing, archive install) are acceptance steps: exact command + expected observable output.

**Discovery gates — the one adaptation you must make.** The spec marks some facts as verify-at-build (draft_v4 §8, V1–V10: Pier's per-trial directory layout, `reward.json`/`ctrf.json` field shapes, ATIF v1.7 usage fields, container→host proxy routing, archive-in-container install, the ADB parser patch, induced-fault classification, evolve.py patch minimality, DeepSeek balance endpoint, server capacity). For each: write an explicit **discovery task** that runs a real probe, records the discovered value to `research-plan/pins/<name>.md` (exact command output pasted), and **STOPs the plan if the observation contradicts the spec's assumption** (escalate to the owner; do not improvise architecture). Downstream tasks reference the recorded pin file — they never invent the value. This is how "no placeholders" coexists with genuine unknowns: a placeholder is forbidden; a discovery step with a recorded output is the mechanism that replaces it.

**Plan document header** (must be the first thing in the file):

```markdown
# der auto-research loop — Stage 2 Implementation Plan

> **For agentic workers:** execute this plan task-by-task, one task per session where possible. Steps use checkbox (`- [ ]`) syntax for tracking. Do not start a task while a prior task's STOP-gate is unresolved. Work on a dedicated branch (Task 0 creates it).

**Goal:** [one sentence]

**Architecture:** [2–3 sentences — from draft_v4 §1]

**Tech Stack:** [exact: Python ≥3.13, uv, datacurve-pier==0.3.0, DeepSWE v1.1 @ <revision>, Qwen Code <version> standalone archive, Docker, systemd, dotenvx]

## Global Constraints
[the section above, verbatim]
```

**Task structure** (every task):

```markdown
### Task N: [Component name]

**Files:**
- Create: `exact/path/file.py`
- Modify: `exact/path/existing.py:<line-range>`
- Test: `tests/exact/path/test_file.py`

**Interfaces:**
- Consumes: [exact signatures from earlier tasks]
- Produces: [exact function names, parameter and return types later tasks rely on]

- [ ] **Step 1: ...** [with the actual code/command/expected output]
...
- [ ] **Step k: Commit** [exact git command + message]
```

## No placeholders — plan failures, never write them

- "TBD", "TODO", "implement later", "fill in details"
- "Add appropriate error handling" / "add validation" / "handle edge cases"
- "Write tests for the above" without the actual test code
- "Similar to Task N" — repeat the code; the implementer may read tasks out of order
- Steps that describe what to do without showing how (code steps require code blocks)
- References to types, functions, or flags not defined in any task and not verified against the primary sources
- Invented Pier/DeepSWE/Qwen specifics where the spec marks a discovery gate — use the pin-file mechanism instead

## What the plan must NOT do

- Redesign the architecture. Stage 1 is approved. If a discovery task falsifies a spec assumption, the plan's prescribed behavior is: stop, record, escalate to the owner with the evidence — not improvise.
- Invent scope: no E2B/Modal execution, no multi-tenancy, no extra dashboards, no parallel-experiment machinery, no premium models in the unattended path. Parked items stay parked.
- Weaken any gate "for now": fail-closed, keyless containers, preregistration-before-execution, and the adopt/sync refusals are not negotiable conveniences.

## Self-review (run it yourself before delivering; fix inline)

1. **Spec coverage:** walk draft_v4 D1–D12, §4 milestones 0–8, and §8 V1–V10 — point to the task implementing each. Every decision, every milestone, every verification item must map to at least one task. List and fix any gap.
2. **Placeholder scan:** search your plan for every red-flag pattern above. Fix them.
3. **Type consistency:** signatures, file paths, CLI flags, schema field names used in later tasks must match their definitions in earlier tasks exactly.
4. **Discovery-gate integrity:** every ▽/V-item has a discovery task with a STOP-gate and a pin file; no downstream step hardcodes a value a discovery task is supposed to produce.
5. **Commit hygiene:** every task ends in a commit; messages are present and specific.

Then deliver the single markdown file as a **downloadable file**. DRY. YAGNI. TDD. Frequent commits.
