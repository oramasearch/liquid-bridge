# Runbooks for lake.live

**The on-call runbooks for production (`lake-prod`: `eu.lake.live`, `us.lake.live`, `lake.live`)
are in techops-docs**, which describes how production is run:
[`docs/lake/runbooks/`](https://github.com/oramasearch/techops-docs/blob/main/docs/lake/runbooks/README.md)
(pull request https://github.com/oramasearch/techops-docs/pull/61, for
https://github.com/oramasearch/liquid-bridge/issues/14).

| techops-docs runbook | Failure | Replaces (removed from here 2026-10-21) |
|---|---|---|
| [`lake-pod-restarts.md`](https://github.com/oramasearch/techops-docs/blob/main/docs/lake/runbooks/lake-pod-restarts.md) | restarts and crash loops: lake#772's blocked server, the store-root hand-off, variables, the store volume | `pod-crash-loop-missing-variable.md` |
| [`schema-job-failure.md`](https://github.com/oramasearch/techops-docs/blob/main/docs/lake/runbooks/schema-job-failure.md) | the `PostgresSchema` Job fails or drifts; the schema gate holds the image | `schema-job-failure-or-drift.md` |
| [`dns.md`](https://github.com/oramasearch/techops-docs/blob/main/docs/lake/runbooks/dns.md) | a host does not resolve or resolves wrong; `CloudflareDNSRecord` ownership | `certificate-or-dns-failure.md` (DNS half) |
| [`cloudflare-edge.md`](https://github.com/oramasearch/techops-docs/blob/main/docs/lake/runbooks/cloudflare-edge.md) | Cloudflare 52x, origin TLS, authenticated origin pulls, stale assets | `certificate-or-dns-failure.md` (certificate half), `cloudflare-stale-asset.md` |

## Older runbooks still here

These were written on 2026-09-05 for the single `Lake/prod` on the managing cluster
(`orama-production-cluster-01`, namespace `lake`), which is temporary (orama-operator#536). They
predate the rule that no cluster is changed by hand (orama bridge `CLAUDE.md`, 2026-10-13): where
they say `kubectl apply -f <cr.json>`, `kubectl delete`, `rollout restart` or a dashboard change,
read it as a step that needs Steve's explicit consent, and prefer the committed-file path in the
techops-docs runbooks. Rolling lake and the operator is the `lake-devops` skill's.

| Runbook | Failure |
|---|---|
| [`store-volume-permission-or-capacity.md`](store-volume-permission-or-capacity.md) | the store volume is not writable, cannot be provisioned, or is full (production cases are in techops-docs `lake-pod-restarts.md`, case D) |
| [`control-database-unreachable-or-full.md`](control-database-unreachable-or-full.md) | `/readyz` 503, CNPG cluster unhealthy or full |
| [`operator-rollout-and-crd-update.md`](operator-rollout-and-crd-update.md) | rolling the operator; CRDs; RBAC |
| [`roll-lake-image.md`](roll-lake-image.md) | shipping a new lake image to `Lake/prod` |
| [`rollback.md`](rollback.md) | undoing a lake image roll or an operator upgrade |
| [`disaster-recovery.md`](disaster-recovery.md) | restoring the control plane, and what has no backup |

Moving these into techops-docs, rewritten for `lake-prod`, is the follow-up named on
https://github.com/oramasearch/liquid-bridge/issues/14.
