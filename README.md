# liquid-bridge

Bridge repo for the **liquid** project — pulls its repositories together as git
submodules so one Claude Code session (or one human) can work across all of them with
full cross-reference.

**liquid** is the tool. **lake** is where it collects (`lake.live`). **liquify** is the
IDE. A **drip** is one captured, signed write — the atom of history.

No application code, no build, no runtime here. Code lives in the modules; cross-module
docs and the action plan live in [`docs/`](docs/).

## Clone

```sh
git clone --recurse-submodules git@github.com:oramasearch/liquid-bridge.git
```

All modules are **private** — you need SSH access to the `oramasearch` org.

## Modules

| Module | What it is |
|---|---|
| [`modules/liquid`](modules/liquid/) | The tool, and **the specification for everything** — research, features, standards. Start with its `docs/research/99-synthesis/`. |
| [`modules/k0s`](modules/k0s/) | Private, upstream-synced copy of k0s. Our changes on the `liquid` branch. |
| [`modules/lake`](modules/lake/) | The lake binary — the hosted service. |
| [`modules/orama-operator`](modules/orama-operator/) | **The Orama operator** (renamed from `orama-cloud-v1-operator`; the Zetta operator). lake is deployed as a `Lake` CR on it — no separate lake operator. Runs in production on AKS. |

## Docs

- [`docs/action-plan.md`](docs/action-plan.md) — the phases, in dependency order.
- [`docs/repositories.md`](docs/repositories.md) — what lives where and the rules per repo.
- [`docs/decisions.md`](docs/decisions.md) — the decisions that gate Phase 1.

## Conventions

Org-wide conventions are in
[`oramasearch/orama-bridge`](https://github.com/oramasearch/orama-bridge) `CLAUDE.md`.
Project conventions are in `modules/liquid/CLAUDE.md`. See [`CLAUDE.md`](CLAUDE.md).
