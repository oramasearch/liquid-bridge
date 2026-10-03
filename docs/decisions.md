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

Feedback drafted in [`taap/`](taap/README.md) (`01-content-addressed-subjects.md` for this item, bridge #1;
`02-protocol-feedback.md` for bridge #8); delivery is Steve's.

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

## 36. Where it runs for now — **decided (Steve, 2026-09-06): AKS, with k0s later.**

lake.live and the Lake CR run on the AKS cluster (`orama-production-cluster-01`) for now. The k0s
distribution keeps everything that landed for it (the node store, admission with transparency-log
verification, the platform surface, the immutable node model, the runbooks and the single-node install
automation), but the single-node validation run (k0s #13) waits until Steve chooses to do it; it does not
block a phase exit or the plan's completion. bridge #13 is answered the same way: AKS first, the on-premises
path stays ready and unproven until then. Revisit when a customer needs the self-hosted install or when
lake.live outgrows the single AKS node.

## 37. Authenticated time on a transparency checkpoint — **decided (Steve, 2026-09-07): a signed `issued_at` in the checkpoint body.**

liquid's admission policy documents `max_checkpoint_age_seconds` and lists `checkpoint stale` as a refusal
reason, but the signed checkpoint body carried no issuance time, so no finite bound could ever be enforced: a
product review admitted a Pod against a checkpoint with a one-second maximum age (liquid #290). Freshness is
kept as a security property, and the log states its own time.

The checkpoint body gains an `issued_at` field — seconds since the Unix epoch, UTC — inside the bytes the log
already signs, so it needs no new signature scheme and no second credential. lake, as the log, emits it on
every checkpoint it publishes; liquid's admission verifier compares it against the configured bound.

The semantics, so that neither side has to guess:

- **Absent bound** — freshness is not enforced, and a checkpoint without `issued_at` is accepted.
- **A positive bound** — freshness is enforced, and a checkpoint without `issued_at` is **refused**
  (`checkpoint stale`). Fail closed: an operator who sets a limit gets the limit, not a silent pass.
- **A zero bound** is rejected when the policy loads, rather than meaning "refuse everything" or
  "enforce nothing" — both readings are traps.
- **Future-dated checkpoints** beyond a small skew allowance (60 seconds) are refused, or a clock set forward
  would make a checkpoint permanently fresh.

The known limit, written down deliberately: the log vouches for its own clock, so this defends against a stale
or replayed checkpoint, not against a log that lies about when it signed. Binding an RFC 3161 timestamp token
to the checkpoint is the stronger form and stays available — liquid already verifies RFC 3161 (decision 32) —
and it is not adopted now because it requires a reachable timestamp authority at publish time, which an
air-gapped log cannot assume. Revisit if a customer needs time attested by someone other than the log.

Old checkpoints published before this change carry no `issued_at` and therefore cannot satisfy a finite bound;
that is the intended migration, not a regression. Producer: lake. Consumer: liquid admission.


Issue: https://github.com/oramasearch/liquid-bridge/issues/23

## 38. Who may write Secrets in a liquid environment — **decided (Steve, 2026-09-07): RBAC is the control, admission is defence in depth.**

The k0s platform contract said a delivered Secret carries controller ownership and
`lake.orama.cloud/sealed=true`, and the consuming Pod carries a derived
`liquid.oramasearch.com/sealed-secret-names` annotation. The `liquid-environment-secrets`
ValidatingAdmissionPolicy checked that those fields were **present**, never that they were **true**:
an envtest reproduction with a non-admin identity admitted a Secret whose `ownerReference` named a
`LakeSealedSecret` that does not exist, and admitted the Pod that mounted it on a hand-written
annotation (k0s #40). The advertised guarantee — Secrets in a liquid environment are
sealed-secret-derived and operator-delivered — was unenforced, and that is why orama-operator #155
could not be fixed on the operator side: the fields that would make delivery work make forgery work
too.

**Only the operator's service account may create or modify Secrets in namespaces labelled
`liquid.oramasearch.com/environment=true`.** Tenants lose direct Secret write in those namespaces;
"operator-delivered" becomes true by construction rather than by assertion. The admission policy
stays, as a second layer that catches a mistake by an authorised writer — not as the control.

CEL admission cannot readily verify that a claimed owner object exists, so a policy-only answer
would need a paramKind, an authorizer check or a webhook, and might not be expressible at all.
RBAC is enforceable today and closes the hole immediately.

Each control's boundary is written down where it is configured, so neither is assumed to be doing
the other's job: k0s `docs/liquid/platform-surface.md` states what RBAC guarantees and what
admission guarantees, and which is authoritative. The operator's delivery path lands against the
corrected contract. Revisit if a tenant workflow genuinely needs to write its own Secrets in an
environment namespace — that would be a change to this boundary, not an exception to it.


**Implementation note (2026-09-07, after a first attempt).** Two facts constrain how this is
expressed, and the first attempt at it stopped on them, correctly. Kubernetes RBAC is **additive**
— an operator-only grant cannot revoke access conferred by some other binding — and RBAC rules
**cannot select namespaces by label**, so "namespaces labelled
`liquid.oramasearch.com/environment=true`" is not a thing a Role can say. The boundary is therefore
expressed the other way round: the distribution's tenant profile
(`static/manifests/liquid/tenant-namespace/profile.yaml`), which the operator instantiates per
environment namespace, carries the **only** grant a tenant identity gets there, and that grant
omits Secrets. "Only the operator writes Secrets" then holds by construction rather than by
subtraction.

Today that profile ships a Namespace, a NetworkPolicy and a ResourceQuota and **no RBAC at all**,
so no tenant identity can currently write Secrets in an environment namespace. The forgery
reproduced in k0s #40 shows the admission policy does not enforce its claim; it does not show a
live exploit, because nothing grants a tenant the access to attempt it. The hole becomes real the
moment tenant access exists — which is exactly what the platform surface (k0s #17) will add — so
the boundary lands with, or before, that grant.


Issue: https://github.com/oramasearch/liquid-bridge/issues/24

## 39. liquid's own filesystem projection — **decided (Steve, 2026-09-08): write our own macOS, Linux and Windows backends; no FUSE library dependency.**

`liquid wrap` observes a build through a mounted filesystem, and the only backend today is
`src/vfs/fuse_fs.cpp` against libfuse3 on Linux and macFUSE on macOS. That is a licence problem
before it is a portability problem: **macFUSE is not licensed for what we need**, and libfuse is
LGPL, which constrains static linking and the licence liquid may itself choose (bridge #2) before
the open-source release (bridge #16). It is also why Phase 2's exit cannot be demonstrated on this
Mac at all: no macFUSE, no `wrap`, no proof (liquid #291, #299).

liquid implements its own projection per platform, behind the interface `fuse_backend` occupies
today. The surrounding ~780 lines — hydration, materialisation, the serialized request queue,
xattrs, observation — are already platform-independent and stay as they are; only the backend is
replaced.

- **Linux** — speak the FUSE **kernel protocol** directly on `/dev/fuse`. The protocol's uapi
  header is dual BSD/GPL precisely so independent userspace implementations exist; this needs no
  libfuse and inherits none of its terms.
- **macOS** — no kernel extension. An **NFS loopback server**: macOS's NFS client is in the kernel
  already, so a userspace server on localhost gives a real mount with nothing third-party
  installed, on every macOS version. FSKit is the newer Apple-sanctioned route and is worth taking
  where the minimum OS allows it, but it cannot be the only path.
- **Windows** — **ProjFS**, the Projected File System built into Windows. Not WinFsp, which is
  GPLv3.

The prize is not only licence hygiene: it removes an install prerequisite that has blocked
demonstrating Phase 2 and Phase 4, makes `wrap` work on a clean machine, and puts Windows on the
same footing as the other two rather than being a permanent exception.

The risk is that a filesystem is a hard thing to write and correctness failures are silent and
data-shaped. Each backend lands with the same conformance suite run against it, and the existing
libfuse backend stays available behind a build option until its replacement passes that suite on
its platform. Revisit if a platform's own facility (FSKit, ProjFS) turns out to be insufficient for
observed builds, which would be a finding worth recording rather than working around.



**Alternatives examined (added 2026-09-08, after the decision — they should have been weighed
before it).** The decision above replaced the FUSE *library* while preserving the choice of a
*filesystem* as the interception point, and did not examine whether interception has to be a
filesystem at all. Recorded now so it is a considered position rather than an inherited one.

- **OS watchers alone (inotify/fanotify, FSEvents, USN journal).** Rejected, and already the
  documented fallback rather than the mechanism (`docs/features/22-change-capture.md`). Watchers
  report that a path *changed*, after the fact; they cannot observe **reads**. A build cache is
  keyed on what an action read, so a watcher-only design guesses its input set and every cache hit
  is unsound. inotify queues overflow and FSEvents coalesces under exactly the load a build
  creates — liquid #282 is this failing in practice, all through the 2026-09-07 session.
- **Syscall interposition (`LD_PRELOAD`, `DYLD_INSERT_LIBRARIES`).** Sees reads, needs no mount and
  no kernel interface, and would be far less work than three filesystem backends. Not adopted
  because the coverage has holes we cannot close: statically linked binaries and anything not
  calling through libc escape it, and macOS SIP blocks injection into protected binaries — so a
  build that shells out to a system tool is unobserved, silently. An unsound cache entry is worse
  than a slow one.
- **`ptrace` or eBPF.** Accurate and complete on Linux, but Linux-only, slow enough to matter on a
  build's syscall volume (`ptrace`), or privileged (eBPF). Neither gives macOS or Windows.
- **Declared inputs, Bazel-style.** The correct answer for a build system that owns its own build
  files, and unavailable here: liquid's premise is wrapping an **unmodified** CMake or Autotools
  project, so there is nothing to declare with.

The filesystem is kept because it is the only mechanism that observes reads, covers every process
regardless of how it was linked, and has an equivalent on all three platforms. The cost is that we
write three backends; the alternative costs correctness we cannot verify.

Issue: https://github.com/oramasearch/liquid-bridge/issues/25

## 40. What happens when someone signs up for lake — **decided (Steve, 2026-09-08): sign-up provisions a personal customer they own.**

lake's `/sign-up` creates a user, an identity document, a credential and a session, then redirects
to `/sessions`. It creates **no customer and no ownership grant**, and `create_customer` requires
global administrator access, which ordinary users are explicitly denied. So there was no path from
sign-up to a first repository at all, however clearly the page was written — a product review
stopped on exactly this (lake #119), and the onboarding fix could not proceed without an answer.

**Signing up creates a customer owned by that user**, so a newcomer lands somewhere they can
actually work. That is what lake.live is for (bridge #17); a hosted service whose sign-up form
leads nowhere is not a hosted service.

What this decision commits us to, stated rather than discovered later:

- **Anyone who signs up creates a billable tenant.** Metering is on unique stored bytes (lake #33),
  so an empty personal customer costs nothing, but the tenant exists and is counted.
- Naming, default quotas and the interaction with metering need settling as part of the
  implementation, not after it.
- Ownership is the grant the review found missing: the user owns the customer, which is what makes
  the first repository reachable.

**The cost:** open self-service provisioning is an abuse surface — unbounded tenant creation by
anyone who can reach the page. It is accepted for now because lake.live is not yet public and the
sign-up form already requires a client-held TAAP identity, which is a meaningful barrier to casual
abuse.

**Revisit if** lake.live opens to the public without another control in front of it, or if tenant
creation turns out to cost anything before a byte is stored. An allowlist gate was considered and
deliberately not adopted now, on the grounds that it becomes a thing to operate.

Issue: https://github.com/oramasearch/liquid-bridge/issues/26 · implements in lake #119

## 41. What the filesystem conformance suite is calibrated against — **decided (Claude, 2026-09-08, unblocking; say so if you want it the other way): a direct in-process backend is the reference, and the libfuse-on-Linux baseline stays owed.**

Decision 39 says each of the three new backends lands only once it passes one conformance suite.
liquid #301 builds that suite, and it was written to be **calibrated against the existing libfuse
backend on Linux** — a known-good reference, so the suite is trustworthy before it judges a
replacement. That is the right instinct and it does not survive contact with the machines we have.

The #301 worker built the suite — nine cases covering named-backend selection, recorded-tree reads,
attributed writes, mutation, xattrs, synthetic times, read-only refusal and partial hydration — and
**all nine skipped**, because macFUSE is absent here. There is no Linux host with `/dev/fuse`
available: the AKS BuildKit worker has no `/dev/fuse`, the Linux machine at `192.168.123.175` times
out, and CI dies at submodule checkout (liquid #291, #299). So the suite has no baseline, cannot be
shown to fail, and #301 stopped without a PR — correctly. Three more issues (#302, #303, #304) sit
behind it.

The reference becomes a **direct in-process backend**: the suite's backend registry gains an entry
that dispatches operations straight to the platform-independent layers — `hydration`,
`materialise`, `request_queue`, `xattrs`, `observation` — with no kernel mount anywhere. Those
~780 lines are what every kernel backend serves, so they are the thing the backends must agree
with. It runs on any host, including this Mac and CI, which means the suite gets a real baseline
and the deliberate-failure demonstration that proves it has teeth.

What this gives up, stated plainly: a suite calibrated against our own core can bless a bug that
lives in the core, where libfuse — third-party, widely exercised — would not. That is a real loss
and it is why **the libfuse-on-Linux baseline remains owed, not cancelled**. It is recorded as
outstanding in `docs/library/vfs.md` and runs the day a Linux lane exists (liquid #299). Until
then, a kernel backend passing the suite means "agrees with liquid's own core", which is weaker
than "agrees with a known-good filesystem" and must not be written up as the stronger claim.

The alternative was to leave #301–#304 blocked on a host nobody has scheduled. Between a weaker
baseline that exists and a stronger one that does not, the suite that runs is worth more —
provided the weakness is written down, which is what this entry is for.

Issue: https://github.com/oramasearch/liquid-bridge/issues/28


## 42. Where liquid is pinned for lake and liquify — **decided (Steve, 2026-09-09): this bridge holds the one pin; neither repository vendors liquid.**

lake and liquify each carried liquid as their own `modules/liquid` submodule while this bridge
also pinned it. That is three pointers at one repository, and they drifted: lake pinned
`8203911` while the bridge pinned `aa60e87`. Nothing reported the disagreement — each repository
built green against a different liquid.

Both submodules are removed. Each build resolves liquid from a cache path with a checked default
of `../liquid`, the sibling checkout in this bridge: `LAKE_LIQUID_SOURCE_DIR` in lake
([lake#145](https://github.com/oramasearch/lake/pull/145)) and `LIQUIFY_LIQUID_SOURCE_DIR` in
liquify ([liquify#69](https://github.com/oramasearch/liquify/pull/69)). A bad path is a
`FATAL_ERROR` that names the flag, so the failure explains itself.

Neither repository builds from a bare clone any more — that is the cost, and it is deliberate.
CI pays it by checking out `oramasearch/liquid` at this bridge's pin into `_external/liquid`,
the way lake already handled Zetta. lake's image takes liquid as a named build context.

**Bumping liquid is now one move here plus the CI `ref:` in each consumer.** Bumping the pointer
in this bridge without moving those refs means CI builds a different liquid than a developer
does — the same drift in a new place. Move them together.


## 43. What lake is to a customer — **decided (Steve, 2026-09-25): Orama's cloud offering, called lake, at lake.live, with repositories at the centre.**

Orama now describes what it does as helping companies **design, train, and ship AI**
(https://github.com/oramasearch/orama-website-v2/pull/386). A customer needs somewhere to do that,
and lake already holds most of it: repositories, drive, datasets and models with training
provenance, environments and deployments, package registries, identity and audit. What it lacked
was a statement of what it is for. Four answers settle that:

- **lake is Orama's cloud offering, and the name customers see is lake.** Its host is **lake.live**,
  linked from orama.com. Today the only deployment is `lake.oramadev.net` on AKS; moving to lake.live
  is https://github.com/oramasearch/liquid-bridge/issues/17.
- **lake also runs on-prem for enterprise customers.** **Orama Studio is a separate on-prem
  enterprise product**, so lake does not link out to Studio. Everything a cloud customer designs,
  trains and ships is a lake page.
- **Repositories are the central object.** A liquid repository is a shared, multiplayer space for any
  data (files, objects, datasets, models, code), closer to a shared drive folder than a code
  repository. Design, Train and Ship are views over repositories, never a second store. This
  matches lake's own contracts, where models, datasets and drive folders are ordinary repositories.
- **Sign-in is Clerk** — *amended the same day (Steve, 2026-09-25): "the existing logins are
  confusing."* The first answer was lake's own identity (passwords, passkeys, TOTP, OAuth, SSO,
  SCIM). Browser sign-in for the cloud is now Clerk; lake's own identity pages stay in the binary
  for an install without Clerk (on-prem) and leave the navigation when Clerk is on. How a Clerk
  user gets a TAAP identity is decision 44.

**What it costs.** lake's home page, navigation and per-repository tabs are rewritten around
Repositories, Design, Train and Ship; the design is `lake/docs/design/cloud.md`
(https://github.com/oramasearch/lake/pull/146). Design has no implementation yet. The code-forge
framing (Code as the first repository tab, "push with liquid" as the headline journey) gives way to
Files and the three verbs, which moves liquid's command line from the front door to one way of
working among several. Two cloud products with different identity systems now exist side by side
(lake and the v2 stack on Clerk) until the migration question below is answered.

**Known limits.** This does not decide what lake.live means for Orama Cloud v1 (`app.orama.com`) or
v2 (Railway and Clerk), or how their customers move. It does not decide whether a Design project is
a repository (proposed in the design) or a control-plane record. And it does not decide whether
liquid's public repositories stay on lake.live before liquid is open source
(https://github.com/oramasearch/liquid-bridge/issues/16).

**Revisit if** lake.live and the v2 stack need one sign-in for the same customers, if a customer
needs Studio's surfaces in the cloud rather than on-prem, or if a class of data turns up that
cannot live in a repository.

Issue: https://github.com/oramasearch/liquid-bridge/issues/31. Design:
https://github.com/oramasearch/liquid-bridge/issues/30. Bears on
https://github.com/oramasearch/liquid-bridge/issues/9.


## 44. Where a Clerk user's TAAP identity comes from — **decided (Steve, 2026-09-25): lake mints one and holds its key.**

lake's policy engine keys every grant on a TAAP identity, and a person with no TAAP identity is
anonymous to it. Until now every lake user brought one: sign-up asked for a public Liquid identity
document, which is the step that made sign-in confusing. A person who signs in through Clerk
(decision 43, amended) arrives with a verified email and nothing else.

So on first sign-in, when no lake-pool account shares that verified email, lake **mints an Ed25519
TAAP identity** for the person (`audit::mint_custodial_identity`, the same derivation as lake's own
identity) and holds the seed wrapped under `LAKE_INSTANCE_KEK` in `custodial_identities`
(migration `0023_custodial_identities`). It then provisions their personal customer with an
`admin` grant, as password sign-up does (decision 40). When an account with the email exists,
the Clerk subject is linked to it instead, and nothing is minted.

The alternatives were asking for the identity document once after Clerk (keeps users' keys in
their hands, keeps the confusing step) and linking existing accounts only (no new users through
Clerk).

**What it costs.** Server custody of a user's signing key is a change to the security model: lake
could sign as a custodial user. Today nothing does; browser work (drive, repositories) is committed
by lake itself, and the seed is held only so the identity can later sign as the person or be
rotated to a key they hold. The seed's protection is the instance key, the same as lake's own
identity, so a compromise of `LAKE_INSTANCE_KEK` and the control database exposes custodial seeds.
Adds one table and one migration, which put the operator's rename cutover on the critical path of
this change (completed 2026-09-25).

**Known limits.** No rotation from a custodial key to a person's own Liquid key exists yet; that is
the path for someone who starts in the browser and later pushes from the command line with their
own identity. Linking by email trusts Clerk's email verification (email-code sign-in with
verification at sign-up).

**Revisit if** anything starts signing as a custodial user (it would need consent and audit of its
own), if the instance key is rotated (custodial seeds must be rewrapped), or if enterprise
customers require that lake never hold a user's key — the on-prem path without Clerk already avoids
custody.

Issue: https://github.com/oramasearch/liquid-bridge/issues/32. Implementation:
https://github.com/oramasearch/lake/pull/148; schema:
https://github.com/oramasearch/orama-operator/pull/170.


## 45. How lake keeps customers apart on Zetta — **decided (Steve, 2026-09-25): a Zetta cluster per customer, a "workspace".**

> **Amended by decision 46 (2026-09-25):** the workspace is now the customer's default Zetta service,
> requested through lake's control Postgres rather than `orama_control.workspaces`. The cluster per
> customer stands.

lake's Design, Train and Ship pages delegate to the Zetta engine: projects and intent, connections,
datasets, pipelines and runs, models and their endpoints, search indexes. Zetta has **no tenancy**:
no customer or workspace namespace, capability calls not scoped by project, and every list returning
every entity on the cluster. Its own governance page says there are no per-project roles yet.

Three ways were weighed: lake scoping one shared cluster (prefixed names, filtered lists, one
privileged token — buildable now, but one missed filter leaks another customer's data); tenancy in
Zetta first (cleanest, but engine work before lake shows anything); and **a cluster per customer**,
chosen: isolation is physical, so no lake bug can show one customer another's projects.

**How it works.** A customer's first visit to Design, Train or Ship offers "Start your workspace".
lake appends a `desired` event to `orama_control.workspaces` on its own data-plane Zetta (the Lake's
owned `OramaZettaCluster`, now with `provisionOperatorSchema`), naming the Lake, the customer and a
slug derived from the customer id (`ws-` + its first 12 hex digits). The operator creates a
Lake-owned `OramaZettaCluster` for it, copies that cluster's admin token into the Secret
`lake-<lake>-workspaces` mounted into lake, and appends `status` events. lake authorizes every page
against its own policy on the customer first, then calls that customer's cluster only.

**What it costs.** A pod and a storage volume per active customer, on what is today a single node:
fine for a handful of customers, not for thousands. Customers who never open Design, Train or Ship
cost nothing. lake holds one admin token per workspace (in a mounted Secret, never in its database).
Zetta clusters idle at a few megabytes of memory; they are scheduled without CPU requests on dev.

**Known limits.** No deletion or suspension of a workspace in this version. No quota on workspace
count. Organization customers share one workspace among their members, and lake's roles on the
customer decide who may act; Zetta's own roles are not used.

**Revisit if** the node count or cost of per-customer clusters becomes the constraint (then tenancy
in Zetta, or pooling small customers), or if Zetta gains workspace scoping.

Issue: https://github.com/oramasearch/liquid-bridge/issues/33. Design:
https://github.com/oramasearch/liquid-bridge/issues/30.

## 46. How a customer runs more than one service — **decided (Steve, 2026-09-25): many managed services per customer, desired state in lake's control Postgres, reconciled by the Orama operator.**

A customer should be able to run several Zetta clusters and several Postgres clusters, not just the
one workspace decision 45 gives them, and see them all on one page. Steve's direction: the Orama
operator manages them through CRDs as it already does; other operators (CloudNativePG for Postgres)
can do the heavy lifting underneath, but **all of it is orchestrated from the Orama operator, which
reads the desired state from lake's control Postgres**.

**How it works.** lake writes one row per service to `services` (migration `0024_services`):
the customer, a kind (`zetta` or `postgres`), a name, a never-reused slug, a small spec
(instances, storage) and whether it should be present. The operator reads that table with pgx,
creates `<lake>-<slug>` as an `OramaZettaCluster` or a CloudNativePG `Cluster`, copies the
service's connection into the Secret `lake-<lake>-services` mounted into lake, and upserts
`service_status`. Deleting sets `desired = 'absent'`; the operator removes the resource and its
volumes and reports `Deleted`. The workspace behind Design, Train and Ship is the customer's
**default Zetta service**. Its slug stays `ws-<12 hex>`, so the operator adopts the cluster
decision 45 created, and its data, instead of making a new one. The full contract is lake
`docs/control-plane/services.md`.

**Why Postgres, not the Zetta stream of decision 45.** The control Postgres already holds every
customer, grant and audit record lake authorizes against. Desired state next to them is one
transaction with the policy check, one backup, and one place to look. The Zetta request stream
existed only because the operator already spoke Zetta over HTTP. The cost is a Postgres client in
the operator: **pgx** (MIT, pure Go), approved by Steve. It is an operator-only dependency, so
liquid's open-source licence question (#2) is untouched.

**What it costs.** Every service is a pod and a volume on today's single node. There is a quota per
Lake (`spec.services.maxServices`) and one per customer (`LAKE_SERVICES_PER_CUSTOMER`, default 5).
The operator connects with lake's own application credential, `lake-<lake>-controldb-app`, rather than a
narrower role. The operator can already read every Secret in the cluster, so a separate role would
not reduce what it can reach, and creating one needs a superuser step the schema Job does not have.

**Known limits.** Endpoints are in-cluster only; a customer cannot reach its Postgres from outside
yet. A service cannot be resized after creation. Design, Train and Ship use only the default Zetta
service.

**Revisit if** services need to be reachable from outside the cluster (then per-service ingress and
TLS), if another kind is added (the kind check and the operator's switch grow together), or if a
narrower operator role becomes cheap (CloudNativePG managed roles plus grants in the schema).

Issue: https://github.com/oramasearch/liquid-bridge/issues/34. Supersedes the request stream of decision 45
(https://github.com/oramasearch/liquid-bridge/issues/33).

## 47. Which services lake offers and what runs them — **decided (Steve, 2026-09-25): a catalog of seven kinds, each on one permissively licensed upstream operator.**

> **Amended (Steve, 2026-09-26): SQLite is a kind after all**, served by `lake-sqlite`, a small web
> service we wrote (orama-operator `cmd/lake-sqlite`, pure-Go SQLite driver `modernc.org/sqlite`,
> BSD-3) that passes HTTP calls through to one SQLite database per service. The Orama operator runs
> it directly, as a single-replica StatefulSet with a volume and a bearer token. There is no
> upstream operator, no replication, and exactly one instance. Migration `0026_sqlite_services`.
> The "SQLite is not a kind" limit below is superseded.

Steve asked for the operators from a licensing-first survey (September 25, 2026) to be added and
offered as lake services, Kafka included. The survey's selections stand:

| Kind | Operator | Pinned | Status |
|---|---|---|---|
| Postgres | CloudNativePG | already installed | production path |
| Kafka | Strimzi | 1.2.0 | production path |
| ClickHouse | Altinity Kubernetes Operator | 0.27.4 | production path; the newer official ClickHouse operator is worth a pilot, not a switch |
| TiDB | PingCAP TiDB Operator | v1.6.6 | the stable 1.x line; upstream `main` is v2 with removed features, evaluated later |
| Cassandra | K8ssandra Operator (with cass-operator) | 1.33.0 | needs cert-manager (v1.21.2); Apache Cassandra images only, never DSE |
| Valkey | valkey-io/valkey-operator | 0.6.0 | upstream says not ready for production, `v1alpha1`; lake no longer labels it (amended below) |
| Zetta | the Orama operator | — | as decision 46 |

**Why these.** Every operator is Apache 2.0 and actively maintained, with documented failover,
upgrade and recovery tooling. That is the bar for a platform we resell. Alternatives rejected by
the survey: Crunchy PGO, whose portal terms forbid offering it as a service without a subscription,
and the archived Banzai Koperator.

**How it works.** The operators are installed from orama-operator's `helmfile.yaml` (label
`tier=service-operators`), cluster-scoped. The Orama operator reads each service from lake's control
Postgres (decision 46) and writes that kind's resource: `Kafka` + `KafkaNodePool` + `KafkaUser`,
`ClickHouseInstallation`, `TidbCluster`, `K8ssandraCluster` or `ValkeyCluster`. It then copies the
connection into lake. We never run the databases ourselves. Migration `0025_service_catalog` widens
the kind check.

**What it costs.** Six more controllers and cert-manager on a single node. Every service is at least
one more pod and volume, and Cassandra and TiDB are memory-heavy. Each operator is an upgrade stream
to follow, especially Valkey, whose 0.6.0 already broke its TLS field. There are **no backups** for
any kind yet.

**Known limits.**
- Endpoints are in-cluster only.
- There is no resize.
- Backups are future work, and need a licence check: the CloudNativePG Barman plugin is Apache 2.0,
  but Barman itself is GPLv3.
- Valkey carries no customer commitment.
- **SQLite is not a kind:** it has no operator and no replication (Litestream is disaster recovery,
  not HA), so it needs its own product design.

**Revisit if** Valkey's operator reaches a stable API (then drop the preview label after failure,
upgrade and restore tests); if TiDB v2 regains BackupSchedule and monitoring; if the official
ClickHouse operator overtakes Altinity in a pilot; or when customer endpoints must leave the cluster.

**Amended 2026-09-26 (Steve, lake#197): the product no longer distinguishes preview kinds.** lake's
kind table has no `preview` flag and no kind — Valkey included — is labelled *preview, not for
production* in the menu or on rows. Valkey's upstream operator is still `v1alpha1`; that risk is
ours to carry (upgrade and restore tests before any customer commitment), not a label to show. The
menu lists Zetta first, preselected, then every other kind by name, each with its measured start
time.

Issue: https://github.com/oramasearch/liquid-bridge/issues/35. Builds on decision 46 (https://github.com/oramasearch/liquid-bridge/issues/34).

## 48. Who sees an organization's space — **decided (Claude, 2026-10-02, on Steve's instruction to merge lake#453's fixes and record the decisions): an organization-wide membership grants its role on the organization's own space.**

**What.** A membership of a whole organization also gets a grant on the organization's own space:
`admin` for owners and admins, `read` for members. Team memberships do not reach the space. Lake
keeps the grant in step with the membership on create, accept, join, role change and removal
(lake#461).

**Why.** Without it an invited member sees nothing in the organization (no repositories, workspaces
or apps), so invitations are useless (lake#443, found by the UX review 2026-10-01). App access
already works this way. Because the grant follows the membership, removing a member removes the
access.

**Rejected.** Team-only grants: stricter, but a new organization needs manual setup before anyone
sees anything. An explicit grant per person: visible, but it drifts from the membership and
survives removal.

**What it costs.** Every member reads everything in the organization's space by default; anything
finer still goes through teams and explicit grants. Memberships created before lake#461 get no
grant (no backfill).

**Revisit if** an organization needs members who must not see the whole space by default, or when
per-resource roles land.

Issue: https://github.com/oramasearch/lake/issues/464.

## 49. How lake rolls on a single-replica, ReadWriteOnce store — **decided (Claude, 2026-10-02, on Steve's instruction to merge lake#453's fixes and record the decisions): `Recreate` by default; an overlapping rollout is an explicit opt-in until two lake processes are proven safe on one store.**

**What.** The deploy-time 503s (orama-operator#243) come from `Recreate` on a one-replica Lake whose
store is ReadWriteOnce: every change stops the only pod before the next can attach the volume. An
overlapping rollout (RollingUpdate, maxSurge 1, maxUnavailable 0, the surge pod pinned to the node
holding the volume) removes that window, but runs two lake processes on one store for its duration.
The operator ships the overlap as an opt-in Lake field; the default stays `Recreate`. Readiness on
`/readyz`, a startup probe, a 15 s preStop drain and a Ready condition that waits for the updated
replicas ship regardless (orama-operator#246).

**Why.** The store volume holds data that is not backed up anywhere (see the never-delete rule for
it). Liquid's per-operation locks and the transparency log's per-append lock suggest two processes
are safe, but nothing tests it. A short 503 window on a development deploy costs less than a
corrupted store.

**What it costs.** Each lake deploy still shows 503s until the new pod is ready (about a minute on
dev).

**Revisit when** lake#467 proves two processes on one store are safe (a concurrent-writer test with
a shutdown in the middle); then dev turns the opt-in on, and later the default can flip.

**Evidence, 2026-10-02 (lake#467, lake PR #474).** Two lake processes on one store root, with concurrent pushes, drive writes, OCI uploads and transparency appends and one process stopped mid-run, corrupted the customer store on every run: the store would not reopen and acknowledged writes were lost. Liquid's object store is single-process by design (in-memory pack offsets, object map and chunk index; overwritten metadata). Lake now takes an exclusive lock on `.lake-owner.lock` in the store root and a second process refuses to start, so the opt-in must stay off. Removing the deploy 503 window needs a multi-process liquid store or a store hand-off.

Issue: https://github.com/oramasearch/orama-operator/issues/247.
