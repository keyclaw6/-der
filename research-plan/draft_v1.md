# der auto-research loop — Stage 1 architecture (DRAFT v1)

Status: draft for adversarial review. Stage 2 (implementation plan for an executing agent) is explicitly out of scope until the owner approves Stage 1.

## 0. Purpose

Stand up an automated research loop around the der harness (Qwen Code base) by adapting the official AHE codebase, so that:

- the harness can be **evolved autonomously** (AHE evaluate → analyze → improve iterations, unattended, resumable), and
- the owner's **own hypotheses** (token-saving middleware, prompt strategies, orchestration variants) can be tested through the **same rollout + scorecard + verdict machinery** (A/B against baseline), and
- every verdict produces a **comparable scorecard** (pass rate, tokens in/out, cost, wall-clock, turns) that feeds the public README dashboard, and
- **DeepSeek v4 pro is the pinned model for every role in the loop** (agent-under-test, Agent Debugger, Evolve Agent, explore agent) for cost and consistency.

## 1. The one-sentence architecture

**Fork AHE as the research spine, keep its loop intact, and swap exactly one thing: the agent-under-test — from AHE's NexAU demo agent to the der harness (Qwen Code headless + our component workspace) — behind harbor's agent interface, with a der-shaped component contract and a qwen-trace converter as the two adapters that make the swap invisible to the rest of the loop.**

Everything else (ADB distillation, evolve agent, manifests, flip attribution, rollback, best-of-N, resume) is inherited, not rebuilt.

## 2. Architecture decisions

### D1. Vendor AHE as `research/` inside the der monorepo; keep an upstream remote

- The der repo gains a top-level `research/` directory: a fork (git subtree or plain vendored copy with `UPSTREAM.md` recording the pinned commit) of china-qijizhifeng/agentic-harness-engineering, MIT attribution preserved.
- Rationale: one repo = one deployment = the vision's "open notebook" (experiments, scorecards, dashboard all live where builders read). Upstream remote kept so AHE improvements can be merged.
- Alternative rejected: separate research repo — splits the public story and doubles ops for a one-person project.

### D2. The agent-under-test is the der harness, plugged in at the harbor seam

- AHE already delegates all rollouts to harbor (`harbor.agent`, `source_config_dir`). We do not touch evolve.py's loop; we change configuration and add an adapter.
- A **der harbor agent**: container image with Qwen Code (pinned version) + a startup shim that (a) materializes the component workspace into Qwen Code project config, (b) runs `qwen -p "<task prompt>"` headless with DeepSeek v4 pro as provider, (c) emits the session trace to a known path.
- Open question for review: does harbor ship a qwen-code adapter already (Terminal-Bench supports many agents natively)? If yes, V1 shrinks further; if no, we write a small custom-agent spec (harbor supports custom agents).

### D3. The component contract: a der-shaped workspace the Evolve Agent edits

AHE's Evolve Agent edits `workspace/` with seven NexAU component types. We redefine the workspace to der's component classes, mapped onto Qwen Code's native surface:

| AHE component type | der workspace file(s) | Qwen Code surface it materializes to |
|---|---|---|
| systemprompt.md | `system/QWEN.md` | project context file (QWEN.md) |
| code_agent.yaml | `agent.yaml` (model, params, mode flags) | settings/config + provider env |
| tool_descriptions/ | `tool_descriptions/` | tool description overrides |
| tools/ | `tools/` (MCP server defs, custom tools) | MCP config + custom tools |
| middleware/ | `middleware/` (hooks) | Qwen Code Hooks (pre/post tool call etc.) |
| skills/ | `skills/` | Auto-Skills / skill packages |
| sub_agents/ | `sub_agents/` (incl. orchestration topologies) | SubAgents / Agent Teams definitions |
| LongTermMEMORY.md | `memory/LongTermMEMORY.md` | Auto-Memory seed |

- A **materializer** (small, deterministic, versioned) renders workspace → a Qwen Code project directory at rollout time. It is the single trust boundary between "what the evolve agent wrote" and "what actually runs"; it validates shapes and fails loudly on unknown files.
- The Evolve Agent's prompts/config are updated (experiment overlay) to describe der's component semantics so its edits are native, not NexAU-flavored.
- This same workspace directory, at its adopted baseline state, IS the daily-driver configuration (`harness/` at repo root). One deployment, two purposes: rollouts run candidate copies; the daily driver runs the adopted baseline.

### D4. Trace pipeline: qwen session logs → AHE trace schema → ADB

- Qwen Code headless runs emit session logs/events (SDK/daemon expose streams; exact format pinned in Stage 2). A **qwen→AHE trace converter** (peer of the existing `trace_converter.py`) normalizes them into the schema ADB consumes, preserving: turns, tool calls + results, token usage per call, timestamps, final status.
- Metrics extraction happens here too: tokens in/out (from provider usage fields), cost (DeepSeek v4 pro pricing table, versioned in config), wall-clock, turns. These flow into scorecards independent of ADB, so scorecards exist even when analysis is skipped.

### D5. Two front doors, one substrate

- **Evolve driver** (inherited `evolve.py` + scripts): unattended autonomous iterations, best-of-N variants, explore agent pointed at Qwen Code source + der docs.
- **Experiment CLI** (thin new entrypoint reusing the same harbor invocation + scorecard code): `research eval <workspace> [--tasks subset]` → scorecard; `research ab <baseline-ws> <candidate-ws>` → paired scorecards + delta report + verdict template. This is how the owner's hand-written hypotheses run without invoking the evolve agent.
- Both doors write into the same `runs/` layout and the same scorecard schema; the dashboard does not care who initiated a run.

### D6. Model policy: DeepSeek v4 pro everywhere, pinned once

- Single source: top-level `llm:` in the der experiment overlay (`configs/experiments/exp-der-*.yaml`) + `.env` (`LLM_*`, `ADB_LLM_*` both → DeepSeek v4 pro endpoint). Exact model string + API base pinned; temperature 0 (or provider minimum) for rollout determinism; provider version recorded in every scorecard.
- The pin covers: rollout agent model, ADB, Evolve Agent, explore agent. Nothing in the research loop calls any other model. (The daily driver's model mix is unaffected.)
- Cost table for DeepSeek v4 pro (input/output/cached rates) is config data, versioned, so cost metrics are reproducible.

### D7. Task suite: pinned local subset, k=2, full suite occasionally

- V1 rollout suite: a **pinned local dataset directory** (`research/dataset/der-suite-v1/`) of ~50 tasks selected from terminal-bench@2.0 (selection script + criteria committed; harbor `path:` mode). Pinning as files beats `dataset:` references for reproducibility and offline reruns.
- `k: 2` rollouts per task (AHE default; gives per-task pass-rate signal for flip attribution).
- Full terminal-bench@2.0 runs are occasional (pre-adoption confirmation, leaderboard attempts), not per-iteration.
- Suite evolution rule: the suite version is part of every scorecard; scorecards are only diffable within the same suite version.

### D8. Infra: single self-hosted server, harbor local Docker first, E2B as an option

- V1 runs on the owner's server: harbor `env:` set to local Docker execution, `n_concurrent` 4–8 (right-sized to one box), tmux launchers + `evolve-resume.sh` for crash recovery.
- E2B (AHE's default) stays configured-but-off: flip to `env: e2b` + key when parallelism or isolation needs outgrow the box.
- Budget guard: per-iteration cost ceiling computed from the pricing table + hard `experiment_timeout_minutes`; the loop refuses to start an iteration whose projected cost exceeds the ceiling. Notifications: keep AHE's webhook notify, pointed at the owner's channel of choice.

### D9. Artifacts, publication, and the dashboard

- `runs/` (as upstream: `iteration_NNN/input|evolve`, `analysis/`, `change_evaluation.json`) — raw traces gitignored (size), everything distilled committed: manifests, scorecards (JSON), analysis digests.
- **Scorecard schema (one JSON per run, one row per task + aggregate):** suite version, workspace git hash, model string, k, per-task pass/fail × k, tokens in/out, cost, wall-clock, turns; aggregate means/deltas vs named baseline.
- **Dashboard generator** (small script): reads all committed scorecards → regenerates SVG charts (pass rate, tokens, cost, wall-clock over experiment sequence) + the experiment index table in README. Runs on verdict; committed with the verdict. GitHub renders SVGs natively — no external service.
- Experiment log: one markdown file per experiment (`experiments/EXP-NNN-slug.md`): hypothesis, setup (workspace diff), scorecard link, verdict — the "open notebook" unit builders read.

### D10. Promotion: verdicts gate adoption; the owner gates the daily driver

- Within the loop, AHE's native discipline applies: manifest per edit, next-round flip attribution, automatic rollback of failed predictions.
- Graduation to the daily driver is a **separate, human-gated step**: a promotion script turns the winning workspace delta into a PR against `harness/` embedding the manifest + scorecard link. Owner merges → daily driver picks it up. The unattended loop never edits `harness/` directly.

## 3. System diagram

```
                         ┌─────────────────────────────── der repo (public, MIT) ───────────────────────────────┐
                         │                                                                                       │
  owner hypotheses ──►  research CLI (eval / ab)  ─┐                                                             │
                         │                          │            ┌── runs/iteration_NNN/{input,evolve}           │
  autonomous loop  ──►  evolve.py (AHE, inherited) ─┤            │   manifests + change_evaluation.json          │
                         │        │                 ▼            │   analysis/ (ADB digests)                     │
                         │        │           harbor rollouts ───┤   scorecards/*.json ──► dashboard SVGs ──► README
                         │        │           (local Docker,     │                                               │
                         │        │            k=2, n_conc 4-8)  └── experiments/EXP-NNN-slug.md (notebook)      │
                         │        │                 │                                                            │
                         │        ▼                 ▼                                                            │
                         │   Evolve Agent      der harbor agent = [ qwen-code (pinned) + materializer(workspace) │
                         │   (DeepSeek v4 pro)      + DeepSeek v4 pro provider + trace emitter ]                 │
                         │        ▲                 │                                                            │
                         │        │                 ▼                                                            │
                         │   ADB digests  ◄── qwen→AHE trace converter (+ metrics extraction)                    │
                         │                                                                                       │
                         │   harness/  = adopted baseline workspace  ◄── promotion PR (human-gated)              │
                         └───────────────────────────────────────────────────────────────────────────────────────┘
```

## 4. Lifecycle walks

**(a) Autonomous evolve iteration:** evolve.py reads config → harbor runs suite (k=2) with der agent on workspace `input/` → traces converted, metrics extracted → attribution binds previous manifest predictions to observed flips, failed edits reverted → ADB distills evidence corpus → Evolve Agent (DeepSeek v4 pro) writes edits + manifests into `evolve/` → scorecard + dashboard regenerate → next iteration (or stop on target/max/budget).

**(b) Owner hypothesis (A/B):** owner branches workspace, hand-writes the change (e.g. new hook middleware that compresses tool outputs) + hypothesis in `experiments/EXP-NNN.md` → `research ab baseline candidate` → paired scorecards + delta → owner writes verdict into the experiment file → dashboard regenerates → adopted deltas go through the promotion PR.

**(c) Promotion:** winning workspace state → promotion script → PR against `harness/` with manifest + scorecard → owner review/merge → daily driver (Qwen Code reading `harness/` materialized config) now runs the adopted baseline.

## 5. Risks and mitigations

1. **evolve.py monolith coupling (202KB):** the NexAU agent may be assumed beyond the documented seams. Mitigation: Stage 2 begins with a seam audit of evolve.py; adapters only at config-documented seams; if coupling is deep, fall back to "harbor-only substrate first" (CLI + scorecards + dashboard shipping value while the evolve driver is adapted).
2. **Harbor lacks a qwen-code adapter:** then we write a custom harbor agent spec (bounded, documented interface). Verification task in review round.
3. **Qwen Code headless trace completeness:** if session logs lack per-call token usage, metrics degrade. Mitigation: daemon/SDK event stream as alternative source; worst case an OpenAI-compatible logging proxy in the rollout container (last resort, adds a component).
4. **Noise vs k=2:** flip attribution on 50 tasks × k=2 is noisy for small effects. Mitigation: inherited AHE behavior first (it works at k=2); for owner A/Bs where the delta matters, `research ab --k 4`; scorecards always carry per-task pass counts so uncertainty is visible.
5. **Benchmark contamination (DeepSeek trained on tasks):** acceptable — the loop measures *relative* deltas under a fixed model; absolute numbers are for fun (leaderboards).
6. **Cost blowout:** budget guard (D8) + DeepSeek pricing + timeouts; per-iteration projected-cost check.
7. **Qwen Code moves fast (nightly releases):** pin the version in the rollout image; upgrades are themselves experiments (run the suite on the new version before adopting).

## 6. Open questions (to resolve in review / Stage 2)

1. Does harbor ship a native qwen-code agent, and does it support local Docker `env` cleanly? (changes D2/D8 sizing)
2. Where exactly do Qwen Code headless session logs live and what do they contain? (D4; Stage 2 pins format)
3. Subset selection method for der-suite-v1 (random stratified by task category? difficulty-balanced?) — needs a defensible, committed criterion.
4. Does AHE's flip-attribution require NexAU trace fields beyond what qwen traces can provide? (seam audit)
5. Promotion PR mechanics: full workspace copy vs delta patch; how flags for daily-driver experiments are represented in `harness/`.

## 7. Rough cost intuition (to be firmed in Stage 2)

One iteration ≈ 50 tasks × 2 rollouts × (task tokens) at DeepSeek v4 pro rates + ADB distillation over traces + one Evolve Agent session. DeepSeek pricing makes the rollout bulk cheap; ADB over ~10M trace tokens is the second-largest line; budget guard caps the sum. Exact numbers require the pricing table + a pilot run (Stage 2 includes a 5-task smoke suite for calibration before full iterations).
