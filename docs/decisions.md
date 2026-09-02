# Phase 0 decisions

These gate Phase 1 of the [action plan](action-plan.md). Each is recorded here with
its options; the *chosen* option is recorded in liquid's `CLAUDE.md` under *Decisions
not to drift past* once made. Detail and evidence live in liquid's feature and research
docs — this page is the index, not the argument.

## 1. One store

Zetta today: C++26, equal-peer CRDT-replicated, clustered, JSONL storage plus large
objects, Postgres-SQL subset, headed and headless. liquid's specification: C++26,
CRDT-backed, content-addressed chunk store, clustered, large objects, Merkle DAG, action
graph, lazy materialisation.

Same kind of system, same language, same team. Options, from liquid
`docs/features/23-metis-and-zetta.md`:

| | Shape | Cost |
|---|---|---|
| A — liquid on Zetta | Zetta's store is liquid's storage layer | Zetta must grow chunking and content addressing |
| B — Zetta on liquid | liquid's chunk store becomes Zetta's substrate | Zetta migrates; liquid must mature first |
| **C — Converge** | One store, two frontends | Highest short-term cost, lowest long-term |
| D — Stay separate | Defined boundary | Two stores, two GC problems, forever |

Recorded recommendation: **C, arrived at via B** — build liquid's chunk store as a
component designed for Zetta to adopt, prove it in liquid, converge.

## 2. One CRDT

`homer6/automerge-cpp` is a from-scratch C++23 Automerge. `zetta-bridge` describes
Zetta's CRDT as "from-scratch C++ Automerge, ~90M ops/sec on 30 cores", and Zetta was
"imported from `homer6/zetta`".

**First establish whether these are the same code or a shared lineage.** If they are,
the decision is where the canonical copy lives and whether it moves under
`oramasearch`. If they are not, pick one and retire the other.

## 3. One coroutine substrate

Zetta uses **Corosio** (cppalliance, vendored). `oramacore-cpp` uses **Boost.Capy**.
liquid's implementation doc names stdexec or Capy. Corosio and Capy may compose —
establish that — but three products in one org should not have three async models.

## 4. TAAP content-addressed subjects

TAAP/1 subjects are key-derived identifiers. Documents, drips, changes and artifacts
are content-addressed and cannot hold keys. Attribution *about* them requires an
object-subject form in the spec — TAAP open question 22.3, which liquid's
`docs/features/25-identity-attestation-and-transparency.md` marks as **required and
blocking**. Suggested shape is recorded there.

This is a spec change, not a liquid design choice, and it needs the protocol owner.

## 5. Licence

Metis is noted source-available. liquid, lake and lake-operator have no stated position.
k0s is Apache 2.0 and its `docs/` is CC-BY-SA-4.0. Decide before anything is
distributed.
