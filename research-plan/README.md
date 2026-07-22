# research-plan/ — der auto-research loop: planning record and execution inputs

Final planning state, ready for implementation. Produced 2026-07-21/22 through a multi-round adversarial process (three internal review rounds, an external GPT 5.6 Sol Pro architecture review, a final gap audit, and an external implementation-plan author audited in round 6). Superseded drafts (v1–v3) were removed in the cleanup commit — Git history is the archive.

## The two files that matter for execution

| Role | File |
| --- | --- |
| **Stage 1 — approved architecture** (decisions D1–D12, build order, verification items) | `research-plan/stage1-architecture.md` |
| **Stage 2 — implementation plan** (34 tasks, unattended-ready, audited + repaired) | `research-plan/2026-07-21-der-auto-research-loop-stage2.md` |

The Stage 2 plan is **unattended-ready**: STOP gates follow the Unattended STOP protocol (Execution conventions §3 — soft stops record deviations to `research-plan/DEVIATIONS.md` and continue with best judgment; hard halts only for spend-limit, security/isolation, or unevaluated-ship violations). All frozen upstream revisions and DeepSeek pricing were verified against live sources on 2026-07-22 (AHE `faf44bc4`, Pier v0.3.0 `e69a20e4`, Qwen v0.20.0 `92fda560`, DeepSWE commit `8cae5984` — benchmark v1.1 has no upstream git tag, pinned by commit; pricing 0.003625/0.435/0.87 per 1M matches the official DeepSeek page).

## Process record

- `context.md` — constraints and source-verified facts gathered before drafting.
- `stage1-architecture.md` — the approved architecture (formerly draft_v4; §9 records the external-review disposition, §10 the full convergence log).
- `reviews/` — the audit trail: `round1_forge/prism/flint` (internal adversarial), `round2_vex/sage` (red team + readiness), `round3_arbiter` (closure), `round4_solpro` (external architecture review — RESTRUCTURE, adopted), `round5_sentry` (integration gap audit), `round6_mason` (Stage 2 plan audit — 58 fixes, verdict READY-AFTER-APPLIED-FIXES).
- `REVIEW_PROMPT.md` / `STAGE2_PROMPT.md` — the mission briefs that produced round 4 and the Stage 2 plan.
- `pins/` and `DEVIATIONS.md` — created during execution by the implementation agent (discovery evidence and recorded deviations).

## Related

- `/VISION.md` — the project's human-owned North Star (approved, committed).
- Upstream sources: [AHE](https://github.com/china-qijizhifeng/agentic-harness-engineering) · [Pier](https://github.com/datacurve-ai/pier) · [DeepSWE](https://github.com/datacurve-ai/deep-swe) · [Qwen Code](https://github.com/QwenLM/qwen-code)
