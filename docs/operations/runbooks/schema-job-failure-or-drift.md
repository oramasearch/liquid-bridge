# Control-plane schema: Job failure or version drift

The operator owns a ConfigMap `lake-prod-controldb-migrations` (lake's `db/schema.sql`, vendored
byte-identical) and a `PostgresSchema lake-prod-controldb-schema` whose controller runs one
idempotent Job `lake-prod-controldb-schema-migrate`: wait for the database, exit 0 if the guard
table exists, else apply the whole file in one transaction. The Job is created **once** and
annotated with the version it applied; a bumped `spec.version` re-applies only after that Job is
deleted (operator `internal/controller/postgresschema_controller.go`; lake
`docs/control-plane/schema.md`; incremental migrations are operator #126). Migrations never run in
lake pods.

## Symptoms

| Symptom | Meaning |
|---|---|
| `kubectl get postgresschema -n lake` → `PHASE Failed` | the Job's pod exhausted its backoff: SQL error, unreachable database, bad `guardTable` |
| `kubectl get lake prod` → `SCHEMA Pending` for long | the Job is waiting for the database Secret or the database itself |
| `VERSION` ≠ `APPLIED` with `PHASE Applied` | **drift**: the ConfigMap has newer SQL than the Job ever ran. Seen 2026-09-05: `VERSION sha256:84cfbefb73f3`, `APPLIED sha256:39f1494b1c77` because the database was migrated by hand (5 → 66 tables) and the Job from 2026-09-02 was never re-run |
| lake answers `500` on capabilities that need a new table (`relation "…" does not exist` in the pod log) | the image is ahead of the database |

## Diagnosis

```sh
kubectl get postgresschema -n lake -o wide
kubectl get postgresschema lake-prod-controldb-schema -n lake -o jsonpath='{.spec.version} {.spec.guardTable} {.status.appliedVersion} {.status.phase}{"\n"}'
kubectl get job -n lake lake-prod-controldb-schema-migrate -o jsonpath='{.metadata.annotations}{"\n"}{.status.conditions[*].type}{"\n"}'
kubectl logs -n lake job/lake-prod-controldb-schema-migrate --tail=40
kubectl get configmap -n lake lake-prod-controldb-migrations -o jsonpath='{.data.schema\.sql}' | grep -o "INSERT INTO schema_migrations[^;]*;" | tail -3
# what the database actually has (read-only):
kubectl exec -n lake lake-prod-controldb-1 -c postgres -- psql -U postgres -d lake -tAc \
  "SELECT version FROM schema_migrations ORDER BY version" 
kubectl exec -n lake lake-prod-controldb-1 -c postgres -- psql -U postgres -d lake -tAc \
  "SELECT to_regclass('public.agent_guard')"           # the current guard; null means the newest migration is missing
```

## Fix

**Drift, database already migrated (the 2026-09-05 state).** Make the record truthful by letting
the Job run again; it is idempotent (`IF NOT EXISTS`, `CREATE OR REPLACE`, `ON CONFLICT DO
NOTHING`) and exits 0 as soon as it sees the guard table:

```sh
kubectl delete postgresschema lake-prod-controldb-schema -n lake     # owned: the operator recreates it within a reconcile
kubectl get postgresschema -n lake -w                                 # Pending → Applying → Applied at the new version
```

The Job is owned by the `PostgresSchema` and is garbage-collected with it; the recreated schema
resource creates a new Job annotated with the current version. Safe for a live lake: the file
adds only what is missing and holds one transaction.

**Database behind the image.** Same command; the Job applies the missing migrations. If the
guard table for the *older* state still exists but is not the current `guardTable`, the Job
still applies (it checks only the configured guard). Roll lake back
([`rollback.md`](rollback.md)) if the outage is live and the Job is slow.

**Job `Failed`.** Read its log. A SQL error means the vendored schema and the database disagree
in a way idempotency does not cover (a changed constraint, a renamed column) — that is a lake
schema bug, not an on-call fix: roll lake back to the image that matches the database, open a
lake issue with the log, and do not hand-edit the database. `WaitingForDatabase` means the CNPG
cluster or its `-app` Secret is missing:
[`control-database-unreachable-or-full.md`](control-database-unreachable-or-full.md).

**The file itself must never be edited on the cluster.** The ConfigMap is regenerated from the
operator's asset on every reconcile; the source of truth is lake's `db/schema.sql`, copied into
the operator per wave (lake `docs/control-plane/schema.md`, *How to change it*).

## Verification

```sh
kubectl get postgresschema -n lake              # VERSION == APPLIED, PHASE Applied
kubectl get lake prod                           # SCHEMA Applied, PHASE Ready
kubectl exec -n lake lake-prod-controldb-1 -c postgres -- psql -U postgres -d lake -tAc \
  "SELECT count(*) FROM schema_migrations"      # 16 rows for 0001–0017 (0003 does not exist)
curl -sS https://<host>/v1/identity | jq .ok    # true
```

## Who to page

lake on-call; the operator maintainer for the controller's behaviour (and to land #126 so the
delete-and-recreate step disappears); the lake maintainer for a SQL error.
