# Repositories

What lives where, and the rules for each. All repositories are **private** under
`oramasearch`.

| Repository | Module path | What it is | Language | Status |
|---|---|---|---|---|
| [`liquid`](https://github.com/oramasearch/liquid) | `modules/liquid` | The tool — VCS, build, package manager, artifact service, runtime. **The specification for everything** lives here. **Open source eventually; never depends on Zetta.** | C++26 | **libliquid** (`liquid::liquid`, static or shared, `find_package` works) + the `liquid` CLI; the Phase 1 API map (`docs/library/api-map.md`) and the chunk-index decision (RocksDB, by benchmark) are recorded; CI on Linux, macOS, Windows and a sanitizer job (green) |
| [`k0s`](https://github.com/oramasearch/k0s) | `modules/k0s` | Private, upstream-synced copy of `k0sproject/k0s`, modified for drips on the `liquid` branch. `main` is a pristine upstream mirror. | Go | Synced; `liquid` branch has docs, `AGENTS.md` and `hack/sync-upstream.sh` (the guarded upstream sync; first real run pending) |
| [`lake`](https://github.com/oramasearch/lake) | `modules/lake` | The lake binary — the hosted service. **Enterprise. Builds on Zetta** (control plane, state, web serving) and consumes liquid's store as a library. | C++26 | Live at https://lake.oramadev.net (`oramasearch/lake:20260902c`): the control surface — one capability registry as REST `/v1`, OpenAPI, MCP — over the Postgres control plane (users, organizations, customers, repositories), server-rendered pages behind the admin sign-in; `/healthz`, `/readyz`, `/metrics` and JSON request logs; CI and a tagged-image workflow (waiting on org secrets) |
| [`liquify`](https://github.com/oramasearch/liquify) | `modules/liquify` | The IDE — native, cross-platform, C++26 on SDL3 + Dear ImGui (the stack Zetta's headed mode uses). **Open source eventually; never depends on Zetta.** Not an editor extension. | C++26 | Hello world: a window, links **libliquid** (liquid pinned as a submodule), `liquify version`, `--smoke`, 1 test; three-platform CI (waiting on the org submodule secret) |
| [`marketing-bridge`](https://github.com/oramasearch/marketing-bridge) | `modules/marketing-bridge` | Go-to-market workspace: positioning, campaign state, cold-email runbooks, analytics. **No product code.** Shared submodule with `orama-cloud-bridge`. | Docs + stdlib Python | Active. Lineup strategy at `docs/brand/get-the-right-data.md`; `orama-search-launch` campaign under `campaigns/` |
| [`orama-operator`](https://github.com/oramasearch/orama-operator) | `modules/orama-operator` | **The Orama operator** — renamed from `orama-cloud-v1-operator`. The Zetta operator, extended with a **`Lake` CR** that deploys lake. Already has its own Zetta observed-state store. | Go | Production on AKS at `oramasearch/orama-operator:lake-crd-8058ab5` (PR #118 branch, helm rev 8). **`Lake/prod`** in namespace `lake`: 3 lake replicas, 50Gi CNPG control DB, schema applied via `PostgresSchema`, https://lake.oramadev.net; `Lake/hello` live at https://lake.oramadev.net. Docker Hub repo renamed with the GitHub repo. |

## Related, not modules of this bridge

| Repository | Relationship |
|---|---|
| [`oramasearch/automerge-cpp`](https://github.com/oramasearch/automerge-cpp) | The CRDT liquid's metadata layer sits on: the org's **private copy** of `homer6/automerge-cpp` (full history, MIT; `homer6` stays the public upstream; decided 2026-09-03). What liquid needs from it is its epic #13. |
| [`oramasearch/oramacore-cpp`](https://github.com/oramasearch/oramacore-cpp) | BM25F search engine liquid specifies. Scaffold. |
| [`oramasearch/zetta`](https://github.com/oramasearch/zetta) | Orama Zetta — the running C++26 CRDT store. lake builds on it. **Read it only via `orama-work/modules/zetta-bridge/modules/zetta`** — standalone clones go stale. |
| [`oramasearch/corosio`](https://github.com/oramasearch/corosio) | **Private patch carrier** for `cppalliance/corosio`. Branch `orama-main`, 2 commits ahead of upstream: `fix(epoll): translate EPOLLHUP/EPOLLRDHUP so a hung-up fd stops spinning` (2026-07-10, PR #2), **not upstreamed** as of 2026-09-02. Zetta consumes it; **liquid and lake must too, never `cppalliance` directly.** |
| [`oramasearch/http`](https://github.com/oramasearch/http) | **Private patch carrier** for `cppalliance/http` (the sans-I/O HTTP + router beast2 rides on). Branch `zetta-patches`. Consume this, never upstream directly. |
| `cppalliance/capy` | **No private copy exists.** Zetta consumes upstream `develop` directly. Create `oramasearch/capy` only when there is a patch to carry — the procedure is for carrying patches, not for mirroring. |
| [`oramasearch/orama-bridge`](https://github.com/oramasearch/orama-bridge) | The org umbrella. Authoritative for conventions. |

## Rules that differ per repository

**`k0s`** — never commit to `main`; it is only ever fast-forwarded from upstream. Our
work is on `liquid`, rebased after each sync. The `upstream` remote's push URL is
deliberately invalid. Procedure in its `ORAMA-FORK.md`. Apache 2.0: distributing
modified binaries requires `LICENSE`, `NOTICE`, and stating that files changed — the
branch split satisfies the last by construction.

**`orama-operator`** — **runs in production on AKS.** PR-based: never fast-forward
`main`; open a PR and leave it open for review. `Lake` is a new CR alongside
`OramaCloudV1` and `OramaZettaCluster`, in the same group (`orama.cloud`). The Go
module path, image name and chart name still read `orama-cloud-v1-operator` after the
GitHub rename — changing them changes the deployed artifact and is a separate,
deliberate step. `config/` is generated and committed; `bin/` is ignored.
The operator's own `CLAUDE.md` names the AKS cluster `orama-production-cluster-01` the
**sandbox** and `make run` the standard dev loop — but the deployed operator holds the
leader lease and `make run` defaults to `leader-elect=false`, so a local run reconciles
the live `OramaZettaCluster`s a second time. The smoke test was done instead by deploying the branch image in-cluster through the chart
(`docker buildx build --platform linux/amd64` + push, `kubectl apply -f chart/crds/`, `helm upgrade
... --force-conflicts` because the July digest pin left the image field owned by `kubectl-set`).
The chart ClusterRole is hand-maintained: a new CR needs its `lakes`-style entries there or the
manager CrashLoops on cache sync.

**`marketing-bridge`** — shared with `orama-cloud-bridge`, so push it before bumping
either pointer. It carries its own hard rules in its `CLAUDE.md`: approval gates G1–G6
before any spend or go-live, US-only compliance defaults with a suppression screen at
every import, no secrets or raw lead CSVs in git, stdlib-only Python in `scripts/`, and
campaign issues on *that* repo rather than a bridge.

**`liquid`** — must never take a dependency on Zetta; it is open source eventually.
**`lake`** — builds on Zetta wherever possible. The two are on opposite sides of a
licence boundary, and that boundary is the reason they have separate stores.

## Corrected: there was no corosio drift

An earlier version of this page claimed Zetta's `modules/corosio` pointed at upstream
`cppalliance` and so was missing the epoll fix. **That was wrong** — it was read from a
standalone `~/dev/oramasearch/zetta` clone 1,053 commits behind. The bridge's Zetta
(`orama-work/modules/zetta-bridge/modules/zetta`) pins:

| Submodule | Source | Pin |
|---|---|---|
| `modules/corosio` | **`oramasearch/corosio`** branch `orama-main` | `1c1a6abf8` — the epoll-fix merge |
| `modules/http` | **`oramasearch/http`** branch `zetta-patches` | `af0353a5b` — a second private patch carrier, for `cppalliance/http` |
| `modules/beast2` | `cppalliance/beast2` | `fb0a9c8dc` |
| `modules/capy` | `cppalliance/capy` branch `develop` | `ce1c7d710` |
| `modules/automerge-cpp` | `homer6/automerge-cpp` | `4dd795513` |
| `modules/oramacore-cpp` | `oramasearch/oramacore-cpp` | `9b74ce177` |

lake vendors the HTTP stack at **these same pins** so the two binaries agree. Read Zetta
only via the bridge — this mistake is why.

## Copies of public upstreams

Never `gh repo fork` — a fork of a public repository is public and cannot be made
private. Create with `gh repo create oramasearch/<name> --private`, push the upstream
history in, add `upstream` as a fetch-only remote, and verify visibility before pushing.
`k0s` was made this way.
