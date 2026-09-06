# lake.live operations

How the hosted lake is run: the objectives it is held to, where its status is read, what the
on-call does when something breaks, what the sandbox cluster holds, and how the host moves to
`lake.live`. Cross-module by nature — the service is lake's binary, deployed by the operator, on
the AKS cluster — so it lives in the bridge. Per-component detail stays in the owning repository:
lake `docs/deployment/aks.md`, `docs/serving/telemetry.md`; operator `docs/lake/README.md`,
`docs/lake/backups.md`.

| Document | What it is | Issue |
|---|---|---|
| [`slos.md`](slos.md) | SLIs and SLOs for `/v1`, the UI, push and pull latency, page TTFB, audit-log freshness and integrity, backup recency, store headroom; error budgets and the burn policy; how each is measured from what lake and the operator expose; what cannot be measured yet | #14 |
| [`status-page.md`](status-page.md) | What the status page shows, where it runs (Cloudflare Pages fed by a Worker probe, outside lake's failure domain), the probe table, incident and review templates | #14 |
| [`runbooks/`](runbooks/README.md) | One runbook per failure seen or foreseen: crash loop on a variable, store volume, control database, schema Job or drift, Cloudflare stale asset, operator rollout and CRDs, rolling lake, rollback, certificate or DNS, disaster recovery. Who to page. | #14 |
| [`aks-housekeeping.md`](aks-housekeeping.md) | Read-only inventory of `orama-production-cluster-01` on 2026-09-05, Phase 0.5 leftovers versus in use, findings, and the cleanup list for the owner's approval | #6 |
| [`lake-live-host.md`](lake-live-host.md) | Moving `Lake/prod` from `lake.oramadev.net` to `lake.live`: zone token scope, Secret, certificate path, the CR change, redirects, what breaks and in which order; the passkey RP ID and OIDC issuer as one-way doors | #5 |

Legal documents for the service are in [`../legal/`](../legal/README.md).

**Conventions.** Every page says what exists, why, how to verify it and how to change it. No
durations are estimated anywhere; objectives and retention periods are stated as facts about the
system. Commands are read-only unless a runbook step says otherwise, and cluster mutations go
through the `Lake` CR, not the objects it owns.
