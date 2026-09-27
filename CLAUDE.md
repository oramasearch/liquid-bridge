# CLAUDE.md — liquid-bridge

## What this is

A **bridge**: a manifest of git submodules plus cross-module docs. **No build, no
runtime, no tests.** The code lives in `modules/`. Read each module's own `CLAUDE.md`
before working inside it.

The project is **liquid** — a version control system, build system, package manager,
artifact service and runtime in one program — and its hosted service **lake**. The
full specification is `modules/liquid/docs/`. The plan is [`docs/action-plan.md`](docs/action-plan.md).

## Where conventions live

| Scope | File |
|---|---|
| **Org-wide** (no AI attribution, no estimates, banned word "seam", private repos only, memory disabled, commit means push, documentation discipline) | [`oramasearch/orama-bridge`](https://github.com/oramasearch/orama-bridge) `CLAUDE.md` — **authoritative** |
| **Project** (vocabulary, the two-tree document rule, confidentiality, research method, decisions not to drift past) | `modules/liquid/CLAUDE.md` |
| **Per module** | that module's `CLAUDE.md` |

This file adds only what is specific to working *across* the modules.

## Modules

| Path | Repository | Read first |
|---|---|---|
| `modules/liquid` | `oramasearch/liquid` | `CLAUDE.md`, then `docs/research/99-synthesis/README.md` |
| `modules/k0s` | `oramasearch/k0s` | `ORAMA-FORK.md` — branch model and sync. **Never commit to `main`.** |
| `modules/lake` | `oramasearch/lake` | `CLAUDE.md` — the control surface (one capability registry → REST `/v1`, OpenAPI, MCP) over the Postgres control plane, users/organizations/customers/repositories, server-rendered pages behind the admin sign-in; `Lake/prod` runs it on AKS. Its adapter-TU, one-registry and trailing-404 rules live there. |
| `modules/liquify` | `oramasearch/liquify` | `CLAUDE.md`. Native cross-platform IDE (SDL3 + Dear ImGui); hello window; links **libliquid** from the sibling `modules/liquid` via `LIQUIFY_LIQUID_SOURCE_DIR`, not a
vendored submodule. Never depends on Zetta. |
| `modules/lake-sqlite` | `oramasearch/lake-sqlite` | `CLAUDE.md`. The web service behind lake's SQLite service kind (Go, pure-Go SQLite); the operator runs its private image. Every service is its own private repo (umbrella rule). |
| `modules/lake-duckdb` | `oramasearch/lake-duckdb` | `CLAUDE.md`. lake's DuckDB service kind (Go); locked-down engine; private image. |
| `modules/lake-polars` | `oramasearch/lake-polars` | `CLAUDE.md`. lake's Polars service kind (Rust); private image. |


**One level up, not modules here.** `orama-operator` and `marketing-bridge` are pinned by the org
umbrella [`oramasearch/orama-bridge`](https://github.com/oramasearch/orama-bridge), not by this
bridge — they are shared across products and must not be vendored twice. Read them at
`orama-work/modules/orama-operator` and `orama-work/modules/marketing-bridge`. Their rules still
apply: the operator is PR-based and never fast-forwards `main`; marketing-bridge keeps its own
approval gates G1–G6 and its campaign issues on that repo.

## Creating users

To create a lake account for someone, in any environment, follow lake's
[`docs/deployment/users.md`](https://github.com/oramasearch/lake/blob/main/docs/deployment/users.md)
(`modules/lake/docs/deployment/users.md`). On lake.oramadev.net people are added in the Clerk
application `lake` (`app_3JpNNpVUwgRgnkItIPbzzRWa2BP`), because sign-up there is restricted.

To sign in to lake.oramadev.net from a browser (no email code) and walk every page after a roll,
follow lake's [`docs/deployment/browser-testing.md`](https://github.com/oramasearch/lake/blob/main/docs/deployment/browser-testing.md):
`tools/e2e/clerk-ticket.sh` mints a one-time Clerk sign-in ticket, `tools/e2e/walkthrough.mjs`
walks Design, Train and Ship with screenshots. Do it before calling a UI change done.

## Reading Zetta and the Orama operator

**Read Zetta only from the umbrella bridge**, never from a standalone clone:

```
/Users/stevesperandeo/dev/homer6/orama-work/modules/zetta-bridge/modules/zetta
```

`orama-bridge` (cloned locally as `orama-work`) pins the intended commit. A standalone
`~/dev/oramasearch/zetta` clone was found **1,053 commits behind** and missing the entire
`include/zetta/api/` HTTP layer — reading from it produced a wrong conclusion. The same
applies to the operator at
`orama-work/modules/orama-operator` (renamed from `orama-cloud-v1-operator` and promoted to a
top-level module of the umbrella on 2026-09-09); note that
checkout may sit on an in-flight feature branch, so cut PR branches from a clean clone of
`origin/main` rather than from the bridge worktree.

## Documentation is part of every change

**Every change to the system is documented in `docs/<topic>/*.md` of the repository that owns
it, in the same commit.** This is a must, not a nicety: the system is documented internally *as
it is built*. "Change" means code, a CR field, a schema, deployed state (a namespace, a Secret, a
DNS record, a helm revision), a build recipe, or a decision. `README.md` and `CLAUDE.md` are
summaries that point at the docs; they never carry the only copy of anything.

| Component | Documents in | Topics so far |
|---|---|---|
| liquid | `modules/liquid/docs/<topic>/` (research, features, standards are topics too) | `library/` (libliquid) |
| lake | `modules/lake/docs/<topic>/` | `serving/`, `control-plane/`, `deployment/`, `build/`, `api/`, `ui/` |
| liquify | `modules/liquify/docs/<topic>/` | `app-shell/` |
| orama-operator | `orama-work/modules/orama-operator/docs/` (its flat convention) + `docs/lake/` for the Lake CR; `docs/crd-reference.md` is the field reference | `lake/` |
| k0s | `modules/k0s/docs/liquid/` on the `liquid` branch (upstream docs are CC-BY-SA; ours sit beside them) | — |
| marketing-bridge | `orama-work/modules/marketing-bridge/docs/<topic>/` | `brand/` (positioning; the lineup strategy is `brand/get-the-right-data.md`), `cold-email/`, `campaigns/`, `analytics/`, `runbooks/` |
| this bridge | `docs/` for anything cross-module: the plan, decisions, the repository map, topology, how work is tracked | `action-plan.md`, `decisions.md`, `repositories.md`, `tracking.md` |

A doc page says **what** exists, **why**, **how to verify** it, and **how to change** it. One
folder per topic, one file per subject, a `docs/README.md` index per repo. Full URLs for
cross-repo links.

**Every server component also exposes its capabilities as an API and as MCP**, in Zetta's
shape: REST under `/v1`, `/v1/openapi.json`, `POST /mcp`; the capability registry is the single
source all three adapters read, and each capability gets a page under `docs/api/`.

## Working across modules

- **Submodule pointers are commits.** After landing a change in a module, push the
  module first, then update the pointer here and push the bridge. A pointer to an unpushed
  commit breaks every clone. **liquify pins liquid too** (`modules/liquify/modules/liquid`,
  library-only): a liquid change reaches liquify only by a deliberate pin bump inside liquify,
  never by editing liquid through liquify's copy.
- **Deploy hygiene** (learned the hard way on 2026-09-02): `docker build` contexts are
  absolute paths, always; `docker image inspect` the entrypoint before any push; every
  pushed image gets an immutable tag and helm points at that tag (a node caches a mutable tag).
  Runbooks: lake `docs/deployment/aks.md`, operator `docs/lake/README.md`.
- **The plan is the sequencing authority.** If a change belongs to a later phase than
  the one in progress, it waits. The most expensive mistake available is storage code
  that ignores the Phase 0 decisions (separate stores by licence; automerge-cpp; Capy + Corosio).
- **Phase 0 is decided** ([`docs/decisions.md`](docs/decisions.md), six entries): separate stores by
  licence, automerge-cpp, Capy + Corosio, TAAP object subjects (still open, spec change), licence
  posture (text open), and lake's planes (Postgres control plane for now, Zetta data plane).
  Phase 0.5 hello world was met on AKS on 2026-09-02; Phase 1 (the store) starts inside libliquid.
- **Documentation discipline applies here too.** A new module updates `.gitmodules`,
  `README.md`, this file and `docs/repositories.md` in the same change.
- **Work is tracked as GitHub issues under one master epic**
  (https://github.com/oramasearch/liquid-bridge/issues/7, structure in
  [`docs/tracking.md`](docs/tracking.md)). A deliverable the specification names gets a leaf issue
  in the owning repo under its phase epic; a feature doc that names work with no issue is the
  drift to catch. The generators live in `tools/issues/` and are idempotent.
- **Work gets done through `/complete-super-epic`** ([`docs/orchestration.md`](docs/orchestration.md)):
  Codex implements each leaf in its own worktree and branch and opens a PR; Claude triages, briefs
  and reviews; the issue closes with a comment when its PR is up. `orama-operator` PRs stay open
  for Steve.

## Every decision is recorded twice — IMPORTANT

**A decision is not made until it exists in both places.** Write it in
[`docs/decisions.md`](docs/decisions.md) of this bridge *and* open a GitHub issue for it, labelled
`decision`, in the repository the decision governs (the bridge when it spans repositories). One
without the other is how a decision gets relitigated three weeks later by someone who searched the
wrong surface.

- **`docs/decisions.md`** carries the reasoning: what was decided, why, what it costs, the known
  limits, and what would make us revisit. It is the document a reader consults to understand the
  system.
- **The issue** carries the state: open while the question is genuinely open, closed with the
  outcome when it is settled, and linked from the master epic so the open ones are visible without
  reading a file.
- **Both link to each other**, and to the issues the decision unblocks.

An entry that says only what was decided, with no cost and no revisit condition, is not finished.
The point is that the next person can tell a settled question from an unexamined assumption.

## We write our own — IMPORTANT

**Default to implementing the primitive ourselves rather than taking a heavy third-party
dependency.** This is not novelty for its own sake; it is a standing decision Steve has made
repeatedly, and a proposal that ignores it will be sent back:

| Instead of | liquid has its own | Decision |
|---|---|---|
| RocksDB / LMDB for the chunk index | fixed-width LSM, rebuildable from packs | liquid CLAUDE.md 8 |
| A third-party SAT/CDCL solver | liquid's own dependency solver | 20 |
| Vendor hardware-token SDKs | command layers over the OS transports | 21 |
| A timestamping/X.509 library | own verification, verify-only | 32 |
| An off-the-shelf secrets envelope | liquid's own sealed envelope | 29 |
| libfuse / macFUSE | own Linux, macOS and Windows projection | 39 |
| A general async runtime | Boost.Capy and Corosio, which are ours | — |

The reasons compound, and any one of them is enough:

- **Licence.** liquid and liquify are going open source under a licence not yet chosen
  ([#2](https://github.com/oramasearch/liquid-bridge/issues/2)). An LGPL or GPL dependency
  constrains that choice and static linking; a non-free one (macFUSE) rules the path out entirely.
- **Prerequisites.** Every dependency a customer must install first is a customer who does not get
  a first useful result. macFUSE being absent is precisely why Phase 2's exit could not be
  demonstrated on any machine we have.
- **Control.** When the primitive is ours, a defect is a fix rather than an upstream negotiation,
  and the behaviour is one we can specify and test rather than infer.

**In practice:** before adding any dependency beyond a codec or a header-only utility, ask. Prefer
the platform's own facility (the FUSE kernel protocol, NFS, ProjFS, FSKit) over a library that
wraps it. Say what the licence is, in the same breath as what the library does. And when we do
write our own, it lands with a conformance suite the previous implementation also passes, so
"ours" never means "less proven".

## The AKS cluster is development, not production — IMPORTANT

`orama-production-cluster-01`, `Lake/prod` and `lake.oramadev.net` are the **development**
environment despite their names; **there is no production yet** (Steve, 2026-09-27; the umbrella
`CLAUDE.md` has the full rule). Rolling lake, the operator and the agents there is a routine dev
deploy: do it without asking. Destructive database actions still need Steve's explicit yes, and the
store volume and instance key Secret are never deleted.

## Builds and deploys stay current — IMPORTANT

**The deploy is part of the work, not a follow-up.** Whenever a change lands that the running system should
carry, rebuild and redeploy it in the same stretch of work; do not leave the cluster or a shipped artifact on an
older commit than the branch it came from. A merged fix that has not been rolled is **not fixed** — the defect
is still live for whoever is using the service, and reporting the merge as if it were the fix is the same class
of error as trusting a green test that skipped.

Do not stop at "merged, images built, ready to roll" and hand the last step back. Carry it through to the
running system, then say what is running. The only reasons to stop short are a hard gate — a production
handoff whose own runbook demands a scheduled window, a destructive database action, or a credential you do
not have — and when one of those stops you, **say so in the first line of the report**, not after the good
news.

- **lake on AKS.** After a merge to lake `main` (including a submodule pointer bump), build the image from the
  true head of `main` and roll `Lake/prod` to it. Check the head with `git rev-parse --short origin/main`
  immediately before the build: a build started before another PR merges ships the older tree. The procedure is
  in `.claude/skills/liquid-dev/SKILL.md` (cluster BuildKit through `buildctl`, no Docker here).
- **The operator.** Same rule; its next deploy must run `docs/operations/rename-cutover.md` first — the chart
  renders its resource names from `orama-operator` while production runs the release `orama-cloud-v1-operator`,
  and Helm cannot rename in place, so the handoff briefly runs both releases under one leader-election ID.
- **Order within a roll.** The operator applies lake's schema from a vendored byte-identical copy, guarded on
  the newest migration's table. When lake's schema changes, the operator is re-vendored, merged and rebuilt
  **first**, then the `PostgresSchema` is deleted so the Job re-runs, and only then does the new lake binary
  roll. Out of order, the Job reports `Applied` while applying nothing — the guard table already exists — and
  the new binary starts against a database missing its migration.
- **liquify.** After a merge that changes what a person sees or runs, rebuild and produce a fresh dmg, and say
  where it is. A screenshot from the headless path is not evidence that the real window works: open the built
  application before claiming a UI change is done.
- **Say what is deployed.** When reporting progress, state the image tag or artifact and the commit it was
  built from, so "merged" and "running" are never confused.

## Confidentiality

Metis material is confidential and lives in `oramasearch/corporate-intelligence`. This
bridge links and does not restate. Nothing from it goes to any external research
service. Every repository here is private and stays private.

## Skills

- `/liquid-dev` (`.claude/skills/liquid-dev/SKILL.md`): how to build, verify and merge in every repository without Docker, and the exact procedure for updating lake and the operator on AKS (cluster BuildKit, schema Job, CR roll, helm). Read it before any deploy or release step.
- `/lake-service` (`.claude/skills/lake-service/SKILL.md`): add or update a lake service kind — choose an upstream operator or build our own wrapper service (when no good permissively licensed operator exists, the Orama operator runs it), the private repo and image, lake's kind and migration, the reconciler, the helmfile, deploy order and the `services.mjs` browser proof.
- `/complete-super-epic`: the orchestration skill that drives Codex workers through the plan.
- `/product-review` (`.claude/skills/product-review/SKILL.md`): test the whole product as a customer would,
  compare what is promised against what runs, and file original issues for the gaps. Use it before claiming an
  area is finished.
- `/lake-ux-review` (`.claude/skills/lake-ux-review/SKILL.md`): lake's UX, job by job (load data, train a model,
  ship it, build an agent), through the browser, the REST API and MCP; checks each claim lake makes against what
  runs, writes `docs/reviews/lake-ux/<date>.md` and files an epic of issues. Run it before a demo and after large
  UI changes.
