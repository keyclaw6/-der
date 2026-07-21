# Agent instructions

Read `VISION.md` before every task. It is the project's human-owned North Star. Never edit, move, or delete `VISION.md` without explicit human approval for that exact change.

This is the only `AGENTS.md` in the repository. Do not create nested copies. Treat this file as a map, not an encyclopedia: start here, then load only the context needed for the task.

## Truth and repository map

- Truth ranks in this order: `VISION.md` first, `openspec/specs/` second, everything else after.
- `VISION.md` defines the enduring outcome and constraints.
- `openspec/specs/` is the behavioral contract. Requirement text uses RFC 2119 keywords (MUST, SHOULD, MAY).
- `openspec/changes/<slug>/` holds temporary proposals for intentional behavior changes.
- `src/` contains production code. `tests/` contains automated tests. `scripts/` contains repository automation.
- Code explains how the system works. Codebase Memory (CBM) explains how code connects.
- Git is history. Add documentation only when code, specs, tests, configuration, or generated state cannot carry the truth.

## Progressive disclosure

1. Read `VISION.md` for what the project is optimizing for.
2. Read the relevant baseline specs and any overlapping active OpenSpec change.
3. Use `codebase-memory-mcp` before broad cross-file exploration: inspect architecture, symbols, call paths, and change impact, then read the exact source and tests before editing.
4. Load additional files only when the task requires them. Do not crawl the repository without a reason.

If CBM is unavailable, say so and continue with direct source inspection. Never claim to have used a tool that was unavailable.

## Harness-engineering principles

Apply the following operating principles from OpenAI's harness-engineering article:

- Humans steer; agents execute. Humans own vision, priorities, and approval. Agents implement, verify, and leave the repository in a legible state.
- The repository is the system of record. Do not rely on hidden chat context, personal memory, or external notes for facts future agents need.
- Optimize for agent legibility: keep canonical commands discoverable, feedback loops short, errors actionable, and important state inspectable from the repository.
- Enforce important boundaries and recurring invariants centrally with schemas, types, tests, linters, or scripts. Allow implementation freedom inside those boundaries.
- When an agent repeatedly struggles, improve the repository's tools, structure, checks, or context instead of adding more ad hoc prompt text.
- Prevent entropy continuously. Remove stale instructions, dead code, obsolete scaffolding, and duplicated patterns before they become examples future agents copy.

## How to code

- Seek the most elegant solution to the current requirement: the smallest, clearest system of concepts, not the smallest diff. Rewrite or restructure when that leaves the repository materially smaller or clearer. Never optimize for patch size or least effort.
- Preserve the established layout and dependency direction. When the layout or canonical commands change, update the README commands in the same change.
- Prefer short feedback loops: reproduce, change, run focused checks, then run the full project checks.
- Parse and validate data at trust boundaries. Do not build behavior on guessed shapes or silent fallbacks.
- Keep the project runnable and verifiable without hidden conversational setup.
- Update tests with code. Test observable behavior and important failure modes rather than implementation trivia.

## YAGNI and maintainable code

Apply YAGNI: first ask whether the code is needed now; then reuse what already exists; prefer the standard library or native platform; reuse an existing dependency; only then add the minimum new implementation or dependency.

YAGNI is not code golf. Keep validation, security, privacy, accessibility, data integrity, observability, and actionable errors where the risk requires them.

Write code as though a human will maintain it. Use clear names, obvious control flow, small cohesive modules, and one authoritative implementation for recurring business rules. Avoid speculative abstractions, options, fallbacks, extension points, and dependencies. Do not duplicate an invariant merely because an agent can update every copy later.

## Spec-driven development

Create intentional behavioral changes under `openspec/changes/<kebab-case-slug>/` before implementation. Keep proposals focused on the current need and state explicit non-goals.

Changes follow the project-local lean schema (`openspec/schemas/lean`): one `proposal.md` covering why, goals and non-goals, what changes, optional design decisions, and a definition of done — plus delta specs. No separate design or tasks files.

After human review, finalize with:

```sh
npm run spec:finalize -- <slug> --human-approved
```

The finalizer applies the OpenSpec delta to `openspec/specs/`, removes the active change and OpenSpec archive copy, and leaves those edits to be committed together. Git history is the archive.

A bug fix that only restores an existing baseline requirement may skip a change proposal, but it must identify the requirement and add regression evidence. Requirement ownership lives in `openspec/ownership.toml` and is validated by `scripts/spec_owners.py`.

## Environment and secrets

Tracked `.env` and `.env.*` files must contain dotenvx public keys and encrypted values only. Private decryption keys belong in `.env.keys` or `DOTENV_PRIVATE_KEY*` process variables and must never be committed, logged, indexed, or pasted into agent conversations.

Use the repository's pinned dotenvx commands:

```sh
npm run env -- <command>
npx dotenvx set <KEY> <value>
```

The human supplies the existing encrypted `.env` and private `.env.keys` through an approved local secret channel. Agents must not ask a human to paste secrets into chat.

## Completion

Before finishing:

- run the smallest relevant tests while iterating;
- run `npm run check` before handoff;
- inspect the diff for accidental complexity, duplicated rules, secret exposure, spec drift, and unrelated changes;
- use CBM change-impact analysis for non-trivial cross-file code changes;
- leave code, tests, specs, ownership, and documented commands consistent.
