# Architecture review brief — der auto-research loop (for GPT 5.6 Sol Pro)

You are a principal-level systems architect performing an independent review of a converged architecture before it is approved and expanded into an implementation plan. You have full repository access and are expected to verify claims against primary sources, not take the document's word for anything load-bearing.

## Your mission, in priority order

1. **Judge the overall architecture.** Is this the right shape — the smallest set of concepts that carries every requirement? Would a materially simpler decomposition honor all constraints? You are reviewing the building, not the paint: do not spend your report on wording nits, style, or restating the document.
2. **Find the most ELEGANT solution.** Wherever you see incidental complexity — a component that exists to patch around another component, a mechanism whose job a simpler mechanism already covers, a distinction that could be deleted — say so and name the simpler form. The best possible outcome of this review is a shorter plan, not a longer one. For every finding: issue → consequence → the concrete simpler alternative.
3. **Answer the six open questions (Q1–Q6 below).** These are genuinely open; the owner wants your independent recommendation on each, with reasoning. Our current positions are stated so you can confirm or overturn them — overturning with evidence is welcome.

## Setup

Clone and read:

```
git clone https://github.com/keyclaw6/-der.git
```

Reading order:
1. `VISION.md` — the project's North Star (approved; treat as given).
2. `research-plan/context.md` — constraints and source-verified facts.
3. `research-plan/draft_v3.md` — **the architecture under review.**
4. `research-plan/reviews/` — three adversarial rounds already ran (systems, source-fidelity, ops, red-team, readiness, closure). Read at least `round1_prism.md` (source audit) and `round2_vex.md` (red team) so you do not re-litigate settled findings without new evidence. The convergence log (draft_v3 §10) summarizes the evolution.

Primary sources to verify against (the reviews cite specific files and line numbers in these):
- AHE (the research-loop base, fixed by owner decision): https://github.com/china-qijizhifeng/agentic-harness-engineering — especially `evolve.py`, `configs/base.yaml`, `trace_converter.py`
- Qwen Code (the harness base runtime, fixed): https://github.com/QwenLM/qwen-code · docs: https://qwenlm.github.io/qwen-code-docs/
- harbor upstream: https://github.com/harbor-framework/harbor · AHE's pinned fork: https://github.com/Curry09/harbor-LJH
- DeepSWE v1.1: https://github.com/datacurve-ai/deep-swe (Harbor task format; 113 tasks; hand-written behavioral verifiers) · Pier runner: https://github.com/datacurve-ai/pier · paper: https://arxiv.org/abs/2607.07946
- Benchmark methodology and reporting discipline worth stealing from: https://github.com/Tura-AI/benchmark/blob/main/doc/benchmark-methodology.md and https://github.com/Tura-AI/benchmark/blob/main/doc/current-test-set-record.md

## Fixed constraints (owner decisions — do not relitigate)

- The research loop is built by adapting the AHE codebase above.
- **DeepSeek v4 pro is the pinned model for running evals inside the harness (rollouts), always** — this keeps measurements cheap and comparable. (Model policy for *analysis* roles is open — Q3.)
- The harness under evolution is der: Qwen Code base + the owner's component layer.
- Public repo; experiments published win-or-lose; README leads with a glanceable dashboard; per-experiment notebook entries.
- Both doors required: an owner-driven experiment CLI and the unattended autonomous loop.
- One-person operation, self-hosted single server, roughly $300–1,500/month ceiling.
- Two-stage planning: this review gates Stage 1 (architecture); Stage 2 (step-by-step implementation plan for an executing agent) comes after.

## Open questions — give a recommendation on each

**Q1. Eval suite: adopt DeepSWE v1.1 as the rollout suite?**
draft_v3 pins terminal-bench@2.0 subsets (AHE-native; AHE's own results are calibrated on it). The owner is inclined toward a subset of **DeepSWE v1.1** instead: Harbor task format (our stack), contamination-free tasks, long-horizon multi-file work far closer to real daily coding than terminal puzzles, and hand-written behavioral verifiers whose LLM-judge disagreement is ~1.4% (vs ~32.4% for SWE-bench Pro inherited tests) — the strongest available defense against false verdicts. Complications you should weigh: since v1.1, correct grading requires **Pier ≥ 0.3.0** (separate verifier environment; `pre_artifacts.sh` patch-extraction flow) — compatibility with AHE's pinned harbor fork is unverified; the dataset is gated on HuggingFace; and network egress differs (Pier exists partly because harbor blocks all outbound traffic in `allow_internet = false` tasks — our der agent must reach its model endpoint from inside the task container; draft_v3's pinning proxy assumes container→host egress). Options include: run rollouts under Pier as the eval backend (replacing or alongside the AHE harbor pin), swap the harbor pin entirely, or keep terminal-bench for the loop and DeepSWE for pre-promotion confirmation. Recommend the elegant path, considering that AHE's `_build_harbor_cmd` emits a plain `harbor run ...` argv (a Pier CLI with compatible flags may be a drop-in; verify).

**Q2. Subset selection and false-negative avoidance.**
The Tura methodology selects 20 DeepSWE tasks language-balanced and difficulty-stratified around official completion anchors (80/60/40/20%). Note a trap: those anchors reflect *frontier-model* completion rates, but our pinned rollout model is DeepSeek v4 pro — cheaper and weaker. Tasks in the frontier 20–40% band may sit at ~0% for our agent, contributing cost and false-negative noise but no gradient signal. Our position: **calibrate empirically against our own baseline** — run the der baseline at k≥5 over candidate tasks, keep tasks whose baseline pass rate falls in a signal band (~15–85%), publish the exclusion record Tura-style, draw the holdout from the same calibrated pool (disjoint), and version suites so longitudinal comparisons stay within a suite version (with a small never-rotated "spine" subset for the long progression chart). Open sub-questions for you: the right signal band and k for calibration; how to handle re-calibration when the baseline improves (suite version bump vs task addition policy); whether difficulty stratification still matters after capability calibration; and anything the Tura methodology gets wrong for *this* use (optimizing a harness against a fixed model, rather than comparing frontier models).

**Q3. Model roles and the Codex subscription.**
Rollouts stay DeepSeek v4 pro — fixed. The open question is the *analysis tier*: trace distillation (ADB), the Evolve Agent, and hypothesis generation. The owner holds a **Codex subscription (GPT 5.6 Sol)**. Our position: keep the measured loop's in-pipeline roles (ADB, Evolve Agent) DeepSeek-pinned at V1 for consistency and zero new auth machinery, and add a bounded **premium analysis role** that runs as a Codex CLI agent (`codex exec`, subscription auth) after an iteration or A/B completes: it reads the distilled evidence, attribution verdicts, and scorecards from the repo, and writes an analysis memo + candidate hypotheses back as files. It is never in the measured path, so comparability is untouched; its model/version is recorded per memo. Notes for your judgment: comparability only *requires* pinning the rollout model — attribution verdicts ground in harbor's reward files, so upgrading the Evolve Agent's model would not corrupt measurements (it changes proposal quality, which outcomes then grade); DeepSWE's own pipeline ran its LLM judge as a Codex CLI agent, so the pattern is proven; an OpenAI-compatible shim over subscription auth for `ADB_LLM_*` would be tighter integration but is fragile and ToS-gray. Recommend the split: which roles stay pinned, which (if any) go premium, and by what mechanism.

**Q4. Recording, presenting, and the progression graph.**
Requirement: an outside builder should see at a glance what worked, what didn't, and how the harness has progressed overall; the README must carry a clear progression graph. draft_v3 has scorecards + per-experiment notebook files + DASHBOARD.md + two SVG charts. Our position: adopt Tura's reporting discipline (per-suite reporting, numerator/denominator/task-revision/k/model/config recorded, exclusions logged as data) and make the README hero chart **baseline pass-rate on the pinned suite over time, annotated with each adopted experiment** (the "total progression of the harness"), with per-experiment verdict badges linking into the notebook. Recommend the minimal artifact set that makes progression legible and trustworthy to outsiders — and cut anything performative.

**Q5. Hypothesis formation.**
Currently implicit: the Evolve Agent derives edits from evidence; the owner adds ideas ad hoc. Our position: a lightweight pre-registered backlog (`experiments/BACKLOG.md`): each entry states hypothesis, motivating evidence (trace/digest links, literature), expected effect and metric, and the falsifiable contract — before anything runs; fed by (a) evidence digests, (b) the premium analysis memos (Q3), (c) the owner, (d) published research. Is there a better mechanism? Keep one-person overhead near zero.

**Q6. Parallel experiments (nice-to-have, not required).**
The single-box flock serializes rollout batches. Options: accept queueing (V1 position); flip harbor's env to E2B for cloud parallelism when needed; multiple runner clones with disjoint suites. Recommend the cheapest path that doesn't distort the architecture — deferring entirely is an acceptable answer.

## Output format

1. **Executive verdict** (≤1 page): approve as-is / approve with changes / restructure — and the two or three sentences that justify it.
2. **Architecture-level findings**, ranked by consequence. Each: issue → consequence → concrete change. Include what you verified in source to reach it.
3. **Answers Q1–Q6**, one recommendation each, with reasoning and any verification you performed.
4. **The elegance pass:** the specific components, mechanisms, or distinctions you would DELETE or merge, and what replaces them. If the plan is already minimal, say so.
5. **What you would build first** if you disagree with the nine-step build order in draft_v3 §5.

Ground every load-bearing claim in the repository or the linked sources; distinguish verified fact from judgment. Do not produce a summary of the plan — produce the review of it.
