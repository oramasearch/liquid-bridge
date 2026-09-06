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

The Linux-only paths most worth a run first: the FUSE mount and Drip watcher tests, the node store (#202),
admission (#203), and the self-host wrapper (#59).

## What is deliberately not early

The forge, the IDE and the consumer drive are the most visible and the most tempting.
All three depend on the store, the graph and the daemon. Building them first is the
single most likely way this fails, and the Xi retrospective in liquid's research is the
cautionary example of converging every novel subsystem in the user-facing layer at once.
