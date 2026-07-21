# Context pack — der auto-research loop (Stage 1: architecture)

## The project (from committed VISION.md, keyclaw6/-der)

A self-hosted coding-agent harness that is simultaneously the owner's daily driver, laboratory, and open notebook. Base: **Qwen Code** (customized, not built from scratch). Improvement method: **Agentic Harness Engineering (AHE)** — evaluate → analyze → improve loop with three observability pillars (file-level git-tracked components; traces distilled into drill-down evidence; every change a falsifiable contract: failure evidence, root cause, targeted fix, predicted impact — verified next rollout, reverted on failed prediction). Non-negotiables: falsifiable contracts, observability at every layer, headless core with replaceable faces, Codebase Memory as code intelligence, open by default (MIT). Success criteria include: unattended evolution loop; comparable scorecards (pass rate, tokens in/out, cost, wall-clock, turns) stored in repo, diffable vs baseline; README dashboard charts regenerated when verdicts land; mixed-model orchestration; leaderboard submissions for fun.

## Owner decisions binding this plan

1. Auto-research harness is based on **https://github.com/china-qijizhifeng/agentic-harness-engineering** (official AHE code, MIT, Python).
2. **DeepSeek v4 pro is used for EVERYTHING in the research loop** — agent-under-test model in evals, Agent Debugger, Evolve Agent, explore agent. Reason: cheap + keeps everything consistent. (The daily-driver harness uses whatever models the owner configures; this pin applies to the research loop.)
3. Base runtime being evolved: the der harness = Qwen Code + owner's custom component layer.
4. One-person operation, self-hosted (cloud server), must be startable/resumable without babysitting.
5. Plan is written in two stages: Stage 1 = architecture (this document's subject), Stage 2 = expansion into an implementation plan for another LLM agent (only after owner approves Stage 1).

## Verified facts — AHE repo (china-qijizhifeng/agentic-harness-engineering @ main)

- Top level: `evolve.py` (202KB main-loop orchestrator), `trace_converter.py` (33KB), `agents/` (code_agent_simple = NexAU-based agent-under-test; evolve_agent; explore_agent), `configs/` (base.yaml + experiments/ overlays with `_base:` inheritance and `${ENV}` substitution from `.env`), `scripts/` (tmux wrappers evolve.sh / evolve-resume.sh), `skills/`, `experiments/`, `pyproject.toml`, MIT LICENSE, paper PDF.
- `configs/base.yaml` (verified content):
  - Dataset: either `path:` (local dataset dir) or `dataset: "terminal-bench@2.0"` (harbor built-in).
  - `target_pass_rate: 0.95`, `max_iterations: 100`, timeouts (`harbor_job_timeout_minutes`, `experiment_timeout_minutes`).
  - Top-level `llm:` = `{api_key: ${LLM_API_KEY}, base_url: ${LLM_BASE_URL}, model: "gpt-5.4"}` — code_agent AND harbor read from this via env passthrough (`${env.LLM_*}`). `.env.example` default model literally `nex-agi/deepseek-v3.1-nex-1`, so DeepSeek-family via OpenAI-compatible base_url is a known-good path.
  - `harbor:` = `{agent: "nexau", env: "e2b", k: 2 (rollouts per task), n_concurrent: 64, force_build, e2b_sandbox_timeout}`.
  - `source_config_dir: "agents/code_agent_simple"`, `agent_config_filename: "code_agent.yaml"` — the agent-under-test config dir is pluggable.
  - `best_of_n:` — N parallel evolve agents per iteration with different strategy hints; best variant adopted; next iteration sees cross-variant comparison.
  - `code_agent_patch`, `evolve_agent`, `explore_agent_patch` — runtime patches (deep-merged) per experiment; evolve_agent LLM falls back to top-level `llm` if unset.
  - `agent_debugger.llm` reads `ADB_LLM_*` env (can be separate model; we will set it to DeepSeek v4 pro too).
  - `explore_agent:` enabled, runs parallel to iteration 1, `code_sources:` = git repos to explore (currently nexau) → generates knowledge skills for the evolve agent.
  - `notify:` Feishu webhook on iteration completion/target/timeouts.
- `.env.example`: LLM_API_KEY/BASE_URL (primary), ADB_LLM_* (debugger), E2B_API_KEY (+ optional self-hosted E2B cluster URL/domain), GITHUB_TOKEN, SERPER_API_KEY (evolve agent web_search), optional HTML parser keys.
- Workspace contract (from README): Evolve Agent may only write inside `workspace/` exposing seven NexAU component types: `systemprompt.md`, `code_agent.yaml`, `tool_descriptions/`, `tools/`, `middleware/`, `skills/`, `sub_agents/`, plus `LongTermMEMORY.md`. Every edit commits 4 manifest fields (failure evidence, root cause, targeted fix, predicted impact). `runs/iteration_NNN/` mixes generations: `input/` (workspace from N-1, just evaluated) and `evolve/` (what N writes, evaluated next loop); flips attributed in `change_evaluation.json`; failed predictions rolled back at file granularity. Analysis artifacts: `analysis/overview.md` + `analysis/detail/{task}.md`, claims linked to raw traces.
- Headline: NexAU-AHE 84.7%±2.1 pass@1 on Terminal-Bench 2 (GPT-5.5); GPT-5.4 69.7→77.0 over 10 iterations.

## Verified facts — Qwen Code (QwenLM/qwen-code, TypeScript, Apache-2.0, v0.20.0-nightly 2026-07-21)

- Modes: interactive `qwen` TUI; **headless `qwen -p "..."`** (scripts/CI, no UI); IDE plugins (VS Code/Zed/JetBrains); Desktop app; **daemon `qwen serve` = shared agent session over HTTP+SSE (ACP), multiple clients, experimental**; SDKs (TypeScript/Python/Java); IM bots (Telegram/DingTalk/WeChat/Feishu).
- Agentic surface: SubAgents, Agent Teams, dynamic workflows, Auto-Memory, Auto-Skills, Hooks, built-in skills (/review /batch /loop /bugfix…), MCP, Plan Mode, LSP, Auto Mode, sandbox, git worktrees, Computer Use.
- Multi-protocol: OpenAI, Anthropic, Gemini, Qwen APIs + any third-party/local (Ollama/vLLM), **runtime switching** — DeepSeek v4 pro via OpenAI-compatible endpoint is directly supported.
- "Agent Arena": multi-model head-to-head on the same task (native).
- Ecosystem GUIs that can sit on top: Qwen Code Desktop, AionUi, Gemini CLI Desktop (cross-platform desktop/web/mobile), acpx/"Qwen Code Claw" (other agents delegate to Qwen Code via ACP).
- Fork lineage: Gemini CLI. Project-level config lives in the repo dir (context file QWEN.md, settings, agents/subagent definitions, skills, hooks, MCP config) — exact paths to be verified in Stage 2.

## Terminology

- **harbor** = Terminal-Bench's rollout runner (task containers, agent adapters, k rollouts, results). AHE delegates all evals to it.
- **ADB / Agent Debugger** = AHE's trace-distillation component (experience observability).
- **der harness** = Qwen Code + the owner's component layer (the thing being daily-driven AND evolved).
- **Component workspace** = the file-level, git-tracked directory of harness components that the Evolve Agent edits and rollouts consume.

## Links

- AHE: https://github.com/china-qijizhifeng/agentic-harness-engineering (raw: https://raw.githubusercontent.com/china-qijizhifeng/agentic-harness-engineering/main/...)
- AHE paper: https://arxiv.org/abs/2604.25850
- Qwen Code: https://github.com/QwenLM/qwen-code — docs: https://qwenlm.github.io/qwen-code-docs/
- Terminal-Bench/harbor: https://github.com/laude-institute/terminal-bench
- der repo: https://github.com/keyclaw6/-der (VISION.md committed at fe9d13b)
