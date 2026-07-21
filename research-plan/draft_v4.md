# der auto-research loop — Stage 1 architecture (v4 — post-external-review restructure)

Status: integrates the external GPT 5.6 Sol Pro review (round 4, verdict RESTRUCTURE — `reviews/round4_solpro.md`) into the round-1–3 converged architecture. All five of the reviewer's approval conditions are adopted. Section 9 records the full adopt/retain/reject disposition. Stage 2 (implementation plan) remains blocked on owner approval.

## 0. Purpose

Stand up an automated research loop around the der harness (Qwen Code base) by adapting the official AHE codebase, so that:

- the owner's **own hypotheses** run through an eval + scorecard + verdict pipeline (A/B against baseline) from day one,
- the harness can then be **evolved autonomously** (AHE evaluate → analyze → improve, unattended, resumable, budget-capped),
- every run produces an **immutable scorecard** feeding one generated public README block (progression chart + experiment ledger),
- **DeepSeek v4 pro is the pinned rollout model, always** — enforced at the network boundary,
- experiments measure what the vision actually cares about: **success, speed, token use, and cost** — each experiment declaring its own contract.

## 1. The architecture is four concepts

```
                        ┌────────────────────────┐
  owner CLI ───────────>│                        │
  (der experiment run)  │   Shared EvalRunner    │────> Pier (pinned 0.3.x) / local Docker
                        │  run(EvalSpec)         │            │
  AHE optimizer ───────>│      -> EvalResult     │            v
  (evolve.py, adapted)  └──────────┬─────────────┘      DerQwenAgent (--agent-import-path)
                                   │                     · staged runtime-shaped harness/
                        canonical run result             · isolated rollout HOME
                        (Pier ATIF + trial result        · Qwen from pinned offline archive
                         + verifier artifacts            · egress only to model-pinning proxy
                         + der normalized record)              │
                                   │                           v
                                   v                    host pinning proxy ──> DeepSeek v4 pro
                     experiment lifecycle record        (key injection, model hard-pin,
                     (experiments/EXP-####-slug.md,      RunBudget enforcement)
                      preregistered → verdict)
                                   │
                                   v
                        one generated README block
                        (hero progression chart + ledger + resource strips)
```

1. **Shared EvalRunner** — one semantic adapter over a pinned Pier: both doors (owner CLI, AHE optimizer) call `EvalRunner.run(EvalSpec) → EvalResult` synchronously; one finalizer writes the scorecard and updates the lifecycle record atomically after a complete terminal result. Fail closed: explicit experiment ID + evaluator job ID; no recovery by directory recency.
2. **DerQwenAgent + pinning proxy** — the agent-under-test: runtime-shaped `harness/` staged by transparent copy/overlay into the task workspace, Qwen Code from a pinned official standalone archive (local read-only cache), isolated rollout HOME, no provider key in containers, model + budget pinned at the proxy.
3. **Experiment lifecycle record** — one markdown file per experiment with machine-readable front matter: preregistered contract (hypothesis, primary metric, minimum effect, guardrails, falsifier, suite version, attempt budget) → execution references → generated result block → verdict. This is simultaneously the hypothesis queue, the preregistration proof (git history), and the notebook.
4. **Generated publication** — README hero chart (adopted-baseline macro pass@1 over time, annotated with adopted experiments, segmented at suite-version changes), a compact ledger of every experiment (including rejected/inconclusive/invalid), and small resource strips (tokens, cost, wall-clock). All generated from scorecards; nothing hand-maintained.

## 2. Load-bearing facts (updated)

**Carried from rounds 1–3 (source-verified, still true):**
- AHE's loop logic is agent-layout-agnostic (`init_workspace` = bare `copytree`; component semantics live in evolve-agent prompts, which we retarget). Evolve/explore agents are NexAU-based on the **host** — that dependency stays.
- AHE's evolve.py currently: builds `harbor run` argvs, parses `verifier/reward.txt`, classifies missing-reward trials as `exception`, recovers after timeout by **selecting the latest existing job dir** (now removed — D3), has iteration-granular resume, no cost accounting, Feishu-only notify, `max_iterations: 100` and unlimited timeouts by default.
- ADB is partially open-source (bundled `agent_debugger_core`); its trace parser recognizes LLM spans by name keywords ("openai"/"gpt"/…) and NexAU span-tree shape. Which parser copy executes in `adb ask` (the open vendored `trace_converter.py` vs. the closed core) determines whether we patch honestly or encode at the view boundary — verification item V6.
- Qwen Code: headless `-p`, project config (QWEN.md, `.qwen/settings.json`, skills), session JSONL with per-call `usageMetadata`, OTLP telemetry, multi-protocol OpenAI-compatible providers, nightly cadence (pin everything).

**New (from DeepSWE/Pier/Tura sources + the round-4 review; items marked ▲ are verified against public docs, ▽ must be re-verified live at build step 1):**
- ▲ DeepSWE v1.1: 113 contamination-free long-horizon tasks, 91 repos, 5 languages, Harbor task format, hand-written behavioral verifiers; verifier-vs-independent-judge disagreement ~1.4% (vs 32.4% SWE-bench Pro) — a comparison, not a measured error rate, but strong. Public repo clone + local path is the current quickstart (the gated HF dataset is not a blocker). Scope skews long-horizon/multi-file; README must describe that honestly.
- ▲ DeepSWE v1.1 grading requires **Pier ≥ 0.3.0**: separate verifier environment, committed agent work, `pre_artifacts.sh` patch extraction, pristine-repository grading.
- ▲ Pier: fork of Harbor for sandboxed CLI-agent evals; per-agent **network allowlists**; custom agents via `--agent-import-path`; local tasks via `-p/--path`; task inclusion `-i/--include-task-name`; `--n-concurrent` and attempt-count controls — all five flags verified in Pier source (`src/pier/cli/jobs.py`), along with `reward.json`, `ctrf.json`, and **ATIF v1.7** trajectory output. **Pin `datacurve-pier==0.3.0`** (the only 0.3.x release on PyPI). Documented cloud path is **Modal** (not E2B). ▽ residual: exact per-trial directory layout pinned at build step 1.
- ▲ Published DeepSeek-v4-pro on DeepSWE (paper's fixed mini-swe-agent): **7.5% pass@1 / 19% pass@4** — not a forecast of der's baseline, but a warning that the qualifying-task pool after calibration may be small; a smaller suite is the correct response, not admitting 0%-baseline tasks.
- ▲ Qwen Code publishes official standalone/offline archives (`--archive` install mode, SHA256SUMS, bundled Node runtime) suited to per-trial installation from a local cache. ▽ in-container offline install smoke-checked at step 1.
- ▽ Container→host route to the pinning proxy under Pier's network setup: allowlists are verified, the exact host-gateway path is not — **first live integration test**; fallback is a stable private hostname / explicit extra-host mapping, never weakened isolation.
- ▲ AHE's per-task comparison state confirmed against source: a task counts as passing only when **all k rollouts pass** (`evolve.py` per-task logic, `tp == len(trials)`), while the headline is a pass@1-style average — the review's claim is verified, and the pass-fraction attribution patch (D7) is justified.
- ▲ The parser that `adb ask` executes is the **closed, bundled `agent_debugger_core`** (pip-installed at runtime from `agents/evolve_agent/skills/agent-debugger-cli/_source`, per evolve.py) — not the open vendored `trace_converter.py` (host-side utility only). Its `is_llm_span` requires a name keyword even for neutral span types. Consequence folded into D6.

## 3. Decisions

### D1. Vendoring and the end of "zero patches"

AHE is vendored at `research/` (plain copy, pinned commit in `UPSTREAM.md`, MIT attribution, ADB partial-open disclosure). **The zero-patch target is retired**: compatibility with an obsolete execution substrate is not an architectural invariant. AHE is intentionally adapted at **one boundary** — the evaluator — plus the enumerated attribution fix. Every AHE modification is recorded in `PATCHES.md` with rationale; the expected steady state is a handful of entries, all at the seam: replace harbor command construction with EvalRunner calls; replace reward-text parsing with EvalResult consumption; delete directory-recency recovery; replace all-k task attribution with per-task pass fractions. der-harbor (the fork-of-fork) is **deleted from the plan**.

### D2. Pier is the sole scored evaluator; DeepSWE v1.1 is the suite

- Exact Pier 0.3.x version + commit pinned. DeepSWE repository + task revisions pinned. One evaluator, one task-loading system, one networking model, one result layout, one definition of a valid run.
- Terminal-Bench is demoted to an optional unscored integration-smoke source (same Pier), never a second promotion authority.
- The acceptance test before any suite work (build step 1) proves the eight-point chain end to end: agent loads via import path → Qwen starts offline from the pinned archive → staged settings/skills recognized → egress only to the proxy → work committed → pre-artifacts extracts the intended patch → verifier runs pristine → reward/CTRF/patch/logs/trajectory/structured-result agree → an induced provider failure classifies as **invalid**, not task failure.

### D3. The EvalRunner contract (one seam, both doors)

- `EvalRunner.run(EvalSpec) → EvalResult`. EvalSpec: experiment ID, harness tree identity, suite version + task list, k, model/proxy policy ID, **RunBudget** (one immutable object: max cost, max wall-clock, attempt caps — passed to both evaluator and proxy), environment (local Docker at V1). EvalResult: evaluator job ID, exact result path, per-task/attempt outcomes classified `passed | failed | invalid`, resource totals, artifact digests.
- The adapter owns: task-path/inclusion translation to Pier flags, DerQwenAgent loading, allowlist + proxy configuration, job identity, result normalization, and the failure/invalid distinction (agent/context timeout = **failed**; provider, network, malformed verifier, infra = **invalid**, recorded, rerun-or-excluded without imputation).
- **Fail closed.** If the exact result path is absent or incomplete, the run is invalid. No recency-based recovery anywhere in the system.
- The **finalizer** (same code path for both doors) atomically: writes the immutable scorecard, appends the generated result block to the lifecycle record, regenerates the README block, applies retention + secret scrub. Runs synchronously after EvalResult; no cron writer, no publication branch, no merge drivers. Autonomous runs execute in a dedicated git worktree; one process lock serializes evals on the box.

### D4. Runtime-shaped harness; transparent staging; no renderer

- `harness/` **is a Qwen project**: `QWEN.md`, `.qwen/settings.json`, `.qwen/skills/<skill>/SKILL.md`, plus `der/` only for genuinely der-specific runtime files. The generalized component schema, context-type language, and materializer/renderer are deleted. AHE's evolve agent edits the real files Qwen consumes (its prompt teaches the Qwen project model and the small der conventions).
- **Staging overlay** (evaluator-side, transparent): copy managed files into the task workspace; select an isolated rollout HOME; disable/isolate rollout auto-memory; inject **immutable runtime bindings** (model endpoint → proxy, attempt budget, execution limits) outside the evolvable namespace; record a staged-files manifest. Overlay-injected keys win over anything evolvable; validation is a merge-policy check over **two enumerated key classes** the evolvable namespace must not set: (1) request-shaping fields (model, endpoint, keys, temperature, top_p, max_tokens), and (2) **host-executable configuration** (hook definitions, MCP server commands, and any other keys that cause command execution) — executable configuration in `harness/.qwen/settings.json` is owner-only at V1. Rollout sandboxes are disposable, but these files are destined for the owner's daily machine on adoption; the executable-keys gate is the v3 content-boundary protection carried into the runtime-shaped layout. Model slots are deleted — the overlay + proxy make them redundant.
- **Managed vs live separation stays** (unchanged from v3): daily sync renders nothing — it copies managed files to the daily Qwen location; the live-state list (auto-memory, auto-learned skills, session state; versioned per qwen release, checked by doctor) is never overwritten; feeding live state back is a manual act. Daily binding of the owner's model mix lives outside the repo.
- **Packaging:** pinned official Qwen standalone archive + checksum, installed per trial from a local read-only cache. No npm registry at rollout time; no per-trial npm-install flow.

### D5. Model pinning (mechanism unchanged, scope simplified)

Trial containers hold **no provider key**; the rendered endpoint is the **host pinning proxy** (systemd service), which injects the key, hard-sets/rejects the `model` field, enforces the RunBudget, and appends `{timestamp, run/role tag, observed model}` to an observation log the finalizer joins into scorecards. The scorecard's model field is proxy-observed, never config-copied. Detection layer: the normalizer asserts observed model == policy. (Slots and workspace literal-scanning are gone — D4 made them unnecessary.)

### D6. Evidence: the evaluator's record is canonical; NexAU is a boundary view

- **Canonical:** Pier's ATIF trajectory, Pier's structured trial result, DeepSWE's verifier artifacts (reward, CTRF, patch, logs), plus **one der-owned normalized run record** referencing those files by digest.
- **ADB compatibility view:** if ADB requires NexAU shape, generate it **ephemerally, immediately before `adb ask`**, from canonical artifacts. Provider/agent identity stays honest. Verified: the live parser is the **closed-source-bundled `agent_debugger_core`** installed from the `_source` tree vendored inside AHE — so the preferred fix is a minimal patch to **our vendored copy of that bundle** (adding the true provider keyword / a provider-neutral LLM-call role), gated on the V8 license check since a patched bundle ships in the MIT monorepo. Fallback if patching is not permissible: the ephemeral view documents the name-keyword mapping and carries the true provider in span attributes — the disguise never touches canonical records, and the mapping is stated in the repo.
- **Golden fixtures + strict mode** move to the normalizer (and the ADB-view generator): committed real Pier/DeepSWE artifacts with expected normalized outputs; strict failure on missing usage/reward fields. Every scorecard field must be traceable to a source artifact.

### D7. Experiments declare their own contracts; attribution uses pass fractions

- **Per-experiment contract, preregistered** in the lifecycle record before execution: one primary metric (e.g. macro pass@1 delta; valid-task median token reduction; wall-clock reduction), a minimum practically meaningful effect, global guardrails (e.g. pass-rate non-inferiority margin for efficiency experiments; token/cost ceilings for quality experiments), a falsifier, the suite version, k, and RunBudget.
- **No universal significance gate.** Reporting: observed effect, valid numerator/denominator, per-task outcomes, a descriptive task-cluster interval. Promotion = preregistered minimum effect met AND guardrails held, on the **confirmation set** (the term "holdout" is retired). No model has promotion authority; the contract + owner decide.
- **Optimizer attribution uses per-task pass fractions** (AHE's all-k binary task state — verified in source — is patched out; seam-adjacent, recorded in PATCHES.md); binary reward per attempt remains the grading truth.
- Validity taxonomy per D3; invalids never impute.
- **Comparability rule:** deltas (in diffs, verdicts, and the generated ledger) are computed only between scorecards with the same suite version and same k; any runtime-manifest digest mismatch between baseline and candidate (Pier version, task revisions, Qwen archive, proxy policy, agent revision) renders the comparison with an explicit **CONFOUNDED** flag — shown, never silent, never a basis for promotion.

### D8. Suites: capability-calibrated, frozen per version, three membership classes

- **Calibration** (operating defaults, not constants): ~30–40 candidate tasks chosen for repo/archetype coverage, auditable verifiers, rough match to the owner's workload distribution; baseline at k=5, boundary tasks extended to k=10; keep tasks in the **20–80% baseline band** (≈2–8/10); if too few qualify, shrink the suite rather than admit 0%-baseline tasks (expected — published DeepSeek mini-swe-agent baseline is 7.5% pass@1).
- **Membership:** development suite (~16, the optimizer's search surface, k=2 routine), **confirmation set** (~8, disjoint, interleaved baseline/candidate at k=4–5 for promotion), reporting **spine** (4–6, carried across versions, labeled reporting-only, never a gate, never specially optimized).
- **Version rules:** frozen membership within a version; new version when <half the development tasks remain in-band across three adopted baselines OR ~20 hypotheses have run against the same development suite (adaptive-exposure trigger); at a change: freeze old, select new from a maintained candidate pool, run the same harness commit on both (bridge), publish both, break the chart line.
- **Leak controls (carried from v3, extended):** pairwise-disjointness test across all suite classes/versions in preflight + CI; confirmation results published aggregate-only (per-task detail stays in run dirs); **confirmation-run traces and artifacts are excluded from ADB views and from the premium critic's evidence bundle** — the disjoint set never feeds hypothesis generation through any channel; explore-agent source allowlists exclude run/notebook artifacts (explore remains **off** at V1); after adoption, the adopted baseline runs the full versioned suite at reporting k — only that point lands on the progression chart.

### D9. Identity and truth (three levels, baseline derived)

1. **Evaluated harness identity:** source commit + git tree OID of `harness/` + runtime-manifest digest (evaluator/runtime immutable inputs: Pier version, task revisions, Qwen archive checksum, proxy policy, agent revision).
2. **Machine result:** one immutable `scorecard.json` per run (schema: experiment ID/status, baseline+candidate tree OIDs, runtime-manifest digest, suite version + task revisions, proxy-observed model + endpoint policy ID, k, valid/passed/failed/invalid counts, retry+exclusion records, per-task rewards and attempt outcomes, tokens/cost/wall-clock/turns/context-limit events, Pier job + result references, evidence digests). Scorecards are never rewritten; schema/pricing changes apply to new runs.
3. **Experiment lifecycle:** one `experiments/EXP-####-slug.md` (front matter: status proposed→running→adopted/rejected/inconclusive/invalid; proposer owner/AHE/Codex/literature; hypothesis; evidence links; intended change + managed-file scope; primary metric + min effect; guardrails; falsifier; suite version + budget; proposal-model metadata when generated). Created **before** execution — the git commit is the preregistration proof. The result table inside is generated from the scorecard.
- **The current baseline is derived**: the most recent adopted scorecard whose harness tree OID matches `main:harness`. `baseline.json` is deleted. Promotion (`der experiment adopt`) = merge the candidate tree to `main:harness` + flip the record's status; identity is re-provable by rebuilding the tree OID + runtime manifest. The unattended loop still never writes to `harness/`.
- **No eval, no ship — both gates carried from v3 into the derived-baseline world:** (a) `der experiment adopt` **refuses when `main:harness` has moved past the experiment's baseline tree OID** (the exact-replace would silently clobber owner edits; `--rebase-and-reeval` re-seeds and at minimum re-runs the confirmation set); if the adoption diff touches executable-configuration keys (D4), the diff renders them under a top-most "EXECUTES ON YOUR MACHINE" section requiring explicit acknowledgment. (b) **Daily sync refuses when the `main:harness` tree OID has no adopted scorecard** — a hand-edited, unevaluated harness does not ship to the daily machine without an explicit `--force` (the owner's deliberate-edit escape hatch, which also marks the derived baseline as unresolved until the next full-suite eval).
- The queue view is generated from `status: proposed` front matter; `BACKLOG.md` is deleted. One active experiment at a time on the serial box.

### D10. Model roles (fixed table)

| Role | V1 mechanism | Notes |
| --- | --- | --- |
| Rollout agent | DeepSeek v4 pro via pinning proxy | Owner constraint; comparability |
| Trace distillation (ADB) | Pinned DeepSeek config | Unattended simplicity; upgrade later = versioned optimizer revision |
| Automated Evolve Agent | Pinned DeepSeek config | One auth path in the autonomous loop |
| Premium proposal critic | **Owner-triggered** local `codex exec`, GPT-5.6 Sol, subscription login, read-only sandbox, schema-constrained output | Consumes a fixed evidence bundle (contract, distilled evidence, attribution, scorecard, raw links, current queue); emits one schema-validated proposal artifact (critique + zero-or-more candidate experiments, which become `status: proposed` lifecycle records). Recorded: CLI version, model + reasoning, prompt/schema digest, input commit + evidence digest, output digest, trigger. Never in the measured path; never in the unattended systemd path at V1; no OpenAI-compatible shim over subscription credentials. |
| Promotion decision | Deterministic contract + owner | No model has promotion authority |

### D11. Publication: one generated README block

Generated from scorecards + lifecycle records, by the finalizer: hero step chart (adopted-baseline macro pass@1 over time; annotations per adopted experiment; series break + bridge points at suite-version changes; optional thin labeled spine series), compact ledger of **every** experiment (adopted/rejected/inconclusive/invalid, observed delta, reason, link), and small aligned resource strips (tokens, cost, wall-clock). Every aggregate carries the Tura-style reporting contract (task revision, model, k, numerator/denominator, retry policy, exclusions). Deleted: `DASHBOARD.md`, the second chart, stored badges, any separate notebook index, any hand-copied score table. README also states DeepSWE's scope honestly (long-horizon repository work; short edits under-represented).

### D12. Ops floor (carried, trimmed to the new shape)

- systemd: evolve service (`Restart=on-failure`, `OnFailure` → notification), watchdog timer (spend actuals from scorecards + provider balance; at RunBudget/monthly ceiling: `systemctl stop` + `COST_CEILING_REACHED` flag gating `ExecStartPre`), pinning-proxy service, optional night window + `CPUQuota`. Provider-side prepaid cap remains the hard wall.
- Notify shim (Feishu-format receiver → owner's channel) with {iteration cost, cumulative, balance, ceiling flag}; AHE notify untouched.
- Preflight/doctor on every entry: Docker up, disk headroom, Pier + archive cache present, suite disjointness test, proxy healthy (1-token ping), qwen daily-vs-evaluated version skew warning, live-state list version.
- Janitor at run end (containers/images prune; evidence retention: keep canonical artifacts for last N runs + anything digest-referenced by committed records; scrub secrets before any commit).
- Runbook + acceptance tests: kill -9 mid-eval → resume (iteration-granular; interrupted work re-spends); ceiling → clean stop, flag blocks restart, notification arrives; induced provider fault → `invalid`.
- Overlay defaults: `max_iterations: 10`, finite timeouts, best_of_n off, explore off.

## 4. Build order (the scoring spine first)

0. **Freeze external identities; define schemas.** Pin AHE commit, Pier version+commit, DeepSWE repo+task revisions, Qwen archive+checksum, agent revision, model+proxy policy. Write EvalSpec/EvalResult/scorecard schemas before orchestration.
1. **One DeepSWE task through Pier, manually.** Smallest DerQwenAgent; prove the eight-point acceptance chain (D2), including the container→host proxy route, plus one deliberate failing task and one induced infrastructure-invalid run. Nothing proceeds while any fact is inferred rather than inspected.
2. **Normalizer + scorecard.** Parse Pier/DeepSWE output into the canonical schema; hand-trace one run session→ATIF→commit→patch→verifier→scorecard; commit golden fixtures; strict mode on.
3. **Integration battery.** 3–5 DeepSWE tasks, different languages/verifier shapes, k=1: proves selection, cleanup, retry classification, proxy, artifact collection.
4. **Shared evaluator door.** Owner CLI over EvalRunner; then patch AHE onto the same interface (remove harbor command construction, reward-text parsing, recency recovery, all-k attribution). Two-iteration toy loop; verify exact job/result association + deterministic resume.
5. **Runtime-shaped `harness/` + promotion identity.** Native Qwen layout; staging overlay + immutable bindings; hand-authored A/B end to end; adopt; rebuild from `main:harness` and prove tree OID + runtime manifest match the evaluated identity. **Owner value ships here.**
6. **Calibrate and freeze suite v1.** k=5 screen (k=10 boundaries); freeze development/confirmation/spine membership; publish the exclusion record; full-suite baseline before any autonomy.
7. **Lifecycle record + README generator.** Pre-run record creation, scorecard attachment, verdict transitions, hero chart + ledger. (Publication comes after the pipeline is trustworthy, not before.)
8. **Analyzers + unattended operation.** ADB boundary view + acceptance test; Codex proposal critic; autonomous AHE service in its worktree; notifications, retention, GC; systemd hardening + recovery drills. Autonomy last — it magnifies every defect below it.

## 5. Lifecycle walks

**(a) Owner hypothesis:** create `EXP-####` record (contract preregistered, commit = proof) → `der experiment run` (lock; EvalSpec with explicit IDs) → EvalRunner → Pier → finalizer writes scorecard, appends generated result block, regenerates README → owner sets verdict per contract → if adopting: confirmation-set eval (interleaved) → `der experiment adopt` merges tree + flips status → daily sync copies managed files (live state untouched).

**(b) Autonomous iteration:** evolve service (worktree, lock) → EvalRunner on development suite (k=2) → attribution from per-task pass fractions + manifests (falsification automatic; evolve-agent rollbacks per policy; snapshot fallback) → ADB boundary view → evolve agent writes edits + manifests → finalizer per run → stop on target / `max_iterations` / RunBudget ceiling (clean stop + flag). Candidates it likes become `status: proposed` lifecycle records — promotion still flows only through (a)'s contract path.

**(c) Premium critique (owner-triggered):** `codex exec` (read-only, schema output) over the evidence bundle → one validated proposal artifact → zero or more new `status: proposed` records; everything recorded.

## 6. Cost model

Unchanged planning band (~$10–50 per ~100-attempt eval at DeepSeek-class pricing; ADB $3–8; evolve session $1–3; an eval is an overnight unit at n-concurrent 4–8). Multipliers pinned in the overlay (`max_iterations: 10`, best_of_n off, finite timeouts). Note: DeepSWE long-horizon tasks may run longer than terminal-bench tasks per attempt — recalibrate the band at build step 3 and set RunBudget accordingly. The prepaid provider cap remains the guard that survives every local bug.

## 7. Risks

1. **Pier/DeepSWE integration facts** (result layout, ATIF fields, pre-artifacts flow, proxy route): front-loaded to build steps 0–3; fail-closed adapter; golden fixtures.
2. **AHE adaptation depth** — patching at the seam could reveal deeper coupling: bounded by the round-1–3 audits (coupling enumerated); PATCHES.md records reality; worst case the optimizer loop is adapted incrementally while the CLI door ships value from step 5.
3. **Small calibrated suite** (weak DeepSeek baseline on DeepSWE): shrink suite rather than dilute; spine + bridge preserve continuity; confirmation interleaving controls drift.
4. **Adaptive overfitting:** confirmation set + version triggers (in-band decay or ~20 hypotheses) + aggregate-only publication + frozen membership.
5. **ADB view fidelity / parser location:** V6; ephemeral view + fixtures + honest identity policy.
6. **Model-pin subversion:** unchanged (keyless containers + proxy + overlay-owned request-shaping fields).
7. **Cost blowout:** RunBudget + watchdog + prepaid wall; DeepSWE per-attempt cost re-measured at step 3.
8. **Qwen nightly cadence:** pinned archive; skew warnings; upgrades are experiments.
9. **ADB opacity/licensing:** disclosed; license check retained (V8).

## 8. Stage-2 verification list

V1. Pier pin smoke on `datacurve-pier==0.3.0` (flags already source-verified): per-trial job/result **directory layout**, exact `reward.json`/`ctrf.json` field shapes, ATIF v1.7 per-call token-usage fields via an OpenAI-compatible DeepSeek endpoint.
V2. The eight-point acceptance chain on one DeepSWE task (D2), incl. container→host proxy routing under Pier networking (fallback: private hostname / extra-host mapping).
V3. Qwen standalone archive (existence verified): offline install from local cache **inside a task container** — bundled-runtime completeness under the container image.
V4. evolve.py attribution patch (all-k claim already source-verified): pin the **minimal** pass-fraction patch set at the seam; confirm no other consumer depends on the all-k state.
V5. Induced-fault classification: provider 4xx/5xx, network kill, malformed verifier → `invalid` (never reward-0 fail); agent/context timeout → `failed`.
V6. ADB parser patch (live path already verified = closed bundled `agent_debugger_core` from `_source`): confirm the pip-install-at-runtime picks up our patched vendored copy; acceptance test with a synthetic converted trace (LLM/tool spans, token sums, drill-down all register with honest provider naming); gated on V8.
V7. DeepSWE task revisions: pin mechanism (repo commit), verifier auditability spot-check on candidate tasks.
V8. ADB `_source` license terms inside an MIT monorepo.
V9. DeepSeek balance endpoint for the watchdog meter (account-type specific).
V10. Server prereqs at Pier concurrency 4–8 (CPU/RAM/disk; provider rate limits); Qwen archive + Pier + DeepSWE revision mirror in the local cache.

## 9. Round-4 disposition (adopt / retain / reject)

**Adopted (all five approval conditions + supporting changes):** Pier as sole scored evaluator; DeepSWE v1.1 primary (terminal-bench demoted to unscored smoke); EvalRunner semantic adapter with intentional AHE patches (zero-patch goal retired; PATH shim, der-harbor fork, and per-trial npm flow deleted); runtime-shaped `harness/` + transparent staging overlay (component schema, renderer, and model slots deleted; pinned standalone archive from local cache); per-experiment preregistered contracts with primary metric/min effect/guardrails/falsifier ("statistically significant" vocabulary dropped; "holdout" → confirmation set; per-task pass-fraction attribution; validity taxonomy); three-level identity (tree OID + runtime manifest; immutable scorecard; lifecycle record; derived baseline — `baseline.json`, `BACKLOG.md`, `DASHBOARD.md`, second chart, badges all deleted); both doors through one synchronous EvalRunner + finalizer (cron writer, publication branch, merge driver, recency recovery deleted; explicit IDs; fail closed); Q2 calibration protocol + suite-version rules + bridge runs; Q3 model-role table (owner-triggered `codex exec` critic, schema output, full provenance recording, no subscription in unattended path, no auth shim); Q6 parallelism deferred (no E2B — Pier's cloud is Modal; equivalence experiment gate before any cloud results join the series); one immutable RunBudget unifying budget/watchdog specs.

**Retained from v3 (compatible, not superseded):** pinning proxy + keyless containers + proxy-observed model; provider prepaid cap; managed/live separation + live-state list + out-of-repo daily binding; isolated rollout HOME; systemd supervision + ceiling flag semantics; notify shim with cost figures; preflight/doctor incl. suite disjointness test; janitor + evidence retention + secret scrub (now in the finalizer); golden fixtures + strict mode (now at the normalizer); confirmation-leak controls (aggregate-only publication, explore-source exclusions, explore off at V1); kill-9/resume + ceiling acceptance tests; cold-start full-suite baseline; overlay safety defaults.

**Rejected/qualified:** nothing material. Two qualifications: (i) the honest-provider-naming fix depends on which ADB parser copy executes (V6) — if a closed parser forces keyword names, the mapping is documented and confined to the ephemeral view, with true identity in span attributes; (ii) the review's "7.5%/19%" DeepSeek figure is treated as a calibration warning, not a der baseline forecast (its own caveat).

## 10. Convergence log

- v1 → v2 (round 1: Forge/Prism/Flint) and v2 → v3 (round 2: Vex/Sage; round 3: Arbiter closure — 27/27 resolved): see draft_v3 §10.
- **v4 gap audit (round 5: Sentry):** integration matrix 100% (6 findings, 6 Q-answers, 26 elegance rows, 5 approval conditions all reflected); four silently-lost v3 protections restored (executable-configuration gate + EXECUTES-ON-YOUR-MACHINE adoption diff; no-eval-no-ship at both adopt and sync gates; CONFOUNDED comparability rule; confirmation-set exclusion from ADB views and critic evidence bundles); one fact corrected (the live ADB parser is the closed bundled `agent_debugger_core`, not the open vendored converter — patch target redirected, license-gated); Pier flags/result formats, the Qwen standalone archive, and the all-k attribution claim verified against source (pin `datacurve-pier==0.3.0`, ATIF v1.7).
- **v3 → v4 (round 4: external GPT 5.6 Sol Pro review — RESTRUCTURE):** evaluation authority moved from AHE's pinned harbor fork to a pinned Pier 0.3.x as sole scored evaluator with DeepSWE v1.1 as the primary suite; the zero-AHE-patch goal replaced by one intentional EvalRunner seam (+ attribution fix); the component renderer/schema and model slots replaced by a runtime-shaped Qwen `harness/` with a transparent staging overlay and overlay-injected immutable bindings; canonical evidence moved to Pier/DeepSWE artifacts with NexAU demoted to an ephemeral, honestly-labeled ADB boundary view; the universal sign-test gate replaced by preregistered per-experiment contracts (primary metric, minimum effect, guardrails, falsifier) with per-task pass-fraction attribution and a versioned confirmation set; identity collapsed to tree OID + runtime manifest + immutable scorecard + lifecycle record with a derived baseline; publication collapsed to one generated README block; orchestration collapsed to one synchronous EvalRunner + finalizer with fail-closed job identity; parallelism deferred (Modal, not E2B, as the future cloud path); npm-tarball install replaced by the pinned official standalone archive; build order rebuilt around the scoring spine (evaluator proven before orchestration, publication after trust, autonomy last).
