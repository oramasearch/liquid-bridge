# Work order — {{ORG_REPO}} issue #{{ISSUE}}

You are working in the git worktree `{{WT}}` on branch `{{BRANCH}}`, branched from `origin/{{BASE}}`
of https://github.com/{{ORG_REPO}}. Read `AGENTS.md`, `CLAUDE.md`, `README.md` and
`docs/README.md` in this directory before doing anything; they apply in full and override this
preamble where they are more specific. If one of them does not exist, say so in your report and
continue; a missing file to read is never a gate.

Rules for this work order:

1. Stay on `{{BRANCH}}`. Never push to `main` or to `{{BASE}}`. Never modify anything outside this worktree.
2. Commit in small, logical commits with messages about the change. **No AI attribution of any
   kind**: no `Co-Authored-By`, no "Generated with", no model, tool or session trailers, in
   commits or the pull request.
3. Every change documents itself in `docs/<topic>/*.md` in the same commit, and `README.md` /
   `CLAUDE.md` status lines are updated when they stop being true. Code without its doc page is
   not done.
4. No time estimates anywhere. The word "seam" is banned.
   Code is written for a reviewer: one statement per line, functions of ordinary length, formatted with
   the repository's formatter (`.clang-format`, `gofmt`, `rustfmt`, as the repo uses) before every
   commit. A function collapsed onto one line is sent back unread.
5. When the work is complete and the proof below passes: first `git fetch origin && git rebase
   origin/{{BASE}}` (other workers land in parallel; resolve status lines and index rows by keeping
   both sides; then `git submodule update --init --recursive`, and if `.gitmodules` or any submodule
   pointer changed, delete the build directories and configure again before re-running the proof;
   re-run the proof if anything but docs changed), then `git push -u origin {{BRANCH}}`, then
   open the pull request with `gh pr create --repo {{ORG_REPO}} --base {{BASE}} --head {{BRANCH}}`
   using a title that names the change and a body with these sections: **What**, **Why**
   (one paragraph, cite `Refs #{{ISSUE}}`), **How verified** (paste the proof output), **Docs**
   (the pages added or changed), **Deferred** (anything from the issue you did not do, and why).
   Do not merge the PR. Do not close the issue. Do not comment on the issue.
6. If a hard gate in the brief fails, or you would need a decision that is not in the brief:
   STOP, do not improvise, and put the diagnosis in your final report.
7. Final report (this is what is read first): files changed, the proof command and its output,
   the PR URL, what was deferred, open questions. Then stop. Do exactly this issue; do not start
   any other.

The issue itself: https://github.com/{{ORG_REPO}}/issues/{{ISSUE}} — read it with
`gh issue view {{ISSUE}} --repo {{ORG_REPO}}`; its **Done when** list is the acceptance test.
