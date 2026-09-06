# liquid-bridge docs

Cross-module documents for the liquid project. Per-module detail lives in each
module's own `docs/`; liquid's `docs/` holds the full specification.

| Document | What it is |
|---|---|
| [`action-plan.md`](action-plan.md) | The phases, in dependency order, with exit criteria. No durations. |
| [`repositories.md`](repositories.md) | What lives where, per-repository rules, and the related repositories that are not modules here. |
| [`decisions.md`](decisions.md) | The Phase 0 decisions that gate everything else. |
| [`tracking.md`](tracking.md) | How work is tracked: the master epic, the phase and repository epics, labels, issue shape, and the generator under `tools/issues/`. |
| [`orchestration.md`](orchestration.md) | How the work gets done: the `/complete-super-epic` skill that drives an epic with Codex workers, one worktree, branch and PR per issue. |
| [`operations/`](operations/README.md) | Running lake.live: SLOs and error budgets, the status page, on-call runbooks, the AKS sandbox inventory and cleanup list, and the plan to move the host to `lake.live`. |
| [`legal/`](legal/README.md) | Drafts for counsel — terms of service, privacy policy, data-processing addendum — grounded in what lake stores, retains and shares. Marked draft, not legal advice. |
| [`taap/`](taap/README.md) | Drafts of the protocol feedback liquid owes the TAAP/1 owner: the content-addressed subject proposal (bridge #1) and the remaining protocol feedback (bridge #8). Sending them is Steve's. |
