# Lean schema fleet rollout

> Fleet-ops runbook for the template owner (`keyclaw6`). Hand this file to an
> agent with GitHub access to roll the lean OpenSpec schema across every owned
> repository. It is idempotent: running it twice changes nothing the second time.
>
> If you created a project from this template, this file is not for your
> project — delete it.

## Exclude list

The owner edits this list before each run. One repository name per line;
everything listed here is skipped without discussion.

```text
agent-first-project-template    # source of truth, already lean
```

Archived repositories and forks are always skipped, even if not listed.

## Mission

Every owned, non-excluded repository ends up with the lean OpenSpec schema
installed and selected, in one clean commit per repository, verified before
push. The lean schema makes a change two artifacts — one proposal (why, goals
and non-goals, what changes, optional design, definition of done) plus delta
specs — with no design.md or tasks.md files.

The canonical schema lives in this repository at `openspec/schemas/lean/`
(three files: `schema.yaml`, `templates/proposal.md`, `templates/spec.md`).
Always copy from this repository's `main`; never rewrite the schema by hand.

## Credentials

Use the **GITHUB PAT** skill. Its token is injected as `GITHUB_PAT` only
inside `RunWithCredentials(skillName: "GITHUB PAT", command: ...)` — it is not
present in bare shell. Call `FetchSkillScripts("GITHUB PAT")` first; it places
a helper at `skills/GITHUB PAT/git_with_pat.sh` that runs any git command with
ephemeral authentication (nothing persisted to `.git/config` or remotes):

```sh
sh "skills/GITHUB PAT/git_with_pat.sh" clone https://github.com/keyclaw6/REPO.git
sh "skills/GITHUB PAT/git_with_pat.sh" -C REPO push origin BRANCH
```

REST calls: `curl -H "Authorization: Bearer ${GITHUB_PAT}" https://api.github.com/...`

Never print, log, or interpolate the token into anything that persists.

## Procedure

1. **Enumerate.** `GET /user/repos?affiliation=owner&per_page=100` (paginate
   until empty). Drop archived repos, forks, and every name on the exclude
   list. Report the resulting worklist before touching anything.

2. **Fetch the canonical schema once.** Clone this repository and keep
   `openspec/schemas/lean/` as the source to copy from.

3. **Classify each repository** (read-only, via the contents API or a clone):
   - **Tier A — has `openspec/config.yaml`:** OpenSpec is already in use.
   - **Tier B — no OpenSpec, has `package.json`:** Node project without OpenSpec.
   - **Tier C — no OpenSpec, no `package.json`:** any other repository.
   - **Already lean** (`openspec/schemas/lean/schema.yaml` present and
     `config.yaml` says `schema: lean`): skip, report "already lean".

4. **Install per tier**, in a fresh clone of the repo's default branch:
   - **Tier A:** copy `openspec/schemas/lean/` in; set `openspec/config.yaml`
     to `schema: lean`. If `package.json` pins `@fission-ai/openspec` below
     `1.6.0`, raise the pin to `1.6.0` (schemas are experimental; that is the
     verified version). Do not touch existing specs or active changes —
     changes created under the old schema keep their own `.openspec.yaml`
     marker and remain valid; only new changes use lean.
   - **Tier B:** create `openspec/config.yaml` (`schema: lean`), copy the
     schema in, create `openspec/specs/.gitkeep` and
     `openspec/changes/.gitkeep`, and add `"@fission-ai/openspec": "1.6.0"`
     to `devDependencies`. Regenerate the lockfile only if one already exists.
   - **Tier C:** same as Tier B but leave `package.json` alone entirely; the
     CLI runs ad hoc via `npx -y @fission-ai/openspec@1.6.0 <command>`.

5. **Verify before pushing.** In the modified clone:

   ```sh
   npx -y @fission-ai/openspec@1.6.0 schema which lean     # must resolve: project
   npx -y @fission-ai/openspec@1.6.0 validate --all --strict
   ```

   Strict validation must pass (or report "No items found"). If it fails
   because of pre-existing content, do not push — skip the repo and report the
   failure verbatim instead. Never force a repo green by editing its specs;
   that is the owner's call.

6. **One commit per repository**, message:
   `Adopt lean OpenSpec schema (proposal + delta specs, definition of done instead of tasks)`
   — push to the default branch. If the push is rejected (branch protection),
   push a branch `adopt-lean-openspec` and open a PR instead; report the link.

## Rules

- Touch only the files named in step 4. No refactors, no formatting fixes, no
  opportunistic cleanup in other people's history.
- Idempotent: a repo that is already correct receives zero commits.
- Anything surprising — unexpected layout, failing validation, permission
  errors — means skip and report, never improvise.
- Read-only exploration first; the first write to any repo is its single commit.

## Report

Finish with one table:

| repo | tier | action | verification | commit / PR |
|---|---|---|---|---|

Actions: `flipped to lean` / `installed` / `already lean` / `excluded` /
`skipped: <reason>`. Every row gets a verification result. Nothing is
considered done without a commit SHA or PR link in the last column.
