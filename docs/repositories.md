# Repositories

What lives where, and the rules for each. All repositories are **private** under
`oramasearch`.

| Repository | Module path | What it is | Language | Status |
|---|---|---|---|---|
| [`liquid`](https://github.com/oramasearch/liquid) | `modules/liquid` | The tool — VCS, build, package manager, artifact service, runtime. **The specification for everything** lives here (`docs/research/`, `docs/features/`, `docs/standards/`). | C++26 (planned) | Design; no code |
| [`k0s`](https://github.com/oramasearch/k0s) | `modules/k0s` | Private, upstream-synced copy of `k0sproject/k0s`, modified for drips on the `liquid` branch. `main` is a pristine upstream mirror. | Go | Synced; `liquid` branch has docs only |
| [`lake`](https://github.com/oramasearch/lake) | `modules/lake` | The lake binary — the hosted service. Forge, drive, platform, registry, identity, secrets, PKI, search. | C++26 (planned) | Skeleton; no code |
| [`lake-operator`](https://github.com/oramasearch/lake-operator) | `modules/lake-operator` | kubebuilder operator deploying lake on k0s; the lake enterprise on-prem install path. | Go | kubebuilder scaffold; `Lake` CRD stub |

## Related, not modules of this bridge

| Repository | Relationship |
|---|---|
| [`homer6/automerge-cpp`](https://github.com/homer6/automerge-cpp) | The CRDT liquid specifies. Still under `homer6`. Subject to the one-CRDT decision. |
| [`oramasearch/oramacore-cpp`](https://github.com/oramasearch/oramacore-cpp) | BM25F search engine liquid specifies. Scaffold. |
| [`oramasearch/zetta`](https://github.com/oramasearch/zetta) | Orama Zetta — the running C++26 CRDT store. Subject to the one-store decision. Bridged by `zetta-bridge`. |
| [`oramasearch/orama-cloud-v1-operator`](https://github.com/oramasearch/orama-cloud-v1-operator) | **The reference pattern for `lake-operator`.** Read its `DESIGN.md`. |
| [`oramasearch/orama-bridge`](https://github.com/oramasearch/orama-bridge) | The org umbrella. Authoritative for conventions. |

## Rules that differ per repository

**`k0s`** — never commit to `main`; it is only ever fast-forwarded from upstream. Our
work is on `liquid`, rebased after each sync. The `upstream` remote's push URL is
deliberately invalid. Procedure in its `ORAMA-FORK.md`. Apache 2.0: distributing
modified binaries requires `LICENSE`, `NOTICE`, and stating that files changed — the
branch split satisfies the last by construction.

**`lake-operator`** — follow `orama-cloud-v1-operator`: one umbrella CRD, thin install
chart (operator + CRDs + RBAC only), `helmfile.yaml` for platform operators, decisions
in `DESIGN.md`. `config/` is generated and committed; `bin/` is ignored.

**`liquid` and `lake`** — no source, build files or CI until Phase 0 of the
[action plan](action-plan.md) is complete. The temptation to start coding before the
store decision is the most expensive mistake available.

## Copies of public upstreams

Never `gh repo fork` — a fork of a public repository is public and cannot be made
private. Create with `gh repo create oramasearch/<name> --private`, push the upstream
history in, add `upstream` as a fetch-only remote, and verify visibility before pushing.
`k0s` was made this way.
