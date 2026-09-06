# Phase 0 decisions

These gate Phase 1 of the [action plan](action-plan.md). Each is recorded here with
its options; the *chosen* option is recorded in liquid's `CLAUDE.md` under *Decisions
not to drift past* once made. Detail and evidence live in liquid's feature and research
docs — this page is the index, not the argument.

## 1. One store — **decided: no. Separate, by licence boundary.**

**liquid does not sit on Zetta.** liquid and liquify will be open source; Zetta is
closed / enterprise source-available; an open-source tool cannot depend on it. So liquid
has its own store. The earlier "converge via B" recommendation was made without this
constraint and is withdrawn.

**lake uses Zetta as much as possible.** lake is enterprise and builds on Zetta —
control plane, operational state, and its web-serving approach. Because lake must host
liquid repositories, it consumes liquid's store **as a library** for repository data.

**lake is deployed by the Orama operator, not a separate one.** `Lake` is a new CR on
`oramasearch/orama-operator` (renamed from `orama-cloud-v1-operator`), which already has
its own Zetta observed-state store: k8s/etcd is the source of truth for *desired* state
(the CRs); Zetta holds *observed* state, synced with anti-flap discipline. See its
`docs/zetta-datastore.md`.

## 2. One CRDT — **decided: `automerge-cpp`, and it stays open.**

MIT-licensed, public, already vendored by Zetta as a submodule. It is the shared *open*
component between liquid (open) and Zetta (closed). **Home decided 2026-09-03 (Steve): a private
copy under the org**, https://github.com/oramasearch/automerge-cpp, created from the full
`homer6/automerge-cpp` history (all tags, MIT preserved); `homer6` stays the public upstream.
liquid and Zetta pin the org copy; changes land there first and are pushed upstream deliberately.

## 3. One coroutine substrate — **decided**

**Boost.Capy for coroutines, Corosio for networking**, across liquid and lake — the
same stack Zetta and `oramacore-cpp` already use. stdexec, which liquid's docs had
named as an alternative, is not used. Recorded in liquid's `CLAUDE.md`.

## 4. TAAP content-addressed subjects

TAAP/1 subjects are key-derived identifiers. Documents, drips, changes and artifacts
are content-addressed and cannot hold keys. Attribution *about* them requires an
object-subject form in the spec — TAAP open question 22.3, which liquid's
`docs/features/25-identity-attestation-and-transparency.md` marks as **required and
blocking**. Suggested shape is recorded there.

This is a spec change, not a liquid design choice, and it needs the protocol owner.

## 5. Licence — **posture decided; text deferred (Steve, 2026-09-03).**

The licence text is chosen before either repository goes public, not before Phase 1 code lands:
no licence headers in Phase 1 files yet; the open-source release epic
(https://github.com/oramasearch/liquid-bridge/issues/16) gates on it.

| | Posture |
|---|---|
| liquid, liquify | **Open source, eventually.** Which licence is open. Must never depend on Zetta. |
| lake, orama-operator | **Enterprise.** |
| Zetta | Closed / source-available. |
| k0s | Apache 2.0 upstream; private copy with `LICENSE` + `NOTICE` + stated changes on distribution. |
| automerge-cpp | MIT — open, shared. |

## 6. lake's planes — **decided: control plane on Postgres (for now), data plane on Zetta.**

lake's operational and control state (accounts, organisations, the repository index, review
state, jobs) lives in a **Postgres** the operator provisions per `Lake` through its existing
CloudNativePG path — the same `<name>-controldb` pattern `OramaCloudV1` uses — on by default
(`spec.postgres`), reaching lake as `LAKE_CONTROL_DB_URI`. The **data plane** — the
content-addressed store, drips, search — is **Zetta**, provisioned per `Lake` as an owned
`OramaZettaCluster` (tracked on orama-operator). "For now" is deliberate: Postgres is a known
control plane today; moving control state into Zetta is a later, explicit decision.

## 7. Landing — **decided (Steve, 2026-09-03).**

Every issue ships as a pull request from its own branch (`docs/orchestration.md`). Claude merges
`liquid`, `lake` and `liquify` PRs after reviewing the diff and the proof; `orama-operator` PRs
(production) stay open for Steve to merge. The issue closes, with a comment, when its PR is up.

## 8. Lake control-plane backups — **decided (Steve, 2026-09-03): Cloudflare R2.**

CNPG's Barman object store to an R2 bucket, matching the operator's backup design
(orama-operator #33) and staying portable when lake moves to our own k0s. Tracked on
orama-operator #127; the bucket and its token are Steve's to create, delivered as a Secret in the
`lake` namespace, never through a prompt.

## 9. Phase 3 transport for REAPI — **decided (Steve, 2026-09-05): own HTTP/2 and protobuf on Corosio.**

**Question.** REAPI v2 is gRPC: HTTP/2 framing, protobuf messages, long-running operations.
liquid's networking is Corosio and the org's HTTP library (`oramasearch/http`) is HTTP/1 only.
Options, from liquid `docs/library/distribution.md` (The transport decision):

1. Depend on `grpc++` and `protobuf`: fastest to first contact; a very large dependency with its
   own threading model outside Capy and Corosio, and a code generator in every libliquid build.
2. Own HTTP/2 client on Corosio and an own protobuf codec for the REAPI message set: more work up
   front, coroutine-native behind the runtime boundary, liquid owns its transport (which #63 needs
   anyway) and the same HTTP/2 layer serves lake later.
3. A sidecar proxy that speaks gRPC on liquid's behalf: a second process and language, and stock
   compatibility depends on it being present.

**Recommendation.** Option 2, consistent with decisions 5 (Capy and Corosio), 7 (libliquid is the
product, Boost behind the boundary) and liquid's decision 8 (build the engine, do not adopt one).

**Status.** Decided: option 2. liquid owns an HTTP/2 client and server layer with gRPC framing
on Corosio and a protobuf codec for the REAPI message set; no `grpc++`, no `protobuf`, no code
generator. The transport is split into two liquid issues under #16 so both halves build in
parallel, and #16 itself integrates them and proves conformance against NativeLink and BuildBarn
in Docker. #63 follows #16.

## 10. Phase 6 starts now, in parallel — **decided (Steve, 2026-09-05).**

**Question.** The plan sequences lake to Phase 6, after the incremental engine and resolution
phases, and the bridge rule is that later-phase work waits. lake has not changed since
2026-09-03 (about 2,000 lines: the control surface, the Postgres control plane, telemetry, CI).

**Decision.** Run Phase 6 now on parallel capacity, all of it ("run it all"). The liquid-facing
leaves (push and pull, repository lifecycle, search over history, the drive, metering on stored
bytes) build against what liquid has (the store, the journal and sync framing, `remote_blob_source`,
the transport from Phase 3 as it lands); the identity, organization, policy, audit, secrets,
certificate and transparency-log leaves have no liquid dependency. Design first, as for Phases 2
and 3: lake `docs/design/phase-6.md`, then briefs, dispatched in waves that respect the small
codebase (identity core, authorisation, audit, push and pull with lifecycle, search, then the
rest). The Phase 4 and 5 rule stays: they wait for the Phase 3 exit.

## 11. Auth as a service — **decided (Steve, 2026-09-05): in scope now.**

lake authenticates its own users and organizations, and offers the same identity system to
applications deployed on it: per-application user pools, hosted sign-in pages, sessions and tokens,
user and organization management, all bound to TAAP identities. Built in Phase 6 alongside lake's
own authentication (lake #20's follow-up epic holds the application-facing surface).

## 12. Secrets-engine API — **decided (Steve, 2026-09-05): clean API only.**

A lake-native secrets, encryption and certificate API in the capability registry (REST, OpenAPI,
MCP), namespaced per customer with mounts per organization. No Vault-compatible surface; External
Secrets Operator support, if ever wanted, is an adapter issue later, not a design constraint now.

## 13. Compliance scope — **decided (Steve, 2026-09-05): SOC 2.**

The architecture is designed for SOC 2 from the start: a complete audit log of authentication,
authorisation decisions and every secret and certificate event; access reviews; change-management
evidence from the forge itself; encryption at rest and in transit. GDPR data residency and
regulated scientific or clinical data are out of scope for the design; nothing precludes them
later, and their consequences are opened as issues only when chosen.

## 14. liquify extension model — **decided (Steve, 2026-09-05): clean native plugin API first.**

A small stable plugin ABI over liquid's query graph, the same non-C++ boundary the specification
names for format codecs and language frontends; no VS Code extension API compatibility in Phase 4.
Compatibility can be added later as an adapter if demand proves it (liquify #7).

## 15. liquify editor buffer rendering — **decided (Steve, 2026-09-05): a retained GPU text layer inside Dear ImGui.**

SDL3 and Dear ImGui stay for the shell and panels; the editor buffer is a retained, GPU-rendered
text layer (glyph atlas, per-blob cached line layout) embedded in an ImGui window, for keystroke
latency and large files (liquify #2).

## 16. lake web UI visual direction — **decided (Steve, 2026-09-05): the Orama design system, as the website v2 and Zetta's web UI render it.**

Steve first asked for three mocked directions (lake #76, kept under `docs/design/ui/mocks/` as reference), then settled it: lake looks like `orama-website-v2` (PR 353's branch) and the web version of Zetta. Both compile their look from `oramasearch/orama-design` (DTCG tokens, IBM Plex, light surfaces, ink text, coral accent, semantic status). Lake vendors those tokens the way the website does (stamped snapshot, generated `/style.css`, a gate against hand edits) and follows Zetta's server-rendered `web_ui.cpp` as the structural template, since Zetta's web UI has the same architecture as lake's. The original wording follows for the record.

Lake's UI has to look good, not only work. Three directions are mocked as static pages of the same
three screens (repository home, change review, organisation) and put in front of Steve as
screenshots before any page is restyled: a quiet developer-tool register (neutral greys, one accent,
system type, light and dark), the Orama brand family (depends on decision 9 of liquid-bridge #9), and a
distinctive editorial identity. Steve picks; the design system then implements that direction across
every page (lake UI epic).

## 17. lake web UI stack — **decided (Steve, 2026-09-05): server-rendered pages plus progressive enhancement.**

Pages stay pure renderers unit-tested as strings, with one stylesheet built on a design-token
system and a small component set. JavaScript is added only as small vanilla islands where a page
needs them (file tree, diff viewer, review comments, command palette); no framework, no build step,
no second codebase. The API stays the only path to data; nothing on a page can do what the API cannot.

## 18. How lake obtains Zetta — **decided (Steve, 2026-09-05): link zetta-api as a client library.**

Lake links the zetta-api client and talks to the Zetta service the operator provisions per `Lake`
(decision 6). One implementation of the chunk store; Zetta stays a service; liquid stays Zetta-free.
Lake is private, so the dependency is contained there (lake #1, unblocks lake #53).

## 19. Zetta code and Codex workers — **decided (Steve, 2026-09-05): workers may read zetta-api.**

zetta-api is ordinary private code for the purposes of lake work: a Codex worker links the client from
the zetta-bridge checkout (`~/dev/homer6/orama-work/modules/zetta-bridge/modules/zetta`, the only place
Zetta is read from) and its headers pass through the worker's service like the rest of lake. Metis
material stays confidential and off every external service.

## 20. The dependency solver — **decided (Steve, 2026-09-05): liquid's own CDCL solver, from scratch.**

No vendored Clingo. liquid #25 builds its own CDCL solver with lexicographic optimisation and unsat-core
extraction over a liquid-specific encoding of the resolution dimensions; the resolution rules live in one
auditable C++ module on the runtime. Consistent with decisions 8 and 9 and with the store (no third-party
engines inside liquid). Spack-grade behaviour is the acceptance, measured by #75's 500-package universe.

## 21. Hardware signing stacks — **decided (Steve, 2026-09-05): own command layers over OS transports.**

liquid #81 speaks CTAP2 (FIDO2), PIV (smart-card APDUs) and TPM2 commands directly over the OS HID, PC/SC
and TPM device transports, with software doubles for tests. No libfido2, OpenSC or tpm2-tss in the signing path.

## 22. How a deploy reaches the cluster — **decided (Steve, 2026-09-05): through the operator's existing control plane, which is Zetta.**

Steve: "the operator already has zetta as its control plane... we can talk to that." The operator keeps its
control state in a Zetta node (`orama_control` database, `docs/zetta-datastore.md` in orama-operator). A
deployment is a row the operator reconciles from: `liquid deploy` writes it over Zetta's capability surface
with credentials the operator mints, the operator turns it into the per-environment resources it owns, and
status flows back the same way. Lake is not a second deployment control plane; it may mirror deployments
for its pages and audit (liquid #84, operator #124, k0s epic).

## 23. How liquid's store reaches each node — **decided (Steve, 2026-09-05): embed liquid on the node.**

A `liquid node-store` component runs on every node of the k0s `liquid` branch, holding the chunk store
and serving image roots to the container runtime; images carry an `io.liquid.tree` annotation naming
their tree. Nodes fetch only the chunks they lack (k0s #14).

## 24. The immutable node image base — **decided (Steve, 2026-09-05): bootc.**

Node images are bootable containers with atomic updates and rollback, produced by liquid's Phase 5 ostree
and bootc projections (k0s #16, liquid #78).

## 25. Distributed storage for the runtime — **decided (Steve, 2026-09-05): Longhorn.**

Replicated block storage on the nodes' disks under k0s, with snapshots and backups; lake's control
Postgres and customer stores take volumes from it (k0s #19).

## 26. Preview environment branching — **decided (Steve, 2026-09-05): template copy with a reflink fast path.**

An environment is a copy of a template repository and store; a metadata operation on reflink filesystems
(APFS, XFS, btrfs), a real copy elsewhere (liquid #87).

## 27. Hot update, tier 1 — **decided (Steve, 2026-09-05): an in-process `liquid-hot` library.**

Processes link a small runtime that receives rebuilt functions from the incremental engine and rebinds call
sites from inside the process; no debugger privileges, works in containers, opt-in (liquid #32).

## 28. Attestation verification at admission — **decided (Steve, 2026-09-05): a `liquid serve admission` component.**

The admission webhook is liquid, verifying with the same code as `liquid verify`; k0s configures the webhook
(k0s #15). No second implementation in Go.

## 29. Sealed secrets for Lake environments — **decided (Steve, 2026-09-05): liquid's own envelope.**

`liquid secret seal` produces a CBOR record encrypted with X25519 and ChaCha20-Poly1305 to the cluster's
public key; the operator unseals into Kubernetes Secrets through its own CRD; no kubeseal compatibility
(operator #129).

## 30. Where the agent edit API lives — **decided (Steve, 2026-09-05): libliquid from the start.**

Structural edits (rename symbol, extract, move, apply a tree edit) are public libliquid API over the
symbols and syntax queries, shared by agents, the CLI and liquify; liquify #8 consumes it (a liquid
companion leaf builds it first).

## 31. Multi-tenancy on the runtime — **decided (Steve, 2026-09-05): microVMs per tenant from the start.**

Customer workloads run in Kata or Firecracker microVMs on shared nodes, one tenant per VM boundary, with
admission verification from liquid (decision 28). Nodes need hardware virtualisation; the k0s `liquid`
branch declares the runtime class (k0s #21).

## 32. Timestamp and X.509 verification in liquid — **decided (Steve, 2026-09-05): own implementation, verification only.**

liquid #210 verifies RFC 3161 tokens and RFC 4998 evidence with its own strict DER reader, X.509 path
validation to pinned trust anchors, CMS SignedData, and verify-only RSA (PKCS#1 v1.5 and PSS) and ECDSA
P-256/P-384 over SHA-256/384, with RFC test vectors and real-TSA fixtures. No signing, no key generation,
no third-party library in the trust path.

## 33. Proof lanes — **decided (Steve, 2026-09-05): no Docker on Steve's machine, for anything in this project.**

Nothing in the workflow may run `docker` on the development Mac: no container-based Linux proofs, no
throwaway Postgres containers, no local image builds. Merges are gated on the macOS static and shared
suites run natively; lake's Postgres-backed suites run against the local Postgres 17 server with a fresh
database per run. Linux proofs run off-host: a Linux lane on the AKS cluster (`ci` namespace, sources
synced from the worktree, `codex-work/tools/linux-proof.sh`) now, and GitHub Actions per PR once the
`ORAMA_SUBMODULES_TOKEN` org secret exists. Until a Linux run has happened for a change, its issue says
"Linux proof deferred" and the change is listed in the action plan's verification debt. Images for the
cluster are built on the cluster and pushed from there.

## 34. How `liquid deploy` reaches the control plane — **settled 2026-09-06 under decision 22 (say so if you want a different answer).**

liquid never depends on Zetta or lake code. `liquid deploy` (liquid #84) talks to the control plane the
operator exposes (decision 22) through its documented REST `/v1` and MCP surface, with liquid's own HTTP
client (`oramasearch/http` over corosio). The contract is an OpenAPI document owned by orama-operator
(`docs/control-plane/openapi.json`); liquid vendors a copy with its digest under `contracts/` and tests
against recorded fixtures, so a contract change is a visible diff on both sides. Environments, rollbacks and
sealed secrets are operations on that contract; nothing in liquid links `orama_control` or zetta-api.

## 35. Admission on k0s: policy sets, events, and the binary on the node — **settled 2026-09-06 under decisions 23 and 28.**

liquid's admission service (#203) serves named policy sets loaded from a directory, each reachable at
`/admit/<policy>`; k0s maps namespaces to policy names in the webhook configuration (one cluster-scoped
webhook, `failurePolicy: Fail`; leniency is a property of a policy, for example an audit-only policy). liquid
has no Kubernetes client: a small k0s-side adapter turns liquid's structured decisions into Kubernetes events.
The service runs from the liquid binary already on the node (decision 23), as a static pod, not from a
published image. Tests use `liquid node-store serve` as the store double; `liquid serve sync` cannot answer
subject lookups.
