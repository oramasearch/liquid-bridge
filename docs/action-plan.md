# liquid — action plan

Phases, in dependency order. **No durations** — a phase is done when its exit criterion
is met, and the exit criteria are things you can check, not things you can feel.

Each phase names the repositories it touches. The repository map is in
[`repositories.md`](repositories.md); the decisions that gate Phase 1 are in
[`decisions.md`](decisions.md). **Work is tracked as GitHub issues:** one epic per phase in
the repo that owns it, plus repository epics for cross-phase work, all linked from the
**master epic** https://github.com/oramasearch/liquid-bridge/issues/7. The structure, labels and
generator are in [`tracking.md`](tracking.md).

The ordering is forced by dependencies, not preference. The most visible products —
the forge, the IDE, the consumer drive — are the *payoff*, and every one of them depends
on the store, the graph and the daemon being right first.

---

## Phase 0 — Decide

**Repos:** `liquid` (docs), `zetta`, the TAAP spec.

Nothing in Phase 1 should be written until these are answered, because each is
expensive to reverse once a storage layer exists. Detail in
[`decisions.md`](decisions.md).

1. ~~One store.~~ **Decided: separate, by licence.** liquid (open source) does not sit
   on Zetta (closed). lake (enterprise) uses Zetta as much as possible and consumes
   liquid's store as a library. Control plane: Postgres (CNPG via the operator) for now;
   data plane: Zetta (`decisions.md` §6). lake is a `Lake` CR on orama-operator, which already has its own Zetta state store.
2. ~~One CRDT.~~ **Decided:** `automerge-cpp`, MIT, shared between liquid and Zetta.
   Only its canonical home is open.
3. ~~One coroutine substrate.~~ **Decided:** Boost.Capy + Corosio, matching Zetta
   and `oramacore-cpp`.
4. **TAAP content-addressed subjects.** Documents, drips and artifacts cannot hold keys.
   The spec needs an object-subject form. This blocks attribution of anything that is
   not an actor.
5. **Licence — posture decided.** liquid/liquify open source eventually; lake and the
   operator enterprise. Which open licence is still open.

**Exit:** each decision recorded in liquid's `CLAUDE.md` *Decisions* with the option
chosen and why. The TAAP change landed in the spec. No epic: the open decisions are listed on the
master epic (bridge #1, #2, #3, #8, #9).

**Status: the gate is lifted for hello-world scaffolding.** Decisions 1, 2, 3 and 5
are recorded; 4 (TAAP object subjects) is the one still needing the protocol owner and
does not block scaffolding.

---

## Phase 0.5 — Hello world, every component

**Repos:** all.

Before the store, before the graph: every module builds, runs, and shows *something*.
This proves the toolchain, the repo layout, and the cross-module wiring, and it is the
first thing anyone can look at.

- **liquid** — **done** (`400b718`). C++26 CMake + Ninja, Clang 17+ auto-selected as Zetta
  does, GoogleTest; `liquid version` and `liquid hello` run, one passing test. No Zetta
  dependency, ever.
- **lake** — **done** (`3f0d95a`). Same build shape; serves the hello page, `/style.css`
  and `GET /v1/server_info` over **Zetta's web-serving approach** (Beast2 on
  Capy/Corosio, one adapter TU, trailing 404), since lake builds on Zetta. Port 4900.
- **orama-operator** — a `Lake` CR (new, alongside `OramaCloudV1` and
  `OramaZettaCluster`) reconciles into a running hello deployment, first on our AKS
  cluster in a disposable namespace, then on k0s. Landed by PR — the operator is in
  production. **Deployed** 2026-09-02: the operator on AKS runs the PR #118 branch image
  `oramasearch/orama-operator:lake-crd-f4457e1` (helm revision 13), **`Lake/prod`** (namespace
  `lake`, 3 replicas, 50Gi Postgres control plane with the schema applied) runs the lake image
  `oramasearch/lake:20260902c` (control surface: REST `/v1`, OpenAPI, MCP, repositories, pages) and answers at **https://lake.oramadev.net** (hello
  page, `/v1/server_info`, JSON 404) through the shared nginx Ingress and an owned Cloudflare
  record. The `Lake` CR is image-agnostic: `pullSecretName`, `port`, `args`, `ingressEnabled`,
  `host`, `dnsSecretRef`.
- **k0s** — **done.** Our `liquid` branch builds (`go build ./cmd/k0s`); GitHub Actions
  are disabled on the private copy.
- **liquify** — **done.** Its own repo (`oramasearch/liquify`, private for now): a native,
  cross-platform window on SDL3 + Dear ImGui (Zetta's headed stack), `liquify version` and a
  `--smoke` self-test, one passing test. Not an editor extension.

**Exit:** `lake` answers HTTP, deployed by `orama-operator` from a `Lake` CR — on AKS
first, then k0s; `liquid version` prints; every module has a green build from a clean
clone. **Met on AKS 2026-09-02** (k0s deployment is Phase 7).

---

## Phase 1 — The store

**Repos:** `liquid`. **Epic:** https://github.com/oramasearch/liquid/issues/33.

- Content-defined chunk store — FastCDC, BLAKE3, packs with range fetch, the
  billion-entry index.
- Object model with **repository composition designed in** — nest, split, combine.
  This cannot be added later.
- CRDT metadata layer over the store, per the Phase 0 decision.
- **TAAP identity and signed drips** from the first commit. Attribution is not a later
  feature.
- Change capture: the VFS journal as primary, OS watchers as fallback, atomic-save
  detection, attribution of writes to actions.
- Garbage collection designed and implemented — leased roots, epoch marking, coupled
  lifetimes.

**Exit:** a repository can be created, written to, nested inside another, split out
again, and cloned lazily; every drip is signed; a 40 GB file and a 40-byte file are
handled by the same code path; GC reclaims space without corrupting a live checkout.

**Status: met on 2026-09-04.** Evidence, all merged on `oramasearch/liquid` with tests:
the chunk store with liquid's own index (#1), the repository over per-directory CRDT
documents with nest, split, combine and conflict values (#2, #3), signed drips and changes
under TAAP/1 identities with rotation (#4, #111), change capture with a reconcile backstop
(#5), the FUSE virtual filesystem and full checkout (#6), encrypted objects with
trust-domain keys, leaf-value encryption and rotation (#7, #52, #53), garbage collection
with leased roots and crash-safe compaction (#8, #46, #126), the 40 GB streaming test (#116),
secret scanning with verified redaction (#50), the simulation harness that found and fixed
the store's crash-safety bug (#55, #100), hash agility (#44), and the `liquid` command line
running the whole scenario as a test (#119). liquify opens a repository through the
library (liquify #15). The whole suite passes on Linux in the `liquid-linux-ci` container
with the mount test running for real (#130, #132); a lost-wake bug in `runtime::offload` and
the libfuse 3.14 argument handling were found there. Git interoperability landed (#43): a
5,497-commit repository imports directly into records in 11 minutes within 168 MB and exports
back to Git with `git fsck --strict` clean and identical trees; the store is 3.17× Git's
delta-compressed pack on that repository, tracked as #133. The updated automerge-cpp (its gap epic closed with fifteen PRs: upstream-compatible hashes
and chunks, checked apply, rollback, incremental and shallow loading, sync wire format, errors at
every boundary, a bidirectional fixture sweep against automerge-rs) is adopted (#136): checkpoints
are compact and open shallowly, drips carry commit metadata, remote changes yield patches.
Remaining on the epic: the offline CI job (#54, waiting on the org secret) and #133. Waiting on the org
CI secret: the offline test job (#54). Decisions taken along the way are in liquid's
`CLAUDE.md` and `docs/library/`.

---

## Phase 2 — The build core

**Repos:** `liquid`. **Epic:** https://github.com/oramasearch/liquid/issues/34.

The first shippable product, and the adoption path.

- Sandboxed action executor with **observed** dependencies.
- The three-tier cache — memory, disk, remote — with signed entries and read-only
  developer defaults.
- `liquid wrap <existing build>` for CMake, Autotools, Make and `compile_commands.json`.
- Reproducibility enforced by construction and verified by sampled re-execution.
- Provenance emitted as TAAP attestations for every action, automatically.
- Cache-miss explanation: `liquid why <target>` names the input that differed.

**Exit:** an existing CMake or Autotools project, unmodified, builds under
`liquid wrap` with correct caching across two machines, and every artifact carries a
verifiable attestation. Sampled re-execution detects an injected non-determinism.

**Status: in progress since 2026-09-04.** Merged: the sandboxed executor with observed
dependencies (#10; `include/liquid/build.hpp`, action and result records, observation by the
mount per pid, Linux namespaces, macOS `sandbox-exec`), proven by seven mount-backed tests in
the Linux container, the attestation profile registry (#62), the signed disk cache with
read-only publication and `why` on a miss (#11), and `liquid wrap` over CMake, Autotools, Make and
`compile_commands.json` fixtures with an exec-time hook serving cached compiles before the tool
starts (#12; a second checkout builds with every action served from cache), sampled
re-execution with quarantine of divergent results and `liquid verify` (#13; an injected
non-determinism is detected and never served), and a signed `slsa_provenance/1` attestation on
every result with `liquid provenance` and DSSE export (#14). In flight: `liquid why` (#15), the
configure fact base (#56), cost-aware eviction (#58), input-verification policy (#60), SBOMs
(#61); then observability (#57) and self-host (#59). The proof environment for anything mount-backed is
the container; macOS execution waits for macFUSE on a host.

---

## Phase 3 — Distribution

**Repos:** `liquid`. **Epic:** https://github.com/oramasearch/liquid/issues/35.

- REAPI v2 compatibility so BuildBarn, BuildBuddy, NativeLink and EngFlow work unchanged.
- Build without the bytes as the only mode — outputs materialise on read.
- Toolchain in the input tree; local/remote racing with a cost model.
- `liquid replay <action>` reproduces any remote failure locally.

**Exit:** a Phase 2 build runs against a stock REAPI backend with the same cache hit
rate as local, and a deliberately non-hermetic action is caught at the read, not at the
remote failure.

**Status: started 2026-09-05.** Design written first, as for Phase 2:
[liquid `docs/library/distribution.md`](https://github.com/oramasearch/liquid/blob/main/docs/library/distribution.md)
(the REAPI mapping of the Phase 2 records, build without the bytes as the only mode, hermeticity
at the read, toolchain as input and racing by a recorded cost model, replay, own workers, deltas).
The REAPI transport is decision 9 in [`decisions.md`](decisions.md), open and Steve's; #16 and #63
wait for it. Landed against a `remote_blob_source` interface with an on-disk double: build
without the bytes with hermeticity enforced at the read (#17), the toolchain as an input and
local/remote racing by a recorded cost model (#18), `liquid replay` (#19), attested delta delivery
(#64). Transport (decision 9): liquid's own HTTP/2 with gRPC framing over h2c and TLS with ALPN
(#155, with Corosio #3), a protobuf codec and the REAPI message set with byte-exact fixtures
(#156), and the REAPI client, remote cache tier and CAS server (#16).

**Exit: met on 2026-09-05; all Phase 3 leaves landed (#63 own workers in liquid#181, 2026-09-05).** The Phase 2 wrap fixtures build against NativeLink and BuildBarn in
Docker with local and remote hit rates of 100% on the second run, Bazel as a stock client gets a
remote cache hit against `liquid serve reapi`, and the deliberately non-hermetic fixture is refused
at the read, never reaching the backend (liquid #167, `tools/reapi-peers/run-reapi-interop.sh`).
Still on the epic: liquid's own scheduler and workers (#63), which the exit does not require.

---

## Phase 4 — The incremental engine

**Repos:** `liquid`, `liquify`. **Epic:** https://github.com/oramasearch/liquid/issues/36 (liquify's part: https://github.com/oramasearch/liquify/issues/13).

- The demand-driven query graph — fingerprints, red-green validation, early cutoff,
  durability tiers.
- The daemon. Graph stays warm; drips invalidate the minimum.
- Continuous clean-rebuild validation against incremental results.
- **liquify on the graph:** the native editor surface backed by liquid's query graph and VFS.
  Instant open of any repository at any size; diagnostics from the same graph the build
  uses, with no second parse.

**Exit:** a one-line change in a large C++ project recompiles one translation unit and
relinks in the time a save takes; the editor shows the diagnostic before the build
finishes; a comment-only edit rebuilds nothing.

**Status: started 2026-09-05 after the Phase 3 exit.** Design first:
[liquid `docs/library/incremental-engine.md`](https://github.com/oramasearch/liquid/blob/main/docs/library/incremental-engine.md)
(queries and actions as one mechanism, red-green validation with early cutoff and durability tiers,
the daemon and its fan-out, clean-rebuild validation, per-definition granularity behind a frontend
module, symbols and the planner, liquify in-process on the graph). Decisions 14 and 15 (a clean
native plugin API; a retained GPU text layer) are in `decisions.md`. Wave one: liquid #20 and #21,
liquify #4 and the shell half of liquify #1.

---

**Exit: met on 2026-09-05.** Comment-only edits rebuild nothing (liquid#20); a one-function edit
recompiles one translation unit and relinks in 496 ms on liquid's own tree (liquid#65, #187); the
editor shows the diagnostic 10 ms after the edit, before the relink (liquify#22); the persisted
graph validates on cold start in 780 ms with no executions and a clean rebuild of 3,753 targets
finds 0 divergences (liquid#191). Still landing under Phase 4: symbols as graph actions (#66), the cost-based
search planner over BM25F, the trigram index and scan (#67), inline build/test/deploy in liquify (#6,
on liquid#193's build event stream).

## Phase 5 — Resolution and projection

**Repos:** `liquid`. **Epic:** https://github.com/oramasearch/liquid/issues/37.

- Spack-grade constraint solver (ASP) with variants, virtual providers, compilers as
  dependencies, target architecture, and unsat-core explanations.
- Content-addressed outputs so an identical rebuild terminates the cascade.
- ABI extraction and diffing on every built library.
- Projection: OCI images (deterministic, computed layers), `.deb`, `.rpm`, `.apk`,
  Helm charts — Tier A (installable).
- The format registry with the first codecs: zip, tar, HDF5 (Tier 2), Parquet, SQLite.

**Exit:** a dependency tree of 500 packages resolves with a human-readable explanation
on conflict; a glibc patch that changes no output rebuilds nothing downstream; one build
projects to a working `.deb`, OCI image and Helm chart with pinned digests and attached
attestations.

---

## Phase 6 — lake

**Repos:** `lake`, `orama-operator`, `k0s`. **Epic:** https://github.com/oramasearch/lake/issues/11 (the operator's part: https://github.com/oramasearch/orama-operator/issues/130; going live: https://github.com/oramasearch/liquid-bridge/issues/17).

In this order, because each surface depends on the one before:

1. **Artifact registry and transparency log.** OCI distribution, ecosystem views, the
   tiled log with **mandatory witness quorum**, optional anchoring, debuginfod by
   build-id.
2. **Identity, secrets, PKI.** TAAP identities as the model; lake as OIDC issuer and
   attester; short-lived certs issued *to* TAAP keys; dynamic secrets; one CA.
3. **The forge.** Change-based review with cursors that survive rebase; no CI YAML —
   the build graph already knows.
4. **The `Lake` CR on orama-operator**, reconciling the whole service on k0s; the
   enterprise on-prem install path. Already provisions the control-plane Postgres
   (`spec.postgres`, CNPG); the owned Zetta data plane is next.
5. **Search.** oramacore-cpp BM25F plus the positional trigram index, indexed by blob
   once, change-atomic publication.
6. **Models and datasets.** The Hugging Face surface — training provenance attached to
   the same chunk store.
7. **The drive.** CFAPI, File Provider, FUSE; the three-tree reconciler; version history
   as a query.

**Exit:** a customer installs k0s and orama-operator on their own hardware, applies one
`Lake` resource, and has a private forge + registry + identity provider whose every
artifact verifies against a witnessed log — with no connection to `lake.live` required.

**Status: started 2026-09-05 in parallel with Phase 3 (decision 10).** Design first: lake
`docs/design/phase-6.md`; then the leaves in waves. Steve's three decisions are made
(decisions 11, 12, 13: auth-as-a-service in scope, a clean secrets API, SOC 2).

Landed by 2026-09-05: identity core (#14, #17), authorisation (#16, #19), audit (#18),
push and pull with repository lifecycle (#12, #13), search (#6, #9), the customer data
plane (#22, #24), PKI with ACME, SSH certificates, caller attestation and break-glass
(#26, #27, #28), the forge's issues, reviews, releases and webhooks (#30, half; enforcement
at the reference update waits on liquid #177), forge export and GitHub import (#31, #32).
Along the way the Postgres store stopped reading `LAKE_INSTANCE_KEK` from the process
environment after startup (lake#68).

Landed 2026-09-05: TUF roles (#34), the log's three modes (#35), RFC 3161 timestamps (#36), tiled
monitoring (#37), replication (#38), per-session agent keys (#39), hash tiles and compact proofs (#88),
search over history (#41), metering and quotas (#33), models and datasets with the Hub surface (#7), auth
as a service (#51), the forge complete with per-reference push outcomes (#30, #71), the drive's sharing and
models read surfaces (#74), process-unique test fixtures (#86), and the web UI on the Orama design system
(#75: #76 mocks, #80 the system on every page, #89 the forge pages; decisions 16 and 17). Running: the
drive web surface (#43, #44), the settings surface (#91). Blocked: #53 on Zetta's service blob API (zetta
#1005), #42 on Phase 5's format registry, #45 on liquid #195. Deployment (2026-09-05): lake `20260905a` runs on AKS at lake.oramadev.net with the control plane, the
instance key (operator #135), a 100 GiB store volume (operator #137, `fsGroup` from #138) and the log in
air-gapped mode; the operator runs `lake-crd-58bf1b8` from `feat/lake-crd`, the schema is applied, and
repository pages render. Operator PRs #131, #133, #134, #136, #137, #138 are merged into `feat/lake-crd`.

---

## Phase 7 — The runtime

**Repos:** `k0s` (`liquid` branch), `orama-operator`, `lake`. **Epic:** https://github.com/oramasearch/k0s/issues/18.

- Chunk-aware node integration: nodes fetch only chunks they lack, across images.
- Deploy on drip, driven by the fan-out rather than a CI trigger.
- Attestation verification at admission: what runs is what was attested.
- Preview environments per change, cheap because images share chunks.
- Talos-style immutable node model on top of k0s, with a real break-glass path.

**Exit:** a drip in a repository produces a running preview environment, and the
environment's image differs from the previous one by only the chunks that changed;
an unattested image is refused at admission.

---

## Phase 8 — The rest

**Repos:** all. **Epic:** https://github.com/oramasearch/liquid/issues/38.

- **Multiplayer and agents:** private speculative replicas, semantic leasing, epoch
  compaction, agent attribution and scoped authority.
- **liquify beyond the graph:** the multiplayer surface, agent presence, the plugin ABI.
- **Hot update**, tiers 0–2, with restart as a first-class outcome.
- **Metis go-to-market:** the forward-deployed motion on an instrumented estate.

**Exit:** defined per item when Phase 7 is done. Do not plan these in detail now.

---

**Deployment 2026-09-06.** lake `oramasearch/lake:20260906a` (lake main b51c69e) is live on AKS behind
https://lake.oramadev.net with the design system, sharing, settings, platform pages and hashed assets; the
operator runs `oramasearch/orama-operator:main-57e0cf7` (main after PR #118 and the follow-ups #144, #146,
#147), the `PostgresSchema` job re-applied the vendored schema (sha256:9ed41771), and the store volume and
instance key were reused. Both images were built on the cluster's BuildKit from this machine with `buildctl`
(no Docker here; the `/liquid-dev` skill records the procedure). `BackupReady` stays False until the R2
backup Secret exists.

**Deployment 2026-09-07.** lake `oramasearch/lake:20260907a` (lake main with liquid at the store backend
interface, structural diff and merge, and committable conflict values) is live at https://lake.oramadev.net,
reconciled by `oramasearch/orama-operator:main-57e0cf7`. The vendored schema is unchanged, so no schema job
was needed. `BackupReady` stays False until the R2 backup Secret exists.

**Deployment 2026-09-08.** lake `oramasearch/lake:20260908b` (lake `main` at `4e8216b`, "Present Lake's
customer repository journey") is live at https://lake.oramadev.net, reconciled by
`oramasearch/orama-operator:main-996567a` — the renamed operator, now the only one reconciling `Lake`;
the former `orama-cloud-v1-operator` release is scaled to 0 pending its helm removal. The `Lake/prod` CR
reports `Ready`, `StoreReady` and `ZettaReady` true and `BackupReady` false (the R2 backup Secret still does
not exist). The control database carries 21 applied migrations, `0001_identity_and_customers` through
`0021_token_attenuation`, matching `db/schema.sql`; `0003` was never used and is absent from both. liquify's
dmg was rebuilt from `0424822`.

**Deployment 2026-09-08 (second roll).** lake `oramasearch/lake:20260908c`
(`sha256:bcbef30ac66ec89cd28dd9bc68d87553cb4e605e068633fd0efd3db053b3a06f`), built on the cluster's
BuildKit from lake `main` at `9403194`, is live at https://lake.oramadev.net. It is **the first lake
image that reports its own source revision**: `GET /v1/server_info` returns
`"revision":"9403194f4d7db225e9f909c94fcbd5d2aad64380"`, and the image carries
`org.opencontainers.image.revision`. `Lake/prod` reports `Ready`, `StoreReady` and `ZettaReady` true,
`BackupReady` false. The schema was unchanged since `4e8216b`, so no schema Job ran. Recorded in
lake `docs/deployment/production-2026-09-08.md` (lake#121, lake#142).

**Deployment 2026-09-26 (later): SQLite, DuckDB and Polars, and Zetta parity phase 2.** Wrapper
services `oramasearch/lake-sqlite`, `lake-duckdb:0.1.0`, `lake-polars:0.1.0` (each its own private
repo and private image, anonymous Hub 404); operator `main-b21b7e2` (release revision 10: DuckDB and
Polars reconciler orama-operator#181, schema re-vendor #182); schema `0027_analytics_services`
Applied (`sha256:0e10ab133613`). The first attempt stuck the `PostgresSchema` Job: re-applying the
whole file re-added migration 0025's `service_kind_check` while `sqlite` rows existed, so older
re-adds are now `NOT VALID` (lake#203). lake `20260926l` (`44f068e`: kinds lake#203, data parity
lake#204). Verified: `services.mjs sqlite duckdb polars` exit 0 with real queries and refused
escapes (lake#207). Then lake `20260926m` (`618ff3a`, Title Case nav and headings, lake#206),
rolled on Steve's go-ahead; `tools/e2e/walkthrough.mjs` passed all 32 steps after it.

**Deployment 2026-09-26: managed services and the service catalog (decisions 46, 47).** In order:
operator `main-4c73fbc` (services reconciler, orama-operator#173/#174; Lake CRD first, release
revision 5), `Lake/prod` `spec.services` enabled with `zettaImage: oramasearch/zetta:dev-f84ab6f`,
schema `0024` applied, lake `20260925i`/`j`; then the upstream operators from the helmfile
(`tier=service-operators`, orama-operator#176), operator `main-a93dd44` (catalog kinds, #177, revision
6), schema `0025`, lake `20260925k` (`7f27e6f`). The Altinity operator had to be told to watch every
namespace (#178). The decision-45 workspace was adopted as the default Zetta service with its data.
Verified in the browser: the walkthrough (project → pipeline → approve → run, run report loads,
zetta#1007 fixed) and every catalog kind created, Ready, connected and deleted from Services —
Postgres, Zetta, Kafka (2 min), ClickHouse (2.5 min), Valkey (1.3 min), TiDB (3 min), Cassandra
(8 min). Node memory 58% with no services running.

**Deployment 2026-09-25 (third roll): Design, Train and Ship on per-customer Zetta workspaces
(decision 45).** Operator `oramasearch/orama-operator:main-04dafde` (orama-operator#171, release
`orama-operator` revision 4, Lake CRD applied first) provisions a Lake-owned `OramaZettaCluster` per
customer from `orama_control.workspaces` on the Lake's data plane; `Lake/prod` has
`spec.workspaces.enabled: true`, which turned on `provisionOperatorSchema` for `lake-prod-zetta`.
lake `oramasearch/lake:20260925h` (`sha256:b483687100112bd2de56e506f64df4a758bdb301b96d77f53c6916e27afb04ef`,
lake `3a3bab1`; lake#152–#157) serves the pages. Exercised end to end in a browser with
`tools/e2e/walkthrough.mjs` (lake `docs/deployment/browser-testing.md`): Clerk sign-in with a
one-time ticket, workspace `prod-ws-6bb777ba498a` provisioned for the gmail tester's customer, a
project created, a pipeline built (capture then compile), approved, checked and run to `succeeded`,
and `churn_model` listed under Ship. Found and fixed on the way: Zetta SQL takes one predicate per
`WHERE` (lake#153), the workspace image requires `compile_intent`'s `input_id` (lake#154), plans
need approval before `gate` (lake#155). Open: `get_run_report` never answers
(https://github.com/oramasearch/zetta/issues/1007); lake times reads out at 15 s.

**Deployment 2026-10-12: the first releases. lake v0.1.0, zetta v0.2.0, liquid v0.1.0.** Three
repositories were tagged for the first time (zetta for the third), each with a GitHub release and
release notes under its `docs/releases/`, and the cluster was rolled to the tagged source:

| | Git tag | Image deployed | Release tag on the image | Digest |
|---|---|---|---|---|
| lake | `v0.1.0` (`2e6f6d7`) | `oramasearch/lake:20261012a` | `oramasearch/lake:v0.1.0` | `sha256:5076598b9bf06bce175588359c466d0c740a87df90e1973d939a2458f728a8ad` |
| zetta | `v0.2.0` (`4015ef7`) | `oramasearch/zetta:main-4015ef76` | `oramasearch/zetta:v0.2.0` | `sha256:46597d1997d1b373c7d4c781ec2c048d9aa5435d32bcfc616467588c6c1e74a6` |
| liquid | `v0.1.0` (`f669726`) | compiled into the lake image | none (no image) | |

lake was built on the cluster's BuildKit from lake `main` at the tag, with liquid at this bridge's
pin `f669726` and the Zetta client transport from `2cfdac2`. `GET /v1/server_info` reports
`"version":"0.1.0"` and `"revision":"2e6f6d72520e96869a229a134313cc16a81b015f"`; the deployed
OpenAPI lists 554 paths. There was no schema change since `20261011u`, so no schema Job ran and
the operator was not touched (`oramasearch/orama-operator:main-61ccfef`). `Lake/prod` reports
`Ready`, `StoreReady` and `ZettaReady` true, `BackupReady` false (unchanged).

zetta was built from a clone at the tag and rolled to both image fields of `Lake/prod`
(`spec.zetta.image` and `spec.services.zettaImage`): the bus `lake-prod-zetta-zetta-0` and the
three workspace Zettas restarted once each, with no container restarts after, and each logs
`zetta 0.2.0: node started`. While the bus restarted, lake answered 503 on
`/v1/receive_agent_tasks` for about a minute (81 responses), then recovered without action.

Each release tag in Docker Hub names the digest the running pod reports; it was added through the
registry API with `retag-image.py`, not by rebuilding. Both repositories still answer 404 to an
anonymous request. The steps are now in the `liquid-dev` skill (*Release images*) and in each
repository's `CLAUDE.md` or release conventions.

**Deployment 2026-09-25 (second roll): Clerk sign-in, schema `0023`, operator cutover.** In order:
the operator CRDs were applied server-side (additive only; all 70 CRD UIDs unchanged); the live
Helm release `orama-operator` was upgraded to `oramasearch/orama-operator:main-83c6d90`
(`sha256:95f512673a17246cd59b247533a49a3c003e6bb5b4ca7722bac6665c64dd4037`, orama-operator#170,
revision 3), which applied lake schema `0023_custodial_identities` itself (PostgresSchema
`sha256:929f2f3cf54c` Applied); the half-finished rename cutover was completed by retiring the
former release `orama-cloud-v1-operator` with `helm uninstall --keep-history` after confirming no
workload, ConfigMap, Secret or CR named its control-plane Service (Lease and CRD UIDs unchanged, one
Lease holder); then lake `oramasearch/lake:20260925b`
(`sha256:95fef8a25ec6ac4703485063bac44596fe7dd0ce78c8c14ea18424538a173d71`, lake `c045b96`, lake#148)
was rolled with `LAKE_CLERK_PUBLISHABLE_KEY` for Clerk application `lake`. `GET /v1/server_info`
reports `"revision":"c045b96f75b429be3f06005e91dc347ffd2a9311"`. A real Clerk `lake` template token
minted through the Backend API was exchanged at `/identity/clerk-session` and signed in to
`/repositories`; it linked to the existing `steve@orama.com` account. The test sessions were then
signed out and revoked. Decisions 43 (amended) and 44.

**Deployment 2026-09-25.** lake `oramasearch/lake:20260925a`
(`sha256:3f9a97c98c13f3a95d781a99233e140a67fb296e9618fdadca857f99397ff033`), built on the cluster's
BuildKit from lake `main` at `8d5e19b` with liquid at the bridge pin `aa60e87`, is live at
https://lake.oramadev.net. `GET /v1/server_info` returns
`"revision":"8d5e19bcddd578b59dd14d70fbb0ef3c3b27df9c"`. It carries the first part of the cloud
design (https://github.com/oramasearch/liquid-bridge/issues/30, lake#147): the home page "Design,
train, and ship AI on your own data", the sidebar regrouped with Ship > Deployments, the account menu,
route-keyed navigation, `GET /deployments`, and Files as the first repository tab. `Lake/prod`
reports `Ready`, `StoreReady` and `ZettaReady` true, `BackupReady` false (unchanged). No schema
change, so no schema Job ran. It is the first image since lake#145 made liquid a named build context;
liquid's own `.dockerignore` emptied that context on the first attempt, and the `liquid-dev` skill now
says to pass a clean copy.

Until `20260908c`, nothing in the running system recorded which source commit an image was built from — no
OCI `org.opencontainers.image.revision`, no build annotation, and `/v1/server_info` reported only
`version 0.0.1` — so `20260908b`'s commit is recorded by hand rather than verifiable from the artifact.
lake #121 closed that; every image from `20260908c` onward answers for itself.

**Runtime, from 2026-09-06 (decision 36).** lake runs on AKS; the k0s distribution is complete and its
single-node validation waits (k0s #13). Phase 7's exit is met on AKS: the `Lake` CR reconciles, the service
answers, and the distribution carries the node store, admission with transparency-log verification, the
platform surface, the immutable node model and the install automation.

## Verification debt (decision 33)

Since 2026-09-06 nothing in the workflow runs Docker on the development machine (`docs/decisions.md` §33).
Merges are gated on the macOS static and shared suites run natively; lake's suites run against the local
Postgres 17 with a fresh database per run. Every change below merged with "Linux proof deferred" on its
issue and needs one Linux run before the next release tag: on GitHub Actions once the
`ORAMA_SUBMODULES_TOKEN` org secret exists, or on a Linux lane off this host.

- liquid: #210 (PR #218), #85 (#224), #202 (#228), #25 (#229), #26 (#215), #204 (#220), #195 (#209),
  #51 (#234), #203 (#227), #205 (#223), #29 (#212), #59 (#233), and every later merge until the lane exists.
- lake: #44 (#100), #91 (#101), #98 (#102), #83 (#103): the Postgres-backed suites ran on the local server;
  the linux/amd64 image builds those briefs asked for did not run.
- k0s: #20 (#28): the container lifecycle suite did not run; unit tests and shellcheck did.
- orama-operator: #129 (#139), #128 (#140): Go build, vet and tests ran; no cluster rehearsal.

The merge verifier builds liquid without a build type (unoptimised); workers build Release. liquid #263 (the
resolver's 500-package test crashing only under optimisation) showed that gap: until it is fixed and a Release
run is part of the gate, a green chain does not prove the optimised binary.

The Linux-only paths most worth a run first: the FUSE mount and Drip watcher tests, the node store (#202),
admission (#203), and the self-host wrapper (#59).

## What is deliberately not early

The forge, the IDE and the consumer drive are the most visible and the most tempting.
All three depend on the store, the graph and the daemon. Building them first is the
single most likely way this fails, and the Xi retrospective in liquid's research is the
cautionary example of converging every novel subsystem in the user-facing layer at once.
