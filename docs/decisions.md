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

**lake-operator has its own Zetta state store**, in addition to k8s — the Zetta
operator's model: k8s/etcd is the source of truth for *desired* state (the CRs); Zetta
holds *observed* state, synced with anti-flap discipline. Reference:
`orama-cloud-v1-operator/docs/zetta-datastore.md`.

## 2. One CRDT — **decided: `automerge-cpp`, and it stays open.**

MIT-licensed, public, already vendored by Zetta as a submodule. It is the shared *open*
component between liquid (open) and Zetta (closed). Only its canonical home
(`homer6` vs `oramasearch`) remains open.

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

## 5. Licence — **posture decided; text not yet chosen.**

| | Posture |
|---|---|
| liquid, liquify | **Open source, eventually.** Which licence is open. Must never depend on Zetta. |
| lake, lake-operator | **Enterprise.** |
| Zetta | Closed / source-available. |
| k0s | Apache 2.0 upstream; private copy with `LICENSE` + `NOTICE` + stated changes on distribution. |
| automerge-cpp | MIT — open, shared. |
