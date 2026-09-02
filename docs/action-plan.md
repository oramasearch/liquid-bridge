# liquid — action plan

Phases, in dependency order. **No durations** — a phase is done when its exit criterion
is met, and the exit criteria are things you can check, not things you can feel.

Each phase names the repositories it touches. The repository map is in
[`repositories.md`](repositories.md); the decisions that gate Phase 1 are in
[`decisions.md`](decisions.md). **Work is tracked as GitHub issues:** one epic per phase in
the repo that owns it, all linked from the tracking epic
https://github.com/oramasearch/liquid-bridge/issues/7 (decisions and follow-ups live here;
Phases 1–5 and 8 on `liquid`, Phase 6 on `lake` + `orama-operator`, Phase 7 on `k0s`).

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
chosen and why. The TAAP change landed in the spec.

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
  `oramasearch/orama-operator:lake-crd-8058ab5` (helm revision 8), **`Lake/prod`** (namespace
  `lake`, 3 replicas, 50Gi Postgres control plane with the schema applied) runs the lake image
  `oramasearch/lake:20260902` and answers at **https://lake.oramadev.net** (hello
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

**Repos:** `liquid`.

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

---

## Phase 2 — The build core

**Repos:** `liquid`.

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

---

## Phase 3 — Distribution

**Repos:** `liquid`.

- REAPI v2 compatibility so BuildBarn, BuildBuddy, NativeLink and EngFlow work unchanged.
- Build without the bytes as the only mode — outputs materialise on read.
- Toolchain in the input tree; local/remote racing with a cost model.
- `liquid replay <action>` reproduces any remote failure locally.

**Exit:** a Phase 2 build runs against a stock REAPI backend with the same cache hit
rate as local, and a deliberately non-hermetic action is caught at the read, not at the
remote failure.

---

## Phase 4 — The incremental engine

**Repos:** `liquid`, `liquify`.

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

---

## Phase 5 — Resolution and projection

**Repos:** `liquid`.

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

**Repos:** `lake`, `orama-operator`, `k0s`.

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

---

## Phase 7 — The runtime

**Repos:** `k0s` (`liquid` branch), `orama-operator`, `lake`.

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

**Repos:** all.

- **Multiplayer and agents:** private speculative replicas, semantic leasing, epoch
  compaction, agent attribution and scoped authority.
- **liquify beyond the graph:** the multiplayer surface, agent presence, the plugin ABI.
- **Hot update**, tiers 0–2, with restart as a first-class outcome.
- **Metis go-to-market:** the forward-deployed motion on an instrumented estate.

**Exit:** defined per item when Phase 7 is done. Do not plan these in detail now.

---

## What is deliberately not early

The forge, the IDE and the consumer drive are the most visible and the most tempting.
All three depend on the store, the graph and the daemon. Building them first is the
single most likely way this fails, and the Xi retrospective in liquid's research is the
cautionary example of converging every novel subsystem in the user-facing layer at once.
