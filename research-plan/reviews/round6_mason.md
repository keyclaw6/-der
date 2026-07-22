# Round 6 — Stage 2 plan audit (Mason)

Audit target: `research-plan/2026-07-21-der-auto-research-loop-stage2.md` (35 tasks, 9,185 lines at commit bdcaf99; 9,920 lines after fixes). Spec: `draft_v4.md`. Contract: `STAGE2_PROMPT.md`. Verified facts honored: `reviews/round5_sentry.md`. All edits applied directly to the plan file; the original is preserved at bdcaf99.

Headline: Tasks 0–9 are dense, source-anchored, and internally consistent (the author's digests in the Task 7 golden fixture were byte-correct on independent recomputation — impressive). Tasks 10–18, however, were drafted against a **parallel naming universe** (`require_passed_pin`/`write_discovery_pin`/`ProxyRegistry`/`load_record`/`AttemptStatus`/sqlite state/a different experiment front-matter schema/different pin field names) that matches nothing Tasks 0–9 build — a cold executor would hit AttributeError/TypeError/ValidationError at nearly every live step of Milestones 1–3. Tasks 19–34 are self-consistent but code-sparse. I repaired the naming universe by (a) adding the two pins-API convenience functions the later tasks already call, and (b) surgically rewriting the drifted steps of Tasks 10–18 against the interfaces Tasks 0–9 actually produce. Coverage of the spec itself was essentially complete; only two consumed-but-never-created fixtures and a handful of nonexistent CLI invocations were true gaps.

---

## 1. COVERAGE MATRIX

### Decisions D1–D12

| Decision | Task(s) | Status |
|---|---|---|
| D1 vendoring, PATCHES.md, retired zero-patch | 20 (vendor + ledger), 21 (four-seam patch), 1 (UPSTREAM.md) | COVERED |
| D2 Pier sole evaluator; DeepSWE primary; 8-point chain; T-B unscored smoke | 0 (pin `datacurve-pier==0.3.0`), 1 (V7), 10 (V2 chain), 34 step 7 (unscored smoke) | COVERED |
| D3 EvalRunner contract; RunBudget; fail-closed; finalizer; validity taxonomy | 2 (EvalSpec/EvalResult), 5 (budget ledger), 12 (taxonomy), 16 (argv/process, exact `Results written to`), 17 (runner + lock), 28 (finalizer) | COVERED |
| D4 runtime-shaped harness; staging overlay; deny policy (request-shaping + executable); archive packaging; managed/live separation | 6 (V3 archive), 7 (staging + two-class deny policy), 23 (harness files, live-state, guarded sync) | COVERED |
| D5 pinning proxy; keyless containers; proxy-observed model | 5 (policy), 8 (proxy/registry/observations/budget), 10 (live route + keyless proof) | COVERED |
| D6 canonical evidence; ADB ephemeral view; golden fixtures + strict mode | 9 (der-owned ATIF conversion — sentry nit 6 satisfied), 11 (V1 shapes), 14 (normalizer + committed live fixtures), 31 (V6 boundary view, honest identity) | COVERED |
| D7 preregistered contracts; pass-fraction attribution; no universal gate; CONFOUNDED comparability | 2 (contract models), 20/21 (pass fractions into optimizer), 24 (comparability/CONFOUNDED), 28 (metrics/decision, no significance test) | COVERED (one deviation: primary-metric vocabulary — §3) |
| D8 calibrated frozen suites; three classes; leak controls | 4 (disjointness incl. cross-version confirmation rule), 26 (calibrate/freeze/CI), 27 (full-suite baseline, aggregate-only confirmation), 31 (ADB exclusion), 32 (critic-bundle exclusion) | COVERED |
| D9 three-level identity; immutable scorecard; lifecycle record; derived baseline; adopt/sync gates | 3 (tree OID + manifest digest), 4 (records/transitions), 15 (immutable writer + hand trace), 23 (no-eval-no-sync + `--force`), 24 (derived baseline, no baseline.json), 25 (adopt refusal, `--rebase-and-reeval`, EXECUTES ON YOUR MACHINE) | COVERED |
| D10 model-role table | 8/10 (rollout via proxy), 20 step 5 (ADB/evolve pinned DeepSeek in overlay), 32 (owner-triggered `codex exec` critic, read-only, schema output, provenance, no shim) | COVERED |
| D11 one generated README block | 29 (marker pair, hero SVG, full ledger, resource strips, no dashboard/badges) | COVERED |
| D12 ops floor | 17 (doctor/lock), 33 (V9 + watchdog + ceiling flag), 34 (systemd units, `ExecStartPre` gate, janitor, notify, runbook, recovery drills incl. kill-9/ceiling/induced-fault) | COVERED |

### Milestones M0–M8 (phase order preserved, 0→5 spine intact)

M0→Tasks 0–5 · M1→6–13 · M2→14–15 · M3→16–19 · M4→20–22 · M5→23–25 (owner-value gate, honest adopt-or-reject) · M6→26–27 · M7→28–29 · M8→30–34. All mapped; every task ends in a commit step.

### Verification items V1–V10 (all have probe script + pin file + exit-78 STOP + downstream pin reads)

| V | Task | Pin file |
|---|---|---|
| V1 layout/reward/ctrf/ATIF-usage | 11 (+14 step 1 extension) | `pins/v1-pier-artifact-layout.md` |
| V2 eight-point chain + proxy route | 10 | `pins/v2-acceptance-chain.md` |
| V3 archive-in-container install | 6 | `pins/v3-qwen-archive-install.md` |
| V4 all-k seam minimality | 21 | `pins/v4-ahe-attribution-seam.md` |
| V5 induced-fault classification | 12 | `pins/v5-fault-classification.md` |
| V6 ADB runtime parser | 31 | `pins/v6-adb-runtime-parser.md` |
| V7 DeepSWE revisions/verifier audit | 1 | `pins/v7-deepswe-revisions.md` |
| V8 ADB `_source` license | 30 | `pins/v8-adb-license.md` |
| V9 DeepSeek balance endpoint | 33 | `pins/v9-deepseek-balance.md` |
| V10 capacity/concurrency 4–8 | 19 | `pins/v10-server-capacity.md` |

Contract compliance: header block present; **Global Constraints verbatim-identical to STAGE2_PROMPT (byte-compared)**; file-structure map precedes tasks and is referenced; every task has Files + Interfaces; discovery gates use pins + STOP semantics; placeholder sweep clean (no TBD/TODO/"similar to Task"/empty fences); no forbidden terms ("holdout", E2B/Modal, DASHBOARD.md, baseline.json, badges appear only in prohibition/negative-check contexts); rollout model everywhere `deepseek-v4-pro` behind the proxy; `datacurve-pier==0.3.0` is the only evaluator pin.

---

## 2. FIXES APPLIED (58, all direct edits)

Pins/errors bridge (unlocks Tasks 10–19 as written):
1. Task 0 `pins.py`: verification-id check `startswith("V")` → accepts `V#`/`M#` (Task 13's M1 milestone pin would fail to load).
2. Task 0 `errors.py`: added `ContractError`, `EvaluationError`, `ProcessLockError`, `UnevaluatedHarnessError`, `NoEvaluatedBaselineError` — imported by Tasks 16/17/23/24 but never defined anywhere.
3. Task 6 Step 5: added `require_passed_pin(ref) -> values-dict` and `write_discovery_pin(...)` wrappers over `load_pin`/`write_pin` — ~40 call sites in Tasks 10–19 used these names with no definition.

Task 6 (V3 discovery):
4. `v7.require(...)` → `v7.value(...)` (2 sites; `PinDocument` has no `require`).
5. Step 1: `--prefix` adaptation note — only `--archive` is source-verified (round5 fact d); a missing `--prefix` is flag-shape adaptation inside the gate, not a spec contradiction/STOP.

Task 7 (staging):
6. Golden `staging-manifest.json`: pretty-printed JSON with SKILL.md-first ordering → exact compact canonical line with sorted-path ordering (`settings.json` first). Digests independently recomputed and confirmed correct; only format/order were wrong — the byte-equality test would have failed.
7. Files/Step 5: removed duplicate Create of `harness/__init__.py` (exists from Task 3).

Task 8 (proxy):
8. Test `ledger.create(...)` → `register_run(run_id, budget, now, expected_attempts=...)` (Task 5's real method).
9. `app.py` `ledger.reserve_request(...)` → `authorize_request(...)`.
10. Added return annotations to `authorize`/`chat_completions` + `RunRegistration` import (`mypy --strict` is asserted clean).
11. `finalize` rewritten to **always append an observation row** (success or provider fault, status_code recorded) — D5's observation log otherwise missed exactly the faults V2/V5/normalizer must classify.

Task 9 (agent):
12. Note: `setup()`'s install line mirrors V3's pinned `install_argv`; the pin, not the listing, is authoritative.

Task 10 (V2 — heaviest repair; was written against nonexistent APIs end to end):
13. Interfaces block: real `stage_harness`/`RunRegistry.issue -> IssuedRunToken`/`BudgetLedger.register_run` signatures; pin fields `qwen_binary`/`container_image_id`/`task_root`/`task_ids`.
14. Step 1 `main()`: `ProxyPolicy.from_toml`/`ProxyRegistry(sqlite)`/`budgets=`/`provider_key=` → real `create_app` wiring (`ModelPolicy` + `Pricing` via new `load_policy_and_pricing` tomllib loader, `RunRegistry`/`BudgetLedger` file stores, `provider_base_url`/`provider_api_key`, `now=utc_now`); import block corrected.
15. Step 2 tests: created the job-level `result.json` both tests assert against (both would have failed as written); observation rows in `ModelObservation` shape.
16. Step 4 inspector: match by `run_id` + `status_code==200` (was `experiment_id`/`job_id`/`status:"completed"` — fields that don't exist in the log); `--run-id` argparse.
17. Step 6: hand-written front matter used a wrong schema (`schema_version: 1`, top-level hypothesis, `run_budget.max_usd`…) and validated via nonexistent `load_record` → record generated through `create_record`/`ExperimentFrontMatter` with real fixture-harness identity; validation via `read_record`.
18. Step 7: healthz expected output includes `policy_id`.
19. Step 8: `task_image_id` → `container_image_id`.
20. Step 9: staging/token issuance rewritten — `stage_harness` 4-arg from `tests/fixtures/harness/managed` (the managed `harness/` does not exist until Milestone 5 — the original staged a nonexistent directory), `RunRegistry.issue` + `BudgetLedger.register_run` with a real `RunBudget`, `RUN_ID=RUN-EXP-0001-acceptance-chain-smoke-01`.
21. Step 10: V7/V3 pin keys corrected (`checkout_path`→`task_root`, `candidate_task_ids`→`task_ids`, `binary_path`→`qwen_binary`).
22. Step 12: `--experiment-id/--job-id` → `--run-id`; `der pin show V2` → `der pins assert V2`.

Tasks 11–13:
23. Task 11 Step 5 / Task 12 Step 9: `der pin show` → `der pins assert` (the CLI Task 0 actually built).
24. Task 12: `AttemptStatus`/`InvalidReason`/`INCOMPLETE_RESULT`/`INFRASTRUCTURE` (none exist in Task 2) → `OutcomeKind`/`FailureReason` with `AttemptClassification` defined in `classification.py`; failed limits map to `AGENT_TIMEOUT`/`CONTEXT_TIMEOUT`, reward-0 to `TASK_ASSERTION`, no-evidence to `INVALID/INFRA`; tests + Interfaces updated.
25. Task 13 Step 2: `DiscoveryBlocked` → `DiscoveryBlockedError`.
26. Task 13 Step 4: `transition_record(target="running", evaluator_job_id=...)` (string target fails enum-set membership; parameter doesn't exist) → enum target + `now=` + `append_run_id=`.

Task 14 (normalizer):
27. Step 1: exact V1 extension keys named (`*_pointer` fields the normalizer reads verbatim).
28. `_observation_rows` by `run_id` (the only key the proxy actually logs); completed-row (status 200) model assertion; fail-closed when a run has no completed row.
29. `_failure` replaced by `_classify` delegating to Task 12's `classify_attempt` — one precedence table instead of two divergent ones; unattributable run-scoped fault rows never invalidate an attempt that produced a valid binary reward (no imputation in either direction).
30. Per-attempt `cost_usd` derived from that attempt's ATIF usage at the pinned policy prices; run-level `resources.cost_usd` stays proxy-observed; honesty note added (the run-scoped log cannot split dollars per attempt).
31. Attempt-index rebasing to zero-based contiguity (Pier's raw numbering may be 1-based; contract requires `range(k)`), raw numbering preserved in `trial_name`/`trial_dir`.
32. Step 7: creates `tests/fixtures/contracts/eval-spec.json` — consumed by four tasks, never created anywhere; fixture observation-row guidance (run_id alignment; invalid fixture needs one 200 row + one 503 row + non-binary reward).
33. Step 9: constructs `var/runs/v2/eval-spec.json` (read but never written) with the real probe identity (fixture-harness tree OID + RuntimeManifest from V3/V7/locked revisions).
34. Files/commit blocks updated for the new fixture.

Task 15 (scorecard):
35. Run directory `RUN-...-candidate-01` → `RUN-...-smoke-01` everywhere (must equal the `run_id` inside the normalized result; observation selection is keyed on it).
36. Step 1: generates `tests/fixtures/contracts/scorecard.json` through the models (consumed, never created).
37. Step 6: `current_identity(cwd, "harness")` (function doesn't exist; directory doesn't exist yet) → identity taken from the normalized result.
38. Step 7: `attach_scorecard` implemented in `records.py` (was called, never defined); terminal transition fixed (enum + `now` + `terminal_reason`); Files/Interfaces/commit updated.

Tasks 16–17 (seam):
39. `build_pier_argv` emitted agent kwargs (`staged_harness_dir`, `run_token`, `proxy_pin`, `archive_pin`) that `DerQwenAgent.__init__` does not accept — guaranteed TypeError on the first real run. Rewritten to emit the exact Task 9 constructor kwargs Task 10 proved live (archive/installer/binary/managed_harness/owner_settings_json/qwen_environment_json/limits), signature extended with `proxy_base_url` + V3 paths; test rewritten with parsed-kwarg assertions; run token confined to `qwen_environment_json`.
40. Task 17 runner: normalizer call fixed (`v1=`, `observations_path=` — was `proxy_observations=` and missing `v1` entirely); `build_pier_argv` fed from V2/V3 pins; `RegistryTokenIssuer` adapter over `RunRegistry`/`BudgetLedger` specified (issue registers both stores, revoke deletes the registration).

Task 18 (battery — second-heaviest repair):
41. Step 1: V7 read via `require_passed_pin` (was regex for a JSON block that the V7 pin does not contain, testing a `verifier_audit` field that does not exist); blocked-amendment guidance replaced a front-matter-corrupting `printf >> pin`.
42. Step 2: `der experiment create` (never implemented) + status `preregistered` (not in the enum) → `create_record` snippet with schema-valid contract; commit-before-run kept as preregistration proof.
43. Step 3: `der harness stage`/`der eval spec-from-record` (never implemented) → `stage_harness` + `EvalSpec` construction snippet; stages the fixture harness (managed `harness/` arrives at M5); conservative pre-V10 `n_concurrent=2` noted.
44. Step 4: removed `dotenvx` around Pier (it would have injected `DEEPSEEK_API_KEY` into the evaluator shell — the exact thing Task 10 asserts absent); added proxy health check, key-absence test, and the RUNNING transition.
45. Step 5: `der experiment finalize` (Task 28's deliverable) and "README block updated" (Task 29's) → composition of proven primitives (`write_scorecard_once` + `attach_scorecard` + terminal transition), matching the milestone's actual dependencies.
46. Step 6: `der scorecard verify` (never implemented) → schema/immutability verification snippet.

Tasks 19–34:
47. Task 19: `DiscoveryContradiction` → `DiscoveryBlockedError`; `der pin verify PATH` → `der pins assert V10`.
48. Task 20: `research/UPSTREAM.md` Create → Modify (Task 1 created it); vendor source = pristine `/var/cache/der/sources/ahe` instead of a fresh clone.
49. Task 22: note pinning the toy-loop CLI flags to the vendored `evolve.py`'s actual surface (record actual invocation; no new CLI beyond the four seams).
50. Task 23: `compute_harness_identity` → `compute_identity`; `der harness policy-check` subcommand defined with its exact output contract (Step 1 depended on it, Step 5 didn't declare it).
51. Task 24: baseline OID source wording → `git(repo_root, "rev-parse", "main:harness")` (`git_tree_oid` takes a directory, not a rev).
52. Task 26: manifest/disjoint modules + tests Create → Modify (Task 4 created them); `SuiteManifest` extension locked to Task 2's field names (`version`, not `suite_version`) with schema/fixture regeneration in the same commit; visible-ID sets clarified as leak-check arguments, not manifest fields.
53. Task 27: Steps 3–4 rewritten — the one-command finalizer/README belong to M7 (spec order), so the initial adopted baseline composes the Task 18 primitives with an explicit bootstrap assertion (`NoEvaluatedBaselineError` + candidate OID == `main:harness`); nonexistent `der scorecard verify`/`der evidence assert-no-confirmation-leak` → real resolver/`scripts/check.py` verification snippet.
54. Task 28: `artifact_manifest.py` + test Create → Modify (Task 14 created them); decision verdict names `qualifies/rejects/...` → Task 2's `PromotionVerdict` values.
55. Task 29: markers `DER:BEGIN` → `DER:START` (the file map's contract for README.md).
56. Tasks 30/31: `--ahe-checkout var/upstream/ahe-faf44bc4` → `/var/cache/der/sources/ahe`; `der pin verify` → `der pins assert V8`. Task 32: `templates/experiment.md` Create → Modify. Task 34: Files/commit add `research/der/cli.py` (`der lock probe`, `der smoke terminal-bench`, `der doctor --require-unattended` had no home).
57. Task 2: Files list adds `research/schemas/critic-proposal.schema.json` (exported and tested but unlisted); import-order fixes in `schema_export.py` and `records.py` (ruff `I001` would break the "no diagnostics" expectations); Execution conventions gain item 9 (a ruff `--fix` pass for I001-only transcription diagnostics is repair, not assertion-weakening).
58. Phase 1 milestone exit: "V1–V5 pins passed" → V1/V2/V3/V5 (+V7 from Phase 0); V4 belongs to Phase 4.

---

## 3. DEVIATIONS FROM SPEC (logged, not silently kept/reverted)

1. **`ExperimentContract.primary_metric = Literal["confirmation_macro_pass_at_1"]` (Task 2) — KEPT.** D7 names a metric family ("macro pass@1 delta; valid-task median token reduction; wall-clock reduction"). The plan's single-literal restriction means efficiency experiments cannot declare a token/latency primary metric at V1. Kept because (a) the guardrail machinery accepts arbitrary metric names, so efficiency concerns are expressible as guardrails now, and (b) widening the Literal without implementing those metrics in Task 28's decision engine would allow contracts the system cannot evaluate — worse than a visible restriction. Recommendation: widen Literal + metrics engine together when the first efficiency experiment is preregistered; owner sign-off desirable.
2. **Scorecard field list vs D9 — KEPT as equivalents.** "Experiment ID/status" → `experiment_record_sha256` + embedded `PromotionDecision`; "retry+exclusion records" → `--max-retries 0` policy plus invalid attempts recorded in place (never imputed, never silently excluded); "task revisions" carried via the runtime-manifest digest + suite manifest rather than duplicated per scorecard. Faithful to intent; noted for the record.
3. **Concrete upstream revisions in the header** (DeepSWE `8cae…`, Qwen v0.20.0 `92fda…`, Pier `e69a…`, AHE `faf44…`) — the spec left freezing to M0; the plan pre-freezes and then *verifies* at Task 1 with STOP-on-mismatch. KEPT (verified-not-trusted), see Escalation 2.
4. **Proxy meters usage to enforce RunBudget max-cost** — expansion beyond v3's "not metering" proxy, mandated by review row 17 and anticipated by round5 §4; implemented with real accounting. KEPT.
5. **Normalizer taxonomy nuance (introduced by my fix 29):** a run-scoped provider-fault row does not invalidate an attempt that produced a valid binary reward when the run has >1 attempts (attribution honesty); with certain attribution (single-attempt runs, or rewardless attempts) the Task 12 precedence table governs unchanged. This is the least-imputing reading of D3/D7; flagged for author awareness.

---

## 4. ESCALATIONS (need owner/author input; not fixable by audit)

1. **Density cliff, Tasks 17–34.** Tasks 0–16 carry full test/implementation code; Tasks 17 (steps 2–3, 5–7), 19, and 22–34 specify exact assertions, CLI shapes, exit codes, and STOP rules in prose but not full code blocks — below STAGE2_PROMPT's letter ("code steps require code blocks", tests written out). The enumerated assertions are precise enough for a skilled zero-context developer, but the mission brief warned the executor "doesn't know good test design very well". Owner choice: accept the judgment tier for Phases 5–8 or commission a densification pass.
2. **Unverifiable-offline literals:** Qwen v0.20.0 and DeepSWE v1.1 tag commits, Pier tag commit, AHE commit, and the DeepSeek v4 pro pricing trio (`0.003625/0.435/0.87` per 1M). Each is guarded by a verify-at-execution STOP (Tasks 1/6/8), so a wrong value halts safely instead of corrupting — but the author should confirm they are transcribed, not hallucinated, to avoid spurious STOPs on day one.
3. **Autonomous record creation:** the file map promises `integrations/ahe.py` "creates experiment records", but preregistration for AHE iterations is only shown manually (Task 22) and the unattended service (Task 34) doesn't spell out the per-iteration record-creation call. One explicit step is needed from the author (or accept Task 34's service as the composition point).
4. **Terminal-bench smoke source (Task 34 step 7):** no terminal-bench task cache/mirror is provisioned anywhere; one sentence on where the cached task comes from is required before that step is executable.
5. **Qwen stream-JSONL subtype strings** (`error_max_turns` etc., Task 9 fixtures) are declared source-shaped and the plan itself subordinates them to V1/V2 live evidence — acceptable, but the author should confirm the greps in Task 9 Step 1 actually surface those literals at v0.20.0.

## 5. COLD-EXECUTABILITY SPOT-CHECK

- **Task 1 (early discovery, V7):** simulated cold: clone-locked cache commands, fixture, script, and STOP path all self-contained; `write_pin` local to the script (no forward deps); executable as written. PASS.
- **Task 7/8/14 (mid TDD):** simulated cold and found the four blockers now fixed — golden-manifest byte mismatch (fix 6), ledger method names (8–9), mypy-strict annotations (10), missing contract fixtures + wrong observation schema in the normalizer (27–33). After fixes, every command has an existing referent and the expected outputs are derivable. PASS (post-fix).
- **Task 18 (late integration):** originally required five CLI commands that no prior task builds, a pin field that doesn't exist, a status outside the enum, and a harness directory that isn't created until Milestone 5 — a cold agent would have had to invent half the system. Rewritten to compose only interfaces produced by Tasks 4/7/15/17; re-simulated end-to-end (record → stage → spec → run → scorecard → verify) with no invention required. PASS (post-fix).

## 6. VERDICT

**READY-AFTER-APPLIED-FIXES** — spec coverage was already complete (D1–D12, M0–M8, V1–V10 all mapped, gates and pins intact) and Tasks 0–9 are execution-grade, but the mid-plan naming-universe drift repaired here (58 fixes) would have stalled a zero-context executor at Milestone 1; the remaining risk is the prose-density tier of Tasks 17–34 and five owner/author escalations, none architectural.
