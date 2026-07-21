# Round 5 — Final gap audit (Sentry)

Scope: verify draft_v4's claimed full integration of the round-4 external review (GPT 5.6 Sol Pro, RESTRUCTURE), sweep v3→v4 for silently dropped protections, spot-verify load-bearing facts, and check owner constraints. This audit does not re-litigate the external review's judgments.

Inputs: `reviews/round4_solpro.md`, `draft_v4.md`, `draft_v3.md`, `context.md`; local AHE source (`ahe-src/evolve.py`, 4716 lines; vendored `trace_converter.py`, 932 lines, at `/tmp/trace_converter.py`); live source of `datacurve-ai/pier`, `datacurve-ai/deep-swe`, PyPI, and QwenLM/qwen-code docs.

---

## 1. INTEGRATION MATRIX

Legend: REFLECTED = v4 states the mechanism (not just intent), with citation. PARTIALLY = mechanism incomplete. MISSING = absent.

### 1.1 The six findings

| # | Finding | Status | v4 evidence |
|---|---|---|---|
| F1 | Wrong evaluation authority → Pier sole evaluator via one semantic EvalRunner adapter; no PATH alias; host→proxy route is first live test | **REFLECTED** | D2 (sole evaluator, pins, one task-loading/networking/result system), D3 (adapter ownership list matches the review's six bullets incl. failed/invalid distinction), §2 ▽ + V2 + build step 1 (proxy route first live test, fallback = private hostname/extra-host, never weakened isolation) |
| F2 | Universal promotion gate mismatch → per-experiment contracts; pass-fraction attribution; drop "statistically significant"; "confirmation set" naming | **REFLECTED** | D7 (primary metric / min effect / guardrails / falsifier / suite / k / RunBudget preregistered; no universal gate; observed effect + numerator/denominator + per-task outcomes + descriptive task-cluster interval; pass fractions for attribution, binary reward per attempt for grading; "holdout" retired) |
| F3 | Compatibility trace made canonical → Pier/DeepSWE artifacts canonical; NexAU ephemeral ADB boundary view; honest provider identity | **REFLECTED, one factual correction needed** | D6 (canonical list matches; ephemeral view immediately before `adb ask`; honest-identity policy incl. closed-parser fallback with true provider in span attributes; fixtures + strict mode at normalizer/view). Correction: D6 names "the open vendored parser" as the preferred patch candidate — refuted by source; see FACT CHECKS (b) |
| F4 | Materializer duplicates Qwen's project model → runtime-shaped `harness/` + transparent staging overlay; pinned standalone archive | **REFLECTED** | D4 (native layout; overlay = copy + isolated HOME + auto-memory isolation + immutable bindings outside evolvable namespace + staged-files manifest; component schema/renderer/model slots deleted; archive from local read-only cache, no npm at rollout) |
| F5 | Two orchestration paths → one synchronous EvalRunner + finalizer; explicit IDs; fail closed; no recency recovery; one lock; dedicated worktree | **REFLECTED** | D3 (both doors; finalizer atomic after complete terminal result; explicit experiment + job IDs; fail-closed on absent/incomplete result path; cron writer/publication branch/merge driver deleted; worktree + one lock), §2 (recency recovery "now removed — D3") |
| F6 | Identity/outcome represented too many times → three levels of truth; derived baseline; generated result block; delete DASHBOARD.md/second chart | **REFLECTED** | D9 (tree OID + runtime-manifest digest; one immutable scorecard.json with the full Q4 field list; one lifecycle record created pre-run; baseline derived from most recent adopted scorecard matching `main:harness`; baseline.json deleted), D11 (generated README block; deletions enumerated) |

### 1.2 The six Q-answers

| Q | Status | v4 evidence |
|---|---|---|
| Q1 DeepSWE + Pier sole backend; T-B demoted; 8-point acceptance; honest scope; 1.4% and 7.5%/19% interpretation | **REFLECTED** | D2 (all 8 acceptance points present, plus staged-settings check; T-B = unscored smoke on same Pier), §2 (1.4% "a comparison, not a measured error rate"; scope honesty in D11 README; gated HF not a blocker; task revisions pinned), §9(iii) (7.5%/19% = calibration warning, not forecast) |
| Q2 Calibration + suite versioning | **REFLECTED** | D8 (~30–40 candidates; k=5 screen, k=10 boundaries; 20–80% band ≈2–8/10; shrink not dilute; 16 dev / 8 confirmation / 4–6 spine; k=2 dev, k=4–5 interleaved confirmation; frozen membership; version triggers = <half in-band across 3 adopted baselines OR ~20 hypotheses; candidate pool; bridge runs; chart break; full-suite reporting-k point post-adoption). Validity taxonomy (timeout=failed; provider/infra=invalid, no imputation) in D3/D7/V5. Minor selection-guidance details absorbed, listed in NITS |
| Q3 Model roles + Codex critic | **REFLECTED** | D10 (table matches role-for-role; owner-triggered `codex exec`, read-only sandbox, schema-constrained output; fixed evidence bundle; one validated proposal artifact → `status: proposed` records; full provenance recording; no subscription in unattended path; no OpenAI-compatible shim; no model has promotion authority) |
| Q4 One scorecard / one lifecycle entry / one generated README | **REFLECTED** | D9(2) scorecard schema covers every Q4 field; D9(3) lifecycle entry pre-created, result table generated from scorecard; D11 (hero chart adopted-only, ledger of every experiment incl. rejected/inconclusive/invalid, resource strips, Tura-style reporting contract on every aggregate, series break + bridge at suite change; deletes: DASHBOARD.md, second SVG, badges, notebook index, hand-copied tables) |
| Q5 Preregistration via lifecycle record; no BACKLOG.md | **REFLECTED** | D9(3) (front-matter field list matches Q5's required fields exactly incl. proposer + proposal-model metadata; git commit = preregistration proof; queue generated from `status: proposed`; BACKLOG.md deleted; one active experiment on the serial box) |
| Q6 Defer parallelism; Modal not E2B; equivalence gate | **REFLECTED** | D3 (one lock, serialized; environment field in EvalSpec, local Docker at V1), §9 (no E2B, Pier cloud = Modal; equivalence experiment gate before cloud results join the series), §6/V10 (n-concurrent 4–8 capped by server prereqs + provider rate limits) |

### 1.3 Elegance pass — 17 delete/merge rows

| Row (delete/merge → replace) | Status | v4 |
|---|---|---|
| 1. Curry Harbor fork as authority → exact Pier pin | REFLECTED | D2 |
| 2. der-harbor in-tree registration → `--agent-import-path` | REFLECTED | D1 ("der-harbor deleted from the plan") + §1 diagram |
| 3. "Zero AHE patches" goal → one tested EvalRunner adapter | REFLECTED | D1 (goal retired; PATCHES.md enumerates the seam patches) |
| 4. T-B loop + DeepSWE promotion backend → DeepSWE scored; same-Pier smoke | REFLECTED | D2 |
| 5. Canonical qwen→NexAU conversion → canonical ATIF/results; NexAU = ADB boundary view | REFLECTED | D6 |
| 6. Fake "openai" naming → true provider / neutral role | REFLECTED (see fact check b for target correction) | D6 |
| 7. Component renderer + context-type schema → runtime-shaped project + overlay | REFLECTED | D4 |
| 8. Per-trial npm install flow → pinned standalone archive from local cache | REFLECTED | D4 |
| 9. PATH command shim → direct adapter invocation | REFLECTED | §9 (shim deleted), D3 |
| 10. Publication branch + cron writer + SVG merge driver → one synchronous finalizer + one lock | REFLECTED | D3 |
| 11. "Latest job dir" recovery → exact job identity, fail closed | REFLECTED | D3, §2 |
| 12. baseline.json + tar identity → `main:harness` tree OID + runtime manifest | REFLECTED | D9 |
| 13. Universal significance gate → experiment contracts | REFLECTED | D7 |
| 14. "Holdout" terminology → versioned confirmation set | REFLECTED | D7/D8 |
| 15. BACKLOG.md + premium memos → one lifecycle record | REFLECTED | D9(3), D10 |
| 16. DASHBOARD.md, two charts, badges → one generated README chart + ledger | REFLECTED | D11 |
| 17. Separate budget/watchdog specs → one immutable RunBudget to evaluator + proxy | REFLECTED | D3 (RunBudget in EvalSpec), D5 (proxy enforces), D12 (watchdog now keys off RunBudget/monthly ceiling) |

### 1.4 Elegance pass — 9 retain rows

| Retain | Status | v4 |
|---|---|---|
| Narrow model-pinning proxy | RETAINED | D5 |
| Provider-side hard spend limits | RETAINED | D12 (prepaid cap = hard wall) |
| Managed vs live harness isolation | RETAINED | D4 (unchanged-from-v3 clause) |
| Isolated rollout home/session state | RETAINED | D4 (overlay: isolated HOME, auto-memory isolated) |
| Immutable raw evaluator evidence | RETAINED | D6 (digest-referenced canonical artifacts) + D9 (scorecards never rewritten) + D12 (retention keeps digest-referenced evidence) |
| One process lock on the single server | RETAINED | D3 |
| Dedicated autonomous worktree | RETAINED | D3 |
| Systemd supervision once synchronous path proven | RETAINED | D12 + build step 8 (autonomy last) |
| Public recording of rejected and invalid experiments | RETAINED | D11 (ledger of every experiment) |

### 1.5 Five approval conditions

| Condition | Status | v4 |
|---|---|---|
| 1. Pier sole scored evaluator for DeepSWE | ADOPTED | D2 |
| 2. One intentional AHE evaluator/result adapter, not a command-name shim | ADOPTED | D1 + D3 |
| 3. Runtime-shaped `harness/` + transparent staging overlay only | ADOPTED | D4 |
| 4. Promotion via preregistered contracts + versioned confirmation set | ADOPTED | D7 + D8 |
| 5. One lifecycle record + one scorecard + one generated README block | ADOPTED | D9 + D11 |

Also checked: v4 §4 build order mirrors the review's steps 0–8 one-for-one (scoring spine first, publication after trust, autonomy last). Matrix totals: **findings 6/6, Q-answers 6/6, delete rows 17/17, retains 9/9, conditions 5/5 — no MISSING, no PARTIALLY at mechanism level.** The review integration itself is complete; the problems found are in the v3→v4 carry-over (next section) and one factual mis-aim (fact check b).

---

## 2. LOST-PROTECTION SWEEP (v3 → v4)

### 2.1 SILENTLY LOST — still applicable under the new architecture, absent from v4

**L1. Executable-content gate + promotion-diff review as the content trust boundary (v3 D4 + D12). Severity: HIGH.**
v3 confined the evolvable surface to 4 non-executable component types ("the materializer rejects everything else loudly"), phased executable classes (MCP, hooks) behind a vetted catalog + "EXECUTES ON YOUR MACHINE" diff banner, and named the promotion diff review "the content trust boundary." v4's runtime-shaped `harness/` makes `.qwen/settings.json` (which can register MCP servers, hooks, auto-mode — per context.md's Qwen surface) directly evolvable by the DeepSeek-driven evolve agent, and the only content guard left is the merge-policy check on request-shaping fields (model/endpoint/keys/sampling — D4). Nothing in v4 stops an evolved hook or MCP entry from shipping to the owner's daily machine via `adopt` + daily sync; the diff-review sentence is gone from walk (a) (adopt merges + flips status, no stated review step). Not superseded: the review deleted the renderer, not the executable-surface policy. Fix: one paragraph in D4 (V1 evolvable namespace excludes/gates executable settings keys, hooks, MCP config — merge-policy check extended beyond request-shaping) + restore the adopt-time diff review sentence in D9/walk (a).

**L2. No-eval-no-ship gate at sync + moved-main guard at adopt (v3 D7 "ship gate" + D12 refuse/`--rebase-and-reeval`). Severity: HIGH.**
v3 closed the merge-time hole explicitly: `research sync` re-hashed `harness/`@HEAD and refused when that hash had no scorecard (`--force` escape); `promote` refused when main had moved past the seed SHA. v4's derived baseline ("most recent adopted scorecard whose tree OID matches `main:harness`") makes an unevaluated hand-edit *detectable* — no scorecard will match — but v4 never states that sync refuses/warns in that state, what the derived baseline resolves to then, or that `der experiment adopt` refuses when `main:harness` has moved from the candidate's recorded baseline OID (exact-replacement merge would silently clobber concurrent owner edits). The harness is the daily driver; owner hand-edits are a normal event. Not superseded by the review (F6 defined the derived baseline; it never addressed the sync/adopt gates, and the retain list keeps managed/live isolation). Fix: sync refuses (with `--force`) when `main:harness` OID has no adopted scorecard; adopt refuses when `main:harness` ≠ the candidate scorecard's baseline OID.

**L3. Comparability guards: same-suite-same-k rule + CONFOUNDED banner (v3 D7). Severity: MODERATE.**
v3: same suite version + same k → comparable; qwen/materializer version mismatch → loud CONFOUNDED banner; suite/k mismatch → refuse. v4 stores the runtime-manifest digest in every scorecard (D9) but states no comparison-time enforcement anywhere: nothing refuses or flags a candidate-vs-derived-baseline delta computed across differing suite version, k, or runtime manifest (Pier/Qwen-archive/proxy-policy drift). Interleaved confirmation runs are inherently same-window/same-manifest, and the chart takes only full-suite reporting-k points, so promotion itself is guarded — but ledger "observed delta" fields and optimizer-vs-baseline comparisons are not. The word CONFOUNDED does not appear in v4. Fix: one rule in D9 or D6-normalizer — deltas only across scorecards with equal suite version + k; runtime-manifest digest mismatch renders the delta only under a confound flag.

**L4. Confirmation set never analyzed by ADB (v3 D8). Severity: MODERATE.**
v3's holdout was "never referenced by the loop, never analyzed by ADB." v4 retains aggregate-only publication and explore-source exclusions (D8) but drops the ADB exclusion. Under v4, confirmation-run traces could legally flow into the ADB boundary view and into the Codex critic's "distilled trace evidence" bundle (D10), feeding confirmation-task specifics back into hypothesis generation — exactly the leak the disjointness rules exist to prevent. Fix: add "confirmation-set traces are excluded from ADB analysis and from proposal-evidence bundles" to D8's leak controls.

### 2.2 Correctly retained (spot-checked present in v4)

Disjointness testing (pairwise, preflight + CI — D8, D12); secret scrub (finalizer D3 + janitor D12); evidence retention (last-N + digest-referenced — D12); notify shim with {iteration cost, cumulative, balance, ceiling flag} (D12); live-state protection (list versioned per qwen release, doctor-checked, sync never overwrites, feedback manual — D4); ceiling-flag semantics (systemctl stop + `COST_CEILING_REACHED` gating `ExecStartPre` + notification — D12); acceptance tests (kill -9/resume with re-spend documented, ceiling stop/flag/notify, induced fault → invalid — D12); preflight/doctor (Docker, disk, Pier + archive cache, disjointness, proxy 1-token ping, version-skew warning, live-state list version — D12); observed-model assertion moved to normalizer (D5); golden fixtures + strict mode at normalizer/view (D6); error taxonomy recast as failed/invalid with no imputation (D3/D7/V5); cold-start full-suite baseline (build 6); overlay safety defaults (`max_iterations: 10`, finite timeouts, best_of_n off, explore off — D12); immutable scorecards + pricing/schema changes apply to new runs only (D9); prepaid provider wall (D12); keyless containers + proxy pin (D5); NexAU host dependency acknowledged (§2); ADB partial-open disclosure + license check (D1, V8); balance-endpoint check (V9); server-prereq/rate-limit check (V10); task-revision pin/mirror (V7, V10).

### 2.3 Correctly deleted / superseded

All-k task attribution (→ pass fractions, D7 — see fact check a); "latest job dir" recovery (→ fail-closed exact identity, D3); job-dir fencing/hygiene rules (→ exact job identity supersedes); harbor PATH-shim flock (→ direct adapter + one lock); run-flag smoke-queue nuance (→ serialized queue); sole-committer cron postprocess (→ synchronous finalizer); dashboard merge driver (→ single writer); baseline.json + tar hash (→ derived baseline + tree OID); model slots + allowlist rendering (→ overlay-wins + request-shaping merge check + keyless containers; the enumeration itself survives in D4); holdout rotation-after-5-failures (→ Q2 version triggers incl. ~20-hypotheses adaptive-exposure — owner-endorsed replacement); verdict-timing note (N scorecard / N+1 flip verdict, async dashboard cells) — superseded: verdicts are now experiment-level, set after confirmation, written atomically by the finalizer; AHE's internal predict-then-verify-next-rollout semantics survive in walk (b); vendored npm tarball install (→ standalone archive); sign-test gate + `research diff` flip table (→ contract reporting); der-harbor fork and in-tree registration (→ import path).

---

## 3. FACT CHECKS

**(a) AHE per-task all-k pass state — VERIFIED.**
`evolve.py` `compute_stats` (line 599): docstring line 602 — "When k>1, groups trials by task name: a task passes only if ALL k rollouts pass." Implementation (~lines 656–669): `task_results[task] = "pass"` iff `tp == len(trials)`, `"exception"` iff all trials exception, else `"fail"` — so 4/5 and 0/5 both land as `"fail"` in the comparison state that feeds `task_history.json` and the cross-iteration flipped/regressed attribution (lines ~787–900). Headline metric when k>1 is the pass@1 Chen-et-al. estimator (line 695), i.e., an average — exactly the review's mismatch. Missing `reward.txt` → `"exception"` (lines ~631–645), confirming v4 §2's claim too. v4 correctly carries this as ▽/V4; this check resolves V4 as TRUE — the pass-fraction patch (D7) is justified and its seam is real.

**(b) Which parser executes in `adb ask` — RESOLVED, with a correction to v4 D6.**
Local evidence: `evolve.py` invokes `adb ask -t <traces>` as a **subprocess** (lines 1463–1464) of an executable pip-installed from the bundled closed-core directory `agents/evolve_agent/skills/agent-debugger-cli/_source` (`_ensure_adb_installed`, lines 1193–1213; `EVOLVE_AGENT_DIR` at line 36). The open vendored top-level `trace_converter.py` (header: "Vendored from agent_debugger_core.runtime.trace_converter to avoid an extra package dependency") is imported by evolve.py in exactly one place — line 2944, inside `_dump_evolve_tracer_to_disk` — to serialize the **evolve agent's own host-side tracer** to cleaned form. A console-script subprocess resolves `agent_debugger_core.runtime.trace_converter` from its own installed package; the repo-top-level file cannot shadow it. **Therefore the closed `_source` bundle carries its own parser copy, and that copy — not the open vendored file — is the live code path in `adb ask`.** Consequences for v4: (i) D6's "patch the parser... (preferred; the open vendored parser is the candidate — V6 verifies which copy executes)" is mis-aimed — patching the open vendored file alone cannot change `adb ask` behavior; the honest-naming patch target is the bundled `_source` package (pre-`pip install`, feasible iff it ships source form — that residual question, plus licensing, is properly V6/V8) or the view boundary fallback v4 already specifies. (ii) The review's "provider-neutral LLM-call role" option does not satisfy the current parser unpatched: `is_llm_span` (trace_converter.py lines 361–378) requires a name containing one of `LLM_SPAN_NAME_KEYWORDS = {openai, anthropic, gemini, gpt, llama}` even for `type: LLM` spans — deepseek/qwen absent, matching v3's audit. (iii) The vendored copy still matters host-side (evolve-agent trace dump); a patch there is separate. V6 is correctly on v4's Section 8 list; it should be re-worded to reflect the resolved direction. Note: `extract_agent_behavior_stats` (evolve.py line 1016) counts spans by `type == "LLM"/"TOOL"` from the already-cleaned trace and does not itself keyword-match.

**(c) Pier CLI surface + structured results — VERIFIED (from source, github.com/datacurve-ai/pier @ main).**
`src/pier/cli/jobs.py`: `-p/--path` (lines 499–503), `-i/--include-task-name` (512–513), `--agent-import-path` "Import path for custom agent" (316–320), `--n-concurrent` → `n_concurrent_trials` (265–271), `--n-attempts` (186–192), retries (282). Structured results: pydantic `TrialResult`/`VerifierResult` (rewards dict) / `JobStats` (pass_at_k, token + cost fields, exception stats); `verifier/reward.json` and `verifier/reward.txt` both defined (`models/trial/paths.py:41–42`); `verifier/ctrf.json` (viewer/server.py:3196). README: augmented ATIF v1.7 trajectories; envs `docker`/`modal` (Modal-not-E2B confirmed); per-agent network allowlists honored under `allow_internet = false`; "Pier does not currently resolve or download Harbor registry datasets directly" (confirms the review's registry-vs-local-path contract difference); no built-in qwen-code agent, so DerQwenAgent-via-import-path is required, as v4 assumes. PyPI `datacurve-pier`: releases 0.1.0/0.2.0/**0.3.0** (latest) — "exact Pier 0.3.x pin" is satisfiable and currently means 0.3.0. Cross-check deep-swe README: DeepSWE v1.1 grading requires Pier ≥ 0.3.0, `pre_artifacts.sh` patch extraction, pristine-container grading, and verifier output layout `verifier/{reward.json (binary reward + pass fractions), ctrf.json, test-stdout.txt, run.log, reports/}` — v4's ▽ "exact result layout pinned at step 1" remains prudent and is on the list (V1).

**(d) Qwen Code standalone/offline archive — VERIFIED (QwenLM/qwen-code docs).**
Official installer supports `detect`/`standalone`/`npm` methods; standalone archives bundle a private Node.js runtime (no local Node needed); offline flow = download release archive + run installer with `--archive PATH` with `SHA256SUMS` in the same directory; installs to `~/.local/lib/qwen-code` with shim at `~/.local/bin/qwen` (Windows equivalents documented). Matches v4 D4/§2 ▲ exactly; v4's ▽ V3 (archive contents/deps verified live) is appropriately still on the list. One documented caveat worth carrying into V3: docs state standalone installs are "not yet fully equivalent to npm installs" in some respects — verify the delta covers headless/project-config behavior der needs.

Summary: (a) VERIFIED · (b) RESOLVED WITH CORRECTION to D6/V6 wording (closed-core copy executes; open vendored file is not the `adb ask` path) · (c) VERIFIED · (d) VERIFIED. Everything v4 marks ▽ genuinely appears in its Section 8 list (V1–V10 cross-checked against §2's ▽ markers — complete).

---

## 4. CONSISTENCY / CONSTRAINTS

**Owner constraints — no violations found.**
- AHE as research-loop base: retained (vendored evolve.py drives the loop); the one-seam patch set is exactly what the owner-endorsed external review demanded — not a violation. PATCHES.md discipline retained (D1).
- DeepSeek v4 pro pinned for rollouts: D10 pins rollout agent, ADB, and evolve agent to DeepSeek; enforcement at network boundary (D5, keyless containers, proxy-observed model in scorecards). The GPT-5.6-Sol Codex critic is owner-triggered, outside the measured path and the unattended path — per the review the owner delivered.
- Qwen Code base: retained (D4 runtime-shaped Qwen project; pinned archive).
- Public dashboard/notebook: satisfied via the generated README block + lifecycle notebook entries (VISION's "README dashboard charts" — DASHBOARD.md deletion doesn't violate it).
- CLI + autonomous loop: both doors over one EvalRunner (D3); CLI door ships owner value at build step 5.
- Stage 2 blocked on owner approval: stated in v4 header.

**Internal consistency — no contradictions found**; two ambiguities worth one sentence each (non-blocking, listed here because they touch mechanism):
- Experiment-record granularity for autonomous sessions: D3's finalizer "appends the generated result block to the lifecycle record" and D9's "one active experiment" imply one record per AHE session with per-iteration scorecards, but v4 never says so; walk (b) says "finalizer per run." State it (a ~10-iteration night = 1 lifecycle record + N scorecards, or N records — pick one).
- The proxy now enforces RunBudget max-cost (D5/D3), which requires it to count usage — v3 explicitly declared the pinning proxy "not metering." The expansion is review-mandated (elegance row 17) and fine, but D5 should acknowledge the proxy now meters enough to enforce the cap, so Stage 2 sizes it accordingly.

---

## 5. NON-BLOCKING NITS

1. D6/V6 wording: re-point the honest-naming patch candidate per fact check (b) (closed `_source` copy executes in `adb ask`; open vendored copy is host-side only; provider-neutral role needs a parser patch either way).
2. `turns` appears in the scorecard schema (D9) without v3 D6's definition ("count of assistant-message events"); restore the one-line definition.
3. v3 D6's bounded incomplete-run handling ("re-queue once, then alert") is thinned to "rerun-or-excluded" (D3); state the retry bound and alert.
4. Q2 selection guidance absorbed but not restated: coverage across the official difficulty spectrum (without threshold use), spread across 20–40/40–60/60–80 der-relative sub-bands, difficulty redefined as pass-probability under the fixed model + baseline harness, stratify by failure mode/task shape/repo scale/verifier structure, language as coverage constraint not quota, and Tura's do-not-import list. §9 adopts the protocol by reference; a pointer sentence in D8 would prevent drift.
5. Daily-sync collision semantics: with the renderer gone, state how sync-copied managed skills coexist with auto-learned skills in the same `.qwen/skills/` tree (managed-name manifest; never delete non-managed entries) — the live-state list covers categories, not name collisions. (v3 had the `skills/der-managed/` namespace for exactly this.)
6. DerQwenAgent's qwen-session→ATIF emission is der-owned conversion code (Pier's built-ins emit ATIF; a custom agent must supply its own); build step 2's hand-trace + fixtures cover it implicitly — name it explicitly under D6's fixture scope.
7. v3 D1's upstream re-sync hygiene (diffs exclude `der/`, run outputs) dropped from D1 — trivial to restate.
8. "Pier 0.3.x" pin: only 0.3.0 exists today; record the exact version+commit at step 0 (v4 already plans this).
9. Q5's "a proposal can be rejected without running and still remain in history" is implied by the ledger + status field but the proposed→rejected (unrun) transition isn't named in D9's status flow.
10. DeepSWE v1.1 leaderboard no longer reports wall-clock (host-dependence) — v4's wall-clock metrics are same-box self-comparisons, so fine, but the README scope note could say so when latency experiments are published.

---

## 6. VERDICT

**GAPS-FOUND** — the external review is integrated essentially completely (6/6 findings, 6/6 Q-answers, 17/17 deletes, 9/9 retains, 5/5 approval conditions, build order intact; no owner-constraint violations), but four still-applicable v3 protections were silently dropped (executable-content gate + adopt-diff review; no-eval-no-ship sync/adopt gates; comparability/CONFOUNDED guard; ADB exclusion for the confirmation set) and one D6/V6 factual mis-aim needs correction (the closed `_source` parser, not the open vendored file, executes in `adb ask`) — all fixable with a handful of paragraphs in v4, no re-restructure.
