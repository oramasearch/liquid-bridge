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
| `modules/lake` | `oramasearch/lake` | `CLAUDE.md`. No code until Phase 0 is done. |
| `modules/lake-operator` | `oramasearch/lake-operator` | `CLAUDE.md`, then `orama-cloud-v1-operator/DESIGN.md` — **the Zetta operator**, and the reference pattern. |

## Working across modules

- **Submodule pointers are commits.** After landing a change in a module, push the
  module first, then update the pointer here and push the bridge. A pointer to an
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
