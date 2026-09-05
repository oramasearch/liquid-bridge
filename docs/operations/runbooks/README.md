# Runbooks for lake.live

One page per failure the deployment has shown or can be foreseen. Every runbook has the same
five parts: **Symptoms**, **Diagnosis**, **Fix**, **Verification**, **Who to page**. Commands
assume `kubectl` is pointed at `orama-production-cluster-01` and the `Lake` is `prod` in
namespace `lake`. Refs https://github.com/oramasearch/liquid-bridge/issues/14.

| Runbook | Failure | Seen |
|---|---|---|
| [`pod-crash-loop-missing-variable.md`](pod-crash-loop-missing-variable.md) | lake exits at start because a variable is missing or wrong (`LAKE_LOG_MODE` defaulting to `witnessed`, no `LAKE_INSTANCE_KEK`, anchored mode without an aggregator) | 2026-09-05 deploy (log mode) |
| [`store-volume-permission-or-capacity.md`](store-volume-permission-or-capacity.md) | the store volume is not writable by lake, cannot be provisioned (RWX on Azure disk), or is full | 2026-09-05 (permission, RWX) |
| [`control-database-unreachable-or-full.md`](control-database-unreachable-or-full.md) | `/readyz` 503, `store_unavailable`, CNPG cluster unhealthy or its 50 Gi volume full | foreseen |
| [`schema-job-failure-or-drift.md`](schema-job-failure-or-drift.md) | the `PostgresSchema` Job fails, or its recorded version differs from what the database holds | 2026-09-05 (drift) |
| [`cloudflare-stale-asset.md`](cloudflare-stale-asset.md) | pages render with an old stylesheet because Cloudflare cached `/style.css` | 2026-09-05 |
| [`operator-rollout-and-crd-update.md`](operator-rollout-and-crd-update.md) | rolling the operator; helm does not update CRDs; RBAC gaps crash the manager | 2026-09-02, 2026-09-05 |
| [`roll-lake-image.md`](roll-lake-image.md) | shipping a new lake image to `Lake/prod` | routine |
| [`rollback.md`](rollback.md) | undoing a lake image roll or an operator upgrade | 2026-09-02 (operator) |
| [`certificate-or-dns-failure.md`](certificate-or-dns-failure.md) | host does not resolve, is not proxied, edge certificate wrong, origin unreachable | foreseen |
| [`disaster-recovery.md`](disaster-recovery.md) | restoring the control plane from R2, and what has no backup (store volume, instance KEK) | foreseen |

## Who to page

Roles, not people; the current holder of each role is kept out of git and in the paging tool.

| Role | Pages for | Today |
|---|---|---|
| **lake on-call** | every runbook's first line | Steve (cluster owner) |
| **operator maintainer** | operator rollouts, CRD and RBAC failures, `PostgresSchema` behaviour, `CloudflareDNSRecord` behaviour | the `orama-operator` PR reviewer; operator PRs are Steve's to merge (decisions.md §7) |
| **Cloudflare account owner** | zone settings, tokens, purge, redirects, SSL mode | Steve |
| **Azure subscription owner** | node pool changes, disk snapshots and restores, quota | Steve |
| **lake maintainer** | a lake bug found by a runbook (a new failure mode gets a lake issue and a runbook in the same PR) | lake `CLAUDE.md` owners |

Paging channel: the webhook the status-page prober posts to ([`../status-page.md`](../status-page.md)).
Until that exists, the on-call reads `kubectl get lake prod -w` and the external probes by hand.

## Conventions shared by every runbook

- **Change the `Lake` CR, not what it owns.** The operator reconciles the Deployment, Service,
  Ingress, ConfigMap, Secrets, PVC, `PostgresSchema` and DNS record from the CR; a `kubectl
  edit deploy` or `kubectl set env` is undone on the next reconcile. Apply a full CR manifest
  with `kubectl apply -f <cr.json>`.
- **Never read Secret values you do not need.** `kubectl get secret <name> -o
  jsonpath='{.data}' | jq 'keys'` shows what keys exist without values. The admin bearer is
  break-glass (lake `docs/api/auth.md`); prefer a scoped token for probes.
- **Immutable image tags only.** A mutable tag with `IfNotPresent` served a stale image on this
  cluster before (operator `docs/install.md`).
- **Build C++ images on the node**, never emulated: the `aks-amd64` buildx builder in the
  `buildkit` namespace ([`roll-lake-image.md`](roll-lake-image.md)).
- **Write down what you did** in the incident file ([`../status-page.md`](../status-page.md))
  and, if the runbook was wrong or incomplete, fix the runbook in the same PR as the review.
