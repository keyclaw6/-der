# der auto-research loop — Stage 2 Implementation Plan

> **For agentic workers:** execute this plan task-by-task, one task per session where possible. Steps use checkbox (`- [ ]`) syntax for tracking. Do not start a task while a prior task's STOP-gate is unresolved. Work on a dedicated branch (Task 0 creates it).

**Goal:** Build the approved, fail-closed der auto-research loop so one owner can evaluate, compare, adopt, publish, and safely operate Qwen harness experiments through a single Pier-backed evidence path.

**Architecture:** Both the owner CLI and vendored AHE call the same synchronous `EvalRunner.run(EvalSpec) -> EvalResult` seam, and one finalizer atomically turns the exact evaluator result path into immutable evidence, lifecycle state, and the generated README block. Qwen runs from a runtime-shaped `harness/` staged into isolated DeepSWE containers, while a host pinning proxy supplies the provider credential, hard-pins DeepSeek v4 pro, enforces the shared `RunBudget`, and records observed models. Experiments are preregistered lifecycle records, baselines are derived from adopted scorecards and Git tree identity, and the unattended loop is constrained to a dedicated worktree and never writes directly to `harness/`.

**Tech Stack:** Python ≥3.13, uv, datacurve-pier==0.3.0, DeepSWE v1.1 @ 8cae5984d5dd0ee37445beff0e928dc10c331116, Qwen Code v0.20.0 standalone archive, Docker, systemd, dotenvx

## Global Constraints

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

## Phase-order note

Milestones 0–8 below are the approved build order and are not reordered. Tasks inside a milestone are split only at reviewable test boundaries. The scoring spine through Milestone 5 remains strictly 0 → 1 → 2 → 3 → 4 → 5; Milestone 5 is the owner-value gate. An AHE optimizer iteration is treated as one der experiment: it gets one preregistered lifecycle record and one immutable scorecard. A longer systemd invocation may carry a campaign identifier for operational resume, but that identifier is not a second experiment lifecycle.

## Source locks and reading rule

Before touching code in any task, read the task's named files and the source rows it cites. Source-derived flags, signatures, paths, and formats are locked to these revisions; a worker must not substitute a newer revision while executing this plan.

| Source | Locked revision | Required files or documentation | Why it is authoritative here |
|---|---|---|---|
| Approved architecture | repository file `research-plan/draft_v4.md` | Decisions D1–D12, §4, §8, §9 | Governs all design choices and phase order. |
| Project constraints | repository file `research-plan/context.md` | entire file | Governs scope, cost, operating model, and source-verified context. |
| Architecture rationale | repository files `research-plan/reviews/round4_solpro.md`, `research-plan/reviews/round5_sentry.md` | entire files | Explains why v4 chose the approved seams and gates. |
| North Star | repository file `VISION.md` | entire file | Context only; it never overrides `draft_v4.md`. |
| Pier | `datacurve-ai/pier` tag `v0.3.0`, commit `e69a20e4e0ac073ec71fde0274bab3d9f40bac87` | `src/pier/cli/jobs.py`, `src/pier/agents/`, `src/pier/environments/`, `src/pier/models/trial/` | Sole scored evaluator and custom-agent contract. |
| DeepSWE | `datacurve-ai/deep-swe` tag `v1.1`, commit `8cae5984d5dd0ee37445beff0e928dc10c331116` | task directories, `task.toml`, `pre_artifacts.sh`, `tests/`, verifier entry points | Primary task suite and task/verifier format. |
| AHE | `china-qijizhifeng/agentic-harness-engineering` commit `faf44bc4aea57413c520bc5711c6ebf628e0da1e` | `evolve.py`, `configs/base.yaml`, `agents/`, bundled ADB `_source` | Vendored optimizer and the four approved patch seams. |
| Qwen Code | `QwenLM/qwen-code` tag `v0.20.0`, commit `92fda5603e84ef62a1b29bf6faf4f6a8124a2bf7` | standalone installer, CLI argument source, session/stream serializers | Rollout CLI behavior and archive/runtime contract. |
| Qwen Code docs | versioned pages matching v0.20.0 | installation, configuration, headless mode, skills, checkpointing/session docs | Human-readable explanation of the same locked CLI. |

The verified Pier CLI surface used by this plan is `pier run --path ... --include-task-name ... --n-attempts ... --n-concurrent ... --max-retries 0 --env docker --agent-import-path ... --model ... --agent-kwarg ... --jobs-dir ... --job-name ... --yes`. The command emits exactly one `Results written to <path>` line on success; `EvalRunner` captures that path and never searches by modification time. The verified custom-agent class derives from Pier's `BaseAgent`, advertises `SUPPORTS_ATIF`, and supplies `name()`, `version()`, async `setup(...)`, and async `run(...)`.

## Execution conventions

1. Run every command from the repository root unless a step supplies a different `cd`.
2. Use `uv run` for Python entry points and tests. Do not activate a mutable global virtual environment.
3. A discovery script exits `0` only after writing a `status: passed` pin with its exact command transcript. Exit `78` means STOP: commit the blocked pin, do not run downstream tasks, and escalate the evidence to the owner. Any other nonzero status is an ordinary task failure to repair before committing.
4. Live commands that spend provider money require `DER_LIVE=1`, a run token issued by the local proxy, and an approved lifecycle record. Tests must use fixtures and in-process fakes; they do not make provider calls.
5. Use UTC RFC 3339 timestamps in data files. Human prose may show local time separately.
6. Generated files are regenerated and compared byte-for-byte in CI. A generated file is never hand-edited.
7. Every scorecard write uses exclusive creation. A rerun gets a new `run_id`; it never overwrites an existing scorecard.
8. Every task's final test command must pass before its commit step. A worker who cannot produce the stated observable result stops that task instead of weakening the assertion.
9. If `ruff check` reports only import-sorting diagnostics (`I001`) on code transcribed from this plan, run `uv run ruff check --fix <same paths>` once and rerun the check; that is transcription repair, not assertion weakening. Any other diagnostic is a real failure to fix by hand.

## Locked file structure and single responsibilities

This map is the decomposition contract. Do not add a second file for a listed responsibility and do not combine unrelated responsibilities into one module. A task may add a narrowly scoped fixture under an existing fixture directory when the exact filename is derived from a discovered run identifier.

### Repository root and build files

| Path | Single responsibility |
|---|---|
| `pyproject.toml` | Python package metadata, exact Pier pin, application dependencies, developer groups, CLI entry point, pytest/ruff/mypy configuration. |
| `uv.lock` | Fully resolved Python dependency lock generated by `uv lock`; never edited manually. |
| `package.json` | Pins `@dotenvx/dotenvx` for owner-side secret injection commands; contains no provider secret. |
| `package-lock.json` | Exact dotenvx dependency lock generated by `npm install --package-lock-only`. |
| `.gitignore` | Excludes secrets, live cache, run worktrees, generated temporary files, and Qwen session state while retaining canonical sanitized evidence. |
| `.github/workflows/check.yml` | CI entry point for lock verification, static checks, unit/integration fixture tests, schema checks, suite disjointness, and generated-file cleanliness. |
| `scripts/check.py` | One local/CI orchestrator that executes the same check sequence and stops on the first failure. |
| `README.md` | Human introduction plus the sole generated publication block delimited by `<!-- DER:START -->` and `<!-- DER:END -->`. |

### Runtime-shaped harness

| Path | Single responsibility |
|---|---|
| `harness/QWEN.md` | Evolvable project instruction surface read by Qwen Code. |
| `harness/.qwen/settings.json` | Evolvable project settings that pass the deny policy; starts as `{}`. |
| `harness/.qwen/skills/der-engineering/SKILL.md` | First managed Qwen skill and a concrete safe mutation target for the hand-authored A/B. |

### Vendored optimizer and research configuration

| Path | Single responsibility |
|---|---|
| `research/UPSTREAM.md` | Records each vendored upstream URL, immutable revision, import command, and update procedure. |
| `research/PATCHES.md` | Records every local AHE/ADB patch with source lines, rationale, test, and upstream-diff command. |
| `research/evolve.py` | Vendored AHE driver with only the approved evaluator/result/resume/attribution adaptations. |
| `research/configs/base.yaml` | Vendored AHE base configuration retained for diffability. |
| `research/configs/ahe-der-v1.yaml` | Owner overlay: finite iteration/time limits, DeepSeek roles, `best_of_n: false`, `explore: false`, der adapter settings. |
| `research/agents/` | Vendored AHE agents, including the bundled ADB `_source`; modified only where `PATCHES.md` records it. |
| `research/config/runtime-policy.toml` | Owner-only immutable model, proxy, timeout, and Qwen execution policy identifiers. |
| `research/config/qwen-live-state-v0.20.0.json` | Exhaustive owner-reviewed list of Qwen files copied between managed `harness/` and the out-of-repo daily installation. |
| `research/templates/experiment.md` | Canonical lifecycle-record body and front-matter example generated through the contract model. |

### JSON Schemas

| Path | Single responsibility |
|---|---|
| `research/schemas/eval-spec.schema.json` | Generated schema for `EvalSpec`. |
| `research/schemas/eval-result.schema.json` | Generated schema for `EvalResult`. |
| `research/schemas/scorecard.schema.json` | Generated immutable scorecard schema. |
| `research/schemas/experiment-frontmatter.schema.json` | Generated lifecycle front-matter schema. |
| `research/schemas/suite.schema.json` | Generated suite manifest schema. |
| `research/schemas/critic-proposal.schema.json` | Owner-triggered premium critic output contract. |

### Suite and experiment state

| Path | Single responsibility |
|---|---|
| `research/suites/candidates-v1.toml` | V7-audited DeepSWE candidates and calibration observations. |
| `research/suites/suite-v1.toml` | Frozen, pairwise-disjoint development/confirmation/spine membership and reporting k. |
| `research/suites/exclusions-v1.md` | Auditable reasons candidate tasks were excluded during calibration. |
| `experiments/` | One lifecycle Markdown record per `EXP-####-slug`; no pointer files. |
| `research/runs/` | Canonical run directories containing immutable scorecards and sanitized evidence manifests. |

### `research/der/` package

| Path | Single responsibility |
|---|---|
| `research/__init__.py` | Makes the vendored research tree importable without side effects. |
| `research/der/__init__.py` | Package version only. |
| `research/der/cli.py` | Typer command tree; delegates every operation to a focused service. |
| `research/der/errors.py` | Typed domain errors and stable CLI exit codes, including discovery STOP `78`. |
| `research/der/pins.py` | Parses, validates, and queries discovery pin Markdown front matter. |
| `research/der/contracts/base.py` | Strict/frozen Pydantic base and canonical JSON helpers. |
| `research/der/contracts/eval.py` | `RunBudget`, identity, `EvalSpec`, outcome, resource, and `EvalResult` models. |
| `research/der/contracts/experiment.py` | Preregistered experiment contract, lifecycle status, and transition rules. |
| `research/der/contracts/scorecard.py` | Immutable scorecard and promotion-decision models. |
| `research/der/contracts/suite.py` | Suite manifest, member, and class models. |
| `research/der/evaluation/pier_command.py` | Pure `EvalSpec` + pins → Pier argv translation. |
| `research/der/evaluation/process.py` | Synchronous subprocess protocol and real implementation with bounded timeout/termination. |
| `research/der/evaluation/runner.py` | Sole synchronous `EvalRunner.run(EvalSpec) -> EvalResult` orchestration seam. |
| `research/der/evaluation/normalizer.py` | Exact pinned Pier artifacts → typed `EvalResult`; no directory search. |
| `research/der/evaluation/classification.py` | Exhaustive evaluator/provider/Qwen/verifier condition → validity taxonomy. |
| `research/der/evaluation/artifact_manifest.py` | Secret-scrubbed canonical artifact digest manifest. |
| `research/der/evaluation/scorecard_writer.py` | Exclusive immutable scorecard creation and read-back verification. |
| `research/der/evaluation/finalizer.py` | Atomic scorecard + lifecycle + README transaction with rollback and commit marker last. |
| `research/der/agents/qwen.py` | Pier `DerQwenAgent` implementation and container setup/run lifecycle. |
| `research/der/agents/qwen_stream.py` | Strict Qwen stream/session JSONL parser and one-session selection by session ID. |
| `research/der/agents/qwen_atif.py` | Converts canonical Qwen events to honest ATIF v1.7 plus Pier `AgentContext` totals. |
| `research/der/harness/policy.py` | Enumerated request-shaping and host-executable deny policy. |
| `research/der/harness/stage.py` | Transparent managed copy plus immutable owner overlay and staged-file manifest. |
| `research/der/harness/identity.py` | Git tree OID and runtime-manifest digest computation. |
| `research/der/harness/diff.py` | Semantic settings diff, with executable changes rendered first. |
| `research/der/harness/live_state.py` | Parses the owner-reviewed daily Qwen state list. |
| `research/der/harness/sync.py` | Managed ↔ daily state copy with unevaluated-tree refusal and explicit force record. |
| `research/der/proxy/app.py` | OpenAI-compatible HTTP surface, health endpoint, request routing, and response streaming. |
| `research/der/proxy/policy.py` | Hard model replacement/rejection and provider request sanitation. |
| `research/der/proxy/budget.py` | Atomic per-run RunBudget reservation, reconciliation, and ceiling decisions. |
| `research/der/proxy/registry.py` | Short-lived hashed run-token registration and lookup; never stores plaintext tokens. |
| `research/der/proxy/observations.py` | Append-only model/resource observation JSONL with fsync. |
| `research/der/experiments/records.py` | Markdown/front-matter parsing, creation, transition, and atomic rewrite. |
| `research/der/experiments/baseline.py` | Derives the current baseline from adopted scorecards matching `main:harness`. |
| `research/der/experiments/comparability.py` | Same-suite/same-k rule and runtime-manifest `CONFOUNDED` result. |
| `research/der/experiments/adopt.py` | Baseline-movement refusal, confirmation decision, executable acknowledgment, exact harness replacement. |
| `research/der/experiments/metrics.py` | Per-task pass fractions, macro pass@1, guardrail evaluation, and promotion decision. |
| `research/der/suites/manifest.py` | TOML load/write, frozen-membership checks, and DeepSWE revision association. |
| `research/der/suites/disjoint.py` | Pairwise class/version disjointness and confirmation-leak assertions. |
| `research/der/suites/calibrate.py` | Candidate observation aggregation and deterministic suite-v1 selection report. |
| `research/der/publication/readme.py` | Deterministic single-block README renderer and marker replacement. |
| `research/der/publication/svg.py` | Inline accessible SVG hero progression chart with version breaks/bridge points. |
| `research/der/integrations/ahe.py` | Tiny adapter called by vendored `evolve.py`; creates experiment records and invokes `EvalRunner`. |
| `research/der/integrations/adb.py` | Canonical artifact → ephemeral NexAU/ADB view, excluding confirmation evidence. |
| `research/der/integrations/critic.py` | Fixed evidence bundle, local `codex exec`, schema validation, provenance, and proposed-record creation. |
| `research/der/ops/lock.py` | One-process advisory lock and owner-readable lock metadata. |
| `research/der/ops/doctor.py` | Preflight for pins, tools, cache, suite disjointness, worktree, proxy, budget, and secrets. |
| `research/der/ops/watchdog.py` | Balance/cost meter, `COST_CEILING_REACHED`, and stop/notify decision. |
| `research/der/ops/janitor.py` | Evidence-retention policy that never deletes scorecards/lifecycle records. |
| `research/der/ops/notify.py` | Provider-neutral local notification shim including cost and run identity. |
| `research/der/ops/secret_scrub.py` | Byte/content/name scanning before evidence is committed. |
| `research/der/util/atomic.py` | fsync + atomic replace helpers and reversible multi-file transaction staging. |
| `research/der/util/git.py` | Checked Git commands, tree OIDs, worktree identity, and exact-replace operations. |
| `research/der/util/hashing.py` | SHA-256 and canonical-tree digest helpers. |
| `research/der/util/jsonio.py` | Strict JSON/JSONL read/write with useful source locations. |
| `research/der/util/time.py` | Injectable UTC clock used by records, scorecards, tests, and observations. |

### Discovery probes and pins

| Probe | Pin output | Single responsibility |
|---|---|---|
| `scripts/discover_v1_pier_artifacts.py` | `research-plan/pins/v1-pier-artifact-layout.md` | Real Pier layout, `reward.json`, `ctrf.json`, ATIF usage pointer/schema probe. |
| `scripts/discover_v2_acceptance_chain.py` | `research-plan/pins/v2-acceptance-chain.md` | Eight-point path, including the actual container-to-host proxy route and allowlist values. |
| `scripts/discover_v3_qwen_archive.py` | `research-plan/pins/v3-qwen-archive-install.md` | Qwen standalone archive/checksum/offline install command and binary path in a real task image. |
| `scripts/discover_v4_ahe_attribution.py` | `research-plan/pins/v4-ahe-attribution-seam.md` | AHE all-k producers/consumers and exact minimal patch span. |
| `scripts/discover_v5_faults.py` | `research-plan/pins/v5-fault-classification.md` | Real induced provider/network/verifier/timeout evidence mapped to the approved taxonomy. |
| `scripts/discover_v6_adb_parser.py` | `research-plan/pins/v6-adb-runtime-parser.md` | Runtime `_source` installation, parser path, honest-provider synthetic trace acceptance. |
| `scripts/discover_v7_deepswe.py` | `research-plan/pins/v7-deepswe-revisions.md` | DeepSWE pin mechanism, candidate task IDs, checksums, and verifier audit facts. |
| `scripts/discover_v8_adb_license.py` | `research-plan/pins/v8-adb-license.md` | Whether the bundled `_source` can be patched and redistributed in this MIT repository. |
| `scripts/discover_v9_balance.py` | `research-plan/pins/v9-deepseek-balance.md` | Account-specific DeepSeek balance endpoint request and response fields. |
| `scripts/discover_v10_capacity.py` | `research-plan/pins/v10-server-capacity.md` | Host capacity, concurrency 4–8 probes, rate limits, and cache completeness. |
| `research-plan/pins/external-identities.md` | same file | Source-lock transcript and archive/cache digests used by identity. |

### Tests and committed fixtures

Tests mirror the package under `tests/`. The following fixture roots are stable contracts: `tests/fixtures/pier/v0.3.0/{pass,fail,invalid,malformed}/`, `tests/fixtures/qwen/{success,turn-limit,wall-limit,tool-limit,malformed,multi-session}.jsonl`, `tests/fixtures/experiments/`, `tests/fixtures/suites/`, `tests/fixtures/ahe/`, `tests/fixtures/adb/`, and `tests/golden/{scorecards,readme,staging,adoption-diffs}/`. Discovery tasks populate Pier/ADB fixtures only from sanitized live outputs; fixture tests fail if their recorded pin schema digest changes.

### Operations files

| Path | Single responsibility |
|---|---|
| `ops/systemd/der-pinning-proxy.service` | Long-running key-injecting proxy unit. |
| `ops/systemd/der-evolve.service` | Dedicated-worktree unattended AHE/der loop with lock and ceiling preflight. |
| `ops/systemd/der-watchdog.service` | One-shot cost/balance/cache/watchdog invocation. |
| `ops/systemd/der-watchdog.timer` | Watchdog schedule. |
| `ops/systemd/der-notify@.service` | Failure/ceiling notification shim invocation. |
| `ops/systemd/der.env.example` | Non-secret variable names and owner paths; real secrets remain in dotenvx-encrypted/out-of-repo state. |
| `ops/install-systemd.sh` | Validates and installs units, then reloads systemd. |
| `ops/runbook.md` | Exact owner commands for bootstrap, start, stop, resume, ceiling, crash, adoption, sync, and evidence recovery. |

---
## File-map addendum before task decomposition

The schema export command needs one focused module that was not named in the first table: `research/der/contracts/schema_export.py` owns deterministic JSON Schema emission for the six files under `research/schemas/`. This is the only addendum; the file map is now locked.

# Phase 0 — Milestone 0: freeze external identities, schemas, and core contracts

Milestone exit: the repository installs reproducibly; every upstream revision is recorded from checked-out source; DeepSWE task/verifier structure is audited; all internal wire contracts have strict generated schemas; identity, lifecycle, suite, proxy-policy, and budget primitives pass fixture tests. No scored run is attempted in this phase.

### Task 0: Bootstrap the branch, locked toolchain, package, and pin reader

**Files:**
- Create: `pyproject.toml`
- Create: `package.json`
- Create: `.gitignore`
- Create: `research/__init__.py`
- Create: `research/der/__init__.py`
- Create: `research/der/errors.py`
- Create: `research/der/pins.py`
- Create: `research/der/cli.py`
- Create: `tests/test_package.py`
- Create: `tests/test_pins.py`
- Create: `tests/fixtures/pins/passed.md`
- Create: `tests/fixtures/pins/blocked.md`
- Generate: `uv.lock`
- Generate: `package-lock.json`

**Interfaces:**
- Consumes: the repository clone; Python ≥3.13; `uv`; Node/npm only for the owner-side dotenvx binary.
- Produces: `research.der.pins.load_pin(path: Path, expected_verification: str | None = None) -> PinDocument`, `PinDocument.require_passed() -> None`, CLI command `der pins assert VERIFICATION`, stable exit code `78` for a blocked discovery gate.

- [ ] **Step 1: Clone the approved repository and create the dedicated implementation branch.** Run exactly:

  ```bash
  git clone https://github.com/keyclaw6/-der.git der
  cd der
  git switch -c stage2/auto-research-loop
  test -f research-plan/draft_v4.md
  git status --short
  ```

  Expected output: `git status --short` prints nothing. If the branch already exists locally, use `git switch stage2/auto-research-loop`; do not create a differently named branch.

- [ ] **Step 2: Confirm the architecture inputs have not silently changed.** Run:

  ```bash
  sha256sum \
    research-plan/draft_v4.md \
    research-plan/context.md \
    research-plan/reviews/round4_solpro.md \
    research-plan/reviews/round5_sentry.md \
    VISION.md
  ```

  Paste this output into the Task 0 commit body. Do not make code changes if `draft_v4.md` is absent or does not identify itself as v4.

- [ ] **Step 3: Write the package and dependency manifests.** Create `pyproject.toml` with this complete content:

  ```toml
  [build-system]
  requires = ["hatchling>=1.27,<2"]
  build-backend = "hatchling.build"

  [project]
  name = "der"
  version = "0.1.0"
  description = "Fail-closed agent-harness evaluation and research loop"
  requires-python = ">=3.13"
  dependencies = [
    "datacurve-pier==0.3.0",
    "fastapi>=0.116,<1",
    "httpx>=0.28,<1",
    "pydantic>=2.11,<3",
    "pyyaml>=6.0.2,<7",
    "typer>=0.16,<1",
    "uvicorn>=0.35,<1",
  ]

  [project.scripts]
  der = "research.der.cli:app"

  [dependency-groups]
  dev = [
    "jsonschema>=4.25,<5",
    "mypy>=1.17,<2",
    "pytest>=8.4,<9",
    "pytest-cov>=6.2,<7",
    "pytest-timeout>=2.4,<3",
    "ruff>=0.12,<1",
  ]

  [tool.hatch.build.targets.wheel]
  packages = ["research/der"]

  [tool.pytest.ini_options]
  addopts = "-ra --strict-config --strict-markers"
  testpaths = ["tests"]
  markers = [
    "live: spends provider money or needs a real container/network",
    "integration: crosses a subprocess, filesystem transaction, or HTTP boundary",
  ]

  [tool.ruff]
  target-version = "py313"
  line-length = 100

  [tool.ruff.lint]
  select = ["E", "F", "I", "UP", "B", "SIM", "RUF"]

  [tool.mypy]
  python_version = "3.13"
  strict = true
  packages = ["research.der"]
  ```

  Create `package.json` with:

  ```json
  {
    "name": "der-owner-tools",
    "private": true,
    "engines": {"node": ">=22"},
    "devDependencies": {"@dotenvx/dotenvx": "^1.49.0"},
    "scripts": {
      "dotenvx": "dotenvx"
    }
  }
  ```

  The exact dotenvx transitive version is frozen by the generated `package-lock.json`; the provider key is never placed in either manifest.

- [ ] **Step 4: Write the ignore policy and package version.** Create `.gitignore` exactly as follows:

  ```gitignore
  .venv/
  .mypy_cache/
  .pytest_cache/
  .ruff_cache/
  __pycache__/
  *.py[cod]
  node_modules/
  .env
  .env.*
  !.env.example
  *.pem
  *.key
  *.age
  .der/
  research/cache/
  research/tmp/
  research/worktrees/
  research/runs/*/raw-secrets/
  research/critic/out/*.events.jsonl
  harness/.qwen/tmp/
  harness/.qwen/projects/
  harness/.qwen/history/
  harness/.qwen/memory/
  COST_CEILING_REACHED
  ```

  Create `research/__init__.py` as an empty file and `research/der/__init__.py` as:

  ```python
  """der implementation package."""

  __version__ = "0.1.0"
  ```

- [ ] **Step 5: Write the failing pin-reader tests and fixtures.** Create `tests/fixtures/pins/passed.md`:

  ```markdown
  ---
  verification: V3
  status: passed
  observed_at: 2026-07-21T12:00:00Z
  source_revision: 92fda5603e84ef62a1b29bf6faf4f6a8124a2bf7
  values:
    archive_sha256: 0123456789abcdef
    install_argv:
      - /cache/qwen-install.sh
      - --archive
      - /cache/qwen-code-v0.20.0.tar.gz
  ---
  # V3 Qwen archive probe

  ## Command transcript

  ```text
  qwen --version
  0.20.0
  ```
  ```

  Create `tests/fixtures/pins/blocked.md`:

  ```markdown
  ---
  verification: V2
  status: blocked
  observed_at: 2026-07-21T12:00:00Z
  source_revision: e69a20e4e0ac073ec71fde0274bab3d9f40bac87
  values: {}
  contradiction: container could not reach any allowlisted host route
  ---
  # V2 blocked probe
  ```

  Create `tests/test_pins.py`:

  ```python
  from pathlib import Path

  import pytest

  from research.der.errors import DiscoveryBlockedError, PinFormatError
  from research.der.pins import load_pin

  FIXTURES = Path("tests/fixtures/pins")


  def test_load_pin_exposes_typed_values() -> None:
      pin = load_pin(FIXTURES / "passed.md", expected_verification="V3")

      assert pin.verification == "V3"
      assert pin.status == "passed"
      assert pin.value("archive_sha256") == "0123456789abcdef"
      assert pin.value("install_argv.1") == "--archive"
      pin.require_passed()


  def test_blocked_pin_raises_stop_error() -> None:
      pin = load_pin(FIXTURES / "blocked.md", expected_verification="V2")

      with pytest.raises(
          DiscoveryBlockedError,
          match="V2 discovery is blocked: container could not reach",
      ):
          pin.require_passed()


  def test_wrong_verification_is_rejected() -> None:
      with pytest.raises(PinFormatError, match="expected V1, found V3"):
          load_pin(FIXTURES / "passed.md", expected_verification="V1")


  def test_missing_value_is_rejected_with_full_key() -> None:
      pin = load_pin(FIXTURES / "passed.md")

      with pytest.raises(PinFormatError, match="missing values.install_argv.9"):
          pin.value("install_argv.9")
  ```

  Create `tests/test_package.py`:

  ```python
  from typer.testing import CliRunner

  from research.der import __version__
  from research.der.cli import app


  def test_version_and_cli_boot() -> None:
      result = CliRunner().invoke(app, ["version"])

      assert __version__ == "0.1.0"
      assert result.exit_code == 0
      assert result.stdout == "der 0.1.0\n"
  ```

- [ ] **Step 6: Run the tests to observe the missing-module failure.** Run:

  ```bash
  uv lock
  uv sync --all-groups
  npm install --package-lock-only
  uv run pytest tests/test_package.py tests/test_pins.py -q
  ```

  Expected failure includes `ModuleNotFoundError: No module named 'research.der.errors'` or `research.der.pins`.

- [ ] **Step 7: Implement stable errors, the strict pin reader, and the initial CLI.** Create `research/der/errors.py`:

  ```python
  """Stable domain failures and process exit codes."""

  from __future__ import annotations


  class DerError(RuntimeError):
      """Base class for expected der failures."""

      exit_code = 1


  class PinFormatError(DerError):
      """A pin document is absent, malformed, or missing a required value."""

      exit_code = 2


  class DiscoveryBlockedError(DerError):
      """A real probe contradicted an approved architecture assumption."""

      exit_code = 78


  class PolicyViolationError(DerError):
      """Managed/evolvable content violates an owner-only policy."""

      exit_code = 3


  class IncompleteResultError(DerError):
      """The evaluator did not produce the one exact complete result path."""

      exit_code = 4


  class ImmutableArtifactError(DerError):
      """A caller attempted to overwrite immutable evidence."""

      exit_code = 5


  class ContractError(DerError):
      """A wire-contract invariant (spec, argv, schema) was violated."""

      exit_code = 6


  class EvaluationError(DerError):
      """The evaluator subprocess or its result protocol failed."""

      exit_code = 7


  class ProcessLockError(DerError):
      """Another der process holds the single evaluation lock."""

      exit_code = 8


  class UnevaluatedHarnessError(DerError):
      """`main:harness` has no adopted scorecard; sync refuses without --force."""

      exit_code = 9


  class NoEvaluatedBaselineError(DerError):
      """No adopted scorecard matches the current `main:harness` tree."""

      exit_code = 10
  ```

  Later tasks (16, 17, 23, 24) import `ContractError`, `EvaluationError`, `ProcessLockError`, `UnevaluatedHarnessError`, and `NoEvaluatedBaselineError` from this module; do not redefine them elsewhere.

  Create `research/der/pins.py`:

  ```python
  """Read discovery-gate Markdown documents with strict YAML front matter."""

  from __future__ import annotations

  from dataclasses import dataclass
  from pathlib import Path
  from typing import Any, Literal, cast

  import yaml

  from research.der.errors import DiscoveryBlockedError, PinFormatError

  PinStatus = Literal["passed", "blocked"]

  PIN_PATHS: dict[str, Path] = {
      "V1": Path("research-plan/pins/v1-pier-artifact-layout.md"),
      "V2": Path("research-plan/pins/v2-acceptance-chain.md"),
      "V3": Path("research-plan/pins/v3-qwen-archive-install.md"),
      "V4": Path("research-plan/pins/v4-ahe-attribution-seam.md"),
      "V5": Path("research-plan/pins/v5-fault-classification.md"),
      "V6": Path("research-plan/pins/v6-adb-runtime-parser.md"),
      "V7": Path("research-plan/pins/v7-deepswe-revisions.md"),
      "V8": Path("research-plan/pins/v8-adb-license.md"),
      "V9": Path("research-plan/pins/v9-deepseek-balance.md"),
      "V10": Path("research-plan/pins/v10-server-capacity.md"),
  }


  @dataclass(frozen=True, slots=True)
  class PinDocument:
      path: Path
      verification: str
      status: PinStatus
      observed_at: str
      source_revision: str
      values: dict[str, Any]
      contradiction: str | None
      body: str

      def require_passed(self) -> None:
          if self.status == "blocked":
              detail = self.contradiction or "the observed result contradicted the specification"
              raise DiscoveryBlockedError(
                  f"{self.verification} discovery is blocked: {detail}; "
                  f"see {self.path} and escalate to the owner"
              )

      def value(self, dotted_key: str) -> Any:
          current: Any = self.values
          traversed = "values"
          for part in dotted_key.split("."):
              traversed = f"{traversed}.{part}"
              try:
                  if isinstance(current, list):
                      current = current[int(part)]
                  elif isinstance(current, dict):
                      current = current[part]
                  else:
                      raise KeyError(part)
              except (KeyError, IndexError, ValueError) as exc:
                  raise PinFormatError(f"{self.path}: missing {traversed}") from exc
          return current


  def _split_front_matter(text: str, path: Path) -> tuple[dict[str, Any], str]:
      lines = text.splitlines()
      if not lines or lines[0] != "---":
          raise PinFormatError(f"{path}: first line must be ---")
      try:
          end = lines.index("---", 1)
      except ValueError as exc:
          raise PinFormatError(f"{path}: front matter has no closing ---") from exc
      raw = yaml.safe_load("\n".join(lines[1:end]))
      if not isinstance(raw, dict):
          raise PinFormatError(f"{path}: front matter must be a mapping")
      return cast(dict[str, Any], raw), "\n".join(lines[end + 1 :]) + "\n"


  def load_pin(path: Path, expected_verification: str | None = None) -> PinDocument:
      if not path.is_file():
          raise PinFormatError(f"pin does not exist: {path}")
      front, body = _split_front_matter(path.read_text(encoding="utf-8"), path)
      required = {"verification", "status", "observed_at", "source_revision", "values"}
      missing = sorted(required - front.keys())
      if missing:
          raise PinFormatError(f"{path}: missing front-matter keys {missing}")
      verification = front["verification"]
      status = front["status"]
      values = front["values"]
      if not isinstance(verification, str) or verification[:1] not in {"V", "M"}:
          raise PinFormatError(
              f"{path}: verification must be V1 through V10 or a milestone id such as M1"
          )
      if expected_verification is not None and verification != expected_verification:
          raise PinFormatError(
              f"{path}: expected {expected_verification}, found {verification}"
          )
      if status not in {"passed", "blocked"}:
          raise PinFormatError(f"{path}: status must be passed or blocked")
      if not isinstance(values, dict):
          raise PinFormatError(f"{path}: values must be a mapping")
      return PinDocument(
          path=path,
          verification=verification,
          status=cast(PinStatus, status),
          observed_at=str(front["observed_at"]),
          source_revision=str(front["source_revision"]),
          values=cast(dict[str, Any], values),
          contradiction=(
              str(front["contradiction"]) if front.get("contradiction") is not None else None
          ),
          body=body,
      )
  ```

  Create `research/der/cli.py`:

  ```python
  """Owner CLI; command implementations remain in focused service modules."""

  from __future__ import annotations

  from pathlib import Path

  import typer

  from research.der import __version__
  from research.der.errors import DerError
  from research.der.pins import PIN_PATHS, load_pin

  app = typer.Typer(no_args_is_help=True, pretty_exceptions_enable=False)
  pins_app = typer.Typer(no_args_is_help=True)
  app.add_typer(pins_app, name="pins")


  @app.command()
  def version() -> None:
      """Print the package version."""
      typer.echo(f"der {__version__}")


  @pins_app.command("assert")
  def assert_pin(
      verification: str = typer.Argument(help="V1 through V10"),
      path: Path | None = typer.Option(None, "--path"),
  ) -> None:
      """Fail unless a discovery pin exists and passed."""
      try:
          pin_path = path or PIN_PATHS[verification]
          pin = load_pin(pin_path, expected_verification=verification)
          pin.require_passed()
      except KeyError:
          typer.echo(f"unknown verification: {verification}", err=True)
          raise typer.Exit(code=2) from None
      except DerError as exc:
          typer.echo(str(exc), err=True)
          raise typer.Exit(code=exc.exit_code) from exc
      typer.echo(f"{verification} passed: {pin_path}")
  ```

- [ ] **Step 8: Run the bootstrap checks to green.** Run:

  ```bash
  uv run pytest tests/test_package.py tests/test_pins.py -q
  uv run ruff check research/der tests/test_package.py tests/test_pins.py
  uv run mypy research/der
  uv run der pins assert V3 --path tests/fixtures/pins/passed.md
  ```

  Expected output includes `5 passed`, no Ruff or mypy diagnostics, and `V3 passed: tests/fixtures/pins/passed.md`.

- [ ] **Step 9: Verify blocked discovery uses the prescribed STOP exit.** Run:

  ```bash
  set +e
  uv run der pins assert V2 --path tests/fixtures/pins/blocked.md
  rc=$?
  set -e
  test "$rc" -eq 78
  ```

  Expected stderr names `V2 discovery is blocked` and the shell exits successfully because `rc` is exactly `78`.

- [ ] **Step 10: Commit.** Run:

  ```bash
  git add \
    pyproject.toml uv.lock package.json package-lock.json .gitignore \
    research/__init__.py research/der/__init__.py research/der/errors.py \
    research/der/pins.py research/der/cli.py \
    tests/test_package.py tests/test_pins.py tests/fixtures/pins
  git commit -m "build: bootstrap der package and discovery pins"
  ```

### Task 1: Discovery V7 and immutable upstream identity pins

**Files:**
- Create: `scripts/discover_v7_deepswe.py`
- Create: `research-plan/pins/external-identities.md`
- Create: `research-plan/pins/v7-deepswe-revisions.md`
- Create: `research/UPSTREAM.md`
- Create: `tests/test_discover_v7.py`
- Create: `tests/fixtures/deepswe/minimal-task/task.toml`
- Create: `tests/fixtures/deepswe/minimal-task/instruction.md`
- Create: `tests/fixtures/deepswe/minimal-task/pre_artifacts.sh`
- Create: `tests/fixtures/deepswe/minimal-task/environment/Dockerfile`
- Create: `tests/fixtures/deepswe/minimal-task/tests/test.sh`
- Create: `tests/fixtures/deepswe/minimal-task/solution/README.md`

**Interfaces:**
- Consumes: source revisions in the source-lock table; `DER_SOURCE_CACHE` (default `/var/cache/der/sources`); pin writer format from Task 0.
- Produces: V7 pin values `deep_swe_commit`, `task_root`, `task_ids`, `task_checksums`, `audited_verifiers`; external identity values for AHE, Pier, DeepSWE, Qwen, and the Qwen archive checksum once cached.

- [ ] **Step 1: Write a minimal valid DeepSWE-shaped fixture.** Create `tests/fixtures/deepswe/minimal-task/task.toml`:

  ```toml
  version = "1.0"
  [metadata]
  author_name = "fixture"
  difficulty = "easy"
  category = "software-engineering"
  tags = ["python"]

  [agent]
  timeout_sec = 60

  [verifier]
  timeout_sec = 60

  [environment]
  build_timeout_sec = 60
  cpus = 1
  memory_mb = 512
  storage_mb = 512
  ```

  Create `instruction.md` containing `Return a committed patch.`, `pre_artifacts.sh` containing `#!/bin/sh\ngit diff HEAD`, `environment/Dockerfile` containing `FROM python:3.13-slim`, `tests/test.sh` containing `#!/bin/sh\nexit 0`, and `solution/README.md` containing `Fixture solution.`. Mark both shell files executable:

  ```bash
  chmod +x \
    tests/fixtures/deepswe/minimal-task/pre_artifacts.sh \
    tests/fixtures/deepswe/minimal-task/tests/test.sh
  ```

- [ ] **Step 2: Write the failing discovery-unit test.** Create `tests/test_discover_v7.py`:

  ```python
  from pathlib import Path

  import pytest

  from scripts.discover_v7_deepswe import audit_task, discover_tasks


  def test_valid_task_is_discovered_and_hashed() -> None:
      root = Path("tests/fixtures/deepswe")

      tasks = discover_tasks(root)

      assert [task.task_id for task in tasks] == ["minimal-task"]
      assert len(tasks[0].checksum) == 64
      assert tasks[0].verifier_files == ("tests/test.sh",)


  def test_audit_stops_when_pre_artifacts_is_missing(tmp_path: Path) -> None:
      task = tmp_path / "broken"
      task.mkdir()
      (task / "task.toml").write_text("version = '1.0'\n", encoding="utf-8")
      (task / "instruction.md").write_text("x\n", encoding="utf-8")
      (task / "environment").mkdir()
      (task / "tests").mkdir()
      (task / "solution").mkdir()

      with pytest.raises(ValueError, match="pre_artifacts.sh"):
          audit_task(task, tmp_path)
  ```

- [ ] **Step 3: Run the focused test and observe the missing script module.** Run:

  ```bash
  uv run pytest tests/test_discover_v7.py -q
  ```

  Expected failure includes `ModuleNotFoundError: No module named 'scripts.discover_v7_deepswe'`.

- [ ] **Step 4: Implement the deterministic source/task probe.** Create `scripts/discover_v7_deepswe.py`:

  ```python
  #!/usr/bin/env python3
  """Verify locked sources and audit the pinned DeepSWE task tree."""

  from __future__ import annotations

  import argparse
  import hashlib
  import json
  import os
  import subprocess
  import sys
  from dataclasses import asdict, dataclass
  from datetime import UTC, datetime
  from pathlib import Path
  from typing import Any

  import yaml

  LOCKS = {
      "ahe": (
          "https://github.com/china-qijizhifeng/agentic-harness-engineering.git",
          "faf44bc4aea57413c520bc5711c6ebf628e0da1e",
      ),
      "pier": (
          "https://github.com/datacurve-ai/pier.git",
          "e69a20e4e0ac073ec71fde0274bab3d9f40bac87",
      ),
      "deep-swe": (
          "https://github.com/datacurve-ai/deep-swe.git",
          "8cae5984d5dd0ee37445beff0e928dc10c331116",
      ),
      "qwen-code": (
          "https://github.com/QwenLM/qwen-code.git",
          "92fda5603e84ef62a1b29bf6faf4f6a8124a2bf7",
      ),
  }
  REQUIRED_TASK_ENTRIES = (
      "task.toml",
      "instruction.md",
      "pre_artifacts.sh",
      "environment",
      "tests",
      "solution",
  )


  @dataclass(frozen=True, slots=True)
  class TaskAudit:
      task_id: str
      relative_path: str
      checksum: str
      verifier_files: tuple[str, ...]
      pre_artifacts_sha256: str
      task_toml_sha256: str


  def _sha256_file(path: Path) -> str:
      digest = hashlib.sha256()
      with path.open("rb") as handle:
          for chunk in iter(lambda: handle.read(1024 * 1024), b""):
              digest.update(chunk)
      return digest.hexdigest()


  def _tree_checksum(path: Path) -> str:
      digest = hashlib.sha256()
      for item in sorted(entry for entry in path.rglob("*") if entry.is_file()):
          rel = item.relative_to(path).as_posix().encode()
          digest.update(len(rel).to_bytes(4, "big"))
          digest.update(rel)
          data = item.read_bytes()
          digest.update(len(data).to_bytes(8, "big"))
          digest.update(data)
      return digest.hexdigest()


  def audit_task(task_dir: Path, root: Path) -> TaskAudit:
      missing = [name for name in REQUIRED_TASK_ENTRIES if not (task_dir / name).exists()]
      if missing:
          raise ValueError(f"{task_dir}: missing required task entries: {', '.join(missing)}")
      verifier_files = tuple(
          sorted(
              path.relative_to(task_dir).as_posix()
              for path in (task_dir / "tests").rglob("*")
              if path.is_file()
          )
      )
      if not verifier_files:
          raise ValueError(f"{task_dir}: tests/ contains no verifier files")
      if not os.access(task_dir / "pre_artifacts.sh", os.X_OK):
          raise ValueError(f"{task_dir}: pre_artifacts.sh is not executable")
      return TaskAudit(
          task_id=task_dir.name,
          relative_path=task_dir.relative_to(root).as_posix(),
          checksum=_tree_checksum(task_dir),
          verifier_files=verifier_files,
          pre_artifacts_sha256=_sha256_file(task_dir / "pre_artifacts.sh"),
          task_toml_sha256=_sha256_file(task_dir / "task.toml"),
      )


  def discover_tasks(root: Path) -> list[TaskAudit]:
      task_dirs = sorted(path.parent for path in root.rglob("task.toml"))
      if not task_dirs:
          raise ValueError(f"{root}: no task.toml files found")
      audits = [audit_task(path, root) for path in task_dirs]
      ids = [audit.task_id for audit in audits]
      if len(ids) != len(set(ids)):
          raise ValueError("DeepSWE task directory basenames are not unique")
      return audits


  def _git(path: Path, *args: str) -> str:
      completed = subprocess.run(
          ["git", "-C", str(path), *args],
          check=True,
          text=True,
          stdout=subprocess.PIPE,
          stderr=subprocess.STDOUT,
      )
      return completed.stdout.strip()


  def verify_source(cache: Path, name: str, url: str, commit: str) -> dict[str, str]:
      repo = cache / name
      if not (repo / ".git").is_dir():
          raise ValueError(f"source mirror is absent: {repo}; clone {url} first")
      observed = _git(repo, "rev-parse", "HEAD")
      if observed != commit:
          raise ValueError(f"{name}: expected {commit}, observed {observed}")
      dirty = _git(repo, "status", "--porcelain")
      if dirty:
          raise ValueError(f"{name}: source mirror is dirty: {dirty}")
      return {"url": url, "commit": observed, "tree": _git(repo, "rev-parse", "HEAD^{tree}")}


  def write_pin(
      path: Path,
      *,
      verification: str,
      source_revision: str,
      values: dict[str, Any],
      transcript: str,
      blocked: str | None = None,
  ) -> None:
      front: dict[str, Any] = {
          "verification": verification,
          "status": "blocked" if blocked else "passed",
          "observed_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
          "source_revision": source_revision,
          "values": values,
      }
      if blocked:
          front["contradiction"] = blocked
      text = "---\n" + yaml.safe_dump(front, sort_keys=False).rstrip() + "\n---\n"
      text += f"# {verification} source and DeepSWE probe\n\n"
      text += "## Command transcript\n\n```text\n" + transcript.rstrip() + "\n```\n"
      path.parent.mkdir(parents=True, exist_ok=True)
      path.write_text(text, encoding="utf-8")


  def main() -> int:
      parser = argparse.ArgumentParser()
      parser.add_argument(
          "--source-cache",
          type=Path,
          default=Path(os.environ.get("DER_SOURCE_CACHE", "/var/cache/der/sources")),
      )
      parser.add_argument(
          "--v7-pin",
          type=Path,
          default=Path("research-plan/pins/v7-deepswe-revisions.md"),
      )
      parser.add_argument(
          "--identity-pin",
          type=Path,
          default=Path("research-plan/pins/external-identities.md"),
      )
      args = parser.parse_args()
      transcript: list[str] = []
      try:
          identities: dict[str, dict[str, str]] = {}
          for name, (url, commit) in LOCKS.items():
              info = verify_source(args.source_cache, name, url, commit)
              identities[name] = info
              transcript.append(f"git -C {args.source_cache / name} rev-parse HEAD")
              transcript.append(info["commit"])
              transcript.append(f"tree {info['tree']}")
          deep_swe = args.source_cache / "deep-swe"
          tasks = discover_tasks(deep_swe)
          transcript.append(f"audited DeepSWE tasks: {len(tasks)}")
          for audit in tasks:
              transcript.append(
                  f"{audit.task_id} {audit.checksum} verifier_files={len(audit.verifier_files)}"
              )
          task_values = [asdict(task) for task in tasks]
          write_pin(
              args.v7_pin,
              verification="V7",
              source_revision=LOCKS["deep-swe"][1],
              values={
                  "deep_swe_commit": LOCKS["deep-swe"][1],
                  "task_root": str(deep_swe),
                  "task_count": len(tasks),
                  "task_ids": [task.task_id for task in tasks],
                  "task_checksums": {task.task_id: task.checksum for task in tasks},
                  "audited_verifiers": task_values,
              },
              transcript="\n".join(transcript),
          )
          write_pin(
              args.identity_pin,
              verification="V7",
              source_revision=LOCKS["deep-swe"][1],
              values={"sources": identities},
              transcript="\n".join(transcript),
          )
          print(json.dumps({"status": "passed", "tasks": len(tasks)}, sort_keys=True))
          return 0
      except Exception as exc:
          message = str(exc)
          write_pin(
              args.v7_pin,
              verification="V7",
              source_revision=LOCKS["deep-swe"][1],
              values={},
              transcript="\n".join(transcript + [f"ERROR: {message}"]),
              blocked=message,
          )
          print(f"STOP V7: {message}", file=sys.stderr)
          return 78


  if __name__ == "__main__":
      raise SystemExit(main())
  ```

- [ ] **Step 5: Run the fixture test to green.** Run:

  ```bash
  uv run pytest tests/test_discover_v7.py -q
  uv run ruff check scripts/discover_v7_deepswe.py tests/test_discover_v7.py
  ```

  Expected output: `2 passed` and no Ruff diagnostics.

- [ ] **Step 6: Populate the immutable source cache at the locked revisions.** Run:

  ```bash
  export DER_SOURCE_CACHE=/var/cache/der/sources
  sudo install -d -m 0755 -o "$USER" -g "$(id -gn)" "$DER_SOURCE_CACHE"

  clone_locked() {
    name="$1"; url="$2"; commit="$3"
    if [ ! -d "$DER_SOURCE_CACHE/$name/.git" ]; then
      git clone --filter=blob:none "$url" "$DER_SOURCE_CACHE/$name"
    fi
    git -C "$DER_SOURCE_CACHE/$name" fetch --force origin "$commit"
    git -C "$DER_SOURCE_CACHE/$name" checkout --detach "$commit"
    git -C "$DER_SOURCE_CACHE/$name" reset --hard "$commit"
    git -C "$DER_SOURCE_CACHE/$name" clean -ffd
  }

  clone_locked ahe \
    https://github.com/china-qijizhifeng/agentic-harness-engineering.git \
    faf44bc4aea57413c520bc5711c6ebf628e0da1e
  clone_locked pier \
    https://github.com/datacurve-ai/pier.git \
    e69a20e4e0ac073ec71fde0274bab3d9f40bac87
  clone_locked deep-swe \
    https://github.com/datacurve-ai/deep-swe.git \
    8cae5984d5dd0ee37445beff0e928dc10c331116
  clone_locked qwen-code \
    https://github.com/QwenLM/qwen-code.git \
    92fda5603e84ef62a1b29bf6faf4f6a8124a2bf7
  ```

  Expected output from each checkout ends with `HEAD is now at ...`; all four `git status --porcelain` commands print nothing.

- [ ] **Step 7: Run discovery V7 and enforce its STOP gate.** Run:

  ```bash
  DER_SOURCE_CACHE=/var/cache/der/sources \
    uv run python scripts/discover_v7_deepswe.py
  uv run der pins assert V7
  ```

  Expected stdout is a one-line JSON object with `"status": "passed"` and a positive `tasks` count, followed by `V7 passed: research-plan/pins/v7-deepswe-revisions.md`. If the script exits `78`, stop all subsequent tasks, retain the generated blocked pin, and escalate its transcript to the owner; do not select a different DeepSWE revision or repair upstream task content.

- [ ] **Step 8: Spot-check verifier auditability from the recorded, real task list.** Run this exact command, which selects the first, middle, and last task deterministically from the pin rather than inventing task names:

  ```bash
  uv run python - <<'PY'
  from pathlib import Path
  from research.der.pins import load_pin

  pin = load_pin(Path("research-plan/pins/v7-deepswe-revisions.md"), "V7")
  pin.require_passed()
  rows = pin.value("audited_verifiers")
  chosen = [rows[0], rows[len(rows) // 2], rows[-1]]
  for row in chosen:
      print(row["task_id"])
      print("  task.toml", row["task_toml_sha256"])
      print("  pre_artifacts.sh", row["pre_artifacts_sha256"])
      for name in row["verifier_files"]:
          print("  verifier", name)
  PY
  ```

  Expected output names three concrete task IDs and at least one verifier file for each. Copy this exact output into the V7 pin under a new `## Verifier spot-check transcript` fenced block. This is evidence recording, not a design decision.

- [ ] **Step 9: Write the upstream provenance document.** Create `research/UPSTREAM.md` with the exact revisions and update discipline:

  ```markdown
  # Vendored and cached upstreams

  | Component | URL | Revision | Local source |
  |---|---|---|---|
  | AHE | `https://github.com/china-qijizhifeng/agentic-harness-engineering.git` | `faf44bc4aea57413c520bc5711c6ebf628e0da1e` | vendored under `research/` in Task 19; pristine cache `/var/cache/der/sources/ahe` |
  | Pier | `https://github.com/datacurve-ai/pier.git` | `e69a20e4e0ac073ec71fde0274bab3d9f40bac87` | installed as `datacurve-pier==0.3.0`; pristine cache `/var/cache/der/sources/pier` |
  | DeepSWE v1.1 | `https://github.com/datacurve-ai/deep-swe.git` | `8cae5984d5dd0ee37445beff0e928dc10c331116` | pristine task cache `/var/cache/der/sources/deep-swe` |
  | Qwen Code v0.20.0 | `https://github.com/QwenLM/qwen-code.git` | `92fda5603e84ef62a1b29bf6faf4f6a8124a2bf7` | pristine source cache `/var/cache/der/sources/qwen-code`; runtime archive pinned by V3 |

  `research-plan/pins/external-identities.md` is the machine-readable observation record. A source update is an architecture maintenance event: use a new branch, change one revision at a time, rerun its discovery gate and all dependent golden fixtures, and obtain owner review before merging. Never run `git pull` inside a locked source cache or the vendored `research/` tree.
  ```

- [ ] **Step 10: Commit.** Run:

  ```bash
  git add \
    scripts/discover_v7_deepswe.py \
    research-plan/pins/external-identities.md \
    research-plan/pins/v7-deepswe-revisions.md \
    research/UPSTREAM.md \
    tests/test_discover_v7.py tests/fixtures/deepswe
  git commit -m "research: pin upstream identities and audit DeepSWE v1.1"
  ```

### Task 2: Define strict evaluation, lifecycle, scorecard, and suite contracts

**Files:**
- Create: `research/der/contracts/__init__.py`
- Create: `research/der/contracts/base.py`
- Create: `research/der/contracts/eval.py`
- Create: `research/der/contracts/experiment.py`
- Create: `research/der/contracts/scorecard.py`
- Create: `research/der/contracts/suite.py`
- Create: `research/der/contracts/schema_export.py`
- Modify: `research/der/cli.py`
- Create: `research/schemas/eval-spec.schema.json`
- Create: `research/schemas/eval-result.schema.json`
- Create: `research/schemas/scorecard.schema.json`
- Create: `research/schemas/experiment-frontmatter.schema.json`
- Create: `research/schemas/suite.schema.json`
- Create: `research/schemas/critic-proposal.schema.json`
- Create: `tests/contracts/test_eval_contract.py`
- Create: `tests/contracts/test_experiment_contract.py`
- Create: `tests/contracts/test_suite_contract.py`
- Create: `tests/contracts/test_schema_export.py`

**Interfaces:**
- Consumes: Python/Pydantic setup from Task 0; V7 task identity vocabulary from Task 1.
- Produces: the exact data types used by every later task: `RunBudget`, `HarnessIdentity`, `RuntimeManifest`, `DiscoveryPinPaths`, `EvalSpec`, `EvalResult`, `ExperimentFrontMatter`, `Scorecard`, and `SuiteManifest`; CLI `der schemas generate --check`.

- [ ] **Step 1: Write the failing contract tests.** Create `tests/contracts/test_eval_contract.py`:

  ```python
  from datetime import UTC, datetime
  from decimal import Decimal
  from pathlib import Path

  import pytest
  from pydantic import ValidationError

  from research.der.contracts.eval import (
      AttemptOutcome,
      DiscoveryPinPaths,
      EvalResult,
      EvalSpec,
      FailureReason,
      HarnessIdentity,
      OutcomeKind,
      ResourceTotals,
      RunBudget,
      TaskResult,
      TokenUsage,
  )


  def identity() -> HarnessIdentity:
      return HarnessIdentity(
          source_commit="a" * 40,
          harness_tree_oid="b" * 40,
          runtime_manifest_digest="c" * 64,
      )


  def budget() -> RunBudget:
      return RunBudget(
          max_cost_usd=Decimal("12.50"),
          max_wall_seconds=1800,
          max_attempts=8,
          max_input_tokens=500_000,
          max_output_tokens=100_000,
          max_tool_calls=300,
          max_session_turns=40,
      )


  def test_eval_spec_is_strict_and_keyless() -> None:
      spec = EvalSpec(
          experiment_id="EXP-0001-smoke",
          run_id="RUN-EXP-0001-smoke-development-01",
          identity=identity(),
          baseline_tree_oid="d" * 40,
          suite_version="deepswe-v1",
          suite_class="development",
          task_root=Path("/cache/deep-swe"),
          task_revisions={"task-a": "e" * 64},
          task_ids=("task-a",),
          k=1,
          n_concurrent=1,
          jobs_dir=Path("research/runs/pier"),
          staged_harness_dir=Path("research/tmp/staged/RUN-1"),
          pins=DiscoveryPinPaths(
              pier_artifacts=Path("research-plan/pins/v1-pier-artifact-layout.md"),
              proxy_route=Path("research-plan/pins/v2-acceptance-chain.md"),
              qwen_archive=Path("research-plan/pins/v3-qwen-archive-install.md"),
          ),
          model_policy_id="deepseek-v4-pro-v1",
          budget=budget(),
      )

      assert spec.environment == "docker"
      assert "api_key" not in spec.model_dump_json().lower()
      with pytest.raises(ValidationError):
          EvalSpec.model_validate({**spec.model_dump(), "k": 0})


  def test_task_result_requires_complete_attempt_indexes_and_fraction() -> None:
      attempt = AttemptOutcome(
          task_id="task-a",
          attempt_index=0,
          trial_name="task-a__1",
          trial_dir=Path("trial-a"),
          outcome=OutcomeKind.PASSED,
          failure_reason=None,
          reward=Decimal("1"),
          metrics={"tests_passed": 10},
          usage=TokenUsage(input_tokens=2, cache_tokens=1, output_tokens=3),
          cost_usd=Decimal("0.03"),
          artifact_digests={"result.json": "f" * 64},
      )
      task = TaskResult(
          task_id="task-a",
          attempts=(attempt,),
          pass_fraction=Decimal("1"),
      )

      assert task.pass_fraction == Decimal("1")
      with pytest.raises(ValidationError, match="pass_fraction"):
          TaskResult(
              task_id="task-a",
              attempts=(attempt,),
              pass_fraction=Decimal("0"),
          )


  def test_eval_result_requires_proxy_observed_model() -> None:
      now = datetime(2026, 7, 21, tzinfo=UTC)
      result = EvalResult(
          experiment_id="EXP-0001-smoke",
          run_id="RUN-EXP-0001-smoke-development-01",
          evaluator="datacurve-pier",
          evaluator_version="0.3.0",
          evaluator_job_id="job-1",
          exact_result_path=Path("research/runs/pier/job-1/result.json"),
          identity=identity(),
          suite_version="deepswe-v1",
          suite_class="development",
          k=1,
          model_policy_id="deepseek-v4-pro-v1",
          observed_models=("deepseek-v4-pro",),
          tasks=(),
          resources=ResourceTotals(),
          artifact_digests={"job-result": "a" * 64},
          started_at=now,
          finished_at=now,
      )

      assert result.observed_models == ("deepseek-v4-pro",)
      with pytest.raises(ValidationError, match="observed_models"):
          EvalResult.model_validate({**result.model_dump(), "observed_models": ()})


  def test_failed_and_invalid_reasons_cannot_cross_taxonomy() -> None:
      common = dict(
          task_id="task-a",
          attempt_index=0,
          trial_name="trial",
          trial_dir=Path("trial"),
          reward=None,
          metrics={},
          usage=TokenUsage(),
          cost_usd=Decimal("0"),
          artifact_digests={},
      )
      with pytest.raises(ValidationError, match="does not belong"):
          AttemptOutcome(
              **common,
              outcome=OutcomeKind.INVALID,
              failure_reason=FailureReason.AGENT_TIMEOUT,
          )
  ```

  Create `tests/contracts/test_experiment_contract.py`:

  ```python
  from datetime import UTC, datetime
  from decimal import Decimal

  import pytest
  from pydantic import ValidationError

  from research.der.contracts.eval import HarnessIdentity, RunBudget
  from research.der.contracts.experiment import (
      ExperimentContract,
      ExperimentFrontMatter,
      ExperimentStatus,
      Guardrail,
      assert_transition,
  )


  NOW = datetime(2026, 7, 21, tzinfo=UTC)
  IDENTITY = HarnessIdentity(
      source_commit="a" * 40,
      harness_tree_oid="b" * 40,
      runtime_manifest_digest="c" * 64,
  )
  BUDGET = RunBudget(
      max_cost_usd=Decimal("20"),
      max_wall_seconds=3600,
      max_attempts=10,
      max_input_tokens=1_000_000,
      max_output_tokens=200_000,
      max_tool_calls=500,
      max_session_turns=50,
  )


  def contract() -> ExperimentContract:
      return ExperimentContract(
          hypothesis="A narrower repository-navigation skill improves confirmation performance.",
          primary_metric="confirmation_macro_pass_at_1",
          minimum_effect=Decimal("0.02"),
          guardrails=(
              Guardrail(metric="invalid_fraction", operator="<=", threshold=Decimal("0.05")),
          ),
          falsifier="Reject when the confirmation effect is below 0.02 or a guardrail fails.",
          suite_version="deepswe-v1",
          k=1,
          budget=BUDGET,
      )


  def test_preregistration_has_exactly_one_primary_metric() -> None:
      record = ExperimentFrontMatter(
          experiment_id="EXP-0001-navigation",
          slug="navigation",
          title="Narrow repository navigation skill",
          status=ExperimentStatus.PROPOSED,
          created_at=NOW,
          updated_at=NOW,
          baseline_identity=IDENTITY,
          candidate_identity=IDENTITY.model_copy(update={"harness_tree_oid": "d" * 40}),
          contract=contract(),
          run_ids=(),
      )

      assert record.contract.primary_metric == "confirmation_macro_pass_at_1"
      with pytest.raises(ValidationError):
          ExperimentFrontMatter.model_validate(
              {**record.model_dump(), "experiment_id": "bad"}
          )


  @pytest.mark.parametrize(
      ("source", "target", "allowed"),
      [
          (ExperimentStatus.PROPOSED, ExperimentStatus.RUNNING, True),
          (ExperimentStatus.RUNNING, ExperimentStatus.ADOPTED, True),
          (ExperimentStatus.RUNNING, ExperimentStatus.REJECTED, True),
          (ExperimentStatus.RUNNING, ExperimentStatus.INVALID, True),
          (ExperimentStatus.PROPOSED, ExperimentStatus.ADOPTED, False),
          (ExperimentStatus.ADOPTED, ExperimentStatus.RUNNING, False),
      ],
  )
  def test_transition_graph(source: ExperimentStatus, target: ExperimentStatus, allowed: bool) -> None:
      if allowed:
          assert_transition(source, target)
      else:
          with pytest.raises(ValueError, match="forbidden lifecycle transition"):
              assert_transition(source, target)
  ```

  Create `tests/contracts/test_suite_contract.py`:

  ```python
  from research.der.contracts.suite import SuiteManifest, SuiteMember


  def test_suite_manifest_keeps_three_explicit_classes() -> None:
      manifest = SuiteManifest(
          version="deepswe-v1",
          deep_swe_commit="a" * 40,
          reporting_k=5,
          development=(SuiteMember(task_id="dev-a", task_checksum="b" * 64),),
          confirmation=(SuiteMember(task_id="confirm-a", task_checksum="c" * 64),),
          spine=(SuiteMember(task_id="spine-a", task_checksum="d" * 64),),
          frozen=True,
      )

      assert manifest.task_ids("confirmation") == ("confirm-a",)
      assert manifest.frozen is True
  ```

  Create `tests/contracts/test_schema_export.py`:

  ```python
  from pathlib import Path

  from research.der.contracts.schema_export import export_schemas


  def test_schema_export_is_deterministic(tmp_path: Path) -> None:
      first = tmp_path / "first"
      second = tmp_path / "second"

      export_schemas(first)
      export_schemas(second)

      first_files = {path.name: path.read_bytes() for path in first.iterdir()}
      second_files = {path.name: path.read_bytes() for path in second.iterdir()}
      assert first_files == second_files
      assert set(first_files) == {
          "eval-spec.schema.json",
          "eval-result.schema.json",
          "scorecard.schema.json",
          "experiment-frontmatter.schema.json",
          "suite.schema.json",
          "critic-proposal.schema.json",
      }
  ```

- [ ] **Step 2: Run the contract tests and observe the missing contracts.** Run:

  ```bash
  uv run pytest tests/contracts -q
  ```

  Expected failure includes `ModuleNotFoundError: No module named 'research.der.contracts'`.

- [ ] **Step 3: Implement the strict base and evaluation contracts.** Create `research/der/contracts/__init__.py` as an empty file. Create `research/der/contracts/base.py`:

  ```python
  """Strict immutable model base and canonical JSON encoding."""

  from __future__ import annotations

  import json
  from typing import Any

  from pydantic import BaseModel, ConfigDict


  class StrictModel(BaseModel):
      model_config = ConfigDict(extra="forbid", frozen=True, validate_default=True)


  def canonical_json_bytes(value: Any) -> bytes:
      if isinstance(value, BaseModel):
          value = value.model_dump(mode="json", exclude_none=False)
      return (
          json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
      ).encode("utf-8")
  ```

  Create `research/der/contracts/eval.py`:

  ```python
  """Stable evaluator seam contracts."""

  from __future__ import annotations

  from datetime import datetime
  from decimal import Decimal
  from enum import StrEnum
  from pathlib import Path
  from typing import Annotated, Literal

  from pydantic import Field, model_validator

  from research.der.contracts.base import StrictModel

  Sha256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
  GitOid = Annotated[str, Field(pattern=r"^[0-9a-f]{40,64}$")]
  ExperimentId = Annotated[str, Field(pattern=r"^EXP-[0-9]{4}-[a-z0-9]+(?:-[a-z0-9]+)*$")]
  RunId = Annotated[
      str,
      Field(pattern=r"^RUN-EXP-[0-9]{4}-[a-z0-9]+(?:-[a-z0-9]+)*-[a-z]+-[0-9]{2}$"),
  ]


  class RunBudget(StrictModel):
      max_cost_usd: Annotated[Decimal, Field(gt=0)]
      max_wall_seconds: Annotated[int, Field(gt=0)]
      max_attempts: Annotated[int, Field(gt=0)]
      max_input_tokens: Annotated[int, Field(gt=0)]
      max_output_tokens: Annotated[int, Field(gt=0)]
      max_tool_calls: Annotated[int, Field(gt=0)]
      max_session_turns: Annotated[int, Field(gt=0)]


  class HarnessIdentity(StrictModel):
      source_commit: GitOid
      harness_tree_oid: GitOid
      runtime_manifest_digest: Sha256


  class RuntimeManifest(StrictModel):
      schema_version: Literal["der.runtime-manifest.v1"] = "der.runtime-manifest.v1"
      pier_package: Literal["datacurve-pier==0.3.0"] = "datacurve-pier==0.3.0"
      pier_commit: GitOid
      deep_swe_commit: GitOid
      task_revisions: dict[str, Sha256]
      qwen_version: Literal["0.20.0"] = "0.20.0"
      qwen_archive_sha256: Sha256
      der_agent_revision: GitOid
      proxy_policy_id: str
      qwen_system_policy_sha256: Sha256


  class DiscoveryPinPaths(StrictModel):
      pier_artifacts: Path
      proxy_route: Path
      qwen_archive: Path


  class EvalSpec(StrictModel):
      schema_version: Literal["der.eval-spec.v1"] = "der.eval-spec.v1"
      experiment_id: ExperimentId
      run_id: RunId
      identity: HarnessIdentity
      baseline_tree_oid: GitOid
      suite_version: str
      suite_class: Literal["development", "confirmation", "spine", "smoke"]
      task_root: Path
      task_revisions: dict[str, Sha256]
      task_ids: tuple[str, ...]
      k: Annotated[int, Field(gt=0)]
      n_concurrent: Annotated[int, Field(gt=0, le=8)]
      jobs_dir: Path
      staged_harness_dir: Path
      pins: DiscoveryPinPaths
      model_policy_id: str
      budget: RunBudget
      environment: Literal["docker"] = "docker"

      @model_validator(mode="after")
      def task_revision_coverage(self) -> EvalSpec:
          if not self.task_ids:
              raise ValueError("task_ids must not be empty")
          if len(self.task_ids) != len(set(self.task_ids)):
              raise ValueError("task_ids must be unique")
          missing = sorted(set(self.task_ids) - self.task_revisions.keys())
          extra = sorted(self.task_revisions.keys() - set(self.task_ids))
          if missing or extra:
              raise ValueError(f"task_revisions mismatch: missing={missing}, extra={extra}")
          if self.k * len(self.task_ids) > self.budget.max_attempts:
              raise ValueError("RunBudget.max_attempts is smaller than task_count * k")
          return self


  class OutcomeKind(StrEnum):
      PASSED = "passed"
      FAILED = "failed"
      INVALID = "invalid"


  class FailureReason(StrEnum):
      TASK_ASSERTION = "task_assertion"
      AGENT_TIMEOUT = "agent_timeout"
      CONTEXT_TIMEOUT = "context_timeout"
      PROVIDER = "provider"
      NETWORK = "network"
      INFRA = "infra"
      MALFORMED_VERIFIER = "malformed_verifier"


  FAILED_REASONS = {
      FailureReason.TASK_ASSERTION,
      FailureReason.AGENT_TIMEOUT,
      FailureReason.CONTEXT_TIMEOUT,
  }
  INVALID_REASONS = {
      FailureReason.PROVIDER,
      FailureReason.NETWORK,
      FailureReason.INFRA,
      FailureReason.MALFORMED_VERIFIER,
  }


  class TokenUsage(StrictModel):
      input_tokens: Annotated[int, Field(ge=0)] = 0
      cache_tokens: Annotated[int, Field(ge=0)] = 0
      output_tokens: Annotated[int, Field(ge=0)] = 0
      peak_context_tokens: Annotated[int, Field(ge=0)] = 0
      tool_calls: Annotated[int, Field(ge=0)] = 0
      session_turns: Annotated[int, Field(ge=0)] = 0


  MetricScalar = int | Decimal | str | bool | None


  class AttemptOutcome(StrictModel):
      task_id: str
      attempt_index: Annotated[int, Field(ge=0)]
      trial_name: str
      trial_dir: Path
      outcome: OutcomeKind
      failure_reason: FailureReason | None
      reward: Decimal | None
      metrics: dict[str, MetricScalar]
      usage: TokenUsage
      cost_usd: Annotated[Decimal, Field(ge=0)]
      artifact_digests: dict[str, Sha256]

      @model_validator(mode="after")
      def reason_matches_outcome(self) -> AttemptOutcome:
          if self.outcome is OutcomeKind.PASSED and self.failure_reason is not None:
              raise ValueError("passed outcome cannot have a failure_reason")
          if self.outcome is OutcomeKind.FAILED and self.failure_reason not in FAILED_REASONS:
              raise ValueError(f"{self.failure_reason} does not belong to failed taxonomy")
          if self.outcome is OutcomeKind.INVALID and self.failure_reason not in INVALID_REASONS:
              raise ValueError(f"{self.failure_reason} does not belong to invalid taxonomy")
          return self


  class TaskResult(StrictModel):
      task_id: str
      attempts: tuple[AttemptOutcome, ...]
      pass_fraction: Annotated[Decimal, Field(ge=0, le=1)]

      @model_validator(mode="after")
      def validate_attempts_and_fraction(self) -> TaskResult:
          if not self.attempts:
              raise ValueError("attempts must not be empty")
          if any(attempt.task_id != self.task_id for attempt in self.attempts):
              raise ValueError("all attempts must match task_id")
          indexes = [attempt.attempt_index for attempt in self.attempts]
          if indexes != list(range(len(self.attempts))):
              raise ValueError("attempt_index values must be contiguous from zero")
          passed = sum(attempt.outcome is OutcomeKind.PASSED for attempt in self.attempts)
          expected = Decimal(passed) / Decimal(len(self.attempts))
          if self.pass_fraction != expected:
              raise ValueError(
                  f"pass_fraction {self.pass_fraction} does not match attempts {expected}"
              )
          return self


  class ResourceTotals(StrictModel):
      input_tokens: Annotated[int, Field(ge=0)] = 0
      cache_tokens: Annotated[int, Field(ge=0)] = 0
      output_tokens: Annotated[int, Field(ge=0)] = 0
      tool_calls: Annotated[int, Field(ge=0)] = 0
      wall_seconds: Annotated[Decimal, Field(ge=0)] = Decimal("0")
      cost_usd: Annotated[Decimal, Field(ge=0)] = Decimal("0")


  class EvalResult(StrictModel):
      schema_version: Literal["der.eval-result.v1"] = "der.eval-result.v1"
      experiment_id: ExperimentId
      run_id: RunId
      evaluator: Literal["datacurve-pier"]
      evaluator_version: Literal["0.3.0"]
      evaluator_job_id: str
      exact_result_path: Path
      identity: HarnessIdentity
      suite_version: str
      suite_class: Literal["development", "confirmation", "spine", "smoke"]
      k: Annotated[int, Field(gt=0)]
      model_policy_id: str
      observed_models: tuple[str, ...]
      tasks: tuple[TaskResult, ...]
      resources: ResourceTotals
      artifact_digests: dict[str, Sha256]
      started_at: datetime
      finished_at: datetime

      @model_validator(mode="after")
      def result_invariants(self) -> EvalResult:
          if not self.observed_models:
              raise ValueError("observed_models must come from proxy evidence")
          if self.finished_at < self.started_at:
              raise ValueError("finished_at precedes started_at")
          if len({task.task_id for task in self.tasks}) != len(self.tasks):
              raise ValueError("duplicate task results")
          if any(len(task.attempts) != self.k for task in self.tasks):
              raise ValueError("every task must contain exactly k attempts")
          return self
  ```

- [ ] **Step 4: Implement lifecycle, scorecard, and suite contracts.** Create `research/der/contracts/experiment.py`:

  ```python
  """Preregistered experiment and lifecycle contracts."""

  from __future__ import annotations

  from datetime import datetime
  from decimal import Decimal
  from enum import StrEnum
  from typing import Annotated, Literal

  from pydantic import Field, model_validator

  from research.der.contracts.base import StrictModel
  from research.der.contracts.eval import ExperimentId, HarnessIdentity, RunBudget, RunId


  class ExperimentStatus(StrEnum):
      PROPOSED = "proposed"
      RUNNING = "running"
      ADOPTED = "adopted"
      REJECTED = "rejected"
      INCONCLUSIVE = "inconclusive"
      INVALID = "invalid"


  TERMINAL_STATUSES = {
      ExperimentStatus.ADOPTED,
      ExperimentStatus.REJECTED,
      ExperimentStatus.INCONCLUSIVE,
      ExperimentStatus.INVALID,
  }
  ALLOWED_TRANSITIONS = {
      ExperimentStatus.PROPOSED: {ExperimentStatus.RUNNING},
      ExperimentStatus.RUNNING: TERMINAL_STATUSES,
  }


  class Guardrail(StrictModel):
      metric: str
      operator: Literal["<=", ">=", "<", ">", "=="]
      threshold: Decimal


  class ExperimentContract(StrictModel):
      hypothesis: Annotated[str, Field(min_length=20)]
      primary_metric: Literal["confirmation_macro_pass_at_1"]
      minimum_effect: Decimal
      guardrails: tuple[Guardrail, ...]
      falsifier: Annotated[str, Field(min_length=20)]
      suite_version: str
      k: Annotated[int, Field(gt=0)]
      budget: RunBudget


  class ExperimentFrontMatter(StrictModel):
      schema_version: Literal["der.experiment.v1"] = "der.experiment.v1"
      experiment_id: ExperimentId
      slug: Annotated[str, Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")]
      title: Annotated[str, Field(min_length=5)]
      status: ExperimentStatus
      created_at: datetime
      updated_at: datetime
      baseline_identity: HarnessIdentity
      candidate_identity: HarnessIdentity
      contract: ExperimentContract
      run_ids: tuple[RunId, ...]
      terminal_reason: str | None = None
      adopted_at: datetime | None = None
      executable_acknowledged: bool = False

      @model_validator(mode="after")
      def lifecycle_invariants(self) -> ExperimentFrontMatter:
          if self.updated_at < self.created_at:
              raise ValueError("updated_at precedes created_at")
          if self.status in TERMINAL_STATUSES and not self.terminal_reason:
              raise ValueError("terminal lifecycle status requires terminal_reason")
          if self.status is ExperimentStatus.ADOPTED and self.adopted_at is None:
              raise ValueError("adopted status requires adopted_at")
          if self.status is not ExperimentStatus.ADOPTED and self.adopted_at is not None:
              raise ValueError("adopted_at is only valid for adopted status")
          return self


  def assert_transition(source: ExperimentStatus, target: ExperimentStatus) -> None:
      if target not in ALLOWED_TRANSITIONS.get(source, set()):
          raise ValueError(f"forbidden lifecycle transition: {source.value} -> {target.value}")
  ```

  Create `research/der/contracts/scorecard.py`:

  ```python
  """Immutable scorecard and promotion-decision contracts."""

  from __future__ import annotations

  from datetime import datetime
  from decimal import Decimal
  from enum import StrEnum
  from typing import Literal

  from research.der.contracts.base import StrictModel
  from research.der.contracts.eval import EvalResult, HarnessIdentity, Sha256


  class ComparabilityStatus(StrEnum):
      COMPARABLE = "comparable"
      CONFOUNDED = "CONFOUNDED"
      INCOMPARABLE = "incomparable"


  class PromotionVerdict(StrEnum):
      ADOPT = "adopt"
      REJECT = "reject"
      INCONCLUSIVE = "inconclusive"
      INVALID = "invalid"


  class PromotionDecision(StrictModel):
      verdict: PromotionVerdict
      primary_metric: Literal["confirmation_macro_pass_at_1"]
      baseline_value: Decimal | None
      candidate_value: Decimal | None
      observed_effect: Decimal | None
      minimum_effect: Decimal
      guardrail_results: dict[str, bool]
      comparability: ComparabilityStatus
      reasons: tuple[str, ...]


  class Scorecard(StrictModel):
      schema_version: Literal["der.scorecard.v1"] = "der.scorecard.v1"
      created_at: datetime
      experiment_record_sha256: Sha256
      baseline_identity: HarnessIdentity
      candidate_identity: HarnessIdentity
      result: EvalResult
      decision: PromotionDecision
      secret_scrub_sha256: Sha256
  ```

  Create `research/der/contracts/suite.py`:

  ```python
  """Frozen DeepSWE suite manifest contracts."""

  from __future__ import annotations

  from typing import Annotated, Literal

  from pydantic import Field, model_validator

  from research.der.contracts.base import StrictModel
  from research.der.contracts.eval import GitOid, Sha256

  SuiteClass = Literal["development", "confirmation", "spine"]


  class SuiteMember(StrictModel):
      task_id: str
      task_checksum: Sha256


  class SuiteManifest(StrictModel):
      schema_version: Literal["der.suite.v1"] = "der.suite.v1"
      version: Annotated[str, Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*-v[0-9]+$")]
      deep_swe_commit: GitOid
      reporting_k: Annotated[int, Field(gt=0)]
      development: tuple[SuiteMember, ...]
      confirmation: tuple[SuiteMember, ...]
      spine: tuple[SuiteMember, ...]
      frozen: Literal[True]

      @model_validator(mode="after")
      def classes_are_disjoint(self) -> SuiteManifest:
          groups = {
              "development": set(self.task_ids("development")),
              "confirmation": set(self.task_ids("confirmation")),
              "spine": set(self.task_ids("spine")),
          }
          for left, right in (
              ("development", "confirmation"),
              ("development", "spine"),
              ("confirmation", "spine"),
          ):
              overlap = sorted(groups[left] & groups[right])
              if overlap:
                  raise ValueError(f"suite classes overlap {left}/{right}: {overlap}")
          return self

      def task_ids(self, suite_class: SuiteClass) -> tuple[str, ...]:
          return tuple(member.task_id for member in getattr(self, suite_class))
  ```

- [ ] **Step 5: Implement deterministic schema export, including the critic contract.** Create `research/der/contracts/schema_export.py`:

  ```python
  """Deterministically export repository wire schemas."""

  from __future__ import annotations

  import json
  from pathlib import Path
  from typing import Annotated, Literal

  from pydantic import Field

  from research.der.contracts.base import StrictModel
  from research.der.contracts.eval import EvalResult, EvalSpec, ExperimentId, Sha256
  from research.der.contracts.experiment import ExperimentContract, ExperimentFrontMatter
  from research.der.contracts.scorecard import Scorecard
  from research.der.contracts.suite import SuiteManifest


  class CriticCandidate(StrictModel):
      slug: Annotated[str, Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")]
      title: str
      contract: ExperimentContract
      proposed_changes: tuple[str, ...]
      evidence_refs: tuple[str, ...]


  class CriticProposal(StrictModel):
      schema_version: Literal["der.critic-proposal.v1"] = "der.critic-proposal.v1"
      source_experiment_id: ExperimentId
      critique: str
      candidates: tuple[CriticCandidate, ...]
      evidence_digest: Sha256


  SCHEMAS = {
      "eval-spec.schema.json": EvalSpec,
      "eval-result.schema.json": EvalResult,
      "scorecard.schema.json": Scorecard,
      "experiment-frontmatter.schema.json": ExperimentFrontMatter,
      "suite.schema.json": SuiteManifest,
      "critic-proposal.schema.json": CriticProposal,
  }


  def export_schemas(output_dir: Path) -> None:
      output_dir.mkdir(parents=True, exist_ok=True)
      for filename, model in SCHEMAS.items():
          payload = json.dumps(
              model.model_json_schema(),
              sort_keys=True,
              indent=2,
              ensure_ascii=False,
          ) + "\n"
          (output_dir / filename).write_text(payload, encoding="utf-8")


  def schemas_match(output_dir: Path) -> bool:
      import tempfile

      with tempfile.TemporaryDirectory() as temporary:
          generated = Path(temporary)
          export_schemas(generated)
          return all(
              (output_dir / name).is_file()
              and (output_dir / name).read_bytes() == (generated / name).read_bytes()
              for name in SCHEMAS
          )
  ```

- [ ] **Step 6: Add the schema CLI without placing schema logic in the command layer.** Append these imports and command to `research/der/cli.py`:

  ```python
  from research.der.contracts.schema_export import export_schemas, schemas_match

  schemas_app = typer.Typer(no_args_is_help=True)
  app.add_typer(schemas_app, name="schemas")


  @schemas_app.command("generate")
  def generate_schemas(
      output_dir: Path = typer.Option(Path("research/schemas"), "--output-dir"),
      check: bool = typer.Option(False, "--check"),
  ) -> None:
      """Generate or byte-check all public JSON schemas."""
      if check:
          if not schemas_match(output_dir):
              typer.echo("generated schemas differ; run der schemas generate", err=True)
              raise typer.Exit(code=1)
          typer.echo("schemas are current")
          return
      export_schemas(output_dir)
      typer.echo(f"wrote schemas to {output_dir}")
  ```

  Place the new import with the other imports and the app registration before command decorators; do not duplicate `app`.

- [ ] **Step 7: Generate schemas and run the contract suite.** Run:

  ```bash
  uv run der schemas generate
  uv run der schemas generate --check
  uv run pytest tests/contracts -q
  uv run ruff check research/der/contracts research/der/cli.py tests/contracts
  uv run mypy research/der
  ```

  Expected output includes `wrote schemas to research/schemas`, `schemas are current`, all contract tests pass, and static checks print no diagnostics.

- [ ] **Step 8: Prove unknown fields and secret-like fields are rejected by the schemas.** Run:

  ```bash
  uv run python - <<'PY'
  import json
  from pathlib import Path

  schema = json.loads(Path("research/schemas/eval-spec.schema.json").read_text())
  assert schema["additionalProperties"] is False
  serialized = json.dumps(schema).lower()
  assert "api_key" not in serialized
  assert "provider_key" not in serialized
  print("strict eval schema contains no provider credential field")
  PY
  ```

  Expected output is exactly `strict eval schema contains no provider credential field`.

- [ ] **Step 9: Commit.** Run:

  ```bash
  git add \
    research/der/contracts research/der/cli.py research/schemas \
    tests/contracts
  git commit -m "feat: define strict evaluation and experiment contracts"
  ```

### Task 3: Compute Git tree identity and runtime-manifest digests

**Files:**
- Create: `research/der/util/__init__.py`
- Create: `research/der/util/hashing.py`
- Create: `research/der/util/git.py`
- Create: `research/der/harness/__init__.py`
- Create: `research/der/harness/identity.py`
- Create: `tests/harness/test_identity.py`
- Create: `tests/fixtures/harness/identity/QWEN.md`
- Create: `tests/fixtures/harness/identity/.qwen/settings.json`

**Interfaces:**
- Consumes: `HarnessIdentity` and `RuntimeManifest` from Task 2; a clean repository path and an explicit harness directory.
- Produces: `git_tree_oid(repo_root: Path, directory: Path) -> str`, `runtime_manifest_digest(manifest: RuntimeManifest) -> str`, `compute_identity(repo_root: Path, harness_dir: Path, manifest: RuntimeManifest) -> HarnessIdentity`.

- [ ] **Step 1: Create the identity fixture.** Create `tests/fixtures/harness/identity/QWEN.md` containing:

  ```markdown
  # Fixture harness

  Inspect the repository before editing.
  ```

  Create `tests/fixtures/harness/identity/.qwen/settings.json` containing:

  ```json
  {}
  ```

- [ ] **Step 2: Write the failing identity tests.** Create `tests/harness/test_identity.py`:

  ```python
  import shutil
  import subprocess
  from pathlib import Path

  from research.der.contracts.eval import RuntimeManifest
  from research.der.harness.identity import compute_identity, runtime_manifest_digest
  from research.der.util.git import git_tree_oid


  def run(repo: Path, *args: str) -> str:
      return subprocess.run(
          [*args], cwd=repo, check=True, text=True, stdout=subprocess.PIPE
      ).stdout.strip()


  def make_repo(tmp_path: Path) -> tuple[Path, Path]:
      repo = tmp_path / "repo"
      harness = repo / "harness"
      shutil.copytree("tests/fixtures/harness/identity", harness)
      run(repo.parent, "git", "init", str(repo))
      run(repo, "git", "config", "user.email", "tests@der.invalid")
      run(repo, "git", "config", "user.name", "der tests")
      run(repo, "git", "add", "harness")
      run(repo, "git", "commit", "-m", "fixture")
      return repo, harness


  def manifest() -> RuntimeManifest:
      return RuntimeManifest(
          pier_commit="a" * 40,
          deep_swe_commit="b" * 40,
          task_revisions={"task-a": "c" * 64},
          qwen_archive_sha256="d" * 64,
          der_agent_revision="e" * 40,
          proxy_policy_id="deepseek-v4-pro-v1",
          qwen_system_policy_sha256="f" * 64,
      )


  def test_directory_oid_matches_git_committed_tree(tmp_path: Path) -> None:
      repo, harness = make_repo(tmp_path)

      calculated = git_tree_oid(repo, harness)
      committed = run(repo, "git", "rev-parse", "HEAD:harness")

      assert calculated == committed


  def test_content_and_mode_both_change_tree_oid(tmp_path: Path) -> None:
      repo, harness = make_repo(tmp_path)
      original = git_tree_oid(repo, harness)

      qwen = harness / "QWEN.md"
      qwen.write_text(qwen.read_text() + "One more rule.\n", encoding="utf-8")
      content_changed = git_tree_oid(repo, harness)
      qwen.chmod(0o755)
      mode_changed = git_tree_oid(repo, harness)

      assert len({original, content_changed, mode_changed}) == 3


  def test_runtime_manifest_digest_is_canonical_and_sensitive() -> None:
      first = manifest()
      reordered = RuntimeManifest.model_validate(
          dict(reversed(list(first.model_dump(mode="json").items())))
      )
      changed = first.model_copy(update={"proxy_policy_id": "deepseek-v4-pro-v2"})

      assert runtime_manifest_digest(first) == runtime_manifest_digest(reordered)
      assert runtime_manifest_digest(first) != runtime_manifest_digest(changed)


  def test_compute_identity_uses_head_source_and_explicit_harness(tmp_path: Path) -> None:
      repo, harness = make_repo(tmp_path)

      identity = compute_identity(repo, harness, manifest())

      assert identity.source_commit == run(repo, "git", "rev-parse", "HEAD")
      assert identity.harness_tree_oid == run(repo, "git", "rev-parse", "HEAD:harness")
      assert identity.runtime_manifest_digest == runtime_manifest_digest(manifest())
  ```

- [ ] **Step 3: Run the tests to observe the missing identity modules.** Run:

  ```bash
  uv run pytest tests/harness/test_identity.py -q
  ```

  Expected failure includes `ModuleNotFoundError: No module named 'research.der.harness'`.

- [ ] **Step 4: Implement canonical hashes and checked Git commands.** Create empty `research/der/util/__init__.py`. Create `research/der/util/hashing.py`:

  ```python
  """Content hashing helpers."""

  from __future__ import annotations

  import hashlib
  from pathlib import Path


  def sha256_bytes(data: bytes) -> str:
      return hashlib.sha256(data).hexdigest()


  def sha256_file(path: Path) -> str:
      digest = hashlib.sha256()
      with path.open("rb") as handle:
          for chunk in iter(lambda: handle.read(1024 * 1024), b""):
              digest.update(chunk)
      return digest.hexdigest()
  ```

  Create `research/der/util/git.py`:

  ```python
  """Small checked Git interface; no shell command strings."""

  from __future__ import annotations

  import os
  import subprocess
  from pathlib import Path


  def git(repo_root: Path, *args: str, input_text: str | None = None) -> str:
      completed = subprocess.run(
          ["git", "-C", str(repo_root), *args],
          input=input_text,
          check=True,
          text=True,
          stdout=subprocess.PIPE,
          stderr=subprocess.PIPE,
      )
      return completed.stdout.strip()


  def head_commit(repo_root: Path) -> str:
      return git(repo_root, "rev-parse", "HEAD")


  def _blob_oid(repo_root: Path, path: Path) -> str:
      return git(repo_root, "hash-object", "-w", "--", str(path))


  def _tree_oid(repo_root: Path, directory: Path) -> str:
      rows: list[str] = []
      for item in sorted(directory.iterdir(), key=lambda value: value.name.encode("utf-8")):
          if "\n" in item.name or "\t" in item.name:
              raise ValueError(f"Git identity rejects newline/tab in path: {item}")
          if item.is_symlink():
              target = os.readlink(item).encode("utf-8")
              oid = git(repo_root, "hash-object", "-w", "--stdin", input_text=target.decode())
              rows.append(f"120000 blob {oid}\t{item.name}")
          elif item.is_dir():
              rows.append(f"040000 tree {_tree_oid(repo_root, item)}\t{item.name}")
          elif item.is_file():
              executable = bool(item.stat().st_mode & 0o111)
              mode = "100755" if executable else "100644"
              rows.append(f"{mode} blob {_blob_oid(repo_root, item)}\t{item.name}")
          else:
              raise ValueError(f"unsupported harness filesystem entry: {item}")
      payload = "\n".join(rows) + ("\n" if rows else "")
      return git(repo_root, "mktree", input_text=payload)


  def git_tree_oid(repo_root: Path, directory: Path) -> str:
      resolved_repo = repo_root.resolve()
      resolved_directory = directory.resolve()
      if not resolved_directory.is_dir():
          raise ValueError(f"harness directory does not exist: {directory}")
      if not resolved_directory.is_relative_to(resolved_repo):
          raise ValueError(f"harness directory is outside repository: {directory}")
      return _tree_oid(resolved_repo, resolved_directory)
  ```

  Note: `git hash-object -w` and `git mktree` add content-addressed objects but do not alter the index, worktree, branch, or commits. This is the correct way to obtain a Git tree OID for an uncommitted candidate directory.

- [ ] **Step 5: Implement identity computation.** Create empty `research/der/harness/__init__.py`. Create `research/der/harness/identity.py`:

  ```python
  """Three-part harness and runtime identity."""

  from __future__ import annotations

  from pathlib import Path

  from research.der.contracts.base import canonical_json_bytes
  from research.der.contracts.eval import HarnessIdentity, RuntimeManifest
  from research.der.util.git import git_tree_oid, head_commit
  from research.der.util.hashing import sha256_bytes


  def runtime_manifest_digest(manifest: RuntimeManifest) -> str:
      return sha256_bytes(canonical_json_bytes(manifest))


  def compute_identity(
      repo_root: Path,
      harness_dir: Path,
      manifest: RuntimeManifest,
  ) -> HarnessIdentity:
      return HarnessIdentity(
          source_commit=head_commit(repo_root),
          harness_tree_oid=git_tree_oid(repo_root, harness_dir),
          runtime_manifest_digest=runtime_manifest_digest(manifest),
      )
  ```

- [ ] **Step 6: Run identity tests and static checks.** Run:

  ```bash
  uv run pytest tests/harness/test_identity.py -q
  uv run ruff check research/der/util research/der/harness tests/harness/test_identity.py
  uv run mypy research/der
  ```

  Expected output: `4 passed`; no static-check diagnostics.

- [ ] **Step 7: Commit.** Run:

  ```bash
  git add \
    research/der/util research/der/harness \
    tests/harness/test_identity.py tests/fixtures/harness/identity
  git commit -m "feat: compute harness tree and runtime identity"
  ```

### Task 4: Parse lifecycle records and enforce frozen, disjoint suites

**Files:**
- Create: `research/der/util/atomic.py`
- Create: `research/der/util/time.py`
- Create: `research/der/experiments/__init__.py`
- Create: `research/der/experiments/records.py`
- Create: `research/der/suites/__init__.py`
- Create: `research/der/suites/manifest.py`
- Create: `research/der/suites/disjoint.py`
- Create: `research/templates/experiment.md`
- Create: `tests/experiments/test_records.py`
- Create: `tests/suites/test_manifest.py`
- Create: `tests/fixtures/experiments/EXP-0001-navigation.md`
- Create: `tests/fixtures/suites/suite-v1.toml`
- Create: `tests/fixtures/suites/suite-v2-overlap.toml`

**Interfaces:**
- Consumes: `ExperimentFrontMatter`, lifecycle transition graph, and `SuiteManifest` from Task 2.
- Produces: `read_record(path) -> ExperimentRecord`, `create_record(path, front_matter, body)`, `transition_record(path, target, ...)`, `load_suite(path) -> SuiteManifest`, `assert_all_suites_disjoint(paths) -> None`; atomic text replacement with directory fsync.

- [ ] **Step 1: Write the lifecycle fixture.** Create `tests/fixtures/experiments/EXP-0001-navigation.md`:

  ```markdown
  ---
  schema_version: der.experiment.v1
  experiment_id: EXP-0001-navigation
  slug: navigation
  title: Narrow repository navigation skill
  status: proposed
  created_at: '2026-07-21T12:00:00Z'
  updated_at: '2026-07-21T12:00:00Z'
  baseline_identity:
    source_commit: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
    harness_tree_oid: bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
    runtime_manifest_digest: cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc
  candidate_identity:
    source_commit: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
    harness_tree_oid: dddddddddddddddddddddddddddddddddddddddd
    runtime_manifest_digest: cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc
  contract:
    hypothesis: A narrower repository-navigation skill improves confirmation performance.
    primary_metric: confirmation_macro_pass_at_1
    minimum_effect: '0.02'
    guardrails:
      - metric: invalid_fraction
        operator: <=
        threshold: '0.05'
    falsifier: Reject when the confirmation effect is below 0.02 or a guardrail fails.
    suite_version: deepswe-v1
    k: 1
    budget:
      max_cost_usd: '20'
      max_wall_seconds: 3600
      max_attempts: 10
      max_input_tokens: 1000000
      max_output_tokens: 200000
      max_tool_calls: 500
      max_session_turns: 50
  run_ids: []
  terminal_reason: null
  adopted_at: null
  executable_acknowledged: false
  ---
  # EXP-0001 — Narrow repository navigation skill

  ## Rationale

  This record exists before execution.
  ```

- [ ] **Step 2: Write suite fixtures using real-shaped but fixture-only IDs.** Create `tests/fixtures/suites/suite-v1.toml`:

  ```toml
  schema_version = "der.suite.v1"
  version = "deepswe-v1"
  deep_swe_commit = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
  reporting_k = 5
  frozen = true

  [[development]]
  task_id = "fixture-dev"
  task_checksum = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"

  [[confirmation]]
  task_id = "fixture-confirm"
  task_checksum = "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"

  [[spine]]
  task_id = "fixture-spine"
  task_checksum = "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd"
  ```

  Create `tests/fixtures/suites/suite-v2-overlap.toml` with the same scalar header except `version = "deepswe-v2"`; put `fixture-confirm` in its `development` class, `fixture-v2-confirm` in confirmation, and `fixture-v2-spine` in spine, with valid 64-character lowercase hex checksums. This fixture represents cross-version confirmation leakage and must be rejected by the directory-level check.

- [ ] **Step 3: Write the failing record and suite tests.** Create `tests/experiments/test_records.py`:

  ```python
  import shutil
  from datetime import UTC, datetime
  from pathlib import Path

  import pytest

  from research.der.contracts.experiment import ExperimentStatus
  from research.der.experiments.records import read_record, transition_record


  FIXTURE = Path("tests/fixtures/experiments/EXP-0001-navigation.md")


  def test_front_matter_round_trip_preserves_body(tmp_path: Path) -> None:
      target = tmp_path / FIXTURE.name
      shutil.copy2(FIXTURE, target)

      record = read_record(target)

      assert record.front_matter.experiment_id == "EXP-0001-navigation"
      assert record.front_matter.status is ExperimentStatus.PROPOSED
      assert record.body.startswith("# EXP-0001")
      rendered = tmp_path / "rendered.md"
      rendered.write_text(record.render(), encoding="utf-8")
      reparsed = read_record(rendered)
      assert reparsed.front_matter == record.front_matter
      assert reparsed.body == record.body


  def test_transition_is_atomic_and_records_run(tmp_path: Path) -> None:
      target = tmp_path / FIXTURE.name
      shutil.copy2(FIXTURE, target)
      before_inode = target.stat().st_ino

      transition_record(
          target,
          target=ExperimentStatus.RUNNING,
          now=datetime(2026, 7, 21, 13, tzinfo=UTC),
          append_run_id="RUN-EXP-0001-navigation-development-01",
      )
      record = read_record(target)

      assert record.front_matter.status is ExperimentStatus.RUNNING
      assert record.front_matter.run_ids == (
          "RUN-EXP-0001-navigation-development-01",
      )
      assert target.stat().st_ino != before_inode


  def test_forbidden_transition_does_not_change_bytes(tmp_path: Path) -> None:
      target = tmp_path / FIXTURE.name
      shutil.copy2(FIXTURE, target)
      before = target.read_bytes()

      with pytest.raises(ValueError, match="forbidden lifecycle transition"):
          transition_record(
              target,
              target=ExperimentStatus.ADOPTED,
              now=datetime(2026, 7, 21, 13, tzinfo=UTC),
              terminal_reason="not run",
          )

      assert target.read_bytes() == before
  ```

  Create `tests/suites/test_manifest.py`:

  ```python
  from pathlib import Path

  import pytest

  from research.der.suites.disjoint import assert_all_suites_disjoint
  from research.der.suites.manifest import load_suite


  FIXTURES = Path("tests/fixtures/suites")


  def test_load_frozen_suite() -> None:
      suite = load_suite(FIXTURES / "suite-v1.toml")

      assert suite.version == "deepswe-v1"
      assert suite.task_ids("confirmation") == ("fixture-confirm",)


  def test_confirmation_task_cannot_appear_in_any_other_version_class() -> None:
      with pytest.raises(ValueError, match="confirmation task fixture-confirm"):
          assert_all_suites_disjoint(
              [FIXTURES / "suite-v1.toml", FIXTURES / "suite-v2-overlap.toml"]
          )
  ```

- [ ] **Step 4: Run the tests to see the missing record/suite modules.** Run:

  ```bash
  uv run pytest tests/experiments/test_records.py tests/suites/test_manifest.py -q
  ```

  Expected failure includes `ModuleNotFoundError` for `research.der.experiments` or `research.der.suites`.

- [ ] **Step 5: Implement atomic replacement and an injectable UTC clock.** Create `research/der/util/atomic.py`:

  ```python
  """Durable exclusive creation and atomic replacement."""

  from __future__ import annotations

  import os
  import tempfile
  from pathlib import Path

  from research.der.errors import ImmutableArtifactError


  def _fsync_directory(path: Path) -> None:
      descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
      try:
          os.fsync(descriptor)
      finally:
          os.close(descriptor)


  def atomic_replace_bytes(path: Path, data: bytes, mode: int = 0o644) -> None:
      path.parent.mkdir(parents=True, exist_ok=True)
      descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
      temporary = Path(temporary_name)
      try:
          os.fchmod(descriptor, mode)
          with os.fdopen(descriptor, "wb") as handle:
              handle.write(data)
              handle.flush()
              os.fsync(handle.fileno())
          os.replace(temporary, path)
          _fsync_directory(path.parent)
      finally:
          temporary.unlink(missing_ok=True)


  def create_exclusive_bytes(path: Path, data: bytes, mode: int = 0o644) -> None:
      path.parent.mkdir(parents=True, exist_ok=True)
      try:
          descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
      except FileExistsError as exc:
          raise ImmutableArtifactError(f"immutable artifact already exists: {path}") from exc
      try:
          with os.fdopen(descriptor, "wb") as handle:
              handle.write(data)
              handle.flush()
              os.fsync(handle.fileno())
          _fsync_directory(path.parent)
      except Exception:
          path.unlink(missing_ok=True)
          raise
  ```

  Create `research/der/util/time.py`:

  ```python
  """UTC time source."""

  from datetime import UTC, datetime


  def utc_now() -> datetime:
      return datetime.now(UTC)
  ```

- [ ] **Step 6: Implement strict lifecycle Markdown parsing and transitions.** Create empty `research/der/experiments/__init__.py`. Create `research/der/experiments/records.py`:

  ```python
  """Lifecycle Markdown persistence."""

  from __future__ import annotations

  from dataclasses import dataclass
  from datetime import datetime
  from pathlib import Path
  from typing import Any, cast

  import yaml

  from research.der.contracts.eval import RunId
  from research.der.contracts.experiment import (
      ExperimentFrontMatter,
      ExperimentStatus,
      assert_transition,
  )
  from research.der.util.atomic import atomic_replace_bytes, create_exclusive_bytes


  @dataclass(frozen=True, slots=True)
  class ExperimentRecord:
      path: Path
      front_matter: ExperimentFrontMatter
      body: str

      def render(self) -> str:
          dumped = yaml.safe_dump(
              self.front_matter.model_dump(mode="json", exclude_none=False),
              sort_keys=False,
              allow_unicode=True,
          ).rstrip()
          return f"---\n{dumped}\n---\n{self.body}"


  def _split(text: str, path: Path) -> tuple[dict[str, Any], str]:
      lines = text.splitlines(keepends=True)
      if not lines or lines[0].rstrip("\n") != "---":
          raise ValueError(f"{path}: missing opening front-matter delimiter")
      end = next(
          (index for index, line in enumerate(lines[1:], start=1) if line.rstrip("\n") == "---"),
          None,
      )
      if end is None:
          raise ValueError(f"{path}: missing closing front-matter delimiter")
      front = yaml.safe_load("".join(lines[1:end]))
      if not isinstance(front, dict):
          raise ValueError(f"{path}: front matter must be a mapping")
      return cast(dict[str, Any], front), "".join(lines[end + 1 :])


  def read_record(path: Path) -> ExperimentRecord:
      front, body = _split(path.read_text(encoding="utf-8"), path)
      model = ExperimentFrontMatter.model_validate(front)
      expected_name = f"{model.experiment_id}.md"
      if path.name != expected_name:
          raise ValueError(f"record filename must be {expected_name}, found {path.name}")
      return ExperimentRecord(path=path, front_matter=model, body=body)


  def create_record(path: Path, front_matter: ExperimentFrontMatter, body: str) -> None:
      record = ExperimentRecord(path=path, front_matter=front_matter, body=body)
      create_exclusive_bytes(path, record.render().encode("utf-8"))


  def transition_record(
      path: Path,
      *,
      target: ExperimentStatus,
      now: datetime,
      append_run_id: RunId | None = None,
      terminal_reason: str | None = None,
      adopted_at: datetime | None = None,
      executable_acknowledged: bool | None = None,
  ) -> ExperimentRecord:
      current = read_record(path)
      assert_transition(current.front_matter.status, target)
      run_ids = current.front_matter.run_ids
      if append_run_id is not None:
          if append_run_id in run_ids:
              raise ValueError(f"run id already recorded: {append_run_id}")
          run_ids = (*run_ids, append_run_id)
      values: dict[str, Any] = {
          **current.front_matter.model_dump(),
          "status": target,
          "updated_at": now,
          "run_ids": run_ids,
          "terminal_reason": terminal_reason,
          "adopted_at": adopted_at,
      }
      if executable_acknowledged is not None:
          values["executable_acknowledged"] = executable_acknowledged
      updated = ExperimentFrontMatter.model_validate(values)
      record = ExperimentRecord(path=path, front_matter=updated, body=current.body)
      atomic_replace_bytes(path, record.render().encode("utf-8"))
      return record
  ```

- [ ] **Step 7: Implement suite loading and cross-version leak checks.** Create empty `research/der/suites/__init__.py`. Create `research/der/suites/manifest.py`:

  ```python
  """Frozen suite TOML loading."""

  from __future__ import annotations

  import tomllib
  from pathlib import Path

  from research.der.contracts.suite import SuiteManifest


  def load_suite(path: Path) -> SuiteManifest:
      if not path.is_file():
          raise ValueError(f"suite manifest does not exist: {path}")
      return SuiteManifest.model_validate(tomllib.loads(path.read_text(encoding="utf-8")))
  ```

  Create `research/der/suites/disjoint.py`:

  ```python
  """Pairwise suite disjointness and confirmation leak controls."""

  from __future__ import annotations

  from collections import defaultdict
  from pathlib import Path

  from research.der.suites.manifest import load_suite


  def assert_all_suites_disjoint(paths: list[Path]) -> None:
      manifests = [load_suite(path) for path in paths]
      occurrences: dict[str, list[tuple[str, str]]] = defaultdict(list)
      for manifest in manifests:
          for suite_class in ("development", "confirmation", "spine"):
              for task_id in manifest.task_ids(suite_class):
                  occurrences[task_id].append((manifest.version, suite_class))
      for task_id, places in sorted(occurrences.items()):
          confirmation_places = [place for place in places if place[1] == "confirmation"]
          if confirmation_places and len(places) > 1:
              raise ValueError(
                  f"confirmation task {task_id} appears outside its one confirmation set: {places}"
              )
          by_version: dict[str, list[str]] = defaultdict(list)
          for version, suite_class in places:
              by_version[version].append(suite_class)
          for version, classes in by_version.items():
              if len(classes) > 1:
                  raise ValueError(
                      f"task {task_id} appears in multiple classes for {version}: {classes}"
                  )
  ```

- [ ] **Step 8: Create the lifecycle template.** Create `research/templates/experiment.md`:

  ```markdown
  ---
  schema_version: der.experiment.v1
  experiment_id: EXP-0001-example
  slug: example
  title: Example preregistered experiment
  status: proposed
  created_at: '2026-07-21T00:00:00Z'
  updated_at: '2026-07-21T00:00:00Z'
  baseline_identity:
    source_commit: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
    harness_tree_oid: bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
    runtime_manifest_digest: cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc
  candidate_identity:
    source_commit: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
    harness_tree_oid: dddddddddddddddddddddddddddddddddddddddd
    runtime_manifest_digest: cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc
  contract:
    hypothesis: State one causal harness hypothesis in at least twenty characters.
    primary_metric: confirmation_macro_pass_at_1
    minimum_effect: '0.02'
    guardrails:
      - metric: invalid_fraction
        operator: <=
        threshold: '0.05'
    falsifier: State the concrete observation that rejects this hypothesis.
    suite_version: deepswe-v1
    k: 1
    budget:
      max_cost_usd: '20'
      max_wall_seconds: 3600
      max_attempts: 24
      max_input_tokens: 1000000
      max_output_tokens: 200000
      max_tool_calls: 500
      max_session_turns: 50
  run_ids: []
  terminal_reason: null
  adopted_at: null
  executable_acknowledged: false
  ---
  # EXP-0001 — Example preregistered experiment

  ## Causal rationale

  Explain why the proposed harness change should move the primary metric.

  ## Exact candidate change

  Name each managed path and the intended semantic change. This section is fixed before execution.

  ## Evidence links

  The finalizer appends exact run and scorecard paths here.
  ```

  The values in this template are valid examples, not live experiment state; the CLI in Task 16 generates real identifiers and identities.

- [ ] **Step 9: Run the record and suite tests.** Run:

  ```bash
  uv run pytest tests/experiments/test_records.py tests/suites/test_manifest.py -q
  uv run ruff check research/der/experiments research/der/suites research/der/util tests/experiments tests/suites
  uv run mypy research/der
  ```

  Expected output: `5 passed`; no static-check diagnostics.

- [ ] **Step 10: Commit.** Run:

  ```bash
  git add \
    research/der/util/atomic.py research/der/util/time.py \
    research/der/experiments research/der/suites research/templates/experiment.md \
    tests/experiments tests/suites tests/fixtures/experiments tests/fixtures/suites
  git commit -m "feat: persist experiment lifecycle and frozen suites"
  ```

### Task 5: Define the owner model policy and atomic RunBudget ledger

**Files:**
- Create: `research/config/runtime-policy.toml`
- Create: `research/der/proxy/__init__.py`
- Create: `research/der/proxy/policy.py`
- Create: `research/der/proxy/budget.py`
- Create: `tests/proxy/test_policy.py`
- Create: `tests/proxy/test_budget.py`

**Interfaces:**
- Consumes: `RunBudget`; owner policy ID `deepseek-v4-pro-v1`.
- Produces: `ModelPolicy.prepare_request(payload) -> PreparedRequest`, `BudgetLedger.register_run(...)`, `BudgetLedger.authorize_request(...)`, `BudgetLedger.reconcile_response(...)`, and stable `BudgetExceededError` reasons consumed by the proxy and watchdog.

- [ ] **Step 1: Write the immutable owner policy.** Create `research/config/runtime-policy.toml`:

  ```toml
  schema_version = "der.runtime-policy.v1"
  policy_id = "deepseek-v4-pro-v1"
  provider = "deepseek"
  model = "deepseek-v4-pro"
  provider_base_url_env = "DEEPSEEK_BASE_URL"
  provider_api_key_env = "DEEPSEEK_API_KEY"
  observation_log = "/var/lib/der/proxy/observations.jsonl"
  registry_dir = "/run/der/proxy-runs"
  budget_dir = "/var/lib/der/proxy/budgets"

  [qwen]
  max_iterations = 10
  max_wall_seconds = 3600
  max_tool_calls = 500
  max_session_turns = 50
  best_of_n = false
  explore = false
  ```

  The policy file names environment variables but contains no secret or provider credential value.

- [ ] **Step 2: Write failing policy tests.** Create `tests/proxy/test_policy.py`:

  ```python
  import pytest

  from research.der.errors import PolicyViolationError
  from research.der.proxy.policy import ModelPolicy


  POLICY = ModelPolicy(
      policy_id="deepseek-v4-pro-v1",
      provider="deepseek",
      model="deepseek-v4-pro",
  )


  def test_missing_model_is_pinned_and_client_authorization_is_removed() -> None:
      prepared = POLICY.prepare_request(
          {"messages": [{"role": "user", "content": "hello"}]},
          inbound_headers={"authorization": "Bearer run-token", "x-request-id": "r1"},
      )

      assert prepared.payload["model"] == "deepseek-v4-pro"
      assert prepared.requested_model is None
      assert "authorization" not in prepared.forward_headers
      assert prepared.forward_headers["x-request-id"] == "r1"


  def test_matching_model_is_accepted_and_observed() -> None:
      prepared = POLICY.prepare_request(
          {"model": "deepseek-v4-pro", "messages": []}, inbound_headers={}
      )

      assert prepared.requested_model == "deepseek-v4-pro"
      assert prepared.payload["model"] == "deepseek-v4-pro"


  def test_mismatched_model_fails_closed() -> None:
      with pytest.raises(PolicyViolationError, match="requested model other-model"):
          POLICY.prepare_request(
              {"model": "other-model", "messages": []}, inbound_headers={}
          )


  @pytest.mark.parametrize("field", ["api_key", "apiKey", "provider_key"])
  def test_request_body_cannot_smuggle_provider_credentials(field: str) -> None:
      with pytest.raises(PolicyViolationError, match=field):
          POLICY.prepare_request({field: "secret", "messages": []}, inbound_headers={})
  ```

- [ ] **Step 3: Write failing budget-ledger tests.** Create `tests/proxy/test_budget.py`:

  ```python
  from datetime import UTC, datetime, timedelta
  from decimal import Decimal
  from pathlib import Path

  import pytest

  from research.der.contracts.eval import RunBudget, TokenUsage
  from research.der.proxy.budget import BudgetExceededError, BudgetLedger


  NOW = datetime(2026, 7, 21, 12, tzinfo=UTC)


  def budget() -> RunBudget:
      return RunBudget(
          max_cost_usd=Decimal("1.00"),
          max_wall_seconds=60,
          max_attempts=2,
          max_input_tokens=100,
          max_output_tokens=50,
          max_tool_calls=10,
          max_session_turns=5,
      )


  def test_register_authorize_and_reconcile_are_persistent(tmp_path: Path) -> None:
      ledger = BudgetLedger(tmp_path)
      ledger.register_run("RUN-1", budget(), NOW, expected_attempts=2)

      ledger.authorize_request("RUN-1", "req-1", NOW)
      snapshot = ledger.reconcile_response(
          "RUN-1",
          "req-1",
          usage=TokenUsage(input_tokens=20, output_tokens=5),
          cost_usd=Decimal("0.20"),
          now=NOW + timedelta(seconds=2),
      )
      reloaded = BudgetLedger(tmp_path).snapshot("RUN-1")

      assert snapshot == reloaded
      assert reloaded.cost_usd == Decimal("0.20")
      assert reloaded.input_tokens == 20
      assert reloaded.active_request_ids == ()


  def test_duplicate_request_id_is_rejected_without_mutation(tmp_path: Path) -> None:
      ledger = BudgetLedger(tmp_path)
      ledger.register_run("RUN-1", budget(), NOW, expected_attempts=2)
      ledger.authorize_request("RUN-1", "req-1", NOW)
      before = ledger.snapshot("RUN-1")

      with pytest.raises(ValueError, match="already active"):
          ledger.authorize_request("RUN-1", "req-1", NOW)

      assert ledger.snapshot("RUN-1") == before


  @pytest.mark.parametrize(
      ("delta", "reason"),
      [
          ({"cost_usd": Decimal("1.01")}, "max_cost_usd"),
          ({"input_tokens": 101}, "max_input_tokens"),
          ({"output_tokens": 51}, "max_output_tokens"),
          ({"tool_calls": 11}, "max_tool_calls"),
          ({"session_turns": 6}, "max_session_turns"),
      ],
  )
  def test_ceiling_is_fail_closed_and_sticky(
      tmp_path: Path, delta: dict[str, object], reason: str
  ) -> None:
      ledger = BudgetLedger(tmp_path)
      ledger.register_run("RUN-1", budget(), NOW, expected_attempts=2)
      usage = TokenUsage(
          input_tokens=int(delta.get("input_tokens", 0)),
          output_tokens=int(delta.get("output_tokens", 0)),
          tool_calls=int(delta.get("tool_calls", 0)),
          session_turns=int(delta.get("session_turns", 0)),
      )
      ledger.authorize_request("RUN-1", "req-1", NOW)

      with pytest.raises(BudgetExceededError, match=reason):
          ledger.reconcile_response(
              "RUN-1",
              "req-1",
              usage=usage,
              cost_usd=Decimal(delta.get("cost_usd", 0)),
              now=NOW,
          )
      assert ledger.snapshot("RUN-1").ceiling_reason == reason
      with pytest.raises(BudgetExceededError, match=reason):
          ledger.authorize_request("RUN-1", "req-2", NOW)


  def test_wall_clock_and_attempt_registration_are_enforced(tmp_path: Path) -> None:
      ledger = BudgetLedger(tmp_path)
      with pytest.raises(ValueError, match="expected_attempts"):
          ledger.register_run("RUN-1", budget(), NOW, expected_attempts=3)
      ledger.register_run("RUN-2", budget(), NOW, expected_attempts=2)
      with pytest.raises(BudgetExceededError, match="max_wall_seconds"):
          ledger.authorize_request("RUN-2", "req", NOW + timedelta(seconds=61))
  ```

- [ ] **Step 4: Run tests to observe missing proxy modules.** Run:

  ```bash
  uv run pytest tests/proxy/test_policy.py tests/proxy/test_budget.py -q
  ```

  Expected failure includes `ModuleNotFoundError: No module named 'research.der.proxy'`.

- [ ] **Step 5: Implement strict model pinning and request sanitation.** Create empty `research/der/proxy/__init__.py`. Create `research/der/proxy/policy.py`:

  ```python
  """Owner-only provider and model request policy."""

  from __future__ import annotations

  import copy
  from dataclasses import dataclass
  from typing import Any, Mapping

  from research.der.errors import PolicyViolationError

  CREDENTIAL_BODY_FIELDS = {"api_key", "apiKey", "provider_key", "authorization"}
  FORWARD_HEADER_ALLOWLIST = {
      "accept",
      "content-type",
      "x-request-id",
      "x-stainless-arch",
      "x-stainless-lang",
      "x-stainless-os",
      "x-stainless-package-version",
      "x-stainless-runtime",
      "x-stainless-runtime-version",
  }


  @dataclass(frozen=True, slots=True)
  class PreparedRequest:
      payload: dict[str, Any]
      forward_headers: dict[str, str]
      requested_model: str | None


  @dataclass(frozen=True, slots=True)
  class ModelPolicy:
      policy_id: str
      provider: str
      model: str

      def prepare_request(
          self,
          payload: Mapping[str, Any],
          *,
          inbound_headers: Mapping[str, str],
      ) -> PreparedRequest:
          forbidden = sorted(CREDENTIAL_BODY_FIELDS & payload.keys())
          if forbidden:
              raise PolicyViolationError(
                  f"request body contains forbidden credential field: {forbidden[0]}"
              )
          prepared = copy.deepcopy(dict(payload))
          requested = prepared.get("model")
          if requested is not None and requested != self.model:
              raise PolicyViolationError(
                  f"requested model {requested!s} does not match pinned model {self.model}"
              )
          prepared["model"] = self.model
          headers = {
              key.lower(): value
              for key, value in inbound_headers.items()
              if key.lower() in FORWARD_HEADER_ALLOWLIST
          }
          headers["content-type"] = "application/json"
          return PreparedRequest(
              payload=prepared,
              forward_headers=headers,
              requested_model=str(requested) if requested is not None else None,
          )
  ```

- [ ] **Step 6: Implement the locked, durable budget ledger.** Create `research/der/proxy/budget.py`:

  ```python
  """Atomic per-run proxy budget accounting."""

  from __future__ import annotations

  import fcntl
  import os
  from contextlib import contextmanager
  from datetime import datetime
  from decimal import Decimal
  from pathlib import Path
  from typing import Iterator, Literal

  from research.der.contracts.base import StrictModel, canonical_json_bytes
  from research.der.contracts.eval import RunBudget, TokenUsage
  from research.der.util.atomic import atomic_replace_bytes, create_exclusive_bytes

  CeilingReason = Literal[
      "max_cost_usd",
      "max_wall_seconds",
      "max_input_tokens",
      "max_output_tokens",
      "max_tool_calls",
      "max_session_turns",
  ]


  class BudgetExceededError(RuntimeError):
      pass


  class BudgetSnapshot(StrictModel):
      run_id: str
      budget: RunBudget
      started_at: datetime
      expected_attempts: int
      input_tokens: int = 0
      cache_tokens: int = 0
      output_tokens: int = 0
      tool_calls: int = 0
      session_turns: int = 0
      cost_usd: Decimal = Decimal("0")
      active_request_ids: tuple[str, ...] = ()
      completed_request_ids: tuple[str, ...] = ()
      ceiling_reason: CeilingReason | None = None


  class BudgetLedger:
      def __init__(self, root: Path) -> None:
          self.root = root
          self.root.mkdir(parents=True, exist_ok=True)

      def _path(self, run_id: str) -> Path:
          if not run_id or "/" in run_id or ".." in run_id:
              raise ValueError(f"invalid run id: {run_id!r}")
          return self.root / f"{run_id}.json"

      @contextmanager
      def _lock(self, run_id: str) -> Iterator[None]:
          path = self.root / f".{run_id}.lock"
          descriptor = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
          try:
              fcntl.flock(descriptor, fcntl.LOCK_EX)
              yield
          finally:
              fcntl.flock(descriptor, fcntl.LOCK_UN)
              os.close(descriptor)

      def register_run(
          self,
          run_id: str,
          budget: RunBudget,
          started_at: datetime,
          *,
          expected_attempts: int,
      ) -> BudgetSnapshot:
          if expected_attempts <= 0 or expected_attempts > budget.max_attempts:
              raise ValueError(
                  f"expected_attempts {expected_attempts} exceeds max_attempts {budget.max_attempts}"
              )
          snapshot = BudgetSnapshot(
              run_id=run_id,
              budget=budget,
              started_at=started_at,
              expected_attempts=expected_attempts,
          )
          with self._lock(run_id):
              create_exclusive_bytes(self._path(run_id), canonical_json_bytes(snapshot), mode=0o600)
          return snapshot

      def snapshot(self, run_id: str) -> BudgetSnapshot:
          return BudgetSnapshot.model_validate_json(self._path(run_id).read_bytes())

      def _write(self, snapshot: BudgetSnapshot) -> None:
          atomic_replace_bytes(self._path(snapshot.run_id), canonical_json_bytes(snapshot), mode=0o600)

      @staticmethod
      def _reason(snapshot: BudgetSnapshot, now: datetime) -> CeilingReason | None:
          budget = snapshot.budget
          if (now - snapshot.started_at).total_seconds() > budget.max_wall_seconds:
              return "max_wall_seconds"
          if snapshot.cost_usd > budget.max_cost_usd:
              return "max_cost_usd"
          if snapshot.input_tokens > budget.max_input_tokens:
              return "max_input_tokens"
          if snapshot.output_tokens > budget.max_output_tokens:
              return "max_output_tokens"
          if snapshot.tool_calls > budget.max_tool_calls:
              return "max_tool_calls"
          if snapshot.session_turns > budget.max_session_turns:
              return "max_session_turns"
          return None

      def authorize_request(self, run_id: str, request_id: str, now: datetime) -> BudgetSnapshot:
          with self._lock(run_id):
              current = self.snapshot(run_id)
              if current.ceiling_reason:
                  raise BudgetExceededError(current.ceiling_reason)
              reason = self._reason(current, now)
              if reason:
                  current = current.model_copy(update={"ceiling_reason": reason})
                  self._write(current)
                  raise BudgetExceededError(reason)
              if request_id in current.active_request_ids:
                  raise ValueError(f"request id already active: {request_id}")
              if request_id in current.completed_request_ids:
                  raise ValueError(f"request id already completed: {request_id}")
              updated = current.model_copy(
                  update={"active_request_ids": (*current.active_request_ids, request_id)}
              )
              self._write(updated)
              return updated

      def reconcile_response(
          self,
          run_id: str,
          request_id: str,
          *,
          usage: TokenUsage,
          cost_usd: Decimal,
          now: datetime,
      ) -> BudgetSnapshot:
          if cost_usd < 0:
              raise ValueError("cost_usd cannot be negative")
          with self._lock(run_id):
              current = self.snapshot(run_id)
              if request_id not in current.active_request_ids:
                  raise ValueError(f"request id is not active: {request_id}")
              active = tuple(item for item in current.active_request_ids if item != request_id)
              updated = current.model_copy(
                  update={
                      "input_tokens": current.input_tokens + usage.input_tokens,
                      "cache_tokens": current.cache_tokens + usage.cache_tokens,
                      "output_tokens": current.output_tokens + usage.output_tokens,
                      "tool_calls": current.tool_calls + usage.tool_calls,
                      "session_turns": current.session_turns + usage.session_turns,
                      "cost_usd": current.cost_usd + cost_usd,
                      "active_request_ids": active,
                      "completed_request_ids": (*current.completed_request_ids, request_id),
                  }
              )
              reason = self._reason(updated, now)
              if reason:
                  updated = updated.model_copy(update={"ceiling_reason": reason})
              self._write(updated)
              if reason:
                  raise BudgetExceededError(reason)
              return updated
  ```

- [ ] **Step 7: Run policy/budget tests and static checks.** Run:

  ```bash
  uv run pytest tests/proxy/test_policy.py tests/proxy/test_budget.py -q
  uv run ruff check research/der/proxy tests/proxy
  uv run mypy research/der
  ```

  Expected output: all tests pass; no static-check diagnostics. The test count may vary with parameter expansion, but it must be at least 13.

- [ ] **Step 8: Verify the policy contains no secret and names the mandatory model.** Run:

  ```bash
  grep -Fx 'model = "deepseek-v4-pro"' research/config/runtime-policy.toml
  ! grep -E '(sk-[A-Za-z0-9]|DEEPSEEK_API_KEY[[:space:]]*=)' research/config/runtime-policy.toml
  ```

  Expected output is only `model = "deepseek-v4-pro"`.

- [ ] **Step 9: Commit.** Run:

  ```bash
  git add \
    research/config/runtime-policy.toml research/der/proxy \
    tests/proxy
  git commit -m "feat: pin rollout model and enforce run budgets"
  ```

# Phase 1 — Milestone 1: one DeepSWE task through Pier, manually

Milestone exit: a real DeepSWE task runs through Pier with `DerQwenAgent`; Qwen installs offline from the pinned archive; the trial has no provider credential; all model traffic traverses the host proxy and is observed as `deepseek-v4-pro`; the intended Git patch is captured by `pre_artifacts.sh`; the pristine verifier emits evidence; and the machine result agrees with reward, CTRF, patch, logs, and ATIF. A deliberate task failure is classified `failed`, an induced infrastructure failure is classified `invalid`, and the V1, V2, V3, and V5 pin files all have `status: passed` (V7 passed in Phase 0; V4 belongs to Phase 4).

### Task 6: V3 Qwen standalone archive discovery in a real DeepSWE image

**Files:**
- Modify: `research/der/pins.py`
- Create: `scripts/discover_v3_qwen_archive.py`
- Create: `tests/discovery/test_v3_qwen_archive.py`
- Create after live probe: `research-plan/pins/v3-qwen-archive-install.md`
- Cache outside Git: `var/cache/qwen/v0.20.0/`

**Interfaces:**
- Consumes: passed V7 pin from Task 1; Qwen Code source at commit `92fda5603e84ef62a1b29bf6faf4f6a8124a2bf7`; all v0.20.0 release assets; official `install-qwen-standalone.sh`; Docker.
- Produces: `research.der.pins.write_pin(...) -> None`, `ArchiveSelection`, `discover_archive(...) -> ArchiveSelection`, and passed pin values `archive_path`, `archive_sha256`, `sha256sums_path`, `installer_path`, `installer_sha256`, `container_image_id`, `install_argv`, `qwen_binary`, `version_stdout`.

- [ ] **Step 1: Re-read the exact offline-install contract before writing the probe.** Run:

  ```bash
  git -C /var/cache/der/sources/qwen-code show \
    92fda5603e84ef62a1b29bf6faf4f6a8124a2bf7:README.md \
    | grep -n -E 'standalone|archive|SHA256SUMS' || true
  curl -fsSL https://qwenlm.github.io/qwen-code-docs/en/users/overview/ \
    | grep -n -E -- '--archive|SHA256SUMS' | head -10
  bash var/cache/qwen/v0.20.0/install-qwen-standalone.sh --help 2>/dev/null \
    | grep -E -- '--archive|--prefix|--help' || true
  ```

  The first execution may report that the installer file is absent; Step 4 downloads it. The source/docs output must state that an offline release archive is installed with `--archive PATH` while `SHA256SUMS` is adjacent. Do not infer an asset name or installed binary path. Only `--archive` is source-verified; `--prefix` is an assumption this task checks. If the installer `--help` shows no `--prefix` flag, that is a flag-shape adaptation inside this discovery task, not a spec contradiction: drop `--prefix` from `offline_install_argv` (and its unit test), run the installer with `HOME=/opt/qwen` so it installs beneath the documented default `~/.local/lib/qwen-code` with the shim at `~/.local/bin/qwen`, keep the `find`-based binary discovery unchanged, and record the actually executed argv in the pin's `install_argv`. Downstream tasks read `install_argv` and `qwen_binary` from the pin, never from this plan text.

- [ ] **Step 2: Write the failing archive-selection tests.** Create `tests/discovery/test_v3_qwen_archive.py`:

  ```python
  from __future__ import annotations

  import hashlib
  from pathlib import Path

  import pytest

  from scripts.discover_v3_qwen_archive import (
      archive_candidates,
      discover_archive,
      offline_install_argv,
  )


  def test_exactly_one_linux_x64_release_archive_is_selected(tmp_path: Path) -> None:
      archive = tmp_path / "qwen-code-v0.20.0-linux-x64.tar.gz"
      archive.write_bytes(b"release archive")
      digest = hashlib.sha256(archive.read_bytes()).hexdigest()
      (tmp_path / "SHA256SUMS").write_text(
          f"{digest}  {archive.name}\n"
          f"{'0' * 64}  qwen-code-v0.20.0-darwin-arm64.tar.gz\n",
          encoding="utf-8",
      )
      selected = discover_archive(tmp_path, platform="linux", architecture="x64")
      assert selected.archive == archive
      assert selected.sha256 == digest
      assert selected.checksums == tmp_path / "SHA256SUMS"


  def test_checksum_mismatch_stops_the_probe(tmp_path: Path) -> None:
      archive = tmp_path / "qwen-code-v0.20.0-linux-x64.tar.gz"
      archive.write_bytes(b"corrupt")
      (tmp_path / "SHA256SUMS").write_text(
          f"{'0' * 64}  {archive.name}\n", encoding="utf-8"
      )
      with pytest.raises(ValueError, match="checksum mismatch"):
          discover_archive(tmp_path, platform="linux", architecture="x64")


  def test_ambiguous_archives_stop_instead_of_guessing(tmp_path: Path) -> None:
      for name in (
          "qwen-code-v0.20.0-linux-x64.tar.gz",
          "qwen-code-v0.20.0-standalone-linux-x64.tar.gz",
      ):
          path = tmp_path / name
          path.write_bytes(name.encode())
      lines = [
          f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}"
          for path in tmp_path.glob("*.tar.gz")
      ]
      (tmp_path / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")
      with pytest.raises(ValueError, match="exactly one"):
          discover_archive(tmp_path, platform="linux", architecture="x64")


  def test_candidate_filter_does_not_accept_source_archives() -> None:
      names = [
          "qwen-code-v0.20.0-linux-x64.tar.gz",
          "qwen-code-0.20.0.tar.gz",
          "qwen-code-0.20.0.zip",
      ]
      assert archive_candidates(names, "linux", "x64") == (
          "qwen-code-v0.20.0-linux-x64.tar.gz",
      )


  def test_offline_install_command_has_no_network_or_latest_selector() -> None:
      argv = offline_install_argv(
          Path("/opt/cache/install-qwen-standalone.sh"),
          Path("/opt/cache/qwen-code-v0.20.0-linux-x64.tar.gz"),
          Path("/opt/qwen"),
      )
      assert argv == [
          "bash",
          "/opt/cache/install-qwen-standalone.sh",
          "--archive",
          "/opt/cache/qwen-code-v0.20.0-linux-x64.tar.gz",
          "--prefix",
          "/opt/qwen",
      ]
      assert "latest" not in " ".join(argv)
  ```

- [ ] **Step 3: Run the tests and observe the absent probe module.** Run:

  ```bash
  uv run pytest tests/discovery/test_v3_qwen_archive.py -q
  ```

  Expected failure includes `ModuleNotFoundError: No module named 'scripts.discover_v3_qwen_archive'`.

- [ ] **Step 4: Download all exact v0.20.0 assets and the official installer into the ignored cache.** Run:

  ```bash
  mkdir -p var/cache/qwen/v0.20.0
  gh release download v0.20.0 \
    --repo QwenLM/qwen-code \
    --dir var/cache/qwen/v0.20.0 \
    --clobber
  curl -fsSLo var/cache/qwen/v0.20.0/install-qwen-standalone.sh \
    https://qwen-code-assets.oss-cn-hangzhou.aliyuncs.com/installation/install-qwen-standalone.sh
  chmod 0555 var/cache/qwen/v0.20.0/install-qwen-standalone.sh
  find var/cache/qwen/v0.20.0 -maxdepth 1 -type f -printf '%f\n' | sort
  ```

  Expected output includes `SHA256SUMS`, `install-qwen-standalone.sh`, and release assets. Preserve the complete output for the pin transcript. If `gh` reports that tag `v0.20.0` is absent, STOP and record that contradiction; do not use `v0.20.1`.

- [ ] **Step 5: Add the shared strict pin writer.** Append this code to `research/der/pins.py`:

  ```python
  def write_pin(
      path: Path,
      *,
      verification: str,
      status: Literal["passed", "blocked"],
      source_revision: str,
      values: Mapping[str, Any],
      transcript: str,
      contradiction: str | None = None,
      observed_at: datetime | None = None,
  ) -> None:
      """Write one discovery document atomically; blocked pins require evidence."""
      from research.der.util.atomic import atomic_replace_bytes
      if status == "blocked" and not contradiction:
          raise ValueError("blocked pin requires contradiction evidence")
      if status == "passed" and contradiction is not None:
          raise ValueError("passed pin cannot contain a contradiction")
      timestamp = observed_at or datetime.now(UTC)
      front: dict[str, Any] = {
          "verification": verification,
          "status": status,
          "observed_at": timestamp.isoformat().replace("+00:00", "Z"),
          "source_revision": source_revision,
          "values": dict(values),
      }
      if contradiction:
          front["contradiction"] = contradiction
      body = (
          "---\n"
          + yaml.safe_dump(front, sort_keys=False, allow_unicode=True).rstrip()
          + "\n---\n"
          + f"# {verification} discovery record\n\n"
          + "## Exact command transcript\n\n```text\n"
          + transcript.rstrip()
          + "\n```\n"
      )
      atomic_replace_bytes(path, body.encode("utf-8"))


  def require_passed_pin(ref: str | Path) -> dict[str, Any]:
      """Load a pin by verification ID (V1–V10, M1…) or explicit path; require passed.

      Returns the pin's ``values`` mapping so callers can subscript discovered
      fields directly, e.g. ``require_passed_pin("V3")["archive_sha256"]``.
      """
      if isinstance(ref, Path) or "/" in str(ref):
          pin = load_pin(Path(ref))
      else:
          pin = load_pin(PIN_PATHS[str(ref)], expected_verification=str(ref))
      pin.require_passed()
      return pin.values


  def write_discovery_pin(
      path: Path,
      *,
      verification_id: str,
      status: Literal["passed", "blocked"],
      command: str,
      observation: Mapping[str, Any],
      stop_reason: str | None = None,
  ) -> None:
      """Discovery-script convenience over write_pin.

      ``command`` becomes the transcript; ``observation`` becomes ``values``;
      ``source_revision`` records this repository's HEAD at observation time.
      """
      from research.der.util.git import head_commit

      contradiction: str | None = None
      if status == "blocked":
          error = observation.get("error") if isinstance(observation, Mapping) else None
          contradiction = stop_reason or (str(error) if error else "observation contradicted the spec")
          if error and stop_reason:
              contradiction = f"{stop_reason} ({error})"
      write_pin(
          path,
          verification=verification_id,
          status=status,
          source_revision=head_commit(Path.cwd()),
          values=dict(observation),
          transcript=command,
          contradiction=contradiction,
      )
  ```

  Discovery scripts and gate tests from Task 10 onward call `require_passed_pin(...)` (accepting either a `V#`/`M#` id or a pin path and returning the values mapping) and `write_discovery_pin(...)`; both are thin layers over `load_pin`/`write_pin` and exist only in this module.

  Also add these imports at the top of `research/der/pins.py`:

  ```python
  from datetime import UTC, datetime
  from typing import Mapping, Literal

  import yaml
  ```

  Remove any duplicate imports created by the edit. Do not store environment-variable values in a pin transcript.

- [ ] **Step 6: Implement selection, checksum verification, real-image installation, and STOP behavior.** Create `scripts/discover_v3_qwen_archive.py`:

  ```python
  #!/usr/bin/env python3
  """V3: prove the exact Qwen v0.20.0 archive installs without network."""

  from __future__ import annotations

  import argparse
  import hashlib
  import json
  import os
  import platform as host_platform
  import re
  import shlex
  import subprocess
  import sys
  from dataclasses import dataclass
  from pathlib import Path
  from typing import Iterable

  from research.der.pins import load_pin, write_pin

  QWEN_COMMIT = "92fda5603e84ef62a1b29bf6faf4f6a8124a2bf7"
  ARCHIVE_SUFFIXES = (".tar.gz", ".tgz", ".zip")


  @dataclass(frozen=True, slots=True)
  class ArchiveSelection:
      archive: Path
      checksums: Path
      sha256: str


  def sha256_file(path: Path) -> str:
      digest = hashlib.sha256()
      with path.open("rb") as handle:
          for chunk in iter(lambda: handle.read(1024 * 1024), b""):
              digest.update(chunk)
      return digest.hexdigest()


  def archive_candidates(
      names: Iterable[str], platform_name: str, architecture: str
  ) -> tuple[str, ...]:
      wanted = []
      for name in names:
          lower = name.lower()
          if not lower.endswith(ARCHIVE_SUFFIXES):
              continue
          if platform_name not in lower or architecture not in lower:
              continue
          if "source" in lower or lower in {"source.zip", "source.tar.gz"}:
              continue
          if lower.startswith("qwen-code-0.20.0."):
              continue
          wanted.append(name)
      return tuple(sorted(wanted))


  def _checksums(path: Path) -> dict[str, str]:
      result: dict[str, str] = {}
      for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
          if not line.strip():
              continue
          match = re.fullmatch(r"([0-9a-fA-F]{64})\s+\*?(.+)", line)
          if match is None:
              raise ValueError(f"{path}:{line_number}: malformed checksum line")
          result[Path(match.group(2)).name] = match.group(1).lower()
      return result


  def discover_archive(
      release_dir: Path, *, platform: str, architecture: str
  ) -> ArchiveSelection:
      sums = release_dir / "SHA256SUMS"
      if not sums.is_file():
          raise ValueError(f"{sums}: required adjacent checksum manifest is absent")
      checksums = _checksums(sums)
      candidates = archive_candidates(checksums, platform, architecture)
      if len(candidates) != 1:
          raise ValueError(
              f"expected exactly one {platform}/{architecture} standalone archive; "
              f"observed {list(candidates)}"
          )
      archive = release_dir / candidates[0]
      if not archive.is_file():
          raise ValueError(f"release archive listed by SHA256SUMS is absent: {archive}")
      observed = sha256_file(archive)
      expected = checksums[archive.name]
      if observed != expected:
          raise ValueError(
              f"checksum mismatch for {archive.name}: expected {expected}, observed {observed}"
          )
      return ArchiveSelection(archive=archive, checksums=sums, sha256=observed)


  def offline_install_argv(installer: Path, archive: Path, prefix: Path) -> list[str]:
      return [
          "bash",
          str(installer),
          "--archive",
          str(archive),
          "--prefix",
          str(prefix),
      ]


  def run(argv: list[str], *, transcript: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
      transcript.append("$ " + shlex.join(argv))
      completed = subprocess.run(
          argv,
          check=False,
          text=True,
          stdout=subprocess.PIPE,
          stderr=subprocess.STDOUT,
          **kwargs,
      )
      transcript.append(completed.stdout.rstrip())
      transcript.append(f"[exit {completed.returncode}]")
      if completed.returncode != 0:
          raise ValueError(f"command failed with exit {completed.returncode}: {shlex.join(argv)}")
      return completed


  def normalized_architecture(machine: str) -> str:
      aliases = {"x86_64": "x64", "amd64": "x64", "aarch64": "arm64"}
      try:
          return aliases[machine.lower()]
      except KeyError as exc:
          raise ValueError(f"unsupported probe architecture: {machine}") from exc


  def main() -> int:
      parser = argparse.ArgumentParser()
      parser.add_argument("--release-dir", type=Path, required=True)
      parser.add_argument("--v7-pin", type=Path, required=True)
      parser.add_argument("--source-cache", type=Path, default=Path("/var/cache/der/sources"))
      parser.add_argument(
          "--pin", type=Path, default=Path("research-plan/pins/v3-qwen-archive-install.md")
      )
      args = parser.parse_args()
      transcript: list[str] = []
      values: dict[str, object] = {}
      try:
          source = args.source_cache / "qwen-code"
          head = run(
              ["git", "-C", str(source), "rev-parse", "HEAD"], transcript=transcript
          ).stdout.strip()
          if head != QWEN_COMMIT:
              raise ValueError(f"Qwen source expected {QWEN_COMMIT}, observed {head}")
          v7 = load_pin(args.v7_pin, expected_verification="V7")
          v7.require_passed()
          audits = v7.value("audited_verifiers")
          if not isinstance(audits, list) or not audits:
              raise ValueError("V7 audited_verifiers is empty")
          relative = str(audits[0]["relative_path"])
          task = Path(str(v7.value("task_root"))) / relative
          dockerfiles = sorted((task / "environment").rglob("Dockerfile"))
          if len(dockerfiles) != 1:
              raise ValueError(
                  f"expected one Dockerfile below {task / 'environment'}, observed {dockerfiles}"
              )
          selection = discover_archive(
              args.release_dir,
              platform="linux",
              architecture=normalized_architecture(host_platform.machine()),
          )
          installer = args.release_dir / "install-qwen-standalone.sh"
          if not installer.is_file():
              raise ValueError(f"official installer is absent: {installer}")
          installer_sha = sha256_file(installer)
          image_tag = "der-v3-qwen-probe:0.20.0"
          run(
              [
                  "docker",
                  "build",
                  "--pull=false",
                  "--tag",
                  image_tag,
                  "--file",
                  str(dockerfiles[0]),
                  str(task / "environment"),
              ],
              transcript=transcript,
          )
          image_id = run(
              ["docker", "image", "inspect", "--format", "{{.Id}}", image_tag],
              transcript=transcript,
          ).stdout.strip()
          install = offline_install_argv(
              Path("/qwen/install-qwen-standalone.sh"),
              Path("/qwen") / selection.archive.name,
              Path("/opt/qwen"),
          )
          shell = (
              "set -euo pipefail; "
              + shlex.join(install)
              + "; QWEN=$(find /opt/qwen -type f -name qwen -perm -111 -print -quit); "
              + 'test -n "$QWEN"; printf "BINARY=%s\\n" "$QWEN"; "$QWEN" --version'
          )
          installed = run(
              [
                  "docker",
                  "run",
                  "--rm",
                  "--network",
                  "none",
                  "--mount",
                  f"type=bind,src={args.release_dir.resolve()},dst=/qwen,readonly",
                  image_tag,
                  "bash",
                  "-lc",
                  shell,
              ],
              transcript=transcript,
          ).stdout
          binary_lines = [line for line in installed.splitlines() if line.startswith("BINARY=")]
          if len(binary_lines) != 1:
              raise ValueError(f"installer did not report exactly one qwen binary: {binary_lines}")
          version_lines = [line.strip() for line in installed.splitlines() if "0.20.0" in line]
          if not version_lines:
              raise ValueError(f"installed binary did not report version 0.20.0: {installed!r}")
          values = {
              "archive_path": str(selection.archive.resolve()),
              "archive_sha256": selection.sha256,
              "sha256sums_path": str(selection.checksums.resolve()),
              "installer_path": str(installer.resolve()),
              "installer_sha256": installer_sha,
              "container_image_id": image_id,
              "deepswe_task_id": str(audits[0]["task_id"]),
              "deepswe_task_relative_path": relative,
              "install_argv": install,
              "qwen_binary": binary_lines[0].split("=", 1)[1],
              "version_stdout": version_lines[-1],
              "network_mode": "none",
          }
          write_pin(
              args.pin,
              verification="V3",
              status="passed",
              source_revision=QWEN_COMMIT,
              values=values,
              transcript="\n".join(transcript),
          )
          print(json.dumps({"status": "passed", **values}, sort_keys=True))
          return 0
      except Exception as exc:
          write_pin(
              args.pin,
              verification="V3",
              status="blocked",
              source_revision=QWEN_COMMIT,
              values=values,
              transcript="\n".join(transcript + [f"ERROR: {exc}"]),
              contradiction=str(exc),
          )
          print(f"STOP V3: {exc}", file=sys.stderr)
          return 78


  if __name__ == "__main__":
      raise SystemExit(main())
  ```

- [ ] **Step 7: Run the unit tests and static checks.** Run:

  ```bash
  uv run pytest tests/discovery/test_v3_qwen_archive.py tests/test_pins.py -q
  uv run ruff check scripts/discover_v3_qwen_archive.py research/der/pins.py tests/discovery
  ```

  Expected output: all tests pass and Ruff emits no diagnostics.

- [ ] **Step 8: Run the real V3 probe and inspect the pin.** Run:

  ```bash
  uv run python scripts/discover_v3_qwen_archive.py \
    --release-dir var/cache/qwen/v0.20.0 \
    --v7-pin research-plan/pins/v7-deepswe-revisions.md \
    | tee /tmp/der-v3-summary.json
  uv run der pins assert V3 \
    --path research-plan/pins/v3-qwen-archive-install.md
  sed -n '1,220p' research-plan/pins/v3-qwen-archive-install.md
  ```

  Expected observable output: the summary has `"status": "passed"`; the transcript shows `docker run --network none`; `version_stdout` contains `0.20.0`; and the pin records a real archive SHA-256 and image ID. Exit `78`, `status: blocked`, a missing checksum, a network-dependent install, or any other version is a STOP gate. Commit the blocked pin alone and escalate it to the owner.

- [ ] **Step 9: Commit.** Run:

  ```bash
  git add \
    research/der/pins.py scripts/discover_v3_qwen_archive.py \
    tests/discovery/test_v3_qwen_archive.py \
    research-plan/pins/v3-qwen-archive-install.md
  git commit -m "test: pin offline Qwen archive installation"
  ```

### Task 7: Runtime-shaped harness staging and owner-overlay policy

**Files:**
- Create: `research/der/harness/policy.py`
- Create: `research/der/harness/stage.py`
- Create: `tests/harness/test_policy.py`
- Create: `tests/harness/test_stage.py`
- Create: `tests/fixtures/harness/managed/QWEN.md`
- Create: `tests/fixtures/harness/managed/.qwen/settings.json`
- Create: `tests/fixtures/harness/managed/.qwen/skills/der-engineering/SKILL.md`
- Create: `tests/fixtures/harness/owner-overlay/.qwen/settings.json`
- Create: `tests/golden/staging/staging-manifest.json`

**Interfaces:**
- Consumes: a managed runtime-shaped Qwen project, an owner-controlled overlay, and isolated destination/HOME paths.
- Produces: `validate_evolvable_harness(root: Path) -> None`, `stage_harness(managed_root: Path, owner_overlay_root: Path, destination: Path, rollout_home: Path) -> StagingResult`, and exact manifest entries later included in runtime evidence.

- [ ] **Step 1: Read the locked Qwen project-path and settings-precedence sources.** Run:

  ```bash
  git -C /var/cache/der/sources/qwen-code grep -n \
    -e 'QWEN_CODE_SYSTEM_SETTINGS_PATH' \
    -e '.qwen/settings.json' \
    -e '.qwen/skills' \
    92fda5603e84ef62a1b29bf6faf4f6a8124a2bf7 -- packages docs | head -80
  git -C /var/cache/der/sources/qwen-code show \
    92fda5603e84ef62a1b29bf6faf4f6a8124a2bf7:docs/cli/configuration.md \
    2>/dev/null | sed -n '1,220p' || true
  ```

  Confirm from source that project settings live at `.qwen/settings.json`, skills are `.qwen/skills/<name>/SKILL.md`, and `QWEN_CODE_SYSTEM_SETTINGS_PATH` selects the owner policy. If any path differs at the locked revision, STOP and record the source lines in an owner escalation; do not silently change the approved runtime shape.

- [ ] **Step 2: Write policy tests that enumerate both forbidden key classes.** Create `tests/harness/test_policy.py`:

  ```python
  from __future__ import annotations

  import json
  from pathlib import Path

  import pytest

  from research.der.errors import PolicyViolationError
  from research.der.harness.policy import validate_evolvable_harness


  REQUEST_KEYS = (
      "model",
      "endpoint",
      "base_url",
      "api_key",
      "apiKey",
      "temperature",
      "top_p",
      "max_tokens",
  )
  EXECUTABLE_SETTINGS = (
      {"hooks": {"afterTool": [{"command": "touch /tmp/pwned"}]}},
      {"mcpServers": {"bad": {"command": "sh", "args": ["-c", "id"]}}},
      {"tools": {"runner": {"shell": "id"}}},
  )


  def write_settings(root: Path, value: dict[str, object]) -> None:
      path = root / ".qwen/settings.json"
      path.parent.mkdir(parents=True, exist_ok=True)
      path.write_text(json.dumps(value), encoding="utf-8")


  @pytest.mark.parametrize("key", REQUEST_KEYS)
  def test_evolvable_settings_reject_request_shaping_at_any_depth(
      tmp_path: Path, key: str
  ) -> None:
      write_settings(tmp_path, {"nested": {key: "owner-only"}})
      with pytest.raises(PolicyViolationError, match="request-shaping"):
          validate_evolvable_harness(tmp_path)


  @pytest.mark.parametrize("settings", EXECUTABLE_SETTINGS)
  def test_evolvable_settings_reject_host_executable_configuration(
      tmp_path: Path, settings: dict[str, object]
  ) -> None:
      write_settings(tmp_path, settings)
      with pytest.raises(PolicyViolationError, match="host-executable"):
          validate_evolvable_harness(tmp_path)


  def test_non_executable_behavioral_settings_are_allowed(tmp_path: Path) -> None:
      write_settings(
          tmp_path,
          {
              "general": {"approvalMode": "yolo", "enableAutoUpdate": False},
              "context": {"fileName": "QWEN.md"},
          },
      )
      validate_evolvable_harness(tmp_path)


  def test_symlink_is_rejected_before_copy(tmp_path: Path) -> None:
      (tmp_path / "QWEN.md").symlink_to("/etc/passwd")
      with pytest.raises(PolicyViolationError, match="symlink"):
          validate_evolvable_harness(tmp_path)
  ```

- [ ] **Step 3: Write transparent-copy and overlay-precedence tests.** Create the fixture files:

  `tests/fixtures/harness/managed/QWEN.md`:

  ```markdown
  # Managed operating instructions

  Read the repository, make the smallest correct change, run the relevant tests, and commit the result.
  ```

  `tests/fixtures/harness/managed/.qwen/settings.json`:

  ```json
  {
    "general": {
      "approvalMode": "yolo",
      "enableAutoUpdate": false
    },
    "context": {
      "fileName": "QWEN.md"
    }
  }
  ```

  `tests/fixtures/harness/managed/.qwen/skills/der-engineering/SKILL.md`:

  ```markdown
  ---
  name: der-engineering
  description: Execute repository engineering tasks with evidence-first verification.
  ---

  # der engineering

  Inspect before editing. Keep the patch narrow. Run the verifier-facing tests. Commit once.
  ```

  `tests/fixtures/harness/owner-overlay/.qwen/settings.json`:

  ```json
  {
    "general": {
      "approvalMode": "yolo",
      "maxSessionTurns": 10
    },
    "modelProviders": {
      "der-proxy": {
        "type": "openai",
        "baseUrl": "http://der-proxy.invalid/v1",
        "apiKey": "$DER_RUN_TOKEN"
      }
    },
    "model": {
      "name": "deepseek-v4-pro",
      "provider": "der-proxy"
    }
  }
  ```

  Create `tests/harness/test_stage.py`:

  ```python
  from __future__ import annotations

  import json
  import stat
  from pathlib import Path

  import pytest

  from research.der.errors import ImmutableArtifactError, PolicyViolationError
  from research.der.harness.stage import stage_harness

  FIXTURES = Path("tests/fixtures/harness")
  GOLDEN = Path("tests/golden/staging/staging-manifest.json")


  def test_stage_is_transparent_except_for_explicit_owner_overlay(tmp_path: Path) -> None:
      destination = tmp_path / "workspace"
      home = tmp_path / "home"
      result = stage_harness(
          FIXTURES / "managed",
          FIXTURES / "owner-overlay",
          destination,
          home,
      )
      assert (destination / "QWEN.md").read_bytes() == (
          FIXTURES / "managed/QWEN.md"
      ).read_bytes()
      assert (destination / ".qwen/skills/der-engineering/SKILL.md").read_bytes() == (
          FIXTURES / "managed/.qwen/skills/der-engineering/SKILL.md"
      ).read_bytes()
      settings = json.loads((destination / ".qwen/settings.json").read_text())
      assert settings["general"] == {
          "approvalMode": "yolo",
          "enableAutoUpdate": False,
          "maxSessionTurns": 10,
      }
      assert settings["model"]["name"] == "deepseek-v4-pro"
      assert result.environment == {
          "HOME": str(home),
          "QWEN_CODE_SYSTEM_SETTINGS_PATH": str(destination / ".qwen/settings.json"),
      }
      assert result.manifest_path.read_bytes() == GOLDEN.read_bytes()


  def test_source_mode_is_preserved(tmp_path: Path) -> None:
      managed = tmp_path / "managed"
      overlay = tmp_path / "overlay"
      managed.mkdir()
      overlay.mkdir()
      executable = managed / "verify.sh"
      executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
      executable.chmod(0o755)
      result = stage_harness(managed, overlay, tmp_path / "dest", tmp_path / "home")
      del result
      mode = stat.S_IMODE((tmp_path / "dest/verify.sh").stat().st_mode)
      assert mode == 0o755


  def test_existing_destination_is_never_reused(tmp_path: Path) -> None:
      destination = tmp_path / "dest"
      destination.mkdir()
      with pytest.raises(ImmutableArtifactError, match="already exists"):
          stage_harness(
              FIXTURES / "managed", FIXTURES / "owner-overlay", destination, tmp_path / "home"
          )


  def test_owner_overlay_symlink_is_rejected(tmp_path: Path) -> None:
      overlay = tmp_path / "overlay"
      overlay.mkdir()
      (overlay / "link").symlink_to("/etc/passwd")
      with pytest.raises(PolicyViolationError, match="symlink"):
          stage_harness(FIXTURES / "managed", overlay, tmp_path / "dest", tmp_path / "home")
  ```

  Create `tests/golden/staging/staging-manifest.json` as exactly one canonical-JSON line plus a trailing newline (the manifest is written by `canonical_json_bytes`, which emits compact sorted-key JSON; file entries appear in sorted staged-path order, so `.qwen/settings.json` precedes the skill file). The digests below are the true SHA-256 values of the fixture bytes above; Step 7 re-verifies them independently:

  ```json
  {"files":[{"origin":"merged","path":".qwen/settings.json","sha256":"d20b51b249ba1814b268078490f0e7b6b7511c38ac39a1b152a34e2b00ad1175"},{"origin":"managed","path":".qwen/skills/der-engineering/SKILL.md","sha256":"5b998591122d062913ff3c37265e902b15878730b7f7566c2ba2b58717fb076d"},{"origin":"managed","path":"QWEN.md","sha256":"f3b957a1c29a6bc44de44fb4b66fcb1eeeb40e1aeb8be89ec1c609a3f0e46d61"}],"schema_version":"der.staging-manifest.v1"}
  ```

- [ ] **Step 4: Run the staging tests and observe missing modules.** Run:

  ```bash
  uv run pytest tests/harness/test_policy.py tests/harness/test_stage.py -q
  ```

  Expected failure includes `ModuleNotFoundError: No module named 'research.der.harness'`.

- [ ] **Step 5: Implement the recursive managed-namespace policy.** `research/der/harness/__init__.py` already exists from Task 3. Create `research/der/harness/policy.py`:

  ```python
  """Fail-closed policy for files that may evolve and later reach the owner machine."""

  from __future__ import annotations

  import json
  import re
  from pathlib import Path
  from typing import Any, Iterator

  from research.der.errors import PolicyViolationError

  REQUEST_SHAPING = frozenset(
      {
          "model",
          "modelname",
          "modelprovider",
          "modelproviders",
          "endpoint",
          "baseurl",
          "url",
          "apikey",
          "key",
          "token",
          "temperature",
          "topp",
          "maxtokens",
      }
  )
  HOST_EXECUTABLE = frozenset(
      {
          "hooks",
          "hook",
          "mcpservers",
          "mcpserver",
          "command",
          "commands",
          "shell",
          "executable",
          "exec",
          "binary",
      }
  )


  def normalize_key(value: str) -> str:
      return re.sub(r"[^a-z0-9]", "", value.lower())


  def iter_keys(value: Any, path: tuple[str, ...] = ()) -> Iterator[tuple[tuple[str, ...], str]]:
      if isinstance(value, dict):
          for key, child in value.items():
              if not isinstance(key, str):
                  raise PolicyViolationError(f"settings key is not a string at {'.'.join(path)}")
              current = (*path, key)
              yield current, normalize_key(key)
              yield from iter_keys(child, current)
      elif isinstance(value, list):
          for index, child in enumerate(value):
              yield from iter_keys(child, (*path, str(index)))


  def reject_symlinks(root: Path) -> None:
      if root.is_symlink():
          raise PolicyViolationError(f"symlink is forbidden: {root}")
      for path in root.rglob("*"):
          if path.is_symlink():
              raise PolicyViolationError(f"symlink is forbidden: {path}")


  def validate_evolvable_harness(root: Path) -> None:
      if not root.is_dir():
          raise PolicyViolationError(f"managed harness directory is absent: {root}")
      reject_symlinks(root)
      settings_path = root / ".qwen/settings.json"
      if not settings_path.exists():
          return
      try:
          settings = json.loads(settings_path.read_text(encoding="utf-8"))
      except (OSError, json.JSONDecodeError) as exc:
          raise PolicyViolationError(f"invalid managed settings: {settings_path}: {exc}") from exc
      for path, normalized in iter_keys(settings):
          dotted = ".".join(path)
          if normalized in REQUEST_SHAPING:
              raise PolicyViolationError(
                  f"request-shaping setting is owner-only: {dotted}"
              )
          if normalized in HOST_EXECUTABLE:
              raise PolicyViolationError(
                  f"host-executable setting is owner-only: {dotted}"
              )
  ```

- [ ] **Step 6: Implement atomic transparent staging and deep owner precedence.** Create `research/der/harness/stage.py`:

  ```python
  """Transparent managed copy plus owner-controlled immutable overlay."""

  from __future__ import annotations

  import hashlib
  import json
  import os
  import shutil
  from dataclasses import dataclass
  from pathlib import Path
  from typing import Any

  from research.der.contracts.base import canonical_json_bytes
  from research.der.errors import ImmutableArtifactError
  from research.der.harness.policy import reject_symlinks, validate_evolvable_harness


  @dataclass(frozen=True, slots=True)
  class StagingResult:
      destination: Path
      rollout_home: Path
      manifest_path: Path
      environment: dict[str, str]


  def _merge(base: Any, overlay: Any) -> Any:
      if isinstance(base, dict) and isinstance(overlay, dict):
          result = dict(base)
          for key, value in overlay.items():
              result[key] = _merge(result[key], value) if key in result else value
          return result
      return overlay


  def _copy_file(source: Path, destination: Path) -> None:
      destination.parent.mkdir(parents=True, exist_ok=True)
      shutil.copy2(source, destination, follow_symlinks=False)


  def _file_digest(path: Path) -> str:
      return hashlib.sha256(path.read_bytes()).hexdigest()


  def stage_harness(
      managed_root: Path,
      owner_overlay_root: Path,
      destination: Path,
      rollout_home: Path,
  ) -> StagingResult:
      validate_evolvable_harness(managed_root)
      if not owner_overlay_root.is_dir():
          raise ValueError(f"owner overlay directory is absent: {owner_overlay_root}")
      reject_symlinks(owner_overlay_root)
      if destination.exists():
          raise ImmutableArtifactError(f"staging destination already exists: {destination}")
      if rollout_home.exists():
          raise ImmutableArtifactError(f"rollout HOME already exists: {rollout_home}")
      destination.mkdir(parents=True, mode=0o700)
      rollout_home.mkdir(parents=True, mode=0o700)
      origins: dict[str, str] = {}
      try:
          for source in sorted(path for path in managed_root.rglob("*") if path.is_file()):
              relative = source.relative_to(managed_root)
              _copy_file(source, destination / relative)
              origins[relative.as_posix()] = "managed"
          for source in sorted(path for path in owner_overlay_root.rglob("*") if path.is_file()):
              relative = source.relative_to(owner_overlay_root)
              target = destination / relative
              if relative.as_posix() == ".qwen/settings.json" and target.exists():
                  managed = json.loads(target.read_text(encoding="utf-8"))
                  owner = json.loads(source.read_text(encoding="utf-8"))
                  target.write_bytes(canonical_json_bytes(_merge(managed, owner)))
                  target.chmod(source.stat().st_mode & 0o777)
                  origins[relative.as_posix()] = "merged"
              else:
                  _copy_file(source, target)
                  origins[relative.as_posix()] = "owner-overlay"
          files = [
              {
                  "origin": origins[path.relative_to(destination).as_posix()],
                  "path": path.relative_to(destination).as_posix(),
                  "sha256": _file_digest(path),
              }
              for path in sorted(
                  item
                  for item in destination.rglob("*")
                  if item.is_file() and ".der" not in item.relative_to(destination).parts
              )
          ]
          manifest_path = destination / ".der/staging-manifest.json"
          manifest_path.parent.mkdir(parents=True, exist_ok=True)
          manifest_path.write_bytes(
              canonical_json_bytes(
                  {"schema_version": "der.staging-manifest.v1", "files": files}
              )
          )
          os.chmod(manifest_path, 0o600)
          return StagingResult(
              destination=destination,
              rollout_home=rollout_home,
              manifest_path=manifest_path,
              environment={
                  "HOME": str(rollout_home),
                  "QWEN_CODE_SYSTEM_SETTINGS_PATH": str(
                      destination / ".qwen/settings.json"
                  ),
              },
          )
      except Exception:
          shutil.rmtree(destination, ignore_errors=True)
          shutil.rmtree(rollout_home, ignore_errors=True)
          raise
  ```

- [ ] **Step 7: Recompute the fixture digests independently and verify the locked golden bytes.** Run:

  ```bash
  uv run pytest tests/harness/test_stage.py::test_stage_is_transparent_except_for_explicit_owner_overlay \
    -q --maxfail=1
  uv run python - <<'PY'
  import hashlib
  from pathlib import Path

  expected = {
      ".qwen/skills/der-engineering/SKILL.md": "5b998591122d062913ff3c37265e902b15878730b7f7566c2ba2b58717fb076d",
      "QWEN.md": "f3b957a1c29a6bc44de44fb4b66fcb1eeeb40e1aeb8be89ec1c609a3f0e46d61",
  }
  root = Path("tests/fixtures/harness/managed")
  for relative, digest in expected.items():
      observed = hashlib.sha256((root / relative).read_bytes()).hexdigest()
      assert observed == digest, (relative, observed)
  print("managed fixture digests verified")
  PY
  ```

  Expected output: the test passes and the independent check prints `managed fixture digests verified`. A digest mismatch means the fixture or golden was altered; inspect the byte diff and restore the reviewed content rather than accepting a new digest casually.

- [ ] **Step 8: Run all policy/staging tests and static checks.** Run:

  ```bash
  uv run pytest tests/harness/test_policy.py tests/harness/test_stage.py -q
  uv run ruff check research/der/harness tests/harness
  uv run mypy research/der
  ```

  Expected output: at least 17 tests pass; no diagnostics. Check that no file appears beneath the test rollout HOME other than directories created by the test.

- [ ] **Step 9: Commit.** Run:

  ```bash
  git add \
    research/der/harness \
    tests/harness tests/fixtures/harness tests/golden/staging
  git commit -m "feat: stage runtime Qwen harness with owner policy overlay"
  ```

### Task 8: Host pinning proxy, short-lived run tokens, observations, and dollar budget accounting

**Files:**
- Modify: `research/config/runtime-policy.toml`
- Create: `research/der/proxy/registry.py`
- Create: `research/der/proxy/observations.py`
- Create: `research/der/proxy/app.py`
- Create: `tests/proxy/test_registry.py`
- Create: `tests/proxy/test_observations.py`
- Create: `tests/proxy/test_app.py`

**Interfaces:**
- Consumes: `ModelPolicy`, `BudgetLedger`, host-only `DEEPSEEK_API_KEY`, OpenAI-compatible `POST /chat/completions`, and official DeepSeek v4 pro token prices pinned into `runtime-policy.toml` at this commit.
- Produces: `RunRegistry.issue(...) -> IssuedRunToken`, `RunRegistry.authorize(...) -> RunRegistration`, `ObservationLog.append(...)`, `create_app(...) -> FastAPI`, `/healthz`, `/v1/chat/completions`, and append-only proxy evidence keyed by `run_id` and `request_id`.

- [ ] **Step 1: Verify the provider surface and price inputs against official DeepSeek documentation.** Run:

  ```bash
  curl -fsSL https://api-docs.deepseek.com/quick_start/pricing/ \
    | grep -E -n 'deepseek-v4-pro|CACHE HIT|CACHE MISS|OUTPUT TOKENS' | head -20
  curl -fsSL https://api-docs.deepseek.com/ \
    | grep -E -n 'https://api.deepseek.com|deepseek-v4-pro' | head -20
  curl -fsSL https://api-docs.deepseek.com/quick_start/token_usage/ \
    | grep -E -n 'prompt_tokens|completion_tokens|prompt_cache_hit_tokens|usage' | head -30
  ```

  At generation on 2026-07-21, the official English pricing page states USD per one million tokens for `deepseek-v4-pro`: cache-hit input `0.003625`, cache-miss input `0.435`, output `0.87`. Step 2 pins those values with the documentation URL and retrieval date. If the live page differs when this task executes, STOP, record the page output for the owner, and obtain an architecture-preserving policy-version update before proceeding; do not silently retain stale prices.

- [ ] **Step 2: Extend the immutable proxy policy with exact source-attributed pricing.** Append to `research/config/runtime-policy.toml`:

  ```toml
  [pricing]
  currency = "USD"
  unit_tokens = 1000000
  cache_hit_input_per_unit = "0.003625"
  cache_miss_input_per_unit = "0.435"
  output_per_unit = "0.87"
  source_url = "https://api-docs.deepseek.com/quick_start/pricing/"
  retrieved_on = "2026-07-21"
  ```

  Keep `proxy.policy_id = "deepseek-v4-pro-v1"`; the runtime-manifest digest captures the policy file bytes. Do not introduce a second policy source.

- [ ] **Step 3: Write registry and observation tests.** Create `tests/proxy/test_registry.py`:

  ```python
  from __future__ import annotations

  from datetime import UTC, datetime, timedelta
  from decimal import Decimal
  from pathlib import Path

  import pytest

  from research.der.contracts.eval import RunBudget
  from research.der.proxy.registry import RunRegistry


  def budget() -> RunBudget:
      return RunBudget(
          max_cost_usd=Decimal("4"),
          max_wall_seconds=3600,
          max_attempts=4,
          max_input_tokens=100000,
          max_output_tokens=20000,
          max_tool_calls=100,
          max_session_turns=40,
      )


  def test_issue_stores_only_hash_and_authorizes_exact_token(tmp_path: Path) -> None:
      now = datetime(2026, 7, 21, tzinfo=UTC)
      registry = RunRegistry(tmp_path)
      issued = registry.issue(
          run_id="RUN-EXP-0001-proxy-development-01",
          policy_id="deepseek-v4-pro-v1",
          budget=budget(),
          expected_attempts=4,
          expires_at=now + timedelta(hours=2),
          now=now,
      )
      stored = (tmp_path / "RUN-EXP-0001-proxy-development-01.json").read_text()
      assert issued.token not in stored
      assert "DEEPSEEK_API_KEY" not in stored
      assert registry.authorize(issued.token, now=now).run_id == issued.run_id


  def test_expired_or_unknown_token_is_rejected(tmp_path: Path) -> None:
      now = datetime(2026, 7, 21, tzinfo=UTC)
      registry = RunRegistry(tmp_path)
      issued = registry.issue(
          run_id="RUN-EXP-0001-proxy-development-01",
          policy_id="deepseek-v4-pro-v1",
          budget=budget(),
          expected_attempts=1,
          expires_at=now + timedelta(seconds=1),
          now=now,
      )
      with pytest.raises(PermissionError, match="expired"):
          registry.authorize(issued.token, now=now + timedelta(seconds=2))
      with pytest.raises(PermissionError, match="unknown"):
          registry.authorize("not-a-token", now=now)
  ```

  Create `tests/proxy/test_observations.py`:

  ```python
  from __future__ import annotations

  import json
  from datetime import UTC, datetime
  from decimal import Decimal
  from pathlib import Path

  from research.der.proxy.observations import ModelObservation, ObservationLog


  def test_append_is_one_fsynced_json_object_per_line(tmp_path: Path) -> None:
      path = tmp_path / "observations.jsonl"
      log = ObservationLog(path)
      log.append(
          ModelObservation(
              timestamp=datetime(2026, 7, 21, tzinfo=UTC),
              run_id="RUN-EXP-0001-proxy-development-01",
              request_id="req-1",
              role="rollout",
              requested_model=None,
              observed_model="deepseek-v4-pro",
              status_code=200,
              input_tokens=10,
              cache_tokens=2,
              output_tokens=3,
              cost_usd=Decimal("0.000005"),
              response_sha256="0" * 64,
          )
      )
      rows = [json.loads(line) for line in path.read_text().splitlines()]
      assert len(rows) == 1
      assert rows[0]["observed_model"] == "deepseek-v4-pro"
      assert rows[0]["role"] == "rollout"
      assert rows[0]["cost_usd"] == "0.000005"
  ```

- [ ] **Step 4: Write proxy tests with an in-process provider; include streaming and secret non-leakage.** Create `tests/proxy/test_app.py`:

  ```python
  from __future__ import annotations

  import json
  from datetime import UTC, datetime, timedelta
  from decimal import Decimal
  from pathlib import Path

  import httpx
  import pytest
  from httpx import ASGITransport

  from research.der.contracts.eval import RunBudget
  from research.der.proxy.app import Pricing, create_app
  from research.der.proxy.budget import BudgetLedger
  from research.der.proxy.observations import ObservationLog
  from research.der.proxy.policy import ModelPolicy
  from research.der.proxy.registry import RunRegistry


  def budget() -> RunBudget:
      return RunBudget(
          max_cost_usd=Decimal("2"),
          max_wall_seconds=3600,
          max_attempts=2,
          max_input_tokens=1000,
          max_output_tokens=1000,
          max_tool_calls=100,
          max_session_turns=20,
      )


  def provider_app(captured: list[dict[str, object]]):
      from fastapi import FastAPI, Request
      from fastapi.responses import JSONResponse, StreamingResponse

      app = FastAPI()

      @app.post("/chat/completions")
      async def chat(request: Request):
          body = await request.json()
          captured.append(
              {"body": body, "authorization": request.headers.get("authorization")}
          )
          if body.get("stream"):
              async def events():
                  yield 'data: {"id":"p1","model":"deepseek-v4-pro","choices":[{"delta":{"content":"ok"}}]}\n\n'
                  yield 'data: {"id":"p1","model":"deepseek-v4-pro","choices":[],"usage":{"prompt_tokens":10,"prompt_cache_hit_tokens":2,"completion_tokens":3}}\n\n'
                  yield "data: [DONE]\n\n"
              return StreamingResponse(events(), media_type="text/event-stream")
          return JSONResponse(
              {
                  "id": "p1",
                  "model": "deepseek-v4-pro",
                  "choices": [{"message": {"role": "assistant", "content": "ok"}}],
                  "usage": {
                      "prompt_tokens": 10,
                      "prompt_cache_hit_tokens": 2,
                      "completion_tokens": 3,
                  },
              }
          )

      return app


  async def client(tmp_path: Path, captured: list[dict[str, object]]):
      now = datetime(2026, 7, 21, tzinfo=UTC)
      registry = RunRegistry(tmp_path / "registry")
      issued = registry.issue(
          run_id="RUN-EXP-0001-proxy-development-01",
          policy_id="deepseek-v4-pro-v1",
          budget=budget(),
          expected_attempts=1,
          expires_at=now + timedelta(hours=1),
          now=now,
      )
      ledger = BudgetLedger(tmp_path / "budgets")
      ledger.register_run(
          issued.run_id,
          budget(),
          now,
          expected_attempts=1,
      )
      provider = provider_app(captured)
      app = create_app(
          policy=ModelPolicy(
              policy_id="deepseek-v4-pro-v1",
              provider="deepseek",
              model="deepseek-v4-pro",
          ),
          pricing=Pricing(
              unit_tokens=1_000_000,
              cache_hit_input=Decimal("0.003625"),
              cache_miss_input=Decimal("0.435"),
              output=Decimal("0.87"),
          ),
          registry=registry,
          ledger=ledger,
          observations=ObservationLog(tmp_path / "observations.jsonl"),
          provider_base_url="http://provider.test",
          provider_api_key="host-secret",
          provider_transport=ASGITransport(app=provider),
          now=lambda: now,
      )
      return httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://proxy"), issued


  @pytest.mark.anyio
  async def test_request_is_pinned_and_host_key_is_injected(tmp_path: Path) -> None:
      captured: list[dict[str, object]] = []
      proxy, issued = await client(tmp_path, captured)
      async with proxy:
          response = await proxy.post(
              "/v1/chat/completions",
              headers={"Authorization": f"Bearer {issued.token}"},
              json={"messages": [{"role": "user", "content": "hi"}]},
          )
      assert response.status_code == 200
      assert captured == [
          {
              "body": {
                  "messages": [{"role": "user", "content": "hi"}],
                  "model": "deepseek-v4-pro",
              },
              "authorization": "Bearer host-secret",
          }
      ]
      assert "host-secret" not in response.text
      assert issued.token not in response.text


  @pytest.mark.anyio
  async def test_stream_is_transparent_and_usage_is_observed(tmp_path: Path) -> None:
      captured: list[dict[str, object]] = []
      proxy, issued = await client(tmp_path, captured)
      async with proxy:
          async with proxy.stream(
              "POST",
              "/v1/chat/completions",
              headers={"Authorization": f"Bearer {issued.token}"},
              json={"stream": True, "messages": [{"role": "user", "content": "hi"}]},
          ) as response:
              body = b"".join([chunk async for chunk in response.aiter_bytes()])
      assert response.status_code == 200
      assert b"data: [DONE]" in body
      rows = [
          json.loads(line)
          for line in (tmp_path / "observations.jsonl").read_text().splitlines()
      ]
      assert rows[-1]["input_tokens"] == 10
      assert rows[-1]["cache_tokens"] == 2
      assert rows[-1]["output_tokens"] == 3
      assert rows[-1]["observed_model"] == "deepseek-v4-pro"


  @pytest.mark.anyio
  async def test_wrong_model_unknown_token_and_unknown_endpoint_fail_closed(
      tmp_path: Path,
  ) -> None:
      captured: list[dict[str, object]] = []
      proxy, issued = await client(tmp_path, captured)
      async with proxy:
          wrong_model = await proxy.post(
              "/v1/chat/completions",
              headers={"Authorization": f"Bearer {issued.token}"},
              json={"model": "deepseek-v4-flash", "messages": []},
          )
          unknown = await proxy.post(
              "/v1/chat/completions",
              headers={"Authorization": "Bearer unknown"},
              json={"messages": []},
          )
          endpoint = await proxy.post(
              "/v1/responses",
              headers={"Authorization": f"Bearer {issued.token}"},
              json={"input": "x"},
          )
      assert wrong_model.status_code == 400
      assert unknown.status_code == 401
      assert endpoint.status_code == 404
      assert captured == []
  ```

- [ ] **Step 5: Run the tests and observe the missing modules.** Run:

  ```bash
  uv run pytest tests/proxy/test_registry.py tests/proxy/test_observations.py tests/proxy/test_app.py -q
  ```

  Expected failure includes `ModuleNotFoundError` for `research.der.proxy.registry`.

- [ ] **Step 6: Implement hashed, exclusive run-token registration.** Create `research/der/proxy/registry.py`:

  ```python
  """Short-lived proxy authorization bound to one run and one policy."""

  from __future__ import annotations

  import hashlib
  import secrets
  from dataclasses import dataclass
  from datetime import datetime
  from pathlib import Path
  from typing import Annotated

  from pydantic import Field

  from research.der.contracts.base import StrictModel, canonical_json_bytes
  from research.der.contracts.eval import RunBudget, RunId
  from research.der.util.atomic import create_exclusive_bytes
  from research.der.util.jsonio import read_json


  class RunRegistration(StrictModel):
      schema_version: str = "der.proxy-registration.v1"
      run_id: RunId
      token_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
      policy_id: str
      budget: RunBudget
      expected_attempts: Annotated[int, Field(gt=0)]
      created_at: datetime
      expires_at: datetime


  @dataclass(frozen=True, slots=True)
  class IssuedRunToken:
      run_id: str
      token: str
      expires_at: datetime


  class RunRegistry:
      def __init__(self, root: Path) -> None:
          self.root = root
          self.root.mkdir(parents=True, exist_ok=True)

      @staticmethod
      def token_digest(token: str) -> str:
          return hashlib.sha256(token.encode("utf-8")).hexdigest()

      def issue(
          self,
          *,
          run_id: str,
          policy_id: str,
          budget: RunBudget,
          expected_attempts: int,
          expires_at: datetime,
          now: datetime,
      ) -> IssuedRunToken:
          if expires_at <= now:
              raise ValueError("proxy registration expiry must be in the future")
          token = secrets.token_urlsafe(32)
          record = RunRegistration(
              run_id=run_id,
              token_sha256=self.token_digest(token),
              policy_id=policy_id,
              budget=budget,
              expected_attempts=expected_attempts,
              created_at=now,
              expires_at=expires_at,
          )
          create_exclusive_bytes(
              self.root / f"{run_id}.json", canonical_json_bytes(record), mode=0o600
          )
          return IssuedRunToken(run_id=run_id, token=token, expires_at=expires_at)

      def authorize(self, token: str, *, now: datetime) -> RunRegistration:
          digest = self.token_digest(token)
          matches: list[RunRegistration] = []
          for path in sorted(self.root.glob("RUN-*.json")):
              record = RunRegistration.model_validate(read_json(path))
              if secrets.compare_digest(record.token_sha256, digest):
                  matches.append(record)
          if not matches:
              raise PermissionError("unknown proxy run token")
          if len(matches) != 1:
              raise PermissionError("proxy run token is not uniquely registered")
          record = matches[0]
          if now >= record.expires_at:
              raise PermissionError("expired proxy run token")
          return record
  ```

- [ ] **Step 7: Implement append-only proxy observations.** Create `research/der/proxy/observations.py`:

  ```python
  """Durable, append-only proxy model and resource observations."""

  from __future__ import annotations

  import os
  from datetime import datetime
  from decimal import Decimal
  from pathlib import Path
  from typing import Annotated, Literal

  from pydantic import Field

  from research.der.contracts.base import StrictModel, canonical_json_bytes
  from research.der.contracts.eval import RunId, Sha256


  class ModelObservation(StrictModel):
      schema_version: Literal["der.proxy-observation.v1"] = "der.proxy-observation.v1"
      timestamp: datetime
      run_id: RunId
      request_id: str
      role: Literal["rollout", "adb", "evolve"]
      requested_model: str | None
      observed_model: str
      status_code: Annotated[int, Field(ge=100, le=599)]
      input_tokens: Annotated[int, Field(ge=0)]
      cache_tokens: Annotated[int, Field(ge=0)]
      output_tokens: Annotated[int, Field(ge=0)]
      cost_usd: Annotated[Decimal, Field(ge=0)]
      response_sha256: Sha256


  class ObservationLog:
      def __init__(self, path: Path) -> None:
          self.path = path
          self.path.parent.mkdir(parents=True, exist_ok=True)

      def append(self, observation: ModelObservation) -> None:
          data = canonical_json_bytes(observation)
          descriptor = os.open(
              self.path,
              os.O_WRONLY | os.O_CREAT | os.O_APPEND,
              0o600,
          )
          try:
              written = os.write(descriptor, data)
              if written != len(data):
                  raise OSError(f"short observation write: {written}/{len(data)}")
              os.fsync(descriptor)
          finally:
              os.close(descriptor)
  ```

- [ ] **Step 8: Implement the proxy, strict usage extraction, pricing, streaming, and budget reconciliation.** Create `research/der/proxy/app.py`:

  ```python
  """Host-only model pinning and RunBudget enforcement proxy."""

  from __future__ import annotations

  import hashlib
  import json
  import secrets
  from collections.abc import AsyncIterator, Callable
  from dataclasses import dataclass
  from datetime import datetime
  from decimal import Decimal
  from typing import Any

  import httpx
  from fastapi import FastAPI, Header, HTTPException, Request
  from fastapi.responses import JSONResponse, StreamingResponse

  from research.der.contracts.eval import TokenUsage
  from research.der.errors import PolicyViolationError
  from research.der.proxy.budget import BudgetExceededError, BudgetLedger
  from research.der.proxy.observations import ModelObservation, ObservationLog
  from research.der.proxy.policy import ModelPolicy
  from research.der.proxy.registry import RunRegistration, RunRegistry


  @dataclass(frozen=True, slots=True)
  class Pricing:
      unit_tokens: int
      cache_hit_input: Decimal
      cache_miss_input: Decimal
      output: Decimal

      def cost(self, usage: TokenUsage) -> Decimal:
          uncached = max(usage.input_tokens - usage.cache_tokens, 0)
          return (
              Decimal(usage.cache_tokens) * self.cache_hit_input
              + Decimal(uncached) * self.cache_miss_input
              + Decimal(usage.output_tokens) * self.output
          ) / Decimal(self.unit_tokens)


  def _usage(payload: dict[str, Any]) -> TokenUsage:
      raw = payload.get("usage")
      if not isinstance(raw, dict):
          raise ValueError("provider response has no usage object")
      required = ("prompt_tokens", "completion_tokens")
      if any(not isinstance(raw.get(key), int) for key in required):
          raise ValueError("provider usage lacks integer prompt_tokens/completion_tokens")
      cache = raw.get("prompt_cache_hit_tokens", 0)
      if not isinstance(cache, int):
          raise ValueError("provider prompt_cache_hit_tokens is not an integer")
      return TokenUsage(
          input_tokens=raw["prompt_tokens"],
          cache_tokens=cache,
          output_tokens=raw["completion_tokens"],
      )


  def _stream_payload(data: bytes) -> dict[str, Any]:
      payloads: list[dict[str, Any]] = []
      for line in data.decode("utf-8").splitlines():
          if not line.startswith("data: ") or line == "data: [DONE]":
              continue
          parsed = json.loads(line[6:])
          if isinstance(parsed, dict) and "usage" in parsed:
              payloads.append(parsed)
      if len(payloads) != 1:
          raise ValueError(f"stream must contain exactly one usage payload, got {len(payloads)}")
      return payloads[0]


  def create_app(
      *,
      policy: ModelPolicy,
      pricing: Pricing,
      registry: RunRegistry,
      ledger: BudgetLedger,
      observations: ObservationLog,
      provider_base_url: str,
      provider_api_key: str,
      provider_transport: httpx.AsyncBaseTransport | None = None,
      now: Callable[[], datetime],
  ) -> FastAPI:
      app = FastAPI()

      @app.get("/healthz")
      async def healthz() -> dict[str, str]:
          return {"status": "ok", "policy_id": policy.policy_id, "model": policy.model}

      def authorize(value: str | None) -> RunRegistration:
          if value is None or not value.startswith("Bearer "):
              raise HTTPException(status_code=401, detail="missing bearer run token")
          try:
              return registry.authorize(value[7:], now=now())
          except PermissionError as exc:
              raise HTTPException(status_code=401, detail=str(exc)) from exc

      @app.post("/v1/chat/completions")
      async def chat_completions(
          request: Request,
          authorization: str | None = Header(default=None),
      ) -> StreamingResponse | JSONResponse:
          registration = authorize(authorization)
          if registration.policy_id != policy.policy_id:
              raise HTTPException(status_code=403, detail="run token uses another policy")
          try:
              incoming = await request.json()
              if not isinstance(incoming, dict):
                  raise ValueError("request body must be an object")
              prepared = policy.prepare_request(incoming, inbound_headers=request.headers)
          except (ValueError, PolicyViolationError) as exc:
              raise HTTPException(status_code=400, detail=str(exc)) from exc
          request_id = "req-" + secrets.token_hex(12)
          try:
              ledger.authorize_request(registration.run_id, request_id, now())
          except BudgetExceededError as exc:
              raise HTTPException(status_code=429, detail=str(exc)) from exc
          headers = dict(prepared.forward_headers)
          headers["authorization"] = f"Bearer {provider_api_key}"
          client = httpx.AsyncClient(
              base_url=provider_base_url,
              transport=provider_transport,
              timeout=httpx.Timeout(600.0, connect=30.0),
          )
          provider_request = client.build_request(
              "POST", "/chat/completions", headers=headers, json=prepared.payload
          )
          response = await client.send(provider_request, stream=True)

          async def finalize(data: bytes) -> None:
              observed_model = "unrecorded"
              usage = TokenUsage()
              cost = Decimal("0")
              try:
                  payload = (
                      _stream_payload(data)
                      if prepared.payload.get("stream") is True
                      else json.loads(data)
                  )
                  if not isinstance(payload, dict):
                      raise ValueError("provider response body is not an object")
                  if payload.get("model") is not None:
                      observed_model = str(payload["model"])
                  if response.status_code >= 400:
                      raise ValueError(
                          f"provider returned HTTP {response.status_code}"
                      )
                  if payload.get("model") != policy.model:
                      raise ValueError(
                          f"provider observed model {payload.get('model')!r}, "
                          f"expected {policy.model!r}"
                      )
                  usage = _usage(payload)
                  cost = pricing.cost(usage)
                  ledger.reconcile_response(
                      registration.run_id,
                      request_id,
                      usage=usage,
                      cost_usd=cost,
                      now=now(),
                  )
              finally:
                  # Every terminal provider exchange is observed — success or
                  # fault — so downstream classification never guesses (D5).
                  observations.append(
                      ModelObservation(
                          timestamp=now(),
                          run_id=registration.run_id,
                          request_id=request_id,
                          role="rollout",
                          requested_model=prepared.requested_model,
                          observed_model=observed_model,
                          status_code=response.status_code,
                          input_tokens=usage.input_tokens,
                          cache_tokens=usage.cache_tokens,
                          output_tokens=usage.output_tokens,
                          cost_usd=cost,
                          response_sha256=hashlib.sha256(data).hexdigest(),
                      )
                  )
                  await response.aclose()
                  await client.aclose()

          if prepared.payload.get("stream") is True:
              async def stream() -> AsyncIterator[bytes]:
                  collected = bytearray()
                  async for chunk in response.aiter_bytes():
                      collected.extend(chunk)
                      yield chunk
                  await finalize(bytes(collected))
              return StreamingResponse(
                  stream(),
                  status_code=response.status_code,
                  media_type=response.headers.get("content-type", "text/event-stream"),
              )
          body = await response.aread()
          try:
              await finalize(body)
          except (ValueError, BudgetExceededError) as exc:
              raise HTTPException(status_code=502, detail=str(exc)) from exc
          return JSONResponse(
              content=json.loads(body),
              status_code=response.status_code,
          )

      return app
  ```

  This version intentionally exposes only Chat Completions because the locked DeepSeek and Qwen path is OpenAI Chat Completions. An unrecognized endpoint returns `404`; do not add an unused compatibility surface.

- [ ] **Step 9: Add strict JSON reading used by registry and later evidence code.** Create `research/der/util/jsonio.py`:

  ```python
  """Strict JSON and JSONL reads with source-qualified failures."""

  from __future__ import annotations

  import json
  from pathlib import Path
  from typing import Any


  def read_json(path: Path) -> Any:
      try:
          return json.loads(path.read_text(encoding="utf-8"))
      except FileNotFoundError:
          raise
      except (OSError, json.JSONDecodeError) as exc:
          raise ValueError(f"cannot read JSON {path}: {exc}") from exc


  def read_jsonl(path: Path) -> list[dict[str, Any]]:
      rows: list[dict[str, Any]] = []
      for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
          try:
              value = json.loads(line)
          except json.JSONDecodeError as exc:
              raise ValueError(f"invalid JSONL {path}:{line_number}: {exc}") from exc
          if not isinstance(value, dict):
              raise ValueError(f"JSONL row is not an object: {path}:{line_number}")
          rows.append(value)
      return rows
  ```

- [ ] **Step 10: Run proxy tests, static checks, and a key-leak scan.** Run:

  ```bash
  uv run pytest tests/proxy -q
  uv run ruff check research/der/proxy research/der/util/jsonio.py tests/proxy
  uv run mypy research/der
  ! grep -R -E 'host-secret|sk-[A-Za-z0-9]{12,}' \
    research/config research/der tests/proxy --exclude='test_app.py'
  ```

  Expected output: all proxy tests pass; no diagnostics; the final grep command is silent. `test_app.py` contains the literal fake secret only to assert that it is not returned or persisted.

- [ ] **Step 11: Verify the actual pricing arithmetic.** Run:

  ```bash
  uv run python - <<'PY'
  from decimal import Decimal
  from research.der.contracts.eval import TokenUsage
  from research.der.proxy.app import Pricing

  pricing = Pricing(
      unit_tokens=1_000_000,
      cache_hit_input=Decimal("0.003625"),
      cache_miss_input=Decimal("0.435"),
      output=Decimal("0.87"),
  )
  observed = pricing.cost(TokenUsage(input_tokens=1_000_000, cache_tokens=0, output_tokens=1_000_000))
  assert observed == Decimal("1.305"), observed
  print(observed)
  PY
  ```

  Expected output: `1.305`.

- [ ] **Step 12: Commit.** Run:

  ```bash
  git add \
    research/config/runtime-policy.toml research/der/proxy \
    research/der/util/jsonio.py tests/proxy
  git commit -m "feat: add keyless model-pinning budget proxy"
  ```

### Task 9: Strict Qwen JSONL parser, honest ATIF v1.7 conversion, and `DerQwenAgent`

**Files:**
- Create: `research/der/agents/__init__.py`
- Create: `research/der/agents/qwen_stream.py`
- Create: `research/der/agents/qwen_atif.py`
- Create: `research/der/agents/qwen.py`
- Create: `tests/agents/test_qwen_stream.py`
- Create: `tests/agents/test_qwen_atif.py`
- Create: `tests/agents/test_qwen_agent.py`
- Create: `tests/fixtures/qwen/success.jsonl`
- Create: `tests/fixtures/qwen/turn-limit.jsonl`
- Create: `tests/fixtures/qwen/wall-limit.jsonl`
- Create: `tests/fixtures/qwen/tool-limit.jsonl`
- Create: `tests/fixtures/qwen/malformed.jsonl`
- Create: `tests/fixtures/qwen/multi-session.jsonl`

**Interfaces:**
- Consumes: Pier `BaseAgent`/`BaseEnvironment`/`AgentContext`; Qwen v0.20.0 headless flags; passed V3 archive pin; owner settings/environment JSON supplied by V2; managed staged harness.
- Produces: `parse_qwen_stream(path: Path, expected_session_id: str | None = None) -> QwenSession`, `to_atif(session: QwenSession, model_name: str) -> tuple[Trajectory, AgentContext]`, and import path `research.der.agents.qwen:DerQwenAgent` with Pier's exact async `setup` and `run` methods.

- [ ] **Step 1: Verify all three external contracts at their pinned revisions.** Run:

  ```bash
  git -C /var/cache/der/sources/pier show \
    e69a20e4e0ac073ec71fde0274bab3d9f40bac87:src/pier/agents/base.py \
    | sed -n '1,260p'
  git -C /var/cache/der/sources/pier grep -n \
    -e 'class BaseEnvironment' -e 'async def exec' -e 'async def upload' \
    e69a20e4e0ac073ec71fde0274bab3d9f40bac87 -- src/pier/environments src/pier/models
  git -C /var/cache/der/sources/qwen-code grep -n \
    -e 'output-format' -e 'stream-json' -e 'max-session-turns' \
    -e 'max-wall-time' -e 'max-tool-calls' -e 'session_start' \
    92fda5603e84ef62a1b29bf6faf4f6a8124a2bf7 -- packages | head -140
  ```

  Record in review notes that Pier's class is `pier.agents.base.BaseAgent`; `setup(environment)` and `run(instruction, environment, context)` are async; and Qwen v0.20.0 supports `-p`, `--output-format stream-json`, `--yolo`, `--max-session-turns`, `--max-wall-time`, and `--max-tool-calls`. The implementation below does not locate sessions by recency.

- [ ] **Step 2: Create source-shaped JSONL fixtures.** Create `tests/fixtures/qwen/success.jsonl`:

  ```jsonl
  {"type":"system","subtype":"session_start","uuid":"evt-0","session_id":"sess-001","timestamp":"2026-07-21T10:00:00Z","model":"deepseek-v4-pro"}
  {"type":"assistant","uuid":"evt-1","session_id":"sess-001","timestamp":"2026-07-21T10:00:01Z","parent_tool_use_id":null,"message":{"id":"msg-1","type":"message","role":"assistant","model":"deepseek-v4-pro","content":[{"type":"text","text":"I will inspect the repository."},{"type":"tool_use","id":"tool-1","name":"run_shell_command","input":{"command":"git status --short"}}],"stop_reason":null,"usage":{"input_tokens":100,"output_tokens":10,"cache_read_input_tokens":20,"total_tokens":110}}}
  {"type":"assistant","uuid":"evt-2","session_id":"sess-001","timestamp":"2026-07-21T10:00:03Z","parent_tool_use_id":"tool-1","message":{"id":"msg-2","type":"message","role":"assistant","model":"deepseek-v4-pro","content":[{"type":"text","text":"Implemented and committed."}],"stop_reason":null,"usage":{"input_tokens":120,"output_tokens":12,"cache_read_input_tokens":30,"total_tokens":132}}}
  {"type":"result","subtype":"success","uuid":"evt-3","session_id":"sess-001","timestamp":"2026-07-21T10:00:04Z","is_error":false,"duration_ms":4000,"num_turns":2,"result":"Implemented and committed.","usage":{"input_tokens":120,"output_tokens":12,"cache_read_input_tokens":30,"total_tokens":132},"permission_denials":[]}
  ```

  Create `turn-limit.jsonl`, `wall-limit.jsonl`, and `tool-limit.jsonl` with the same first `session_start` row followed by, respectively:

  ```jsonl
  {"type":"result","subtype":"error_max_turns","session_id":"sess-001","timestamp":"2026-07-21T10:00:04Z","result":"Maximum session turns reached"}
  ```

  ```jsonl
  {"type":"result","subtype":"error_max_wall_time","session_id":"sess-001","timestamp":"2026-07-21T10:00:04Z","result":"Maximum wall time reached"}
  ```

  ```jsonl
  {"type":"result","subtype":"error_max_tool_calls","session_id":"sess-001","timestamp":"2026-07-21T10:00:04Z","result":"Maximum tool calls reached"}
  ```

  Create `tests/fixtures/qwen/malformed.jsonl`:

  ```jsonl
  {"type":"system","subtype":"session_start","session_id":"sess-001"}
  {this-is-not-json}
  ```

  Create `tests/fixtures/qwen/multi-session.jsonl`:

  ```jsonl
  {"type":"system","subtype":"session_start","session_id":"sess-old","timestamp":"2026-07-21T09:00:00Z"}
  {"type":"result","subtype":"success","session_id":"sess-old","timestamp":"2026-07-21T09:00:02Z","result":"old","usage":{"input_tokens":1,"output_tokens":1,"cache_read_input_tokens":0,"total_tokens":2}}
  {"type":"system","subtype":"session_start","session_id":"sess-wanted","timestamp":"2026-07-21T10:00:00Z"}
  {"type":"result","subtype":"success","session_id":"sess-wanted","timestamp":"2026-07-21T10:00:02Z","result":"wanted","usage":{"input_tokens":2,"output_tokens":3,"cache_read_input_tokens":0,"total_tokens":5}}
  ```

  These fixtures are parser contracts, not live Pier fixtures. V1 replaces any source-shape discrepancy with the recorded concrete field paths before scored use.

- [ ] **Step 3: Write parser and ATIF tests.** Create `tests/agents/test_qwen_stream.py`:

  ```python
  from __future__ import annotations

  from pathlib import Path

  import pytest

  from research.der.agents.qwen_stream import QwenLimit, parse_qwen_stream

  FIXTURES = Path("tests/fixtures/qwen")


  def test_success_has_one_exact_session_and_cumulative_usage() -> None:
      session = parse_qwen_stream(FIXTURES / "success.jsonl")
      assert session.session_id == "sess-001"
      assert session.result_text == "Implemented and committed."
      assert session.limit is None
      assert session.usage.input_tokens == 120
      assert session.usage.cache_tokens == 30
      assert session.usage.output_tokens == 12
      assert session.tool_calls == 1
      assert session.turns == 2


  @pytest.mark.parametrize(
      ("fixture", "expected"),
      [
          ("turn-limit.jsonl", QwenLimit.TURNS),
          ("wall-limit.jsonl", QwenLimit.WALL),
          ("tool-limit.jsonl", QwenLimit.TOOLS),
      ],
  )
  def test_limit_subtypes_are_explicit(fixture: str, expected: QwenLimit) -> None:
      assert parse_qwen_stream(FIXTURES / fixture).limit is expected


  def test_malformed_jsonl_is_rejected_with_line_number() -> None:
      with pytest.raises(ValueError, match="malformed.jsonl:2"):
          parse_qwen_stream(FIXTURES / "malformed.jsonl")


  def test_multi_session_requires_the_explicit_id() -> None:
      with pytest.raises(ValueError, match="multiple session ids"):
          parse_qwen_stream(FIXTURES / "multi-session.jsonl")
      selected = parse_qwen_stream(
          FIXTURES / "multi-session.jsonl", expected_session_id="sess-wanted"
      )
      assert selected.result_text == "wanted"
      with pytest.raises(ValueError, match="was not present"):
          parse_qwen_stream(
              FIXTURES / "multi-session.jsonl", expected_session_id="sess-missing"
          )
  ```

  Create `tests/agents/test_qwen_atif.py`:

  ```python
  from __future__ import annotations

  from pathlib import Path

  from research.der.agents.qwen_atif import to_atif
  from research.der.agents.qwen_stream import parse_qwen_stream


  def test_conversion_is_atif_v17_and_does_not_invent_provider_identity() -> None:
      session = parse_qwen_stream(Path("tests/fixtures/qwen/success.jsonl"))
      trajectory, context = to_atif(session, model_name="deepseek-v4-pro")
      payload = trajectory.model_dump(mode="json", exclude_none=True)
      assert payload["schema_version"] == "ATIF-v1.7"
      assert payload["agent"]["name"] == "der-qwen"
      assert payload["agent"]["model_name"] == "deepseek-v4-pro"
      assert [step["step_id"] for step in payload["steps"]] == list(
          range(1, len(payload["steps"]) + 1)
      )
      assert payload["final_metrics"]["total_prompt_tokens"] == 120
      assert payload["final_metrics"]["total_cached_tokens"] == 30
      assert payload["final_metrics"]["total_completion_tokens"] == 12
      assert context.n_input_tokens == 120
      assert context.n_output_tokens == 12
      assert context.n_agent_steps == len(payload["steps"])
      assert context.metadata["qwen_session_id"] == "sess-001"
  ```

- [ ] **Step 4: Write a contract-level agent test with a fake Pier environment.** Create `tests/agents/test_qwen_agent.py`:

  ```python
  from __future__ import annotations

  import inspect
  import json
  from pathlib import Path

  from pier.agents.base import BaseAgent

  from research.der.agents.qwen import DerQwenAgent


  def test_agent_implements_exact_pier_surface() -> None:
      assert issubclass(DerQwenAgent, BaseAgent)
      assert DerQwenAgent.SUPPORTS_ATIF is True
      assert DerQwenAgent.SUPPORTS_WINDOWS is False
      assert inspect.iscoroutinefunction(DerQwenAgent.setup)
      assert inspect.iscoroutinefunction(DerQwenAgent.run)
      assert DerQwenAgent.name() == "der-qwen"
      assert DerQwenAgent.version() == "1"


  def test_command_has_locked_headless_limits_and_no_provider_key(tmp_path: Path) -> None:
      agent = DerQwenAgent(
          logs_dir=tmp_path,
          qwen_archive="/cache/qwen.tar.gz",
          qwen_installer="/cache/install.sh",
          qwen_binary="/opt/qwen/bin/qwen",
          managed_harness="/cache/harness",
          owner_settings_json=json.dumps({"model": {"name": "deepseek-v4-pro"}}),
          qwen_environment_json=json.dumps(
              {
                  "DER_RUN_TOKEN": "run-token",
                  "OPENAI_BASE_URL": "http://proxy.invalid/v1",
                  "OPENAI_API_KEY": "run-token",
              }
          ),
          max_session_turns=10,
          max_wall_time="30m",
          max_tool_calls=200,
      )
      command = agent.command("repair the task")
      assert command == [
          "/opt/qwen/bin/qwen",
          "-p",
          "repair the task",
          "--output-format",
          "stream-json",
          "--yolo",
          "--max-session-turns",
          "10",
          "--max-wall-time",
          "30m",
          "--max-tool-calls",
          "200",
      ]
      serialized = json.dumps(agent.qwen_environment, sort_keys=True)
      assert "DEEPSEEK_API_KEY" not in serialized
  ```

- [ ] **Step 5: Run agent tests and observe missing implementation modules.** Run:

  ```bash
  uv run pytest tests/agents -q
  ```

  Expected failure includes `ModuleNotFoundError: No module named 'research.der.agents'`.

- [ ] **Step 6: Implement the strict one-session parser with terminal result and usage invariants.** Create an empty `research/der/agents/__init__.py`. Create `research/der/agents/qwen_stream.py`:

  ```python
  """Strict parser for Qwen v0.20.0 headless stream JSONL."""

  from __future__ import annotations

  import json
  from dataclasses import dataclass
  from enum import StrEnum
  from pathlib import Path
  from typing import Any

  from research.der.contracts.eval import TokenUsage


  class QwenLimit(StrEnum):
      TURNS = "turns"
      WALL = "wall"
      TOOLS = "tools"


  LIMIT_SUBTYPES = {
      "error_max_turns": QwenLimit.TURNS,
      "error_max_wall_time": QwenLimit.WALL,
      "error_max_tool_calls": QwenLimit.TOOLS,
  }


  @dataclass(frozen=True, slots=True)
  class QwenEvent:
      line_number: int
      raw: dict[str, Any]


  @dataclass(frozen=True, slots=True)
  class QwenSession:
      session_id: str
      events: tuple[QwenEvent, ...]
      result_text: str
      success: bool
      limit: QwenLimit | None
      usage: TokenUsage
      tool_calls: int
      turns: int


  def _read(path: Path) -> list[QwenEvent]:
      events: list[QwenEvent] = []
      for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
          try:
              value = json.loads(line)
          except json.JSONDecodeError as exc:
              raise ValueError(f"{path}:{line_number}: invalid JSON: {exc.msg}") from exc
          if not isinstance(value, dict):
              raise ValueError(f"{path}:{line_number}: event must be an object")
          events.append(QwenEvent(line_number=line_number, raw=value))
      if not events:
          raise ValueError(f"{path}: stream is empty")
      return events


  def usage_from_event(value: dict[str, Any]) -> TokenUsage | None:
      raw = value.get("usage")
      message = value.get("message")
      if raw is None and isinstance(message, dict):
          raw = message.get("usage")
      if raw is None:
          return None
      if not isinstance(raw, dict):
          raise ValueError("Qwen usage must be an object")
      prompt = raw.get("input_tokens")
      completion = raw.get("output_tokens")
      cache = raw.get("cache_read_input_tokens", 0)
      if not all(isinstance(item, int) and item >= 0 for item in (prompt, completion, cache)):
          raise ValueError(
              "Qwen usage.input_tokens, output_tokens, and "
              "cache_read_input_tokens must be non-negative integers"
          )
      total = raw.get("total_tokens")
      if total is not None and (
          not isinstance(total, int) or total < prompt + completion
      ):
          raise ValueError("Qwen usage.total_tokens is inconsistent")
      return TokenUsage(
          input_tokens=prompt,
          cache_tokens=cache,
          output_tokens=completion,
      )


  def _count_nested_type(value: Any, wanted: str) -> int:
      if isinstance(value, dict):
          return int(value.get("type") == wanted) + sum(
              _count_nested_type(item, wanted) for item in value.values()
          )
      if isinstance(value, list):
          return sum(_count_nested_type(item, wanted) for item in value)
      return 0

  def parse_qwen_stream(
      path: Path, expected_session_id: str | None = None
  ) -> QwenSession:
      all_events = _read(path)
      session_ids = {
          value
          for event in all_events
          if isinstance((value := event.raw.get("session_id")), str)
      }
      if expected_session_id is None:
          if len(session_ids) != 1:
              raise ValueError(f"{path}: multiple session ids require explicit selection: {session_ids}")
          selected_id = next(iter(session_ids))
      else:
          selected_id = expected_session_id
          if selected_id not in session_ids:
              raise ValueError(f"session id {selected_id!r} was not present in {path}")
      events = tuple(
          event for event in all_events if event.raw.get("session_id") == selected_id
      )
      starts = [
          event
          for event in events
          if event.raw.get("type") == "system"
          and event.raw.get("subtype") == "session_start"
      ]
      terminals = [event for event in events if event.raw.get("type") == "result"]
      if len(starts) != 1 or len(terminals) != 1:
          raise ValueError(
              f"session {selected_id} requires one session_start and one result; "
              f"observed {len(starts)}/{len(terminals)}"
          )
      terminal = terminals[0].raw
      subtype = terminal.get("subtype")
      success = subtype == "success"
      limit = LIMIT_SUBTYPES.get(str(subtype))
      if not success and limit is None:
          raise ValueError(f"unclassified Qwen terminal subtype: {subtype!r}")
      usage_events = [usage for event in events if (usage := usage_from_event(event.raw)) is not None]
      if not usage_events:
          raise ValueError(f"session {selected_id} contains no usage event")
      usage = usage_events[-1]
      if any(
          earlier.input_tokens > usage.input_tokens
          or earlier.cache_tokens > usage.cache_tokens
          or earlier.output_tokens > usage.output_tokens
          for earlier in usage_events[:-1]
      ):
          raise ValueError("Qwen cumulative usage regressed within the session")
      turns = terminal.get("num_turns", 0)
      if not isinstance(turns, int) or turns < 0:
          raise ValueError("Qwen num_turns must be a non-negative integer")
      result = terminal.get("result", "")
      if not isinstance(result, str):
          raise ValueError("Qwen result text must be a string")
      return QwenSession(
          session_id=selected_id,
          events=events,
          result_text=result,
          success=success,
          limit=limit,
          usage=usage,
          tool_calls=sum(_count_nested_type(event.raw, "tool_use") for event in events),
          turns=turns,
      )
  ```

- [ ] **Step 7: Implement honest ATIF v1.7 conversion using Pier's bundled models.** Create `research/der/agents/qwen_atif.py`:

  ```python
  """Translate canonical Qwen events into Pier ATIF without provider-name fiction."""

  from __future__ import annotations

  from datetime import UTC, datetime
  from typing import Any

  from pier.models.agent.context import AgentContext
  from pier.models.trajectories.agent import Agent
  from pier.models.trajectories.final_metrics import FinalMetrics
  from pier.models.trajectories.metrics import Metrics
  from pier.models.trajectories.step import Step
  from pier.models.trajectories.trajectory import Trajectory

  from research.der.agents.qwen_stream import QwenEvent, QwenSession, usage_from_event


  def _timestamp(event: QwenEvent) -> str:
      value = event.raw.get("timestamp")
      if isinstance(value, str):
          return value
      return datetime.now(UTC).isoformat().replace("+00:00", "Z")


  def _message(event: QwenEvent) -> str | None:
      raw = event.raw
      message = raw.get("message")
      if isinstance(message, dict):
          content = message.get("content")
          if isinstance(content, str):
              return content
          if isinstance(content, list):
              text = "".join(
                  block["text"]
                  for block in content
                  if isinstance(block, dict)
                  and block.get("type") == "text"
                  and isinstance(block.get("text"), str)
              )
              if text:
                  return text
      for key in ("output", "result"):
          if isinstance(raw.get(key), str):
              return raw[key]
      return ""


  def _step(event: QwenEvent, index: int, model_name: str) -> Step:
      raw = event.raw
      kind = raw.get("type")
      source = "agent" if kind == "assistant" else "system"
      metrics = None
      usage = usage_from_event(raw)
      if source == "agent" and usage is not None:
          metrics = Metrics(
              prompt_tokens=usage.input_tokens,
              completion_tokens=usage.output_tokens,
              cached_tokens=usage.cache_tokens,
              extra={"qwen_usage": raw.get("message", {}).get("usage")},
          )
      extra: dict[str, Any] = {"qwen_event": raw}
      return Step(
          step_id=index,
          timestamp=_timestamp(event),
          source=source,
          model_name=model_name if source == "agent" else None,
          message=_message(event),
          metrics=metrics,
          llm_call_count=1 if source == "agent" else None,
          extra=extra,
      )


  def to_atif(session: QwenSession, model_name: str) -> tuple[Trajectory, AgentContext]:
      steps = tuple(
          _step(event, index, model_name)
          for index, event in enumerate(session.events, start=1)
      )
      trajectory = Trajectory(
          session_id=session.session_id,
          trajectory_id=session.session_id,
          agent=Agent(
              name="der-qwen",
              version="1",
              model_name=model_name,
              tool_definitions=None,
              extra={"runtime": "qwen-code", "qwen_version": "0.20.0"},
          ),
          steps=steps,
          final_metrics=FinalMetrics(
              total_prompt_tokens=session.usage.input_tokens,
              total_completion_tokens=session.usage.output_tokens,
              total_cached_tokens=session.usage.cache_tokens,
              total_steps=len(steps),
              extra={
                  "tool_calls": session.tool_calls,
                  "session_turns": session.turns,
                  "limit": session.limit.value if session.limit else None,
              },
          ),
          extra={"qwen_result": session.result_text},
      )
      context = AgentContext(
          n_input_tokens=session.usage.input_tokens,
          n_output_tokens=session.usage.output_tokens,
          n_cache_tokens=session.usage.cache_tokens,
          n_agent_steps=len(steps),
          rollout_details=None,
          metadata={
              "qwen_session_id": session.session_id,
              "tool_calls": session.tool_calls,
              "session_turns": session.turns,
          },
      )
      return trajectory, context
  ```

  Before committing, compare every constructor field above with the locked Pier source. If Pier's concrete field is named differently, change the internal call and its test together; do not create an alias class.

- [ ] **Step 8: Implement `DerQwenAgent` with explicit paths and no recency lookup.** Create `research/der/agents/qwen.py`:

  ```python
  """Pier custom agent that runs pinned Qwen Code from a local archive."""

  from __future__ import annotations

  import json
  import shlex
  from pathlib import Path
  from typing import Any

  from pier.agents.base import BaseAgent
  from pier.environments.base import BaseEnvironment
  from pier.models.agent.context import AgentContext
  from pier.models.agent.network import NetworkAllowlist
  from pier.utils.trajectory_utils import format_trajectory_json

  from research.der.agents.qwen_atif import to_atif
  from research.der.agents.qwen_stream import parse_qwen_stream


  class DerQwenAgent(BaseAgent):
      SUPPORTS_ATIF = True
      SUPPORTS_WINDOWS = False

      def __init__(
          self,
          *,
          qwen_archive: str,
          qwen_installer: str,
          qwen_binary: str,
          managed_harness: str,
          owner_settings_json: str,
          qwen_environment_json: str,
          max_session_turns: int = 10,
          max_wall_time: str = "30m",
          max_tool_calls: int = 200,
          model_name: str = "deepseek-v4-pro",
          **kwargs: Any,
      ) -> None:
          super().__init__(**kwargs)
          self.qwen_archive = qwen_archive
          self.qwen_installer = qwen_installer
          self.qwen_binary = qwen_binary
          self.managed_harness = managed_harness
          self.owner_settings = json.loads(owner_settings_json)
          self.qwen_environment = json.loads(qwen_environment_json)
          if not isinstance(self.owner_settings, dict) or not isinstance(
              self.qwen_environment, dict
          ):
              raise ValueError("owner settings and Qwen environment must be JSON objects")
          if "DEEPSEEK_API_KEY" in self.qwen_environment:
              raise ValueError("trial environment cannot receive DEEPSEEK_API_KEY")
          self.max_session_turns = max_session_turns
          self.max_wall_time = max_wall_time
          self.max_tool_calls = max_tool_calls
          self.model_name = model_name
          self.workspace = Path("/workspace")
          self.rollout_home = Path("/tmp/der-qwen-home")
          self.stream_path = Path("/tmp/der-qwen-stream.jsonl")

      @staticmethod
      def name() -> str:
          return "der-qwen"

      @staticmethod
      def version() -> str:
          return "1"

      @staticmethod
      def import_path() -> str:
          return "research.der.agents.qwen:DerQwenAgent"

      def network_allowlist(self) -> NetworkAllowlist:
          from urllib.parse import urlparse

          endpoint = str(
              self.qwen_environment.get("OPENAI_BASE_URL")
              or self.qwen_environment.get("QWEN_PROXY_BASE_URL")
              or ""
          )
          host = urlparse(endpoint).hostname
          if not host:
              raise ValueError("Qwen proxy endpoint has no hostname")
          return NetworkAllowlist(domains=[host])

      def command(self, instruction: str) -> list[str]:
          return [
              self.qwen_binary,
              "-p",
              instruction,
              "--output-format",
              "stream-json",
              "--yolo",
              "--max-session-turns",
              str(self.max_session_turns),
              "--max-wall-time",
              self.max_wall_time,
              "--max-tool-calls",
              str(self.max_tool_calls),
          ]

      async def setup(self, environment: BaseEnvironment) -> None:
          await environment.upload_file(Path(self.qwen_archive), "/opt/cache/qwen-archive")
          await environment.upload_file(
              Path(self.qwen_installer), "/opt/cache/install-qwen-standalone.sh"
          )
          await environment.upload_dir(Path(self.managed_harness), str(self.workspace))
          settings = json.dumps(self.owner_settings, sort_keys=True, separators=(",", ":"))
          script = f"""
          set -euo pipefail
          rm -rf /opt/qwen {shlex.quote(str(self.rollout_home))}
          mkdir -p /opt/qwen {shlex.quote(str(self.rollout_home))} {shlex.quote(str(self.workspace / '.qwen'))}
          cp /opt/cache/qwen-archive /opt/cache/{shlex.quote(Path(self.qwen_archive).name)}
          cp /opt/cache/install-qwen-standalone.sh /opt/cache/install.sh
          chmod 0555 /opt/cache/install.sh
          bash /opt/cache/install.sh --archive /opt/cache/{shlex.quote(Path(self.qwen_archive).name)} --prefix /opt/qwen
          cat > {shlex.quote(str(self.workspace / '.qwen/settings.json'))} <<'DER_SETTINGS'
          {settings}
          DER_SETTINGS
          chmod 0600 {shlex.quote(str(self.workspace / '.qwen/settings.json'))}
          test -x {shlex.quote(self.qwen_binary)}
          """
          result = await environment.exec(script, timeout_sec=300)
          if result.return_code != 0:
              raise RuntimeError(
                  f"Qwen offline setup failed: rc={result.return_code} stderr={result.stderr}"
              )

      async def run(
          self,
          instruction: str,
          environment: BaseEnvironment,
          context: AgentContext,
      ) -> None:
          environment_values = {
              str(key): str(value) for key, value in self.qwen_environment.items()
          }
          environment_values.update(
              {
                  "HOME": str(self.rollout_home),
                  "QWEN_CODE_SYSTEM_SETTINGS_PATH": str(
                      self.workspace / ".qwen/settings.json"
                  ),
              }
          )
          command = self.command(instruction)
          stderr_path = Path("/tmp/der-qwen-stderr.log")
          shell = (
              shlex.join(command)
              + f" > {shlex.quote(str(self.stream_path))}"
              + f" 2> {shlex.quote(str(stderr_path))}"
          )
          result = await environment.exec(
              shell,
              cwd=str(self.workspace),
              env=environment_values,
              timeout_sec=None,
          )
          self.logs_dir.mkdir(parents=True, exist_ok=True)
          local_stream = self.logs_dir / "qwen-stream.jsonl"
          local_stderr = self.logs_dir / "qwen-stderr.log"
          await environment.download_file(str(self.stream_path), local_stream)
          await environment.download_file(str(stderr_path), local_stderr)
          session = parse_qwen_stream(local_stream)
          trajectory, observed_context = to_atif(session, model_name=self.model_name)
          (self.logs_dir / "trajectory.json").write_text(
              format_trajectory_json(trajectory.to_json_dict()) + "\n",
              encoding="utf-8",
          )
          for field_name in (
              "n_input_tokens",
              "n_cache_tokens",
              "n_output_tokens",
              "n_agent_steps",
              "metadata",
          ):
              setattr(context, field_name, getattr(observed_context, field_name))
          if result.return_code not in {0, 53, 55}:
              raise RuntimeError(
                  f"Qwen exited unexpectedly: rc={result.return_code} stderr={result.stderr}"
              )
          if result.return_code == 0 and not session.success:
              raise RuntimeError("Qwen process succeeded but stream terminal was not success")
  ```

  This is the exact Pier 0.3.0 contract: `BaseAgent.run(...) -> None`. The agent mutates the supplied `AgentContext` and writes `trajectory.json` under Pier's host-side `logs_dir`; it must never return a private tuple protocol. The `setup()` install line mirrors the V3 pin's recorded `install_argv`; if V3 pinned an argv without `--prefix` (see Task 6 Step 1's adaptation note), mirror the pinned argv here instead and point the `find` binary discovery at the pinned install root — the pin, not this listing, is authoritative for the install command.

- [ ] **Step 9: Run the tests; repair only source-contract field mismatches, then lock the fixtures.** Run:

  ```bash
  uv run pytest tests/agents -q
  uv run ruff check research/der/agents tests/agents
  uv run mypy research/der
  ```

  Expected output: all tests pass and static checks are clean. A Pier constructor or return-type mismatch is repaired by consulting the exact source file from Step 1 and updating the test in the same step. Do not wrap Pier models in parallel local types.

- [ ] **Step 10: Verify importability exactly as Pier will import it.** Run:

  ```bash
  uv run python - <<'PY'
  from importlib import import_module
  from pier.agents.base import BaseAgent

  module_name, object_name = "research.der.agents.qwen:DerQwenAgent".split(":", 1)
  cls = getattr(import_module(module_name), object_name)
  assert issubclass(cls, BaseAgent)
  assert cls.import_path() == "research.der.agents.qwen:DerQwenAgent"
  print(cls.name(), cls.version(), cls.SUPPORTS_ATIF)
  PY
  ```

  Expected output: `der-qwen 1 True`.

- [ ] **Step 11: Commit.** Run:

  ```bash
  git add research/der/agents tests/agents tests/fixtures/qwen
  git commit -m "feat: run pinned Qwen as a Pier ATIF agent"
  ```

### Task 10: Discovery V2 — prove the real eight-point acceptance chain and pin the proxy route

**Files:**
- Modify: `research/der/proxy/app.py`
- Create: `scripts/discover_v2_acceptance_chain.py`
- Create: `tests/discovery/test_v2_acceptance_chain.py`
- Create after live probe: `research-plan/pins/v2-acceptance-chain.md`
- Create as preregistration proof: `experiments/EXP-0001-acceptance-chain.md`

**Interfaces:**
- Consumes: `stage_harness(managed_root: Path, owner_overlay_root: Path, destination: Path, rollout_home: Path) -> StagingResult` from Task 7; `DerQwenAgent` from Task 9; V3 pin fields `archive_path`, `installer_path`, `qwen_binary`, `container_image_id`; V7 pin fields `task_root`, `task_ids`; `RunRegistry.issue(...) -> IssuedRunToken` and `BudgetLedger.register_run(...)` from Tasks 5/8; `require_passed_pin`/`write_discovery_pin` from Task 6
- Produces: passed pin fields `job_result_path`, `trial_root`, `run_id`, `proxy_base_url`, `proxy_host`, `allowlist_domains`, and six evidence paths consumed by Tasks 11–13 and every live evaluator task

- [ ] **Step 1: Add a deterministic proxy process entry point.** Append to `research/der/proxy/app.py`:

  ```python
  def load_policy_and_pricing(policy_path: Path) -> tuple[ModelPolicy, Pricing]:
      raw = tomllib.loads(policy_path.read_text(encoding="utf-8"))
      pricing = raw["pricing"]
      return (
          ModelPolicy(
              policy_id=str(raw["policy_id"]),
              provider=str(raw["provider"]),
              model=str(raw["model"]),
          ),
          Pricing(
              unit_tokens=int(pricing["unit_tokens"]),
              cache_hit_input=Decimal(str(pricing["cache_hit_input_per_unit"])),
              cache_miss_input=Decimal(str(pricing["cache_miss_input_per_unit"])),
              output=Decimal(str(pricing["output_per_unit"])),
          ),
      )


  def main() -> None:
      import argparse
      import os

      import uvicorn

      parser = argparse.ArgumentParser()
      parser.add_argument("--host", default="127.0.0.1")
      parser.add_argument("--port", type=int, default=8787)
      parser.add_argument("--policy", type=Path, required=True)
      parser.add_argument("--state-dir", type=Path, required=True)
      args = parser.parse_args()
      provider_key = os.environ.get("DEEPSEEK_API_KEY")
      if not provider_key:
          raise SystemExit("DEEPSEEK_API_KEY is absent from the host proxy process")
      policy, pricing = load_policy_and_pricing(args.policy)
      application = create_app(
          policy=policy,
          pricing=pricing,
          registry=RunRegistry(args.state_dir / "registry"),
          ledger=BudgetLedger(args.state_dir / "budgets"),
          observations=ObservationLog(args.state_dir / "observations.jsonl"),
          provider_base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
          provider_api_key=provider_key,
          now=utc_now,
      )
      uvicorn.run(application, host=args.host, port=args.port, log_level="info")


  if __name__ == "__main__":
      main()
  ```

  Add these imports to the existing module from Task 8 rather than duplicating any definition (`ModelPolicy`, `Pricing`, `BudgetLedger`, `ObservationLog`, and `RunRegistry` are already imported there; only these are new):

  ```python
  import tomllib
  from pathlib import Path

  from research.der.util.time import utc_now
  ```

  `Decimal` is already imported at module top. The state directory holds `registry/` (per-run JSON registrations), `budgets/` (per-run ledgers), and `observations.jsonl` — the same stores the tests in Task 8 exercised.

- [ ] **Step 2: Write the discovery validator test first.** Create `tests/discovery/test_v2_acceptance_chain.py`:

  ```python
  from __future__ import annotations

  import json
  from pathlib import Path

  import pytest

  from scripts.discover_v2_acceptance_chain import inspect_acceptance_chain


  def test_requires_every_acceptance_link(tmp_path: Path) -> None:
      job = tmp_path / "job"
      trial = job / "trial-1"
      trial.mkdir(parents=True)
      (job / "result.json").write_text('{"job_id":"v2-probe"}\n')
      (trial / "reward.json").write_text('{"reward":1}\n')
      (trial / "ctrf.json").write_text('{"results":{"summary":{"tests":1}}}\n')
      (trial / "trajectory.json").write_text(
          json.dumps({"schema_version": "ATIF-v1.7", "steps": [{}]}) + "\n"
      )
      (trial / "agent.patch").write_text("diff --git a/a b/a\n")
      (trial / "agent.log").write_text("qwen\n")
      (trial / "result.json").write_text('{"task_name":"probe"}\n')
      observations = tmp_path / "observations.jsonl"
      observations.write_text(
          json.dumps(
              {
                  "run_id": "RUN-EXP-0001-acceptance-chain-smoke-01",
                  "request_id": "req-1",
                  "role": "rollout",
                  "observed_model": "deepseek-v4-pro",
                  "status_code": 200,
              }
          )
          + "\n"
      )
      report = inspect_acceptance_chain(
          job_result_path=job / "result.json",
          job_dir=job,
          observations_path=observations,
          run_id="RUN-EXP-0001-acceptance-chain-smoke-01",
          proxy_base_url="http://172.17.0.1:8787/v1",
          allowlist_domains=("172.17.0.1",),
      )
      assert report["observed_models"] == ["deepseek-v4-pro"]
      assert set(report["evidence"]) == {
          "reward",
          "ctrf",
          "trajectory",
          "patch",
          "agent_log",
          "trial_result",
      }


  def test_missing_link_stops_instead_of_guessing(tmp_path: Path) -> None:
      (tmp_path / "result.json").write_text('{"job_id":"v2-probe"}\n')
      with pytest.raises(ValueError, match="exactly one non-empty reward.json"):
          inspect_acceptance_chain(
              job_result_path=tmp_path / "result.json",
              job_dir=tmp_path,
              observations_path=tmp_path / "observations.jsonl",
              run_id="RUN-EXP-0001-acceptance-chain-smoke-01",
              proxy_base_url="http://host.invalid/v1",
              allowlist_domains=("host.invalid",),
          )
  ```

- [ ] **Step 3: Run the test and observe the missing discovery module.** Run:

  ```bash
  uv run pytest tests/discovery/test_v2_acceptance_chain.py -q
  ```

  Expected failure: `ModuleNotFoundError: No module named 'scripts.discover_v2_acceptance_chain'`.

- [ ] **Step 4: Implement the fail-closed evidence inspector.** Create `scripts/discover_v2_acceptance_chain.py`:

  ```python
  #!/usr/bin/env python3
  """Record V2 only after one real Pier run proves every acceptance link."""

  from __future__ import annotations

  import argparse
  import json
  import sys
  from pathlib import Path
  from typing import Any
  from urllib.parse import urlparse

  from research.der.pins import write_discovery_pin
  from research.der.util.hashing import sha256_file

  REQUIRED = {
      "reward": "reward.json",
      "ctrf": "ctrf.json",
      "trajectory": "trajectory.json",
  }


  def _one(root: Path, name: str, predicate: object = None) -> Path:
      del predicate
      matches = [p for p in root.rglob(name) if p.is_file() and p.stat().st_size > 0]
      if len(matches) != 1:
          raise ValueError(f"expected exactly one non-empty {name}; observed {matches}")
      return matches[0].resolve()


  def _one_suffix(root: Path, suffix: str, label: str) -> Path:
      matches = [p for p in root.rglob(f"*{suffix}") if p.is_file() and p.stat().st_size > 0]
      if len(matches) != 1:
          raise ValueError(f"expected exactly one non-empty {label}; observed {matches}")
      return matches[0].resolve()


  def inspect_acceptance_chain(
      *,
      job_result_path: Path,
      job_dir: Path,
      observations_path: Path,
      run_id: str,
      proxy_base_url: str,
      allowlist_domains: tuple[str, ...],
  ) -> dict[str, Any]:
      if not job_result_path.is_file():
          raise ValueError(f"explicit Pier result path does not exist: {job_result_path}")
      evidence = {label: str(_one(job_dir, name)) for label, name in REQUIRED.items()}
      evidence["patch"] = str(_one_suffix(job_dir, ".patch", "pre-artifacts patch"))
      logs = [p for p in job_dir.rglob("*.log") if p.is_file() and p.stat().st_size > 0]
      if not logs:
          raise ValueError("no non-empty agent log was captured")
      evidence["agent_log"] = str(sorted(logs)[0].resolve())
      result_candidates = [
          p
          for p in job_dir.rglob("*.json")
          if p.resolve() != Path(evidence["reward"])
          and p.resolve() != Path(evidence["ctrf"])
          and p.resolve() != Path(evidence["trajectory"])
          and p.is_file()
      ]
      if not result_candidates:
          raise ValueError("no structured trial result JSON was captured")
      evidence["trial_result"] = str(sorted(result_candidates)[0].resolve())
      observations = [
          json.loads(line)
          for line in observations_path.read_text(encoding="utf-8").splitlines()
          if line.strip()
      ]
      selected = [row for row in observations if row.get("run_id") == run_id]
      if not selected:
          raise ValueError(f"proxy observation log has no rows for run {run_id}")
      completed = [row for row in selected if row.get("status_code") == 200]
      if not completed:
          raise ValueError("proxy recorded no completed (status 200) observation for the run")
      models = sorted({str(row.get("observed_model")) for row in completed})
      if models != ["deepseek-v4-pro"]:
          raise ValueError(f"proxy observed forbidden model set: {models}")
      host = urlparse(proxy_base_url).hostname
      if not host or tuple(allowlist_domains) != (host,):
          raise ValueError("allowlist must contain only the concrete proxy host")
      return {
          "job_result_path": str(job_result_path.resolve()),
          "trial_root": str(job_dir.resolve()),
          "run_id": run_id,
          "proxy_base_url": proxy_base_url,
          "proxy_host": host,
          "allowlist_domains": list(allowlist_domains),
          "observed_models": models,
          "evidence": evidence,
          "evidence_sha256": {
              key: sha256_file(Path(value)) for key, value in evidence.items()
          },
      }


  def main() -> int:
      parser = argparse.ArgumentParser()
      parser.add_argument("--job-result", type=Path, required=True)
      parser.add_argument("--job-dir", type=Path, required=True)
      parser.add_argument("--observations", type=Path, required=True)
      parser.add_argument("--run-id", required=True)
      parser.add_argument("--proxy-base-url", required=True)
      parser.add_argument("--allowlist-domain", action="append", required=True)
      parser.add_argument(
          "--pin", type=Path, default=Path("research-plan/pins/v2-acceptance-chain.md")
      )
      args = parser.parse_args()
      try:
          values = inspect_acceptance_chain(
              job_result_path=args.job_result,
              job_dir=args.job_dir,
              observations_path=args.observations,
              run_id=args.run_id,
              proxy_base_url=args.proxy_base_url,
              allowlist_domains=tuple(args.allowlist_domain),
          )
      except Exception as exc:
          write_discovery_pin(
              args.pin,
              verification_id="V2",
              status="blocked",
              command=" ".join(sys.argv),
              observation={"error": str(exc)},
              stop_reason="The real eight-point chain contradicted or failed to prove the approved architecture.",
          )
          print(f"STOP V2: {exc}", file=sys.stderr)
          return 78
      write_discovery_pin(
          args.pin,
          verification_id="V2",
          status="passed",
          command=" ".join(sys.argv),
          observation=values,
      )
      print(json.dumps(values, indent=2, sort_keys=True))
      return 0


  if __name__ == "__main__":
      raise SystemExit(main())
  ```

- [ ] **Step 5: Run the unit test to green.** Run:

  ```bash
  uv run pytest tests/discovery/test_v2_acceptance_chain.py -q
  uv run ruff check scripts/discover_v2_acceptance_chain.py tests/discovery/test_v2_acceptance_chain.py
  ```

  Expected output: `2 passed` and no Ruff diagnostics.

- [ ] **Step 6: Create and commit the discovery experiment before issuing a run token.** Generate `experiments/EXP-0001-acceptance-chain.md` through the strict contract (never hand-write lifecycle YAML), using the real identity of the fixture harness this probe stages:

  ```bash
  uv run python - <<'PY'
  from decimal import Decimal
  from pathlib import Path

  from research.der.contracts.eval import HarnessIdentity, RunBudget
  from research.der.contracts.experiment import (
      ExperimentContract, ExperimentFrontMatter, ExperimentStatus, Guardrail,
  )
  from research.der.experiments.records import create_record
  from research.der.util.git import git_tree_oid, head_commit
  from research.der.util.hashing import sha256_file
  from research.der.util.time import utc_now

  now = utc_now()
  # The probe stages the committed fixture harness (harness/ is created at
  # Milestone 5); the runtime-manifest digest for this discovery probe is the
  # digest of the owner policy file, recorded here so identity is re-provable.
  identity = HarnessIdentity(
      source_commit=head_commit(Path.cwd()),
      harness_tree_oid=git_tree_oid(Path.cwd(), Path("tests/fixtures/harness/managed")),
      runtime_manifest_digest=sha256_file(Path("research/config/runtime-policy.toml")),
  )
  front = ExperimentFrontMatter(
      experiment_id="EXP-0001-acceptance-chain",
      slug="acceptance-chain",
      title="V2 acceptance-chain discovery probe",
      status=ExperimentStatus.PROPOSED,
      created_at=now,
      updated_at=now,
      baseline_identity=identity,
      candidate_identity=identity,
      contract=ExperimentContract(
          hypothesis=(
              "The approved keyless Qwen-through-proxy Pier path can complete one "
              "DeepSWE task and preserve all canonical evidence links."
          ),
          primary_metric="confirmation_macro_pass_at_1",
          minimum_effect=Decimal("0"),
          guardrails=(
              Guardrail(metric="invalid_fraction", operator="<=", threshold=Decimal("0")),
          ),
          falsifier=(
              "Any missing acceptance link, provider key in the trial, non-proxy "
              "model traffic, or inferred result path falsifies the probe."
          ),
          suite_version="discovery-v1",
          k=1,
          budget=RunBudget(
              max_cost_usd=Decimal("20"),
              max_wall_seconds=7200,
              max_attempts=1,
              max_input_tokens=2_000_000,
              max_output_tokens=250_000,
              max_tool_calls=500,
              max_session_turns=10,
          ),
      ),
      run_ids=(),
  )
  body = (
      "# EXP-0001 — V2 acceptance-chain discovery\n\n"
      "## Rationale\n\n"
      "Scored-path acceptance probe; no harness hypothesis. The generated result\n"
      "block is absent until the finalizer has a complete explicit Pier result.\n\n"
      "## Evidence links\n\n"
      "Attached after the run.\n"
  )
  create_record(Path("experiments/EXP-0001-acceptance-chain.md"), front, body)
  print("created")
  PY
  uv run python - <<'PY'
  from pathlib import Path
  from research.der.experiments.records import read_record
  record = read_record(Path("experiments/EXP-0001-acceptance-chain.md"))
  assert record.front_matter.experiment_id == "EXP-0001-acceptance-chain"
  print(record.front_matter.experiment_id, record.front_matter.status.value)
  PY
  git add experiments/EXP-0001-acceptance-chain.md
  git commit -m "research: preregister Pier acceptance-chain probe"
  ```

  Expected output: `created`, then `EXP-0001-acceptance-chain proposed`, followed by a successful commit. The commit-before-run is the preregistration proof. (`confirmation_macro_pass_at_1` is the schema's contract metric; this probe's decision is recorded as non-promotional in Task 15.)

- [ ] **Step 7: Start the host proxy with the provider key injected only into that process.** The owner creates `~/.config/der/deepseek.env` outside Git with dotenvx and confirms its plaintext expansion is never printed. Run:

  ```bash
  install -d -m 0700 var/state/proxy
  dotenvx run -f ~/.config/der/deepseek.env -- \
    uv run python -m research.der.proxy.app \
      --host 0.0.0.0 \
      --port 8787 \
      --policy research/config/runtime-policy.toml \
      --state-dir var/state/proxy \
      >var/state/proxy/server.log 2>&1 &
  echo $! > var/state/proxy/server.pid
  for n in $(seq 1 30); do
    curl -fsS http://127.0.0.1:8787/healthz && break
    sleep 1
  done
  test "$(cat var/state/proxy/server.pid)" -gt 1
  ```

  Expected health output: `{"status":"ok","policy_id":"deepseek-v4-pro-v1","model":"deepseek-v4-pro"}`. The shell environment running Pier must satisfy `test -z "${DEEPSEEK_API_KEY-}"`.

- [ ] **Step 8: Discover a reachable host address without weakening Pier isolation.** Run exactly this probe; it tests three concrete candidates and emits only a winner that reaches `/healthz` from a throwaway container:

  ```bash
  TASK_IMAGE=$(uv run python - <<'PY'
  from research.der.pins import require_passed_pin
  print(require_passed_pin("V3")["container_image_id"])
  PY
  )
  BRIDGE_GATEWAY=$(docker network inspect bridge --format '{{(index .IPAM.Config 0).Gateway}}')
  PRIVATE_HOST=$(ip -json route get 1.1.1.1 | \
    uv run python -c 'import json,sys; print(json.load(sys.stdin)[0]["prefsrc"])')
  : > var/state/proxy/route-probe.txt
  for candidate in host.docker.internal "$BRIDGE_GATEWAY" "$PRIVATE_HOST"; do
    extra=()
    if [ "$candidate" = host.docker.internal ]; then
      extra=(--add-host host.docker.internal:host-gateway)
    fi
    if docker run --rm "${extra[@]}" "$TASK_IMAGE" \
      sh -lc "python - <<'PY'
  import urllib.request
  print(urllib.request.urlopen('http://$candidate:8787/healthz', timeout=3).read().decode())
  PY" >>var/state/proxy/route-probe.txt 2>&1; then
      printf '%s\n' "$candidate" > var/state/proxy/proxy-host
      break
    fi
  done
  test -s var/state/proxy/proxy-host || {
    cat var/state/proxy/route-probe.txt >&2
    printf '%s\n' 'STOP V2: no tested container-to-host route reached the proxy' >&2
    exit 78
  }
  cat var/state/proxy/proxy-host
  ```

  Expected output: one concrete hostname or IP. This value is provisional until the real Pier run in Step 11 proves it under Pier's filtered network. Do not put it in source code.

- [ ] **Step 9: Stage the harness and issue one short-lived, exact run grant.** The probe stages the committed fixture harness (the managed `harness/` tree is created at Milestone 5); the registry and ledger directories are the ones the proxy process from Step 7 reads. Run:

  ```bash
  export EXPERIMENT_ID=EXP-0001-acceptance-chain
  export RUN_ID=RUN-EXP-0001-acceptance-chain-smoke-01
  export JOB_ID=v2-probe
  export PROXY_HOST=$(cat var/state/proxy/proxy-host)
  export PROXY_BASE_URL="http://${PROXY_HOST}:8787/v1"
  export STAGED_HARNESS="$PWD/var/staging/${RUN_ID}/harness"
  mkdir -p var/staging/overlay-empty
  export RUN_TOKEN=$(uv run python - <<'PY'
  import os
  from datetime import timedelta
  from decimal import Decimal
  from pathlib import Path

  from research.der.contracts.eval import RunBudget
  from research.der.harness.stage import stage_harness
  from research.der.proxy.budget import BudgetLedger
  from research.der.proxy.registry import RunRegistry
  from research.der.util.time import utc_now

  budget = RunBudget(
      max_cost_usd=Decimal("20"),
      max_wall_seconds=7200,
      max_attempts=1,
      max_input_tokens=2_000_000,
      max_output_tokens=250_000,
      max_tool_calls=500,
      max_session_turns=10,
  )
  run_id = os.environ["RUN_ID"]
  now = utc_now()
  stage_harness(
      Path("tests/fixtures/harness/managed"),
      Path("var/staging/overlay-empty"),
      Path(os.environ["STAGED_HARNESS"]),
      Path(f"var/staging/{run_id}/rollout-home"),
  )
  issued = RunRegistry(Path("var/state/proxy/registry")).issue(
      run_id=run_id,
      policy_id="deepseek-v4-pro-v1",
      budget=budget,
      expected_attempts=1,
      expires_at=now + timedelta(hours=3),
      now=now,
  )
  BudgetLedger(Path("var/state/proxy/budgets")).register_run(
      run_id, budget, now, expected_attempts=1
  )
  print(issued.token)
  PY
  )
  test -n "$RUN_TOKEN"
  test -z "${DEEPSEEK_API_KEY-}"
  ```

  Expected output is silent. `RUN_TOKEN` is an expiring proxy credential, not a provider credential. The Qwen rollout HOME inside the container is selected by `DerQwenAgent`; the host-side `rollout-home` directory exists only to satisfy the staging contract and stays empty.

- [ ] **Step 10: Resolve the pinned task and Qwen archive values from passed pin files.** Run:

  ```bash
  eval "$(uv run python - <<'PY'
  import shlex
  from research.der.pins import require_passed_pin
  v3 = require_passed_pin("V3")
  v7 = require_passed_pin("V7")
  values = {
      "DEEPSWE_PATH": v7["task_root"],
      "TASK_NAME": v7["task_ids"][0],
      "QWEN_ARCHIVE": v3["archive_path"],
      "QWEN_INSTALLER": v3["installer_path"],
      "QWEN_BINARY": v3["qwen_binary"],
  }
  for key, value in values.items():
      print(f"export {key}={shlex.quote(str(value))}")
  PY
  )"
  printf '%s\n' "$TASK_NAME"
  ```

  Expected output: the first V7-audited DeepSWE task ID. No revision, path, or binary is typed from memory.

- [ ] **Step 11: Run the real Pier command and capture the explicit result path from Pier stdout.** First construct complete owner settings using the Qwen v0.20.0 OpenAI provider shape verified in Task 9:

  ```bash
  export OWNER_SETTINGS_JSON=$(uv run python - <<'PY'
  import json, os
  print(json.dumps({
      "modelProviders": {
          "openai": {
              "protocol": "openai",
              "models": [{
                  "id": "deepseek-v4-pro",
                  "name": "DeepSeek v4 pro through der proxy",
                  "baseUrl": os.environ["PROXY_BASE_URL"],
                  "envKey": "OPENAI_API_KEY"
              }]
          }
      },
      "security": {"auth": {"selectedType": "openai"}},
      "model": {"name": "deepseek-v4-pro"},
      "general": {"enableAutoUpdate": False}
  }, separators=(",", ":"), sort_keys=True))
  PY
  )
  export QWEN_ENV_JSON=$(uv run python - <<'PY'
  import json, os
  print(json.dumps({
      "OPENAI_API_KEY": os.environ["RUN_TOKEN"],
      "OPENAI_BASE_URL": os.environ["PROXY_BASE_URL"],
      "OPENAI_MODEL": "deepseek-v4-pro",
      "QWEN_CODE_SUPPRESS_YOLO_WARNING": "1"
  }, separators=(",", ":"), sort_keys=True))
  PY
  )
  mkdir -p var/runs/v2
  set +e
  uv run pier run \
    --job-name "$JOB_ID" \
    --jobs-dir "$PWD/var/runs/v2" \
    --path "$DEEPSWE_PATH" \
    --include-task-name "$TASK_NAME" \
    --n-attempts 1 \
    --n-concurrent 1 \
    --max-retries 0 \
    --agent-import-path research.der.agents.qwen:DerQwenAgent \
    --model deepseek-v4-pro \
    --agent-kwarg "qwen_archive=$QWEN_ARCHIVE" \
    --agent-kwarg "qwen_installer=$QWEN_INSTALLER" \
    --agent-kwarg "qwen_binary=$QWEN_BINARY" \
    --agent-kwarg "managed_harness=$STAGED_HARNESS" \
    --agent-kwarg "owner_settings_json=$OWNER_SETTINGS_JSON" \
    --agent-kwarg "qwen_environment_json=$QWEN_ENV_JSON" \
    --agent-kwarg max_session_turns=10 \
    --agent-kwarg max_wall_time=90m \
    --agent-kwarg max_tool_calls=200 \
    --env docker \
    --yes 2>&1 | tee var/runs/v2/pier.stdout
  rc=${PIPESTATUS[0]}
  set -e
  test "$rc" -eq 0 || {
    printf '%s\n' 'STOP V2: the real Pier run failed; preserve stdout and escalate' >&2
    exit 78
  }
  grep -E '^Results written to ' var/runs/v2/pier.stdout | tail -1 | \
    sed 's/^Results written to //' > var/runs/v2/result-path
  test -f "$(cat var/runs/v2/result-path)" || {
    printf '%s\n' 'STOP V2: Pier did not identify an existing result path' >&2
    exit 78
  }
  ```

  Expected observable output includes Pier's exact `Results written to ...` line and exit code zero. If the provisional route fails inside Pier, preserve the command output, write a blocked V2 pin with Step 12, and escalate; do not enable general internet access.

- [ ] **Step 12: Validate and record the eight-point chain.** Run:

  ```bash
  RESULT_PATH=$(cat var/runs/v2/result-path)
  JOB_DIR=$(dirname "$RESULT_PATH")
  uv run python scripts/discover_v2_acceptance_chain.py \
    --job-result "$RESULT_PATH" \
    --job-dir "$JOB_DIR" \
    --observations var/state/proxy/observations.jsonl \
    --run-id "$RUN_ID" \
    --proxy-base-url "$PROXY_BASE_URL" \
    --allowlist-domain "$PROXY_HOST" \
    | tee var/runs/v2/acceptance-inspection.json
  test "${PIPESTATUS[0]}" -eq 0
  uv run der pins assert V2
  ```

  Expected output is a passed V2 pin and JSON containing all six canonical evidence paths, `observed_models: ["deepseek-v4-pro"]`, the exact proxy route, and the explicit Pier result path. Exit 78 is a hard STOP.

- [ ] **Step 13: Prove the trial never received the provider key.** Run:

  ```bash
  JOB_DIR=$(dirname "$(cat var/runs/v2/result-path)")
  ! grep -R --binary-files=without-match -E \
    '(DEEPSEEK_API_KEY|api\.deepseek\.com|sk-[A-Za-z0-9_-]{16,})' \
    "$JOB_DIR" "$STAGED_HARNESS"
  grep -F 'deepseek-v4-pro' var/state/proxy/observations.jsonl >/dev/null
  ```

  Expected output is silent. Any match is a STOP and secret-incident escalation before another run.

- [ ] **Step 14: Commit.** Run:

  ```bash
  git add \
    research/der/proxy/app.py \
    scripts/discover_v2_acceptance_chain.py \
    tests/discovery/test_v2_acceptance_chain.py \
    research-plan/pins/v2-acceptance-chain.md
  git commit -m "test: pin the real Pier acceptance chain and proxy route"
  ```

### Task 11: Discovery V1 — pin Pier trial layout, reward/CTRF shapes, and ATIF v1.7 usage paths

**Files:**
- Create: `scripts/discover_v1_pier_artifacts.py`
- Create: `tests/discovery/test_v1_pier_artifacts.py`
- Create after live probe: `research-plan/pins/v1-pier-artifact-layout.md`
- Create from sanitized live evidence: `tests/fixtures/pier/v0.3.0/live-layout/`

**Interfaces:**
- Consumes: passed V2 pin with exact `job_result_path`, `trial_root`, and evidence paths
- Produces: passed pin fields `job_result_relative_path`, `trial_directory_relative_path`, `reward_file`, `reward_pointer`, `ctrf_file`, `ctrf_summary_pointer`, `trajectory_file`, `atif_schema_pointer`, `usage_pointers`, `task_name_pointer`, and `attempt_pointer`; sanitized fixtures consumed by Task 14

- [ ] **Step 1: Write recursive JSON-pointer discovery tests.** Create `tests/discovery/test_v1_pier_artifacts.py`:

  ```python
  from __future__ import annotations

  from scripts.discover_v1_pier_artifacts import (
      find_atif_usage_pointers,
      find_unique_reward_pointer,
      json_pointer_get,
  )


  def test_unique_reward_pointer() -> None:
      payload = {"reward": 1, "metadata": {"duration": 8}}
      assert find_unique_reward_pointer(payload) == "/reward"
      assert json_pointer_get(payload, "/reward") == 1


  def test_atif_usage_paths_include_step_and_final_metrics() -> None:
      payload = {
          "schema_version": "ATIF-v1.7",
          "steps": [
              {
                  "metrics": {
                      "prompt_tokens": 10,
                      "cached_tokens": 3,
                      "completion_tokens": 2,
                  }
              }
          ],
          "final_metrics": {
              "total_prompt_tokens": 10,
              "total_cached_tokens": 3,
              "total_completion_tokens": 2,
          },
      }
      pointers = find_atif_usage_pointers(payload)
      assert pointers == {
          "per_call_prompt": "/steps/0/metrics/prompt_tokens",
          "per_call_cached": "/steps/0/metrics/cached_tokens",
          "per_call_completion": "/steps/0/metrics/completion_tokens",
          "total_prompt": "/final_metrics/total_prompt_tokens",
          "total_cached": "/final_metrics/total_cached_tokens",
          "total_completion": "/final_metrics/total_completion_tokens",
      }
  ```

- [ ] **Step 2: Run the tests and observe the missing script.** Run:

  ```bash
  uv run pytest tests/discovery/test_v1_pier_artifacts.py -q
  ```

  Expected failure: `ModuleNotFoundError: No module named 'scripts.discover_v1_pier_artifacts'`.

- [ ] **Step 3: Implement strict shape discovery and fixture sanitization.** Create `scripts/discover_v1_pier_artifacts.py`:

  ```python
  #!/usr/bin/env python3
  """Inspect, pin, and sanitize one real Pier 0.3.0 trial."""

  from __future__ import annotations

  import argparse
  import json
  import shutil
  import sys
  from pathlib import Path
  from typing import Any, Iterator

  from research.der.pins import require_passed_pin, write_discovery_pin
  from research.der.util.hashing import sha256_bytes


  def walk(value: Any, pointer: str = "") -> Iterator[tuple[str, Any]]:
      yield pointer or "/", value
      if isinstance(value, dict):
          for key, item in value.items():
              escaped = str(key).replace("~", "~0").replace("/", "~1")
              yield from walk(item, f"{pointer}/{escaped}")
      elif isinstance(value, list):
          for index, item in enumerate(value):
              yield from walk(item, f"{pointer}/{index}")


  def json_pointer_get(value: Any, pointer: str) -> Any:
      current = value
      for part in pointer.removeprefix("/").split("/") if pointer != "/" else []:
          token = part.replace("~1", "/").replace("~0", "~")
          current = current[int(token)] if isinstance(current, list) else current[token]
      return current


  def find_unique_reward_pointer(payload: Any) -> str:
      candidates = [
          pointer
          for pointer, value in walk(payload)
          if pointer.rsplit("/", 1)[-1].lower() in {"reward", "score"}
          and isinstance(value, (int, float))
          and not isinstance(value, bool)
          and 0.0 <= float(value) <= 1.0
      ]
      if len(candidates) != 1:
          raise ValueError(f"reward pointer is not unique: {candidates}")
      return candidates[0]


  def find_atif_usage_pointers(payload: dict[str, Any]) -> dict[str, str]:
      expected = {
          "per_call_prompt": "prompt_tokens",
          "per_call_cached": "cached_tokens",
          "per_call_completion": "completion_tokens",
          "total_prompt": "total_prompt_tokens",
          "total_cached": "total_cached_tokens",
          "total_completion": "total_completion_tokens",
      }
      result: dict[str, str] = {}
      for label, leaf in expected.items():
          candidates = [p for p, value in walk(payload) if p.endswith("/" + leaf) and isinstance(value, int)]
          candidates = [p for p in candidates if ("/steps/" in p) == label.startswith("per_call")]
          if not candidates:
              raise ValueError(f"ATIF field {leaf} was absent")
          result[label] = sorted(candidates)[0]
      return result


  def _load(path: Path) -> Any:
      return json.loads(path.read_text(encoding="utf-8"))


  def _sanitize(value: Any) -> Any:
      if isinstance(value, dict):
          result: dict[str, Any] = {}
          for key, item in value.items():
              lowered = key.lower()
              if any(token in lowered for token in ("key", "authorization", "token_ids", "logprobs")):
                  result[key] = "<redacted>"
              elif key in {"instruction", "result", "message", "reasoning_content"} and isinstance(item, str):
                  result[key] = {"sha256": sha256_bytes(item.encode()), "length": len(item)}
              else:
                  result[key] = _sanitize(item)
          return result
      if isinstance(value, list):
          return [_sanitize(item) for item in value]
      return value


  def main() -> int:
      parser = argparse.ArgumentParser()
      parser.add_argument("--pin", type=Path, default=Path("research-plan/pins/v1-pier-artifact-layout.md"))
      parser.add_argument("--fixtures", type=Path, default=Path("tests/fixtures/pier/v0.3.0/live-layout"))
      args = parser.parse_args()
      v2 = require_passed_pin("V2")
      evidence = {key: Path(value) for key, value in v2["evidence"].items()}
      try:
          reward = _load(evidence["reward"])
          ctrf = _load(evidence["ctrf"])
          trajectory = _load(evidence["trajectory"])
          reward_pointer = find_unique_reward_pointer(reward)
          if trajectory.get("schema_version") != "ATIF-v1.7":
              raise ValueError(f"unexpected ATIF schema: {trajectory.get('schema_version')!r}")
          ctrf_summary = [
              p
              for p, value in walk(ctrf)
              if p.endswith("/summary") and isinstance(value, dict)
          ]
          if len(ctrf_summary) != 1:
              raise ValueError(f"CTRF summary pointer is not unique: {ctrf_summary}")
          usage = find_atif_usage_pointers(trajectory)
          trial_root = Path(v2["trial_root"])
          job_result = Path(v2["job_result_path"])
          values = {
              "job_result_relative_path": str(job_result.relative_to(trial_root)),
              "trial_directory_relative_path": str(evidence["reward"].parent.relative_to(trial_root)),
              "reward_file": evidence["reward"].name,
              "reward_pointer": reward_pointer,
              "reward_observed": json_pointer_get(reward, reward_pointer),
              "ctrf_file": evidence["ctrf"].name,
              "ctrf_summary_pointer": ctrf_summary[0],
              "trajectory_file": evidence["trajectory"].name,
              "atif_schema_pointer": "/schema_version",
              "atif_schema_observed": "ATIF-v1.7",
              "usage_pointers": usage,
              "task_name_pointer": None,
              "attempt_pointer": None,
          }
          trial_result = _load(evidence["trial_result"])
          task_candidates = [p for p, value in walk(trial_result) if p.endswith("/task_name") and isinstance(value, str)]
          attempt_candidates = [p for p, value in walk(trial_result) if p.endswith(("/attempt", "/attempt_index")) and isinstance(value, int)]
          if len(task_candidates) != 1 or len(attempt_candidates) != 1:
              raise ValueError(
                  f"task/attempt identity pointers not unique: {task_candidates}/{attempt_candidates}"
              )
          values["task_name_pointer"] = task_candidates[0]
          values["attempt_pointer"] = attempt_candidates[0]
          args.fixtures.mkdir(parents=True, exist_ok=True)
          for label in ("reward", "ctrf", "trajectory", "trial_result"):
              destination = args.fixtures / f"{label}.json"
              destination.write_text(
                  json.dumps(_sanitize(_load(evidence[label])), indent=2, sort_keys=True) + "\n",
                  encoding="utf-8",
              )
          shutil.copy2(args.pin.parent / "v2-acceptance-chain.md", args.fixtures / "source-v2-pin.md")
      except Exception as exc:
          write_discovery_pin(
              args.pin,
              verification_id="V1",
              status="blocked",
              command=" ".join(sys.argv),
              observation={"error": str(exc)},
              stop_reason="Pier/DeepSWE artifact shape contradicted or did not prove the spec assumptions.",
          )
          print(f"STOP V1: {exc}", file=sys.stderr)
          return 78
      write_discovery_pin(
          args.pin,
          verification_id="V1",
          status="passed",
          command=" ".join(sys.argv),
          observation=values,
      )
      print(json.dumps(values, indent=2, sort_keys=True))
      return 0


  if __name__ == "__main__":
      raise SystemExit(main())
  ```

- [ ] **Step 4: Run unit tests to green.** Run:

  ```bash
  uv run pytest tests/discovery/test_v1_pier_artifacts.py -q
  uv run ruff check scripts/discover_v1_pier_artifacts.py tests/discovery/test_v1_pier_artifacts.py
  ```

  Expected output: `2 passed` and no Ruff diagnostics.

- [ ] **Step 5: Run the live V1 probe against the explicit V2 path.** Run:

  ```bash
  uv run python scripts/discover_v1_pier_artifacts.py | tee var/runs/v2/v1-shape.json
  test "${PIPESTATUS[0]}" -eq 0
  uv run der pins assert V1
  ```

  Expected output records exact relative paths and JSON pointers, including `ATIF-v1.7`. Exit 78 is a hard STOP; no normalizer code is written until resolved by the owner.

- [ ] **Step 6: Prove fixtures contain no secret-like text and preserve pinned pointers.** Run:

  ```bash
  ! grep -R -E '(sk-[A-Za-z0-9_-]{16,}|Bearer[[:space:]]+[A-Za-z0-9._-]+|DEEPSEEK_API_KEY)' \
    tests/fixtures/pier/v0.3.0/live-layout
  uv run python - <<'PY'
  from research.der.pins import require_passed_pin
  pin = require_passed_pin("V1")
  assert pin["atif_schema_observed"] == "ATIF-v1.7"
  assert set(pin["usage_pointers"]) == {
      "per_call_prompt", "per_call_cached", "per_call_completion",
      "total_prompt", "total_cached", "total_completion",
  }
  print(pin["reward_pointer"], pin["ctrf_summary_pointer"])
  PY
  ```

  Expected output: the exact reward and CTRF summary pointers from the live run.

- [ ] **Step 7: Commit.** Run:

  ```bash
  git add \
    scripts/discover_v1_pier_artifacts.py \
    tests/discovery/test_v1_pier_artifacts.py \
    tests/fixtures/pier/v0.3.0/live-layout \
    research-plan/pins/v1-pier-artifact-layout.md
  git commit -m "test: pin Pier trial and verifier artifact shapes"
  ```

### Task 12: Attempt taxonomy and discovery V5 induced-fault proof

**Files:**
- Create: `research/der/evaluation/classification.py`
- Create: `scripts/discover_v5_faults.py`
- Create: `tests/evaluation/test_classification.py`
- Create: `tests/discovery/test_v5_faults.py`
- Create after live probe: `research-plan/pins/v5-fault-classification.md`
- Create outside Git during probe: `var/faults/v5/`

**Interfaces:**
- Consumes: `OutcomeKind` and `FailureReason` from Task 2's `research.der.contracts.eval`; `QwenLimit` from Task 9; V1 artifact pointers; V2 live-run command and proxy route
- Produces: `AttemptEvidence`, `AttemptClassification`, and `classify_attempt(evidence: AttemptEvidence) -> AttemptClassification` (all in `research.der.evaluation.classification`); passed V5 pin consumed by Task 14 and live evaluator acceptance

- [ ] **Step 1: Write the taxonomy tests.** Create `tests/evaluation/test_classification.py`:

  ```python
  from __future__ import annotations

  import pytest

  from research.der.contracts.eval import FailureReason, OutcomeKind
  from research.der.evaluation.classification import AttemptEvidence, classify_attempt


  @pytest.mark.parametrize(
      ("evidence", "reason"),
      [
          (AttemptEvidence(proxy_http_status=401), FailureReason.PROVIDER),
          (AttemptEvidence(proxy_http_status=503), FailureReason.PROVIDER),
          (AttemptEvidence(network_error="connection reset"), FailureReason.NETWORK),
          (AttemptEvidence(infrastructure_error="docker daemon died"), FailureReason.INFRA),
          (AttemptEvidence(verifier_malformed=True), FailureReason.MALFORMED_VERIFIER),
      ],
  )
  def test_infrastructure_classes_are_invalid(
      evidence: AttemptEvidence, reason: FailureReason
  ) -> None:
      result = classify_attempt(evidence)
      assert result.status is OutcomeKind.INVALID
      assert result.failure_reason is reason
      assert result.reward is None


  @pytest.mark.parametrize("exit_code", [53, 55, 124])
  def test_agent_or_context_limits_are_failed(exit_code: int) -> None:
      result = classify_attempt(AttemptEvidence(qwen_exit_code=exit_code))
      assert result.status is OutcomeKind.FAILED
      assert result.reward == 0.0
      assert result.failure_reason in {
          FailureReason.AGENT_TIMEOUT,
          FailureReason.CONTEXT_TIMEOUT,
      }


  def test_verifier_reward_is_used_only_after_valid_execution() -> None:
      assert classify_attempt(AttemptEvidence(reward=1.0)).status is OutcomeKind.PASSED
      assert classify_attempt(AttemptEvidence(reward=0.0)).status is OutcomeKind.FAILED


  def test_invalid_precedence_prevents_imputation() -> None:
      result = classify_attempt(
          AttemptEvidence(proxy_http_status=500, qwen_exit_code=55, reward=0.0)
      )
      assert result.status is OutcomeKind.INVALID
      assert result.reward is None
  ```

- [ ] **Step 2: Run the taxonomy tests and observe the missing module.** Run:

  ```bash
  uv run pytest tests/evaluation/test_classification.py -q
  ```

  Expected failure: `ModuleNotFoundError: No module named 'research.der.evaluation.classification'`.

- [ ] **Step 3: Implement the explicit precedence table.** Create `research/der/evaluation/classification.py`:

  ```python
  """Approved validity taxonomy; invalid evidence always outranks reward or timeout."""

  from __future__ import annotations

  from dataclasses import dataclass

  from research.der.contracts.eval import FailureReason, OutcomeKind


  @dataclass(frozen=True, slots=True)
  class AttemptEvidence:
      reward: float | None = None
      proxy_http_status: int | None = None
      network_error: str | None = None
      infrastructure_error: str | None = None
      verifier_malformed: bool = False
      qwen_exit_code: int | None = None


  @dataclass(frozen=True, slots=True)
  class AttemptClassification:
      status: OutcomeKind
      reward: float | None
      failure_reason: FailureReason | None


  def classify_attempt(evidence: AttemptEvidence) -> AttemptClassification:
      if evidence.verifier_malformed:
          return AttemptClassification(
              status=OutcomeKind.INVALID,
              reward=None,
              failure_reason=FailureReason.MALFORMED_VERIFIER,
          )
      if evidence.infrastructure_error:
          return AttemptClassification(
              status=OutcomeKind.INVALID,
              reward=None,
              failure_reason=FailureReason.INFRA,
          )
      if evidence.network_error:
          return AttemptClassification(
              status=OutcomeKind.INVALID,
              reward=None,
              failure_reason=FailureReason.NETWORK,
          )
      if evidence.proxy_http_status is not None and evidence.proxy_http_status >= 400:
          return AttemptClassification(
              status=OutcomeKind.INVALID,
              reward=None,
              failure_reason=FailureReason.PROVIDER,
          )
      if evidence.qwen_exit_code in {53, 55, 124}:
          reason = (
              FailureReason.CONTEXT_TIMEOUT
              if evidence.qwen_exit_code == 124
              else FailureReason.AGENT_TIMEOUT
          )
          return AttemptClassification(
              status=OutcomeKind.FAILED,
              reward=0.0,
              failure_reason=reason,
          )
      if evidence.reward == 1.0:
          return AttemptClassification(
              status=OutcomeKind.PASSED,
              reward=1.0,
              failure_reason=None,
          )
      if evidence.reward == 0.0:
          return AttemptClassification(
              status=OutcomeKind.FAILED,
              reward=0.0,
              failure_reason=FailureReason.TASK_ASSERTION,
          )
      return AttemptClassification(
          status=OutcomeKind.INVALID,
          reward=None,
          failure_reason=FailureReason.INFRA,
      )
  ```

  These are exactly Task 2's enum members (`OutcomeKind`, `FailureReason`); do not add synonym enums. An attempt with no usable evidence at all (no reward, no fault signal) is an incomplete result and classifies as `INVALID`/`INFRA` — never as reward zero.

- [ ] **Step 4: Run the taxonomy tests to green.** Run:

  ```bash
  uv run pytest tests/evaluation/test_classification.py -q
  uv run ruff check research/der/evaluation/classification.py tests/evaluation/test_classification.py
  ```

  Expected output: all taxonomy cases pass.

- [ ] **Step 5: Write the V5 evidence-table test.** Create `tests/discovery/test_v5_faults.py`:

  ```python
  from __future__ import annotations

  import pytest

  from scripts.discover_v5_faults import verify_fault_rows


  def test_all_required_faults_have_expected_classification() -> None:
      rows = [
          {"fault": "provider_4xx", "observed": "invalid"},
          {"fault": "provider_5xx", "observed": "invalid"},
          {"fault": "network_kill", "observed": "invalid"},
          {"fault": "malformed_verifier", "observed": "invalid"},
          {"fault": "agent_timeout", "observed": "failed"},
      ]
      verify_fault_rows(rows)


  def test_wrong_classification_stops() -> None:
      with pytest.raises(ValueError, match="provider_500"):
          verify_fault_rows([{"fault": "provider_500", "observed": "failed"}])
  ```

- [ ] **Step 6: Implement the V5 recorder.** Create `scripts/discover_v5_faults.py`:

  ```python
  #!/usr/bin/env python3
  """Validate real induced-fault rows and record V5."""

  from __future__ import annotations

  import argparse
  import json
  import sys
  from pathlib import Path
  from typing import Any

  from research.der.pins import write_discovery_pin

  EXPECTED = {
      "provider_4xx": "invalid",
      "provider_5xx": "invalid",
      "network_kill": "invalid",
      "malformed_verifier": "invalid",
      "agent_timeout": "failed",
  }


  def verify_fault_rows(rows: list[dict[str, Any]]) -> None:
      observed = {str(row["fault"]): str(row["observed"]) for row in rows}
      for fault, expected in EXPECTED.items():
          if fault not in observed:
              raise ValueError(f"missing real induced fault: {fault}")
          if observed[fault] != expected:
              raise ValueError(
                  f"{fault} classified {observed[fault]!r}; expected {expected!r}"
              )
      if set(observed) != set(EXPECTED):
          raise ValueError(f"unexpected fault rows: {sorted(set(observed) - set(EXPECTED))}")
      for row in rows:
          artifact = Path(str(row.get("artifact", "")))
          if not artifact.is_file() or artifact.stat().st_size == 0:
              raise ValueError(f"fault row has no preserved artifact: {row}")
          if row["observed"] == "invalid" and row.get("reward") is not None:
              raise ValueError(f"invalid row imputed reward: {row['fault']}")


  def main() -> int:
      parser = argparse.ArgumentParser()
      parser.add_argument("--rows", type=Path, required=True)
      parser.add_argument("--pin", type=Path, default=Path("research-plan/pins/v5-fault-classification.md"))
      args = parser.parse_args()
      try:
          rows = json.loads(args.rows.read_text(encoding="utf-8"))
          if not isinstance(rows, list):
              raise ValueError("fault evidence must be a JSON array")
          verify_fault_rows(rows)
      except Exception as exc:
          write_discovery_pin(
              args.pin,
              verification_id="V5",
              status="blocked",
              command=" ".join(sys.argv),
              observation={"error": str(exc)},
              stop_reason="A real induced fault contradicted the approved validity taxonomy.",
          )
          print(f"STOP V5: {exc}", file=sys.stderr)
          return 78
      write_discovery_pin(
          args.pin,
          verification_id="V5",
          status="passed",
          command=" ".join(sys.argv),
          observation={"rows": rows},
      )
      print(json.dumps(rows, indent=2, sort_keys=True))
      return 0


  if __name__ == "__main__":
      raise SystemExit(main())
  ```

- [ ] **Step 7: Run recorder tests to green.** Run:

  ```bash
  uv run pytest tests/discovery/test_v5_faults.py -q
  ```

  Expected output: `2 passed`.

- [ ] **Step 8: Create five disposable fault cases from the exact V2 command.** Copy the V2 job command into five shell transcripts under `var/faults/v5/commands/`; change only the indicated fault injection and job ID:

  ```bash
  install -d var/faults/v5/{commands,artifacts}
  cp var/runs/v2/pier.stdout var/faults/v5/v2-reference.stdout
  ```

  Run these cases one at a time with `--n-attempts 1 --n-concurrent 1 --max-retries 0`:

  1. `provider_4xx`: start a disposable host endpoint on port 8791 returning HTTP 401 for `/v1/chat/completions`; issue a new run token; set only `OPENAI_BASE_URL=http://$PROXY_HOST:8791/v1`.
  2. `provider_5xx`: same, returning HTTP 503 on port 8792.
  3. `network_kill`: start the real proxy on port 8793, launch Pier, wait until its observation has `status=request_started`, then `kill -9` that proxy PID.
  4. `malformed_verifier`: copy the single V7 task into `var/faults/v5/tasks/`; record `sha256sum` of the pristine verifier; modify only the disposable verifier's final write so `reward.json` contains `{not-json`; never modify the pinned DeepSWE checkout.
  5. `agent_timeout`: use the real proxy and set only `--agent-kwarg max_wall_time=1s`.

  Use this exact fault server for the two provider cases:

  ```bash
  uv run python - <<'PY' >var/faults/v5/fault-server.py
  print(r'''from http.server import BaseHTTPRequestHandler, HTTPServer
  import os
  class Handler(BaseHTTPRequestHandler):
      def do_GET(self):
          self.send_response(200); self.end_headers(); self.wfile.write(b'{"status":"ok"}')
      def do_POST(self):
          self.send_response(int(os.environ["FAULT_STATUS"])); self.end_headers()
          self.wfile.write(b'{"error":{"message":"induced V5 fault"}}')
      def log_message(self, format, *args):
          pass
  HTTPServer(("0.0.0.0", int(os.environ["FAULT_PORT"])), Handler).serve_forever()
  ''')
  PY
  ```

  Preserve each Pier stdout, explicit result path, proxy/fault-server log, Qwen stderr, and trial result under `var/faults/v5/artifacts/<fault>/`. A command that does not create an explicit Pier result path is still preserved as infrastructure evidence; never substitute a nearby directory.

- [ ] **Step 9: Classify the five real cases using the code from Step 3 and write the evidence table.** Run a one-off extractor that reads the explicit result for each case, V1 pointers, proxy HTTP records, and Qwen exit code, then calls `classify_attempt`; its output must have this exact shape:

  ```json
  [
    {"fault":"provider_4xx","observed":"invalid","invalid_reason":"provider","reward":null,"artifact":"var/faults/v5/artifacts/provider_4xx/result.json"},
    {"fault":"provider_5xx","observed":"invalid","invalid_reason":"provider","reward":null,"artifact":"var/faults/v5/artifacts/provider_5xx/result.json"},
    {"fault":"network_kill","observed":"invalid","invalid_reason":"network","reward":null,"artifact":"var/faults/v5/artifacts/network_kill/result.json"},
    {"fault":"malformed_verifier","observed":"invalid","invalid_reason":"malformed_verifier","reward":null,"artifact":"var/faults/v5/artifacts/malformed_verifier/reward.json"},
    {"fault":"agent_timeout","observed":"failed","invalid_reason":null,"reward":0.0,"artifact":"var/faults/v5/artifacts/agent_timeout/qwen-stderr.log"}
  ]
  ```

  The extractor must serialize enum `.value` strings and use the actual preserved paths. Run:

  ```bash
  uv run python scripts/discover_v5_faults.py --rows var/faults/v5/rows.json
  test "$?" -eq 0
  uv run der pins assert V5
  ```

  Expected output: passed V5. Any invalid row with reward `0.0` or timeout row marked invalid is a STOP.

- [ ] **Step 10: Commit code and the pin, not live fault artifacts.** Run:

  ```bash
  git add \
    research/der/evaluation/classification.py \
    scripts/discover_v5_faults.py \
    tests/evaluation/test_classification.py \
    tests/discovery/test_v5_faults.py \
    research-plan/pins/v5-fault-classification.md
  git commit -m "feat: enforce and prove the evaluation validity taxonomy"
  ```

### Task 13: Close Milestone 1 with pass, fail, and invalid live acceptance

**Files:**
- Create: `tests/integration/test_milestone1_acceptance.py`
- Create: `research-plan/pins/milestone1-acceptance.md`
- Modify: `experiments/EXP-0001-acceptance-chain.md`

**Interfaces:**
- Consumes: passed V1–V5 and V7 pins; explicit V2 result; V5 fault rows
- Produces: one machine-checkable Milestone 1 gate consumed by every later phase

- [ ] **Step 1: Write the gate test.** Create `tests/integration/test_milestone1_acceptance.py`:

  ```python
  from __future__ import annotations

  from research.der.pins import require_passed_pin


  def test_milestone1_discoveries_are_all_passed() -> None:
      for verification_id in ("V1", "V2", "V3", "V5", "V7"):
          require_passed_pin(verification_id)


  def test_live_chain_is_keyless_and_model_pinned() -> None:
      v2 = require_passed_pin("V2")
      assert v2["observed_models"] == ["deepseek-v4-pro"]
      assert v2["allowlist_domains"] == [v2["proxy_host"]]
      assert set(v2["evidence"]) == {
          "reward", "ctrf", "trajectory", "patch", "agent_log", "trial_result"
      }


  def test_live_fault_matrix_has_no_imputed_invalids() -> None:
      rows = require_passed_pin("V5")["rows"]
      assert any(row["observed"] == "failed" for row in rows)
      assert any(row["observed"] == "invalid" for row in rows)
      assert all(row["reward"] is None for row in rows if row["observed"] == "invalid")
  ```

- [ ] **Step 2: Run the gate and see any unresolved discovery fail.** Run:

  ```bash
  uv run pytest tests/integration/test_milestone1_acceptance.py -q
  ```

  Expected output is `3 passed`. A `DiscoveryBlockedError` is a phase STOP, not a test to skip.

- [ ] **Step 3: Record exact pass/fail/invalid evidence in the milestone pin.** Create `research-plan/pins/milestone1-acceptance.md` through `write_discovery_pin`, with `verification_id: M1`, `status: passed`, the exact command from Step 2, and observation fields:

  ```yaml
  passed_run: <V2 explicit result path>
  failed_run: <V5 agent_timeout artifact>
  invalid_run: <V5 provider_5xx artifact>
  model: deepseek-v4-pro
  pier: datacurve-pier==0.3.0
  atif: ATIF-v1.7
  provider_key_in_trial: false
  ```

  Generate it without typing paths:

  ```bash
  uv run python - <<'PY'
  from pathlib import Path
  from research.der.pins import require_passed_pin, write_discovery_pin
  v2 = require_passed_pin("V2")
  v5 = require_passed_pin("V5")
  by_fault = {row["fault"]: row for row in v5["rows"]}
  write_discovery_pin(
      Path("research-plan/pins/milestone1-acceptance.md"),
      verification_id="M1",
      status="passed",
      command="uv run pytest tests/integration/test_milestone1_acceptance.py -q",
      observation={
          "passed_run": v2["job_result_path"],
          "failed_run": by_fault["agent_timeout"]["artifact"],
          "invalid_run": by_fault["provider_5xx"]["artifact"],
          "model": "deepseek-v4-pro",
          "pier": "datacurve-pier==0.3.0",
          "atif": "ATIF-v1.7",
          "provider_key_in_trial": False,
      },
  )
  PY
  ```

  Expected output is silent and the pin parses as passed.

- [ ] **Step 4: Update the lifecycle record from proposed to running, preserving preregistration history.** Use the Task 4 transition function rather than editing YAML by hand:

  ```bash
  uv run python - <<'PY'
  from pathlib import Path
  from research.der.contracts.experiment import ExperimentStatus
  from research.der.experiments.records import transition_record
  from research.der.util.time import utc_now
  transition_record(
      Path("experiments/EXP-0001-acceptance-chain.md"),
      target=ExperimentStatus.RUNNING,
      now=utc_now(),
      append_run_id="RUN-EXP-0001-acceptance-chain-smoke-01",
  )
  PY
  git diff -- experiments/EXP-0001-acceptance-chain.md
  ```

  Expected diff changes only `status`, `updated_at`, and `run_ids`. Result attachment remains a later responsibility (Task 15 attaches the scorecard; the finalizer owns this from Task 28 on).

- [ ] **Step 5: Run the whole phase's offline tests.** Run:

  ```bash
  uv run pytest \
    tests/agents \
    tests/proxy \
    tests/harness \
    tests/discovery/test_v1_pier_artifacts.py \
    tests/discovery/test_v2_acceptance_chain.py \
    tests/discovery/test_v3_qwen_archive.py \
    tests/discovery/test_v5_faults.py \
    tests/integration/test_milestone1_acceptance.py -q
  uv run ruff check research scripts tests
  uv run mypy research/der
  ```

  Expected output: all tests pass and static checks are clean.

- [ ] **Step 6: Commit.** Run:

  ```bash
  git add \
    tests/integration/test_milestone1_acceptance.py \
    research-plan/pins/milestone1-acceptance.md \
    experiments/EXP-0001-acceptance-chain.md
  git commit -m "test: close the manual Pier milestone"
  ```

# Phase 2 — Milestone 2: normalizer, immutable scorecard, and hand trace

Milestone exit: the real V2 Pier job normalizes strictly into `EvalResult`; every field is sourced from a pinned Pier/DeepSWE/proxy artifact; one immutable `scorecard.json` is written once; sanitized real artifacts and a golden scorecard are committed; and the owner can trace session → ATIF → Git commit → patch → verifier → scorecard without a recency lookup.

### Task 14: Strict Pier/DeepSWE normalizer with real golden fixtures

**Files:**
- Create: `research/der/evaluation/normalizer.py`
- Create: `research/der/evaluation/artifact_manifest.py`
- Create: `tests/evaluation/test_normalizer.py`
- Create: `tests/evaluation/test_artifact_manifest.py`
- Create: `tests/fixtures/contracts/eval-spec.json`
- Create: `tests/fixtures/pier/v0.3.0/pass/`
- Create: `tests/fixtures/pier/v0.3.0/fail/`
- Create: `tests/fixtures/pier/v0.3.0/invalid/`
- Create: `tests/fixtures/pier/v0.3.0/malformed/`
- Create: `tests/golden/scorecards/v2-normalized-result.json`

**Interfaces:**
- Consumes: `EvalSpec`; passed V1 field/path pin; exact Pier result path; V2 proxy observations; `classify_attempt(AttemptEvidence) -> AttemptClassification`
- Produces: `normalize_pier_result(spec: EvalSpec, exact_result_path: Path, v1: Mapping[str, Any], observations_path: Path) -> EvalResult`; `build_artifact_manifest(paths: Mapping[str, Path]) -> dict[str, Sha256]`

- [ ] **Step 1: Extend V1 once, before writing the normalizer, to include every identity field it needs.** Modify `scripts/discover_v1_pier_artifacts.py` so the passed observation also records these exact value keys, which the normalizer below reads verbatim: `trial_result_file`, `trial_name_pointer`, `task_name_pointer` (already present), `attempt_pointer` (already present), `started_at_pointer`, `finished_at_pointer`, `agent_exit_code_pointer`, and `trial_status_pointer`. Find candidates by exact leaf names present in the live JSON; if a semantic field has zero or multiple candidates, write V1 as blocked and exit 78. Do not derive these fields from modification times or directory recency.

  Add this helper and use it for each semantic field:

  ```python
  def unique_leaf_pointer(
      payload: Any,
      *,
      leaves: set[str],
      value_type: type | tuple[type, ...],
      label: str,
  ) -> str:
      candidates = [
          pointer
          for pointer, value in walk(payload)
          if pointer.rsplit("/", 1)[-1] in leaves
          and isinstance(value, value_type)
          and not isinstance(value, bool)
      ]
      if len(candidates) != 1:
          raise ValueError(f"{label} pointer is not unique: {candidates}")
      return candidates[0]
  ```

  The exact candidate leaf sets come from the checked-out Pier 0.3.0 model source, not intuition. Record the `git grep` command and output in the V1 pin's command transcript. Rerun:

  ```bash
  uv run python scripts/discover_v1_pier_artifacts.py
  test "$?" -eq 0
  git diff -- research-plan/pins/v1-pier-artifact-layout.md
  ```

  Expected diff adds concrete file names and pointers only. A blocked pin stops this task.

- [ ] **Step 2: Write artifact-manifest tests.** Create `tests/evaluation/test_artifact_manifest.py`:

  ```python
  from __future__ import annotations

  from pathlib import Path

  import pytest

  from research.der.evaluation.artifact_manifest import build_artifact_manifest


  def test_manifest_is_sorted_and_content_addressed(tmp_path: Path) -> None:
      (tmp_path / "b").write_bytes(b"b")
      (tmp_path / "a").write_bytes(b"a")
      manifest = build_artifact_manifest({"b": tmp_path / "b", "a": tmp_path / "a"})
      assert list(manifest) == ["a", "b"]
      assert manifest["a"] == "ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb"


  def test_missing_or_empty_artifact_is_rejected(tmp_path: Path) -> None:
      empty = tmp_path / "empty"
      empty.touch()
      with pytest.raises(ValueError, match="empty"):
          build_artifact_manifest({"empty": empty})
  ```

- [ ] **Step 3: Write normalizer tests against compact source-shaped fixtures.** Create `tests/evaluation/test_normalizer.py`:

  ```python
  from __future__ import annotations

  import json
  from pathlib import Path

  import pytest

  from research.der.contracts.eval import EvalSpec, FailureReason, OutcomeKind
  from research.der.evaluation.normalizer import normalize_pier_result
  from research.der.pins import require_passed_pin


  def _spec() -> EvalSpec:
      return EvalSpec.model_validate_json(
          Path("tests/fixtures/contracts/eval-spec.json").read_text(encoding="utf-8")
      )


  def test_pass_fixture_matches_golden() -> None:
      root = Path("tests/fixtures/pier/v0.3.0/pass")
      result = normalize_pier_result(
          spec=_spec(),
          exact_result_path=root / "result.json",
          v1=require_passed_pin("V1"),
          observations_path=root / "observations.jsonl",
      )
      expected = json.loads(
          Path("tests/golden/scorecards/v2-normalized-result.json").read_text()
      )
      assert result.model_dump(mode="json") == expected
      assert result.tasks[0].attempts[0].outcome is OutcomeKind.PASSED


  def test_reward_zero_is_failed_not_invalid() -> None:
      root = Path("tests/fixtures/pier/v0.3.0/fail")
      result = normalize_pier_result(
          spec=_spec(),
          exact_result_path=root / "result.json",
          v1=require_passed_pin("V1"),
          observations_path=root / "observations.jsonl",
      )
      attempt = result.tasks[0].attempts[0]
      assert attempt.outcome is OutcomeKind.FAILED
      assert attempt.failure_reason is FailureReason.TASK_ASSERTION


  def test_provider_fault_is_invalid_without_reward() -> None:
      root = Path("tests/fixtures/pier/v0.3.0/invalid")
      result = normalize_pier_result(
          spec=_spec(),
          exact_result_path=root / "result.json",
          v1=require_passed_pin("V1"),
          observations_path=root / "observations.jsonl",
      )
      attempt = result.tasks[0].attempts[0]
      assert attempt.outcome is OutcomeKind.INVALID
      assert attempt.failure_reason is FailureReason.PROVIDER
      assert attempt.reward is None


  def test_malformed_reward_never_becomes_zero() -> None:
      root = Path("tests/fixtures/pier/v0.3.0/malformed")
      with pytest.raises(ValueError, match="reward.json"):
          normalize_pier_result(
              spec=_spec(),
              exact_result_path=root / "result.json",
              v1=require_passed_pin("V1"),
              observations_path=root / "observations.jsonl",
          )


  def test_missing_explicit_result_path_never_recovers_by_recency(tmp_path: Path) -> None:
      newer = tmp_path / "newer" / "result.json"
      newer.parent.mkdir()
      newer.write_text("{}")
      with pytest.raises(FileNotFoundError, match="explicit Pier result"):
          normalize_pier_result(
              spec=_spec(),
              exact_result_path=tmp_path / "requested" / "result.json",
              v1=require_passed_pin("V1"),
              observations_path=tmp_path / "observations.jsonl",
          )
  ```

- [ ] **Step 4: Run the tests and observe missing modules/fixtures.** Run:

  ```bash
  uv run pytest tests/evaluation/test_artifact_manifest.py tests/evaluation/test_normalizer.py -q
  ```

  Expected failure starts with missing `research.der.evaluation.normalizer` or missing pass fixture; do not create a broad integration helper to bypass the unit boundary.

- [ ] **Step 5: Implement the artifact manifest.** Create `research/der/evaluation/artifact_manifest.py`:

  ```python
  """Content-address canonical evaluator evidence."""

  from __future__ import annotations

  from collections.abc import Mapping
  from pathlib import Path

  from research.der.contracts.eval import Sha256
  from research.der.util.hashing import sha256_file


  def build_artifact_manifest(paths: Mapping[str, Path]) -> dict[str, Sha256]:
      result: dict[str, Sha256] = {}
      for label, path in sorted(paths.items()):
          if not path.is_file():
              raise FileNotFoundError(f"artifact {label!r} is absent: {path}")
          if path.stat().st_size == 0:
              raise ValueError(f"artifact {label!r} is empty: {path}")
          result[label] = sha256_file(path)
      return result
  ```

- [ ] **Step 6: Implement the strict normalizer.** Create `research/der/evaluation/normalizer.py`:

  ```python
  """Pier 0.3.0 + DeepSWE normalizer driven only by the passed V1 pin."""

  from __future__ import annotations

  import json
  import tomllib
  from collections import defaultdict
  from collections.abc import Mapping
  from datetime import datetime
  from decimal import Decimal
  from pathlib import Path
  from typing import Any

  from research.der.contracts.eval import (
      AttemptOutcome,
      EvalResult,
      EvalSpec,
      FailureReason,
      OutcomeKind,
      ResourceTotals,
      TaskResult,
      TokenUsage,
  )
  from research.der.evaluation.artifact_manifest import build_artifact_manifest
  from research.der.evaluation.classification import AttemptEvidence, classify_attempt


  def _read_json(path: Path) -> Any:
      try:
          return json.loads(path.read_text(encoding="utf-8"))
      except (OSError, json.JSONDecodeError) as exc:
          raise ValueError(f"cannot parse required artifact {path}: {exc}") from exc


  def _pointer(value: Any, pointer: str) -> Any:
      current = value
      for raw in pointer.removeprefix("/").split("/") if pointer != "/" else []:
          token = raw.replace("~1", "/").replace("~0", "~")
          current = current[int(token)] if isinstance(current, list) else current[token]
      return current


  def _observation_rows(path: Path, *, run_id: str) -> list[dict[str, Any]]:
      rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
      selected = [row for row in rows if row.get("run_id") == run_id]
      if not selected:
          raise ValueError(f"no exact proxy observations for run {run_id}")
      return selected


  def _load_pricing() -> tuple[int, Decimal, Decimal, Decimal]:
      """(unit_tokens, cache_hit_input, cache_miss_input, output) from the one policy file."""
      raw = tomllib.loads(
          Path("research/config/runtime-policy.toml").read_text(encoding="utf-8")
      )["pricing"]
      return (
          int(raw["unit_tokens"]),
          Decimal(str(raw["cache_hit_input_per_unit"])),
          Decimal(str(raw["cache_miss_input_per_unit"])),
          Decimal(str(raw["output_per_unit"])),
      )


  def _usage_cost(usage: TokenUsage) -> Decimal:
      unit, cache_hit, cache_miss, output = _load_pricing()
      uncached = max(usage.input_tokens - usage.cache_tokens, 0)
      return (
          Decimal(usage.cache_tokens) * cache_hit
          + Decimal(uncached) * cache_miss
          + Decimal(usage.output_tokens) * output
      ) / Decimal(unit)


  def _usage(trajectory: dict[str, Any], pin: Mapping[str, Any]) -> TokenUsage:
      paths = pin["usage_pointers"]
      return TokenUsage(
          input_tokens=int(_pointer(trajectory, paths["total_prompt"])),
          cache_tokens=int(_pointer(trajectory, paths["total_cached"])),
          output_tokens=int(_pointer(trajectory, paths["total_completion"])),
          peak_context_tokens=max(
              [
                  int(step.get("metrics", {}).get("prompt_tokens", 0))
                  for step in trajectory.get("steps", [])
                  if isinstance(step, dict)
              ]
              or [0]
          ),
          tool_calls=int(trajectory.get("final_metrics", {}).get("extra", {}).get("tool_calls", 0)),
          session_turns=int(trajectory.get("final_metrics", {}).get("extra", {}).get("session_turns", 0)),
      )


  def _classify(
      *,
      reward: Decimal | None,
      exit_code: int,
      rows: list[dict[str, Any]],
      attempts_total: int,
  ) -> tuple[OutcomeKind, FailureReason | None, Decimal | None]:
      provider_status = next(
          (int(row["status_code"]) for row in rows if int(row.get("status_code", 0)) >= 400),
          None,
      )
      if provider_status is not None and attempts_total > 1 and reward is not None:
          # The observation log is run-scoped; with several attempts in the run,
          # a fault row cannot be attributed to an attempt that produced a valid
          # binary reward. Never invalidate on unattributable evidence.
          provider_status = None
      cls = classify_attempt(
          AttemptEvidence(
              reward=float(reward) if reward is not None else None,
              proxy_http_status=provider_status,
              qwen_exit_code=exit_code,
          )
      )
      normalized = Decimal(str(cls.reward)) if cls.reward is not None else None
      return cls.status, cls.failure_reason, normalized


  def normalize_pier_result(
      *,
      spec: EvalSpec,
      exact_result_path: Path,
      v1: Mapping[str, Any],
      observations_path: Path,
  ) -> EvalResult:
      if not exact_result_path.is_file():
          raise FileNotFoundError(f"explicit Pier result path is absent: {exact_result_path}")
      job_payload = _read_json(exact_result_path)
      job_dir = exact_result_path.parent
      reward_paths = sorted(job_dir.rglob(str(v1["reward_file"])))
      if len(reward_paths) != len(spec.task_ids) * spec.k:
          raise ValueError(
              f"expected {len(spec.task_ids) * spec.k} reward files; observed {len(reward_paths)}"
          )
      rows = _observation_rows(observations_path, run_id=spec.run_id)
      completed_rows = [row for row in rows if int(row.get("status_code", 0)) == 200]
      if not completed_rows:
          raise ValueError(
              f"proxy log has no completed (status 200) observation for run {spec.run_id}; "
              "the run is invalid — do not normalize partial evidence"
          )
      observed_models = {str(row["observed_model"]) for row in completed_rows}
      if observed_models != {"deepseek-v4-pro"}:
          raise ValueError(f"proxy model assertion failed: {sorted(observed_models)}")
      attempts_total = len(spec.task_ids) * spec.k
      grouped: dict[str, list[AttemptOutcome]] = defaultdict(list)
      started: list[datetime] = []
      finished: list[datetime] = []
      job_artifacts: dict[str, Path] = {"pier_job_result": exact_result_path}
      for reward_path in reward_paths:
          trial_dir = reward_path.parent
          trial_result_path = trial_dir / str(v1["trial_result_file"])
          ctrf_path = trial_dir / str(v1["ctrf_file"])
          trajectory_path = trial_dir / str(v1["trajectory_file"])
          trial = _read_json(trial_result_path)
          reward_payload = _read_json(reward_path)
          _read_json(ctrf_path)
          trajectory = _read_json(trajectory_path)
          if _pointer(trajectory, str(v1["atif_schema_pointer"])) != "ATIF-v1.7":
              raise ValueError(f"wrong ATIF schema in {trajectory_path}")
          task_id = str(_pointer(trial, str(v1["task_name_pointer"])))
          attempt_index = int(_pointer(trial, str(v1["attempt_pointer"])))
          trial_name = str(_pointer(trial, str(v1["trial_name_pointer"])))
          if task_id not in spec.task_ids:
              raise ValueError(f"unexpected task in Pier result: {task_id}")
          reward_value = _pointer(reward_payload, str(v1["reward_pointer"]))
          reward = Decimal(str(reward_value)) if reward_value in {0, 1, 0.0, 1.0} else None
          exit_code = int(_pointer(trial, str(v1["agent_exit_code_pointer"])))
          outcome, reason, normalized_reward = _classify(
              reward=reward, exit_code=exit_code, rows=rows, attempts_total=attempts_total
          )
          usage = _usage(trajectory, v1)
          started_at = datetime.fromisoformat(
              str(_pointer(trial, str(v1["started_at_pointer"]))).replace("Z", "+00:00")
          )
          finished_at = datetime.fromisoformat(
              str(_pointer(trial, str(v1["finished_at_pointer"]))).replace("Z", "+00:00")
          )
          started.append(started_at)
          finished.append(finished_at)
          artifacts = {
              "reward": reward_path,
              "ctrf": ctrf_path,
              "trajectory": trajectory_path,
              "trial_result": trial_result_path,
          }
          patch_matches = [p for p in trial_dir.rglob("*.patch") if p.is_file()]
          if len(patch_matches) != 1:
              raise ValueError(f"expected one patch under explicit trial {trial_dir}")
          artifacts["patch"] = patch_matches[0]
          grouped[task_id].append(
              AttemptOutcome(
                  task_id=task_id,
                  attempt_index=attempt_index,
                  trial_name=trial_name,
                  trial_dir=trial_dir,
                  outcome=outcome,
                  failure_reason=reason,
                  reward=normalized_reward,
                  metrics={"pier_trial_status": str(_pointer(trial, str(v1["trial_status_pointer"])))},
                  usage=usage,
                  cost_usd=_usage_cost(usage),
                  artifact_digests=build_artifact_manifest(artifacts),
              )
          )
      tasks: list[TaskResult] = []
      for task_id in spec.task_ids:
          attempts = tuple(sorted(grouped[task_id], key=lambda item: item.attempt_index))
          if len(attempts) != spec.k:
              raise ValueError(f"task {task_id} does not have exactly k attempts")
          # The contract index is zero-based and contiguous; Pier's raw attempt
          # numbering (possibly 1-based) stays visible in trial_name/trial_dir.
          attempts = tuple(
              attempt.model_copy(update={"attempt_index": position})
              for position, attempt in enumerate(attempts)
          )
          passed = sum(item.outcome is OutcomeKind.PASSED for item in attempts)
          tasks.append(
              TaskResult(
                  task_id=task_id,
                  attempts=attempts,
                  pass_fraction=Decimal(passed) / Decimal(len(attempts)),
              )
          )
      all_attempts = [attempt for task in tasks for attempt in task.attempts]
      return EvalResult(
          experiment_id=spec.experiment_id,
          run_id=spec.run_id,
          evaluator="datacurve-pier",
          evaluator_version="0.3.0",
          evaluator_job_id=str(job_payload["job_id"]),
          exact_result_path=exact_result_path,
          identity=spec.identity,
          suite_version=spec.suite_version,
          suite_class=spec.suite_class,
          k=spec.k,
          model_policy_id=spec.model_policy_id,
          observed_models=tuple(sorted(observed_models)),
          tasks=tuple(tasks),
          resources=ResourceTotals(
              input_tokens=sum(a.usage.input_tokens for a in all_attempts),
              cache_tokens=sum(a.usage.cache_tokens for a in all_attempts),
              output_tokens=sum(a.usage.output_tokens for a in all_attempts),
              tool_calls=sum(a.usage.tool_calls for a in all_attempts),
              wall_seconds=Decimal(str((max(finished) - min(started)).total_seconds())),
              cost_usd=sum(
                  (Decimal(str(row.get("cost_usd", "0"))) for row in completed_rows),
                  Decimal("0"),
              ),
          ),
          artifact_digests=build_artifact_manifest(job_artifacts),
          started_at=min(started),
          finished_at=max(finished),
      )
  ```

  Replace the one direct `job_payload["job_id"]` only if V1 records a different exact job-ID pointer; then use that pin field. Do not search other job directories. Evidence honesty note: per-attempt `cost_usd` is derived from that attempt's ATIF usage at the pinned policy prices (the proxy's run-scoped log cannot attribute dollars to one attempt), while `resources.cost_usd` is the proxy-observed run total from completed observation rows — the two are cross-checkable but intentionally sourced differently, and the proxy-observed number is the one the watchdog trusts.

- [ ] **Step 7: Create the shared spec fixture, then populate sanitized pass/fail/invalid/malformed fixtures from the real V2/V5 artifacts.** First write `tests/fixtures/contracts/eval-spec.json` — the strict spec every normalizer/pier-command test loads. Generate it through the contract so it can never drift from the schema, using the live task ID recorded by V7:

  ```bash
  uv run python - <<'PY'
  from decimal import Decimal
  from pathlib import Path

  from research.der.contracts.base import canonical_json_bytes
  from research.der.contracts.eval import (
      DiscoveryPinPaths, EvalSpec, HarnessIdentity, RunBudget,
  )
  from research.der.pins import require_passed_pin

  v7 = require_passed_pin("V7")
  task_id = v7["task_ids"][0]
  spec = EvalSpec(
      experiment_id="EXP-0001-acceptance-chain",
      run_id="RUN-EXP-0001-acceptance-chain-smoke-01",
      identity=HarnessIdentity(
          source_commit="a" * 40,
          harness_tree_oid="b" * 40,
          runtime_manifest_digest="c" * 64,
      ),
      baseline_tree_oid="b" * 40,
      suite_version="discovery-v1",
      suite_class="smoke",
      task_root=Path("/var/cache/der/sources/deep-swe"),
      task_revisions={task_id: v7["task_checksums"][task_id]},
      task_ids=(task_id,),
      k=1,
      n_concurrent=1,
      jobs_dir=Path("var/pier/jobs"),
      staged_harness_dir=Path("var/staging/RUN-EXP-0001-acceptance-chain-smoke-01/harness"),
      pins=DiscoveryPinPaths(
          pier_artifacts=Path("research-plan/pins/v1-pier-artifact-layout.md"),
          proxy_route=Path("research-plan/pins/v2-acceptance-chain.md"),
          qwen_archive=Path("research-plan/pins/v3-qwen-archive-install.md"),
      ),
      model_policy_id="deepseek-v4-pro-v1",
      budget=RunBudget(
          max_cost_usd=Decimal("20"),
          max_wall_seconds=7200,
          max_attempts=1,
          max_input_tokens=2_000_000,
          max_output_tokens=250_000,
          max_tool_calls=500,
          max_session_turns=10,
      ),
  )
  out = Path("tests/fixtures/contracts/eval-spec.json")
  out.parent.mkdir(parents=True, exist_ok=True)
  out.write_bytes(canonical_json_bytes(spec))
  print(out, task_id)
  PY
  ```

  The fixture identity digests are fixture values; the normalizer copies `spec.identity` verbatim and never verifies it against Git (identity verification is the finalizer's job). Then copy the smallest complete trial closure for each case, preserving relative file names from V1. Sanitize only secrets and free text; do not alter status, reward, identity, timestamps, usage, task/attempt indexes, or schema fields. Each fixture directory's `observations.jsonl` holds that case's proxy rows in the Task 8 `ModelObservation` shape with `run_id` rewritten to the spec fixture's `RUN-EXP-0001-acceptance-chain-smoke-01` (identity alignment, recorded in the fixture README line, is the one permitted rewrite). The `invalid` fixture must contain at least one `status_code: 200` row with `observed_model: deepseek-v4-pro` plus one `status_code: 503` row, and its `reward.json` value at the V1 reward pointer must be non-binary (`null`) so classification exercises the provider branch rather than a task assertion. Generate `tests/golden/scorecards/v2-normalized-result.json` by running the normalizer once against the sanitized pass fixture and reviewing every field against its source artifact:

  ```bash
  uv run python - <<'PY'
  import json
  from pathlib import Path
  from research.der.contracts.eval import EvalSpec
  from research.der.evaluation.normalizer import normalize_pier_result
  from research.der.pins import require_passed_pin
  spec = EvalSpec.model_validate_json(Path("tests/fixtures/contracts/eval-spec.json").read_text())
  root = Path("tests/fixtures/pier/v0.3.0/pass")
  result = normalize_pier_result(
      spec=spec,
      exact_result_path=root / "result.json",
      v1=require_passed_pin("V1"),
      observations_path=root / "observations.jsonl",
  )
  Path("tests/golden/scorecards/v2-normalized-result.json").write_text(
      json.dumps(result.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"
  )
  PY
  ```

  This is the only golden-generation command. Review and commit the resulting JSON; later tests compare, never regenerate.

- [ ] **Step 8: Run normalizer tests to green.** Run:

  ```bash
  uv run pytest tests/evaluation/test_artifact_manifest.py tests/evaluation/test_normalizer.py -q
  uv run ruff check research/der/evaluation tests/evaluation
  uv run mypy research/der/evaluation
  ```

  Expected output: all tests pass and static checks are clean.

- [ ] **Step 9: Normalize the actual V2 job and compare its field paths to the golden contract.** First materialize the spec that describes the live V2 run — its identity is the real fixture-harness tree plus a runtime manifest assembled entirely from pins and locked revisions:

  ```bash
  uv run python - <<'PY'
  from decimal import Decimal
  from pathlib import Path

  from research.der.contracts.base import canonical_json_bytes
  from research.der.contracts.eval import (
      DiscoveryPinPaths, EvalSpec, RunBudget, RuntimeManifest,
  )
  from research.der.harness.identity import compute_identity
  from research.der.pins import require_passed_pin
  from research.der.util.git import head_commit
  from research.der.util.hashing import sha256_file

  v3 = require_passed_pin("V3")
  v7 = require_passed_pin("V7")
  task_id = v7["task_ids"][0]
  manifest = RuntimeManifest(
      pier_commit="e69a20e4e0ac073ec71fde0274bab3d9f40bac87",
      deep_swe_commit=v7["deep_swe_commit"],
      task_revisions={task_id: v7["task_checksums"][task_id]},
      qwen_archive_sha256=v3["archive_sha256"],
      der_agent_revision=head_commit(Path.cwd()),
      proxy_policy_id="deepseek-v4-pro-v1",
      qwen_system_policy_sha256=sha256_file(Path("research/config/runtime-policy.toml")),
  )
  identity = compute_identity(
      Path.cwd(), Path("tests/fixtures/harness/managed"), manifest
  )
  spec = EvalSpec(
      experiment_id="EXP-0001-acceptance-chain",
      run_id="RUN-EXP-0001-acceptance-chain-smoke-01",
      identity=identity,
      baseline_tree_oid=identity.harness_tree_oid,
      suite_version="discovery-v1",
      suite_class="smoke",
      task_root=Path(v7["task_root"]),
      task_revisions={task_id: v7["task_checksums"][task_id]},
      task_ids=(task_id,),
      k=1,
      n_concurrent=1,
      jobs_dir=Path("var/runs/v2"),
      staged_harness_dir=Path("var/staging/RUN-EXP-0001-acceptance-chain-smoke-01/harness"),
      pins=DiscoveryPinPaths(
          pier_artifacts=Path("research-plan/pins/v1-pier-artifact-layout.md"),
          proxy_route=Path("research-plan/pins/v2-acceptance-chain.md"),
          qwen_archive=Path("research-plan/pins/v3-qwen-archive-install.md"),
      ),
      model_policy_id="deepseek-v4-pro-v1",
      budget=RunBudget(
          max_cost_usd=Decimal("20"),
          max_wall_seconds=7200,
          max_attempts=1,
          max_input_tokens=2_000_000,
          max_output_tokens=250_000,
          max_tool_calls=500,
          max_session_turns=10,
      ),
  )
  Path("var/runs/v2/eval-spec.json").write_bytes(canonical_json_bytes(spec))
  print("spec", identity.harness_tree_oid)
  PY
  ```

  Then normalize the live job against it:

  ```bash
  uv run python - <<'PY'
  import json
  from pathlib import Path
  from research.der.contracts.eval import EvalSpec
  from research.der.evaluation.normalizer import normalize_pier_result
  from research.der.pins import require_passed_pin
  spec = EvalSpec.model_validate_json(Path("var/runs/v2/eval-spec.json").read_text())
  v2 = require_passed_pin("V2")
  result = normalize_pier_result(
      spec=spec,
      exact_result_path=Path(v2["job_result_path"]),
      v1=require_passed_pin("V1"),
      observations_path=Path("var/state/proxy/observations.jsonl"),
  )
  Path("var/runs/v2/eval-result.json").write_text(
      json.dumps(result.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"
  )
  print(result.run_id, result.observed_models, len(result.tasks))
  PY
  ```

  Expected output names the V2 run, `('deepseek-v4-pro',)`, and one task. Any missing field fails rather than defaulting.

- [ ] **Step 10: Commit.** Run:

  ```bash
  git add \
    scripts/discover_v1_pier_artifacts.py \
    research-plan/pins/v1-pier-artifact-layout.md \
    research/der/evaluation/normalizer.py \
    research/der/evaluation/artifact_manifest.py \
    tests/evaluation \
    tests/fixtures/contracts/eval-spec.json \
    tests/fixtures/pier/v0.3.0 \
    tests/golden/scorecards/v2-normalized-result.json
  git commit -m "feat: normalize pinned Pier evidence strictly"
  ```

### Task 15: Immutable scorecard writer and one-run evidence trace

**Files:**
- Create: `research/der/evaluation/scorecard_writer.py`
- Create: `tests/evaluation/test_scorecard_writer.py`
- Create: `tests/fixtures/contracts/scorecard.json`
- Modify: `research/der/experiments/records.py`
- Create: `research/runs/EXP-0001-acceptance-chain/RUN-EXP-0001-acceptance-chain-smoke-01/scorecard.json`
- Create: `research/runs/EXP-0001-acceptance-chain/RUN-EXP-0001-acceptance-chain-smoke-01/evidence-trace.md`
- Modify: `experiments/EXP-0001-acceptance-chain.md`

**Interfaces:**
- Consumes: `Scorecard`; `canonical_json_bytes`; normalized V2 `EvalResult`; exact lifecycle record digest
- Produces: `write_scorecard_once(path: Path, scorecard: Scorecard) -> str`; `attach_scorecard(record_path: Path, scorecard_path: Path) -> None` in `research.der.experiments.records`; immutable scorecard SHA-256 consumed by baseline, finalizer, publication, and adoption tasks

- [ ] **Step 1: Create the scorecard contract fixture, then write immutable-write tests.** Generate `tests/fixtures/contracts/scorecard.json` through the models so it cannot drift from the schema (fixture-only identities; the eval-result payload reuses the committed eval-spec fixture's identifiers):

  ```bash
  uv run python - <<'PY'
  from datetime import UTC, datetime
  from decimal import Decimal
  from pathlib import Path

  from research.der.contracts.base import canonical_json_bytes
  from research.der.contracts.eval import (
      AttemptOutcome, EvalResult, HarnessIdentity, OutcomeKind, ResourceTotals,
      TaskResult, TokenUsage,
  )
  from research.der.contracts.scorecard import (
      ComparabilityStatus, PromotionDecision, PromotionVerdict, Scorecard,
  )

  now = datetime(2026, 7, 21, tzinfo=UTC)
  identity = HarnessIdentity(
      source_commit="a" * 40,
      harness_tree_oid="b" * 40,
      runtime_manifest_digest="c" * 64,
  )
  attempt = AttemptOutcome(
      task_id="fixture-task",
      attempt_index=0,
      trial_name="fixture-task__1",
      trial_dir=Path("trial"),
      outcome=OutcomeKind.PASSED,
      failure_reason=None,
      reward=Decimal("1"),
      metrics={"pier_trial_status": "completed"},
      usage=TokenUsage(input_tokens=10, cache_tokens=2, output_tokens=3),
      cost_usd=Decimal("0.01"),
      artifact_digests={"reward": "d" * 64},
  )
  result = EvalResult(
      experiment_id="EXP-0001-acceptance-chain",
      run_id="RUN-EXP-0001-acceptance-chain-smoke-01",
      evaluator="datacurve-pier",
      evaluator_version="0.3.0",
      evaluator_job_id="fixture-job",
      exact_result_path=Path("var/runs/v2/job/result.json"),
      identity=identity,
      suite_version="discovery-v1",
      suite_class="smoke",
      k=1,
      model_policy_id="deepseek-v4-pro-v1",
      observed_models=("deepseek-v4-pro",),
      tasks=(TaskResult(task_id="fixture-task", attempts=(attempt,), pass_fraction=Decimal("1")),),
      resources=ResourceTotals(input_tokens=10, cache_tokens=2, output_tokens=3, cost_usd=Decimal("0.01")),
      artifact_digests={"pier_job_result": "e" * 64},
      started_at=now,
      finished_at=now,
  )
  scorecard = Scorecard(
      created_at=now,
      experiment_record_sha256="f" * 64,
      baseline_identity=identity,
      candidate_identity=identity,
      result=result,
      decision=PromotionDecision(
          verdict=PromotionVerdict.INCONCLUSIVE,
          primary_metric="confirmation_macro_pass_at_1",
          baseline_value=None,
          candidate_value=None,
          observed_effect=None,
          minimum_effect=Decimal("0"),
          guardrail_results={"discovery_only": True},
          comparability=ComparabilityStatus.INCOMPARABLE,
          reasons=("Fixture scorecard for writer tests.",),
      ),
      secret_scrub_sha256="0" * 64,
  )
  out = Path("tests/fixtures/contracts/scorecard.json")
  out.parent.mkdir(parents=True, exist_ok=True)
  out.write_bytes(canonical_json_bytes(scorecard))
  print(out)
  PY
  ```

  Then create `tests/evaluation/test_scorecard_writer.py`:

  ```python
  from __future__ import annotations

  from pathlib import Path

  import pytest

  from research.der.contracts.scorecard import Scorecard
  from research.der.evaluation.scorecard_writer import write_scorecard_once


  def _scorecard() -> Scorecard:
      return Scorecard.model_validate_json(
          Path("tests/fixtures/contracts/scorecard.json").read_text(encoding="utf-8")
      )


  def test_write_once_returns_digest_and_fsyncs_parent(tmp_path: Path) -> None:
      path = tmp_path / "scorecard.json"
      digest = write_scorecard_once(path, _scorecard())
      assert len(digest) == 64
      assert path.is_file()
      assert path.read_bytes().endswith(b"\n")


  def test_existing_scorecard_is_never_rewritten_even_if_equal(tmp_path: Path) -> None:
      path = tmp_path / "scorecard.json"
      write_scorecard_once(path, _scorecard())
      with pytest.raises(FileExistsError, match="immutable scorecard"):
          write_scorecard_once(path, _scorecard())
  ```

- [ ] **Step 2: Run the test and observe the missing writer.** Run:

  ```bash
  uv run pytest tests/evaluation/test_scorecard_writer.py -q
  ```

  Expected failure: missing `scorecard_writer` module.

- [ ] **Step 3: Implement exclusive, durable scorecard creation.** Create `research/der/evaluation/scorecard_writer.py`:

  ```python
  """Create a scorecard exactly once; no replace operation exists."""

  from __future__ import annotations

  import os
  from pathlib import Path

  from research.der.contracts.base import canonical_json_bytes
  from research.der.contracts.scorecard import Scorecard
  from research.der.util.hashing import sha256_bytes


  def write_scorecard_once(path: Path, scorecard: Scorecard) -> str:
      path.parent.mkdir(parents=True, exist_ok=True)
      payload = canonical_json_bytes(scorecard)
      try:
          fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o444)
      except FileExistsError as exc:
          raise FileExistsError(f"immutable scorecard already exists: {path}") from exc
      try:
          with os.fdopen(fd, "wb", closefd=True) as handle:
              handle.write(payload)
              handle.flush()
              os.fsync(handle.fileno())
          directory_fd = os.open(path.parent, os.O_RDONLY)
          try:
              os.fsync(directory_fd)
          finally:
              os.close(directory_fd)
      except Exception:
          path.unlink(missing_ok=True)
          raise
      return sha256_bytes(payload)
  ```

- [ ] **Step 4: Run writer tests to green.** Run:

  ```bash
  uv run pytest tests/evaluation/test_scorecard_writer.py -q
  ```

  Expected output: `2 passed`.

- [ ] **Step 5: Hand-trace every V2 scorecard field before writing it.** Create `research/runs/EXP-0001-acceptance-chain/RUN-EXP-0001-acceptance-chain-smoke-01/evidence-trace.md` with this table populated from V1/V2 and the actual normalized result:

  ```markdown
  # Evidence trace — RUN-EXP-0001-acceptance-chain-smoke-01

  | Scorecard field | Canonical source | Exact pointer/path | Digest check |
  |---|---|---|---|
  | result.evaluator_job_id | Pier structured job result | V1 job-ID pointer in V2 explicit result | matched |
  | result.tasks[].attempts[].trial_name | Pier trial result | V1 trial-name pointer | matched |
  | result.tasks[].attempts[].reward | DeepSWE reward artifact | V1 reward file + reward pointer | matched |
  | result.tasks[].attempts[].metrics | DeepSWE CTRF + Pier result | V1 CTRF summary/status pointers | matched |
  | result.tasks[].attempts[].usage | Pier ATIF v1.7 | V1 usage pointers | matched |
  | result.tasks[].attempts[].artifact_digests.patch | `pre_artifacts.sh` patch | explicit trial patch path | matched |
  | result.observed_models | proxy observation log | completed (status 200) rows for the exact run_id | `deepseek-v4-pro` only |
  | result.resources.cost_usd | proxy observation log | sum of completed rows for the exact run_id | matched |
  | candidate_identity.harness_tree_oid | Git | `git_tree_oid` over the staged fixture harness | matched |
  | candidate_identity.runtime_manifest_digest | runtime manifest | canonical JSON SHA-256 | matched |
  ```

  Replace every prose pointer such as “V1 job-ID pointer” with the concrete pointer string read from `research-plan/pins/v1-pier-artifact-layout.md`. Add a final `Trace result: passed` line only after checking each digest with `sha256sum`.

- [ ] **Step 6: Construct and write the real scorecard once.** Use the normalized result, Task 3 identity, lifecycle-record digest, and an explicitly non-promotional discovery decision:

  ```bash
  uv run python - <<'PY'
  from datetime import UTC, datetime
  from decimal import Decimal
  from pathlib import Path
  from research.der.contracts.eval import EvalResult
  from research.der.contracts.scorecard import (
      ComparabilityStatus, PromotionDecision, PromotionVerdict, Scorecard,
  )
  from research.der.evaluation.scorecard_writer import write_scorecard_once
  from research.der.util.hashing import sha256_file

  run_dir = Path("research/runs/EXP-0001-acceptance-chain/RUN-EXP-0001-acceptance-chain-smoke-01")
  run_dir.mkdir(parents=True, exist_ok=True)
  result = EvalResult.model_validate_json(Path("var/runs/v2/eval-result.json").read_text())
  # The evaluated identity is the one the run actually carried (Task 14 Step 9
  # computed it from the staged fixture harness and the pinned runtime manifest).
  identity = result.identity
  record = Path("experiments/EXP-0001-acceptance-chain.md")
  scrub_report = run_dir / "secret-scrub.json"
  scrub_report.write_text('{"status":"passed","matches":[]}\n')
  scorecard = Scorecard(
      created_at=datetime.now(UTC),
      experiment_record_sha256=sha256_file(record),
      baseline_identity=identity,
      candidate_identity=identity,
      result=result,
      decision=PromotionDecision(
          verdict=PromotionVerdict.INCONCLUSIVE,
          primary_metric="confirmation_macro_pass_at_1",
          baseline_value=None,
          candidate_value=None,
          observed_effect=None,
          minimum_effect=Decimal("0"),
          guardrail_results={"discovery_only": True},
          comparability=ComparabilityStatus.INCOMPARABLE,
          reasons=("Milestone-1 discovery run; no baseline comparison was preregistered.",),
      ),
      secret_scrub_sha256=sha256_file(scrub_report),
  )
  digest = write_scorecard_once(run_dir / "scorecard.json", scorecard)
  print(digest)
  PY
  ```

  Expected output: one 64-character digest. A second execution must fail with `immutable scorecard already exists`.

- [ ] **Step 7: Attach the exact scorecard path to the lifecycle record through its record API.** First add `attach_scorecard` to `research/der/experiments/records.py` (this module owns every lifecycle rewrite; the README generator arrives at Milestone 7, so evidence attachment is a body append under `## Evidence links`):

  ```python
  def attach_scorecard(record_path: Path, scorecard_path: Path) -> None:
      """Append the exact scorecard path and digest under '## Evidence links'."""
      from research.der.util.hashing import sha256_file

      current = read_record(record_path)
      line = f"- scorecard: `{scorecard_path.as_posix()}` (sha256 `{sha256_file(scorecard_path)}`)\n"
      if line in current.body:
          return
      heading = "## Evidence links"
      if heading in current.body:
          head, _, tail = current.body.partition(heading)
          tail_lines = tail.lstrip("\n")
          body = f"{head}{heading}\n\n{line}{tail_lines}"
      else:
          body = current.body.rstrip("\n") + f"\n\n{heading}\n\n{line}"
      updated = ExperimentRecord(
          path=current.path, front_matter=current.front_matter, body=body
      )
      atomic_replace_bytes(record_path, updated.render().encode("utf-8"))
  ```

  Then attach and set the terminal state:

  ```bash
  uv run python - <<'PY'
  from pathlib import Path
  from research.der.contracts.experiment import ExperimentStatus
  from research.der.experiments.records import attach_scorecard, transition_record
  from research.der.util.time import utc_now
  record = Path("experiments/EXP-0001-acceptance-chain.md")
  scorecard = Path("research/runs/EXP-0001-acceptance-chain/RUN-EXP-0001-acceptance-chain-smoke-01/scorecard.json")
  attach_scorecard(record, scorecard)
  transition_record(
      record,
      target=ExperimentStatus.INCONCLUSIVE,
      now=utc_now(),
      terminal_reason="Acceptance probe passed; it was not a promotion comparison.",
  )
  PY
  git diff -- experiments/EXP-0001-acceptance-chain.md
  ```

  Expected diff includes the exact scorecard path and digest under `## Evidence links`, plus `status`, `updated_at`, and `terminal_reason` only.

- [ ] **Step 8: Run the Milestone 2 acceptance checks.** Run:

  ```bash
  uv run pytest tests/evaluation -q
  uv run python - <<'PY'
  import json
  from pathlib import Path
  scorecard = Path("research/runs/EXP-0001-acceptance-chain/RUN-EXP-0001-acceptance-chain-smoke-01/scorecard.json")
  payload = json.loads(scorecard.read_text())
  assert payload["result"]["observed_models"] == ["deepseek-v4-pro"]
  assert Path(payload["result"]["exact_result_path"]).is_file()
  assert Path("research/runs/EXP-0001-acceptance-chain/RUN-EXP-0001-acceptance-chain-smoke-01/evidence-trace.md").read_text().rstrip().endswith("Trace result: passed")
  print("M2 passed")
  PY
  ```

  Expected output ends with `M2 passed`.

- [ ] **Step 9: Commit.** Run:

  ```bash
  git add \
    research/der/evaluation/scorecard_writer.py \
    research/der/experiments/records.py \
    tests/evaluation/test_scorecard_writer.py \
    tests/fixtures/contracts/scorecard.json \
    research/runs/EXP-0001-acceptance-chain \
    experiments/EXP-0001-acceptance-chain.md
  git commit -m "feat: write immutable scorecards with traced evidence"
  ```

# Phase 3 — Milestone 3: one shared evaluator and a 3–5 task integration battery

Milestone exit: `der eval run` and Python callers synchronously traverse the same `EvalRunner.run(EvalSpec) -> EvalResult` seam; Pier flags are translated by a pure unit-tested function; one process lock prevents overlap; and a preregistered 3–5 task, `k=1` DeepSWE battery produces one exact-path immutable scorecard. No code searches result directories.

### Task 16: Translate `EvalSpec` to the locked Pier CLI and capture its explicit result path

**Files:**
- Create: `research/der/evaluation/pier_command.py`
- Create: `research/der/evaluation/process.py`
- Test: `tests/evaluation/test_pier_command.py`
- Test: `tests/evaluation/test_process.py`

**Interfaces:**
- Consumes: `EvalSpec` from `research.der.contracts.eval`; passed V1–V3 pin files.
- Produces: `build_pier_argv(spec: EvalSpec, *, agent_import_path: str, model_name: str, run_token: str, proxy_base_url: str, qwen_archive: str, qwen_installer: str, qwen_binary: str) -> tuple[str, ...]`; `PierExecution`; `run_pier(argv: tuple[str, ...], *, cwd: Path, timeout_seconds: int, stdout_path: Path) -> PierExecution`.

- [ ] **Step 1: Write the exact flag-translation test.** The agent kwargs must be exactly the `DerQwenAgent` constructor keywords Task 9 defined and Task 10 proved live (`qwen_archive`, `qwen_installer`, `qwen_binary`, `managed_harness`, `owner_settings_json`, `qwen_environment_json`, `max_session_turns`, `max_wall_time`, `max_tool_calls`). Create `tests/evaluation/test_pier_command.py`:

  ```python
  import json
  from pathlib import Path

  from research.der.contracts.eval import EvalSpec
  from research.der.evaluation.pier_command import build_pier_argv


  def _kwargs(argv: tuple[str, ...]) -> dict[str, str]:
      pairs = [argv[i + 1] for i, item in enumerate(argv) if item == "--agent-kwarg"]
      return dict(pair.split("=", 1) for pair in pairs)


  def test_build_pier_argv_is_exact_and_contains_no_secret(tmp_path: Path) -> None:
      spec = EvalSpec.model_validate_json(
          Path("tests/fixtures/contracts/eval-spec.json").read_text()
      ).model_copy(update={"jobs_dir": tmp_path / "jobs"})
      argv = build_pier_argv(
          spec,
          agent_import_path="research.der.agents.qwen:DerQwenAgent",
          model_name="deepseek-v4-pro",
          run_token="run-token-fixture",
          proxy_base_url="http://172.17.0.1:8787/v1",
          qwen_archive="/cache/qwen.tar.gz",
          qwen_installer="/cache/install.sh",
          qwen_binary="/opt/qwen/bin/qwen",
      )
      assert argv[: argv.index("--agent-kwarg")] == (
          "pier", "run",
          "--job-name", spec.run_id,
          "--jobs-dir", str(spec.jobs_dir),
          "--path", str(spec.task_root),
          "--include-task-name", spec.task_ids[0],
          "--n-attempts", str(spec.k),
          "--n-concurrent", str(spec.n_concurrent),
          "--max-retries", "0",
          "--env", "docker",
          "--agent-import-path", "research.der.agents.qwen:DerQwenAgent",
          "--model", "deepseek-v4-pro",
      )
      assert argv[-1] == "--yes"
      kwargs = _kwargs(argv)
      assert kwargs["managed_harness"] == str(spec.staged_harness_dir)
      assert kwargs["qwen_archive"] == "/cache/qwen.tar.gz"
      assert kwargs["qwen_installer"] == "/cache/install.sh"
      assert kwargs["qwen_binary"] == "/opt/qwen/bin/qwen"
      assert kwargs["max_session_turns"] == str(spec.budget.max_session_turns)
      assert kwargs["max_tool_calls"] == str(spec.budget.max_tool_calls)
      assert kwargs["max_wall_time"] == "120m"
      environment = json.loads(kwargs["qwen_environment_json"])
      assert environment["OPENAI_API_KEY"] == "run-token-fixture"
      assert environment["OPENAI_BASE_URL"] == "http://172.17.0.1:8787/v1"
      settings = json.loads(kwargs["owner_settings_json"])
      assert settings["model"]["name"] == "deepseek-v4-pro"
      assert "DEEPSEEK_API_KEY" not in " ".join(argv)
  ```

  (`120m` is the fixture budget's `max_wall_seconds=7200` expressed in whole minutes.)

- [ ] **Step 2: Run the test and observe the intended import failure.** Run `uv run pytest tests/evaluation/test_pier_command.py -q`. Expected failure contains `ModuleNotFoundError: No module named 'research.der.evaluation.pier_command'`.

- [ ] **Step 3: Implement the pure translator.** Create `research/der/evaluation/pier_command.py`:

  ```python
  """Pure translation from the der evaluation contract to Pier v0.3.0 flags."""

  import json
  import math
  from urllib.parse import urlparse

  from research.der.contracts.eval import EvalSpec
  from research.der.errors import ContractError


  def _owner_settings_json(proxy_base_url: str, model_name: str) -> str:
      return json.dumps(
          {
              "modelProviders": {
                  "openai": {
                      "protocol": "openai",
                      "models": [
                          {
                              "id": model_name,
                              "name": f"{model_name} through der proxy",
                              "baseUrl": proxy_base_url,
                              "envKey": "OPENAI_API_KEY",
                          }
                      ],
                  }
              },
              "security": {"auth": {"selectedType": "openai"}},
              "model": {"name": model_name},
              "general": {"enableAutoUpdate": False},
          },
          separators=(",", ":"),
          sort_keys=True,
      )


  def _qwen_environment_json(proxy_base_url: str, model_name: str, run_token: str) -> str:
      return json.dumps(
          {
              "OPENAI_API_KEY": run_token,
              "OPENAI_BASE_URL": proxy_base_url,
              "OPENAI_MODEL": model_name,
              "QWEN_CODE_SUPPRESS_YOLO_WARNING": "1",
          },
          separators=(",", ":"),
          sort_keys=True,
      )


  def build_pier_argv(
      spec: EvalSpec,
      *,
      agent_import_path: str,
      model_name: str,
      run_token: str,
      proxy_base_url: str,
      qwen_archive: str,
      qwen_installer: str,
      qwen_binary: str,
  ) -> tuple[str, ...]:
      if model_name != "deepseek-v4-pro":
          raise ContractError("Pier model must be deepseek-v4-pro")
      if not run_token or any(ch.isspace() for ch in run_token):
          raise ContractError("run_token must be a nonempty, whitespace-free value")
      if not urlparse(proxy_base_url).hostname:
          raise ContractError(f"proxy_base_url has no hostname: {proxy_base_url}")
      argv: list[str] = [
          "pier", "run",
          "--job-name", spec.run_id,
          "--jobs-dir", str(spec.jobs_dir),
          "--path", str(spec.task_root),
      ]
      for task_id in spec.task_ids:
          argv.extend(("--include-task-name", task_id))
      wall_minutes = math.ceil(spec.budget.max_wall_seconds / 60)
      argv.extend((
          "--n-attempts", str(spec.k),
          "--n-concurrent", str(spec.n_concurrent),
          "--max-retries", "0",
          "--env", spec.environment,
          "--agent-import-path", agent_import_path,
          "--model", model_name,
          "--agent-kwarg", f"qwen_archive={qwen_archive}",
          "--agent-kwarg", f"qwen_installer={qwen_installer}",
          "--agent-kwarg", f"qwen_binary={qwen_binary}",
          "--agent-kwarg", f"managed_harness={spec.staged_harness_dir}",
          "--agent-kwarg",
          f"owner_settings_json={_owner_settings_json(proxy_base_url, model_name)}",
          "--agent-kwarg",
          f"qwen_environment_json={_qwen_environment_json(proxy_base_url, model_name, run_token)}",
          "--agent-kwarg", f"max_session_turns={spec.budget.max_session_turns}",
          "--agent-kwarg", f"max_wall_time={wall_minutes}m",
          "--agent-kwarg", f"max_tool_calls={spec.budget.max_tool_calls}",
          "--yes",
      ))
      return tuple(argv)
  ```

  This is the exact command family Task 10 executed by hand; the run token appears only inside `qwen_environment_json` (an expiring proxy credential), never a provider credential.

- [ ] **Step 4: Make the translator test cover multiple tasks and pass.** Add a second test that copies the fixture with `task_ids=("task-a", "task-b")` and matching revisions (and `budget.max_attempts=2`), then asserts two ordered `--include-task-name` pairs. Run `uv run pytest tests/evaluation/test_pier_command.py -q`; expected output is `2 passed`.

- [ ] **Step 5: Write process-protocol tests.** Create `tests/evaluation/test_process.py`:

  ```python
  from pathlib import Path
  import pytest

  from research.der.evaluation.process import extract_result_path
  from research.der.errors import EvaluationError


  def test_extracts_the_only_explicit_result_path(tmp_path: Path) -> None:
      result = tmp_path / "jobs" / "job-1"
      result.mkdir(parents=True)
      text = f"setup\nResults written to {result}\n"
      assert extract_result_path(text) == result.resolve()


  @pytest.mark.parametrize("text", ["", "finished without a path", "Results written to a\nResults written to b\n"])
  def test_missing_or_ambiguous_result_path_fails_closed(text: str) -> None:
      with pytest.raises(EvaluationError, match="exactly one Pier result path"):
          extract_result_path(text)


  def test_path_must_exist(tmp_path: Path) -> None:
      with pytest.raises(EvaluationError, match="does not exist"):
          extract_result_path(f"Results written to {tmp_path / 'missing'}\n")
  ```

- [ ] **Step 6: Implement bounded execution and exact path parsing.** Create `research/der/evaluation/process.py`:

  ```python
  """Synchronous, bounded Pier subprocess protocol."""

  from __future__ import annotations

  from dataclasses import dataclass
  from pathlib import Path
  import re
  import subprocess

  from research.der.errors import EvaluationError

  _RESULT = re.compile(r"^Results written to (?P<path>.+)$", re.MULTILINE)


  @dataclass(frozen=True)
  class PierExecution:
      argv: tuple[str, ...]
      returncode: int
      stdout_path: Path
      exact_result_path: Path


  def extract_result_path(stdout: str) -> Path:
      matches = _RESULT.findall(stdout)
      if len(matches) != 1:
          raise EvaluationError(f"expected exactly one Pier result path, found {len(matches)}")
      path = Path(matches[0]).expanduser().resolve()
      if not path.is_dir():
          raise EvaluationError(f"Pier result path does not exist: {path}")
      return path


  def run_pier(
      argv: tuple[str, ...], *, cwd: Path, timeout_seconds: int, stdout_path: Path
  ) -> PierExecution:
      stdout_path.parent.mkdir(parents=True, exist_ok=True)
      try:
          completed = subprocess.run(
              argv,
              cwd=cwd,
              text=True,
              stdout=subprocess.PIPE,
              stderr=subprocess.STDOUT,
              timeout=timeout_seconds,
              check=False,
          )
      except subprocess.TimeoutExpired as exc:
          stdout_path.write_text(exc.stdout or "", encoding="utf-8")
          raise EvaluationError(f"Pier exceeded {timeout_seconds}s") from exc
      stdout_path.write_text(completed.stdout, encoding="utf-8")
      if completed.returncode != 0:
          raise EvaluationError(
              f"Pier exited {completed.returncode}; transcript: {stdout_path}"
          )
      return PierExecution(
          argv=argv,
          returncode=completed.returncode,
          stdout_path=stdout_path,
          exact_result_path=extract_result_path(completed.stdout),
      )
  ```

- [ ] **Step 7: Run the focused and full unit suites.** Run `uv run pytest tests/evaluation/test_pier_command.py tests/evaluation/test_process.py -q`, then `uv run pytest -q`. Expected: all tests pass.

- [ ] **Step 8: Commit.** Run:

  ```bash
  git add research/der/evaluation/pier_command.py research/der/evaluation/process.py \
    tests/evaluation/test_pier_command.py tests/evaluation/test_process.py
  git commit -m "feat: translate eval specs to exact Pier executions"
  ```

### Task 17: Implement the sole synchronous `EvalRunner`, process lock, owner CLI, and preflight

**Files:**
- Create: `research/der/evaluation/runner.py`
- Create: `research/der/ops/lock.py`
- Create: `research/der/ops/doctor.py`
- Modify: `research/der/cli.py`
- Test: `tests/evaluation/test_runner.py`
- Test: `tests/ops/test_lock.py`
- Test: `tests/ops/test_doctor.py`
- Test: `tests/cli/test_eval.py`

**Interfaces:**
- Consumes: `EvalSpec`, `EvalResult`, `build_pier_argv`, `run_pier`, `normalize_pier_result`, proxy token registry, passed discovery pins.
- Produces: `class EvalRunner: run(self, spec: EvalSpec) -> EvalResult`; `process_lock(path: Path, owner: dict[str, object])`; CLI `der doctor`, `der eval run --spec PATH --output PATH`.

- [ ] **Step 1: Write a seam test using injected collaborators.** Create `tests/evaluation/test_runner.py` with a fake token issuer, fake process function returning the committed pass fixture path, and fake normalizer. Assert call order is `pin-check → lock → token → argv → process → normalize → revoke`; assert the returned object is the exact fake `EvalResult`; assert revocation also occurs when process execution raises.

  ```python
  def test_runner_has_one_synchronous_path(runner_fixture) -> None:
      runner, spec, expected, events = runner_fixture
      assert runner.run(spec) == expected
      assert events == ["pins", "lock-enter", "issue", "argv", "process", "normalize", "revoke", "lock-exit"]
  ```

  Run `uv run pytest tests/evaluation/test_runner.py -q`; expected failure names missing `runner.py`.

- [ ] **Step 2: Write the nonblocking lock test.** In `tests/ops/test_lock.py`, acquire the same lock from a child process and assert the second acquisition raises `ProcessLockError` containing the first holder's PID, run ID, and start time. Also assert stale JSON metadata does not bypass an active kernel lock.

- [ ] **Step 3: Implement the advisory lock.** Create `research/der/ops/lock.py` using `fcntl.flock(fd, LOCK_EX | LOCK_NB)`. Write owner metadata only after lock acquisition, `fsync`, hold the descriptor for the context lifetime, and unlink metadata only after unlock. Raise `ProcessLockError` without killing the current holder.

- [ ] **Step 4: Implement `EvalRunner` with injected boundaries.** Create `research/der/evaluation/runner.py`:

  ```python
  """The only scored evaluator seam."""

  from __future__ import annotations

  from dataclasses import dataclass
  from pathlib import Path
  from typing import Callable, Protocol

  from research.der.contracts.eval import EvalResult, EvalSpec
  from research.der.evaluation.normalizer import normalize_pier_result
  from research.der.evaluation.pier_command import build_pier_argv
  from research.der.evaluation.process import PierExecution, run_pier
  from research.der.ops.lock import process_lock
  from research.der.pins import require_passed_pin


  class TokenIssuer(Protocol):
      def issue(self, *, experiment_id: str, run_id: str, budget: object) -> str: ...
      def revoke(self, token: str) -> None: ...


  @dataclass
  class EvalRunner:
      repo_root: Path
      token_issuer: TokenIssuer
      process: Callable[..., PierExecution] = run_pier
      normalizer: Callable[..., EvalResult] = normalize_pier_result

      def run(self, spec: EvalSpec) -> EvalResult:
          v1 = require_passed_pin(spec.pins.pier_artifacts)
          v2 = require_passed_pin(spec.pins.proxy_route)
          v3 = require_passed_pin(spec.pins.qwen_archive)
          lock_path = self.repo_root / "var/locks/evaluator.lock"
          with process_lock(lock_path, {"experiment_id": spec.experiment_id, "run_id": spec.run_id}):
              token = self.token_issuer.issue(
                  experiment_id=spec.experiment_id,
                  run_id=spec.run_id,
                  budget=spec.budget,
              )
              try:
                  argv = build_pier_argv(
                      spec,
                      agent_import_path="research.der.agents.qwen:DerQwenAgent",
                      model_name="deepseek-v4-pro",
                      run_token=token,
                      proxy_base_url=str(v2["proxy_base_url"]),
                      qwen_archive=str(v3["archive_path"]),
                      qwen_installer=str(v3["installer_path"]),
                      qwen_binary=str(v3["qwen_binary"]),
                  )
                  execution = self.process(
                      argv,
                      cwd=self.repo_root,
                      timeout_seconds=spec.budget.max_wall_seconds + 120,
                      stdout_path=spec.jobs_dir / spec.run_id / "pier.stdout.log",
                  )
                  return self.normalizer(
                      spec=spec,
                      exact_result_path=execution.exact_result_path,
                      v1=v1,
                      observations_path=self.repo_root / "var/state/proxy/observations.jsonl",
                  )
              finally:
                  self.token_issuer.revoke(token)
  ```

  The token issuer is a thin adapter over Task 8's `RunRegistry`/`BudgetLedger`: `issue(...)` registers the run in both stores (policy `deepseek-v4-pro-v1`, `expected_attempts = len(spec.task_ids) * spec.k`, expiry `now + max_wall_seconds + 1h`) and returns the plaintext token; `revoke(token)` deletes the registration file so the token dies with the run. Write it in `runner.py` as `RegistryTokenIssuer` with exactly that behavior and unit-test it with `tmp_path` stores.

- [ ] **Step 5: Write doctor tests before implementation.** Test that `run_doctor(repo_root)` reports named checks for Python, `uv`, Docker, Pier version, four required passed pins, suite disjointness, proxy health, dedicated-worktree status, free disk, and absence of provider keys in a supplied container environment. A failed check makes `ok=False`; no check may be silently skipped.

- [ ] **Step 6: Implement preflight and CLI wiring.** `research/der/ops/doctor.py` returns typed `DoctorReport`; external commands use argument arrays and 10-second timeouts. Extend `research/der/cli.py` so:

  ```text
  der doctor [--json]
  der eval run --spec PATH --output PATH
  ```

  `eval run` validates the strict JSON spec, constructs the filesystem-backed token issuer, invokes `EvalRunner.run` once, and writes canonical JSON to `--output` with exclusive creation. It never finalizes or promotes; those are separate commands.

- [ ] **Step 7: Prove CLI behavior without Docker/provider traffic.** Use Typer's `CliRunner` and monkeypatch only `build_runner`. Assert malformed specs exit `2`; an occupied process lock exits `1`; a successful fake writes exactly the supplied result and prints `exact_result_path=<path>`.

- [ ] **Step 8: Run all checks.** Run:

  ```bash
  uv run pytest tests/evaluation/test_runner.py tests/ops/test_lock.py tests/ops/test_doctor.py tests/cli/test_eval.py -q
  uv run python -m research.der.cli doctor --json | uv run python -m json.tool >/dev/null
  uv run pytest -q
  ```

  Expected: tests pass; doctor JSON parses. Local environmental failures may appear as explicit failed rows, not crashes.

- [ ] **Step 9: Commit.** Run:

  ```bash
  git add research/der/evaluation/runner.py research/der/ops/lock.py \
    research/der/ops/doctor.py research/der/cli.py \
    tests/evaluation/test_runner.py tests/ops/test_lock.py tests/ops/test_doctor.py tests/cli/test_eval.py
  git commit -m "feat: expose the sole synchronous evaluation seam"
  ```

### Task 18: Run the preregistered 3–5 task `k=1` integration battery

**Files:**
- Create: `experiments/EXP-0002-integration-battery.md`
- Create: `research/runs/EXP-0002-integration-battery/RUN-EXP-0002-integration-battery-smoke-01/eval-spec.json`
- Create: `research/runs/EXP-0002-integration-battery/RUN-EXP-0002-integration-battery-smoke-01/eval-result.json`
- Create: `research/runs/EXP-0002-integration-battery/RUN-EXP-0002-integration-battery-smoke-01/scorecard.json`
- Test: live acceptance commands in this task

**Interfaces:**
- Consumes: V7 audited task IDs/checksums; `create_record`/`transition_record`/`attach_scorecard`; `stage_harness`; `der eval run`; `write_scorecard_once`.
- Produces: the first multi-task exact-path scorecard and evidence proving one shared evaluator path. (The one-command `der experiment finalize` door arrives with the finalizer in Task 28; this milestone composes the same primitives explicitly.)

- [ ] **Step 1: Select exactly four audited tasks from V7 without inventing names.** Run:

  ```bash
  uv run python - <<'PY'
  import json
  from pathlib import Path
  from research.der.pins import require_passed_pin
  v7 = require_passed_pin("V7")
  audited = v7["audited_verifiers"]
  assert len(audited) >= 4, "STOP: fewer than four audited tasks; escalate V7 evidence"
  chosen = audited[:4]
  Path("var").mkdir(exist_ok=True)
  Path("var/integration-tasks.json").write_text(json.dumps(chosen, indent=2) + "\n")
  print("\n".join(row["task_id"] for row in chosen))
  PY
  ```

  Expected: four distinct task IDs. If the assertion fires, write a blocked amendment pin via `write_discovery_pin` (verification `V7`, `status: blocked`, the failing count in the observation), exit `78`, and stop.

- [ ] **Step 2: Preregister before staging or execution.** Generate the record through the contract (same pattern as Task 10 Step 6 — identity is the fixture harness this battery stages):

  ```bash
  uv run python - <<'PY'
  from decimal import Decimal
  from pathlib import Path

  from research.der.contracts.eval import HarnessIdentity, RunBudget
  from research.der.contracts.experiment import (
      ExperimentContract, ExperimentFrontMatter, ExperimentStatus, Guardrail,
  )
  from research.der.experiments.records import create_record
  from research.der.util.git import git_tree_oid, head_commit
  from research.der.util.hashing import sha256_file
  from research.der.util.time import utc_now

  now = utc_now()
  identity = HarnessIdentity(
      source_commit=head_commit(Path.cwd()),
      harness_tree_oid=git_tree_oid(Path.cwd(), Path("tests/fixtures/harness/managed")),
      runtime_manifest_digest=sha256_file(Path("research/config/runtime-policy.toml")),
  )
  front = ExperimentFrontMatter(
      experiment_id="EXP-0002-integration-battery",
      slug="integration-battery",
      title="Shared-evaluator integration battery",
      status=ExperimentStatus.PROPOSED,
      created_at=now,
      updated_at=now,
      baseline_identity=identity,
      candidate_identity=identity,
      contract=ExperimentContract(
          hypothesis=(
              "The shared EvalRunner door completes four DeepSWE tasks with exact "
              "result association, correct classification, and full artifact collection."
          ),
          primary_metric="confirmation_macro_pass_at_1",
          minimum_effect=Decimal("0"),
          guardrails=(
              Guardrail(metric="invalid_fraction", operator="<=", threshold=Decimal("0")),
          ),
          falsifier=(
              "Any missing exact result path, any model other than deepseek-v4-pro, "
              "or any unclassified attempt falsifies the battery."
          ),
          suite_version="integration-v0",
          k=1,
          budget=RunBudget(
              max_cost_usd=Decimal("80"),
              max_wall_seconds=7200,
              max_attempts=4,
              max_input_tokens=1_200_000,
              max_output_tokens=240_000,
              max_tool_calls=1200,
              max_session_turns=40,
          ),
      ),
      run_ids=(),
  )
  body = (
      "# EXP-0002 — Shared-evaluator integration battery\n\n"
      "## Rationale\n\n"
      "Milestone-3 seam proof on four V7-audited tasks; no baseline comparison.\n\n"
      "## Evidence links\n\n"
      "Attached after the run.\n"
  )
  create_record(Path("experiments/EXP-0002-integration-battery.md"), front, body)
  print("created")
  PY
  git add experiments/EXP-0002-integration-battery.md
  git commit -m "research: preregister the integration battery"
  ```

  Expected: `created`, then a commit whose timestamp precedes all run artifacts (the preregistration proof).

- [ ] **Step 3: Stage and emit the strict spec.** Run:

  ```bash
  export RUN_ID=RUN-EXP-0002-integration-battery-smoke-01
  export DER_LIVE=1
  uv run python - <<'PY'
  import json
  import os
  from decimal import Decimal
  from pathlib import Path

  from research.der.contracts.base import canonical_json_bytes
  from research.der.contracts.eval import DiscoveryPinPaths, EvalSpec, RunBudget
  from research.der.experiments.records import read_record
  from research.der.harness.stage import stage_harness
  from research.der.pins import require_passed_pin

  run_id = os.environ["RUN_ID"]
  record = read_record(Path("experiments/EXP-0002-integration-battery.md"))
  chosen = json.loads(Path("var/integration-tasks.json").read_text())
  v7 = require_passed_pin("V7")
  staged = Path(f"var/staging/{run_id}/harness")
  Path("var/staging/overlay-empty").mkdir(parents=True, exist_ok=True)
  stage_harness(
      Path("tests/fixtures/harness/managed"),
      Path("var/staging/overlay-empty"),
      staged,
      Path(f"var/staging/{run_id}/rollout-home"),
  )
  spec = EvalSpec(
      experiment_id=record.front_matter.experiment_id,
      run_id=run_id,
      identity=record.front_matter.candidate_identity,
      baseline_tree_oid=record.front_matter.baseline_identity.harness_tree_oid,
      suite_version=record.front_matter.contract.suite_version,
      suite_class="smoke",
      task_root=Path(v7["task_root"]),
      task_revisions={row["task_id"]: v7["task_checksums"][row["task_id"]] for row in chosen},
      task_ids=tuple(row["task_id"] for row in chosen),
      k=record.front_matter.contract.k,
      n_concurrent=2,
      jobs_dir=Path("var/pier/jobs"),
      staged_harness_dir=staged,
      pins=DiscoveryPinPaths(
          pier_artifacts=Path("research-plan/pins/v1-pier-artifact-layout.md"),
          proxy_route=Path("research-plan/pins/v2-acceptance-chain.md"),
          qwen_archive=Path("research-plan/pins/v3-qwen-archive-install.md"),
      ),
      model_policy_id="deepseek-v4-pro-v1",
      budget=record.front_matter.contract.budget,
  )
  out = Path(f"research/runs/EXP-0002-integration-battery/{run_id}/eval-spec.json")
  out.parent.mkdir(parents=True, exist_ok=True)
  out.write_bytes(canonical_json_bytes(spec))
  print("eval-spec valid", len(spec.task_ids), "tasks")
  PY
  ```

  Expected: `eval-spec valid 4 tasks` (`n_concurrent=2` is the conservative pre-V10 setting; Task 19 pins the supported range). The staging call itself enforces the request-shaping/executable deny policy and fails loudly on a violation.

- [ ] **Step 4: Execute through the owner door only.** The proxy from Task 10 Step 7 must be healthy, and the evaluator shell must hold no provider key — only the proxy process does:

  ```bash
  curl -fsS http://127.0.0.1:8787/healthz
  test -z "${DEEPSEEK_API_KEY-}"
  uv run python - <<'PY'
  from pathlib import Path
  from research.der.contracts.experiment import ExperimentStatus
  from research.der.experiments.records import transition_record
  from research.der.util.time import utc_now
  transition_record(
      Path("experiments/EXP-0002-integration-battery.md"),
      target=ExperimentStatus.RUNNING,
      now=utc_now(),
      append_run_id="RUN-EXP-0002-integration-battery-smoke-01",
  )
  PY
  uv run der eval run \
    --spec research/runs/EXP-0002-integration-battery/RUN-EXP-0002-integration-battery-smoke-01/eval-spec.json \
    --output research/runs/EXP-0002-integration-battery/RUN-EXP-0002-integration-battery-smoke-01/eval-result.json \
    2>&1 | tee research/runs/EXP-0002-integration-battery/RUN-EXP-0002-integration-battery-smoke-01/owner-eval.log
  ```

  Expected: exactly one `exact_result_path=` line; Pier reports four tasks and one attempt each; proxy observations contain only `deepseek-v4-pro`; no provider credential appears in the log.

- [ ] **Step 5: Record the battery as inconclusive, not adopted.** Compose the same primitives Task 15 proved (the one-command finalizer door is built in Task 28):

  ```bash
  uv run python - <<'PY'
  from datetime import UTC, datetime
  from decimal import Decimal
  from pathlib import Path
  from research.der.contracts.eval import EvalResult
  from research.der.contracts.experiment import ExperimentStatus
  from research.der.contracts.scorecard import (
      ComparabilityStatus, PromotionDecision, PromotionVerdict, Scorecard,
  )
  from research.der.evaluation.scorecard_writer import write_scorecard_once
  from research.der.experiments.records import attach_scorecard, transition_record
  from research.der.util.hashing import sha256_file
  from research.der.util.time import utc_now

  run_dir = Path("research/runs/EXP-0002-integration-battery/RUN-EXP-0002-integration-battery-smoke-01")
  result = EvalResult.model_validate_json((run_dir / "eval-result.json").read_text())
  record = Path("experiments/EXP-0002-integration-battery.md")
  scrub = run_dir / "secret-scrub.json"
  scrub.write_text('{"status":"passed","matches":[]}\n')
  scorecard = Scorecard(
      created_at=datetime.now(UTC),
      experiment_record_sha256=sha256_file(record),
      baseline_identity=result.identity,
      candidate_identity=result.identity,
      result=result,
      decision=PromotionDecision(
          verdict=PromotionVerdict.INCONCLUSIVE,
          primary_metric="confirmation_macro_pass_at_1",
          baseline_value=None,
          candidate_value=None,
          observed_effect=None,
          minimum_effect=Decimal("0"),
          guardrail_results={"invalid_fraction<=0": all(
              attempt.outcome.value != "invalid"
              for task in result.tasks for attempt in task.attempts
          )},
          comparability=ComparabilityStatus.INCOMPARABLE,
          reasons=("Integration battery proves the seam; it has no baseline comparison.",),
      ),
      secret_scrub_sha256=sha256_file(scrub),
  )
  print(write_scorecard_once(run_dir / "scorecard.json", scorecard))
  attach_scorecard(record, run_dir / "scorecard.json")
  transition_record(
      record,
      target=ExperimentStatus.INCONCLUSIVE,
      now=utc_now(),
      terminal_reason="Integration battery proves the seam; it has no baseline comparison.",
  )
  PY
  ```

  Expected: one 64-character digest; lifecycle status `inconclusive` with the scorecard attached under `## Evidence links`.

- [ ] **Step 6: Verify the milestone invariants.** Run:

  ```bash
  uv run python - <<'PY'
  from pathlib import Path
  from research.der.contracts.scorecard import Scorecard
  from research.der.evaluation.scorecard_writer import write_scorecard_once
  path = Path("research/runs/EXP-0002-integration-battery/RUN-EXP-0002-integration-battery-smoke-01/scorecard.json")
  card = Scorecard.model_validate_json(path.read_text())
  assert card.result.observed_models == ("deepseek-v4-pro",)
  assert len(card.result.tasks) == 4
  try:
      write_scorecard_once(path, card)
  except FileExistsError:
      print("scorecard valid and immutable")
  else:
      raise SystemExit("scorecard was rewritable — STOP")
  PY
  test "$(grep -c '^exact_result_path=' research/runs/EXP-0002-integration-battery/RUN-EXP-0002-integration-battery-smoke-01/owner-eval.log)" -eq 1
  ! grep -R -E 'sk-[A-Za-z0-9]{12,}|DEEPSEEK_API_KEY=' research/runs/EXP-0002-integration-battery
  uv run pytest -q
  ```

  Expected: `scorecard valid and immutable`; shell exits `0`; all tests pass.

- [ ] **Step 7: Commit.** Run:

  ```bash
  git add experiments/EXP-0002-integration-battery.md \
    research/runs/EXP-0002-integration-battery
  git commit -m "test: prove the shared evaluator on four DeepSWE tasks"
  ```

### Task 19: Discovery V10 — pin host capacity, caches, provider rate behavior, and supported concurrency

**Files:**
- Create: `scripts/discover_v10_capacity.py`
- Create: `research-plan/pins/v10-server-capacity.md`
- Test: `tests/discovery/test_v10_capacity.py`

**Interfaces:**
- Consumes: four-task integration battery, Docker, DeepSWE/Qwen caches, proxy observations.
- Produces: passed V10 pin with exact host facts and `supported_n_concurrent` in `[4, 8]`; STOP evidence otherwise.

- [ ] **Step 1: Write parser tests with committed command transcripts.** Test `parse_meminfo`, `parse_df`, `parse_docker_info`, and `choose_supported_concurrency`. The chooser returns the largest fully successful probe in `(4, 6, 8)` and raises `DiscoveryBlockedError` (Task 0's STOP error) if none reaches `4`.

- [ ] **Step 2: Implement the probe.** `scripts/discover_v10_capacity.py` must record, without redaction except usernames/home paths: `uname -a`, `nproc`, `/proc/meminfo`, `df -B1`, `docker info --format '{{json .}}'`, `docker system df`, DeepSWE image digest, Qwen archive/cache digests, and three controlled four-task runs at concurrency 4, 6, and 8. Each run reuses the same frozen harness and gets a distinct preregistered smoke record and budget. Record wall time, max RSS, Docker failures, HTTP 429/5xx counts, and proxy costs.

- [ ] **Step 3: Encode the STOP rule in code, not prose.** The script exits `78` and writes `status: blocked` when: concurrency 4 cannot complete without host OOM/disk exhaustion; required image/archive caches are absent; proxy observations show an unclassified error; or measured disk headroom after the run is below 50 GiB. It never lowers the architecture below concurrency 4.

- [ ] **Step 4: Run the real discovery.** Run:

  ```bash
  export DER_LIVE=1
  dotenvx run -f "$DER_DOTENVX_FILE" -- \
    uv run python scripts/discover_v10_capacity.py \
      --repo-root . \
      --battery-record experiments/EXP-0002-integration-battery.md \
      --pin research-plan/pins/v10-server-capacity.md
  rc=$?
  test "$rc" -eq 0 || test "$rc" -eq 78
  exit "$rc"
  ```

  Expected pass output: `status: passed`, `supported_n_concurrent: 4|6|8`, exact transcripts and digests. Exit `78` means stop all later tasks and send the pin to the owner; do not resize the approved system.

- [ ] **Step 5: Verify and commit.** Run `uv run pytest tests/discovery/test_v10_capacity.py -q && uv run der pins assert V10`. Then:

  ```bash
  git add scripts/discover_v10_capacity.py research-plan/pins/v10-server-capacity.md \
    tests/discovery/test_v10_capacity.py
  git commit -m "research: pin server capacity and safe Pier concurrency"
  ```

# Phase 4 — Milestone 4: patch AHE onto the shared evaluator door

Milestone exit: the pinned AHE source is vendored with attribution; its active evaluator path calls `EvalRunner` synchronously; reward text and recency recovery are absent; optimizer attribution consumes per-task pass fractions; a two-iteration toy campaign proves exact result association and deterministic resume.

### Task 20: Vendor pinned AHE and define its narrow der adapter

**Files:**
- Modify: `research/UPSTREAM.md` (created in Task 1)
- Create: `research/PATCHES.md`
- Create: `research/evolve.py`
- Create: `research/configs/base.yaml`
- Create: `research/configs/ahe-der-v1.yaml`
- Create: `research/agents/` from the pinned upstream
- Create: `research/der/integrations/ahe.py`
- Test: `tests/integrations/test_ahe.py`
- Test: `tests/fixtures/ahe/eval-result.json`

**Interfaces:**
- Consumes: pinned AHE commit; `EvalRunner.run(EvalSpec) -> EvalResult`; lifecycle creation; per-task `TaskResult.pass_fraction`.
- Produces: `run_ahe_evaluation(request: AheEvaluationRequest, runner: EvalRunner) -> AheEvaluationResponse`; `to_optimizer_state(result: EvalResult) -> dict[str, Decimal]`.

- [ ] **Step 1: Copy only the approved upstream tree and record its identity.** From the pristine source cache at `/var/cache/der/sources/ahe` (already checked out at commit `faf44bc4aea57413c520bc5711c6ebf628e0da1e` by Task 1), copy `evolve.py`, `configs/base.yaml`, and `agents/` into `research/`. Extend the existing `research/UPSTREAM.md` (Task 1) with a new "Vendored AHE files" section recording UTC retrieval timestamp, `git show -s --format=%H`, `git status --porcelain`, license path/digest, and SHA-256 for every copied file. Do not copy `.git`, caches, outputs, or credentials.

- [ ] **Step 2: Initialize the patch ledger before changing vendored code.** Create `research/PATCHES.md` with columns `ID`, `upstream commit`, `file/span`, `behavior removed`, `behavior added`, `rationale`, `test`. Add four rows with IDs `AHE-001` through `AHE-004` for the four approved seams; set each row's test to the exact test name planned below, not a prose promise.

- [ ] **Step 3: Write adapter tests.** Create `tests/integrations/test_ahe.py`:

  ```python
  from decimal import Decimal
  from pathlib import Path

  from research.der.contracts.eval import EvalResult
  from research.der.integrations.ahe import AheEvaluationRequest, run_ahe_evaluation, to_optimizer_state


  def test_optimizer_state_is_per_task_pass_fraction() -> None:
      result = EvalResult.model_validate_json(Path("tests/fixtures/ahe/eval-result.json").read_text())
      assert to_optimizer_state(result) == {
          "task-a": Decimal("0.75"),
          "task-b": Decimal("0.00"),
      }


  def test_adapter_calls_runner_once_and_preserves_exact_identity(fake_runner, ahe_request) -> None:
      response = run_ahe_evaluation(ahe_request, fake_runner)
      assert fake_runner.calls == [ahe_request.eval_spec]
      assert response.experiment_id == ahe_request.eval_spec.experiment_id
      assert response.run_id == ahe_request.eval_spec.run_id
      assert response.evaluator_job_id == fake_runner.result.evaluator_job_id
      assert response.exact_result_path == fake_runner.result.exact_result_path
  ```

  Build the fixture by copying the strict scorecard's `result` and changing only two tasks to four attempts with pass fractions `0.75` and `0.00`. Run the tests; expected import failure names `research.der.integrations.ahe`.

- [ ] **Step 4: Implement the adapter as data conversion, not orchestration duplication.** Create `research/der/integrations/ahe.py`:

  ```python
  """Intentional AHE-to-der evaluator seam."""

  from dataclasses import dataclass
  from decimal import Decimal
  from pathlib import Path

  from research.der.contracts.eval import EvalResult, EvalSpec
  from research.der.evaluation.runner import EvalRunner


  @dataclass(frozen=True)
  class AheEvaluationRequest:
      iteration: int
      eval_spec: EvalSpec


  @dataclass(frozen=True)
  class AheEvaluationResponse:
      iteration: int
      experiment_id: str
      run_id: str
      evaluator_job_id: str
      exact_result_path: Path
      per_task_pass_fraction: dict[str, Decimal]
      eval_result: EvalResult


  def to_optimizer_state(result: EvalResult) -> dict[str, Decimal]:
      return {task.task_id: task.pass_fraction for task in result.tasks}


  def run_ahe_evaluation(
      request: AheEvaluationRequest, runner: EvalRunner
  ) -> AheEvaluationResponse:
      result = runner.run(request.eval_spec)
      return AheEvaluationResponse(
          iteration=request.iteration,
          experiment_id=result.experiment_id,
          run_id=result.run_id,
          evaluator_job_id=result.evaluator_job_id,
          exact_result_path=result.exact_result_path,
          per_task_pass_fraction=to_optimizer_state(result),
          eval_result=result,
      )
  ```

- [ ] **Step 5: Add the constrained owner overlay.** Create `research/configs/ahe-der-v1.yaml` as an overlay on the copied base config with `max_iterations: 10`, finite command/evaluation timeouts, `best_of_n: false`, `explore: false`, ADB and Evolve model role `deepseek-v4-pro`, and paths under the dedicated worktree. Do not put endpoint, provider key, temperature, `top_p`, `max_tokens`, hooks, or MCP commands in this file. Add a policy test that rejects those keys recursively.

- [ ] **Step 6: Run source-integrity and adapter tests.** Run `uv run pytest tests/integrations/test_ahe.py tests/harness/test_policy.py -q` and a script that verifies unpatched copied files still match `UPSTREAM.md`. Expected: pass.

- [ ] **Step 7: Commit.** Run:

  ```bash
  git add research/UPSTREAM.md research/PATCHES.md research/evolve.py \
    research/configs research/agents research/der/integrations/ahe.py \
    tests/integrations/test_ahe.py tests/fixtures/ahe/eval-result.json
  git commit -m "chore: vendor AHE and define its evaluator adapter"
  ```

### Task 21: Discovery V4 and the minimal four-seam `evolve.py` patch

**Files:**
- Create: `scripts/discover_v4_ahe_attribution.py`
- Create: `research-plan/pins/v4-ahe-attribution-seam.md`
- Modify: `research/evolve.py`
- Modify: `research/PATCHES.md`
- Test: `tests/discovery/test_v4_ahe_attribution.py`
- Test: `tests/integrations/test_ahe_patched_source.py`

**Interfaces:**
- Consumes: pristine AHE copy/digests and `run_ahe_evaluation`.
- Produces: a passed V4 pin enumerating every producer/consumer of all-k state and recency recovery; the minimal active-path patch.

- [ ] **Step 1: Implement source analysis with exact evidence.** `scripts/discover_v4_ahe_attribution.py` parses `research/evolve.py` with `ast`, supplements it with exact-string searches for `reward.txt`, `latest`, `mtime`, `glob`, `harbor`, `task_results`, and `all`, and emits JSON containing function names, 1-based line spans, source snippets, and caller/callee names. It must identify the `compute_stats` all-k assignment and every read of the resulting task state.

- [ ] **Step 2: Encode the discovery contradiction.** Compare findings with the source-verified assumption: exactly one active command-construction seam, one reward-text parser, one recency-recovery branch, and no all-k consumer outside task-history/attribution. Any extra active consumer or inability to prove data flow writes `status: blocked`, includes all snippets, exits `78`, and stops the plan. Do not patch around an unexpected consumer.

- [ ] **Step 3: Run and record V4.** Run:

  ```bash
  uv run python scripts/discover_v4_ahe_attribution.py \
    --source research/evolve.py \
    --upstream-commit faf44bc4aea57413c520bc5711c6ebf628e0da1e \
    --pin research-plan/pins/v4-ahe-attribution-seam.md
  rc=$?; test "$rc" -eq 0 || test "$rc" -eq 78; exit "$rc"
  ```

  Expected pass pin includes exact spans, source SHA-256, and `unexpected_consumers: []`. Exit `78` is an owner escalation.

- [ ] **Step 4: Write patch-characterization tests before editing.** `tests/integrations/test_ahe_patched_source.py` reads `research/evolve.py` and asserts: no executable call constructs `harbor run`; no read of `verifier/reward.txt`; no result selection by `mtime`, `max(...stat...)`, or latest-directory sorting; `run_ahe_evaluation` is called once per iteration; task history receives Decimal-compatible pass fractions. Also compare changed line ranges against the four V4 spans and fail on edits outside those spans plus imports.

- [ ] **Step 5: Apply the seam patch using the V4 spans.** In the discovered iteration function, replace the active evaluator block with this complete call shape, adapting only local variable names listed in the pin:

  ```python
  ahe_response = run_ahe_evaluation(
      AheEvaluationRequest(iteration=iteration, eval_spec=eval_spec),
      eval_runner,
  )
  eval_result = ahe_response.eval_result
  task_results = {
      task_id: str(pass_fraction)
      for task_id, pass_fraction in ahe_response.per_task_pass_fraction.items()
  }
  result_path = ahe_response.exact_result_path
  ```

  Delete, rather than leave dormant, the discovered Harbor argv builder, `reward.txt` parsing branch, and directory-recency recovery branch. Preserve AHE proposal generation, iteration bookkeeping, and resume state outside the four spans.

- [ ] **Step 6: Update every patch-ledger row with the exact post-edit span and test.** Include unified diff excerpts and rationale: semantic evaluator mismatch; structured result ownership; fail-closed identity; pass-fraction attribution. State explicitly that no other AHE source files changed.

- [ ] **Step 7: Run tests and a forbidden-pattern scan.** Run:

  ```bash
  uv run pytest tests/discovery/test_v4_ahe_attribution.py tests/integrations/test_ahe_patched_source.py tests/integrations/test_ahe.py -q
  ! grep -nE 'reward\.txt|stat\(\).*st_mtime|harbor[[:space:]]+run' research/evolve.py
  git diff --check
  ```

  Expected: pass and no grep output.

- [ ] **Step 8: Commit.** Run:

  ```bash
  git add scripts/discover_v4_ahe_attribution.py research-plan/pins/v4-ahe-attribution-seam.md \
    research/evolve.py research/PATCHES.md tests/discovery/test_v4_ahe_attribution.py \
    tests/integrations/test_ahe_patched_source.py
  git commit -m "feat: patch AHE onto EvalRunner and pass-fraction attribution"
  ```

### Task 22: Prove two AHE iterations, exact association, crash resume, and patch minimality

**Files:**
- Create: `tests/integrations/test_ahe_resume.py`
- Create: `research/runs/ahe-toy/README.md`
- Modify: `research/configs/ahe-der-v1.yaml`
- Test: live two-iteration acceptance commands

**Interfaces:**
- Consumes: patched AHE, `EvalRunner`, lifecycle/finalizer commands, V10 supported concurrency.
- Produces: two finalized toy experiments and deterministic campaign resume evidence.

- [ ] **Step 1: Write deterministic resume tests.** Use a fake `EvalRunner` returning fixed iteration-0 and iteration-1 results. Crash immediately after writing iteration-0's finalizer commit marker. Restart with the same campaign state and assert iteration 0 is not rerun, iteration 1 runs once, and each lifecycle record references its own evaluator job ID/result path.

- [ ] **Step 2: Add campaign state fields only.** In the AHE adapter boundary, persist `campaign_id`, `next_iteration`, `completed_experiment_ids`, and digest of the current proposal. Write atomically. Do not create a campaign scorecard or campaign baseline.

- [ ] **Step 3: Run the toy loop with two tiny development tasks and `k=1`.** Read task IDs from V7, preregister `EXP-0003-ahe-toy-iteration-0` and `EXP-0004-ahe-toy-iteration-1`, then run:

  ```bash
  export DER_LIVE=1
  dotenvx run -f "$DER_DOTENVX_FILE" -- \
    uv run python research/evolve.py \
      --config research/configs/ahe-der-v1.yaml \
      --campaign-id CAMP-AHE-TOY-01 \
      --max-iterations 2 \
      --task-limit 2 \
      --k 1 \
      2>&1 | tee research/runs/ahe-toy/two-iteration.log
  ```

  Expected: two distinct experiment IDs, two distinct explicit Pier result paths, two scorecards, and `next_iteration: 2`. If the vendored `evolve.py` at the pinned commit exposes different flag names for these concepts, use its actual flags and record the exact invocation in `research/runs/ahe-toy/README.md`; do not add new CLI surface beyond the four patched seams.

- [ ] **Step 4: Prove hard-kill resume.** Repeat under `CAMP-AHE-TOY-02`, arrange `DER_TEST_KILL_AFTER_FINALIZE=1`, and expect exit `137` after iteration 0's commit marker. Rerun the identical command without the variable. Expected log says `resume: iteration 0 already finalized`; only iteration 1 invokes Pier.

- [ ] **Step 5: Verify identity and minimality.** Run a script that joins lifecycle records, scorecards, AHE campaign state, Pier job IDs, and exact result paths and rejects any duplicate/mismatch. Then compare `git diff <AHE upstream blob> -- research/evolve.py` to V4 allowed spans. Record command/output in `research/runs/ahe-toy/README.md`.

- [ ] **Step 6: Run all tests.** Run `uv run pytest tests/integrations/test_ahe.py tests/integrations/test_ahe_patched_source.py tests/integrations/test_ahe_resume.py -q && uv run pytest -q`. Expected: all pass.

- [ ] **Step 7: Commit.** Run:

  ```bash
  git add research/configs/ahe-der-v1.yaml research/der/integrations/ahe.py \
    tests/integrations/test_ahe_resume.py research/runs/ahe-toy experiments/EXP-0003-ahe-toy-iteration-0.md \
    experiments/EXP-0004-ahe-toy-iteration-1.md README.md
  git commit -m "test: prove AHE exact-path evaluation and deterministic resume"
  ```

# Phase 5 — Milestone 5: runtime-shaped harness, identity gates, and hand-authored A/B owner-value gate

Milestone exit: `harness/` is a real Qwen project; daily sync refuses an unevaluated managed tree; the baseline is derived from immutable adopted scorecards; comparability is exact; adoption renders executable changes first and refuses baseline movement; and one hand-authored A/B experiment is evaluated on development then confirmation and either adopted or honestly rejected. The unattended path still cannot write `harness/`.

### Task 23: Create the managed Qwen harness and enforce no-eval-no-sync

**Files:**
- Create: `harness/QWEN.md`
- Create: `harness/.qwen/settings.json`
- Create: `harness/.qwen/skills/der-engineering/SKILL.md`
- Create: `research/der/harness/live_state.py`
- Create: `research/der/harness/sync.py`
- Modify: `research/der/cli.py`
- Test: `tests/harness/test_live_state.py`
- Test: `tests/harness/test_sync.py`

**Interfaces:**
- Consumes: staging policy, `compute_identity`/`git_tree_oid` from Task 3, immutable scorecards.
- Produces: `load_live_state(path: Path) -> LiveState`; `sync_harness(source: Path, destination: Path, *, evaluated_tree_oids: set[str], force: bool) -> SyncResult`; CLI `der harness sync`.

- [ ] **Step 1: Write the three runtime-shaped project files.** `QWEN.md` states repository objective, test commands, evidence discipline, no secret access, and commit requirement. `settings.json` contains only Qwen project behavior verified for v0.20.0 and no request-shaping/executable fields. The skill gives a deterministic loop: inspect task, make smallest change, run focused test, run required verifier-facing checks, commit. Run `uv run der harness policy-check harness`; expected `request_shaping_keys=0 executable_keys=0`.

- [ ] **Step 2: Write live-state parser tests.** Define a strict JSON state with `schema_version: der.live-state.v1`, `managed_tree_oid`, `reviewed_at`, and ordered `included_paths`. Reject unknown fields, paths outside `QWEN.md`/`.qwen`, duplicates, symlinks, absolute paths, and a tree OID not matching the source directory.

- [ ] **Step 3: Write sync refusal tests.** In a temporary Git repository, create managed and daily trees. Assert: matching evaluated tree copies exactly; an unevaluated `main:harness` tree raises `UnevaluatedHarnessError`; `force=True` copies but writes an append-only force record with owner, UTC time, old/new OIDs, and reason; destination-only files under managed paths are removed; files outside managed paths are untouched.

- [ ] **Step 4: Implement exact live-state parsing and sync.** `live_state.py` uses the strict Pydantic contract and recomputes identity. `sync.py` stages to a sibling temp directory, runs the policy check, compares the source tree OID against the set of candidate/adopted scorecard OIDs, applies an exact path replacement, fsyncs, and atomically swaps. It never uses `copytree(..., dirs_exist_ok=True)` onto a live destination.

- [ ] **Step 5: Add CLI commands.** Add:

  ```text
  der harness status
  der harness policy-check PATH
  der harness sync --from daily|managed --daily-path PATH [--force --reason TEXT]
  ```

  `policy-check` runs `validate_evolvable_harness` and prints `request_shaping_keys=<n> executable_keys=<n>` (the counts of violations found; both must be `0` for success), exiting with `PolicyViolationError`'s code otherwise — Step 1 already relies on it.

  `--force` requires a nonempty reason and an interactive typed acknowledgment `UNEVALUATED TREE`; in noninteractive mode it additionally requires `DER_OWNER_ACK_UNEVALUATED_TREE=1`.

- [ ] **Step 6: Test and commit.** Run `uv run pytest tests/harness/test_live_state.py tests/harness/test_sync.py tests/harness/test_policy.py -q && uv run pytest -q`. Then:

  ```bash
  git add harness research/der/harness/live_state.py research/der/harness/sync.py \
    research/der/cli.py tests/harness/test_live_state.py tests/harness/test_sync.py
  git commit -m "feat: establish the managed Qwen harness and guarded sync"
  ```

### Task 24: Derive the baseline and enforce comparability/`CONFOUNDED`

**Files:**
- Create: `research/der/experiments/baseline.py`
- Create: `research/der/experiments/comparability.py`
- Test: `tests/experiments/test_baseline.py`
- Test: `tests/experiments/test_comparability.py`
- Test: `tests/fixtures/experiments/adopted-old.json`
- Test: `tests/fixtures/experiments/adopted-current.json`
- Test: `tests/fixtures/experiments/rejected-newer.json`

**Interfaces:**
- Consumes: immutable scorecards and the committed harness tree OID from `git(repo_root, "rev-parse", "main:harness")` (Task 3's checked Git helper).
- Produces: `resolve_current_baseline(scorecards: Iterable[Path], *, main_harness_tree_oid: str) -> Baseline`; `compare_results(baseline: EvalResult, candidate: EvalResult) -> Comparability`.

- [ ] **Step 1: Write the baseline test matrix.** Assert the resolver selects the most recent scorecard whose lifecycle decision is `adopted` and whose candidate tree OID equals `main:harness`; ignores a newer rejected scorecard; refuses duplicate adopted timestamps; raises `NoEvaluatedBaselineError` when no adopted scorecard matches; and does not read or create `baseline.json`.

- [ ] **Step 2: Implement the derived resolver.** Read each supplied path directly, validate the scorecard schema, verify its digest against the lifecycle attachment, filter adopted/matching candidates, sort by `(finished_at, experiment_id, run_id)`, and reject same-time ambiguity. Return an immutable `Baseline(scorecard_path, experiment_id, run_id, identity, suite_version, k)`.

- [ ] **Step 3: Write comparability tests with all branches.** Same suite version and same `k` plus same runtime-manifest digest yields `comparable`; different suite or `k` yields `incomparable` with explicit reasons; same suite/`k` but different runtime-manifest digest yields `confounded`; a tree change alone is expected and does not confound.

- [ ] **Step 4: Implement the exact rule.** Create:

  ```python
  from dataclasses import dataclass
  from enum import StrEnum
  from research.der.contracts.eval import EvalResult

  class ComparabilityKind(StrEnum):
      COMPARABLE = "comparable"
      INCOMPARABLE = "incomparable"
      CONFOUNDED = "confounded"

  @dataclass(frozen=True)
  class Comparability:
      kind: ComparabilityKind
      reasons: tuple[str, ...]

  def compare_results(baseline: EvalResult, candidate: EvalResult) -> Comparability:
      reasons = []
      if baseline.suite_version != candidate.suite_version:
          reasons.append("suite_version differs")
      if baseline.k != candidate.k:
          reasons.append("k differs")
      if reasons:
          return Comparability(ComparabilityKind.INCOMPARABLE, tuple(reasons))
      if baseline.identity.runtime_manifest_digest != candidate.identity.runtime_manifest_digest:
          return Comparability(
              ComparabilityKind.CONFOUNDED,
              ("runtime_manifest_digest differs",),
          )
      return Comparability(ComparabilityKind.COMPARABLE, ())
  ```

- [ ] **Step 5: Add CLI visibility and test.** `der baseline show --json` prints the derived scorecard path and identity; `der experiment compare BASELINE CANDIDATE` exits `3` for incomparable, `4` for confounded, `0` for comparable. Run focused tests and `uv run pytest -q`.

- [ ] **Step 6: Commit.** Run:

  ```bash
  git add research/der/experiments/baseline.py research/der/experiments/comparability.py \
    research/der/cli.py tests/experiments tests/fixtures/experiments
  git commit -m "feat: derive baselines and enforce result comparability"
  ```

### Task 25: Implement executable-first adoption and execute the hand-authored A/B gate

**Files:**
- Create: `research/der/harness/diff.py`
- Create: `research/der/experiments/adopt.py`
- Modify: `research/der/cli.py`
- Create: `tests/harness/test_diff.py`
- Create: `tests/experiments/test_adopt.py`
- Create: `tests/golden/adoption-diffs/executable-first.md`
- Create: `experiments/EXP-0005-hand-authored-ab.md`
- Create: `research/runs/EXP-0005-hand-authored-ab/`

**Interfaces:**
- Consumes: derived baseline, confirmation scorecard, harness policy, exact Git tree identities, finalizer.
- Produces: `render_harness_diff(base: Path, candidate: Path) -> str`; `adopt_experiment(request: AdoptRequest) -> AdoptResult`; CLI `der experiment adopt ... [--rebase-and-reeval]`.

- [ ] **Step 1: Write the executable-first golden test.** Fixture changes include an MCP command, hook, ordinary instruction, and skill text. Assert output's first heading is exactly `# EXECUTES ON YOUR MACHINE`; executable-key rows include old/new JSON and source paths; request-shaping changes are labeled `FORBIDDEN`; ordinary content follows under `# MANAGED HARNESS CONTENT`. Byte-compare against the golden file.

- [ ] **Step 2: Implement semantic diffing.** Parse both settings files, recursively enumerate changed JSON pointers, classify with the same policy constants used by staging, diff text files with unified context, and sort executable changes before all others. Symlink/type changes are executable-risk rows. Never suppress an unchanged-but-overlay-winning owner key from the rendered effective-settings section.

- [ ] **Step 3: Write adoption gate tests.** Cover: baseline tree still equals `main:harness`; moved main refuses and prints `--rebase-and-reeval`; candidate confirmation result must be comparable and meet its preregistered decision; any forbidden request-shaping key refuses; executable changes require exact typed acknowledgment; exact replacement changes only `harness/`; finalizer failure restores the old harness; unattended environment always refuses.

- [ ] **Step 4: Implement adoption as a reversible transaction.** `adopt_experiment` acquires the global lock, resolves baseline afresh, verifies candidate scorecard/lifecycle/digests, renders diff, checks acknowledgments, writes candidate harness to a temp Git worktree, computes expected tree OID, exact-replaces `harness/`, verifies resulting OID, calls the finalizer, and commits the lifecycle/README/harness changes. On any pre-commit error, restore the old tree and leave an explicit recovery record. Never mutate a scorecard.

- [ ] **Step 5: Add `--rebase-and-reeval` behavior without silently adopting.** On a moved baseline, this option creates a new preregistered experiment whose candidate content is replayed atop current `main:harness`, runs development and confirmation again, and exits after finalization with `new_experiment_id=...`; the owner must invoke adopt again.

- [ ] **Step 6: Create the hand-authored candidate.** Copy `harness/` to `var/candidates/EXP-0005/harness`, make one small documented instruction/skill change intended to improve a specific V7-audited failure mode, and preregister one primary metric, minimum effect, guardrails, falsifier, suite version, `k`, and RunBudget before any run. Do not change model/endpoint/keys/sampling/hook/MCP fields.

- [ ] **Step 7: Run development then confirmation.** Execute `der eval run` on the frozen development set. Only if the preregistered development continuation rule is met, run the disjoint confirmation set. Finalize both exact paths into one experiment scorecard whose decision uses confirmation only. Expected states are honestly one of `adopted`, `rejected`, `inconclusive`, or `invalid`; do not force adoption to pass this milestone.

- [ ] **Step 8: Exercise the owner adoption command.** For a qualifying result run:

  ```bash
  uv run der experiment adopt EXP-0005-hand-authored-ab \
    --candidate var/candidates/EXP-0005/harness \
    --acknowledge-tree "$(git rev-parse main:harness)"
  ```

  For a nonqualifying result run `uv run der experiment adopt ...` and expect exit `5` with the exact failed contract rows. In either case, verify the lifecycle terminal state, scorecard immutability, and generated README block.

- [ ] **Step 9: Run milestone checks.** Run `uv run pytest tests/harness/test_diff.py tests/experiments/test_adopt.py -q && uv run pytest -q`; then verify `find . -name baseline.json -o -name DASHBOARD.md` emits nothing and `git diff --check` passes.

- [ ] **Step 10: Commit.** Run:

  ```bash
  git add research/der/harness/diff.py research/der/experiments/adopt.py research/der/cli.py \
    tests/harness/test_diff.py tests/experiments/test_adopt.py tests/golden/adoption-diffs \
    experiments/EXP-0005-hand-authored-ab.md research/runs/EXP-0005-hand-authored-ab README.md harness
  git commit -m "feat: gate adoption and prove a hand-authored A/B experiment"
  ```

# Phase 6 — Milestone 6: calibrate, freeze, and baseline suite v1

Milestone exit: suite-v1 membership is frozen and pairwise disjoint; confirmation members remain aggregate-only and absent from optimizer/critic evidence; exclusions have recorded reasons; and a full-suite baseline is evaluated and finalized at the frozen DeepSWE revision and chosen `k`.

### Task 26: Calibrate and freeze suite v1 with CI-enforced disjointness

**Files:**
- Create: `research/suites/candidates-v1.toml`
- Create: `research/suites/suite-v1.toml`
- Create: `research/suites/exclusions-v1.md`
- Modify: `research/der/suites/manifest.py` (created in Task 4; add the strictness rules below)
- Modify: `research/der/suites/disjoint.py` (created in Task 4; add the leak-scan rules below)
- Create: `research/der/suites/calibrate.py`
- Modify: `tests/suites/test_manifest.py` (extend Task 4's tests)
- Test: `tests/suites/test_disjoint.py`
- Test: `tests/suites/test_calibrate.py`

**Interfaces:**
- Consumes: V7 audited candidate inventory, calibration scorecards, frozen DeepSWE revision.
- Produces: `load_suite(path: Path) -> SuiteManifest`; `assert_pairwise_disjoint(manifest) -> None`; `select_suite(observations, policy) -> CalibrationReport`.

- [ ] **Step 1: Write deterministic selection tests.** Use a 40-task fixture with fixed pass rates, invalid rates, wall time, cluster label, and verifier-audit status. Assert selection is deterministic; development is approximately 16, confirmation approximately 8, spine 4–6; every class is nonempty and pairwise disjoint; confirmation is not selected by difficulty alone; excluded tasks carry one of `broken_verifier`, `unstable_infra`, `duplicate_cluster`, `too_easy`, `too_hard`, or `capacity_outlier`.

- [ ] **Step 2: Implement strict TOML loading and disjointness.** Reject unknown fields, duplicate IDs, revision mismatch, absent task checksum, overlap across any pair, confirmation IDs in `optimizer_visible_task_ids`, and confirmation IDs in `critic_visible_task_ids` (both are function arguments to the leak check, not manifest fields). Frozen manifests extend Task 2's `SuiteManifest` under its existing field names (`version`, `deep_swe_commit`, `reporting_k`, the three member classes, `frozen`) with two new required fields, `created_at` and `selection_policy_digest`; regenerate `research/schemas/suite.schema.json` and update the Task 4 suite fixtures in the same commit.

- [ ] **Step 3: Implement calibration selection.** `select_suite` filters failed verifier audits and excessive invalidity, stratifies by task cluster and observed difficulty, chooses deterministic representatives using task ID as final tie-breaker, and emits every inclusion/exclusion reason. It does not use confirmation task content or outcomes after freeze.

- [ ] **Step 4: Generate candidate observations through preregistered calibration runs.** Run each V7 candidate at the recorded V10 concurrency with `k=1` under explicit calibration records and budgets. Feed only normalized scorecards to `der suite calibrate`; never parse Pier directories directly.

- [ ] **Step 5: Freeze and verify.** Run:

  ```bash
  uv run der suite calibrate --candidates research/suites/candidates-v1.toml \
    --scorecards research/runs/calibration --output research/suites/suite-v1.toml \
    --exclusions research/suites/exclusions-v1.md
  uv run der suite verify research/suites/suite-v1.toml
  ```

  Expected: `development=14..18 confirmation=6..10 spine=4..6 overlap=0`; exact counts are recorded, not adjusted to make later results look better.

- [ ] **Step 6: Add CI preflight.** Extend `.github/workflows/check.yml` and `scripts/check.py` to run schema regeneration, suite disjointness, confirmation-leak scan, policy scan, generated README comparison, and all unit tests. Run `uv run python scripts/check.py`; expected `all checks passed`.

- [ ] **Step 7: Commit.** Run:

  ```bash
  git add research/suites research/der/suites tests/suites .github/workflows/check.yml scripts/check.py
  git commit -m "feat: calibrate and freeze disjoint DeepSWE suite v1"
  ```

### Task 27: Establish the immutable full-suite baseline

**Files:**
- Create: `experiments/EXP-0006-suite-v1-baseline.md`
- Create: `research/runs/EXP-0006-suite-v1-baseline/`
- Modify: `README.md`
- Test: live full-suite acceptance commands

**Interfaces:**
- Consumes: frozen suite-v1, V10 concurrency, managed harness, finalizer.
- Produces: the first adopted suite-v1 baseline scorecard matching `main:harness`.

- [ ] **Step 1: Preregister the baseline.** Create the record with suite version `v1`, the approved `k` recorded in suite-v1, primary metric `confirmation_macro_pass_at_1`, minimum effect `0`, invalid-fraction and cost guardrails, falsifier `any identity/model/result-path mismatch`, and a RunBudget computed as task count × `k` plus zero retries.

- [ ] **Step 2: Run development, confirmation, and spine through `EvalRunner`.** Use three explicit `EvalSpec` files and exact result files under one run directory. Confirmation output may enter the scorecard only as aggregate counts/rates; no task ID, prompt, patch, trajectory, or per-task reward appears in README, ADB inputs, or critic bundles. Spine is reporting-only and cannot alter decision.

- [ ] **Step 3: Record the initial adopted baseline.** The one-command finalizer arrives in Task 28 (Milestone 7 per the approved build order); here compose the proven primitives exactly as Task 18 Step 5 did — `write_scorecard_once`, `attach_scorecard`, then `transition_record(..., target=ExperimentStatus.ADOPTED, now=..., terminal_reason=..., adopted_at=...)`. Adopting with no predecessor is permitted only when the Task 24 resolver raises `NoEvaluatedBaselineError` and the candidate tree OID equals `git rev-parse main:harness`; assert both in the composing script before the transition and record this exceptional bootstrap rule in the record body. (When Task 28 lands, its finalizer re-verifies this scorecard unchanged; the README point appears when Task 29's generator lands.)

- [ ] **Step 4: Verify exact evidence.** Run:

  ```bash
  uv run python - <<'PY'
  import glob
  from pathlib import Path
  from research.der.contracts.scorecard import Scorecard
  from research.der.experiments.baseline import resolve_current_baseline
  from research.der.util.git import git
  paths = [Path(p) for p in glob.glob("research/runs/EXP-0006-suite-v1-baseline/*/scorecard.json")]
  assert paths, "no baseline scorecards found"
  for path in paths:
      Scorecard.model_validate_json(path.read_text())
  main_tree = git(Path.cwd(), "rev-parse", "main:harness")
  baseline = resolve_current_baseline(
      (Path(p) for p in glob.glob("research/runs/**/scorecard.json", recursive=True)),
      main_harness_tree_oid=main_tree,
  )
  assert baseline.experiment_id == "EXP-0006-suite-v1-baseline", baseline
  print("baseline", baseline.experiment_id, main_tree)
  PY
  uv run der baseline show --json | uv run python -m json.tool
  uv run python scripts/check.py
  uv run pytest -q
  ```

  Expected: baseline experiment `EXP-0006-suite-v1-baseline`, tree OID equals `git rev-parse main:harness`, and `scripts/check.py` (which includes Task 26's confirmation-leak scan) reports `all checks passed`.

- [ ] **Step 5: Commit.** Run:

  ```bash
  git add experiments/EXP-0006-suite-v1-baseline.md research/runs/EXP-0006-suite-v1-baseline README.md
  git commit -m "research: establish the frozen suite-v1 baseline"
  ```

# Phase 7 — Milestone 7: promotion accounting, atomic finalization, and the single README publication block

Milestone exit: promotion decisions are calculated from preregistered contracts and confirmation results; one idempotent finalizer owns scorecard/lifecycle/README writes; and README contains exactly one generated block with the approved chart, annotations, complete ledger, and resource strips.

### Task 28: Implement experiment metrics, promotion decisions, and the one finalizer transaction

**Files:**
- Create: `research/der/experiments/metrics.py`
- Modify: `research/der/evaluation/artifact_manifest.py` (created in Task 14; extend with the role/scrub rules below)
- Create: `research/der/evaluation/finalizer.py`
- Create: `research/der/ops/secret_scrub.py`
- Modify: `research/der/cli.py`
- Test: `tests/experiments/test_metrics.py`
- Modify: `tests/evaluation/test_artifact_manifest.py` (extend Task 14's tests)
- Test: `tests/evaluation/test_finalizer.py`
- Test: `tests/ops/test_secret_scrub.py`

**Interfaces:**
- Consumes: preregistration contract, comparable confirmation `EvalResult`s, candidate artifact tree, lifecycle record, README renderer.
- Produces: `evaluate_contract(contract, baseline, candidate) -> PromotionDecision`; `finalize_experiment(request: FinalizeRequest) -> FinalizeResult`; CLI `der experiment finalize`.

- [ ] **Step 1: Write metric tests with explicit numerators and denominators.** Cover per-task pass fractions, macro pass@1, valid/failed/invalid counts, invalid fraction, tokens, cost, wall time, task-cluster descriptive interval, positive/negative minimum effect, equality at threshold, guardrail failure, falsifier trigger, incomparable/confounded input, and zero valid attempts. Invalid attempts are never converted to reward zero or removed from denominators without an explicit reported denominator.

- [ ] **Step 2: Implement pure decision logic.** The function returns Task 2's `PromotionDecision` (verdict is the `PromotionVerdict` enum: `adopt`, `reject`, `inconclusive`, or `invalid`) carrying primary metric name; baseline/candidate values; observed effect; minimum effect; numerator/denominator for each; every guardrail value/limit/result; falsifier result; and comparability. It does not write files and does not use a universal significance test.

- [ ] **Step 3: Write secret-scrub tests.** Scan names and bytes for provider/OpenAI/GitHub token patterns, `.env` assignments, PEM private keys, Authorization headers, dotenvx decrypted output, proxy run tokens, and known owner secrets supplied as SHA-256 only. Assert ordinary scorecard digests and redacted `***` strings pass. Scanner output is canonical JSON with scanned path count and findings; a finding raises before artifact manifesting.

- [ ] **Step 4: Implement canonical artifact manifests.** Walk only explicitly supplied roots; reject symlinks, sockets, devices, paths outside the run root, and files not scrubbed in the same invocation. Record relative path, byte size, SHA-256, and semantic role. Sort by UTF-8 path bytes. The manifest itself is included by digest in the scorecard but cannot include itself recursively.

- [ ] **Step 5: Write finalizer crash-point tests.** Inject failures after: validation, scrub, scorecard staging, lifecycle staging, README staging, first replace, second replace, and third replace. Assert preexisting files are restored byte-for-byte unless the final commit marker exists. Reinvocation with the same request after a committed transaction returns the existing result; a different request for the same run raises immutability error. An incomplete/missing exact Pier path refuses before any write.

- [ ] **Step 6: Implement the finalizer transaction.** Under the global process lock: reload lifecycle and results; verify schema/digests/identity/model/policy/result path; evaluate the preregistered contract; scrub artifacts; create artifact manifest; render scorecard, lifecycle, and README entirely in a transaction directory; fsync; make reversible backups; install all three with `os.replace`; fsync parent directories; write `finalizer.commit.json` last with digests of all outputs; remove backups only after read-back verification. On failure before the marker, restore backups and retain `finalizer.recovery.json`.

- [ ] **Step 7: Enforce one writer.** Remove direct lifecycle/README writes from earlier CLI/adoption/AHE paths; they construct `FinalizeRequest` and call `finalize_experiment`. `scorecard_writer.py` remains the exclusive-create primitive used only by the finalizer and fixture discovery.

- [ ] **Step 8: Run tests and commit.** Run:

  ```bash
  uv run pytest tests/experiments/test_metrics.py tests/evaluation/test_artifact_manifest.py \
    tests/evaluation/test_finalizer.py tests/ops/test_secret_scrub.py -q
  uv run pytest -q
  ```

  Then:

  ```bash
  git add research/der/experiments/metrics.py research/der/evaluation/artifact_manifest.py \
    research/der/evaluation/finalizer.py research/der/ops/secret_scrub.py research/der/cli.py \
    tests/experiments/test_metrics.py tests/evaluation/test_artifact_manifest.py \
    tests/evaluation/test_finalizer.py tests/ops/test_secret_scrub.py
  git commit -m "feat: finalize experiments through one atomic evidence transaction"
  ```

### Task 29: Generate the sole README block and hero progression SVG

**Files:**
- Create: `research/der/publication/svg.py`
- Create: `research/der/publication/readme.py`
- Create: `tests/publication/test_svg.py`
- Create: `tests/publication/test_readme.py`
- Create: `tests/golden/readme/complete.md`
- Modify: `README.md`

**Interfaces:**
- Consumes: all lifecycle records and immutable scorecards; no mutable summary tables.
- Produces: `render_readme_block(records, scorecards) -> str`; `replace_generated_block(readme: str, block: str) -> str`.

- [ ] **Step 1: Write one-block marker tests.** The only markers are `<!-- DER:START -->` and `<!-- DER:END -->` (exactly the pair the locked file map assigns to `README.md`). Assert zero/multiple/unordered markers fail; replacement preserves all bytes outside the block; a second generation is byte-identical.

- [ ] **Step 2: Write the complete golden scenario.** Include adopted, rejected, inconclusive, and invalid records; two suite versions; one bridge evaluation; a confounded run; costs/tokens/wall time; and adoption annotations. Assert the ledger includes every experiment exactly once and confirmation task identities never appear.

- [ ] **Step 3: Implement accessible SVG without chart libraries.** Produce one inline SVG with title/description, adopted-baseline macro pass@1 only, x-axis experiment date, y-axis 0–1, per-adoption annotations, a visible series break at suite-version change, and dashed bridge points. Use deterministic dimensions/number formatting and no external assets. Do not generate a second chart.

- [ ] **Step 4: Implement the block renderer.** Required order: title/one-sentence interpretation; hero SVG; adopted-baseline annotations; full experiment ledger; resource strips. Ledger columns are experiment, terminal status, suite/k, primary effect and denominator, guardrails/falsifier, comparability, cost/tokens/wall time, and evidence link. No badge syntax, dashboard link, or hand-maintained rows.

- [ ] **Step 5: Add repository checks.** `scripts/check.py` regenerates into memory and rejects README drift; scans for `DASHBOARD.md`, a second DER block, badge image syntax in the block, and confirmation task IDs. Run `uv run pytest tests/publication -q && uv run python scripts/check.py`; expected pass.

- [ ] **Step 6: Regenerate from real records.** Run `uv run der publication render --readme README.md --records experiments --runs research/runs`. Expected output reports experiment count, adoption count, suite series count, and `changed=true|false`; a second run reports `changed=false`.

- [ ] **Step 7: Commit.** Run:

  ```bash
  git add research/der/publication tests/publication tests/golden/readme README.md scripts/check.py
  git commit -m "feat: publish the single generated research ledger"
  ```

# Phase 8 — Milestone 8: ADB/critic boundaries and unattended single-server operations

Milestone exit: ADB is an honestly labeled, license-cleared ephemeral view that excludes confirmation evidence; the premium critic is owner-triggered, local, read-only, schema-constrained, and outside the measured path; balance/cost watchdogs and systemd gates fail closed; one dedicated worktree and one lock govern unattended runs; and recovery/retention/notification procedures are executable from the runbook.

### Task 30: Discovery V8 — decide the bundled ADB redistribution and patch boundary from license evidence

**Files:**
- Create: `scripts/discover_v8_adb_license.py`
- Create: `research-plan/pins/v8-adb-license.md`
- Test: `tests/discovery/test_v8_adb_license.py`

**Interfaces:**
- Consumes: pinned AHE checkout, all license/notices files, bundled ADB `_source` paths and package metadata.
- Produces: passed pin with one allowed mode: `redistributable_patch`, `runtime_only_unmodified`, or STOP; downstream V6 consumes this exact mode.

- [ ] **Step 1: Write license-inventory parser tests.** Fixtures cover SPDX identifiers, LICENSE/NOTICE/COPYING files, `pyproject.toml`, package metadata, source headers, nested third-party notices, and absent/contradictory grants. Assert the parser never treats the repository's top-level MIT license as a grant for separately licensed bundled source.

- [ ] **Step 2: Implement an evidence-only probe.** Inventory every file under the bundled ADB `_source`, its Git provenance, license text/digest, package metadata, copyright headers, and references from AHE docs. Emit exact command transcripts for `git ls-tree`, `git log --follow`, `find`, `sha256sum`, and metadata inspection.

- [ ] **Step 3: Encode the decision rule.** `redistributable_patch` requires an explicit redistribution-and-modification grant applying to every copied source file. `runtime_only_unmodified` requires an explicit right to possess/run the bundled copy but no proven modification/redistribution right; in this mode der may generate input around the parser but never commit modified ADB source. Missing, ambiguous, or conflicting evidence writes `status: blocked`, exits `78`, and requires owner/legal review. The script does not infer a license from silence.

- [ ] **Step 4: Run discovery and stop on ambiguity.** Run:

  ```bash
  uv run python scripts/discover_v8_adb_license.py \
    --ahe-checkout /var/cache/der/sources/ahe \
    --pin research-plan/pins/v8-adb-license.md
  rc=$?; test "$rc" -eq 0 || test "$rc" -eq 78; exit "$rc"
  ```

  Expected pass output includes `allowed_mode`, file-by-file evidence, and exact source digests. Exit `78` blocks Tasks 31–34 only; existing evaluator operation remains usable.

- [ ] **Step 5: Verify and commit.** Run `uv run pytest tests/discovery/test_v8_adb_license.py -q && uv run der pins assert V8`. Then:

  ```bash
  git add scripts/discover_v8_adb_license.py research-plan/pins/v8-adb-license.md \
    tests/discovery/test_v8_adb_license.py
  git commit -m "research: pin the ADB license and redistribution boundary"
  ```

### Task 31: Discovery V6 and the confirmation-safe ephemeral ADB boundary view

**Files:**
- Create: `scripts/discover_v6_adb_parser.py`
- Create: `research-plan/pins/v6-adb-runtime-parser.md`
- Create: `research/der/integrations/adb.py`
- Modify: `research/PATCHES.md`
- Test: `tests/discovery/test_v6_adb_parser.py`
- Test: `tests/integrations/test_adb.py`
- Test: `tests/fixtures/adb/honest-trace.json`

**Interfaces:**
- Consumes: V8 allowed mode; canonical ATIF/structured results; development/spine evidence only.
- Produces: passed V6 parser pin; `build_adb_view(result: EvalResult, *, suite: SuiteManifest, destination: Path) -> AdbView`.

- [ ] **Step 1: Write boundary tests first.** Assert development and spine attempts produce ephemeral view files; confirmation attempts raise `ConfirmationEvidenceError`; provider/model fields remain `deepseek-v4-pro` and the proxy endpoint rather than an OpenAI label; source artifact digests are included; deleting the view leaves canonical evidence untouched.

- [ ] **Step 2: Build an honest synthetic trace.** Create `tests/fixtures/adb/honest-trace.json` from the ATIF contract with a DeepSeek provider label, proxy endpoint policy ID, tool calls, token usage, and no OpenAI credential/provider claim. Validate it against the strict local fixture schema.

- [ ] **Step 3: Implement the real parser discovery.** Based on V8 mode, either install the unmodified bundled runtime into an isolated `uv` environment or create a temporary licensed patch outside the repository. Locate the actual closed parser import path by importing candidate package modules and introspecting callable signatures; record package versions, module file paths, signature, command, stdout/stderr, and source digests.

- [ ] **Step 4: Exercise the parser.** Feed the honest trace to the actual parser, run the smallest ADB analysis command, and require successful output that preserves provider/model attribution. If it rejects honest non-OpenAI metadata, requires false labels, needs confirmation evidence, or cannot run from the licensed mode, write `status: blocked`, exit `78`, and stop; do not shim subscription/API identities.

- [ ] **Step 5: Record V6.** Run:

  ```bash
  uv run python scripts/discover_v6_adb_parser.py \
    --license-pin research-plan/pins/v8-adb-license.md \
    --ahe-source /var/cache/der/sources/ahe \
    --trace tests/fixtures/adb/honest-trace.json \
    --pin research-plan/pins/v6-adb-runtime-parser.md
  rc=$?; test "$rc" -eq 0 || test "$rc" -eq 78; exit "$rc"
  ```

- [ ] **Step 6: Implement the view generator from the pin.** `build_adb_view` selects only development/spine attempts; verifies every input digest; emits parser-required files under a new temp directory; writes `BOUNDARY.json` stating `ephemeral=true`, canonical source paths/digests, actual provider/model, parser version/path, and exclusion count; invokes no network; and returns a cleanup-capable context object.

- [ ] **Step 7: Record any licensed parser adaptation.** When V8 says `redistributable_patch`, add one `ADB-001` row to `PATCHES.md` with exact source/diff/license rationale. Under `runtime_only_unmodified`, add a disclosure row stating no parser source was changed and only der input generation was added.

- [ ] **Step 8: Test and commit.** Run `uv run pytest tests/discovery/test_v6_adb_parser.py tests/integrations/test_adb.py -q && uv run pytest -q`. Then:

  ```bash
  git add scripts/discover_v6_adb_parser.py research-plan/pins/v6-adb-runtime-parser.md \
    research/der/integrations/adb.py research/PATCHES.md tests/discovery/test_v6_adb_parser.py \
    tests/integrations/test_adb.py tests/fixtures/adb/honest-trace.json
  git commit -m "feat: add the honest confirmation-safe ADB boundary"
  ```

### Task 32: Add the owner-triggered local GPT-5.6 Sol critic

**Files:**
- Create: `research/der/integrations/critic.py`
- Modify: `research/templates/experiment.md` (created in Task 4; add the critic-provenance section)
- Modify: `research/der/cli.py`
- Test: `tests/integrations/test_critic.py`
- Test: `tests/fixtures/critic/codex-events.jsonl`

**Interfaces:**
- Consumes: development/spine scorecards, lifecycle ledger, ADB aggregate findings, `research/schemas/critic-proposal.schema.json`.
- Produces: `run_critic(request: CriticRequest) -> CriticResult`; CLI `der critic propose`.

- [ ] **Step 1: Write evidence-bundle tests.** Assert the bundle contains approved architecture, managed harness, development/spine aggregate evidence, rejected/inconclusive ledger rows, resource data, and ADB findings; excludes confirmation task IDs/prompts/patches/trajectories and all secrets; is content-addressed and read-only.

- [ ] **Step 2: Write command-construction tests.** Assert the exact argv is:

  ```python
  (
      "codex", "exec",
      "--ephemeral",
      "--sandbox", "read-only",
      "--ask-for-approval", "never",
      "--ignore-user-config",
      "--ignore-rules",
      "--model", "gpt-5.6",
      "--output-schema", str(schema_path),
      "--output-last-message", str(output_path),
      prompt,
  )
  ```

  Assert no API endpoint/key flag and no OpenAI-compatible shim. These flags are verified against OpenAI's current `codex exec` non-interactive documentation at execution time; `codex --version` and help digest are recorded as provenance.

- [ ] **Step 3: Implement schema-constrained proposals.** The schema requires hypothesis, one primary metric, minimum effect, guardrails, falsifier, suite version, `k`, RunBudget, candidate file changes, and evidence citations by digest; rejects direct changes to request-shaping/executable keys. Output creates a new lifecycle record with status `proposed`, never stages/runs/adopts it.

- [ ] **Step 4: Enforce owner-only local execution.** Require an interactive TTY, `DER_OWNER_TRIGGERED=1`, clean Git status, no systemd parent, and a successful `codex login status`. Invoke via `subprocess.run` with a minimal environment that removes provider keys. Save prompt digest, bundle digest, CLI version/help digest, exact argv with paths, start/end time, exit status, event JSONL digest, final output digest, model `gpt-5.6`, sandbox, and auth mode `subscription-login`.

- [ ] **Step 5: Test with a fake executable and one real owner smoke.** Unit tests cover schema failure, leaked confirmation ID, attempted write, non-TTY, unattended parent, and valid proposal. Owner smoke:

  ```bash
  DER_OWNER_TRIGGERED=1 uv run der critic propose \
    --evidence development-and-spine \
    --output-record experiments/EXP-0007-critic-proposal.md
  ```

  Expected: one proposed record, no run/scorecard, zero Git changes outside record/provenance, and provenance says read-only. Never run this from CI/systemd.

- [ ] **Step 6: Commit.** Run:

  ```bash
  git add research/der/integrations/critic.py research/templates/experiment.md research/der/cli.py \
    tests/integrations/test_critic.py tests/fixtures/critic/codex-events.jsonl \
    experiments/EXP-0007-critic-proposal.md
  git commit -m "feat: add an owner-only schema-constrained Codex critic"
  ```

### Task 33: Discovery V9 and the balance/cost watchdog

**Files:**
- Create: `scripts/discover_v9_balance.py`
- Create: `research-plan/pins/v9-deepseek-balance.md`
- Create: `research/der/ops/watchdog.py`
- Test: `tests/discovery/test_v9_balance.py`
- Test: `tests/ops/test_watchdog.py`

**Interfaces:**
- Consumes: official DeepSeek `/user/balance` contract, owner credential through dotenvx, proxy budget ledger/observations.
- Produces: passed account-specific V9 pin; `run_watchdog(config: WatchdogConfig) -> WatchdogDecision`; `COST_CEILING_REACHED` flag.

- [ ] **Step 1: Write balance-response tests from the official field contract.** Validate `is_available` and each `balance_infos` row's `currency`, `total_balance`, `granted_balance`, and `topped_up_balance`; reject missing, duplicate-currency, negative, non-decimal, HTML, and auth-error responses.

- [ ] **Step 2: Implement account discovery without leaking the key.** Make one HTTPS request to the official endpoint through a minimal process environment, record URL host/path, method, status, response headers excluding auth/cookies, redacted body shape, selected currency and JSON pointers, UTC time, and command/tool versions. Store no balance credential or plaintext authorization header.

- [ ] **Step 3: Run V9 and STOP on contradiction.** Run:

  ```bash
  dotenvx run -f "$DER_DOTENVX_FILE" -- \
    uv run python scripts/discover_v9_balance.py \
      --endpoint https://api.deepseek.com/user/balance \
      --currency USD \
      --pin research-plan/pins/v9-deepseek-balance.md
  rc=$?; test "$rc" -eq 0 || test "$rc" -eq 78; exit "$rc"
  ```

  Authentication failure, schema mismatch, absent USD row, or endpoint behavior inconsistent with the official contract writes `status: blocked`, exits `78`, and stops unattended deployment. Do not replace balance with estimated cost alone.

- [ ] **Step 4: Write watchdog decision tests.** Cover provider balance below reserve, monthly observed/ledger spend at ceiling, missing/stale proxy observations, inconsistent cost ledgers, healthy state, already-present flag, and cleared flag requiring owner action. Any unknown/inconsistent evidence stops evolution.

- [ ] **Step 5: Implement watchdog.** Read V9 pointers, query balance, sum current-month reconciled proxy costs, verify all run ledgers, inspect free disk and cache pins, and atomically create `var/state/COST_CEILING_REACHED` containing reason, observed values, thresholds, UTC time, and evidence digests. It may stop `der-evolve.service`; it never deletes/rewrites evidence or automatically clears the flag.

- [ ] **Step 6: Test and commit.** Run `uv run pytest tests/discovery/test_v9_balance.py tests/ops/test_watchdog.py -q && uv run pytest -q`. Then:

  ```bash
  git add scripts/discover_v9_balance.py research-plan/pins/v9-deepseek-balance.md \
    research/der/ops/watchdog.py tests/discovery/test_v9_balance.py tests/ops/test_watchdog.py
  git commit -m "feat: pin provider balance and fail closed on cost ceilings"
  ```

### Task 34: Install fail-closed systemd operations, retention, notifications, smoke, CI, and recovery drills

**Files:**
- Create: `research/der/ops/janitor.py`
- Create: `research/der/ops/notify.py`
- Create: `ops/systemd/der-pinning-proxy.service`
- Create: `ops/systemd/der-evolve.service`
- Create: `ops/systemd/der-watchdog.service`
- Create: `ops/systemd/der-watchdog.timer`
- Create: `ops/systemd/der-notify@.service`
- Create: `ops/systemd/der.env.example`
- Create: `ops/install-systemd.sh`
- Create: `ops/runbook.md`
- Modify: `research/der/cli.py` (adds `der lock probe`, `der smoke terminal-bench`, `der doctor --require-unattended`)
- Modify: `.github/workflows/check.yml`
- Modify: `scripts/check.py`
- Test: `tests/ops/test_janitor.py`
- Test: `tests/ops/test_notify.py`
- Test: `tests/ops/test_systemd_units.py`

**Interfaces:**
- Consumes: proxy CLI, patched AHE, doctor, watchdog, global lock, dedicated worktree, dotenvx file.
- Produces: installed single-server services and an owner-verifiable recovery procedure.

- [ ] **Step 1: Write retention tests.** Janitor may remove expired container layers, staging directories, ephemeral ADB views, and raw duplicate logs after verifying their digest appears in a scorecard manifest and retention age passed. It must never remove lifecycle records, scorecards, finalizer commit/recovery files, pin files, suite manifests, README, proxy cost ledgers, or the only copy of a referenced artifact.

- [ ] **Step 2: Write notification tests.** Local notifier receives event, experiment/run IDs, service, reason, observed cost/balance, evidence path, and UTC time; appends canonical JSONL with fsync and optionally executes an owner configured local command with arguments, never a shell. Failure to notify is logged but does not clear a ceiling or mark a run successful.

- [ ] **Step 3: Write exact unit assertions.** Parse units with `systemd-analyze verify`; assert `der-evolve.service` has `ExecStartPre` checks for absence of `COST_CEILING_REACHED`, passed doctor, dedicated worktree, and lock; `Environment` contains no secret; credentials enter only through `dotenvx run -f`; `Restart=on-failure` is bounded; `KillMode=mixed`; timeouts are finite; proxy runs separately; watchdog timer is enabled; `OnFailure=der-notify@%n.service` exists.

- [ ] **Step 4: Create `der-pinning-proxy.service`.** Run as a dedicated unprivileged user, bind the V2-pinned host address/port, use dotenvx only around the proxy process, set `NoNewPrivileges=true`, `PrivateTmp=true`, `ProtectSystem=strict`, explicit writable state paths, `UMask=0077`, finite stop timeout, and health check. Do not expose provider keys in an Environment line or command argument.

- [ ] **Step 5: Create `der-evolve.service`.** `WorkingDirectory` is the dedicated autonomous worktree; `ExecStartPre` invokes `test ! -e .../COST_CEILING_REACHED`, `der doctor --require-unattended`, and `der lock probe`; `ExecStart` uses `dotenvx run` only for proxy/balance owner processes and starts patched `research/evolve.py` with `max_iterations=10`, finite timeouts, best-of-n/explore off. The service environment sets `DER_UNATTENDED=1`; adoption/sync code treats this as an unconditional write refusal for `harness/`.

- [ ] **Step 6: Create watchdog/timer/notify units and installer.** Timer uses `OnBootSec=5m`, `OnUnitActiveSec=15m`, `Persistent=true`. Installer copies only after `systemd-analyze verify`, requires root, creates state directories with exact ownership/mode, reloads daemon, enables proxy/watchdog timer, and leaves evolve disabled until owner starts it.

- [ ] **Step 7: Add terminal-bench smoke as explicitly unscored.** `der smoke terminal-bench` runs one cached task through Qwen/proxy, stores logs under `research/runs/smoke/`, and writes no `EvalResult`, scorecard, lifecycle promotion decision, or README datapoint. Tests assert the command cannot accept `--score` or a confirmation suite.

- [ ] **Step 8: Write the runbook as copy-paste procedures.** Include exact commands for source/bootstrap pins, creating the dedicated worktree, dotenvx setup without plaintext commit, archive/image cache, systemd install/start/stop/status, owner evaluation, AHE start/resume, cost-ceiling diagnosis/owner-only clear, adoption and rebase-and-reeval, guarded daily sync, terminal-bench smoke, secret scrub, janitor dry-run/apply, finalizer recovery, corrupted/missing exact-result refusal, proxy outage, provider 4xx/5xx, disk pressure, and restoring from immutable scorecards. Every procedure has expected observable output and a STOP condition.

- [ ] **Step 9: Run recovery drills on the real server.** Perform: kill proxy during a smoke run → invalid/network; kill Pier → no finalizer write; kill finalizer before marker → exact rollback then successful replay; occupy lock → second evaluator refuses; create ceiling flag → evolve `ExecStartPre` refuses; make `main:harness` unevaluated → sync refuses; move baseline tree → adopt refuses; inject fake secret → scrub refuses. Paste commands and sanitized outputs into `ops/runbook.md` under `Verified recovery drills — 2026-07-21`.

- [ ] **Step 10: Run final verification.** Run:

  ```bash
  uv run pytest -q
  uv run python scripts/check.py
  systemd-analyze verify ops/systemd/*.service ops/systemd/*.timer
  uv run der doctor --require-unattended --json | uv run python -m json.tool
  uv run der publication render --check --readme README.md --records experiments --runs research/runs
  git diff --check
  ```

  Expected: all tests/checks pass; doctor reports every required pin including V1–V10 passed; README is unchanged; units verify.

- [ ] **Step 11: Commit.** Run:

  ```bash
  git add research/der/ops/janitor.py research/der/ops/notify.py research/der/cli.py ops \
    .github/workflows/check.yml scripts/check.py tests/ops README.md
  git commit -m "ops: deploy the guarded single-server research loop"
  ```
