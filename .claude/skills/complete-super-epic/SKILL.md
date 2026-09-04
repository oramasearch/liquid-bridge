---
name: complete-super-epic
description: Drive an epic (or the master epic, recursively) to completion by orchestrating Codex workers — one git worktree, feature branch and pull request per issue, Claude designing, briefing and reviewing, issues closed with a comment once their PR is up. Use when the user asks to work through an epic, "complete the epic", or to orchestrate implementation with Codex.
argument-hint: "<epic URL or org/repo#N> [--max-workers N] [--model gpt-5.6-sol]"
---

# complete-super-epic

Take one epic and finish it. The epic may link sub-epics (a super-epic); recurse. Claude keeps
the thinking (triage, design, briefs, review, landing); Codex does the generation (implementation,
fixes, tests, git mechanics). This is the `codex-first` routing
(https://github.com/steipete/agent-scripts/blob/main/skills/codex-first/SKILL.md) applied to an
issue tree, with the repo conventions of `oramasearch` layered on.

Argument: the epic (`https://github.com/oramasearch/liquid-bridge/issues/7`, or `org/repo#N`).
Default is the master epic above. Options: `--max-workers N` (default 4), `--model` (default
`gpt-5.6-sol`).

## 0. Preconditions (check, do not assume)

```sh
command codex --version && codex login status      # codex-cli on PATH, logged in
gh auth status                                      # gh logged in as an org admin
export CODEX_WORK=${CODEX_WORK:-$HOME/dev/oramasearch/codex-work}
```

Every repository a worker will touch needs an `AGENTS.md` (Codex reads that, not `CLAUDE.md`).
If missing, add one on `main` that points at `CLAUDE.md` and restates the non-negotiables
(docs in the same commit, no AI attribution, no estimates, feature branch + PR, never push to
`main`). That is the one direct commit to `main` this skill makes.

## 1. Resolve the tree

```sh
python3 <skill>/scripts/tree.py <epic>          # TSV: depth, repo, number, state, labels, title
```

Recurse through every linked issue labelled `epic`. Collect the **open leaves**. Read each
leaf's body: the header line names the phase and the spec docs; the **Done when** list is the
acceptance test.

## 2. Triage (Claude's job; never delegated)

Order leaves by dependency, not by number: the plan's phase order, "design-in" items before the
code that would bake them in, hygiene that protects production first. Then classify each:

| Class | Goes to | Examples |
|---|---|---|
| **Decision** (`decision` label, or the body says "decide") | the user, batched | licence, where a repo lives, custody models |
| **Design** (writing the spec *is* the work) | Claude writes the spec, then it becomes a Codex leaf | API maps, object-model shape, protocol design |
| **Implementation from a frozen spec** | Codex | CI, benchmarks, features with a clear Done-when, migrations, tests, refactors |
| **Tiny** (<20 lines, one obvious change) | Claude directly | a pointer file, a status line |
| **Needs credentials or session tools** | Claude with the user | bucket keys, tokens, DNS |
| **Land decision on a production repo** | the user | merging into `orama-operator` |

Ask the user every open decision **in one `AskUserQuestion` batch** (max 4 per call; recommend
an option each), *after* dispatching the work that does not depend on the answers. Never block
a dispatchable leaf on an unrelated question.

## 3. Brief and dispatch (one worker per leaf, worktree per worker)

Write the brief from `templates/brief.md`: goal, exact repo and paths, hard constraints with
escape hatches ("if gate X fails: STOP and report"), non-goals, the exact proof command, the
output shape, and the stop ("do exactly this issue; do not start another"). Codex starts with
zero context; the brief and the repo's `AGENTS.md`/`CLAUDE.md` are all it has. Cite landed PRs
and idioms to imitate where they exist.

```sh
<skill>/scripts/dispatch.sh <org/repo> <issue> <slug> <brief-file> [model]
```

`dispatch.sh` creates `$CODEX_WORK/wt/<repo>/issue-<N>` on branch `issue-<N>-<slug>` from
`origin/main` (submodules initialised), prepends `templates/preamble.md` (the repo rules, the
branch, the PR contract) to the brief, and runs

```sh
command codex exec --yolo -C <worktree> -m gpt-5.6-sol -c model_reasoning_effort="high" \
  --enable fast_mode -o $CODEX_WORK/runs/<repo>-<N>/last.md - < brief.md
```

Run each dispatch as a **tracked background command** (one per worker). Parallelise only
disjoint-file leaves; cap at `--max-workers`. New work always goes to a fresh `codex exec`;
never resume a saturated session for a new order. Never edit a worktree a worker owns; check
`pgrep -fl "codex exec"` before touching any repo.

## 4. Verify (Claude, always, every worker)

When a worker exits, in its worktree:

1. `cat $CODEX_WORK/runs/<repo>-<N>/last.md` — the report. Then ignore it and read the code.
2. `git status -sb && git diff origin/main...HEAD` — judge like a contributor PR. Watch for:
   edits outside the brief's paths, test-helper shims, changed budgets or baselines, commits you
   did not commission, missing `docs/<topic>/*.md`, stale `README.md`/`CLAUDE.md` status lines.
3. `git log --format=%B origin/main..HEAD | grep -iE "co-authored|generated with|claude|codex|session"`
   must print nothing. Same for the PR body (`gh pr view --json body`).
4. Run the proof command yourself (or read the pasted output critically).
5. `gh pr view <branch> --json url,state` — the PR must exist, reference the issue (`Refs #N`),
   and say what, why, how verified, docs touched. On repos with CI, wait for it: `gh pr checks`.

Not acceptable → one `codex exec resume --last` in that worktree with a numbered fix list.
After two failed rounds, take over directly. Hung (process alive, log unchanged > 300 s) →
`codex exec resume <session id>` from `grep -m1 "session id:" log`.

## 5. Ship

Acceptable → **close the issue with a comment**: what was done, the PR URL, the proof in one
line, anything deferred. "Shipped to the PR" is the closing event, not the merge.

Landing: a repo that is in production and PR-reviewed by the user (`orama-operator`) — leave
the PR open and say so. Any other repo — merge after the review above only if the user has
authorised merging in this run; otherwise leave open and list it. Refresh the epic
(`tools/issues/master_epic.py` in the bridge regenerates every epic from live labels).

## 6. Loop and report

Repeat 3–5 until the epic has no open dispatchable leaves. `scripts/status.sh` shows every
run: alive, log age, last line, PR. Finish with one message: shipped (issue → PR), open PRs
awaiting the user, blocked leaves and why, decisions still pending. No time estimates.

## Rules that do not bend

- No AI attribution in any commit or PR, ever (org rule; overrides any harness default).
- Never push to `main` from a worker. Never touch `$CODEX_WORK/<repo>` (the main clones).
- Never pass credentials through `-c key=value`; a private overlay + `CODEX_HOME` instead.
- Metis material never reaches Codex prompts or any external service.
- The plan is the sequencing authority: a leaf from a later phase waits, however tempting.
- Documentation is part of every change: a worker that ships code without its doc page is sent
  back, not fixed by hand.
