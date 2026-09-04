# How work is tracked

Everything is a GitHub issue in the repository that owns the work, and every issue hangs off an
epic. **One master epic links every epic:**
https://github.com/oramasearch/liquid-bridge/issues/7. Start there.

## The shape

```
master epic — liquid-bridge #7
├── phase epics (one per phase of the action plan, in the repo that owns the phase)
│     Phase 1  The store                        liquid #33
│     Phase 2  The build core                   liquid #34
│     Phase 3  Distribution                     liquid #35
│     Phase 4  The incremental engine, liquify  liquid #36
│     Phase 5  Resolution and projection        liquid #37
│     Phase 6  lake                             lake #11
│     Phase 7  The runtime                      k0s #18
│     Phase 8  Multiplayer, hot update, agents  liquid #38
├── repository epics (cross-phase work that one repo owns)
│     The Lake CR                               orama-operator #130
│     liquify — the IDE                         liquify #13
│     Open-source release of liquid + liquify   liquid-bridge #16
│     lake.live — the hosted service            liquid-bridge #17
│     What liquid needs from automerge-cpp       automerge-cpp #13
└── leaf issues, under one or more of the above
```

Phase 0 (decide) has no epic: its open decisions are listed on the master. Phase 0.5 (hello
world) is met; its k0s half is k0s #13.

A phase epic lists every leaf carrying its phase label in its own repo, plus `On <repo>:`
sections for leaves in other repos that belong to the phase (liquify's Phase 4 work sits under
liquid #36; the operator's Lake work sits under lake #11). A leaf may appear in more than one
epic; it lives in exactly one repository.

## Labels

| Repo | Labels used |
|---|---|
| `liquid` | `phase-1` … `phase-8`, `epic`, `decision`, `documentation` |
| `lake` | `phase-6`, `ops`, `epic`, `decision` |
| `liquify` | `phase-4`, `phase-5`, `phase-8`, `ops`, `epic`, `decision` |
| `k0s` | `phase-7`, `ops`, `epic`, `decision` |
| `orama-operator` | `lake` on everything for the `Lake` CR, plus its own `p1`–`p4`, `gap`, `e2e`, `epic` |
| `liquid-bridge` | `decision`, `ops`, `epic`, `phase-0`, `phase-8` |

`decision` issues surface in the master's *Decisions still open*; `ops` issues in its
*Operations and follow-ups*. Both lists are regenerated, not hand-edited.

## What an issue looks like

- **Leaf:** a header line (phase · plan · the feature docs it comes from · the research it
  rests on), one paragraph in the specification's own terms, and a **Done when** checklist that
  is checkable, not felt.
- **Epic:** the same header with the master link, the phase's exit criterion from the plan, and
  `## Issues` as a list of full URLs (GitHub renders the title and state of each).

Titles are specific and concrete: the subsystem, the command, the protocol, the guarantee. No
marketing.

## Where the issues came from

The first pass (2026-09-02, `tools/issues/create_issues.py`) turned the action plan's bullets into
one leaf each and one epic per phase. The second pass (2026-09-03,
`tools/issues/master_epic.py`) audited all 25 feature documents in
`modules/liquid/docs/features/` against the open issues and opened a leaf for every deliverable
the specification names that no issue covered — 108 of them — then added the four repository
epics and rewrote #7 as the master. Both scripts are idempotent: an existing issue with the same
title in the same repo is reused, and every epic body is regenerated from live labels.

Repeat the audit whenever the specification changes: a feature document that names a deliverable
with no issue is the drift to catch.

## How to add work

1. Open the leaf in the repository that owns it, with its phase label (or `ops` / `decision`),
   in the shape above. Link the feature doc it comes from.
2. Add it to the phase epic's list — by hand, or by adding it to `master_epic.py` and re-running
   (`python3 tools/issues/master_epic.py`, needs `gh` logged in as an org admin), which
   regenerates every epic and the master.
3. Close a leaf with a comment naming the commit that delivered it. Epic checkboxes reflect the
   leaf's state on the next regeneration.

## How the work gets done

See [`orchestration.md`](orchestration.md): the `/complete-super-epic` skill takes an epic and
works its leaves with Codex, one worktree, branch and PR per issue, closing each issue with a
comment when its PR is up.

## How to verify

`gh issue list --repo oramasearch/<repo> --label epic` shows the epics per repo; every one of
them links the master in its header line, and the master links every one of them.
