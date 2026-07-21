# Bootstrap

> One-time guided setup: the founding session between the human and the agent. This file is the protocol for that session and is deleted in the same commit that records its output. If `VISION.md` is already filled in, this file is stale — delete it.

## Why

A project created from this template starts with placeholder truth: `VISION.md` has no intent and `openspec/specs/` has no behavior. Implementation is cheap; alignment is the scarce input. The riskiest moment in an agent-built project is the fluffy start — code written before human and agent agree on what is worth building.

This protocol turns setup into a deliberate working session that produces the vision, the founding behavioral contract, and the initial architecture before any code exists.

## What the session produces

- `VISION.md` completed and explicitly approved by the human.
- Initial baseline specs for one to three V1 capabilities under `openspec/specs/`.
- Canonical setup, run, and verify commands recorded in `README.md`.
- An `openspec/ownership.toml` entry for every requirement.
- The deletion of this file, committed together with all of the above.

Founding is not changing: the baseline starts empty, so the first specs are written directly to `openspec/specs/`. Every later behavior change goes through `openspec/changes/<slug>/` as usual.

## Non-goals

- No code or prototypes during the session; dependency choices stop at the stack decision recorded in `README.md`.
- No roadmap beyond V1. Later capabilities become ordinary OpenSpec changes.
- No new documentation artifacts such as glossaries or ADR trees. Settled vocabulary belongs in the specs' own language; hard-to-reverse decisions belong in Git history.

## Division of labor

The agent contributes what models are good at: information access and research, prior art, option generation, and a recommendation for every question it asks. The human contributes what humans are good at: judgment about what is worth wanting, what is acceptable, and what is out of scope. The agent recommends; the human decides.

## Conduct

1. Ask exactly one question at a time, then wait. Never send a questionnaire.
2. Attach a recommendation to every question — your best answer and the reasoning in one or two sentences. The human aligns by agreeing or pushing back, not by facing a blank prompt.
3. Research before asking. Anything answerable from the repository or from public sources — prior art, comparable products, evidence the problem exists, common failure modes of similar systems — is your homework, not a question. Bring findings back as short summaries with a recommendation.
4. Challenge the premise at least once, early: what is the real problem underneath the stated idea, who has it today, and what do they do about it now? If honest research weakens the idea, say so plainly.
5. Write as decisions resolve. Fill the relevant `VISION.md` section or README command documentation the moment it settles and read it back to the human. Do not batch writing to the end.
6. Hold the falsifiability bar: every vision statement must be one a reasonable person could disagree with, and success must be observable. "Fifty weekly active users completing X by June" clears the bar; "a delightful experience" does not.
7. Non-goals must be real temptations — plausible directions this project could actually drift toward — not strawmen.
8. Depth over speed. This session lays the groundwork for everything that follows; there is no time pressure. Do not compress phases or skip approval gates.
9. The human's explicit approval closes each phase. Disagreement reopens the question; silence is not consent.

## Phases

### 1. Orient

- 1.1 Read `VISION.md`, `README.md`, and this file in full.
- 1.2 Confirm the human wants to run the bootstrap now, and ask for the raw idea in their own words — unpolished is fine.

### 2. Vision

- 2.1 Interview toward each `VISION.md` section in order: North Star, Who it serves, What success looks like, Non-negotiables, Not optimizing for.
- 2.2 Research prior art and evidence for the problem; present findings with a recommendation before locking the North Star.
- 2.3 Fill each section as it resolves and read it back.
- 2.4 Obtain explicit approval of the completed `VISION.md`.

### 3. Reality check

- 3.1 Walk the core experience end to end with the human: happy path, failure paths, edge cases.
- 3.2 Identify the riskiest assumption — the thing that, if false, kills the idea — and how V1 tests it cheaply.
- 3.3 Split scope: the smallest V1 that produces the vision's outcome. Everything else is explicitly later.

### 4. First specs

- 4.1 Agree on one to three V1 capabilities and their kebab-case names.
- 4.2 Write each as a baseline spec at `openspec/specs/<capability>/spec.md` in this shape:

  ```markdown
  # <capability>

  ## Purpose

  One paragraph: why this capability exists. Optionally one Non-goals line
  naming what it deliberately excludes.

  ## Requirements

  ### Requirement: <Testable behavior, stated as an outcome>

  The system MUST <one behavior; RFC 2119 keywords>.

  #### Scenario: <Happy path>

  - **WHEN** ...
  - **THEN** ...

  #### Scenario: <Failure mode>

  - **WHEN** <invalid input, fault, or boundary condition>
  - **THEN** <specified safe behavior>
  ```

- 4.3 Cover the failure modes from the reality check as scenarios, not only the happy path.
- 4.4 Validate: `npm run spec:validate`.

### 5. Stack and commands

- 5.1 Research candidate stacks and structures; present two or three options with trade-offs and one recommendation. The human picks.
- 5.2 Record the canonical setup, run, and verify commands in `README.md`. Structure lives in the code itself; CBM explains how it connects.
- 5.3 Ensure the commands are real and runnable, not aspirational.

### 6. Ownership and verification

- 6.1 Add an `openspec/ownership.toml` entry for every requirement, keyed `<capability>/<requirement-title-as-kebab-case>`.
- 6.2 Run `npm run check` and resolve every error.

### 7. Review, delete, commit

- 7.1 Present the full diff for human review: `VISION.md`, `README.md`, baseline specs, ownership.
- 7.2 After explicit approval, delete this `BOOTSTRAP.md` and commit everything together. Git history is the archive; a project bootstraps once.

## Exit criteria

The session is complete only when all of the following hold:

- Every `VISION.md` section is filled with falsifiable statements the human has approved.
- One to three V1 capabilities have baseline specs, each requirement testable, with scenarios covering the failure modes surfaced in the reality check.
- `README.md` documents real, runnable setup, run, and verify commands.
- Every requirement has an entry in `openspec/ownership.toml`.
- `npm run check` passes.
- This file no longer exists.

The interview mechanics follow grill-with-docs; the discovery posture follows vibe-check. Both are listed in the README sources.
