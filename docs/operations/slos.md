# lake.live service objectives

**What.** The service-level indicators (SLIs) for the hosted lake, the objectives (SLOs) set on
them, the error budgets those objectives imply, and how each indicator is measured from what
lake and the operator already expose. Refs
https://github.com/oramasearch/liquid-bridge/issues/14.

**Why.** A hosted service needs stated objectives before it has customers: they decide what
pages someone, what waits for a working day, and when a rollout stops. The objectives below are
set for the deployment as it is (`Lake/prod`: one replica, one node, TLS at Cloudflare only) and
each names the condition under which it tightens. They are objectives, not promises to customers;
the customer-facing service level is a placeholder in
[`../legal/terms-of-service.draft.md`](../legal/terms-of-service.draft.md) until the owner sets it.

**Scope.** `Lake/prod` on `orama-production-cluster-01`, reached today at
https://lake.oramadev.net and, after [`lake-live-host.md`](lake-live-host.md), at `lake.live`.
Everything below reads `<host>` for either.

## Indicators

| SLI | Definition | Source of truth | Probe |
|---|---|---|---|
| **`/v1` availability** | Fraction of requests to `route=~"/v1/.*"` answered without a 5xx and without a connection failure. 4xx are not failures: `403 unauthorized`, `404 not_found`, `409 conflict`, `429` quota are correct answers. | `lake_http_requests_total{route=~"/v1/.*",status=~"5.."}` over `lake_http_requests_total{route=~"/v1/.*"}` (lake `docs/serving/telemetry.md`) | External `GET https://<host>/v1/server_info`: `200`, `ok:true`, `value.store == "postgres"`. `GET /readyz`: `200 {"ok":true,"store":"postgres"}`; `503` means the control store failed its `SELECT 1` ping. |
| **UI availability** | Same definition over the page routes (`/`, `/repositories`, `/repository`, `/sign-in`, `/audit`, …). | `lake_http_requests_total{route!~"/v1/.*",route!="unmatched"}` | External `GET https://<host>/` expecting `200` and `<title>lake` in the body; `GET /repositories` expecting `200` or a sign-in redirect. **Use GET, never HEAD**: HEAD falls through to the trailing 404 (observed 2026-09-05: `curl -I /` answers `404`). |
| **Push and pull latency** | Server-side request duration of the binary sync routes `/v1/repositories/:id/sync/{find-missing,push,pull,chunks}` and of `refs`, at p50 and p99 over 30 days. | `histogram_quantile(0.5|0.99, sum by (le) (rate(lake_http_request_duration_seconds_bucket{route=~"/v1/repositories/.*/sync/.*"}[5m])))`. Bytes moved come from metering (`transfer_in_bytes`, `transfer_out_bytes`, lake `docs/api/metering.md`) so a slow request that moved a gigabyte can be told from a slow request that moved nothing. | A synthetic `liquid` client pushing and pulling a fixed small repository (the CLI scenario liquid #119 runs as a test). **Does not exist yet**; see gaps. |
| **Time to first byte, pages** | Wall time from request to first response byte for `/`, `/repositories` and one public `/repository?id=…`, measured outside Azure, through Cloudflare. | External only. Server-side page render time is 0.02–0.08 ms (`duration_ms` in the request log, 2026-09-05), so TTFB is Cloudflare, the ingress and the network. | `curl -o /dev/null -w '%{time_starttransfer}'` once a minute from two vantages. Baseline 2026-09-05, Vancouver → Cloudflare YVR → eastus: 0.24–0.47 s on `/healthz`, `/readyz`, `/v1/server_info`, `/v1/identity`. |
| **Audit-log freshness** | Age of the newest `audit_events` row. Every registry capability outcome, including public reads and failures, appends one signed row (lake `docs/api/audit.md`), so under any traffic the newest row is recent. | `GET /v1/audit?limit=1` with a bearer → `items[0].occurred_at`; `lake_store_calls_total{result!="ok"}` rising is the leading indicator that appends fail. | A synthetic caller issuing one authenticated read a minute makes the indicator meaningful when there is no customer traffic. |
| **Audit-log integrity** | `GET /v1/verify_audit` returns `{verified:true}`: every signature, digest and predecessor link recomputes. | The capability itself. | Daily authenticated call; any `false` or error is an incident, not budget. |
| **Backup recency** | Age of the newest completed CNPG `Backup` of `lake-prod-controldb`, and whether the last restore rehearsal passed. | `kubectl get lake prod -o jsonpath='{.status.backupReady} {.status.lastBackupTime}'`; `kubectl get backups.postgresql.cnpg.io -n lake` (operator `docs/lake/backups.md`, PR https://github.com/oramasearch/orama-operator/pull/131). | The `BackupReady` condition on the `Lake`. **Red as of 2026-09-05:** `BackupReady=False`, `control-plane backups are disabled`; no `Backup` objects exist. |
| **Store volume headroom** | Free fraction of the PVC `lake-prod-store` (100 GiB, `managed-csi`, RWO) that holds every customer store and the transparency log. | `kubelet_volume_stats_available_bytes{persistentvolumeclaim="lake-prod-store"} / kubelet_volume_stats_capacity_bytes{…}`, scraped from the kubelet by the Azure Monitor managed Prometheus already on the cluster (`ama-metrics`). | Same metric; a write that hits `ENOSPC` also shows as `lake_store_calls_total{result!="ok"}` and `500`s on push. |
| **Edge certificate and DNS** | The host resolves to Cloudflare, is proxied, and the edge certificate is valid. | `kubectl get cloudflarednsrecords -n lake` `READY=true`; `openssl s_client -connect <host>:443 -servername <host>` `notAfter`. | Once a day from the external prober. |

## Objectives and error budgets

All objectives are over a rolling 30 days.

| SLI | Objective | Budget per 30 days | Tightens to | When |
|---|---|---|---|---|
| `/v1` availability | **99.5 %** | 3 h 36 min | 99.9 % (43 min) | ≥ 2 lake replicas (needs an RWX store class or a single-writer store design, operator `docs/lake/README.md` *Store volume*), a PodDisruptionBudget and liveness probe (operator #122), a second node in the pool, and one full month of external probe data at ≥ 99.9 %. |
| UI availability | **99.5 %** | 3 h 36 min | 99.9 % | Same conditions. |
| Push and pull latency | **p50 ≤ 0.5 s, p99 ≤ 5 s** per sync request; `refs` and `find-missing` **p99 ≤ 1 s**. Excludes `4xx` and `429` (quota) answers. | 1 % of requests may exceed p99 | p99 ≤ 2 s | After the synthetic client has run a month and the histogram buckets are widened (see gaps). |
| TTFB, pages | **p50 ≤ 0.5 s, p99 ≤ 2 s** external | 1 % of probes | p50 ≤ 0.3 s | After TLS terminates at the ingress with `Full (strict)` and static assets carry content hashes (lake #98). |
| Audit freshness | newest row **≤ 5 min** old while the synthetic caller runs | 3 h 36 min of staleness | — | — |
| Audit integrity | `verify_audit` **true on every daily run** | none: a failure is an incident | — | — |
| Backup recency | newest completed backup **≤ 26 h** old (daily `0 0 3 * * *` schedule plus slack); restore rehearsal **passes each quarter** on a copy | 1 missed day per 30 | ≤ 2 h (WAL archiving already ships continuously once Barman is on) | After `lake-prod-backups-r2` exists and `spec.postgres.backup.enabled: true`. |
| Store headroom | **≥ 20 % free**, or an expansion is in progress | — | — | — |
| Edge certificate | valid **≥ 14 days** ahead, host proxied | none | — | — |

**Budget policy.**

- Burn alerts: a *fast burn* (2 % of the monthly budget in one hour, i.e. about four minutes of
  full outage) pages the on-call; a *slow burn* (10 % in 24 hours) opens an `ops` issue.
- With more than half the monthly budget spent, image rolls to `Lake/prod` stop except fixes for
  the incident that spent it; the [`runbooks/roll-lake-image.md`](runbooks/roll-lake-image.md)
  preamble says to check this page first.
- With the budget exhausted, every further roll needs a written post-incident review
  ([`status-page.md`](status-page.md) template) merged before it goes out.
- The single-node cluster means a node reboot (AKS auto-upgrade, a VM host event) spends the
  whole `/v1` and UI budget at once. Until there is a second node, treat AKS maintenance windows
  as planned maintenance on the status page.

## What cannot be measured yet

Each of these is a gap between the objective and the evidence, not a reason to drop the objective.

1. **`/metrics` needs a credential.** `GET /metrics` accepts the admin bearer or a `lake_session`
   cookie (lake `docs/serving/telemetry.md`). The scraper on the cluster is Azure Monitor managed
   Prometheus (`ama-metrics` in `kube-system`; CRDs `podmonitors.azmonitoring.coreos.com`,
   `servicemonitors.azmonitoring.coreos.com`). A `PodMonitor` selecting
   `app.kubernetes.io/name=lake` with `authorization.credentials` from a Secret is the wiring; the
   Secret should hold a scoped API token created for the scraper rather than the admin bearer.
   Owner: operator #15 (observability) and #122 (hardening); the operator should render the
   `PodMonitor` from the `Lake`.
2. **No external prober exists.** The status page ([`status-page.md`](status-page.md)) is the
   prober; until it runs, availability is known only from server-side counters, which cannot see
   a dead pod, a broken ingress or a stale DNS record.
3. **Histogram buckets stop at 5 s** (0.001 … 5 s). A p99 above 5 s reads as "> 5 s" and nothing
   more. Widening the bucket array is a lake change in `src/telemetry/metrics.cpp`; both request
   and store histograms change together.
4. **No synthetic sync client.** Needs a lake issue: a Job or Worker that pushes and pulls a fixed
   repository with the `liquid` CLI and reports duration and bytes.
5. **Backups are off**, so backup recency is red by construction. Turning them on is an owner
   action: create `lake-prod-backups-r2` in `lake` and set `spec.postgres.backup` on the `Lake`
   (operator `docs/lake/backups.md`). The store volume and the `lake-prod-instance-kek` Secret
   have **no backup path at all**; see
   [`runbooks/disaster-recovery.md`](runbooks/disaster-recovery.md).
6. **One replica, one node.** The availability objectives are honest for that shape and will be
   missed by any node event. This is the reason they are 99.5 % and not 99.9 %.

## How to verify

```sh
H=https://lake.oramadev.net
curl -sS -o /dev/null -w 'server_info %{http_code} ttfb=%{time_starttransfer}\n' $H/v1/server_info
curl -sS -o /dev/null -w 'readyz      %{http_code}\n' $H/readyz
curl -sS -o /dev/null -w 'page /      %{http_code} ttfb=%{time_starttransfer}\n' $H/
kubectl get lake prod -o jsonpath='{.status.phase} backupReady={.status.backupReady} lastBackup={.status.lastBackupTime}{"\n"}'
kubectl get cloudflarednsrecords -n lake
# with the admin bearer (break-glass; prefer a scoped token):
# curl -sS -H "Authorization: Bearer $T" "$H/v1/audit?limit=1" | jq '.value.items[0].occurred_at'
# curl -sS -H "Authorization: Bearer $T" "$H/v1/verify_audit"
```

Server-side PromQL, once `/metrics` is scraped:

```promql
1 - sum(rate(lake_http_requests_total{route=~"/v1/.*",status=~"5.."}[30d])) / sum(rate(lake_http_requests_total{route=~"/v1/.*"}[30d]))
histogram_quantile(0.99, sum by (le) (rate(lake_http_request_duration_seconds_bucket{route=~"/v1/repositories/.*/sync/.*"}[5m])))
sum(rate(lake_store_calls_total{result!="ok"}[5m]))
```

## How to change

Change an objective here and the matching probe threshold in the status page configuration in
the same PR, with the date and the reason in the row. A new SLI needs its measurement source
named before its objective is set; an objective without a working measurement is listed under
*What cannot be measured yet*, not in the objectives table.
