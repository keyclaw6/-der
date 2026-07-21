# der auto-research loop — Stage 1 architecture (DRAFT v2)

Status: revision after adversarial round 1 (Forge/systems, Prism/source-fidelity, Flint/operations — all REVISE; all blockers addressed below). Stage 2 (implementation plan for an executing agent) remains out of scope until owner approval.

## 0. Purpose

Stand up an automated research loop around the der harness (Qwen Code base) by adapting the official AHE codebase, so that:

- the owner's **own hypotheses** run through a rollout + scorecard + verdict pipeline (A/B against baseline) from day one,
- the harness can then be **evolved autonomously** (AHE evaluate → analyze → improve, unattended, resumable, budget-capped),
- every run produces a **comparable scorecard** (pass rate, tokens in/out, cost, wall-clock, turns) feeding the public dashboard,
- **DeepSeek v4 pro is the pinned model for every research-loop role** (rollout agent, Agent Debugger, Evolve Agent, explore agent) — enforced structurally, not aspirationally.

## 1. The architecture in three sentences

1. **The substrate is the product:** materializer + der harbor agent + trace converter + scorecards + `research` CLI + dashboard form a free-standing eval pipeline, independently testable, shipping owner value (hand-written A/Bs) before any autonomy exists.
2. **The inherited AHE loop (`evolve.py`) is a client of that substrate**, consuming it purely through its config seams (`harbor.agent`, `source_config_dir`, `${LLM_*}` env) — verified against source: harbor invocation is fully config-driven and the workspace layout is a bare `copytree` with no hardcoded component names.
3. The swap of agent-under-test is **one role behind two adapters plus prompt retargeting**: a der harbor agent (workspace → Qwen Code, registered in our harbor fork), a qwen→NexAU trace converter (running inside the agent's post-run hook), and der-flavored evolve/explore prompts replacing the NexAU-specific ones.

## 2. What the source audit established (load-bearing facts)

- **Seam verified:** `_build_harbor_cmd` emits agent name, env, and `--ak config_path={workspace}/agent.yaml` entirely from config; `init_workspace` is `copytree` + `git init` — the seven NexAU component names appear nowhere in `evolve.py` logic. Component semantics live in the evolve-agent prompts/skills, which we retarget.
- **Harbor pin is load-bearing:** AHE pins `Curry09/harbor-LJH` (16 ahead / **920 behind** upstream `harbor-framework/harbor`; incompatible agent base API). Its qwen agent is a 68-line trace-blind stub; **upstream's `qwen_code.py` (348 lines) is the reference implementation** — session JSONL capture, ATIF trajectory, per-call token usage. Custom agents on the pinned fork require in-tree registration (AHE's own pattern for `nexau`) or an `--agent-import-path` patch.
- **Trace contract is strict:** `evolve.py` and the evolve-agent prompts hardcode `agent/nexau_in_memory_tracer[.cleaned].json` (NexAU span-tree shape); ADB's `is_llm_span` counts only spans whose **name contains "openai"/"gpt"/"anthropic"/"gemini"/"llama"** with OpenAI-completion-shaped outputs — qwen/deepseek are not keywords. The converter must name spans accordingly or analysis silently zeroes out.
- **Attribution needs nothing from traces:** flip attribution consumes only the evolve agent's own `change_manifest.json` + harbor's `verifier/reward.txt` per trial. Rollback reality: falsification verdicts are automatic; per-file rollback is executed by the Evolve Agent per prompt policy; automatic full-workspace rollback to best-ever snapshot exists as fallback.
- **Qwen Code emits per-call token usage in three forms** (chat-recording session JSONL `usageMetadata`; `--output-format json` summaries; OTLP telemetry) — the metrics story needs no proxy.
- **Upstream footguns (verified defaults):** `max_iterations: 100`, both timeouts `0` (unlimited), notify is Feishu-format-only, resume granularity is the iteration, `evolve.py` has zero cost accounting, and the host keeps a NexAU dependency (evolve/explore agents are NexAU) plus Python ≥ 3.13 + uv + tmux.
- **ADB is only partially open-source** (bundled `agent_debugger_core` installable; works self-hosted with DeepSeek) — must be disclosed in the public notebook; license check in Stage 2.

## 3. Decisions

### D1. Vendor AHE as `research/` in the der monorepo (plain copy + `UPSTREAM.md`)

Plain vendored copy pinned to a commit recorded in `UPSTREAM.md`; MIT attribution preserved; re-syncing upstream is a periodic diff exercise. No git subtree. The public notebook discloses the partially-closed ADB component. Host prerequisites named: Python ≥ 3.13, uv, tmux, Docker, Node (for Qwen Code), NexAU (host-side, for evolve/explore agents — it does not disappear after the swap).

### D2. Harbor: stay on AHE's pin; register the der agent in our fork of that fork

- We fork `Curry09/harbor-LJH` → `der-harbor`, and register the **der agent in-tree** (new `agents/installed/der_qwen.py` + one enum line), exactly mirroring how AHE registered `nexau`. The agent ports upstream's `qwen_code.py` mechanics (npm-install pinned `@qwen-code/qwen-code@<version>` at trial setup — or prebuilt task images with `force_build: false` as the optimization) onto the fork's base API, adding: workspace upload (`environment.upload_dir` in `setup()`), host-side materialization before upload, fresh-HOME isolation (no owner qwen state, loop-scoped DeepSeek key only), and post-run trace conversion + metrics extraction in `populate_context_post_run`.
- `PATCHES.md` ledger governs `evolve.py` divergence: every patch recorded with rationale; **target: zero entries** (registration avoids the `--agent-import-path` patch; budget and notify are solved outside the loop — D9, D13).
- Upstream harbor migration is a named, deferred option; revisit only if the fork blocks something concrete (its incompatible agent API makes switching a rewrite of the der agent — priced in, not planned).

### D3. Substrate-first dependency structure; `research` CLI is the primary interface

- New code lives in `research/der/` as small, single-purpose modules behind one CLI: `research smoke` (frozen 5-task list, k=1, <15 min, ~$1 — run after every change), `research eval <workspace> [--suite S] [--k N]`, `research diff <scorecard-A> <scorecard-B>` (per-task flip table + paired sign-test/binomial CI + an explicit `inconclusive` verdict when the CI includes zero), `research ab` (sugar: eval ×2 + diff), `research promote <run>`, `research dashboard`, `research postprocess` (see D10), plus preflight/doctor checks (D13).
- `evolve.py` (the autonomy driver) consumes the same workspace, suites, agent, and scorecard machinery purely via config — it enters last in the build order (Section 5) at toy scale.
- Reusable internals of `evolve.py` (`run_harbor`, `compute_stats`) may be imported by the CLI (it is an importable module) — reuse, don't reimplement.

### D4. Component workspace: one source of truth, two materialization contexts

- `harness/` (repo root) is the **workspace source** — managed component files only. It is not itself a runnable Qwen config.
- The **materializer** is a pure function `(workspace, context) → rendered Qwen Code config`, where context ∈ {rollout, daily}: rollout renders into the trial's project dir (via the der agent); daily renders into the user-level Qwen config location **outside the repo** via `der sync` (run manually after merging a promotion). A maintained **live-state list** (Auto-Memory files, auto-learned skills, session state) is never overwritten by sync; feeding live state back into `harness/` is a deliberate manual act. This kills the promotion-clobbers-my-memory failure and the private-state-in-public-repo leak.
- **V1 component contract (4 types):** `system/QWEN.md`, `agent.yaml` (schema-validated; see D5), `skills/`, `memory/LongTermMEMORY.md` (seed). The materializer **rejects everything else loudly**. The full 8-type target schema (adding `tool_descriptions/`, `tools/` = MCP, `middleware/` = hooks, `sub_agents/`) is documented as the roadmap; executable classes (hooks, MCP, tools) phase in later behind their own guardrails: vetted-catalog-only MCP references, hooks as diffable in-workspace scripts, and promotion diffs rendering executable content under a top-most "EXECUTES ON YOUR MACHINE" section.
- The evolve-agent prompt is retargeted to describe exactly the implemented der component types (replacing `nexau-evolution-guide`); the explore agent's `code_sources` swap NexAU for Qwen Code docs + der docs — but explore stays **off** at V1 (D9).

### D5. Model-slot indirection makes the DeepSeek pin enforceable

- Workspace files may reference **model slots only** (`primary`, `subagent-default`, named slots). Binding maps live outside the workspace: the research overlay binds every slot → DeepSeek v4 pro (pinned model string, base URL, temperature policy); the owner's daily binding maps slots → their chosen mix.
- The materializer **fails validation on any literal model/provider/base_url/temperature string anywhere in the workspace** — the Evolve Agent structurally cannot un-pin the loop (the most rewarding reward-hack otherwise available to it), and scorecard comparability survives. `agent.yaml`'s schema explicitly enumerates evolvable params vs context-pinned params.
- Wording discipline: temperature pinning is **variance reduction**, not determinism; nothing downstream may assume deterministic rollouts (that is what k exists for). AHE's NexAU-shaped `code_agent_patch` default is replaced in the der overlay with der's schema.

### D6. Trace + metrics contract (the one genuinely new load-bearing component)

- The **qwen→NexAU trace converter** runs **inside the der harbor agent's `populate_context_post_run`** (there is no post-eval seam in `evolve.py` — placement is forced, and correct: that's where upstream qwen_code.py builds its trajectory).
- Input: Qwen Code chat-recording session JSONL (`~/.qwen/projects/<project>/chats/`, copied out of the trial container), `usageMetadata` per assistant event as the metrics source; OTLP file telemetry as secondary. Output: NexAU InMemoryTracer **span tree** at `agent/nexau_in_memory_tracer.json` + payload-trimmed `agent/nexau_in_memory_tracer.cleaned.json` — LLM spans **named to contain "openai"** with OpenAI-completion-shaped outputs including `usage`; tool spans `type: "TOOL"`. This satisfies `adb ask`, `extract_agent_behavior_stats`, and the file paths baked into the evolve-agent prompts, with zero evolve.py changes.
- **Golden fixtures + strict mode:** committed real session logs with expected converted outputs as unit fixtures; strict mode fails the trial on missing usage fields rather than defaulting zeros (a converter that silently emits zeros makes ADB analyze fiction N paid iterations before anyone notices). Tolerate absent `cached/thoughts` fields from OpenAI-compatible DeepSeek responses.
- **Error taxonomy:** every trial classified `passed | failed | errored` (provider 4xx/5xx, sandbox/infra faults, infra timeouts — enumerated in Stage 2). `errored` is excluded from pass rates and flip attribution; an iteration missing non-errored results for any task×k is marked `incomplete` and skipped by postprocess (then re-queued or alerted).

### D7. Scorecards, lineage, and comparability

- **Scorecard schema (JSON, one per run):** run id, suite id+version, k, workspace **content hash** (SHA-256 over a canonical tar: sorted paths, zeroed mtimes) + git SHA when one exists, model string + provider base + pricing-table version, qwen-code version, materializer version, per-task `passed/failed/errored` counts × k, tokens in/out (+cached), cost, wall-clock, turns; aggregate stats + named baseline ref. Comparability rule: **same suite version and same k, or the diff refuses**.
- **Seeding rule (one line):** every evolve run and every `research eval/ab` seeds its workspace from `harness/` at a recorded git SHA; per-run loop lineage is ephemeral; promotion PRs are cut against that same seed SHA. Owner hand-edits automatically enter the next run; unmerged loop progress is deliberately discarded unless promoted.
- **No eval, no ship:** `research promote` re-hashes the candidate `harness/` state and verifies it equals the `workspace_hash` of the scorecard being promoted; mismatch = refuse. "Promote with a small manual tweak" is structurally impossible.
- **Cold start:** `research eval harness/` runs once before the first evolve run — scorecard-0 gives the dashboard a baseline point and attribution a floor.
- **Verdict timing documented:** iteration N's scorecard exists at N; its flip-attributed verdict (`change_evaluation.json`) lands at N+1. The dashboard plots scorecards immediately and fills verdict cells asynchronously.

### D8. Suites: frozen ID lists, a holdout, no ceremony

- `der-suite-v1`: **committed task-ID list** (~50, seeded random from `terminal-bench@2.0`, one-line provenance note), passed to harbor via `-t` filters against the pinned dataset reference. `der-holdout-v1`: ~30 disjoint task IDs, **never referenced by the loop, never analyzed by ADB**. `der-smoke-v1`: 5 tasks for the smoke path. Local dataset mirror only if the upstream reference proves mutable (Stage-2 check).
- **Holdout gate on promotion:** promoting a workspace requires a fresh holdout scorecard with pass-rate delta ≥ 0 vs the current baseline's holdout score (CI-aware per D3's diff semantics). Overfit-to-suite hacks — the guaranteed failure mode of optimizing 50 visible tasks for many iterations — die at the gate instead of moving into the daily driver.
- k=2 (upstream default; per-task pass-rate signal for attribution); `research ab --k 4` when a hypothesis needs tighter noise bounds; occasional full-suite runs pre-adoption or for leaderboard fun.

### D9. Budget: provider-side prepaid cap is the wall; actuals are the meter; no cost model

- **Hard wall:** DeepSeek prepaid balance / provider spend cap sized to the monthly budget — the only control that survives every local bug.
- **Meter:** cumulative actuals (rollout costs summed from scorecards + provider balance polled between iterations, which also captures ADB/evolve/explore overhead without any proxy). A **watchdog timer** (systemd) checks spend against `max_run_cost_usd`; at ceiling it stops the loop (SIGTERM to the tmux session) — safe because resume granularity is the iteration and `evolve-resume.sh` exists. No projected-cost model, no evolve.py patch. Iteration-end notifications carry {iteration cost, cumulative cost, provider balance} (D13).
- **Overlay defaults that must ship:** `max_iterations: 10` (upstream 100 would be a $1K–5K unattended surprise), both timeouts set finite, `best_of_n: off` (×N rollout-cost multiplier; a later deliberate experiment), `explore_agent: off` at V1, `force_build: false` with pre-built suite images.
- A per-role metering proxy (single LLM_BASE_URL) is a named **later option** if fine-grained cost attribution ever earns its keep; it is not V1.

### D10. Runs layout, locks, working copies, postprocess

- Namespaced runs: `research/runs/evolve/<run-id>/iteration_NNN/` (AHE-native inner layout preserved) vs `research/runs/adhoc/<exp-id>/`. An **flock single-writer lock** wraps every harbor invocation: `research eval/ab` refuses (with `--queue`) while an evolve iteration holds it; one box, one rollout batch at a time.
- **The loop runs in its own clone** (`~/research-runner/der`), commits once per iteration ("research: iteration NNN scorecard + attribution") to a dedicated `research-runs` branch; the owner merges opportunistically. The daily driver never reads the runner's tree (daily config lives outside the repo per D4).
- `research postprocess` is an **idempotent pure function of `runs/`**: (re)builds missing/stale scorecards, regenerates dashboard artifacts, applies the trace-retention policy (keep last N iterations + traces referenced by committed digests; delete/compress the rest), and runs a **secret scrub** (no keys/base-URLs in committed artifacts). Cron-safe every 10 minutes during runs; crash between harbor-finish and scorecard-write self-heals on the next tick.
- Raw traces are gitignored AND garbage-collected (gitignored ≠ deleted; ~10M trace tokens/iteration fills a disk in weeks).

### D11. Publication: dashboard v0 + notebook

- `research dashboard`: one idempotent script regenerating everything from committed scorecards. **V1 = pass-rate chart + cost chart (SVG) + experiment index table.** SVGs live at fixed paths (`docs/dashboard/*.svg`) embedded from README — README text itself almost never changes; the full experiment index lives in `DASHBOARD.md` linked from README (kills the README-as-conflict-hotspot problem while honoring "README leads with a glanceable dashboard").
- The notebook unit: `experiments/EXP-NNN-slug.md` (hypothesis, setup/workspace diff, scorecard link, verdict) from a committed `TEMPLATE.md`. The ADB partial-open-source status is disclosed in the repo.

### D12. Promotion: small script, human content-gate, loop never touches `harness/`

`research promote <run>`: create branch → copy winning workspace over `harness/` → verify evaluated-equals-promoted hash (D7) → require a fresh holdout scorecard (D8) → commit with manifest + scorecard path in the message → print "review the diff, then merge." The **promotion diff review is the content trust boundary** (the materializer is only the shape boundary) — tractable at V1 because the component contract contains no executable classes yet. The unattended loop never writes to `harness/`. After merge: `der sync` (D4) updates the daily driver.

### D13. Ops floor (the 3am story)

- **systemd** units, not bare tmux: the loop under `Restart=on-failure` with `OnFailure=` → webhook notification; the watchdog timer (D9); optional night-window timer + `CPUQuota`/`Nice` so rollouts don't peg the box the owner is daily-driving (supported-but-degraded coexistence, heavy runs scheduled off-hours by default).
- **Notify shim:** a ~10-line Feishu-format-compatible receiver forwarding to the owner's channel (ntfy/Telegram) — AHE's notify stays unpatched. Messages include cost figures (D9).
- **Preflight/doctor** in every CLI entry: Docker up, ≥X GB free disk, suite images present, provider key answers a 1-token ping, qwen version matches the adopted baseline's evaluated version (warn on skew), live-state list intact. Disk janitor runs end-of-iteration (prune exited containers/dangling images, trace GC per D10).
- **Runbook** (half page): loop dead → `systemctl status` → resume command → restarts from iteration boundary (re-spends the interrupted iteration — documented, acceptable). "kill -9 mid-rollout, then resume" is an acceptance test in the skeleton.
- **Rollout isolation:** trial containers get a fresh HOME, injected env only (loop-scoped DeepSeek key), never the owner's personal qwen state or credentials.

## 4. System diagram

```
                    der repo (public, MIT) ──────────────────────────────────────────────┐
                    │                                                                     │
 owner ──► research CLI ── smoke/eval/ab ──┐                                              │
           (primary interface)             │ flock lock                                   │
 autonomy ► evolve.py (AHE, vendored,      ├──► harbor (der-harbor fork pin) ──► trial containers
            config-level client)  ─────────┘         │                            [qwen-code pinned,
                    │                                │                             fresh HOME, rendered
                    ▼                                ▼                             workspace, DeepSeek v4 pro
            Evolve Agent (DeepSeek v4 pro)   der agent post-run hook:              via model slots]
            edits workspace copies           traces → NexAU span tree
            + change manifests               + usageMetadata → metrics
                    │                                │
                    ▼                                ▼
            ADB digests (DeepSeek) ◄── runs/{evolve,adhoc}/... ──► research postprocess (idempotent)
                                                                     ├─ scorecards (hash-addressed)
   watchdog (systemd): spend meter,                                  ├─ docs/dashboard/*.svg + DASHBOARD.md
   provider balance, stop-at-ceiling                                 └─ trace GC + secret scrub
                    │
 harness/ (workspace SOURCE, 4 component types, model slots only)
    ▲ research promote (hash-verified + holdout-gated + owner diff review)
    └──► der sync ──► daily Qwen config (outside repo; live-state list never overwritten)
```

## 5. Build order (walking skeleton — becomes Stage 2's milestone spine)

0. **Seam-kill spike (~$1, no code):** one terminal-bench task via harbor on local Docker with a built-in agent (proves `env: docker` on the pin — AHE never exercised it); `qwen -p` headless against DeepSeek by hand; confirm session JSONL + per-call usage lands.
1. **Minimal der harbor agent** in the der-harbor fork: pinned qwen + one-file workspace stub; one task, k=1. Proof: trace file lands at the contracted path.
2. **Converter + scorecard** over that trace; golden fixture committed; strict mode on. Proof: numbers match the raw log by hand.
3. **`research smoke` / `research eval`**: frozen 5-task list end-to-end. (The owner-facing CLI exists from here on.)
4. **Dashboard v0** from committed scorecards (validates the schema before anything depends on it).
5. **Materializer v1 (4 types, slot enforcement) + `research diff`.** Proof: a real hand-written A/B end to end. **Owner value ships here, before any evolve-agent work.**
6. **ADB integration** (DeepSeek-pinned) over smoke-suite traces. Proof: digest claims link to real trace events — validates the converter against its actual consumer.
7. **evolve.py at toy scale:** 5-task suite, `max_iterations: 2`, best_of_n/explore off. Proof: manifests written; attribution binds predictions to observed flips on qwen traces; rollback fires on a failed prediction; **kill -9 mid-rollout → resume works**.
8. **Production V1:** 50-task suite + holdout, k=2, systemd + watchdog + janitor + notify, cold-start baseline scorecard, then a real 10-iteration run.

## 6. Lifecycle walks

**(a) Autonomous evolve iteration:** watchdog/preflight pass → evolve.py (in runner clone, under lock) seeds workspace from `harness/`@SHA → harbor runs suite k=2 with the der agent (traces + metrics emitted per-trial by the post-run hook) → attribution binds the previous manifest's predictions to observed flips (verdicts in `change_evaluation.json`; Evolve Agent executes per-file rollbacks per policy; best-ever snapshot rollback as fallback) → ADB distills evidence → Evolve Agent writes edits + manifests into `evolve/` → postprocess emits scorecard, regenerates dashboard, GCs traces → iteration commit to `research-runs` → stop on target / `max_iterations` / spend ceiling.

**(b) Owner hypothesis (A/B):** branch `harness/`, hand-write the change + `experiments/EXP-NNN.md` from template → `research ab` (waits on lock; both sides seeded and hashed) → `research diff` prints flip table + CI, possibly `inconclusive` → owner writes the verdict → dashboard regenerates → promote if warranted.

**(c) Promotion + sync:** `research promote <run>` (hash check + holdout gate) → owner reviews the diff (content boundary) → merge → `der sync` renders managed components into the daily config, never touching live state.

## 7. Cost model (planning band; pricing table versioned in Stage 2)

At DeepSeek-class pricing (~$0.3–0.6/M in, $1–2/M out, cached ~10× cheaper): rollout ≈ $0.05–0.35 → **$5–35 per 100-rollout iteration**; ADB ≈ $3–8; evolve agent ≈ $1–3 → **≈ $10–50 per iteration**, 3–6 h wall-clock at n_concurrent 4–8 (an iteration is an overnight unit; ~1–2/day natural ceiling). Multipliers to keep visible: `max_iterations` (overlay pins 10), `best_of_n` (×N, off), unlimited-by-default timeouts (overlay sets finite). Continuous operation lands ~$300–1,500/mo — the prepaid provider cap is the guardrail that makes all other guards optional.

## 8. Risks

1. **Converter fidelity** (the one new load-bearing component): mitigated by golden fixtures, strict mode, ADB acceptance test at skeleton step 6, and the `is_llm_span` naming contract written into D6.
2. **Harbor fork drift:** pinned fork is 920 commits behind upstream with an incompatible agent API; we accept it (AHE's tested substrate), isolate exposure in one agent file, and keep upstream migration as a priced option.
3. **Suite overfitting:** guaranteed failure mode of long-run optimization on 50 visible tasks → holdout gate (D8) + full-suite runs before adoption.
4. **Noise at k=2:** CI-aware diffs with explicit `inconclusive`; `--k 4` escalation; errored-trial taxonomy keeps infra noise out of attribution.
5. **evolve.py coupling beyond enumerated seams:** narrowed by audit to trace filenames/schema, agent registration, notify format, `code_agent_patch` shape — all addressed without patches; `PATCHES.md` ledger if reality disagrees.
6. **Monorepo/live-state corruption:** dual materialization contexts + live-state list + separate runner clone + `research-runs` branch (D4/D10).
7. **Model pin subversion by the evolve agent:** slot indirection + literal-string rejection (D5).
8. **Cost blowout:** prepaid wall + watchdog + overlay defaults (D9).
9. **ADB opacity/licensing:** disclosed; license check in Stage 2; worst case ADB is replaceable behind `adb ask`'s CLI surface (a later project, not V1).
10. **Qwen Code nightly cadence:** version pinned per suite evaluation; doctor warns on daily/evaluated skew; upgrades are themselves experiments.

## 9. Stage-2 verification list (live-install checks, inherited from audit)

1. Harbor pin smoke: flag surface matches `_build_harbor_cmd`; job-dir naming regex; trial-dir layout; der agent instantiation via in-tree registration with `--ak config_path=...`.
2. `env: docker` end-to-end on the pin (build, upload_dir, log download) — AHE never exercised it.
3. Real NexAU trial dir: pin the exact in-sandbox `.cleaned.json` byte-shape (span-tree vs cleaned-dict) before finalizing the converter.
4. `adb ask` acceptance: synthetic qwen→NexAU trace registers LLM/tool spans, token sums, drill-down.
5. Pinned qwen version flags: `--chat-recording`, `--auth-type openai --openai-api-key/--openai-base-url`, `--yolo`, turn/wall-time limits; session path layout; `usageMetadata` population via DeepSeek OpenAI-compatible endpoint (tolerate absent cached/thoughts).
6. Exact Qwen Code project-config paths for the 4 V1 component types (nightly docs drift).
7. Whether harbor `result.json` carries token/cost context fields on the pin (cheap secondary scorecard source).
8. ADB `_source` license terms inside an MIT monorepo.
9. Notify shim receiver choice; watchdog SIGTERM→resume drill.
10. Server prereqs: Python ≥ 3.13, uv, tmux, Docker capacity at n_concurrent 4–8; DeepSeek rate limits at that concurrency; dataset reference immutability (else mirror locally).

## 10. Convergence log

- **v1 → v2 (round 1: Forge/systems, Prism/fidelity, Flint/ops — all REVISE):** dependency inversion to substrate-first (build order = walking skeleton); workspace split into source-of-truth + two materialization contexts with live-state protection and `der sync`; model-slot indirection making the DeepSeek pin materializer-enforced; trace contract corrected to exact NexAU filenames/span shapes with "openai"-named LLM spans, converter relocated into the der agent's post-run hook, golden fixtures + strict mode; harbor pin decision made explicit (fork-of-fork registration, PATCHES.md targeting zero evolve.py patches, upstream qwen_code.py as reference); V1 component contract cut to 4 non-executable types with the 8-type table as roadmap; budget rebuilt on provider prepaid cap + actuals watchdog (projected-cost model deleted); suites as frozen ID lists + disjoint holdout gate on promotion; error taxonomy + incomplete-iteration rule; runs namespacing + flock + separate runner clone + `research-runs` branch; dashboard conflict-proofed (fixed SVG paths + DASHBOARD.md); promotion simplified to a hash-verifying script with human diff review as the named content boundary; ops floor added (systemd, notify shim with cost, janitor, preflight/doctor, rollout isolation, runbook); cost model grounded ($10–50/iteration, overnight unit, overlay defaults pinned); ADB partial-open disclosure; rollback semantics corrected (falsification automatic, reversal agent-executed, snapshot fallback).
