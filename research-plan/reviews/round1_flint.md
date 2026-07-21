# Round 1 review — Flint (operator / YAGNI / cost lens)

Reviewer stance: one person, one server, spare time, LLM-agent implementer. The draft's core bet — inherit AHE's loop, swap the agent-under-test at the harbor seam — is the right bet and I do not touch it. Everything below is about scope, sequencing, and the ops floor. Where I cite config defaults, I verified them against the vendored source (`/agent/workspace/research-plan/ahe-src/base.yaml`, `evolve.py`).

---

## OVERBUILT (cut list)

Each item: what to cut, and the concrete replacement.

**O1. D3 — full 8-type component contract at V1.**
Eight materialization surfaces (system prompt, settings, tool descriptions, MCP tools, hooks, skills, sub-agents, memory) means eight validation paths, eight failure modes, and an evolve-agent prompt that must teach all eight — before the first iteration ever runs. Sub-agents/orchestration topologies alone are a project.
*Replace with:* phased contract. V1 materializer implements **QWEN.md + agent.yaml + skills/ + LongTermMEMORY.md** and rejects everything else loudly (the fail-loud behavior is already designed — use it as the phase gate). The full 8-type table stays in the doc as the target schema; hooks/middleware land in V1.x when the owner's first hook hypothesis needs them; sub_agents last. The evolve-agent prompt only offers implemented types.

**O2. D10 — promotion-PR machinery.**
A script that authors PRs against your own repo, embedding manifests and scorecard links, is automation for a review audience of one.
*Replace with:* `research promote <run>` = create branch, copy winning workspace over `harness/`, commit with manifest + scorecard path in the message, print "review the diff, then `gh pr create` or merge." ~20 lines. The human gate is the owner reading `git diff`, which they'd do anyway. PR-body templating is V2 if the public notebook ever demands it.

**O3. D7 — subset-selection ceremony.**
"Selection script + defensible criteria" (and open question 3 debating stratification methods) is methodology theater. Reproducibility comes from the frozen artifact, not the selection procedure.
*Replace with:* a committed `der-suite-v1/tasks.txt` — seeded random sample from terminal-bench@2.0, one line in the suite README: "seed=42, sampled YYYY-MM-DD from tb@2.0." If the sample turns out unbalanced, curate suite-v2 with reasons; suite version is already in every scorecard (D7's one genuinely good idea — keep that). Also reconsider vendoring 50 task directories into the repo: tb@2.0 is itself a pinned reference; an ID-list filter against the pinned dataset is lighter if harbor supports it. Decide in skeleton step 0, not by default-vendoring.

**O4. D8 — projected-cost budget guard.**
"Refuses to start an iteration whose projected cost exceeds the ceiling" requires a cost model that will be wrong in both directions.
*Replace with:* actuals only. (a) Provider-side prepaid balance / spend cap sized to the monthly budget — survives every local bug. (b) In-loop cumulative meter summed from usage fields, checked between iterations against `max_run_cost_usd`; refuse next iteration if `spent + last_iteration_actual > cap`. Trailing-actual is a better predictor than any projection and is ~15 lines.

**O5. D5 — `research ab` delta-report + verdict-template generation.**
The CLI is a fixed requirement; this scope isn't. A "verdict template" generator is a static file wearing a script costume.
*Replace with:* `research eval` (core) + `research diff a.json b.json` (paired per-task flip table + aggregate deltas). `research ab` stays as ~10 lines of sugar calling eval twice + diff. Verdict template = committed `experiments/TEMPLATE.md` the owner copies.

**O6. Explore agent on at V1 (D5, and upstream default `enabled: true`).**
Verified: upstream points it at the NexAU repo + a fixed web-source reading list — all wrong for der, and it burns tokens before the basic loop is even proven. "Parallel to iteration 1, zero time cost" is not zero token cost.
*Replace with:* `explore_agent.enabled: false` in the der overlay for V1. Enabling it (pointed at qwen-code *docs* + der docs, not the full TS source tree) becomes itself an experiment with a scorecard, later.

**O7. D1 — the subtree-vs-vendored choice.**
Git subtree is a recurring papercut (merge weirdness, contributor confusion) with zero payoff at this scale.
*Replace with:* plain vendored copy + `UPSTREAM.md` with the pinned commit. Re-syncing upstream is a diff exercise an LLM agent does fine. Delete the option from the doc; options are also cost.

**O8. D9 — dashboard scope (trim, not cut — it's an owner requirement).**
Four chart types + index regeneration "runs on verdict" implies wiring into the loop.
*Replace with:* one idempotent script, `research dashboard`, regenerates everything from scratch from committed scorecards: V1 = pass-rate chart + cost chart + experiment index table. Tokens/wall-clock charts are a later afternoon. Call it manually or at end-of-run; no hook plumbing, no incremental state.

---

## UNDERBUILT (add list)

Where the single operator loses hours (or hundreds of dollars) as drafted.

**U1. Smoke path as a first-class command — not a Stage-2 calibration footnote.**
§7 buries the 5-task smoke suite. It must be `research smoke`: frozen 5-task list, k=1, exercises the full pipeline (materialize → rollout → convert → scorecard) in <15 min and <$1. Run it after every harness/config/image change and before every full run. Add `research eval --task <id> --keep-container` for single-task interactive postmortems. Without these, every pipeline bug costs a 100-rollout iteration to discover.

**U2. Golden-trace fixtures + converter strict mode.**
The qwen→AHE trace converter is the single new load-bearing component. If it silently emits zeros for token usage or malforms turns, ADB analyzes garbage, the evolve agent edits from noise, and you find out N paid iterations later. Add: committed real qwen session logs + expected converted output as unit fixtures; a strict mode that **fails the run** on missing usage fields instead of defaulting them. This is the cheapest insurance in the whole plan.

**U3. The 3am story: systemd, not tmux.**
tmux + evolve-resume.sh dies with a server reboot and fails silently. Add: a systemd unit (`Restart=on-failure`, `OnFailure=` → curl a notification) wrapping the resume-capable invocation; a half-page runbook: "loop dead → `systemctl status` → resume command → it restarts from iteration N." Verified in evolve.py: resume granularity is the **iteration** — it rolls metadata/workspace back to the iteration boundary, so a crash at 90% of an iteration re-spends that iteration. Acceptable, but say it out loud, and make "kill -9 mid-rollout, then resume successfully" an acceptance test in the skeleton (step 7).

**U4. Notification reality + cost visibility before the bill.**
Verified: upstream notify is Feishu-webhook-only, fires on iteration completion/target/timeout — not on process death (U3 covers that). Add a 10-line generic webhook shim (ntfy.sh/Telegram) or accept Feishu, and put **{iteration cost, cumulative run cost, provider balance}** in every iteration-end message. DeepSeek exposes a balance endpoint; one call, no bill shock. The dashboard already charts cost — this is the push channel for it.

**U5. Disk janitor + preflight.**
50 task images (0.5–2 GB each) + per-rollout containers + raw traces on one box that is also the daily driver: when Docker's disk fills, *everything* on the server breaks. Add: end-of-iteration janitor (prune exited containers + dangling images; zstd or delete raw traces after ADB distillation, keep last N iterations), and a preflight in every CLI entry (docker up, ≥X GB free, API key answers a 1-token ping, suite images present). Also verified: `harbor_job_timeout_minutes: 0` and `experiment_timeout_minutes: 0` — **unlimited** — upstream. The der overlay must set both; D8 currently assumes a "hard timeout" that is off by default.

**U6. Contention with the daily driver.**
The loop at n_concurrent 4–8 will peg the box while the owner is using their daily harness. Add: systemd `CPUQuota`/`Nice` on the loop, memory/CPU caps on task containers, and/or a night-window timer. One paragraph in Stage 2; hours of mystery-latency saved.

**U7. Noise guard in `research diff`.**
At 50 tasks × k=2, a 2-point true delta is invisible and a 5-point delta is marginal. The diff output should print the per-task flip table plus one line of paired sign-test / binomial CI so the owner doesn't write verdicts on noise. ~30 lines; prevents wrong adoptions, which are the most expensive failure this system can produce.

**U8. Rollout environment isolation.**
The rollout image must not inherit the owner's personal qwen state (settings, auth, memory) — fresh HOME, injected env only, DeepSeek key scoped to the loop. Name it now so Stage 2 builds the image that way; this is a classic "why is the rollout using my logged-in config" afternoon-loser.

---

## WALKING SKELETON (ordered)

Promote Risk 1's fallback ("harbor-only substrate first") to *the plan*. CLI substrate before evolve driver; evolve.py enters last, at toy scale. Each step has a proof; stubs listed are acceptable.

0. **Seam-kill spike (no code).** (a) Run one terminal-bench task via harbor on local Docker with any built-in agent — proves local `env` works (open Q1). (b) Check for an existing qwen-code harbor adapter. (c) Run `qwen -p` headless against the DeepSeek endpoint by hand; capture the session log; confirm per-call token usage exists (open Q2). Kills the two biggest unknowns for ~$1.
1. **Minimal der harbor agent.** Container: pinned qwen + hardcoded QWEN.md (materializer stubbed as one file copy). One task, k=1, local Docker. Proof: task runs, trace file lands at the known path.
2. **Trace converter + scorecard.** Convert that one trace; extract tokens/cost/wall-clock/turns; emit scorecard JSON. Commit the golden fixture (U2). Proof: numbers match the raw log by hand-check.
3. **`research smoke` / `research eval`.** Frozen 5-task list, k=1, thin CLI wrapping steps 1–2, aggregate scorecard. This *is* the required experiment CLI arriving early, and the smoke path (U1) forever after.
4. **Dashboard v0.** Script reads committed scorecards → pass-rate + cost SVGs + index table in README. Owner requirement visible early; validates the scorecard schema before anything depends on it.
5. **Materializer v1 + workspace arg + `research diff`.** QWEN.md + agent.yaml + skills/ + memory (O1 scope); reject the rest. Proof: owner runs a real hand-written A/B end to end. **Value ships here, before any evolve-agent work.**
6. **ADB integration.** DeepSeek-pinned ADB over the smoke-suite traces. Proof: spot-check that digest claims link to real trace events (not hallucinated structure) — this validates the converter against AHE's actual consumer.
7. **evolve.py at toy scale.** Full AHE iteration on the 5-task suite: max_iterations=2, best_of_n off, explore off. Proof: manifests written, flip attribution binds predictions to observed flips on qwen traces, rollback fires on a failed prediction, and **kill -9 mid-rollout → resume works** (U3). The architecture is proven at this step.
8. **Scale to production V1.** 50-task suite, k=2, n_concurrent tuned to the box, spend meter + timeouts set, systemd unit, notifications, janitor. Then let it run 10 iterations.

---

## COST SANITY CHECK (§7)

Assumed pricing (public DeepSeek history: V3-era ≈ $0.27/M in, $1.10/M out; V3.2 cut to ≈ $0.28/$0.42 with ~$0.03 cached input). Reasonable planning band for "v4 pro": **$0.3–0.6/M input, $1–2/M output, cached input ~10× cheaper**. Versioned pricing table (D6) replaces this in Stage 2.

Per-iteration arithmetic at 50 tasks × k=2 = 100 rollouts:
- Agentic rollout ≈ 0.3–1.5M input tokens (context regrows each turn; high cache-hit on shared prefixes), 10–40K output → **$0.05–0.35/rollout** cache-adjusted.
- Rollout bulk: **$5–35/iteration** (tail to ~$60+ if long-horizon tasks or timeout-retry storms).
- ADB over ~10M trace tokens: **$3–8**. Evolve agent session: **$1–3**.
- **Total ≈ $10–50 per iteration.** §7's qualitative ordering (rollouts #1, ADB #2) checks out, and no stated number means nothing dishonest — but §7 sins by omission on the *multipliers*:
  - `max_iterations: 100` is the verified upstream default → an unattended run is **$1K–5K** if nobody changes it. The der overlay must ship `max_iterations: 10`.
  - `best_of_n` evaluates **all N variants** (verified in base.yaml comments) → rollout cost ×N. It defaults off; keep it off for V1 and label it a cost multiplier when enabled.
  - Both timeouts default to **0 = unlimited** (verified); D8's "hard timeout" doesn't exist until the overlay sets it.
- Wall-clock: 100 rollouts at n_concurrent 4–8, ~10–20 min/rollout → **3–6 h/iteration**. An iteration is an overnight unit; ~1–2/day max on one box. That both caps monthly spend naturally (~$300–1,500/mo if run continuously) and makes the smoke path (U1) non-optional.

**The single guardrail that matters most: the provider-side prepaid balance / hard spend cap.** It is the only control that survives every local bug — converter zeros, meter bugs, runaway retries, a hung iteration. The in-loop actual-spend meter (O4) is the UX layer on top; the prepaid wall is the safety layer.

---

## D1–D10 LINE CALLS

- **D1 — KEEP (simplified):** monorepo vendoring is right for one person; plain copy + UPSTREAM.md, drop the subtree option (O7).
- **D2 — KEEP:** the harbor-seam swap is the whole architecture; skeleton step 0 must verify adapter existence + local Docker before anything else is built.
- **D3 — SIMPLIFY:** phase the contract to 4 component types with loud rejection of the rest (O1); full table is the target schema, not the V1 build.
- **D4 — KEEP (harden):** load-bearing; add golden fixtures + strict-on-missing-usage (U2) or the whole loop analyzes fiction.
- **D5 — KEEP (resequenced + trimmed):** both doors are required, but the CLI substrate ships first (skeleton 3–5); ab = eval×2 + diff, verdict template is a static file (O5); explore agent off at V1 (O6).
- **D6 — KEEP:** single pin, env-driven, versioned pricing table — exactly right; just don't promise "determinism" from temp 0, only variance reduction.
- **D7 — SIMPLIFY:** frozen seeded task-ID list replaces selection ceremony (O3); k=2 keep (upstream default, flip attribution needs it); occasional full-suite runs keep.
- **D8 — KEEP (rework guard):** local-Docker-first is the right call; replace projected-cost with actuals + prepaid cap (O4), set both timeouts explicitly (U5), add systemd/janitor/contention limits (U3/U5/U6).
- **D9 — KEEP (scoped):** required by owner; one idempotent regenerate-all script, two charts + index at V1 (O8); experiment md files keep — they're just files.
- **D10 — SIMPLIFY:** human gate keep, machinery cut: branch+copy+commit script printing next steps (O2); the unattended loop never touching `harness/` is the one hard rule — keep it verbatim.

---

## VERDICT

**REVISE** — the architecture (inherit AHE, swap at the harbor seam, one repo) is sound and should not change, but Stage 1 must invert sequencing to CLI-substrate-first with evolve.py entering at toy scale, shrink the V1 component contract to four types, and add the ops/cost floor (smoke command, golden-trace strict mode, systemd recovery, disk janitor, actuals-based spend cap with max_iterations=10) before any full iteration is paid for.
