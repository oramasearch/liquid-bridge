# Control database unreachable or full

The control plane is the CloudNativePG cluster `lake-prod-controldb` (1 instance, 50 Gi,
Postgres 18) in `lake`; lake reaches it through `LAKE_CONTROL_DB_URI`
(`postgresql://lake:…@lake-prod-controldb-rw.lake:5432/lake`), one connection reused, one
transaction per call (lake `docs/control-plane/postgres.md`). Every capability, sign-in and audit
append touches it, so when it is gone, lake is a static hello page.

## Symptoms

- `GET /readyz` → `503 {"ok":false,"error":{"code":"store_unavailable",…}}`; `/healthz` still
  `200` (the process is alive). Kubernetes does not restart the pod for this — readiness only
  removes it from the Service, so the site answers `503` from the ingress.
- Every `/v1` call → `503 store_unavailable`; pages redirect to sign-in or render an error.
- `lake_store_calls_total{result="store_unavailable"}` rising; `lake_up` still 1.
- `kubectl get lake prod` → `DB 0/1` or `PHASE Degraded`.
- Full disk: Postgres logs `could not extend file … No space left on device`; writes fail while
  reads work — sign-in fails (it appends an audit row), public repository reads may still work.

## Diagnosis

```sh
kubectl get clusters.postgresql.cnpg.io -n lake                         # STATUS "Cluster in healthy state", READY 1
kubectl describe cluster lake-prod-controldb -n lake | sed -n '/Status/,/Events/p'
kubectl get pods -n lake -l cnpg.io/cluster=lake-prod-controldb -o wide
kubectl logs -n lake lake-prod-controldb-1 -c postgres --tail=50
kubectl get pvc -n lake lake-prod-controldb-1                          # Bound, 50Gi
kubectl exec -n lake lake-prod-controldb-1 -c postgres -- df -h /var/lib/postgresql/data
kubectl get svc -n lake lake-prod-controldb-rw                         # the endpoint lake uses
kubectl get endpoints -n lake lake-prod-controldb-rw                   # must list the primary pod
kubectl logs -n lake deploy/lake-prod --since=10m | grep -c store_unavailable
kubectl get pods -n cnpg-system                                        # the CNPG operator itself
```

Distinguish:

| Finding | Meaning |
|---|---|
| Cluster healthy, endpoints present, lake still `store_unavailable` | lake's connection is stale or the password rotated: the `lake-prod-controldb-app` Secret changed and the pod has the old value → roll the lake pod |
| Postgres pod `Pending` or `CrashLoopBackOff` | node pressure (84 % CPU requests on the one node — [`../aks-housekeeping.md`](../aks-housekeeping.md)) or a corrupt data directory |
| `df` at 100 % | full; go to *Fix: full* |
| CNPG operator pod down | the Cluster is not being managed; failover/restart will not happen |
| Node `NotReady` | everything is down; the single-node cluster has no other place to run |

## Fix

**Unreachable, cluster healthy.** `kubectl rollout restart deploy/lake-prod -n lake` re-reads the
Secret and reconnects. (This is an exception to "change the CR": a restart changes nothing the
operator owns.)

**Postgres pod down.** Let CNPG restart it; if it does not, `kubectl delete pod
lake-prod-controldb-1 -n lake` and CNPG recreates it on the same PVC. If the pod cannot schedule,
free requests (remove the idle builder, housekeeping item 4) rather than lowering Postgres
resources.

**Full.** `spec.postgres.storageSize` is a creation-time value in the CR, but CNPG grows the PVC in
place when the class allows expansion (`default` = Azure disk, allowed): set the larger size on the
CNPG `Cluster` through the Lake CR (`spec.postgres.storageSize: 100Gi`, `kubectl apply -f` the
CR) and confirm CNPG picks it up; if the operator does not pass the change through, patch the
Cluster's `spec.storage.size` directly and open an operator issue. Then find what filled it:

```sh
kubectl exec -n lake lake-prod-controldb-1 -c postgres -- psql -U postgres -d lake -c \
  "SELECT relname, pg_size_pretty(pg_total_relation_size(oid)) FROM pg_class WHERE relkind='r' ORDER BY pg_total_relation_size(oid) DESC LIMIT 10"
```

`audit_events` is append-only and never pruned (400-day floor, lake `docs/api/audit.md`); its
growth is a function of request volume, which is the input to capacity planning, not a thing to
delete. Never `DELETE` from it; the trigger refuses, and deletion would break the signature
chain.

**Corruption or lost volume.** Stop; this is [`disaster-recovery.md`](disaster-recovery.md).

## Verification

```sh
curl -sS https://<host>/readyz                                # {"ok":true,"store":"postgres"}
kubectl get lake prod                                          # DB 1/1, PHASE Ready
curl -sS -H "Authorization: Bearer $T" "https://<host>/v1/verify_audit"    # {"verified":true} — the chain survived
```

## Who to page

lake on-call; the operator maintainer if the `Lake`'s Postgres fields do not reach the CNPG
Cluster; the Azure subscription owner for disk or node problems.
