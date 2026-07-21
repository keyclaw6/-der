# research-plan/ — der auto-research loop planning artifacts

Stage 1 (architecture) planning record for the der auto-research loop. Produced 2026-07-21 through an adversarial multi-agent review process; committed here so external reviewers can access the full record.

## Status

- **Stage 1 (architecture): converged** after 3 adversarial review rounds (6 reviewer agents, 27/27 findings resolved). Under external review; not yet owner-approved.
- **Stage 2 (implementation plan): not started** — blocked on owner approval of Stage 1.

## Reading order

1. `context.md` — project context, owner constraints, and source-verified facts about AHE, Qwen Code, and harbor.
2. `draft_v3.md` — **the architecture under review** (v1 and v2 are retained for history; the convergence log in §10 summarizes what changed and why).
3. `reviews/` — the six review documents:
   - `round1_forge.md` (systems/contracts), `round1_prism.md` (source-fidelity audit against AHE/harbor/Qwen Code code), `round1_flint.md` (operations/YAGNI/cost)
   - `round2_vex.md` (red team on round-1 additions), `round2_sage.md` (implementation-readiness)
   - `round3_arbiter.md` (closure audit: resolution matrix + regression sweep)
4. `REVIEW_PROMPT.md` — the mission brief for the external (GPT 5.6 Sol Pro) architecture review, including the open questions the review should answer.

## Related documents

- `/VISION.md` (repo root) — the project's human-owned North Star (committed, approved).
- AHE (the research-loop base): https://github.com/china-qijizhifeng/agentic-harness-engineering
- Qwen Code (the harness base runtime): https://github.com/QwenLM/qwen-code
- DeepSWE v1.1 (candidate eval suite): https://github.com/datacurve-ai/deep-swe · runner: https://github.com/datacurve-ai/pier
- Benchmark methodology reference: https://github.com/Tura-AI/benchmark/blob/main/doc/benchmark-methodology.md

Note: review files reference local audit paths like `ahe-src/evolve.py` with line numbers — those refer to the AHE repository's files at its current `main` (pinned commit recorded during Stage 2), fetchable from the AHE link above.
