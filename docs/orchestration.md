# How the work gets done: orchestrating Codex

**What exists.** The `/complete-super-epic` skill at
[`.claude/skills/complete-super-epic/`](../.claude/skills/complete-super-epic/) (symlinked into
`~/.claude/skills/` so every session has it) drives an epic to completion: Claude triages,
designs, writes the briefs and reviews; Codex (`codex exec`, model `gpt-5.6-sol`, reasoning
`high`, `fast_mode`) implements each leaf issue in its own git worktree and feature branch and
opens a pull request. The issue is closed, with a comment saying what was done, when its PR is
up. Its parts:

| Path | Role |
|---|---|
| `SKILL.md` | the procedure: preconditions, resolve the tree, triage, brief, dispatch, verify, ship, loop |
| `scripts/dispatch.sh <org/repo> <issue> <slug> <brief>` | worktree `wt/<repo>/issue-N` on branch `issue-N-<slug>` from `origin/main`; preamble + brief → `codex exec --yolo`; log and report under `runs/<repo>-N/` |
| `scripts/status.sh` | one line per run: alive, log age, PR, last log line |
| `scripts/tree.py <epic>` | the epic's tree as TSV, recursing through sub-epics |
| `templates/preamble.md` | the rules every worker gets: the branch, no attribution, docs in the same commit, the PR contract, STOP on a failed gate |
| `templates/brief.md` | the shape of a work order: goal, where, hard gates, non-goals, proof, output |

The work root is `$CODEX_WORK` (default `~/dev/oramasearch/codex-work`): `<repo>/` are the
main clones, never edited; `wt/<repo>/issue-N/` the worktrees; `runs/<repo>-N/` the brief, log
and final report; `briefs/` the per-issue briefs Claude wrote. Each repository carries an
`AGENTS.md` that points Codex at `CLAUDE.md`, because Codex reads the former and not the latter.

**Why.** The `codex-first` routing
(https://github.com/steipete/agent-scripts/blob/main/skills/codex-first/SKILL.md): Claude tokens
are metered, Codex is flat-rate, so generation and exploration go to Codex and Claude spends on
the spec and the diff review. One worktree per issue makes parallel workers safe; one PR per
issue keeps review and history legible; closing on PR keeps the epics honest about what has
been built versus what has been merged.

**How to verify.** `scripts/status.sh`. Every PR body carries `Refs #N`, a *How verified*
section with the proof output, and a *Docs* section. `git log --format=%B origin/main..HEAD |
grep -iE "co-authored|generated with|claude|codex"` prints nothing on any worker branch.

**How to change.** Edit the skill; the templates carry the repo rules, the scripts carry the
mechanics. A new repository needs its `AGENTS.md` before its first worker. The model and the
work root are environment (`CODEX_MODEL`, `CODEX_WORK`).

**Landing.** `orama-operator` is in production and PR-reviewed by Steve: its PRs stay open.
Other repositories: merged by Claude after the review in step 4 of the skill, only when Steve
has authorised merging for the run.
