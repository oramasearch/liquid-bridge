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
| `modules/lake` | `oramasearch/lake` | `CLAUDE.md` — hello world serves on Zetta's stack; its adapter-TU and trailing-404 rules live there. |
| `modules/liquify` | `oramasearch/liquify` | `CLAUDE.md`. Native IDE; hello window. Never depends on Zetta. |
| `modules/orama-operator` | `oramasearch/orama-operator` | Its `CLAUDE.md` and `DESIGN.md`. **The Zetta operator, extended with a `Lake` CR.** Production on AKS: PR-based workflow, never fast-forward `main`. |

## Reading Zetta and the Orama operator

**Read Zetta only from the umbrella bridge**, never from a standalone clone:

```
/Users/stevesperandeo/dev/homer6/orama-work/modules/zetta-bridge/modules/zetta
```

`orama-bridge` (cloned locally as `orama-work`) pins the intended commit. A standalone
`~/dev/oramasearch/zetta` clone was found **1,053 commits behind** and missing the entire
`include/zetta/api/` HTTP layer — reading from it produced a wrong conclusion. The same
applies to the operator at
`orama-work/modules/orama-cloud-v1-bridge/modules/orama-cloud-v1-operator`; note that
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
| lake | `modules/lake/docs/<topic>/` | `serving/`, `control-plane/`, `deployment/`, `build/`, `api/` |
| liquify | `modules/liquify/docs/<topic>/` | `app-shell/` |
| orama-operator | `modules/orama-operator/docs/` (its flat convention) + `docs/lake/` for the Lake CR; `docs/crd-reference.md` is the field reference | `lake/` |
| k0s | `modules/k0s/docs/liquid/` on the `liquid` branch (upstream docs are CC-BY-SA; ours sit beside them) | — |
| this bridge | `docs/` for anything cross-module: the plan, decisions, the repository map, topology | `action-plan.md`, `decisions.md`, `repositories.md` |

A doc page says **what** exists, **why**, **how to verify** it, and **how to change** it. One
folder per topic, one file per subject, a `docs/README.md` index per repo. Full URLs for
cross-repo links.

**Every server component also exposes its capabilities as an API and as MCP**, in Zetta's
shape: REST under `/v1`, `/v1/openapi.json`, `POST /mcp`; the capability registry is the single
source all three adapters read, and each capability gets a page under `docs/api/`.

## Working across modules

- **Submodule pointers are commits.** After landing a change in a module, push the
  module first, then update the pointer here and push the bridge. **liquify pins liquid
  too** (`modules/liquify/modules/liquid`, library-only): a liquid change reaches liquify only
  by a deliberate pin bump inside liquify, never by editing liquid through liquify's copy. A pointer to an
  unpushed commit breaks every clone.
- **The plan is the sequencing authority.** If a change belongs to a later phase than
  the one in progress, it waits. The most expensive mistake available is writing
  storage code before the Phase 0 store decision.
- **Phase 0 is not optional.** [`docs/decisions.md`](docs/decisions.md) lists five
  decisions. None of `liquid` or `lake` gets source until they are recorded.
- **Documentation discipline applies here too.** A new module updates `.gitmodules`,
  `README.md`, this file and `docs/repositories.md` in the same change.

## Confidentiality

Metis material is confidential and lives in `oramasearch/corporate-intelligence`. This
bridge links and does not restate. Nothing from it goes to any external research
service. Every repository here is private and stays private.
