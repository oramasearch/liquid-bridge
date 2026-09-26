---
name: lake-service
description: Add a new lake service kind (a database, stream, engine or compute service a customer creates on lake's Services page) or update an existing one — choosing an upstream Kubernetes operator or building our own wrapper service, the private repo and image, lake's kind and migration, the Orama operator reconciler, the helmfile, credentials, readiness, deletion, start times, deploy order, and the browser proof. Use when asked to "add a service", "offer X on lake", "add a service kind", "update/upgrade the Kafka/Postgres/… service", or bump a service operator or image.
---

# /lake-service

How a service kind is added to lake, or changed, end to end. The architecture is decisions 46 and
47 (`docs/decisions.md`); the contract lake and the operator build to is lake
`docs/control-plane/services.md` (the catalog table), and the customer-facing page is lake
`docs/api/services.md`. Read all three before starting.

**The shape, in one breath:** lake writes the customer's desired service to its control Postgres
(`services`); the **Orama operator** reads it, writes the Kubernetes resource(s) for that kind in the
Lake's namespace, copies the connection into the Secret `lake-<lake>-services` (`<slug>.json`,
mounted in lake), and reports `service_status`. The customer sees it on **Ship → Services** and gets
its connection from **Show connection**. Nothing about a customer's service is ever decided by the
operator, and lake never talks to Kubernetes.

## 1. Decide what runs it — upstream operator or our own

Research first (web-grounded, cite sources, record them in the decision): the service's licence, and
whether a **production-grade, permissively licensed** Kubernetes operator exists.

| Situation | What we do | Examples |
|---|---|---|
| A mature, actively maintained operator under a permissive licence (Apache 2.0, MIT, BSD), with documented failover, upgrade and recovery, and no terms that restrict offering it as a service | **Use it.** Install it from the helmfile; the Orama operator writes *its* resource | CloudNativePG, Strimzi, Altinity, TiDB Operator, K8ssandra |
| No such operator — none exists, it is immature, its licence or its **distribution/portal terms** forbid hosting or resale, or it is really something else (an Airflow task operator, a vendor's on-prem product) | **Add the functionality to our own operator.** The Orama operator runs the service directly as plain Kubernetes workloads (StatefulSet or Deployment, Service, Secret), and, where the service has no network API of its own, **we write a small wrapper service** that exposes it | SQLite (`lake-sqlite`), DuckDB and Polars (lake#195) |
| A promising but not production-ready operator the customer still wants | Use it, but mark the kind `preview` in lake's kind table (the UI says *preview, not for production*) and say why in the decision | Valkey (valkey-io operator, `v1alpha1`) |

Check the **service's own licence** too: it must allow a paid hosted offering (MIT, Apache, BSD,
PostgreSQL, public domain). Exclude anything whose terms restrict internal use or resale (Crunchy
PGO's portal terms, Polars On-Prem). Note trademark limits: descriptive names only ("Postgres",
"powered by DuckDB"), never "<Vendor> Cloud".

Record the choice as a **decision** (bridge `docs/decisions.md` plus an issue labelled `decision`;
amend decision 47 for a new kind), with the licence, the operator or the reason there is none, the
cost, and what would make us revisit.

## 2. Our own wrapper service (when step 1 says so)

**Every service is its own private repo with its own private image** (umbrella `CLAUDE.md`). Never
put a service inside the operator or lake.

1. `gh repo create oramasearch/lake-<name> --private`; `gh repo view … --json visibility` must say
   `PRIVATE`. Model it on `oramasearch/lake-sqlite`: `cmd/`, `internal/server/`, `Dockerfile`
   (digest-pinned builder, distroless/static or equivalent, numeric non-root user, read-only root
   filesystem), `Makefile`, `README.md`, `CLAUDE.md`, `docs/api.md`.
2. **API:** HTTP on 8080, `Authorization: Bearer <token>` on everything but `GET /healthz`
   (constant-time compare), JSON errors `{error:{code,message}}`, a request timeout, a body cap, a
   row cap, graceful SIGTERM, one JSON log line per request that **never** logs SQL, parameters,
   bodies or the token. `/healthz` answers 200 only when the engine really answers.
3. **Sandbox untrusted input.** Treat customer SQL/code as code: disable filesystem and network
   access the engine allows (DuckDB `enable_external_access=false`, no extension autoload,
   `lock_configuration`), limits on memory, CPU and time, and a test that tries each escape.
4. **Docker Hub: create the repository private before the first push** (Hub API `POST
   /v2/repositories/` with `is_private: true`) — a first push creates it **public**. After every
   push to a new name, an anonymous `curl -s -o /dev/null -w '%{http_code}'
   https://hub.docker.com/v2/repositories/oramasearch/<name>/` must answer **404**.
5. Build `linux/amd64` on the cluster BuildKit (`/liquid-dev`), immutable semver tag.
6. Pin it in this bridge: `git submodule add git@github.com:oramasearch/lake-<name>.git
   modules/lake-<name>`, and update `README.md`, `CLAUDE.md` and `docs/repositories.md`.

## 3. The contract (lake, first)

In lake, on a feature branch:

1. **`docs/control-plane/services.md`** — add the kind's row to *The catalog*: what runs it, the
   resource(s) the Orama operator writes, what `instances` means (and its allowed values), when it is
   Ready, the credential fields in `<slug>.json`, the in-cluster `endpoint`, and what deletion must
   remove (PVCs the upstream operator keeps).
2. **Migration** `db/schema.sql`: widen `service_kind_check` (drop and re-add, idempotent) with a new
   guard table, `NNNN_<name>` in `schema_migrations`. Apply it twice to a scratch database to prove
   idempotency. Update `CLAUDE.md`'s guard name and `docs/control-plane/schema.md`.
3. **Kind table** `include/lake/control/store.hpp` `service_kinds`: key, label, `ready_minutes`
   (placeholder until measured), `preview`. It drives validation, the menu and start-time hints.
   Add any per-kind validation (SQLite: `instances` must be 1) in `create_service`.
4. **`service_connection`** returns whatever the operator delivers except `kind`; Zetta's admin
   token is the one thing never returned.
5. Tests in `tests/test_workspaces.cpp` (the kind is accepted, its validation, its connection) and a
   Postgres-backed store test if the store changes. `docs/api/services.md` gains the kind.
6. Push the contract commit first — the operator vendors the schema from it.

## 4. The operator (orama-operator, PR-based)

1. **Upstream operator:** add it to `helmfile.yaml` under `tier=service-operators`, **pinned**
   (chart version), **watching every namespace** (check the chart's default — Strimzi, K8ssandra and
   Altinity all default to their own namespace; Altinity reads an *empty* `include` as its own
   namespace only), CRDs installed (a presync hook when the chart omits them, as TiDB), dependencies
   via `needs:` (K8ssandra → cert-manager). Document it in `docs/install.md`.
2. **Reconciler:** a kind in `internal/controller/lake_service_catalog.go` plus
   `lake_service_<kind>.go`: build the resource(s) as **unstructured** objects from the **pinned CRD
   schema** (fetch the CRD at that version and validate against it — never write fields from
   memory); readiness from its status **and** the credential written; the credential from the
   upstream Secret (trusted only when the resource owns it) or a generated one
   `<name>-credentials`; deletion removes the resource, then leftover PVCs selected by its labels,
   then the Secret, then writes `Deleted`; a missing CRD fails only that kind (`the <kind> operator is
   not installed on this cluster`). Give each object its own `app.kubernetes.io/instance`. For our
   own wrapper: StatefulSet (volume) or Deployment, ClusterIP Service, probes on `/healthz`, modest
   requests and a memory limit, non-root, read-only root filesystem, seccomp, `imagePullSecrets` from
   the Lake's `spec.pullSecretName`, and an image field on the Lake CRD with a chart default.
3. RBAC markers for the new API groups; `make manifests`; keep e2e CRDs out of `chart/crds/`.
4. Vendor lake's schema byte-identically and select the new guard (`hack/check-lake-schema.py`).
5. Tests with the fake client and store: build, ready gating, credential, deletion order, foreign
   object refusal, not-installed message, quota. Docs: `docs/lake/services.md`, `DESIGN.md` entry.
6. `go build ./... && go vet ./... && go test ./... && helm lint chart/`.

## 5. Deploy, in this order

1. Upstream operator: `helmfile -l name=<release> sync --wait` (or `-l tier=service-operators`).
2. Wrapper image (if any) pushed and confirmed private.
3. Operator: merge (merge commit, never squash), build `main-<sha>`, `kubectl apply -f chart/crds/`,
   `helm upgrade orama-operator` with the stored values (`/liquid-dev` step 5). The `PostgresSchema`
   re-applies the new migration by content hash; confirm `Applied` with the new version.
4. lake: merge, build from the true head of `main`, roll `Lake/prod`, confirm `GET /v1/server_info`
   reports the commit.
5. **Prove it in the browser** (`docs/deployment/browser-testing.md` §3c):
   `node tools/e2e/services.mjs https://lake.oramadev.net <ticket> <out> <kind>` must exit 0 —
   create, Ready, connection fields, (real queries for wrapper kinds), delete. Read `log.json` and
   the screenshots.
6. **Measure the start time** from that run and set `ready_minutes` (rounded up) plus the table in
   lake `docs/api/services.md`; ship that as a follow-up.
7. Record the deploy in `docs/action-plan.md` and `docs/handover.md` (what is deployed, verified
   how), bump this bridge's and the umbrella's pointers, close the issue with the proof.

## Updating an existing kind

| Change | Do |
|---|---|
| Upstream operator version | Read its release notes for CRD and API changes (Valkey 0.6.0 broke a field); bump the pinned version in `helmfile.yaml`; if the CRD changed, re-fetch it and re-validate what the reconciler writes; `helmfile sync` that release; run `services.mjs <kind>` |
| Engine version (Postgres major, Kafka, Cassandra image) | Change the version the reconciler writes or its default; decide whether existing services roll or only new ones get it, and say so; test an upgrade of a live test service, not just a fresh one |
| Our wrapper service | Change its repo, release a new semver tag (private repo still 404 anonymously), bump the operator's default image; an image change rolls every service of that kind once |
| What `instances` / `storage_gi` mean, or new spec fields | Contract first (`services.md`), then lake validation, then the reconciler; resize is not supported today — say so rather than half-doing it |
| Credential shape | Contract, operator credential builder, and lake's Show connection together; existing services get the new shape on the next reconcile |
| Retiring a kind | Stop offering it in the kind table first (existing services keep running), then a decision on migrating or deleting them — never delete a customer's data without Steve's explicit go-ahead |

## Rules that always apply

- Private by default: repo, image, everything. Never `gh repo fork` a public upstream.
- Merge commits, never squash. Commit means push. No AI attribution.
- Never write "seam". Documentation in the same change.
- A merged change is not done until it is deployed and `services.mjs` passes for that kind.
- Customers' services hold customer data: no destructive action on a live service, volume or
  database without Steve's explicit permission, in any environment.
