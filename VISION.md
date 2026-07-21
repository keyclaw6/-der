# Vision

> Human-owned North Star. Agents must not edit this file without explicit human approval.

## North Star

A self-hosted coding-agent harness that is simultaneously my **daily driver**, my **laboratory**, and an **open notebook** for anyone building the same thing.

Today my agent work runs through stock Codex: a sealed harness where orchestration topology, prompt handling, and model choice are someone else's decisions. This project replaces it with a harness built by customizing a proven open-source base — **Qwen Code**, chosen through an explicit comparison — so that feature table stakes come from upstream while three layers stay mine:

1. **Orchestration I design.** Agent topologies are configuration, not code forks — and no single topology is the point. A Sentinel intent layer handing goals to an orchestrator that delegates to workers is one arrangement I want to try; flat single-agent setups, competing orchestration loops, and shapes I haven't thought of yet are equally first-class. Every role in whatever topology is active is independently assignable to any model from any provider under my own API keys and subscriptions, and the topology itself is a swappable, experimentable unit.

2. **An evolution loop, not a settings page.** The harness improves the way [Agentic Harness Engineering](https://arxiv.org/abs/2604.25850) improves harnesses: every editable layer is decomposed into file-level, git-tracked components; rollout traces are distilled into drill-down evidence instead of raw logs; and every change ships as a falsifiable contract — failure evidence, root cause, targeted fix, predicted impact — verified against the next rollout and reverted when the prediction fails. Hypotheses (token-saving features, prompt handling strategies, orchestration variants) are validated on a cheap rollout suite — benchmark subsets run on inexpensive models — before they touch my daily configuration. Experiments run behind flags in the deployment I use every day; there is no separate experiment branch.

3. **Research in the open.** The repository is public under MIT, and every experiment — hypothesis, setup, scorecard, verdict, including the failures — is published in the repo and indexed from the README so interested builders can read along, reproduce, and fork. The README leads with a glanceable dashboard: charts, regenerated from experiment scorecards, showing how the harness is trending on the metrics that matter — task success, speed, token use, cost — so continual measured improvement is publicly visible, not claimed.

The enduring outcome: **my harness changes are adopted on measured evidence, never on vibes — and the evidence is public.**

## Who it serves

- **The owner-operator (me).** I daily-drive the harness for real coding work and experiment on it in the same deployment. Every capability exists to serve this one user's workflow first.
- **Builders reading along.** Anyone constructing their own harness can follow the published experiment log, reuse the components, and fork the repo. They are readers and forkers, not customers: the project publishes for them but is not steered by them.

## What success looks like

- **Mixed-model orchestration is real:** a real task completes with models from two different providers filling different roles in one session — e.g. a frontier model planning while cheaper workers execute — with both the topology and the per-role model assignment changeable per session without code changes.
- **Comparable scorecards:** every experiment produces the same metrics — task pass rate, tokens in/out, cost, wall-clock, turns — stored in the repo and diffable against baseline.
- **Glanceable public progress:** the README renders up-to-date charts of pass rate, wall-clock, tokens, and cost across experiment iterations, regenerated automatically when a verdict lands; a visitor can tell within a minute whether the harness is improving and which change moved which metric.
- **The evolution loop runs unattended:** evaluate → analyze → improve iterations execute end-to-end, every edit carries its manifest (evidence, root cause, fix, prediction), and edits whose predictions fail are reverted automatically.
- **Leaderboards, for fun:** when an evolved configuration looks strong, it gets submitted to public benchmark leaderboards — rank-chasing is embraced as fun and as an external sanity check, with at least one public submission in the first year.
- **Anywhere access:** I can start, steer, and approve sessions from a phone browser as well as a desktop.

## Non-negotiables

- **Every change is a falsifiable contract.** Failure evidence, root cause, targeted fix, and predicted impact are recorded before adoption and verified against the next rollout — the AHE manifest discipline applies to harness changes whether a human or an agent proposes them.
- **Observability at every layer.** Harness components are file-level and git-tracked; traces are distilled into evidence I can drill into; nothing I run daily is a black box I cannot inspect.
- **Headless core, replaceable faces.** The harness core is a server with a documented API and event stream. The TUI is the first thin client; web and mobile GUIs are swappable clients on the same protocol. No UI owns state, so any face can be replaced without touching the core.
- **Codebase Memory is the code-intelligence layer.** Structural understanding of code — architecture, symbols, call paths, change impact — flows through CBM, not ad-hoc crawling.
- **Open by default.** MIT license; experiments are published win or lose. Negative results are results.

## Not optimizing for

- **Feature parity with opencode, Codex, or Claude Code.** The upstream base supplies table stakes; I do not chase TUI polish or breadth.
- **Becoming a hosted product.** No multi-tenancy, billing, signups, SLAs, or support. Open code is not a hosted service.
