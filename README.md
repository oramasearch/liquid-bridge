# liquid-bridge

The coordination repository for the liquid project. It pulls the project's repositories
together as git submodules so one session, human or agent, can work across all of them with
full cross-reference, and it holds what belongs to no single module: the plan, the decisions,
the repository map, the orchestration skill, and the operations, publishing and legal docs.

liquid is the tool. lake is where it collects (`lake.live`). liquify is the IDE. A drip is one
captured, signed write, the atom of history. The full specification is `modules/liquid/docs/`.

No application code, no build, no runtime here. Code lives in the modules.

## How to use it

- The plan is [`docs/action-plan.md`](docs/action-plan.md): the phases in dependency order,
  each with exit criteria. It is the sequencing authority; a change that belongs to a later
  phase waits.
- Decisions are recorded in [`docs/decisions.md`](docs/decisions.md). Phase 0 is decided, and
  nothing drifts past those entries without a new one.
- The repository map is [`docs/repositories.md`](docs/repositories.md): what lives where, the
  rules that differ per repository, and the related repositories that are not modules here.
- Progress is tracked as GitHub issues under one master epic,
  https://github.com/oramasearch/liquid-bridge/issues/7, which links every phase and repository
  epic across the repos. Start there. The shape, the labels and the generator under
  [`tools/issues/`](tools/issues/) are in [`docs/tracking.md`](docs/tracking.md).
- Work gets done through the `/complete-super-epic` skill in
  [`.claude/skills/`](.claude/skills/complete-super-epic/): Codex implements each leaf issue in
  its own worktree and branch and opens a PR; Claude triages, briefs and reviews. How it runs
  is in [`docs/orchestration.md`](docs/orchestration.md).
- Running the hosted service is [`docs/operations/`](docs/operations/README.md): SLOs, the
  status page, on-call runbooks, the AKS inventory, and the move to `lake.live`. Publishing
  readiness for the open-source release is [`docs/publishing/`](docs/publishing/README.md).
  Drafts for counsel are [`docs/legal/`](docs/legal/README.md).
- [`docs/README.md`](docs/README.md) indexes every cross-module page and says where each
  module documents itself.

## Clone

```sh
git clone --recurse-submodules git@github.com:oramasearch/liquid-bridge.git
```

Every module is private; you need SSH access to the `oramasearch` org.

## Modules

| Module | One line |
|---|---|
| [`modules/liquid`](modules/liquid/) | The tool, and the specification for everything. Start with its `docs/research/99-synthesis/`. |
| [`modules/k0s`](modules/k0s/) | Private, upstream-synced copy of k0s; Orama's changes are on the `liquid` branch. |
| [`modules/lake`](modules/lake/) | The lake binary, the hosted service; live on AKS as `Lake/prod`. |
| [`modules/liquify`](modules/liquify/) | The IDE: native, cross-platform, links libliquid. |
| [`modules/lake-sqlite`](modules/lake-sqlite/) | The web service behind lake's SQLite service kind: one SQLite database over HTTP, run by the Orama operator. Private, own private image. |

**Not modules here — one level up.** The **Orama operator** (lake runs on it as a `Lake` CR) and
**marketing-bridge** are shared across products, so they are pinned once by the org umbrella
[`oramasearch/orama-bridge`](https://github.com/oramasearch/orama-bridge) rather than vendored
again here. Read them at `orama-work/modules/orama-operator` and
`orama-work/modules/marketing-bridge`; standalone clones go stale. See
[`docs/repositories.md`](docs/repositories.md).

Language, status, and the rules for each are in [`docs/repositories.md`](docs/repositories.md).

## Rules

- Org-wide conventions live in [`oramasearch/orama-bridge`](https://github.com/oramasearch/orama-bridge)
  `CLAUDE.md` and are authoritative. Project conventions are in `modules/liquid/CLAUDE.md`.
  What is specific to working across the modules is in [`CLAUDE.md`](CLAUDE.md). Read a
  module's own `CLAUDE.md` before working inside it.
- Every change documents itself in `docs/<topic>/*.md` of the repository that owns it, in the
  same commit. `README.md` and `CLAUDE.md` are summaries and never hold the only copy of
  anything.
- Submodule pointers are commits: push the module first, then bump the pointer here.
- No AI attribution anywhere. Every repository here is private and stays private.
