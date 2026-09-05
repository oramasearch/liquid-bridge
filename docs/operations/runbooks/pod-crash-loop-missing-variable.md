# Pod crash loop on a missing or wrong variable

## Symptoms

- `kubectl get pods -n lake` shows `lake-prod-…` in `CrashLoopBackOff` or `Error`, restarts
  climbing; `kubectl get lake prod` shows `READY 0`, `PHASE Progressing` or `Degraded`.
- External: `GET /healthz` fails or times out; if an old ReplicaSet's pod is still serving, the
  site works but the rollout never completes.
- The status page shows API and Web UI *Outage* together.

## Diagnosis

```sh
kubectl get pods -n lake -l app.kubernetes.io/name=lake
kubectl logs -n lake deploy/lake-prod --previous --tail=20     # the dying container's last words
kubectl get deploy -n lake lake-prod -o jsonpath='{range .spec.template.spec.containers[0].env[*]}{.name}{"\n"}{end}'
kubectl get lake prod -o jsonpath='{.spec.env}{"\n"}'
```

lake exits with status 2 before serving when its configuration is invalid; the reason is the
last stderr line. Known messages and their causes (lake `src/main.cpp`, `docs/serving/`,
`docs/control-plane/log.md`, `docs/api/audit.md`):

| Log line | Cause | Variable |
|---|---|---|
| `lake: invalid transparency log configuration: …` (witnesses or threshold) | `LAKE_STORE_ROOT` is set (always, by the operator) and `LAKE_LOG_MODE` is unset, so it defaults to **`witnessed`**, which requires configured witnesses. This is the 2026-09-05 failure that led to `spec.env` being added to the CR (operator #137). | `LAKE_LOG_MODE=air-gapped` until witnesses exist; or `LAKE_LOG_WITNESSES` + `LAKE_LOG_WITNESS_THRESHOLD` |
| `lake: invalid transparency log configuration: … aggregator` | `LAKE_LOG_MODE=anchored` without `LAKE_LOG_AGGREGATOR` | `LAKE_LOG_AGGREGATOR` |
| `LAKE_INSTANCE_KEK is required to load the generated identity` / `… to persist a generated identity` / `… for encrypted credentials` | The control database holds a wrapped identity seed or encrypted credentials and the pod has no KEK. The operator mints `lake-<name>-instance-kek` while Postgres is enabled (operator #135); if the Secret was deleted the operator mints a **new** one and the old ciphertext is unrecoverable — see [`disaster-recovery.md`](disaster-recovery.md) before doing anything. | `LAKE_INSTANCE_KEK` (operator-owned; never set it in `spec.env`, the operator ignores conflicts) |
| `lake: <NAME> must be an unsigned integer` | A numeric variable (`LAKE_LOG_WITNESS_THRESHOLD`, `LAKE_TSA_*_SECONDS`, `LAKE_PRICE_*`, `LAKE_STORAGE_QUOTA_BYTES`) has a non-numeric value | the named variable |
| `lake: cannot start: <reason>` | the server refused to bind or build its router: a bad `--listen`, or a store that cannot be opened | `spec.args`, `LAKE_CONTROL_DB_URI` (operator-owned) |
| `"admin_token_set":"no"` in the startup JSON (not a crash) | the admin Secret is missing; every guarded call answers 403 | `LAKE_ADMIN_TOKEN` (operator-owned) |
| Pod `Pending`, not crashing | not this runbook: an unbound store PVC — [`store-volume-permission-or-capacity.md`](store-volume-permission-or-capacity.md) | — |

Operator-owned variables (`LAKE_ADMIN_TOKEN`, `LAKE_INSTANCE_KEK`, `LAKE_CONTROL_DB_URI`,
`LAKE_CONTROL_DB_PASSWORD`, `LAKE_STORE_ROOT`) come from Secrets and the PVC the operator manages;
if one is empty, check that its Secret exists (`kubectl get secrets -n lake`) and that the
operator is running (`kubectl get deploy -n orama-system orama-cloud-v1-operator`).

## Fix

1. Take the current CR: `kubectl get lake prod -o json > lake-prod-cr.json`, strip `status`
   and `metadata.{resourceVersion,uid,generation,creationTimestamp,managedFields}`.
2. Set or correct the variable under `spec.env` (a list of Kubernetes `EnvVar`; `valueFrom`
   Secret references are allowed for anything sensitive — `LAKE_REPLICATION_TOKEN`,
   `LAKE_IDENTITY_SEED`).
3. `kubectl apply -f lake-prod-cr.json`. The operator rolls the Deployment.
4. If the cause is a *new* lake image that requires a variable the CR does not set, prefer
   rolling back the image ([`rollback.md`](rollback.md)) and adding the variable in a second,
   calm step.

Do not `kubectl set env deploy/lake-prod`: the operator reverts it on the next reconcile.

## Verification

```sh
kubectl rollout status deploy/lake-prod -n lake
kubectl logs -n lake deploy/lake-prod | head -1      # one JSON startup line: "event":"startup", "log_mode", "store":"postgres", "admin_token_set":"yes"
kubectl get lake prod                                # READY 1, PHASE Ready
curl -sS https://<host>/readyz                        # {"ok":true,"store":"postgres"}
```

## Who to page

lake on-call. If the missing variable is operator-owned (KEK, admin token, DB URI), also the
operator maintainer. A new required variable in a lake release that the CR cannot express is a
lake issue and an operator issue.
