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
