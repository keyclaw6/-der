# Agent-first project template

A small repository template for projects developed by humans and coding agents. It is based primarily on OpenAI's harness-engineering approach: make the repository the system of record, give agents a concise map with progressive disclosure, make the project legible and verifiable, enforce important boundaries centrally, and remove stale patterns continuously.

## Structure

```text
AGENTS.md              One repository-wide operating map
VISION.md              Human-owned North Star
BOOTSTRAP.md            One-time guided setup protocol (self-removing)
src/                    Production code
tests/                  Automated tests
openspec/               Specs, changes, ownership, and the lean workflow schema
scripts/                Small repository lifecycle checks
.github/workflows/      CI running the repository checks
.mcp.json               Codebase Memory MCP configuration
.env                    Tracked dotenvx-encrypted environment placeholder
package.json            Pinned OpenSpec and dotenvx tooling
```

There is exactly one `AGENTS.md` and no `docs/` directory. CI runs the repository checks on every push and pull request; nothing mechanically protects `VISION.md` — agents are instructed not to change it without explicit human approval.

## Prerequisites

- Git
- Node.js 20.19 or newer
- Python 3.11 or newer
- `codebase-memory-mcp` installed for code intelligence

## Start a project

1. Copy this repository or use it as a template.
2. Replace `.env` with your existing encrypted dotenvx file. Put the matching private file at `.env.keys`; it is ignored by Git, Docker, and CBM.
3. Install the pinned tools:

   ```sh
   npm ci
   ```

4. Install `codebase-memory-mcp` and ensure its binary is on `PATH`, or adjust `.mcp.json` for the local installation.
5. Run the bootstrap: ask your agent to run `BOOTSTRAP.md`. It interviews you — one question at a time, with research and a recommendation attached to every question — to write `VISION.md` and the initial baseline specs, then deletes itself in the same commit. To skip the guided session, delete `BOOTSTRAP.md`, fill `VISION.md`, and write the first baseline specs by hand.
6. Verify the result:

   ```sh
   npm run check
   ```

A clone without `.env.keys` can inspect the repository and update encrypted values with the public key in `.env`, but it cannot decrypt secrets. Provision the private key outside Git.

## Common commands

Run a command with the encrypted environment:

```sh
npm run env -- your-command
```

Set or rotate an encrypted value:

```sh
npx dotenvx set API_KEY "<value-from-your-local-secret-manager>"
```

Create and validate an OpenSpec change:

```sh
npx openspec new change add-example
npx openspec validate add-example --strict
```

After human review, apply the delta and remove the change folder:

```sh
npm run spec:finalize -- add-example --human-approved
```

Run all repository checks:

```sh
npm run check
```

## Truth model

`VISION.md` is the highest truth. `openspec/specs/` is the second: the behavioral contract, written with RFC 2119 keywords. Proposed behavior lives temporarily in `openspec/changes/<slug>/`. Code explains implementation, tests provide executable evidence, CBM explains structural connections, and Git is history. Documentation is added only when those sources cannot carry the truth.

After human review, an OpenSpec delta is applied to the baseline and the active change folder is removed in the same commit. Git history is the archive. Each requirement heading has an ownership entry in `openspec/ownership.toml` using `<capability-path>/<requirement-title-as-kebab-case>`.

## Dotenvx convention

Encrypted `.env` and `.env.*` files are tracked. They may contain `DOTENV_PUBLIC_KEY*` and `encrypted:...` values. `.env.keys`, `.env.keys.*`, and `DOTENV_PRIVATE_KEY*` values remain outside source control.

The template uses the official pinned dotenvx CLI directly rather than wrapping it in custom application code.

## Design basis

The root `AGENTS.md` explicitly applies these harness-engineering principles:

- humans steer and agents execute;
- repository-local knowledge is the system of record;
- the root instructions are a map with progressive disclosure;
- code, commands, tests, and state should be legible to agents;
- important invariants are enforced centrally while implementation remains flexible;
- feedback loops should be short and actionable;
- recurring failures improve the harness rather than expand ad hoc prompts;
- stale patterns and accidental complexity are removed continuously.

OpenSpec supplies the spec-driven workflow, running on the project-local lean schema (`openspec/schemas/lean`): a change is one proposal plus delta specs, with a definition of done instead of a task file. Codebase Memory supplies structural code intelligence. Dotenvx supplies tracked encrypted environment files. The YAGNI and human-maintainability guidance is kept to a few direct rules rather than adding Ponytail or another policy dependency.

The bootstrap protocol's interview mechanics follow grill-with-docs: one question at a time, a recommendation attached to every question, research before asking, and decisions written into the repository as they resolve. Its discovery posture follows vibe-check: find the problem under the stated idea, pressure-test whether it is worth solving, and split the smallest V1 from everything later.

Sources:

- https://openai.com/index/harness-engineering/
- https://github.com/Fission-AI/OpenSpec/
- https://github.com/DeusData/codebase-memory-mcp
- https://dotenvx.com/docs/env-keys-file
- https://github.com/dotenvx/dotenvx
- https://blog.scottlogic.com/2026/06/16/ponytail-yagni-and-the-problem-with-prompt-benchmarks.html
- https://unstack.io/write-code-like-a-human-will-maintain-it
- https://github.com/DietrichGebert/ponytail
- https://www.aihero.dev/grill-with-docs
- https://github.com/TexasBedouin/vibe-check
