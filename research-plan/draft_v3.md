# der auto-research loop — Stage 1 architecture (v3 — convergence candidate)

Status: integrates adversarial rounds 1 (Forge/systems, Prism/source-fidelity, Flint/ops) and 2 (Vex/red-team, Sage/readiness). Stage 2 (expansion into an implementation plan for an executing agent) begins only after owner approval of this document.

## 0. Purpose

Stand up an automated research loop around the der harness (Qwen Code base) by adapting the official AHE codebase, so that:

- the owner's **own hypotheses** run through a rollout + scorecard + verdict pipeline (A/B against baseline) from day one,
- the harness can then be **evolved autonomously** (AHE evaluate → analyze → improve, unattended, resumable, budget-capped),
- every run produces a **comparable scorecard** (pass rate, tokens in/out, cost, wall-clock, turns) feeding the public dashboard,
- **DeepSeek v4 pro is the pinned model for every research-loop role** — enforced at the network boundary, not by trusting workspace content.

## 1. The architecture in three sentences

1. **The substrate is the product:** materializer + der harbor agent + trace converter + scorecards + `research` CLI + dashboard form a free-standing eval pipeline, independently testable, shipping owner value (hand-written A/Bs) before any autonomy exists.
2. **The inherited AHE loop (`evolve.py`) is a client of that substrate**, consuming it purely through its config seams (`harbor.agent`, `source_config_dir`, `${LLM_*}` env) — verified against source: harbor invocation is fully config-driven and the workspace layout is a bare `copytree` with no hardcoded component names.
3. The agent-under-test swap is **one role behind two adapters plus prompt retargeting**: a der harbor agent (workspace → Qwen Code, registered in-tree in our harbor fork), a qwen→NexAU trace converter (inside the agent's post-run hook), and der-flavored evolve/explore prompts replacing the NexAU-specific ones.

## 2. Load-bearing facts from the source audits

- **Seam verified:** `_build_harbor_cmd` emits agent name, env, and `--ak config_path={workspace}/agent.yaml` entirely from config, as a plain `["harbor", "run", ...]` argv (which makes a PATH shim possible — D10); `init_workspace` is `copytree` + `git init`; the seven NexAU component names appear nowhere in `evolve.py` logic — component semantics live in the evolve-agent prompts/skills, which we retarget.
- **Runs path is hardcoded:** evolve.py writes `research/experiments/<run-id>/runs/iteration_NNN/` (`EXPERIMENTS_DIR` is a module constant, no config seam) — the layout in D10 follows this reality.
- **Harbor pin is load-bearing:** AHE pins `Curry09/harbor-LJH` (16 ahead / 920 behind upstream `harbor-framework/harbor`; incompatible agent base API). Its qwen agent is a 68-line trace-blind stub; **upstream's `qwen_code.py` (348 lines) is the reference implementation** (session JSONL capture, ATIF trajectory, per-call token usage). Custom agents on the pin require in-tree registration (AHE's own pattern for `nexau`).
- **Trace contract is strict:** `evolve.py` + evolve-agent prompts hardcode `agent/nexau_in_memory_tracer[.cleaned].json` (NexAU span-tree shape); ADB's `is_llm_span` counts only spans **named** with "openai"/"gpt"/"anthropic"/"gemini"/"llama" and OpenAI-completion-shaped outputs — qwen/deepseek are not keywords.
- **Attribution needs nothing from traces:** flip attribution consumes the evolve agent's `change_manifest.json` + harbor's `verifier/reward.txt`. A trial with **no** `reward.txt` is already classified `exception` by evolve.py and excluded from real flips — der's error taxonomy maps onto this existing mechanism (D6). Falsification verdicts are automatic; per-file rollback is executed by the Evolve Agent per prompt policy; automatic full-workspace rollback to best-ever snapshot is the fallback.
- **Qwen Code emits per-call token usage in three forms** (chat-recording session JSONL `usageMetadata`; `--output-format json`; OTLP telemetry) — no metering proxy needed for rollout metrics.
- **Upstream footguns (verified defaults):** `max_iterations: 100`, both timeouts unlimited, Feishu-only notify, iteration-granular resume, zero cost accounting, `wait_for_harbor` timeout falls back to **stale existing job dirs** ("Using existing results after timeout") — fenced in D10. Host keeps NexAU + Python ≥ 3.13 + uv; tmux is dev-only (D9 runs the loop under systemd directly).
- **ADB is partially open-source** (bundled `agent_debugger_core`; works self-hosted with DeepSeek) — disclosed publicly; license check in Stage 2.

## 3. Decisions

### D1. Vendor AHE as `research/`; one uv project; plain copy + `UPSTREAM.md`

- AHE files live directly under `research/` (pinned commit recorded in `UPSTREAM.md`; MIT attribution kept). **der-new code is a package at `research/der/`**; the vendored `pyproject.toml` is extended so the `research` CLI can import `evolve.py` internals (`run_harbor`, `compute_stats`) — reuse, don't reimplement. Upstream re-sync diffs exclude `der/`, `experiments/` (run outputs), `runs/`, and der overlays.
- Host prerequisites: Python ≥ 3.13, uv, Docker, Node (Qwen Code), NexAU (host-side — the evolve/explore agents keep using it). tmux only for interactive dev sessions.
- The public notebook discloses the partially-closed ADB component.

### D2. Harbor: stay on AHE's pin; der agent registered in our fork; qwen shipped as a vendored tarball

- Fork `Curry09/harbor-LJH` → **`der-harbor`**; register the der agent **in-tree** (`agents/installed/der_qwen.py` + one enum line), mirroring AHE's `nexau` registration. The agent ports upstream `qwen_code.py` mechanics onto the fork's base API: workspace upload via `environment.upload_dir` in `setup()`, host-side materialization before upload, fresh-HOME isolation, run, then trace conversion + metrics extraction in `populate_context_post_run`.
- **Install mechanism (V1):** per-trial install of the pinned `@qwen-code/qwen-code@<version>` **from a vendored tarball uploaded into the trial** — no npm-registry dependency at rollout time (100 registry installs/iteration at a 2% flake rate would stall the unattended loop most nights). Prebaking qwen into suite images is a named later optimization; `force_build: false` governs task-env image caching only and is orthogonal.
- **Code ownership / dependency direction:** materializer and converter live in the `research/der` package; **der-harbor depends on `research/der`** (agent code runs host-side and imports it directly). One direction, no cycles.
- **`PATCHES.md` ledger** governs `evolve.py` divergence: every patch recorded with rationale; **target: zero entries** (registration, locking, budget, and notify are all solved outside the loop — D9, D10, D13). Upstream-harbor migration stays a priced, deferred option.

### D3. Substrate-first; the `research` CLI is the primary interface

- One CLI, small modules: `research smoke` (frozen 5-task list, k=1, <15 min, ~$1), `research eval <workspace> [--suite S] [--k N]`, `research diff <scorecard-A> <scorecard-B>`, `research ab <workspace-A> <workspace-B>` (sugar: two evals + diff; sides are explicit workspace paths), `research promote <run-id>`, `research sync` (owner-side daily render — D4), `research dashboard`, `research postprocess`, plus preflight/doctor.
- `research diff` prints the per-task flip table + a **paired one-sided sign test** on the pass-rate delta, and labels the verdict `improved / regressed / inconclusive`; comparability guards per D7.
- **Baseline registry:** `research/baseline.json` — a committed pointer {scorecard path, workspace_hash, suite versions} naming the *current baseline*. It is updated **in the promotion commit itself** (D12) and is what "vs baseline" means everywhere (scorecards, holdout gate, dashboard deltas).
- `evolve.py` enters last (Section 5), at toy scale, as a config-level client.

### D4. Component workspace: one source of truth, two materialization contexts, disjoint managed/live targets

- `harness/` (repo root) is the **workspace source** — managed components only, never a runnable config itself.
- **Materializer:** pure function `(workspace, bindings, context) → rendered Qwen Code config`, context ∈ {rollout, daily}. Rollout renders into the trial's project dir (invoked host-side by the der agent pre-upload); daily renders via **`research sync`** into the user-level Qwen config location outside the repo.
- **Managed and live state get disjoint render targets:** managed skills render into a namespaced subdir (`skills/der-managed/`) that sync owns entirely; the memory seed renders to a der-managed file included via Qwen's context-import mechanism (Stage-2 verifies import support on the pinned version; fallback: sync rewrites only a fenced `<!-- der-managed -->` region). Auto-Memory, auto-learned skills, and session state (the **live-state list**, versioned per qwen release and re-checked by doctor) are never written by sync. Feeding live state back into `harness/` is a manual, deliberate act. Promoted improvements therefore actually ship without ever clobbering live state.
- **V1 component contract (4 types):** `system/QWEN.md`, `agent.yaml` (schema-validated; see D5), `skills/`, `memory/LongTermMEMORY.md`. The materializer **rejects everything else loudly**. The 8-type target schema (adding `tool_descriptions/`, `tools/` = MCP, `middleware/` = hooks, `sub_agents/`) is roadmap; executable classes phase in later behind: vetted-catalog-only MCP references, hooks as diffable in-workspace scripts, and promotion diffs rendering executable content under a top-most "EXECUTES ON YOUR MACHINE" section.
- Evolve-agent prompt retargeted to exactly the implemented der component types (replacing `nexau-evolution-guide`); explore agent's `code_sources` swap to Qwen Code docs + der docs **minus** `runs/`, `DASHBOARD.md`, `experiments/` (holdout-leak exclusions written into the overlay now, though explore stays off at V1 — D9).

### D5. Model pin: allowlist rendering + a pinning proxy at the network boundary

The slot design stays; its enforcement is rebuilt (round-2 blocker: free-text scanning is undecidable and the trial container held a live key next to a yolo shell):

- **Slots:** workspace files reference model slots only (`primary`, `subagent-default`, named). Binding maps are a materializer input: the **research binding is a committed overlay file**; the **daily binding lives outside the repo** next to the daily config (it legitimately contains the owner's private model mix/endpoints) and is read by `research sync` at render time.
- **Field-allowlist rendering (decidable), not literal-string scanning:** structured config surfaces (`agent.yaml`, later `sub_agents/`, `tools/`) render through an enumerated schema; request-shaping fields (model, endpoint, api_key, temperature, top_p, max_tokens — everything in the request body except messages/tools) are **not renderable from workspace content** and come only from context bindings; `${...}` interpolation from workspace values is banned. Prose files (QWEN.md, skills) are out of validation scope — prose cannot bind a model, because bindings only exist outside the workspace. `agent.yaml`'s evolvable-vs-pinned parameter enumeration is a Stage-2 deliverable (starting set: evolvable = qwen behavior toggles, session-turn caps; pinned = every request-shaping field).
- **The wall is the network, not the filesystem:** trial containers receive **no real provider key**. The rendered config points qwen at a **host-level pinning proxy** (one systemd service, reached via the container's host gateway); the proxy injects the real key and hard-sets/rejects the `model` field. Evolve-authored free text instructing the agent to curl the provider directly fails (no key in the container); traffic through the proxy gets the pinned model regardless of what any workspace content says. This is a narrow, rollout-path-only component (key isolation + model pinning — **not** metering; session JSONL remains the trace/metrics source).
- **Detection layer:** converter strict mode asserts observed per-event `model` == binding; the proxy appends `{timestamp, run/role tag, observed model}` to an observation log, and postprocess joins that log into scorecards — the scorecard's `model` field is recorded from **proxy-observed** values, not from config.

### D6. Trace + metrics contract; error taxonomy mapped onto evolve.py's own mechanism

- The **qwen→NexAU converter** runs inside `der_qwen.populate_context_post_run` (evolve.py has no post-eval seam; this is also where upstream qwen_code.py builds its trajectory). Input: chat-recording session JSONL (copied from the trial), `usageMetadata` per assistant event as metrics source (tolerating absent cached/thoughts fields from OpenAI-compatible DeepSeek); OTLP file telemetry secondary. Output: NexAU InMemoryTracer **span tree** at `agent/nexau_in_memory_tracer.json` + payload-trimmed `.cleaned.json`; LLM spans **named to contain "openai"** with OpenAI-completion-shaped outputs incl. `usage`; tool spans `type: "TOOL"`. Satisfies `adb ask`, `extract_agent_behavior_stats`, and the prompt-baked paths with zero evolve.py changes.
- **Golden fixtures + strict mode:** committed real session logs with expected outputs as unit fixtures; strict mode fails the trial on missing usage fields (a converter emitting silent zeros makes ADB analyze fiction) and on observed-model ≠ binding (D5).
- **Error taxonomy = evolve.py's existing exception path:** der `errored` ≡ the pin's `exception` class. Mechanism: the der agent surfaces provider/infra faults by **raising** (trial ends with `exception.txt`, no `reward.txt`) — never by letting a fault land as `reward.txt = 0.0`, which would count as a real fail and poison attribution. Enumerated fault list in Stage 2; Section 9 verifies the mechanics on the pin. An iteration missing non-errored results for any task×k is `incomplete`: postprocess skips its scorecard and the watchdog re-queues it once (bounded), then alerts.
- **`turns` defined:** count of assistant-message events (model-call rounds) in the session log.

### D7. Scorecards, lineage, comparability, and the ship gate

- **Scorecard schema (immutable once written):** run id; suite id+version + dataset reference; k; workspace **content hash** (canonical tar: sorted paths, zeroed mtimes) + git SHA when one exists; **proxy-observed** model string + provider base + pricing-table version; qwen-code version; materializer version; **der-harbor (agent) version**; per-trial `passed/failed/errored` rolled up per-task × k; tokens in/out (+cached), cost, wall-clock, turns recorded **per-trial, aggregated per-task, then run-aggregate**; named baseline ref (from `research/baseline.json`).
- **Comparability:** same suite version + same k → comparable; qwen-code or materializer-major version mismatch → diff still renders but under a loud **CONFOUNDED** banner; suite/k mismatch → refuse.
- **Seeding rule:** every evolve run and every eval seeds from `harness/` at a recorded git SHA; loop lineage is ephemeral; promotion branches are cut against that same seed SHA.
- **No eval, no ship — enforced at both gates:** `research promote` verifies candidate-tree hash == scorecard `workspace_hash` and refuses when `harness/`@main has moved past the seed SHA (`--rebase-and-reeval` re-seeds and at minimum re-runs the holdout). **`research sync` re-hashes `harness/`@HEAD and refuses when that hash has no scorecard** (`--force` escape for deliberate owner-only edits) — closing the merge-time hole where evaluated-branch ⊕ owner-edits produced a never-evaluated shipped state.
- **Cold start:** `research eval harness/` runs before the first evolve run (dashboard baseline point + attribution floor). **Verdict timing:** iteration N's scorecard exists at N; its flip-attributed verdict lands at N+1; the dashboard fills verdict cells asynchronously.

### D8. Suites: frozen ID lists, a guarded holdout, an exact gate

- `der-suite-v1` (~50 task IDs, seeded random from `terminal-bench@2.0`, one-line provenance), `der-holdout-v1` (~30 disjoint IDs, never referenced by the loop, never analyzed by ADB), `der-smoke-v1` (5 IDs, disjoint from holdout) — passed to harbor via `-t` filters; local dataset mirror only if the upstream reference proves mutable (Stage-2 check).
- **Disjointness is an invariant, not an assertion:** a committed pairwise-disjointness test across all versions of {smoke, suite, holdout} runs in preflight and CI; suite files carry a header naming the holdout they exclude.
- **Holdout leak controls:** holdout scorecards are committed **aggregate-only** (per-task detail stays in gitignored run dirs); the explore-agent source allowlist excludes run/notebook artifacts (D4); **adaptive-reuse budget:** after 5 failed promotion attempts against the same holdout, rotate to `der-holdout-v(n+1)` and re-baseline.
- **Gate predicate (exact):** promotion requires a fresh holdout scorecard with **point pass-rate delta ≥ 0 AND not conclusively negative** (one-sided paired sign test at α = 0.05 does not reject "no worse"). `inconclusive`-but-nonnegative passes — at 30 tasks × k=2, requiring CI-excludes-zero would block essentially all promotions. "Fresh" = same workspace_hash as the candidate, current holdout version, baseline unchanged since. `research promote` does not auto-run the eval; it refuses with the exact command to run (cost and lock stay explicit).
- k=2 default; `research ab --k 4` for tighter noise bounds; occasional full-suite runs pre-adoption or for leaderboard fun.

### D9. Budget: prepaid wall, actuals meter, clean-stop watchdog; one process model

- **Hard wall:** DeepSeek prepaid balance / provider spend cap sized to the monthly budget — survives every local bug.
- **Meter:** cumulative actuals = rollout costs from scorecards + provider balance polled between iterations (captures ADB/evolve/explore overhead; balance-endpoint existence is a Section-9 check).
- **Process model (one answer):** the loop runs as `der-evolve.service` (systemd executes evolve.py/resume wrapper directly; `Restart=on-failure`; `OnFailure=` → notification). tmux is dev-only. **Ceiling stop is a state change, not a signal:** the watchdog timer runs `systemctl stop der-evolve.service` (clean stop ≠ failure → no restart loop) and writes a `COST_CEILING_REACHED` flag; the unit's `ExecStartPre` refuses to start while the flag exists (defends against reflexive manual restarts); the notification carries the flag and spend figures.
- **Overlay defaults that must ship:** `max_iterations: 10`; both timeouts finite; `best_of_n: off` (×N cost multiplier; a later deliberate experiment); `explore_agent: off` at V1; `force_build: false` with pre-built suite images.
- A per-role metering proxy remains a named later option; the D5 pinning proxy deliberately does not meter.

### D10. Runs layout (source-true), locks, single committer, immutable artifacts

- **Evolve runs live where evolve.py puts them:** `research/experiments/<run-id>/runs/iteration_NNN/` (`EXPERIMENTS_DIR` is a hardcoded constant; no patch). CLI runs live at `research/runs/adhoc/<exp-id>/`. Postprocess scans both. Naming disambiguation: `research/experiments/` = AHE run outputs; top-level `experiments/` = the public notebook.
- **Locking, two mechanisms:** (1) a **run-scoped advisory flag** held by `der-evolve.service` — adhoc full-suite runs are refused while an evolve run is active; only smoke-class runs may `--queue` into inter-iteration gaps; (2) a **`harbor` PATH shim** in the runner environment owns an flock around every actual harbor invocation (evolve.py builds a plain `["harbor", "run", ...]` argv — the shim covers both callers with zero patches), acquiring with a bounded wait and **failing fast** past it, so a busy lock surfaces as a clean iteration error — never as a timeout, because `wait_for_harbor`'s timeout path falls back to stale existing job dirs ("Using existing results after timeout") and would feed attribution fiction.
- **Job-dir hygiene:** the scorecard builder reads the newest job dir **whose trial set is complete**; superseded/partial job dirs in an iteration dir are fenced/pruned at resume (Stage-2 pins the fork's resume/rerun semantics) so neither postprocess nor evolve.py's fallback can resurrect them.
- **The loop runs in its own clone** (`~/research-runner/der`), on a dedicated `research-runs` branch, merged opportunistically by the owner. **`research postprocess` is the sole committer** (cron-driven every ~10 minutes during runs — evolve.py has no iteration-end seam to invoke it; ticks and manual invocations share a repo-level flock): it (re)builds **missing or corrupt** scorecards only — **scorecards are immutable once written**; pricing/schema changes apply to new runs — regenerates dashboard artifacts, applies trace retention (keep last N iterations + digest-referenced traces; GC the rest — gitignored ≠ deleted), and runs the secret scrub (no keys/base-URLs in committed artifacts).
- Dashboard artifacts carry a `.gitattributes` merge driver (`ours`) + the rule "rerun `research postprocess` after any merge," killing cross-clone SVG conflicts.

### D11. Publication: dashboard v0 + notebook

- `research dashboard`: one idempotent script regenerating everything from committed scorecards. **V1 = pass-rate chart + cost chart (SVG) + experiment index.** SVGs at fixed paths (`docs/dashboard/*.svg`) embedded from README (README text almost never changes); full index in `DASHBOARD.md`, linked from README — honoring "README leads with a glanceable dashboard" without making README a conflict hotspot.
- Notebook unit: `experiments/EXP-NNN-slug.md` (hypothesis, setup/workspace diff, scorecard link, verdict) from a committed `TEMPLATE.md`. Holdout results appear aggregate-only (D8). ADB's partial-open status disclosed.

### D12. Promotion: exact-replacement script, human content-gate, loop never touches `harness/`

`research promote <run-id>` (run-id resolves to an evolve iteration or an adhoc exp): branch **from the run's seed SHA** → **exact replacement** of the managed tree in `harness/` (extraneous files deleted — the hash check verifies the whole tree) → verify evaluated-equals-promoted hash → verify the holdout gate (D8; refuses with the command to run if no fresh holdout scorecard exists) → update `research/baseline.json` in the same commit → commit with manifest + scorecard path → print "review the diff, then merge." The **promotion diff review is the content trust boundary** (materializer = shape boundary; tractable at V1 because the contract contains no executable classes). If `harness/`@main ≠ seed SHA: refuse, offer `--rebase-and-reeval`. The unattended loop never writes to `harness/`. After merge: `research sync` (gated by D7's ship-gate hash check) renders managed components into the daily config.

### D13. Ops floor (the 3am story)

- **systemd everywhere:** `der-evolve.service` (D9), the watchdog timer, the pinning proxy service (D5), optional night-window timer + `CPUQuota`/`Nice` (rollouts coexist with daily driving, degraded-but-supported; heavy runs default off-hours).
- **Notify shim:** ~10-line Feishu-format-compatible receiver forwarding to the owner's channel (ntfy/Telegram); AHE's notify stays unpatched; messages carry {iteration cost, cumulative cost, provider balance, ceiling flag}.
- **Preflight/doctor** on every CLI entry: Docker up; disk headroom; suite images present; suite/holdout/smoke disjointness test; provider key answers a 1-token ping; pinning proxy healthy; qwen version matches the adopted baseline's evaluated version (warn on skew); live-state list version matches the installed qwen release.
- **Janitor** at iteration end: prune exited containers/dangling images; trace GC per D10.
- **Runbook** (half page): loop dead → `systemctl status` → resume → restarts from iteration boundary (re-spends the interrupted iteration — documented). Acceptance tests: kill -9 mid-rollout → resume; ceiling → clean stop, flag blocks restart, notification arrives.
- **Rollout isolation:** fresh HOME, injected env only, **no real provider key in containers** (D5), never the owner's personal qwen state.

## 4. System diagram

```
                der repo (public, MIT) ────────────────────────────────────────────────┐
                │                                                                       │
 owner ──► research CLI (primary): smoke/eval/ab/diff/promote/sync/dashboard/postprocess│
                │            └── run-flag + harbor PATH-shim flock ──┐                  │
 autonomy ► der-evolve.service (systemd): evolve.py, config client ──┤                  │
                │                                                    ▼                  │
                │                                harbor (der-harbor fork pin)           │
                │                                    │ trial containers:                │
                ▼                                    │  qwen-code (vendored tarball,    │
        Evolve Agent (DeepSeek v4 pro)               │  pinned), fresh HOME, NO KEY,    │
        edits workspace copies + manifests           │  rendered workspace              │
                │                                    ▼                                  │
                │                          host pinning proxy (systemd) ──► DeepSeek v4 pro
                ▼                                    │  key injection + model hard-pin  │
        ADB digests (DeepSeek)  ◄── der agent post-run hook: session JSONL → NexAU span │
                │                    tree + usageMetadata → metrics (strict mode)       │
                ▼                                                                       │
   research/experiments/<run>/runs/… + research/runs/adhoc/… ──► postprocess (sole      │
   watchdog timer: spend actuals,                                committer, idempotent) │
   systemctl stop + ceiling flag                                  ├─ immutable scorecards
                │                                                 ├─ docs/dashboard/*.svg + DASHBOARD.md
                ▼                                                 └─ trace GC + secret scrub
 harness/ (workspace SOURCE, 4 types, slots only) ◄── research promote (seed-SHA branch,
    │                                                  exact replace, hash + holdout gate,
    └─► research sync (ship gate: hash must have a scorecard)      baseline.json update)
            └─► daily Qwen config (outside repo; der-managed namespaces; live state untouched)
```

## 5. Build order (walking skeleton — Stage 2's milestone spine)

0. **Seam-kill spike (~$1, no code):** one terminal-bench task via harbor on local Docker with a built-in agent (proves `env: docker` on the pin); `qwen -p` headless against DeepSeek by hand; confirm session JSONL + per-call usage; confirm container→host networking for the future proxy.
1. **Minimal der harbor agent** (der-harbor fork): vendored-tarball qwen install + one-file workspace stub; one task, k=1. Proof: **raw qwen session JSONL lands in the trial's agent logs dir**.
2. **Converter + scorecard** over that trace; golden fixture committed; strict mode on. Proof: converted span tree + numbers match the raw log by hand.
3. **`research smoke` / `research eval`**: frozen 5-task list end-to-end. (The owner-facing CLI exists from here on.)
4. **Dashboard v0** from committed scorecards (validates the schema before anything depends on it).
5. **Materializer v1 (4 types, allowlist rendering, slots) + pinning proxy + `research diff`.** Proof: a real hand-written A/B end to end, containers holding no key. **Owner value ships here.**
6. **ADB integration** (DeepSeek-pinned) over smoke-suite traces. Proof: digest claims link to real trace events.
7. **evolve.py at toy scale:** 5-task suite, `max_iterations: 2`, best_of_n/explore off, **retargeted evolve-agent prompt + der overlay (incl. der-schema `code_agent_patch` replacement)**. Proof: manifests written; attribution binds predictions to observed flips; rollback fires on a (contrived, injected) falsified prediction; kill -9 mid-rollout → resume works; superseded job dir fenced.
8. **Production V1:** 50-task suite + holdout + disjointness test, k=2, systemd units + watchdog + janitor + notify shim, cold-start baseline scorecard, then a real 10-iteration run.

## 6. Lifecycle walks

**(a) Autonomous evolve iteration:** preflight passes → `der-evolve.service` (runner clone, run flag held) seeds workspace from `harness/`@SHA → harbor (via shim lock) runs suite k=2 with the der agent — containers keyless, model pinned at the proxy; traces + metrics emitted per-trial → attribution binds the previous manifest's predictions to observed flips (errored ≡ exception excluded); Evolve Agent executes per-file rollbacks per policy (snapshot rollback as fallback) → ADB distills evidence → Evolve Agent writes edits + manifests → postprocess (sole committer) emits the immutable scorecard, regenerates dashboard, GCs traces, commits to `research-runs` → stop on target / max_iterations / ceiling (clean systemctl stop + flag).

**(b) Owner hypothesis (A/B):** branch `harness/`, hand-write the change + `experiments/EXP-NNN.md` → `research ab ws-A ws-B` (refused during an evolve run unless smoke-class; both sides seeded + hashed) → `research diff` prints flip table + sign test (`improved/regressed/inconclusive`; CONFOUNDED banner on version mismatch) → owner records the verdict → dashboard regenerates → promote if warranted.

**(c) Promotion + sync:** `research promote <run-id>` (seed-SHA branch, exact replace, hash check, holdout gate, baseline.json update) → owner reviews the diff (content boundary) → merge → `research sync` (refuses unevaluated HEAD without `--force`) renders managed components into the daily config; live state untouched.

## 7. Cost model (planning band; pricing table versioned in Stage 2)

At DeepSeek-class pricing (~$0.3–0.6/M in, $1–2/M out, cached ~10× cheaper): rollout ≈ $0.05–0.35 → **$5–35 per 100-rollout iteration**; ADB ≈ $3–8; evolve agent ≈ $1–3 → **≈ $10–50 per iteration**, 3–6 h wall-clock at n_concurrent 4–8 (an iteration is an overnight unit). Multipliers kept visible: `max_iterations` (pinned 10), `best_of_n` (×N, off), timeouts (finite in overlay). Continuous operation ~$300–1,500/mo; the prepaid provider cap is the guardrail that makes every other guard merely convenient.

## 8. Risks

1. **Converter fidelity:** golden fixtures, strict mode, observed-model assertion, ADB acceptance at step 6.
2. **Model-pin subversion:** solved at the network boundary (keyless containers + pinning proxy); allowlist rendering closes config surfaces; free text is explicitly not trusted and doesn't need to be.
3. **Harbor fork drift:** accepted (AHE's tested substrate); exposure isolated in one agent file; upstream migration priced, not planned.
4. **Suite overfitting / holdout leakage:** holdout gate + disjointness invariant + aggregate-only publication + explore-source exclusions + rotation budget.
5. **Noise at k=2:** sign-test verdicts with explicit `inconclusive`; `--k 4` escalation; errored ≡ exception taxonomy keeps infra noise out of attribution.
6. **evolve.py coupling beyond enumerated seams:** narrowed by two audits to trace paths/shapes, registration, notify format, runs path, timeout-fallback behavior — all addressed without patches; `PATCHES.md` if reality disagrees.
7. **Concurrency/state corruption:** run flag + shim flock + sole-committer postprocess + immutable scorecards + job-dir fencing + separate runner clone.
8. **Cost blowout:** prepaid wall + actuals watchdog + clean-stop flag + overlay defaults.
9. **ADB opacity/licensing:** disclosed; license check in Stage 2; replaceable behind `adb ask`'s CLI surface as a later project.
10. **Qwen nightly cadence:** version pinned per evaluation; CONFOUNDED banner on cross-version diffs; doctor warns on daily/evaluated skew; upgrades run as experiments.

## 9. Stage-2 verification list (live-install checks)

1. Harbor pin smoke: flag surface matches `_build_harbor_cmd`; job-dir naming regex; trial-dir layout; der agent instantiation via in-tree registration with `--ak config_path=...`.
2. `env: docker` end-to-end on the pin (build, `upload_dir`, log download) + **vendored-tarball qwen install inside a trial** (verify the tarball bundles its runtime deps and that node/npm exists or is provisioned in task containers; prebaked images remain the fallback) + **container→host networking to the pinning proxy**.
3. Real NexAU trial dir: pin the exact in-sandbox `.cleaned.json` byte-shape before finalizing the converter.
4. `adb ask` acceptance: synthetic qwen→NexAU trace registers LLM/tool spans, token sums, drill-down.
5. Pinned qwen flags/behavior: `--chat-recording` (or default session writing), `--auth-type openai --openai-api-key/--openai-base-url`, `--yolo`, turn/wall-time caps; session path layout; `usageMetadata` population via the proxy to DeepSeek (tolerate absent cached/thoughts); **context-import mechanism for the memory seed** (else fenced-region fallback).
6. Exact Qwen project-config paths for the 4 V1 component types on the pinned version.
7. Harbor `result.json` token/cost context fields on the pin (cheap secondary scorecard source).
8. **Errored mechanics:** an agent-raised fault yields `exception.txt` with no `reward.txt` (→ classified `exception`, excluded from real flips); confirm provider faults cannot terminate as `reward.txt = 0.0`.
9. **Resume/rerun semantics on the pin:** superseded job dirs (fence/prune behavior); whether errored trials are retried natively.
10. **DeepSeek balance/usage endpoint** for the watchdog meter (account-type specific).
11. ADB `_source` license terms inside an MIT monorepo.
12. Server prereqs: Python ≥ 3.13, uv, Docker capacity at n_concurrent 4–8; DeepSeek rate limits at that concurrency; dataset reference immutability (else mirror).

## 10. Convergence log

- **v1 → v2 (round 1 — Forge/systems, Prism/fidelity, Flint/ops; all REVISE):** substrate-first inversion; workspace source-of-truth with two materialization contexts + live-state protection; model-slot indirection; exact NexAU trace contract (filenames, "openai" span naming, converter inside the agent hook, golden fixtures/strict mode); harbor pin decision + in-tree registration + PATCHES.md; V1 contract cut to 4 non-executable types; budget rebuilt on prepaid wall + actuals; frozen ID suites + holdout gate; error taxonomy; runs namespacing/locks/runner clone; dashboard conflict-proofing; promotion simplified with hash gate; ops floor (systemd, notify shim, janitor, preflight, isolation, runbook); cost band grounded; ADB disclosure; rollback semantics corrected.
- **v2 → v3 (round 2 — Vex/red-team REVISE, Sage/readiness CONVERGED-WITH-PUNCH-LIST):** model pin moved to the network boundary (keyless trial containers + host pinning proxy; allowlist rendering replaces undecidable literal scanning; proxy-observed model in scorecards); ship gate added at `research sync` (merge-time hole closed) + promote refuses on moved main; watchdog stop became `systemctl stop` + ceiling flag (restart-flapping killed; process model unified on systemd, tmux dev-only); flock realized as a `harbor` PATH shim + run-scoped flag with fail-fast (stale-job-dir timeout fallback fenced; job-dir hygiene rule); qwen shipped as vendored tarball (registry-flake stall killed); holdout disjointness made an invariant (test in preflight/CI, aggregate-only publication, explore-source exclusions, rotation budget); managed/live render targets made disjoint (namespaced skills, imported memory seed); comparability extended to qwen/materializer versions (CONFOUNDED banner); scorecards immutable; postprocess sole committer; runs path corrected to evolve.py's hardcoded `research/experiments/<run>/runs/`; baseline registry (`research/baseline.json`) named; exact holdout-gate predicate stated; promotion semantics pinned (seed-SHA branch, exact replace, no auto-eval); `der sync` folded into `research sync`; packaging/layout/dependency-direction stated; skeleton proofs corrected; Section 9 extended (errored mechanics, balance endpoint, tarball install, proxy networking, import mechanism, resume semantics).
