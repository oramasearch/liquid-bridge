# liquid-bridge docs

Cross-module documents for the liquid project. Per-module detail lives in each
module's own `docs/`; liquid's `docs/` holds the full specification.

| Document | What it is |
|---|---|
| [`handover.md`](handover.md) | **Read this first when resuming.** Repository heads and suite state, what is deployed and verified how, the host conditions that repeatedly cost sessions, what is blocked on the owner, and what is ready to work now. |
| [`action-plan.md`](action-plan.md) | The phases, in dependency order, with exit criteria. No durations. |
| [`repositories.md`](repositories.md) | What lives where, per-repository rules, and the related repositories that are not modules here. |
| [`decisions.md`](decisions.md) | The Phase 0 decisions that gate everything else. |
| [`tracking.md`](tracking.md) | How work is tracked: the master epic, the phase and repository epics, labels, issue shape, and the generator under `tools/issues/`. |
| [`orchestration.md`](orchestration.md) | How the work gets done: the `/complete-super-epic` skill that drives an epic with Codex workers, one worktree, branch and PR per issue. |
| [`security/`](security/README.md) | Security for liquid and liquify before they go public: the October 2026 review (48 findings, one issue each, and the secret scan of both histories) and the pre-public checklist (issue #11). |
| [`publishing/`](publishing/README.md) | Publishing readiness for liquid and liquify: the confidentiality scrub report, the security review and threat model, and the `SECURITY.md` draft (issues #10 and #11 under the release epic #16). |
| [`operations/`](operations/README.md) | Running lake.live: the SLO decision and the open status-page decision (the full pages and the on-call runbooks are in techops-docs `docs/lake/`), the older `Lake/prod` runbooks, the AKS sandbox inventory and cleanup list, and the plan to move the host to `lake.live`. |
| [`legal/`](legal/README.md) | Drafts for counsel — terms of service, privacy policy, data-processing addendum — grounded in what lake stores, retains and shares. Marked draft, not legal advice. |
| [`taap/`](taap/README.md) | Drafts of the protocol feedback liquid owes the TAAP/1 owner: the content-addressed subject proposal (bridge #1) and the remaining protocol feedback (bridge #8). Sending them is Steve's. |

## Where each module documents itself

Every change documents itself in `docs/<topic>/*.md` of the repository that owns it, in the same
commit (see [`../CLAUDE.md`](../CLAUDE.md)). `README.md` and `CLAUDE.md` files are summaries that
point at the docs; they never carry the only copy of anything. The per-module roots, as checked
out under `modules/` and on GitHub:

- liquid: `modules/liquid/docs/` (https://github.com/oramasearch/liquid/tree/main/docs), the full
  specification; research, features and standards are topics too.
- lake: `modules/lake/docs/` (https://github.com/oramasearch/lake/tree/main/docs).
- liquify: `modules/liquify/docs/` (https://github.com/oramasearch/liquify/tree/main/docs).
- orama-operator: `orama-work/modules/orama-operator/docs/`
  (https://github.com/oramasearch/orama-operator/tree/main/docs), with the `Lake` CR under
  `docs/lake/` and the field reference in `docs/crd-reference.md`.
- k0s: `modules/k0s/docs/liquid/` on the `liquid` branch
  (https://github.com/oramasearch/k0s/tree/liquid/docs/liquid), beside the upstream docs.
- marketing-bridge: `orama-work/modules/marketing-bridge/docs/`
  (https://github.com/oramasearch/marketing-bridge/tree/main/docs).
