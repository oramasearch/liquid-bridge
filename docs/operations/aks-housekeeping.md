# AKS sandbox housekeeping after Phase 0.5

**What.** The inventory of `orama-production-cluster-01` as read on 2026-09-05 (about 22:55 UTC,
read-only: `kubectl get`, `helm list`, `kubectl top`), what on it is a Phase 0.5 leftover and
what is in use, and a cleanup list **for the owner to approve**. Nothing in this page has been
executed. Refs https://github.com/oramasearch/liquid-bridge/issues/6.

**Why.** The cluster is one node and its CPU requests stand at 84 % of allocatable. Every
leftover costs headroom for `Lake/prod` rollouts and money for public IPs and disks, and every
leftover with a public address is attack surface.

## Inventory

### Node

| | |
|---|---|
| Cluster | `orama-production-cluster-01`, Kubernetes v1.35.5, Cilium, `eastus` zone 3 |
| Nodes | **1**: `aks-agentpool-33345110-vmss000000`, `Standard_D8as_v7` (8 vCPU, 32 GiB), Ubuntu 24.04.4, containerd 2.3.2 |
| Allocatable | 7820 m CPU, 29.7 GiB memory, 110 pods |
| Requests | CPU **6578 m (84 %)**, memory 14.2 GiB (49 %) |
| Limits | CPU 55.7 cores (712 %), memory 108 GiB (372 %) — overcommitted, as expected for a sandbox |
| Live usage (`kubectl top`) | 3455 m CPU (44 %), 15.2 GiB memory (52 %) |

A single node means every node event (AKS auto-upgrade, VM host maintenance) is a full outage of
everything below; see [`slos.md`](slos.md).

### Namespaces and releases

| Namespace | Age | What is in it | Helm release |
|---|---|---|---|
| `lake` | 3 d | `Lake/prod` and everything it owns (below) | — (operator-managed) |
| `orama-system` | 59 d | the operator; `OramaCloudV1/v1`; `OramaZettaCluster/juan`, `/nine` | `orama-cloud-v1-operator` rev 16, image `oramasearch/orama-operator:lake-crd-58bf1b8` (branch `feat/lake-crd`) |
| `buildkit` | 3 d | the `aks-amd64` buildx builder pod | — (created by `docker buildx create`) |
| `cnpg-system` | 59 d | CloudNativePG operator | `cnpg` (cloudnative-pg 0.29.0, app 1.30.0) |
| `ingress-nginx` | 58 d | the shared ingress controller, LoadBalancer `172.212.70.79` | `ingress-nginx` 4.15.1 |
| `gatekeeper-system` | 59 d | Azure Policy add-on | AKS-managed |
| `kube-system` | 59 d | AKS add-ons: Azure Monitor logs and metrics (managed Prometheus), image cleaner, workload identity, overlay upgrade | AKS-managed |
| `default` | 59 d | only the `kubernetes` Service | — |

CRDs present beyond the operator's own: CNPG (`clusters`, `backups`, `scheduledbackups`, …),
Cilium, `volumesnapshots.snapshot.storage.k8s.io` (Azure disk CSI snapshots are available),
Azure Monitor `podmonitors`/`servicemonitors`, eraser (image cleaner). **No cert-manager.**

### `lake` namespace (in use: this is production)

| Resource | Detail |
|---|---|
| `Lake/prod` | `host: lake.oramadev.net`, `image: oramasearch/lake:20260905b`, `replicas: 1`, `env: LAKE_LOG_MODE=air-gapped, LAKE_PUBLIC_HOST=lake.oramadev.net`, `store: 100Gi managed-csi RWO`, `postgres: 1 instance, 50Gi`; status `Ready`, `StoreReady=True`, **`BackupReady=False` (backups disabled)** |
| Deployment `lake-prod` | 1/1, pod started 2026-09-05T22:54Z, 0 restarts; readiness `GET /`; no liveness probe, no resource requests (operator #122) |
| CNPG `lake-prod-controldb` | 1 instance, healthy, PVC 50 Gi (`default` class), Postgres 18 |
| `PostgresSchema lake-prod-controldb-schema` | `spec.version sha256:84cfbefb73f3`, **`status.appliedVersion sha256:39f1494b1c77`** (see findings) |
| PVC `lake-prod-store` | 100 Gi, `managed-csi`, RWO, bound 2026-09-05 ~22:42Z |
| Ingress `lake-prod` | host `lake.oramadev.net` → Service, no TLS section (TLS at Cloudflare only) |
| `CloudflareDNSRecord lake-prod-dns` | `lake.oramadev.net → 172.212.70.79`, proxied, Ready |
| Secrets | `lake-prod-admin`, `lake-prod-instance-kek` (minted 2026-09-05 ~22:02Z), `lake-prod-controldb-{app,ca,replication,server}`, `oramasearch-dockerhub` (pull), `cloudflare-api-token` (**`oramadev.net` zone**, copied from `orama-system`) |
| Job `lake-prod-controldb-schema-migrate` | Complete, ran 2026-09-02 |
| ReplicaSets | 9, eight at 0 replicas from the day's rollouts (Deployment history, harmless; the default `revisionHistoryLimit` of 10 prunes them) |

### `orama-system` namespace

| Resource | Detail | In use? |
|---|---|---|
| Deployment `orama-cloud-v1-operator` | 1/1, image `lake-crd-58bf1b8`, restarted 2026-09-05T22:47Z | **Yes**: reconciles `Lake/prod` |
| `OramaCloudV1/v1` | `us-east`, primary, profile `light`, 22/22 ready, 54 d: 16 Deployments, 6 StatefulSets (`v1-analytics`, `v1-broker`, `v1-cache`, `v1-harvest-mongo`, `v1-search`, `v1-writer`), CNPG `v1-controldb`, 7 PVCs × 10 Gi, Ingress `app.oramadev.net` (+ `docs.sandbox.local`), `CloudflareDNSRecord v1-dashboard-dns`, `CloudflareR2Bucket v1-legacy-indexes`, 30 Services, ~25 Secrets | **Not a Phase 0.5 leftover.** The One Orama v1 sandbox; the largest consumer on the node. Owner's call, out of scope for this list. |
| `OramaZettaCluster/juan` | 1 node, image `oramasearch/zetta:headless-v1-sandbox` (mutable tag), 41 d; StatefulSet `juan-zetta`, PVC `data-juan-zetta-0` 5 Gi, **public LoadBalancer `juan-zetta-peer-0` 20.124.167.16:7777**, Ingress `juan.oramadev.net`, DNS record, Secrets `juan-zetta-admin`, `juan-zetta-cluster` | **Phase 0.5 leftover.** Steve: can be deleted (issue #6). |
| `OramaZettaCluster/nine` | 1 node, digest-pinned zetta image, 55 d; StatefulSet `nine-zetta`, PVC `data-nine-zetta-0` 5 Gi, **public LoadBalancer `nine-zetta-peer-0` 20.237.28.55:7777**, Ingress `zetta.oramadev.net`, DNS record, Secrets `nine-zetta-admin`, `nine-zetta-cluster` | **Phase 0.5 leftover.** Same. |
| Job `nine-e2e-e2e` | Failed 0/1, 47 d, two `Failed` pods `nine-e2e-e2e-2l9rv`, `-89w2c` | Leftover from a July e2e run. |
| Secrets `cloudflare-api-token`, `cloudflare-r2`, `oramasearch-dockerhub` | zone token (`oramadev.net`), R2 credentials, pull secret | In use by the operator's Cloudflare CRs and pulls. |

### `buildkit` namespace

| Resource | Detail |
|---|---|
| Deployment `aks-amd640` | `moby/buildkit:buildx-stable-1-rootless`, 1/1, pod running since 2026-09-05T15:07Z; **requests 2 CPU / 4 GiB, limits 6 CPU / 12 GiB** |

Created by `docker buildx create --name aks-amd64 --driver kubernetes …` (lake `CLAUDE.md`; bridge
memory *amd64 image builds*). It is the only way to build the C++ images natively on amd64 from an
Apple Silicon workstation until the tagged-image GitHub Actions workflow has its org secrets. The
issue #6 text calls the namespace "empty"; on 2026-09-05 it holds the live builder.

### PVCs (all `Bound`, all RWO)

| Namespace | PVC | Size | Class | Belongs to |
|---|---|---|---|---|
| `lake` | `lake-prod-store` | 100 Gi | `managed-csi` | `Lake/prod` customer stores and log — **production data, no backup** |
| `lake` | `lake-prod-controldb-1` | 50 Gi | `default` | `Lake/prod` control plane — **production data, no backup** |
| `orama-system` | `v1-controldb-1` and `data-v1-{analytics,broker,cache,harvest-mongo,search,writer}-0` | 7 × 10 Gi | `default` | `OramaCloudV1/v1` |
| `orama-system` | `data-juan-zetta-0`, `data-nine-zetta-0` | 2 × 5 Gi | `default` | the two Zetta leftovers; **retained after the CRs are deleted** and need an explicit delete |

### Public addresses

| Address | What |
|---|---|
| `172.212.70.79` | ingress-nginx LoadBalancer: `lake.oramadev.net`, `app.oramadev.net`, `juan.oramadev.net`, `zetta.oramadev.net` |
| `20.124.167.16` | `juan-zetta-peer-0` (Zetta peer port 7777, leftover) |
| `20.237.28.55` | `nine-zetta-peer-0` (Zetta peer port 7777, leftover) |

## Findings the owner should know now

1. **`Lake/prod` has no backups and two things no backup could restore.** `BackupReady=False`
   (`control-plane backups are disabled`); the Secret `lake-prod-backups-r2` does not exist. Even
   with CNPG backups on, the **store volume** (customer content, the transparency log) and the
   **`lake-prod-instance-kek` Secret** (which wraps lake's identity seed, every customer KEK, TOTP
   seeds, OAuth and webhook secrets) have no copy anywhere. Losing the KEK makes the database
   backup unusable for anything encrypted. See
   [`runbooks/disaster-recovery.md`](runbooks/disaster-recovery.md).
2. **The operator's record of the control-plane schema is stale.** `PostgresSchema
   lake-prod-controldb-schema` wants `sha256:84cfbefb73f3` (migrations `0001`–`0017`) but
   `status.appliedVersion` is `sha256:39f1494b1c77`, the `0001`+`0002` file its one Job applied
   on 2026-09-02. The database itself was migrated by hand on 2026-09-05 (5 → 66 tables) and lake
   `20260905b` runs against it — `/v1/identity` answers, so `lake_identity` (migration `0005`)
   exists. The controller creates its Job once and re-applies only after that Job is deleted
   (`postgresschema_controller.go`), so the status will stay wrong until the owned
   `PostgresSchema` is deleted and recreated; the idempotent file then finds `agent_guard` and
   exits 0, or adds what is missing. Runbook:
   [techops-docs `schema-job-failure.md`](https://github.com/oramasearch/techops-docs/blob/main/docs/lake/runbooks/schema-job-failure.md).
3. **CPU requests at 84 % on one node.** A `Lake` rollout surges one pod (no requests, so it
   schedules), but anything with requests — a second lake replica with limits, a CNPG replica, a
   restore Cluster for a rehearsal — may not fit while the builder pod holds 2 CPU / 4 GiB.
4. **Origin traffic is plaintext.** The Ingress has no TLS; Cloudflare terminates TLS at the
   edge and reaches `172.212.70.79:80` over HTTP. Operator #122 (TLS at the Ingress) and a
   Cloudflare Origin CA certificate with `Full (strict)` close this; see
   [`lake-live-host.md`](lake-live-host.md).
5. **A failed RWX provisioning attempt is still in the event log**: `lake-prod-store` was first
   requested with `ReadWriteMany` on `managed-csi` (Azure disk cannot: `mountVolume is not
   supported for access mode: MULTI_NODE_MULTI_WRITER`), then recreated as RWO with
   `replicas: 1`. The operator's default is still RWX (operator `docs/lake/README.md`); a Lake
   created without `spec.store.accessModes: [ReadWriteOnce]` on this cluster stays `Pending`.
6. **The pod restarted at 22:54Z on 2026-09-05 with no `--previous` container**, i.e. a fresh
   pod from a rollout, not a crash; 0 restarts on every lake and operator pod. The `Lake`
   condition history is clean.
7. **`Lake/hello` and the `lake-dev` namespace no longer exist.** Issue #6's fourth item is
   already resolved: the only Lake is `Lake/prod` in `lake`.

## Phase 0.5 leftovers versus in use

| Item | Verdict |
|---|---|
| `OramaZettaCluster/juan`, `/nine` and everything they own (StatefulSets, two public LBs, two Ingresses, two DNS records, four Secrets) | **Leftover.** Nothing reads them: lake's data plane is not provisioned yet (operator #125) and, when it is, it will be an *owned* `OramaZettaCluster` per `Lake`, not these. |
| PVCs `data-juan-zetta-0`, `data-nine-zetta-0` | **Leftover.** Survive CR deletion by design; explicit delete needed. |
| Job `nine-e2e-e2e` and its two `Failed` pods | **Leftover.** |
| `buildkit` namespace | **In use** as the documented builder home; the *pod* is a reservation that should not idle. |
| `Lake/hello`, `lake-dev` | **Gone already.** |
| Secret `cloudflare-api-token` in `lake` | **In use until the host moves**, then replaced by a `lake.live`-zone Secret and removed ([`lake-live-host.md`](lake-live-host.md)). |
| Docker Hub repository `oramasearch/orama-cloud-v1-operator` | **Probably leftover** (pre-rename builds). Not verifiable from the cluster: the deployed image is `oramasearch/orama-operator:lake-crd-58bf1b8` and no pod references the old name. Check the Hub for pulls in the last 30 days before deleting. |
| `OramaCloudV1/v1` | **Not a Phase 0.5 item.** Listed for completeness because it dominates the node; a separate decision. |
| Old lake ReplicaSets | Harmless; pruned automatically. |

## Proposed cleanup — for approval, not executed

Each line is one command the owner runs or approves; the destructive ones are marked. Order
matters: CRs first (they tear down LBs and DNS records), PVCs after, namespace last.

| # | Action | Command | Destroys | Frees |
|---|---|---|---|---|
| 1 | Delete the two Zetta sandbox clusters | `kubectl delete oramazettacluster juan nine -n orama-system` | two Zetta nodes (sandbox data only), two StatefulSets, **two public IPs**, Ingresses `juan.oramadev.net`, `zetta.oramadev.net`, their DNS records and `*-zetta-{admin,cluster}` Secrets | node CPU/memory of two Zetta pods; two Standard public IPs and LB rules |
| 2 | Delete their retained volumes (**destructive; after 1 completes**) | `kubectl delete pvc data-juan-zetta-0 data-nine-zetta-0 -n orama-system` | 2 × 5 Gi of sandbox Zetta data | two Azure disks |
| 3 | Delete the failed e2e Job | `kubectl delete job nine-e2e-e2e -n orama-system` | a failed Job record and two dead pods | nothing material; tidiness |
| 4 | Remove the idle builder **pod**, keep the namespace | `docker buildx rm aks-amd64` (from the workstation that created it; leaves the namespace) | nothing persistent — the builder is recreated by `docker buildx create …` when the next build needs it | **2 CPU / 4 GiB of requests (26 % of allocatable CPU)** |
| 5 | Retire the pre-rename Docker Hub repository | Hub UI, or `dockerhub-ops`, after confirming zero pulls in 30 days | old `orama-cloud-v1-operator` images | Hub storage; removes a name someone could pull by mistake |
| 6 | After the host moves: drop the `oramadev.net` zone token copy from `lake` | `kubectl delete secret cloudflare-api-token -n lake` (only once `Lake/prod` references the `lake.live` Secret and `kubectl get cloudflarednsrecords -n lake` shows no `oramadev.net` record) | a token copy that a `lake`-namespace compromise could use against `oramadev.net` | blast radius |

**Not proposed:** anything in `orama-system` belonging to `OramaCloudV1/v1`; the `cnpg`,
`ingress-nginx` and AKS-managed releases; the `default` namespace (it only holds the API
Service).

### The builder: keep the namespace, do not idle the pod

Recommendation: **keep `buildkit` as the documented home; create the builder for a build and
remove it after** (`docker buildx create --name aks-amd64 --driver kubernetes … --driver-opt
namespace=buildkit,…` then `docker buildx rm aks-amd64`), exactly as the recipe already says. The
pod is 26 % of the node's CPU requests while it idles, and it holds no state worth keeping (the
build cache is rebuilt on the next run; `--load` moves the image to the workstation, then
`docker push`). Remove the namespace itself only when both of these are true: the lake `image`
workflow publishes `oramasearch/lake:<tag>` from GitHub Actions (blocked on the org secrets,
lake `docs/build/ci.md`), and the operator image is built the same way. Until then the builder
is also the emergency path in [`runbooks/roll-lake-image.md`](runbooks/roll-lake-image.md).

## How to verify

Re-run the inventory read-only and diff against this page:

```sh
kubectl get nodes -o wide; kubectl top nodes
kubectl get ns; helm list -A
kubectl get lake,oramazettacluster,oramacloudv1 -A
kubectl get clusters.postgresql.cnpg.io,postgresschema,cloudflarednsrecords -A
kubectl get pvc -A; kubectl get svc -A | grep LoadBalancer; kubectl get ingress -A
kubectl get deploy -n buildkit -o jsonpath='{.items[*].spec.template.spec.containers[*].resources}'
kubectl describe node | sed -n '/Allocated resources/,/Events/p'
```

## How to change

When an item in the cleanup table is executed, move it to a dated *Done* list at the end of this
page with the command that ran, and update the inventory tables; the page is the record of what
the sandbox holds. A new workload on the cluster gets a row in the inventory in the same PR that
deploys it (bridge `CLAUDE.md`, *Documentation is part of every change*).
