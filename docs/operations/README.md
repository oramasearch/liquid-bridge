# lake.live operations

How the hosted lake is run: the objectives it is held to, where its status is read, what the
on-call does when something breaks, what the sandbox cluster holds, and how the host moves to
`lake.live`. Cross-module by nature — the service is lake's binary, deployed by the operator, on
the AKS cluster — so it lives in the bridge. Per-component detail stays in the owning repository:
lake `docs/deployment/aks.md`, `docs/serving/telemetry.md`; operator `docs/lake/README.md`,
`docs/lake/backups.md`.

| Document | What it is | Issue |
|---|---|---|
| [`slos.md`](slos.md) | The SLO decision for `lake.live` (proposed 2026-10-21): per region, 99.5 % availability of the API and web app, latency thresholds, budget policy. The full objectives live in techops-docs `docs/lake/slos.md` | #14 |
| [`status-page.md`](status-page.md) | The open status-page decision for Steve (where it runs, the host, who posts, the paging channel). The full page lives in techops-docs `docs/lake/status-page.md` | #14 |
| [`runbooks/`](runbooks/README.md) | Links to the production runbooks in techops-docs `docs/lake/runbooks/` (pod restarts, schema Job, DNS, Cloudflare), and the older `Lake/prod` runbooks still here | #14 |
| [`aks-housekeeping.md`](aks-housekeeping.md) | Read-only inventory of `orama-production-cluster-01` on 2026-09-05, Phase 0.5 leftovers versus in use, findings, and the cleanup list for the owner's approval | #6 |
| [`lake-live-host.md`](lake-live-host.md) | Moving `Lake/prod` from `lake.oramadev.net` to `lake.live`: zone token scope, Secret, certificate path, the CR change, redirects, what breaks and in which order; the passkey RP ID and OIDC issuer as one-way doors | #5 |

Legal documents for the service are in [`../legal/`](../legal/README.md).

**Conventions.** Every page says what exists, why, how to verify it and how to change it. No
durations are estimated anywhere; objectives and retention periods are stated as facts about the
system. Commands are read-only unless a runbook step says otherwise, and cluster mutations go
through the `Lake` CR, not the objects it owns.
