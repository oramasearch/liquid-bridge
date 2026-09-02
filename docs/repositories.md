# Repositories

What lives where, and the rules for each. All repositories are **private** under
`oramasearch`.

| Repository | Module path | What it is | Language | Status |
|---|---|---|---|---|
| [`liquid`](https://github.com/oramasearch/liquid) | `modules/liquid` | The tool — VCS, build, package manager, artifact service, runtime. **The specification for everything** lives here. **Open source eventually; never depends on Zetta.** | C++26 | Bootstrap |
| [`k0s`](https://github.com/oramasearch/k0s) | `modules/k0s` | Private, upstream-synced copy of `k0sproject/k0s`, modified for drips on the `liquid` branch. `main` is a pristine upstream mirror. | Go | Synced; `liquid` branch has docs only |
| [`lake`](https://github.com/oramasearch/lake) | `modules/lake` | The lake binary — the hosted service. **Enterprise. Builds on Zetta** (control plane, state, web serving) and consumes liquid's store as a library. | C++26 | Bootstrap |
| [`lake-operator`](https://github.com/oramasearch/lake-operator) | `modules/lake-operator` | kubebuilder operator deploying lake on k0s; the enterprise on-prem path. **Its own Zetta as observed-state store**, like the Zetta operator. | Go | kubebuilder scaffold; `Lake` CRD stub |

## Related, not modules of this bridge

| Repository | Relationship |
|---|---|
| [`homer6/automerge-cpp`](https://github.com/homer6/automerge-cpp) | The CRDT liquid specifies. Still under `homer6`. Subject to the one-CRDT decision. |
| [`oramasearch/oramacore-cpp`](https://github.com/oramasearch/oramacore-cpp) | BM25F search engine liquid specifies. Scaffold. |
| [`oramasearch/zetta`](https://github.com/oramasearch/zetta) | Orama Zetta — the running C++26 CRDT store. Subject to the one-store decision. Bridged by `zetta-bridge`. |
| [`oramasearch/orama-cloud-v1-operator`](https://github.com/oramasearch/orama-cloud-v1-operator) | **The Zetta operator, and the reference pattern for `lake-operator`.** The name is historical — do not read it as Cloud-v1-only. Read its `DESIGN.md`. |
| [`oramasearch/corosio`](https://github.com/oramasearch/corosio) | **Private patch carrier** for `cppalliance/corosio`, per the org procedure. Default branch `orama-main`, 2 commits ahead of upstream `develop`: one real fix — `fix(epoll): translate EPOLLHUP/EPOLLRDHUP so a hung-up fd stops spinning` (2026-07-10, PR #2). **Not upstreamed** as of 2026-09-02 (`EPOLLRDHUP` absent from upstream `develop`). **liquid and lake must consume this, not `cppalliance` directly.** |
| `cppalliance/capy` | **No private copy exists.** Zetta consumes upstream `develop` directly. Create `oramasearch/capy` only when there is a patch to carry — the procedure is for carrying patches, not for mirroring. |
| [`oramasearch/orama-bridge`](https://github.com/oramasearch/orama-bridge) | The org umbrella. Authoritative for conventions. |

## Rules that differ per repository

**`k0s`** — never commit to `main`; it is only ever fast-forwarded from upstream. Our
work is on `liquid`, rebased after each sync. The `upstream` remote's push URL is
deliberately invalid. Procedure in its `ORAMA-FORK.md`. Apache 2.0: distributing
modified binaries requires `LICENSE`, `NOTICE`, and stating that files changed — the
branch split satisfies the last by construction.

**`lake-operator`** — follow `orama-cloud-v1-operator` (the Zetta operator): one umbrella CRD, thin install
chart (operator + CRDs + RBAC only), `helmfile.yaml` for platform operators, decisions
in `DESIGN.md`. `config/` is generated and committed; `bin/` is ignored.

**`liquid`** — must never take a dependency on Zetta; it is open source eventually.
**`lake`** — builds on Zetta wherever possible. The two are on opposite sides of a
licence boundary, and that boundary is the reason they have separate stores.

## A drift to know about

Zetta's `.gitmodules` points `modules/corosio` at **`cppalliance/corosio`**, pinned at
`7c636ac97` — which is the *base* of `orama-main`, not its head. **Zetta is therefore
not consuming its own epoll fix.** Either the submodule was never repointed after the
private copy was made, or it was repointed back. On Linux this means a hung-up fd can
still spin. Repoint to `oramasearch/corosio` `orama-main`, or upstream the fix — but
note upstream `develop` has since taken a breaking `refactor!:` (timers → stateless
delay/timeout, 2026-07-08) and ported to capy's `io_result` alias, so rebasing
`orama-main` is not a fast-forward.

liquid and lake should not repeat this: point at `oramasearch/corosio` from the first
commit.

## Copies of public upstreams

Never `gh repo fork` — a fork of a public repository is public and cannot be made
private. Create with `gh repo create oramasearch/<name> --private`, push the upstream
history in, add `upstream` as a fetch-only remote, and verify visibility before pushing.
`k0s` was made this way.
