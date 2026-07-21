# Round 4 — External architecture review (GPT 5.6 Sol Pro)

> Provenance: independent review performed by GPT 5.6 Sol Pro against commit 5eea08d per `REVIEW_PROMPT.md`; delivered by the owner 2026-07-21 22:43 CET. Reproduced as received; two tables whose formatting was flattened in transit have been restored to markdown form without wording changes.

## 1. Executive verdict

**RESTRUCTURE.**

Do not approve draft_v3 as the Stage 2 implementation skeleton. Approve the architecture only after replacing its Harbor substrate with a single Pier-based evaluator and collapsing the trace, materialization, orchestration, and reporting mechanisms that currently compensate for the old substrate.

The product shape is right: an evolvable Qwen Code harness, an AHE-derived optimizer, a fixed rollout model, two operating doors, strict evidence retention, and public experiment history. The implementation shape is not yet the smallest one. It was converged around two assumptions that DeepSWE v1.1 invalidates:

- AHE's pinned Harbor fork should remain the execution authority.
- Avoiding changes to AHE is intrinsically simpler than defining an explicit evaluator seam.

DeepSWE v1.1 requires a separate verifier environment and the pre-artifact/pristine-repository grading lifecycle provided by Pier 0.3.0 or later. Pier resembles Harbor's CLI, but it is not contract-compatible with AHE: task-selection flags differ, custom-agent registration differs, dataset handling differs, and AHE currently reads verifier/reward.txt while DeepSWE/Pier uses structured trial results and reward.json. Preserving the Harbor fork would therefore produce either incorrect grading or two parallel evaluation systems.

The smaller architecture has four concepts:

```
                    ┌────────────────────────┐
Owner CLI ─────────>│                        │
AHE optimizer ─────>│ Shared EvalRunner      │────> Pier/Docker
                    │                        │          │
                    └──────────┬─────────────┘          v
                               │                 DerQwenAgent
                    canonical run result          + model proxy
                               │
                               v
                    experiment lifecycle record
                               │
                               v
                       generated README block
```

harness/ should itself be a runnable-shaped Qwen project. The evaluator stages it into a task, applies only immutable runtime bindings, invokes Pier, and normalizes Pier's artifacts. AHE is deliberately adapted at that one boundary. The owner CLI calls the same boundary. Everything else is either optimizer logic or generated publication output.

This is a bounded restructure, not a new project. AHE remains the research-loop base, Qwen Code remains the harness runtime, DeepSeek v4 pro remains the fixed rollout model, and the managed/live separation and model-pinning proxy remain sound. The necessary change is to stop treating compatibility with obsolete execution assumptions as an architectural invariant.

## 2. Architecture-level findings

### Finding 1. The architecture is built around the wrong evaluation authority

**Issue.** draft_v3 makes AHE's pinned Curry Harbor fork authoritative, introduces a der-harbor registration layer, and targets effectively zero changes to AHE's runner. That was coherent while Terminal-Bench and AHE's existing output layout were the evaluation target. It is not coherent with DeepSWE v1.1.

**Consequence.** Adopting DeepSWE while retaining the old Harbor fork leads to one of two bad designs:
- DeepSWE is run through a backend that does not implement its required verifier lifecycle.
- Pier is bolted on as a second confirmation backend, giving the project two task-loading systems, two agent registrations, two networking models, two result layouts, and two notions of a valid run.

The second option also means the optimizer searches against one measurement distribution and promotion is decided by another. That is not merely extra machinery; it weakens attribution.

**Concrete change.** Make an exact version of Pier 0.3.x the sole scored evaluator. Adapt AHE through one explicit interface, for example:

```
EvalRunner.run(EvalSpec) -> EvalResult
```

That adapter should own:
- Local task-path and task-inclusion translation.
- Loading DerQwenAgent through Pier's custom-agent import mechanism.
- Model endpoint and allowlist configuration.
- Exact job identity and result location.
- Normalization of Pier trial results, reward.json, CTRF output, trajectory, patch, logs, and invalid-run reasons.
- The distinction between task failure and infrastructure-invalid execution.

Do not implement this as a PATH alias that merely renames pier to harbor. AHE emits harbor run, uses -t for task inclusion, supports Harbor's --dataset path, and expects verifier/reward.txt. Pier uses -i/--include-task-name, supports local -p/--path, imports custom agents explicitly, and carries structured result state. Several common flags do align—agent, model, API key, concurrency, and jobs directory—which is why the adapter should be small, but it must be a semantic adapter.

DeepSWE v1.1 explicitly requires a separate verifier environment, committed agent work, pre-artifact patch extraction, and pristine grading; its documentation specifies Pier 0.3.0 or later for correct execution. Pier also has per-agent network allowlists intended to let an installed agent reach necessary endpoints while the task remains otherwise air-gapped.

One point remains genuinely unverified from source: whether the intended Linux container-to-host route to the der model-pinning proxy works under Pier's network setup. Pier's allowlist support is verified; the exact host-gateway path is not. That must be the first live integration test. If direct host routing fails, expose the proxy through a stable private hostname or explicit extra-host mapping rather than weakening task network isolation.

### Finding 2. The proposed universal promotion gate does not match the project's hypothesis space

**Issue.** draft_v3 converges on a generally applied pass-rate/sign-test gate. The North Star, however, explicitly includes hypotheses about success, speed, token use, and cost. A universal "pass rate must significantly improve" rule is only correct for success-rate experiments.

There is a second problem inside AHE. Its headline pass rate is effectively a pass@1-style average when multiple attempts are run, but its per-task comparison state treats a task as passing only when all rollouts pass. That becomes stricter as k increases and turns a 4/5 task into the same attribution state as a 0/5 task.

**Consequence.**
- A change that preserves quality while reducing tokens by 30% can be rejected because it did not increase pass rate.
- A change that raises a task from 1/5 to 4/5 can disappear from the optimizer's task-level attribution.
- A small, repeatedly reused suite gets dressed in stronger inferential language than it supports.
- Changing k changes the meaning of AHE's all-rollouts task labels.

**Concrete change.** Each experiment must declare its own contract before execution:
- One primary metric.
- A minimum practically meaningful effect.
- Global guardrails.
- A falsifier.
- The suite, attempt count, and budget.

Examples:
- Quality experiment: primary metric is macro pass@1 delta; token and cost limits are guardrails.
- Efficiency experiment: primary metric is valid-task median token reduction; pass rate has a predeclared non-inferiority margin.
- Latency experiment: primary metric is wall-clock reduction; quality and cost are guardrails.

Use per-task pass fractions for optimizer attribution rather than all-k binary states. Retain binary reward per attempt for grading.

I would also remove "statistically significant" as the general promotion vocabulary. On a small suite undergoing repeated adaptive optimization, report the observed effect, valid numerator and denominator, task-level outcomes, and a descriptive task-cluster interval. Promotion should be based on the preregistered minimum effect and guardrails, not on a small-sample p-value that implies a clean fixed-design experiment.

Finally, call the disjoint set a confirmation set, not a holdout. Once the system repeatedly uses or publicly exposes its aggregate result, it is not an untouched statistical holdout.

### Finding 3. The plan makes a compatibility trace more canonical than the actual execution evidence

**Issue.** The draft converts Qwen execution into a NexAU-shaped trace and labels provider spans as "openai" to satisfy an inherited parser. That is a semantic disguise introduced for one consumer. The draft then treats the converted representation as part of the central evidence architecture.

**Consequence.**
- A parser convenience becomes a project-wide data model.
- Provider and role identity become misleading.
- Conversion defects can silently alter the optimizer's evidence.
- The project becomes coupled to ADB's current input assumptions instead of to the evaluator's actual record.
- Future debugging has to determine whether an observed behavior came from Qwen, the converter, or the analyzer.

**Concrete change.** Make these the canonical evidence:
- Pier's ATIF trajectory.
- Pier's structured trial result.
- DeepSWE's verifier reward, CTRF report, extracted patch, verifier logs, and related artifacts.
- One der-owned normalized run record that references those files by digest.

Pier advertises augmented ATIF output for agent trajectories; DeepSWE's v1.1 flow produces the verifier and patch artifacts needed to audit a verdict.

If ADB still requires NexAU, generate NexAU as an ephemeral compatibility view immediately before ADB. Patch the parser to recognize the true provider/agent roles, or use a provider-neutral LLM-call role. Never claim that a DeepSeek/Qwen span was OpenAI traffic.

This still permits strict converter fixtures and source-to-derived drill-down. It simply puts the truth on the correct side of the adapter.

### Finding 4. The generalized substrate materializer duplicates Qwen's own project model

**Issue.** draft_v3 defines a generalized component schema and a materializer whose output, rather than the checked-in harness, is the runnable system. It maintains distinctions between source components, daily context, rollout context, rendered prompts, and runtime placement.

Qwen Code already has project-level settings, checked-in project skills, a root QWEN.md, imported context files, explicit system-prompt controls, structured headless output, and project-scoped sessions.

**Consequence.**
- There are two representations of the harness: the component source and the rendered Qwen project.
- Promotion verifies a renderer plus a harness rather than the harness itself.
- Daily and rollout behavior can drift through materialization rules.
- AHE must reason about an owner-defined abstraction before it can change the actual files Qwen consumes.
- Every new native Qwen capability risks another translation rule.

**Concrete change.** Store every evolvable object in its runtime-shaped form:

```
harness/
  QWEN.md
  .qwen/
    settings.json
    skills/
      <skill>/SKILL.md
  der/
    <only genuinely der-specific runtime files>
```

The evaluator may still need a staging step because the DeepSWE task repository is Qwen's working project. That step should be a transparent copy/overlay, not a renderer:
- Copy the managed Qwen files into the task workspace.
- Select an isolated rollout home rather than the daily-driver home.
- Disable or isolate rollout auto-memory.
- Inject immutable model endpoint, attempt budget, and execution limits outside the evolvable namespace.
- Record a manifest of what was staged.

Keep managed/live separation. Delete the generalized four-type component language unless a component genuinely cannot be expressed through Qwen's project model.

For packaging, use Qwen Code's pinned official standalone archive and checksum from a local read-only cache rather than constructing an npm-install flow for every trial. The project publishes standalone/offline archives specifically for that installation mode.

### Finding 5. The two operating doors are implemented as two orchestration paths

**Issue.** The draft uses an indirect command shim, a runner clone and branch, a lock, later cron-based post-processing, and publication/merge machinery around the autonomous path. The owner-driven CLI has a neighboring but not identical flow.

AHE also has a dangerous recovery behavior: after a timeout it can select the latest existing job directory and continue with those results. In an unattended system, that can associate stale evidence with the wrong experiment.

**Consequence.**
- Correctness depends on branch state, process state, filesystem recency, cron timing, and post-processing order.
- A human run and an autonomous run can disagree despite nominally using the same harness.
- A stale job directory can become a valid-looking scorecard.
- Publication needs conflict-resolution machinery because it has more than one writer.

**Concrete change.**

Both doors must call the same synchronous EvalRunner and the same finalizer:

```
der experiment run ...  ─┐
                         ├──> EvalRunner ──> Finalizer
AHE iteration ----------─┘
```

Retain one process lock or serialized queue on the single server. A dedicated Git worktree for autonomous activity is sensible isolation. A separate publication branch, cron writer, SVG merge driver, and "latest job" recovery path are not.

Every run must receive an explicit experiment ID and evaluator job ID. The adapter must return the exact result path. If that path is absent or incomplete, the run is invalid and fails closed. Never recover by directory recency.

The finalizer should atomically write the scorecard and update the experiment record only after the evaluator has produced a complete terminal result.

### Finding 6. The same experiment identity and outcome are represented too many times

**Issue.** The draft has overlapping identity and publication mechanisms: Git revision, canonical tar hash, a baseline pointer, exact replacement rules, scorecards, notebook files, DASHBOARD.md, multiple SVGs, and badge-style summaries.

**Consequence.**
- There are multiple candidates for "what is currently deployed."
- A baseline pointer can disagree with main.
- A notebook conclusion can disagree with its scorecard.
- Dashboard and README can diverge.
- More code is spent synchronizing presentation than measuring the harness.

**Concrete change.** Use three levels of truth:

1. Evaluated harness identity: the source commit plus the Git tree OID of harness/, accompanied by a runtime-manifest digest covering immutable evaluator/runtime inputs.
2. Machine result: one immutable scorecard.json.
3. Experiment lifecycle: one Markdown notebook entry, created before execution and completed after it.

The current baseline is derived: it is the most recent adopted scorecard whose harness tree OID matches main:harness. No independently mutable baseline.json is required.

The Markdown result block should be generated from the scorecard rather than manually copied. The README chart and experiment ledger should be generated from those same records. Delete DASHBOARD.md and the second independent chart.

## 3. Answers to Q1–Q6

### Q1. Adopt DeepSWE v1.1 as the rollout suite?

**Recommendation: yes.** Use DeepSWE v1.1 as the primary rollout distribution and Pier as the sole scored evaluation backend.

Do not keep Terminal-Bench as the optimizer's main loop and reserve DeepSWE for promotion. That saves no architecture. It creates a dual-backend system and allows the optimizer to learn against terminal puzzles while the project claims progress on long-horizon repository work.

DeepSWE has 113 tasks across TypeScript, Go, Python, JavaScript, and Rust, uses Harbor-style task structure, and supplies purpose-built behavioral verifiers. Version 1.1's separate verifier environment and pre-artifact patch extraction are materially better suited to evaluating repository changes than inherited tests alone.

The published 1.4% figure needs precise interpretation. It is verifier-versus-independent-judge disagreement, compared with 32.4% on SWE-Bench Pro in the reported analysis. It is not a measured 1.4% verifier error rate, because neither side is established as ground truth. It is nevertheless strong evidence that DeepSWE's verifier behavior is substantially less ambiguous under that comparison.

DeepSWE is also not a complete proxy for all daily software work. Its scope emphasizes long-horizon repository tasks and underrepresents short edits and some single-file work. That is acceptable here because the rollout suite should stress the harness behaviors the project most wants to improve, but the README should describe the scope honestly.

The published DeepSeek-v4-pro result—7.5% pass@1 and 19% pass@4—was obtained with the paper's fixed mini-swe-agent setup, not with der. It therefore supports the concern that frontier-model completion anchors will not transfer, but it is not a forecast of der's baseline.

Pier is not a literal drop-in for AHE, but it is close enough that one adapter is preferable to maintaining the old Harbor fork:
- Common concepts and several flags align.
- Task inclusion differs: AHE/Harbor -t, Pier -i.
- AHE's registry dataset path is not Pier's local-path contract.
- A custom der agent must be provided through Pier's import path.
- AHE's current reward-file parser is not compatible with DeepSWE v1.1 results.

The current DeepSWE quickstart clones the public repository and runs it by local path. Consequently, the previously noted gated Hugging Face dataset is not a load-bearing acquisition blocker for the present public flow. Pin the repository/task revision nonetheless.

Before suite calibration, require one end-to-end acceptance task to prove all of the following:
1. DerQwenAgent loads through Pier.
2. The pinned Qwen runtime starts offline.
3. The agent reaches only the model-pinning proxy.
4. The agent's changes are committed.
5. pre_artifacts.sh extracts the intended patch.
6. The verifier runs from the pristine repository state.
7. Reward, CTRF, patch, logs, trajectory, and structured result agree.
8. A deliberately induced provider/network failure is classified as invalid rather than task failure.

Terminal-Bench can remain an optional external benchmark or provide a few unscored integration-smoke tasks. It should not remain a second promotion authority.

### Q2. Subset selection and false-negative avoidance

**Recommendation: capability-calibrate against der + DeepSeek v4 pro, but do not mutate a suite after it has been frozen.**

Tura's official-rate anchors are historical completion rates over its evaluated model pool, not inherent difficulty values. Its exact language balance is a deliberate comparison policy, not evidence that five languages should each receive equal weight in a der optimization suite.

I recommend this initial procedure.

**Calibration**

Start with approximately 30–40 candidate tasks, selected for:
- Repository and task-archetype coverage.
- Strong, auditable verifier behavior.
- A rough match to the owner's expected language/workload distribution.
- Coverage across the official difficulty spectrum, without treating the official rates as selection thresholds.

Run the baseline at k=5.
- Keep obvious middle tasks provisionally.
- Extend tasks with 0/5, 1/5, 4/5, or 5/5 to k=10 when they are needed for coverage or appear near a boundary.
- Treat calibration as screening, not as precise estimation.

Use a 20–80% baseline signal band for the active suite. With ten attempts, that means retaining tasks with roughly 2–8 baseline successes. Favor a spread across the der-relative 20–40%, 40–60%, and 60–80% regions rather than filling the suite with tasks clustered around 50%.

I prefer 20–80% to 15–85% because it maps cleanly to small attempt counts and excludes tasks whose useful signal is mostly a rare event. If too few tasks qualify, reduce suite size rather than silently admit a collection of 0%-baseline tasks.

**Initial suite**

A reasonable operating default is:
- 16 development/search tasks.
- 8 disjoint confirmation tasks.
- A 4–6 task reporting spine selected from the first suite and carried across versions.

The spine is not a third promotion gate. It is a reporting view for long-term continuity and will eventually saturate or become stale. It must never receive special optimization weight.

During routine search, use k=2 on the development suite. For a candidate that reaches confirmation, interleave baseline and candidate attempts on the confirmation suite at k=4 or k=5. Interleaving by task reduces the risk that provider or machine conditions systematically favor one arm.

After adoption, run the adopted baseline on the complete versioned suite at the reporting k, and use only that full-suite result as the next progression-chart point.

Those numbers are operating defaults, not architectural constants. The important invariants are disjoint search/confirmation membership, fixed membership inside a suite version, and explicit attempt counts.

**Recalibration and suite versions**

Never add, remove, or swap tasks inside an existing suite version.

Create a new version when either:
- Fewer than half of the development tasks remain in the 20–80% band across three adopted baseline evaluations, or
- Approximately 20 hypotheses have been evaluated against the same development suite.

The second trigger recognizes adaptive exposure even when scores have not visibly saturated. It is a policy judgment, not a sourced statistical threshold.

At a version change:
- Freeze the old suite.
- Select the new suite from a separately maintained candidate pool.
- Run the same harness commit on old and new suites in the same evaluation window.
- Publish both bridge results.
- Break the main chart line between suite versions rather than pretending the percentages are directly comparable.

**What still counts as difficulty stratification**

Difficulty stratification still matters, but redefine difficulty as pass probability under the fixed rollout model and current baseline harness. Also stratify by failure mode, task shape, repository scale, language, and verifier structure. Language is a coverage constraint, not necessarily an equal-weight quota.

**What to retain and reject from Tura**

Retain Tura's discipline around:
- Pinned task identity and revision.
- Model, configuration, k, source revision, harness revision, retry policy, and infrastructure metadata.
- Published numerator and denominator.
- Invalid-run and exclusion records.
- Per-replicate retention rather than only aggregate scores.

Do not import:
- Frontier-model completion anchors as der difficulty labels.
- Equal per-language weighting unless it matches the intended workload.
- The assumption that a static comparison methodology directly solves repeated adaptive optimization.
- Any implication that a publicly and repeatedly consulted confirmation result remains a pristine holdout.

Follow the DeepSWE/Tura distinction for validity: agent or context timeout is a task failure; provider, network, malformed verifier, or infrastructure failure is invalid, recorded, and rerun or excluded without imputation.

### Q3. Model roles and the Codex subscription

**Recommendation: keep the unattended V1 analysis path DeepSeek-pinned, and add one owner-triggered Codex proposal critic outside the measured path.**

The split should be:

| Role | V1 model/mechanism | Reason |
| --- | --- | --- |
| Rollout agent | DeepSeek v4 pro through the pinning proxy | Fixed owner constraint and measurement comparability |
| Trace distillation / ADB | Pinned DeepSeek configuration | Keeps unattended operation simple and reproducible |
| Automated Evolve Agent | Pinned DeepSeek configuration | Avoids introducing a second authentication and execution path into the autonomous loop |
| Premium analysis | Local codex exec, GPT-5.6 Sol, subscription login | Higher-quality bounded critique and proposal generation outside evaluation |
| Promotion decision | Deterministic experiment contract plus owner/system policy | No model receives promotion authority |

The reason to keep ADB and the automated Evolve Agent on DeepSeek in V1 is operational simplicity, not measurement purity. The owner is correct that changing the proposal model does not corrupt rollout measurements; it changes optimizer quality. Such a change can later be evaluated as an optimizer revision, provided the analysis model and prompt are recorded.

The premium Codex role should run after an experiment or small batch and should consume a fixed evidence bundle:
- Experiment contract.
- Distilled trace evidence.
- Task-level attribution.
- Scorecard.
- Selected raw evidence links.
- Current hypothesis queue.

It should emit one schema-validated proposal artifact, not a free-form memo plus a separate set of hypothesis files. That artifact can contain critique, alternative causal explanations, and zero or more candidate experiments.

Run it from a trusted host with a read-only sandbox and structured output, for example using codex exec with an output schema. Codex CLI officially supports ChatGPT subscription login, model selection, read-only execution, and schema-constrained output. GPT-5.6 Sol is the current recommended Codex model in the official material reviewed.

Record:
- Codex CLI version.
- Exact model and reasoning setting.
- Prompt/schema digest.
- Input commit and evidence-manifest digest.
- Output digest.
- Whether execution was owner-triggered or automated.

Do not build an OpenAI-compatible shim over subscription credentials for ADB_LLM_*. It is unnecessary, fragile, and collapses a supported interactive authentication mechanism into an unsupported service interface.

Do not put the owner's subscription session into the unattended systemd path. Official guidance favors API-key authentication for programmatic/CI use and cautions against exposing Codex execution to untrusted environments. If premium analysis later becomes unattended, use the supported programmatic authentication route and treat that as a separately versioned optimizer change.

DeepSWE's independent verifier review used Codex CLI, which validates the execution pattern, but it does not establish Codex as an oracle. Its output remains a hypothesis source, not evidence or a verdict.

### Q4. Recording, presentation, and the progression graph

**Recommendation: keep one machine record, one lifecycle notebook entry, and one generated README presentation.**

The minimal artifact set is:

**1. Immutable scorecard**

scorecard.json should contain:
- Experiment ID and status.
- Harness tree OIDs for baseline and candidate.
- Runtime/evaluator manifest digest.
- Suite version and task revisions.
- Rollout model and endpoint policy identifier.
- k, valid attempts, passes, failures, and invalids.
- Retry and exclusion records.
- Per-task rewards and attempt outcomes.
- Tokens, cost, wall time, turns, and context-limit events.
- Pier job/result references and evidence digests.

This is the machine authority for results.

**2. One experiment lifecycle notebook entry**

Create experiments/EXP-####-slug.md before execution. It starts as the preregistered proposal and is appended with execution references, result, verdict, and adoption commit.

The result table in the Markdown should be generated from scorecard.json, not manually transcribed.

This one file satisfies both the hypothesis backlog and the required per-experiment notebook. It also proves through Git history that the falsifier existed before the result.

**3. One generated README block**

The README should contain:
- A hero step chart showing the adopted harness baseline's macro pass@1 over time.
- An annotation for each adopted experiment.
- A compact ledger of every experiment, including rejected, inconclusive, and invalid runs.
- Links from each experiment ID to its notebook entry.
- Small aligned resource strips for tokens, cost, and wall time, satisfying the North Star without creating separate dashboards.

Only adopted states belong on the progression line. Rejected experiments belong in the ledger with their observed delta and reason. Otherwise the "harness progression" chart becomes a chart of attempted candidates rather than the system actually shipped.

At a suite-version change, terminate the old series and start a new segment. Show bridge evaluations of the same harness commit on both versions. A thin reporting-spine series can provide continuity, but it must be clearly labeled and must not be mistaken for the promotion metric.

Tura's most valuable contribution here is not its visual style but its reporting contract: task revision, model/build, replicate count, numerator, denominator, retry policy, and declared exclusions must accompany every aggregate.

Delete:
- DASHBOARD.md.
- A second independently generated SVG.
- Stored badge artifacts.
- A separate notebook index.
- Any manually edited score table duplicated from the scorecard.

One composite SVG plus one generated ledger is enough.

### Q5. Hypothesis formation

**Recommendation: preregister experiments, but do not add experiments/BACKLOG.md as a second source of truth.**

Use the experiment notebook itself as the lifecycle object. Before a run begins, create:

```
experiments/EXP-####-slug.md
```

with machine-readable front matter and a short human-readable contract.

Required fields should be limited to:
- status: proposed, running, adopted, rejected, inconclusive, or invalid.
- proposer: owner, AHE, Codex, or literature.
- Hypothesis.
- Motivating evidence links.
- Intended change and managed-file scope.
- Primary metric and minimum effect.
- Guardrails.
- Falsifier.
- Suite version and attempt budget.
- Proposal model/prompt metadata when model-generated.

A queue page can be generated from status: proposed; it should not itself contain hypotheses.

This merges four proposed mechanisms:
- Owner ideas.
- AHE-generated ideas.
- Premium Codex analysis.
- Literature-derived ideas.

All produce the same experiment object. A proposal can be rejected without running and still remain in history. Once selected, its Git commit is the preregistration point. After execution, the same file gains scorecard links and the verdict.

Keep one active experiment on the serial machine. Do not add prioritization scores, voting, or a separate research database until a real backlog-size problem appears.

### Q6. Parallel experiments

**Recommendation: defer cross-experiment parallelism entirely in V1.**

Use:
- One serialized local experiment queue.
- One process lock.
- Pier's --n-concurrent only for attempts within the active experiment, capped according to CPU, memory, Docker, and model-provider constraints. Pier exposes both concurrency and attempt-count controls.

Do not create multiple runner clones with disjoint suites. That introduces resource interference and makes baseline/candidate comparisons depend on which runner and load profile executed them.

Do not add E2B now. Pier's documented cloud execution path is Modal; adding E2B would require a second environment implementation rather than merely changing evaluator configuration.

When queue delay becomes a measured operational problem, add one environment option to EvalSpec and first run a preregistered equivalence experiment comparing local Docker with the chosen Pier cloud environment on the same task revisions, model endpoint, timeout, and retry policy. Until equivalence is characterized, do not join cloud results to the main progression series.

This keeps parallelism an evaluator deployment choice rather than a new architectural subsystem.

## 4. The elegance pass

These are the mechanisms I would delete or merge.

| Delete or merge | Replace with |
| --- | --- |
| Curry Harbor fork as scored authority | Exact Pier pin as the sole evaluator |
| der-harbor in-tree agent registration | Pier --agent-import-path for DerQwenAgent |
| "Zero AHE patches" as a design goal | One explicit, tested EvalRunner adapter |
| Terminal-Bench loop plus DeepSWE promotion backend | DeepSWE for scored work; same-Pier smoke tasks for integration |
| Canonical Qwen-to-NexAU trace conversion | Canonical Pier ATIF/result artifacts; NexAU only as an ADB boundary view |
| Fake "openai" provider naming | Actual provider/agent role or provider-neutral event type |
| Generalized component renderer and context-type schema | Runtime-shaped Qwen project plus transparent staging overlay |
| Per-trial npm installation flow | Pinned official Qwen standalone archive from a local cache |
| PATH command shim as evaluator integration | Direct adapter invocation |
| Separate publication branch, cron writer, and SVG merge driver | One synchronous finalizer and one process lock |
| "Latest job directory" timeout recovery | Exact job identity; fail closed when incomplete |
| baseline.json plus independent tar identity | main:harness Git tree OID plus runtime-manifest digest |
| Universal significance gate | Experiment-specific primary metric, minimum effect, and guardrails |
| "Holdout" terminology | Versioned confirmation set |
| BACKLOG.md plus premium analysis memos | One experiment lifecycle record from proposal through verdict |
| DASHBOARD.md, two charts, and stored badges | One generated README chart and ledger |
| Separate budget/watchdog specifications | One immutable RunBudget passed to evaluator and proxy |

The mechanisms I would retain are equally important:
- The narrow model-pinning proxy.
- Provider-side hard spend limits.
- Managed versus live harness isolation.
- Isolated rollout home/session state.
- Immutable raw evaluator evidence.
- One process lock on the single server.
- A dedicated autonomous worktree.
- Systemd supervision once the synchronous path is proven.
- Public recording of rejected and invalid experiments.

Those are direct controls on real failure modes. The deleted mechanisms mostly exist because the draft has indirect evaluator, rendering, and publication paths.

## 5. What I would build first

I disagree with the emphasis of the nine-step order in draft_v3. It front-loads substrate abstractions and publication/orchestration before the new evaluator contract is proven. I would build the scoring spine first.

**Step 0: Freeze the external identities.** Pin and record: AHE commit; Pier version and commit; DeepSWE repository and task revisions; Qwen standalone archive version and checksum; der agent revision; rollout-model identifier and proxy policy. Define the canonical EvalSpec, EvalResult, and scorecard schemas before writing orchestration.

**Step 1: Complete one DeepSWE task through Pier manually.** Build the smallest DerQwenAgent needed to run one task. Prove: Qwen starts from the pinned offline archive; staged project settings and skills are recognized; rollout state is isolated; the model endpoint is reachable through the pinning proxy and unrelated egress remains blocked; repository changes are committed; pre-artifact extraction captures the right patch; the verifier operates against the pristine repository; reward, CTRF, patch, logs, trajectory, and result agree. Deliberately execute one failing task and one infrastructure-invalid run to validate classification. Do not proceed while any of those facts are inferred rather than inspected.

**Step 2: Build the result normalizer and scorecard.** Parse Pier/DeepSWE output into the canonical result schema. Manually trace one run from Qwen session → ATIF trajectory → committed repository change → extracted patch → verifier report → normalized scorecard. Every scorecard field must be traceable back to a source artifact.

**Step 3: Run a small integration battery.** Three to five DeepSWE tasks with different languages and verifier shapes at k=1. This is not the research suite. It proves task selection, cleanup, retry classification, proxy operation, and artifact collection across more than one repository.

**Step 4: Implement the shared evaluator door.** Add the owner CLI over EvalRunner. Then patch AHE to use the same interface. Remove: Harbor command construction from the active path; reward-text parsing; directory-recency recovery; all-rollouts-pass task attribution. Run a two-iteration toy AHE loop and verify exact job/result association and deterministic resume behavior.

**Step 5: Make harness/ runtime-shaped and prove promotion identity.** Move evolvable Qwen files into their native project layout. Implement only the transparent staging overlay and immutable runtime bindings. Run a hand-authored baseline/candidate A/B. Adopt it, rebuild from main:harness, and prove that the rebuilt tree and runtime manifest match the evaluated identity.

**Step 6: Calibrate and freeze suite v1.** Perform the k=5/sequential-k=10 baseline calibration. Freeze development, confirmation, and reporting-spine membership. Publish the exclusion record. Run the complete suite baseline before allowing autonomous optimization.

**Step 7: Add the lifecycle record and README generator.** Implement: pre-run experiment record creation; scorecard attachment; verdict transition; one README chart and ledger. At this point outside readers can audit real data. Building the dashboard earlier would only produce a polished view of an untrusted pipeline.

**Step 8: Add analyzers and unattended operation.** Only after the evaluator and promotion path are trustworthy: add ADB's compatibility adapter; add the owner-triggered Codex proposal critic; add the autonomous AHE service; add notifications, retention, and garbage collection; add systemd hardening and recovery tests. Autonomy should be the last architectural layer because it magnifies every scoring, identity, and recovery defect below it.

## Approval conditions for Stage 2

I would approve progression into the implementation plan once the owner accepts these five architectural changes:

1. Pier is the sole scored evaluator for DeepSWE.
2. AHE receives one intentional evaluator/result adapter rather than a command-name shim.
3. harness/ is stored in runtime-shaped Qwen form, with only a transparent staging overlay.
4. Promotion is based on preregistered experiment-specific contracts and a versioned confirmation set, not a universal sign-test gate.
5. One experiment lifecycle record, one scorecard, and one generated README block replace the overlapping backlog, baseline, dashboard, and publication mechanisms.

With those changes, the architecture becomes materially shorter while honoring every fixed constraint. Without them, Stage 2 would formalize a collection of compatibility workarounds that DeepSWE has already made unnecessary.
