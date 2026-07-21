# research-plan/ — der auto-research loop planning artifacts

Stage 1 (architecture) planning record for the der auto-research loop. Produced 2026-07-21 through an adversarial multi-agent review process; committed here so external reviewers can access the full record.

## Status

- **Stage 1 (architecture): restructured and final-audited.** Rounds 1–3 (internal adversarial: 6 reviewer agents) converged draft_v3; round 4 (external GPT 5.6 Sol Pro review) returned RESTRUCTURE with five approval conditions — all adopted in **draft_v4**; round 5 (gap audit) verified 100% integration, restored four dropped protections, and source-verified the new load-bearing facts. **Awaiting owner approval.**
- **Stage 2 (implementation plan): not started** — blocked on owner approval of Stage 1.

## Reading order

1. `context.md` — project context, owner constraints, and source-verified facts about AHE, Qwen Code, and harbor.
2. `draft_v4.md` — **the architecture awaiting approval** (§9 records the round-4 adopt/retain/reject disposition; §10 is the convergence log; v1–v3 retained for history).
3. `reviews/` — the eight review documents:
   - `round1_forge.md` (systems/contracts), `round1_prism.md` (source-fidelity audit against AHE/harbor/Qwen Code code), `round1_flint.md` (operations/YAGNI/cost)
   - `round2_vex.md` (red team on round-1 additions), `round2_sage.md` (implementation-readiness)
   - `round3_arbiter.md` (closure audit: resolution matrix + regression sweep)
   - `round4_solpro.md` (**external GPT 5.6 Sol Pro review** — RESTRUCTURE verdict that produced v4)
   - `round5_sentry.md` (final gap audit of the v4 integration)
4. `REVIEW_PROMPT.md` — the mission brief that produced the round-4 external review.

## Related documents

- `/VISION.md` (repo root) — the project's human-owned North Star (committed, approved).
- AHE (the research-loop base): https://github.com/china-qijizhifeng/agentic-harness-engineering
- Qwen Code (the harness base runtime): https://github.com/QwenLM/qwen-code
- DeepSWE v1.1 (candidate eval suite): https://github.com/datacurve-ai/deep-swe · runner: https://github.com/datacurve-ai/pier
- Benchmark methodology reference: https://github.com/Tura-AI/benchmark/blob/main/doc/benchmark-methodology.md

Note: review files reference local audit paths like `ahe-src/evolve.py` with line numbers — those refer to the AHE repository's files at its current `main` (pinned commit recorded during Stage 2), fetchable from the AHE link above.
