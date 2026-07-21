# Round 3 — Arbiter (closure audit of draft_v3.md)

Scope: verify v3's claim to integrate round 2 (Vex F1–F12, Sage punch-list 1–15), sweep for regressions against v3-internal consistency, round-1 settlements, owner constraints, and blocker-level holes in v3's NEW mechanisms. Source facts underpinning new mechanisms re-verified against `/agent/workspace/research-plan/ahe-src/evolve.py`: `EXPERIMENTS_DIR = PROJECT_DIR / "experiments"` (:37, used :262/:267); plain `["harbor", "run", ...]` argv (:410); timeout fallback to `find_latest_job_dir(iteration_dir)` / "Using existing results after timeout" (:499–502); missing `verifier/reward.txt` → `"exception"` class (:628–638) with exception-vs-real-flip separation (:884–896); config-sourced model string (:1993). All five hold; v3's new mechanisms stand on verified ground.

---

## RESOLUTION MATRIX

### Vex F1–F12

| # | Sev | Ruling | Evidence in v3 |
|---|-----|--------|----------------|
| F1 | BLOCKER | **RESOLVED** | All three fix parts implemented. (a) D5 field-allowlist rendering over enumerated structured surfaces; request-shaping fields (model, endpoint, api_key, temperature, **top_p, max_tokens**) not renderable from workspace content; `${...}` interpolation banned; prose explicitly out of scope with the reason stated. (b) D5 keyless trial containers + host pinning proxy (systemd service, host gateway) injecting the key and hard-setting/rejecting `model`; explicitly "not metering; session JSONL remains the trace/metrics source" — round-1 settlement intact; D13 restates "no real provider key in containers"; §9 item 2 + skeleton step 0 verify container→host networking. (c) D6 strict mode asserts observed per-event model == binding; D7 schema records **proxy-observed** model string (correcting the evolve.py:1993 config-sourced pattern). |
| F2 | MAJOR | **RESOLVED** | D7 "No eval, no ship — enforced at both gates": `research sync` re-hashes `harness/`@HEAD and refuses when the hash has no scorecard (`--force` escape for deliberate owner-only edits); `research promote` refuses when `harness/`@main moved past seed SHA, offers `--rebase-and-reeval` (re-seed + at minimum re-run holdout). D12 and lifecycle (c) repeat both gates. "Structurally impossible" wording is gone. |
| F3 | MAJOR | **RESOLVED** | D9 "Process model (one answer)": systemd executes evolve.py/resume wrapper directly; ceiling stop = `systemctl stop der-evolve.service` (clean stop ≠ failure, no restart loop) + `COST_CEILING_REACHED` flag + `ExecStartPre` refusal; notification carries flag + spend. tmux marked dev-only in D1, §2, and D9 (three-way inconsistency gone). D13 acceptance test covers ceiling → clean stop → flag blocks restart. |
| F4 | MAJOR | **RESOLVED** | D10 names both mechanisms: (1) run-scoped advisory flag held by `der-evolve.service`; adhoc full-suite refused during an evolve **run**; only smoke-class may `--queue`; (2) `harbor` PATH shim owns the flock (plain-argv fact verified, :410 — zero patches), bounded wait + fail-fast so a busy lock is a clean iteration error, never a timeout scavenging stale job dirs (fallback fact verified, :499–502). Job-dir hygiene rule + §9 item 9 (resume/rerun semantics) + step-7 proof "superseded job dir fenced" cover part (c). |
| F5 | MAJOR | **RESOLVED** | D2: per-trial install from a **vendored tarball uploaded into the trial**, no npm-registry dependency at rollout; prebaking = named later optimization; `force_build` conflation explicitly untangled ("task-env image caching only and is orthogonal"). D6: watchdog re-queues an `incomplete` iteration once (bounded), then alerts — the re-queue owner Vex demanded. §9 items 2 (tarball install live check) and 9 (native errored-trial retry) added. Residual on the mechanism itself noted in REGRESSION SWEEP (node runtime / bundling), non-blocking. |
| F6 | MAJOR | **RESOLVED** | All four parts: (i) D8 pairwise-disjointness test across all versions of {smoke, suite, holdout} in preflight (D13) and CI, suite headers naming their holdout; (ii) aggregate-only holdout scorecards in committed artifacts (D8, D11), per-task detail gitignored; (iii) D4 explore `code_sources` exclusions written into the overlay now, explore still off at V1; (iv) adaptive-reuse budget: rotate holdout after 5 failed promotions and re-baseline. |
| F7 | MAJOR | **RESOLVED** | D4 disjoint render targets: managed skills → `skills/der-managed/` owned by sync; memory seed → der-managed file via qwen context-import (§9 item 5 verifies on the pin; fenced `<!-- der-managed -->` region fallback named); live-state list never written by sync, versioned per qwen release, re-checked by doctor (D13). "Promoted improvements therefore actually ship without ever clobbering live state" — exactly the failing pair F7 exposed. |
| F8 | MINOR | **RESOLVED** | D7 comparability: qwen-code or materializer-major mismatch → diff renders under loud CONFOUNDED banner (never silent); suite/k mismatch → refuse. Schema carries qwen-code + materializer + der-harbor versions. |
| F9 | MINOR | **RESOLVED** | D10: `research postprocess` is the **sole committer**; loop wrapper invokes it at iteration end; cron ticks and invocations share a repo-level flock. Dashboard SVGs get `.gitattributes` `ours` merge driver + "rerun postprocess after any merge" (D10/D11). |
| F10 | MINOR | **RESOLVED** | D7 schema "(immutable once written)"; D10 postprocess rebuilds **missing or corrupt** scorecards only; pricing/schema changes apply to new runs. |
| F11 | MINOR | **RESOLVED** | D10: scorecard builder reads newest job dir **whose trial set is complete**; superseded/partial dirs fenced/pruned at resume; §9 item 9 pins the fork's resume/rerun semantics; step-7 acceptance includes the fence. |
| F12 | MINOR | **RESOLVED** | D5: research binding = committed overlay file (the public pin); daily binding lives **outside the repo** next to the daily config (owner's private mix/endpoints), read by `research sync` at render time — verbatim implementation of the fix. |

### Sage punch-list 1–15

| # | Ruling | Evidence in v3 |
|---|--------|----------------|
| 1 | **RESOLVED** | D10 states the source-true path `research/experiments/<run-id>/runs/iteration_NNN/` (constant verified, :37) with `research/runs/adhoc/<exp-id>/` for CLI runs, postprocess scanning both, no patch; naming disambiguation from the top-level notebook `experiments/` stated. §2 carries the fact; §4 diagram and D1 exclusion list are consistent. |
| 2 | **RESOLVED** | D6: der `errored` ≡ the pin's `exception` class; mechanism stated (agent **raises**; trial ends with `exception.txt`, no `reward.txt`; provider faults never land as `reward.txt = 0.0`); §2 bullet repeats it; §9 item 8 verifies both directions on the pin. Source mapping confirmed (:628–638). |
| 3 | **RESOLVED** | D9 one process model (systemd direct, `systemctl stop`, tmux dev-only); "SIGTERM to the tmux session" deleted; D13 "systemd everywhere." |
| 4 | **RESOLVED** | D2 pins V1 install = per-trial install of pinned `@qwen-code/qwen-code@<version>` (from vendored tarball); prebake = named later optimization; `force_build` scope note present. |
| 5 | **RESOLVED** | D2: materializer + converter live in `research/der`; **der-harbor depends on `research/der`** (agent code host-side, imports directly); "one direction, no cycles." |
| 6 | **RESOLVED** | D8 exact predicate: point delta ≥ 0 AND not conclusively negative (one-sided paired sign test, α = 0.05, does not reject "no worse"); `inconclusive`-but-nonnegative passes, with the 30×k=2 rationale; "fresh" defined (same workspace_hash, current holdout version, baseline unchanged); promote refuses rather than auto-runs. |
| 7 | **RESOLVED** | D12: branch **from the run's seed SHA**; copy = **exact replacement** of the managed tree (extraneous files deleted; hash verifies whole tree); holdout gate refuses with the exact command if no fresh scorecard (freshness per D8). |
| 8 | **RESOLVED** | D3 baseline registry: `research/baseline.json` (committed pointer {scorecard path, workspace_hash, suite versions}), updated in the promotion commit itself (D12), declared "what 'vs baseline' means everywhere"; referenced by D7 schema. |
| 9 | **RESOLVED** | D5 scopes validation to structured config surfaces with the reason (prose cannot bind; bindings exist only outside the workspace); D4 materializer signature is `(workspace, bindings, context)`; both binding locations named at decision level (committed overlay file / outside-repo next to daily config). Exact filenames left to Stage 2 — listed as a nit below, not an architecture choice. |
| 10 | **RESOLVED** | D10 lock reworded run-scoped (advisory flag held by the service for the whole run) + per-invocation shim flock (the seam that exists); postprocess named executor of per-iteration commits to `research-runs`. |
| 11 | **RESOLVED** | Step 1 proof = raw qwen session JSONL in the trial's agent logs dir; step 7 scope adds retargeted evolve-agent prompt + der overlay incl. der-schema `code_agent_patch` replacement; rollback proof marked "(contrived, injected) falsified prediction." |
| 12 | **RESOLVED** | D7: granularity stated (per-trial → per-task → run-aggregate); der-harbor (agent) version + dataset reference added to schema; D6 defines `turns` (assistant-message events / model-call rounds in the session log). |
| 13 | **RESOLVED** | D1: AHE files directly under `research/`; der code a package at `research/der/`; vendored pyproject extended so the CLI imports evolve.py internals; upstream re-sync diffs exclude `der/`, `experiments/` (run outputs), `runs/`, overlays. |
| 14 | **RESOLVED** | `der sync` folded into `research sync` (D3/D4; convergence log; no stray `der` CLI remains anywhere in v3). agent.yaml evolvable-vs-pinned enumeration assigned to Stage 2 **with a named starting set** (D5). |
| 15 | **RESOLVED** | §9 gains item 8 (errored mechanics), item 10 (DeepSeek balance/usage endpoint), and item 2 extended to tarball-install-in-trial + proxy networking (the npm-reachability check correctly transformed after D2's tarball decision made registry reachability moot). |

**Counts: 27 RESOLVED / 0 PARTIALLY / 0 UNRESOLVED.**

---

## REGRESSION SWEEP

**Pinning proxy (new mechanism) — no conflict found.**
- *Seam facts:* the proxy sits outside every enumerated seam; qwen's base_url is set by the rendered config (materializer output), which the der agent controls host-side pre-upload. No evolve.py or harbor change; PATCHES.md-zero intact.
- *Harbor env model:* trial env is der-agent-injected (fresh HOME, injected env only, D13); host-side roles (evolve agent, ADB, explore) keep their own `${LLM_*}`/`ADB_LLM_*` plumbing and are not forced through the proxy. Container→host-gateway reachability is the one genuine unknown and it is named twice (skeleton step 0, §9 item 2) — verified before anything depends on it.
- *Metering settlement:* D5 "not metering; session JSONL remains the trace/metrics source" + D9 "the D5 pinning proxy deliberately does not meter; per-role metering proxy remains a named later option." Round-1 demotion intact. Recording the observed model string is identity observation, not cost accounting — no contradiction, though the proxy→scorecard channel is unstated (ambiguity #2 below).
- *DeepSeek-everywhere:* the proxy enforces the owner constraint rather than threatening it; daily context never touches the proxy (daily bindings, owner's own keys), matching the context pack's daily-driver exemption.

**Sync ship-gate — does not break the owner's hand-edit workflow.** The permitted flow survives on two paths: (a) owner hand-edits normally travel through `research ab`/eval, producing a scorecard whose workspace_hash matches what ships → sync passes cleanly; (b) deliberate unevaluated edits ship via the explicit `--force` escape v3 retains. The gate converts a silent hole into a visible choice; nothing the context pack permits is forbidden.

**Runs-path correction — consistent at every reference.** §2 (fact), D10 (layout + both scan roots), §4 diagram (`research/experiments/<run>/runs/… + research/runs/adhoc/…`), D1 (re-sync exclusions), D11/lifecycle (b) (top-level `experiments/` = notebook, disambiguated in D10). One stale echo in D4's explore-exclusion literals (ambiguity #4) — intent unambiguous via D8's "run/notebook artifacts."

**Round-1 settlements:** substrate-first (§1, D3), converter contract (D6 unchanged in shape: NexAU span tree, "openai" span naming, in-hook placement, fixtures/strict mode), vendoring (D1), cost band (§7 numerically unchanged), proxy-not-metering (above), V1 4-type non-executable contract (D4), holdout gate strengthened not weakened (D8). All intact.

**Owner constraints:** AHE base ✓ (vendored, client-through-seams, zero-patch target); DeepSeek-everywhere ✓ (§0, D5, diagram: evolve agent, ADB, rollouts all DeepSeek v4 pro; daily driver exempt as the context pack specifies); Qwen Code base ✓; two-stage ✓ (approval gate in §0/§3-status, §9 is a live-install list not silent assumptions); dashboard/notebook ✓ (D11, README-glanceable honored); CLI + unattended/resumable autonomy ✓ (D3 primary CLI, D9/D13 systemd + resume + runbook, lifecycles a–c).

**Internal contradictions:** none found at architecture level. D6's incomplete-handling agrees with D10's job-dir rule; D8's gate agrees with D3's diff verdicts; D5/D6/D7 agree on proxy-observed model; D9's meter and D5's non-metering proxy are disjoint duties.

**New-mechanism holes (flagged, all non-blocking):**
1. *Vendored tarball residual:* "no npm-registry dependency" holds only if the published qwen package is a self-contained bundle (else `npm install ./tarball.tgz` still resolves transitive deps from the registry) — and the node runtime itself must be provisioned per trial (upstream qwen_code.py uses an nvm fetch, which is the same network-flake class F5 targeted). Not blocker-level: §9 item 2 live-checks exactly this install path before anything ships, and the fallback (prebake into suite images) is already named in D2. Stage 2 should widen item 2's wording to cover node provisioning + dependency closure explicitly.
2. *"Loop wrapper invokes postprocess at iteration end"* names an invocation point evolve.py exposes no seam for. Harmless: postprocess is idempotent, flock-serialized, and cron-driven anyway (sole-committer property does not depend on the iteration-end call); a runs-dir watcher or post-shim-exit hook can realize it if wanted.
3. *Proxy-observed → scorecard channel* unstated (see ambiguity #2). One Stage-2 sentence; no architectural consequence — in the research context the proxy only ever admits one pinned model, so the run-level field is well-defined.

None of the three forces a design change under any resolution; each has a named fallback or a covering verification item.

---

## REMAINING AMBIGUITIES (non-blocking; Stage 2 absorbs)

1. D5 "hard-sets/rejects the `model` field" — rewrite-silently vs 4xx-on-mismatch are both readable. Pick one (suggest: reject, so drift is loud and the D6 assertion has teeth; or hard-set + proxy-side mismatch log).
2. How proxy-observed model values reach the scorecard (proxy log file postprocess reads? correlation granularity = run-level?) — unstated interface, one sentence.
3. §9 item 2 should explicitly include node-runtime provisioning and transitive-dependency closure for the tarball install (see sweep #1).
4. D4's explore-exclusion literals ("`runs/`, `DASHBOARD.md`, `experiments/`") predate the D10 path correction; should read `research/experiments/`, `research/runs/`, top-level `experiments/`, `DASHBOARD.md`. D8's "run/notebook artifacts" already states the intent.
5. Whether the holdout gate hard-refuses or proceeds-under-CONFOUNDED when candidate and baseline scorecards differ in qwen-code/materializer version (D7 defines the banner for `research diff` only; matters after an "upgrade run as an experiment").
6. Watchdog "re-queues an incomplete iteration once" — mechanism unstated (presumably `systemctl start` → resume-from-boundary for evolve runs; re-run command for adhoc).
7. `skills/der-managed/` assumes the pinned qwen loads skills from namespaced subdirs — fold into §9 item 6 (trivial fallback: filename prefixing).
8. Exact binding-map filenames for both contexts (committed overlay file; outside-repo daily file) unnamed — deliberate Stage-2 detail, but Stage 2 must name them.
9. Run-flag file location/protocol by which the CLI detects an active evolve run — Stage-2 detail.
10. Typo: §4 diagram contains "харbor" (Cyrillic х/а homoglyphs) — cosmetic, but fix before it confuses grep-driven tooling.

None of these admits two readings that change the system's shape; every one resolves inside Stage 2 without revisiting a decision.

---

## VERDICT

**CONVERGED** — all 27 round-2 findings are genuinely implemented in v3's wording (not gestured at), the sweep found zero regressions against v3-internal consistency, round-1 settlements, or owner constraints, and the only residuals are ten non-blocking nits (chiefly: widen §9 item 2 to node/bundling, name the proxy→scorecard channel, pick the proxy's reject-vs-rewrite behavior) that Stage 2 absorbs without reopening any decision — v3 is ready for owner approval and Stage-2 expansion.
