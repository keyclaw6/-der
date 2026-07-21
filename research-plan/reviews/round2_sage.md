# Round 2 — Sage (implementation-readiness judgment of draft_v2.md)

Ruling question: (a) can the owner approve this understanding what they get; (b) can Stage 2 expand it into an implementation plan without the executing agent making architecture-level decisions? Round-1 blockers (Forge B1–B5, Prism corrections 1–12, Flint O/U lists) are verifiably addressed in v2 and are not re-opened. New evidence below was checked against the vendored source (`/agent/workspace/research-plan/ahe-src/evolve.py`); line numbers refer to that copy.

---

## HIDDEN CHOICES (per decision)

**D1 — vendoring.** Decided (plain copy, pin in UPSTREAM.md, prereqs named). Two residual choices an implementer must not have to make:
- Layout: "vendor AHE as `research/`" plus "new code lives in `research/der/`" (D3) implies der-new code sits *inside* the vendored tree. Plausible and consistent with `research/runs/`-relative behavior, but never stated — nor is the rule that upstream re-sync diffs exclude `der/`, `runs/`, overlays.
- Packaging: the CLI "imports `run_harbor`, `compute_stats`" from evolve.py — whether `research/` remains one uv/Python≥3.13 project (AHE's pyproject extended) or `der/` is its own package determines how that import works. One sentence needed.

**D2 — harbor fork + der agent.** Registration decision fully made (fork-of-fork, in-tree + enum, mirrors nexau; zero-patch target explicit). Two hidden choices:
- Install mechanism at V1: "npm-install pinned qwen at trial setup — or prebuilt task images with `force_build: false` as the optimization" conflates two axes. `force_build` governs task-environment image caching; the agent install script runs per trial regardless unless qwen is baked into images. D9 mandates `force_build: false` + prebuilt suite images, which an agent could read as "qwen is prebaked." Pick: V1 = per-trial npm install of the pinned version; prebaking qwen into images = named later optimization.
- Code ownership/dependency direction: materializer and converter are `research/der/` modules (D3, D6) but execute *inside* `der_qwen.py`, which lives in the der-harbor repo — while `research/pyproject` pins der-harbor. How der_qwen.py reaches that code (der-harbor depends on a der package; code vendored into the fork next to the agent; or agent-embedded) is undecided. Any answer works; the doc must give one.

**D3 — CLI.** Surface enumerated with args for eval/diff. Hidden:
- `research ab` semantics: what are sides A and B (two workspace paths? current branch vs named baseline?) — unspecified; an agent must invent the interface.
- "current baseline" is load-bearing in three places (scorecard `named baseline ref`, D8 gate "vs the current baseline's holdout score", D7 attribution floor) but no registry is named: where the baseline pointer lives and when it updates (presumably on promote-merge).
- Minor: "paired sign-test/binomial CI" reads as two options; name one test.

**D4 — workspace/materializer.** Contract types, rejection behavior, contexts, live-state list, sync — all decided. Hidden:
- `agent.yaml`'s content domain (which Qwen Code knobs it actually drives; the evolvable-vs-pinned enumeration promised in D5) has no assigned home. Assign the enumeration explicitly to Stage 2 with a named starting set, or it becomes an implementer's invention.
- `der sync` introduces a second CLI (`der`) that is never defined anywhere; either name the owner-side `der` CLI as a deliverable or fold sync into `research`.

**D5 — model slots.** Enforcement decided. Hidden:
- The materializer signature `(workspace, context) → config` omits the binding maps, which are a third input; and the maps' locations are unnamed (research binding: which file — the AHE experiment overlay? daily binding: which file outside the repo?).
- "fails validation on any literal model/provider/base_url/temperature string **anywhere** in the workspace" is unimplementable as written over prose files (QWEN.md/skills mentioning a model name in text would false-positive; prose cannot bind a model anyway since bindings only come from outside-workspace maps). Scope the rejection to structured/config surfaces and say why prose is exempt.

**D6 — trace/metrics/error taxonomy.** Converter placement, filenames, span naming, fixtures, strict mode: decided and source-consistent. Two gaps:
- **Verified against source:** evolve.py already has its own taxonomy — a trial with no `verifier/reward.txt` is classified `"exception"` (evolve.py:628–646), and flip analysis separates infra categories (`infra_recovered/infra_lost/exception_to_fail/...`, :844–852) from real flips. D6's `errored` must be stated as mapping 1:1 onto that mechanism, and the mechanism named: provider/infra faults must surface as harbor exceptions (no reward.txt), because a provider 429 that still yields `reward.txt = 0.0` is counted a real **fail** and poisons attribution. As written, "errored is excluded from flip attribution" is asserted without the mechanism that makes it true, and it is missing from the Section 9 list.
- "turns" appears in the scorecard with no definition (assistant events? model calls? task-level turns?) — comparability of the field depends on it.

**D7 — scorecards.** Schema is near-complete. Ambiguities: whether tokens/cost/wall-clock/turns are per-task(-trial) or run-aggregate; missing fields: der-harbor (agent) version — the der agent's code affects results as much as the materializer's — and the dataset reference backing the suite; baseline-ref resolution (see D3).

**D8 — suites/holdout.** Suite mechanics decided. One genuine hidden choice: the gate predicate. "pass-rate delta ≥ 0 ... (CI-aware per D3's diff semantics)" admits two radically different implementations — point-estimate ≥ 0 (inconclusive allowed) vs CI-excludes-zero (at 30 tasks × k=2, nearly nothing would ever promote). State the exact predicate including the treatment of `inconclusive`.

**D9 — budget.** Wall/meter/watchdog decided. One contradiction: the watchdog sends "SIGTERM to the tmux session" while D13 says "systemd units, **not bare tmux**." Whether the systemd unit runs evolve.py directly (then stop = `systemctl stop`, no tmux exists) or wraps AHE's tmux scripts (then Restart/OnFailure semantics need care) is a process-model choice the implementer currently has to make. Also: the provider balance endpoint the meter polls is assumed, not on the verification list.

**D10 — runs layout/locks/clone.** Three findings:
- **Path contradiction with source (new evidence):** evolve.py writes runs to `EXPERIMENTS_DIR / <experiment_name> / "runs" / iteration_NNN` where `EXPERIMENTS_DIR = PROJECT_DIR / "experiments"` is a module constant with no config seam (evolve.py:37, :262, :300). Evolve runs therefore land at `research/experiments/<run-id>/runs/...`, **not** `research/runs/evolve/<run-id>/...` as D10 states. As written, an implementing agent must choose between violating the stated layout and violating D2's zero-patch target. Fix by stating the AHE-native path (with `research/runs/adhoc/` for CLI runs and postprocess scanning both) or by sanctioning a path patch in PATCHES.md. Also disambiguate from the top-level notebook `experiments/` directory, which now collides in name.
- Lock granularity: "while an evolve **iteration** holds it" implies per-iteration acquire/release, which has no seam without patching evolve.py. The implementable reading is a run-scoped lock held by the systemd-wrapped process for the whole evolve run. Reword.
- The per-iteration commit to `research-runs` has no named executor (evolve.py does not commit to the outer repo). Postprocess is the natural owner; say so.

**D11 — dashboard/notebook.** Decided; no hidden choices (committer question covered by D10 fix).

**D12 — promotion.** Steps enumerated but three semantics missing: (a) the branch base — D7 says promotion PRs are "cut against that same seed SHA," the script just says "create branch"; branching from HEAD instead breaks the hash check whenever the owner hand-edited after the seed; (b) copy semantics — exact-replace (delete extraneous files) vs overlay copy changes what the hash check verifies; (c) "require a fresh holdout scorecard" — does promote *run* the holdout eval (cost, lock) or refuse until one exists, and what is "fresh"?

**D13 — ops.** Complete except the tmux/systemd contradiction counted under D9.

---

## INTERFACE GAPS

1. **Materializer:** signature must include binding maps as input and name their locations; output paths per context are correctly delegated to Stage-2 item 6; live-state list needs a stated location (file in repo vs daily config).
2. **Converter:** input/output fully pinned (filenames, span naming, usage shape) — the strongest interface in the doc. Gap: "turns" undefined; error-classification signals (what the converter reads to emit `errored`) deferred to Stage 2 inline but the *mapping to evolve.py's exception path* is the part that cannot be deferred (see D6).
3. **Scorecard schema:** add metric granularity statement, der-harbor/agent version, dataset reference, and the baseline-ref resolution rule.
4. **CLI:** `research ab` argument semantics; `research promote <run>` — what a run-id resolves to (evolve iteration vs adhoc exp) is inferable but worth one line; refuse/exit behavior under lock is specified (`--queue`).
5. **Promote/sync:** branch base, copy semantics, holdout freshness (D12); `der sync` CLI identity (D4).
6. **der-harbor ↔ research/der dependency direction** (D2) — the one interface with no stated owner on either side.

## SKELETON CHECK

Order is sound: 0 kills the two real unknowns for ~$1; 2 consumes 1's output; 4 validates the scorecard schema before 5–8 depend on it; 5 ships owner value before autonomy; 6 validates the converter against its actual consumer before evolve.py consumes anything at 7. No hard dependency inversions. Three wording-level defects:
- Step 1's proof "trace file lands at the contracted path" is ambiguous: the contracted (NexAU) path is the *converter's* output, which arrives in step 2. Step 1's checkable proof is the raw qwen session JSONL landing in the trial's agent logs dir.
- Step 7 requires artifacts no earlier step builds: the retargeted evolve-agent prompt (D4) and the der overlay incl. the der-schema `code_agent_patch` replacement (D5). Add them to step 7's stated scope so Stage 2 sequences them.
- Step 7's proof "rollback fires on a failed prediction" is not deterministically checkable in 2 iterations; note that the acceptance test may inject a contrived falsified prediction.

## SCOPE CHECK

Everything the owner asked for is present with a mechanism: end-to-end autonomous loop (lifecycle a; resumable, budget-capped, unattended per D9/D13); DeepSeek pin enforced structurally (D5); built on the specified AHE repo through verified seams (D1/D2, §2); comparable scorecards + dashboard + notebook (D7/D11); CLI + autonomy dual door (D3); two-stage discipline maintained (Stage-2 gates in §9). Nothing invented: explore, best_of_n, metering proxy, 8-type contract, upstream-harbor migration, and ADB replacement are all correctly parked as named later options, not build items. The holdout gate is the only owner-unrequested mechanism, and it is a justified integrity control mandated in round 1, disclosed in D8/D12. VISION items out of the research loop (mixed-model daily orchestration, leaderboard fun) are correctly left to daily bindings / occasional full-suite runs.

## STAGE-2 READINESS

Section 9 is a genuine empirical gate — every item is a live-install check with a falsifiable outcome. Three unverified assumptions elsewhere in the doc belong on it:
- **Errored-trial mechanics (from D6):** confirm on the pin that an agent-raised error yields `exception.txt` with no `reward.txt` (→ evolve.py classifies `exception` and attribution excludes it), and whether provider faults can instead terminate as `reward.txt = 0.0` "fail" (taxonomy leak); align der `errored` with upstream `exception` accordingly.
- **Provider balance/usage endpoint** for the watchdog meter (D9 polls it; nothing verifies it exists for the chosen DeepSeek account type).
- **In-container npm reachability:** if V1 installs qwen per trial, task containers must reach the npm registry — fold into item 2's `env: docker` end-to-end check.

## PUNCH-LIST (wording fixes; no architecture changes)

1. **D10 must state the real evolve-run path:** `research/experiments/<run-id>/runs/iteration_NNN/` (AHE-native; evolve.py:37/:262/:300 — `EXPERIMENTS_DIR` is a constant, no config seam), with `research/runs/adhoc/` for CLI runs and postprocess scanning both — or explicitly sanction a path patch in PATCHES.md. Add one line disambiguating the notebook `experiments/` dir from `research/experiments/`.
2. **D6 must state the errored↔exception mapping:** der `errored` ≡ evolve.py's existing `exception` class (trial with no `reward.txt`); the der agent surfaces provider/infra faults as harbor exceptions, not reward-0 failures; add the Section-9 verification item above.
3. **D9/D13 must pick one process model:** systemd runs evolve.py directly and the watchdog stops it via `systemctl stop` (or equivalent) — delete "SIGTERM to the tmux session" or reinstate tmux explicitly; the two sections currently contradict.
4. **D2 must pin the V1 install mechanism:** per-trial npm install of pinned `@qwen-code/qwen-code@<version>`; prebaking qwen into suite images is a named later optimization; note `force_build` governs task-env images only.
5. **D2/D6 must state code ownership:** which repo carries materializer + converter and the dependency direction between der-harbor and `research/der` (e.g., der-harbor depends on the der package, or the code lives in the fork beside `der_qwen.py`).
6. **D8 must state the exact holdout-gate predicate,** including whether `inconclusive` passes (e.g., "point delta ≥ 0 and not conclusively negative" vs "CI excludes zero") — the two readings differ by an order of magnitude in strictness at 30×k=2.
7. **D12 must state:** branch from the run's seed SHA (per D7); copy = exact replacement of the managed tree (extraneous files deleted); whether promote triggers the holdout eval or refuses without a fresh one, and the freshness definition.
8. **D3/D7/D8 must name the baseline registry:** where the current-baseline pointer lives and that it updates on promote-merge.
9. **D5 must scope literal-string rejection to structured config surfaces** (prose cannot bind models; bindings come only from outside-workspace maps) and add binding maps to the materializer signature with named file locations for both contexts.
10. **D10 must reword the lock as run-scoped** (held by the evolve process for the whole run; per-iteration release has no seam) and name postprocess as the executor of per-iteration commits to `research-runs`.
11. **Skeleton step 1 proof** = raw qwen session JSONL in the trial logs dir (converted-path proof belongs to step 2); **step 7 scope** must add "retargeted evolve-agent prompt + der overlay incl. der-schema `code_agent_patch`"; note the contrived-falsification acceptance test.
12. **D7 must state metric granularity** (per-task/per-trial, then aggregated), define `turns`, and add `der-harbor version` + `dataset reference` to the schema.
13. **D1/D3 must state the vendored layout** (AHE files directly under `research/`, der-new code under `research/der/`, upstream re-sync diffs exclude der/runs/overlays) and the packaging arrangement that lets the CLI import evolve.py.
14. **D4 must introduce the `der` CLI** (owner-side, currently only `der sync` exists) or fold sync into `research`; and assign the agent.yaml evolvable-param enumeration to Stage 2 with a named starting set.
15. **Section 9 additions:** errored-mechanics check (item 2 above), provider balance endpoint, in-container npm reachability folded into the `env: docker` item.

## VERDICT

**CONVERGED-WITH-PUNCH-LIST** — every D1–D13 decision picks one path with a stated mechanism and the skeleton/scope hold; the fifteen items above are wording-level (one factual path correction, one taxonomy-mapping statement, one process-model contradiction, twelve precision fixes) and can be applied without another review round.
