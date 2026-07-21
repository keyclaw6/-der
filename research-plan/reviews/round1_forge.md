# Round 1 review — Forge (systems architecture)

Scope: draft_v1.md against context.md. Fixed constraints (AHE base, DeepSeek v4 pro everywhere in the loop, Qwen Code runtime, two-stage plan) are respected; everything else is fair game.

---

## BLOCKERS

### B1. "This same workspace directory IS the daily-driver configuration" is false as written, and dangerous
D3 claims the workspace at adopted baseline *is* the daily-driver config; the diagram says `harness/ = adopted baseline workspace`; lifecycle (c) says the daily driver runs "Qwen Code reading `harness/` materialized config." Those are three different designs and the draft never picks one. Concretely broken:

- **Source vs rendered ambiguity.** Is `harness/` the workspace source (needs the materializer to run — when? on merge? by whom?) or the rendered Qwen Code config (then it is a derived artifact that drifts from the source)? An implementing agent will guess, and either guess corrupts the "evaluated state = shipped state" story.
- **Config-layer mismatch.** Rollouts materialize into the *task container's project directory* (project-level Qwen config). The owner daily-drives across many repos, so daily-driver components must land in the *user/global* Qwen config layer, which has different semantics (global QWEN.md vs project QWEN.md, global vs project MCP/hooks). "One deployment, two purposes" silently assumes one materialization target; there are two, with different shapes.
- **Live-state clobber + privacy leak.** Qwen Code Auto-Memory and Auto-Skills *write into their own config at runtime*. If the daily driver's config lives inside `harness/` in the public MIT repo, months of accumulated personal memory (a) sit one `git add -A` away from publication, and (b) get overwritten by the next promotion re-materialization. In containers this self-modification is discarded; on the daily driver it is precious state the draft has no story for.

**Failure in practice:** first promotion after a few weeks of daily driving either wipes the owner's accumulated memory or the owner stops merging promotions to protect it — the loop and the daily driver permanently fork. → Fix F1.

### B2. The DeepSeek v4 pro pin is asserted in D6 but not enforceable through the D3 workspace
`agent.yaml` (workspace, evolve-agent-writable) carries "model, params, mode flags"; `sub_agents/` definitions in Qwen Code can specify per-subagent models. Nothing stops the Evolve Agent from "improving" pass rate by editing a model string — the single most rewarding reward-hack available to it — which un-pins the loop and silently invalidates every scorecard comparison. D6 ("nothing in the research loop calls any other model") and D3 (evolve agent edits agent.yaml params) directly contradict. Same class of leak: D6 pins temperature 0, but agent.yaml "params" are evolvable. → Fix F2.

### B3. The materializer is called "the single trust boundary" but only checks shape; the actual content boundary is an unnamed human
`middleware/` = Qwen Code Hooks = shell commands executed on the host. `tools/` = MCP server definitions = arbitrary processes. In rollout containers that's acceptable (disposable sandbox). But the promotion flow carries evolve-agent-authored hook/MCP code into `harness/` and onto the owner's server, executing daily with the owner's credentials — and the only gate is a one-person PR review of LLM-generated code, which the draft never even names as the boundary. The trust-boundary claim as stated ("validates shapes and fails loudly on unknown files") is not the property that matters; a well-shaped hook that curls `$LLM_API_KEY` somewhere passes it. → Fix F3.

### B4. Two of the draft's own decisions are unimplementable without patching the evolve.py monolith the draft promises not to touch
D2: "We do not touch evolve.py's loop." But:
- D8's budget guard — "the loop refuses to start an iteration whose projected cost exceeds the ceiling" — requires a pre-iteration hook *inside* evolve.py's loop. No such seam is documented.
- D9's "dashboard regenerates on verdict; committed with the verdict" and D4's metrics-extraction step have no specified integration point. Scorecard writing must happen per-iteration during an unattended multi-day run; nothing in inherited AHE does it.

An implementing agent will resolve this the obvious wrong way: patch evolve.py, forfeiting upstream merges and creating exactly the coupling risk the draft lists as Risk 1. → Fixes F4, F5.

### B5. No baseline lineage rule: the loop's workspace lineage and `harness/` diverge by design, and nothing reconciles them
Where does an evolve run's iteration-0 `input/` workspace come from? The draft never says. Two lineages exist: the loop's `runs/iteration_NNN` chain and the human-gated `harness/`. The owner *will* hand-edit `harness/` (it's their daily driver; they'll tweak QWEN.md at 11pm), and the owner may merge promotion PRs out of order or not at all. If the next run seeds from the last run's final state, hand-edits never enter the loop and promotion PRs conflict forever; if it seeds from `harness/`, that must be stated because it discards unmerged loop progress. Related: nothing guarantees the promoted state is byte-identical to an evaluated state — "workspace git hash" in the scorecard is undefined for states that were never committed as git objects mid-run. → Fixes F6, F7.

---

## MAJORS

### M1. Trace/metrics/budget should be unified on a metering proxy — the draft's "last resort" is actually the strongest primary design
Risk 3 treats an OpenAI-compatible logging proxy as a last resort and bets primary on Qwen Code session-log formats — an *unstable internal surface of a nightly-release project* (Risk 7 admits it moves fast). The wire protocol is the stable surface: a passthrough proxy captures full request/response message arrays (turns + tool calls reconstructible = the trace), provider-truth token usage (= metrics), and — because AHE routes *everything* through one `LLM_BASE_URL` — a single metering point for rollouts, ADB, Evolve Agent, and explore agent, which is precisely what the budget guard needs and what B4 lacks. One ~200-line component replaces three under-specified mechanisms. → Fix F5.

### M2. A pinned 50-task suite optimized against for up to 100 iterations guarantees overfitting; promotion has no generalization gate
The evolve loop will memorize suite-specific hacks into `skills/` and `LongTermMEMORY.md`. D7's "full suite occasionally" is not a gate. Without a held-out set, the daily driver inherits benchmark-shaped tricks that do nothing for real work — the opposite of the project's point. → Fix F8.

### M3. No error taxonomy: at k=2, one DeepSeek 429 poisons flip attribution
A provider outage or infra failure mid-rollout is indistinguishable from a workspace-caused failure in the draft's scorecard schema. With k=2, a single errored rollout flips a task's signal and AHE's attribution will "detect" a regression, revert a good edit, and record a false verdict on the public dashboard. Partial iterations (crash at task 37/50) have the same problem: the schema assumes complete rows. → Fix F9.

### M4. Two front doors, one box, no lock: concurrent evolve + `research ab` runs race on compute and on `runs/`
n_concurrent 4–8 is sized to the whole box; a mid-iteration owner A/B doubles container load, interleaves writes into a shared `runs/` layout (iteration_NNN numbering collides), and triggers two concurrent dashboard regenerations. Separately, daily-driver use during rollouts contends on CPU/RAM/Docker daemon/disk, and the draft has no trace-retention policy (gitignored ≠ deleted; ~10M trace tokens/iteration fills a disk in weeks). → Fixes F10, F11.

### M5. Unattended runs must commit to a repo the owner is actively working in; README is a guaranteed conflict hotspot
Who commits scorecards/manifests during a multi-day unattended run, to which branch, in which clone? The dashboard regenerates README content — the single most owner-edited file — on every verdict. "One repo = one deployment" conflates repo with working copy: the loop and the owner sharing one working tree is a git-index race. → Fix F12.

### M6. Materializer runs 100× per iteration in the wrong place
D2 puts materialization in the container startup shim: a workspace with one bad file fails identically inside 100 containers *after* the iteration's cost is committed, and per-image materializer copies invite version skew. Validate and render once, pre-flight, in the driver; ship rendered config into containers. → Fix F13.

### M7. The draft's Risk-1 fallback is the correct primary structure (structural simplification)
`research eval/ab` (D5) already requires every substrate piece — materializer, der harbor agent, converter/proxy, scorecards, dashboard — with zero dependence on evolve.py. Build that as the free-standing layer; evolve.py is then *one client* of the substrate, consuming it purely through config at the documented seams (`source_config_dir`, `harbor.agent`, env). This is not a new component count; it is a dependency inversion that de-risks the 202KB monolith to "config consumer," makes the Stage-2 sequencing obvious (substrate shippable and testable before any evolve run), and means a deep-coupling discovery in the seam audit delays nothing except autonomy. → Fix F14.

---

## MINORS

1. **Scorecard schema is missing fields it needs to honor its own claims:** materializer version, Qwen Code version, pricing-table version, workspace *content hash* (see F7), per-task errored-vs-failed counts, run id, seed baseline ref. "Diffable within the same suite version" must also require same k.
2. **`force_build` on, per rollout, on one box** = repeated image builds × 50 tasks. Pre-build task images once per suite version; `force_build: false` in the der overlay.
3. **Verdict timing is N+1:** iteration N's scorecard exists at N, its flip-attributed verdict lands at N+1 (change_evaluation is next-round). Dashboard semantics must say charts plot scorecards at N and verdict cells fill in asynchronously, or the "committed with the verdict" wording misleads.
4. **A/B deltas at 50×k=2 will be read as signal when they're noise.** The `research ab` delta report must print a paired-bootstrap 95% CI over tasks on the pass-rate delta; the verdict template requires either CI-excluding-zero or an explicit "inconclusive" label.
5. **Cold start unstated:** `harness/` v0 is owner-authored; run `research eval harness/` once to produce scorecard-0 *before* the first evolve run, so the dashboard has a baseline point and attribution has a floor.
6. **Daily/rollout Qwen version skew:** daily driver on nightly, rollouts pinned. Stamp the qwen version in every scorecard; a `der doctor` check warns when the running daily version ≠ the version the adopted baseline was evaluated under.
7. **"Temperature 0 for rollout determinism" over-promises.** Providers are nondeterministic at t=0 and task envs add noise. Say "variance reduction"; forbid any downstream logic (caching, rollout skipping) from assuming determinism — k exists precisely because there is none.
8. **Secret hygiene rule missing:** committed artifacts (scorecards, manifests, analysis digests, proxy logs if F5 adopted) must be scrubbed of base URLs/keys; add a pre-commit scrub check in the postprocess step.
9. **Path ambiguity:** does AHE write `runs/` at repo top level or `research/runs/`? Pin it: `research/runs/` (AHE-native relative path, zero patching); `experiments/` stays top-level as the public notebook; dashboard scans `research/runs/**/scorecard.json`.
10. **Explore agent runs parallel to iteration 1 and costs real tokens** — include it in the budget projection and in the F5 proxy metering (per-role attribution), or the first iteration blows its ceiling mysteriously.

---

## PROPOSED FIXES

**F1 (for B1) — Split source-of-truth from materialization contexts; keep live state out of the repo.**
Reword D3's claim to: "one *source of truth*, two *materialization contexts*." Mechanism: `harness/` is workspace **source only** (managed components, seven classes + memory *seed*). The materializer takes `(workspace, context)` where context ∈ {rollout, daily}: rollout renders into the task container project dir; daily renders into the user-level Qwen config location **outside the repo** (exact paths pinned in Stage 2). Add a `der sync` command: after a promotion merge, re-render managed files into the daily location. The materializer carries an explicit **live-state list** (Auto-Memory files, auto-learned skills, session state) that `der sync` never overwrites; feeding live state back into `harness/` is a manual, deliberate act. This kills the clobber, the privacy leak, and the source/rendered ambiguity in one move.

**F2 (for B2) — Model-slot indirection; materializer rejects literal model strings.**
Workspace files may only reference model *slots* (`primary`, `subagent-default`, named slots). Binding maps live outside the workspace: the research overlay binds every slot → DeepSeek v4 pro (+ pinned temperature); the owner's daily config binds slots → their chosen mix. The materializer **fails validation on any literal model/provider/base_url/temperature string anywhere in the workspace** (agent.yaml, sub_agents/, tools/). Split agent.yaml's schema into evolvable params vs pinned-by-context params, enumerated explicitly. This makes D6 enforceable instead of aspirational and preserves the exact same workspace for both contexts.

**F3 (for B3) — Name the content-trust boundary and constrain executable component classes.**
State plainly: the materializer is the *shape* boundary; the **promotion PR review is the content boundary** — and make that review tractable: (a) `tools/` may only *reference* MCP servers from a vetted catalog file committed under owner-only ownership (evolve agent can reorder/configure, not introduce arbitrary commands); (b) hooks must be scripts stored inside the workspace (no inline one-liners invoking network fetches), so they are diffable; (c) the promotion script renders a PR body with executable-content diffs (hooks, MCP, tools) in a separate, top-most section labeled "EXECUTES ON YOUR MACHINE"; (d) rollout containers keep full freedom — the constraint applies at materialize-for-daily time, so the evolve loop's search space inside the sandbox is not throttled.

**F4 (for B4, dashboard/scorecards) — Make all der-side artifacts a pure, idempotent function of `runs/`.**
New command `research postprocess`: scans `research/runs/`, (re)builds any missing/stale scorecards from harbor results + proxy metrics, regenerates dashboard SVGs and the experiment index. Safe to run at any time, from cron every 10 minutes during runs and on demand. No evolve.py patch, crash-safe by construction (a crash between harbor finish and scorecard write self-heals on next tick), and both front doors get scorecards from the identical code path.

**F5 (for B4 budget + M1 + Risk 3) — Promote the metering proxy to a first-class component and the primary trace source.**
A local OpenAI-compatible passthrough proxy is the single `LLM_BASE_URL`/`ADB_LLM_BASE_URL` for the entire loop. It provides: (1) canonical wire traces (full message arrays → turns/tool-calls for the converter; session logs demoted to optional enrichment); (2) provider-truth token usage per call, tagged per role (rollout/ADB/evolve/explore via distinct ports or an injected header); (3) budget enforcement as an **external watchdog**: cumulative-spend counter, at ceiling it stops accepting new requests (429) and signals the tmux session to pause — no "loop refuses" seam inside evolve.py required. Replace D8's budget wording accordingly and rewrite Risk 3's mitigation order.

**F6 (for B5) — One-line seeding rule.**
"Every evolve run and every `research eval/ab` seeds its iteration-0 input from `harness/` at a recorded git SHA; per-run loop lineage is ephemeral; promotion PRs are cut against that same seed SHA." Owner hand-edits automatically enter the next run; unmerged loop progress is deliberately discarded unless promoted — which is the honest semantics of a human-gated `harness/`.

**F7 (for B5, scorecard↔git divergence) — Content-address the workspace; enforce evaluated-equals-promoted.**
Define `workspace_hash` = SHA-256 of a canonical tar (sorted paths, zeroed mtimes/uids) of workspace files; record it in every scorecard (git SHA additionally when one exists). Promotion invariant: **no eval, no ship** — the PR body carries the workspace_hash; a CI check re-hashes the PR's resulting `harness/` state and fails on mismatch, making "promote with a small manual tweak" structurally impossible.

**F8 (for M2) — Holdout gate on promotion.**
Split the pinned suite: `der-suite-v1` (~50 tasks, loop-visible) + `der-holdout-v1` (~30 disjoint tasks, never referenced by the loop, never analyzed by ADB). Promotion requires a fresh holdout scorecard with pass-rate delta ≥ 0 vs the current baseline's holdout score (CI-aware per Minor 4). Overfit hacks then die at the gate instead of moving into the owner's daily driver.

**F9 (for M3) — Error taxonomy + completeness rule.**
Converter classifies every rollout terminal state as `passed | failed | errored` (provider 4xx/5xx, sandbox/infra faults, timeouts-of-infrastructure — enumerated list in Stage 2). Scorecards count them separately; flip attribution and pass-rate aggregates exclude `errored`; an iteration scorecard is emitted only when non-errored results exist for every task × k, else the run is marked `incomplete` and postprocess skips it (and the watchdog re-queues or alerts). Stage-2 verification item: confirm whether AHE/harbor resume re-runs a partial iteration or reuses partial results, and make the budget watchdog count re-runs either way.

**F10 (for M4) — Single-writer lock + namespaced runs.**
An flock-based run lock around any harbor invocation: `research eval/ab` refuses (with a clear message and `--queue`) while an evolve iteration holds it. Namespace the layout: `research/runs/evolve/<run-id>/iteration_NNN/` vs `research/runs/adhoc/<exp-id>/`; postprocess and dashboard read both. Dashboard regeneration is serialized by the same lock (or exclusively owned by postprocess per F4).

**F11 (for M4 coexistence) — Resource + retention policy, stated.**
Harbor containers run under a CPU/memory-capped cgroup (sized to leave the owner an interactive slice); raw traces get a retention rule (e.g., keep last N iterations + any trace referenced by a committed analysis digest; delete the rest on postprocess tick); disk high-water-mark check before each iteration in the watchdog. State explicitly: daily driving during a rollout is supported-but-degraded; heavy iterations are scheduled off-hours by default.

**F12 (for M5) — Separate working copies + conflict-proof dashboard paths.**
The loop runs in its own clone (`~/research-runner/der`), commits once per iteration ("research: iteration NNN scorecard + attribution"), and pushes to a dedicated branch (`research-runs`); the owner merges opportunistically. Dashboard SVGs live at fixed paths (`docs/dashboard/*.svg`) referenced from README so README.md itself almost never changes; the experiment index table lives in `DASHBOARD.md` (linked from README), not in README. The daily driver never reads from the runner's working tree (consistent with F1's out-of-repo daily materialization).

**F13 (for M6) — Pre-flight materialization, once.**
The driver validates + renders the workspace exactly once per iteration (or per CLI run) before harbor launch; containers receive the rendered config (mounted/baked), plus the materializer version stamped into the scorecard. Container startup shim shrinks to "point qwen at the rendered dir, run, emit trace."

**F14 (for M7) — Invert the build order in the architecture text.**
Rewrite the one-sentence architecture and Risk 1: the substrate (materializer + der harbor agent + proxy/converter + scorecards + postprocess + CLI) is the **primary deliverable**, independently testable via `research eval`; the inherited evolve driver is a config-level *client* of that substrate. The seam audit then gates only autonomy, not value delivery. This also gives Stage 2 its natural milestone sequence: smoke suite → substrate → first baseline scorecard → evolve client → first unattended run.

**F15 (minors 1–10)** — adopt as written above: schema additions incl. same-k comparability; pre-built suite images with `force_build: false`; N/N+1 verdict semantics documented; paired-bootstrap CI in `research ab`; cold-start baseline eval; `der doctor` version-skew warning; "variance reduction" wording with no-determinism-assumptions rule; secret-scrub in postprocess; `research/runs/` path pinned; explore-agent cost in projection + per-role metering.

---

## VERDICT

REVISE — the loop core is sound and correctly inherited, but the workspace/daily-driver contract (B1), the unenforceable model pin (B2), the misnamed trust boundary (B3), the unimplementable-without-patching integration points (B4), and the missing baseline lineage rule (B5) would each corrupt state or fork the system in its first weeks of real operation.
