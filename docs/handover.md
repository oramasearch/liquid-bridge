# Where the work stands, and how to pick it up

Written 2026-09-09. This is the document to read first when resuming. Its live counterpart is
https://github.com/oramasearch/liquid-bridge/issues/29 — the issue carries the state, this file
carries the detail and the reproductions. It records **what is running,
what is green, what is blocked, and the host conditions that have repeatedly cost whole sessions**.

The plan is [`action-plan.md`](action-plan.md); decisions are [`decisions.md`](decisions.md); how work
is tracked is [`tracking.md`](tracking.md); the master epic is
https://github.com/oramasearch/liquid-bridge/issues/7. This file does not restate them — it says
where the moving parts are right now.

**Resuming? Start here.**

1. **[operator#168](https://github.com/oramasearch/orama-operator/issues/168)** — production
   follow-ups from the 2026-09-09 outage. **Updated 2026-09-25:** the operator now runs
   `main-83c6d90` (so #167's e2e gating is in effect) and the rename cutover is finished; what
   remains is retiring the 3 e2e CRDs. R2 and the v1 bucket are ignored while v1 awaits deprecation.
2. Read [the outage section](#the-operator-was-down-for-12-hours-on-2026-09-09-and-what-changed)
   before touching the operator, and [the host conditions](#the-host-conditions-that-waste-sessions)
   before believing any test failure.
3. Open PRs awaiting review: [liquify#70](https://github.com/oramasearch/liquify/pull/70) (idle CPU).
4. Then [the ordinary queue](#ready-to-work-now).

## Repository heads

| Repository | Branch | Head | Suite |
|---|---|---|---|
| liquid | `main` | `aa60e87` | **699 / 699** serial, 2026-09-09 after the fseventsd restart (was 697 — the armed-watcher tests run now) |
| liquify | `main` | `e1f49c9` | **140 / 140**, re-run after the liquid rewiring |
| lake | `oramasearch/lake:20260927b` | `797ce72` | rolled 2026-09-27: agents (epic lake#228): Train → Agents and the Agent Library, launches on agent-runtime, Ask Orama, Discover, the Agent Factory, Pipelines as agent tools, non-expiring keys, and **cron schedules as CronJobs** (lake#244, migration 0031 applied). Live-proven: job and CronJob runs of a Python agent return results; Ask Orama read + delegation; Project Agent S-1 Pipeline; Auto-Suggest 3/5 |
| orama-operator | `main` | `058a7d8` | `go build`/`vet`/`test ./...` green, `helm lint` clean |
| k0s | `liquid` | `dc5587465` | `go build`/`vet` clean, 15 tests ok |

Both liquid and liquify are **fully green for the first time in this cycle**. That is new, and it is
the property to protect: a suite with known-failing tests trains everyone to read red as noise, which
is what cost four separate sessions before #282 was diagnosed.

## What is deployed

| | Running | Built from | Verified |
|---|---|---|---|
| lake | `oramasearch/lake:20260927b` | `797ce72` | rolled 2026-09-27: agents (epic lake#228): Train → Agents and the Agent Library, launches on agent-runtime, Ask Orama, Discover, the Agent Factory, Pipelines as agent tools, non-expiring keys, and **cron schedules as CronJobs** (lake#244, migration 0031 applied). Live-proven: job and CronJob runs of a Python agent return results; Ask Orama read + delegation; Project Agent S-1 Pipeline; Auto-Suggest 3/5 |
| operator | `oramasearch/orama-operator:main-c2bc15a` | `c2bc15a` | release `orama-operator` revision 15: services, stores, the Agent Library, agent launches (#186, label fix #187) and one CronJob per agent schedule (#189); schema guard `agent_cron_guard` |
| service operators | cert-manager v1.21.2, Strimzi 1.2.0, Altinity 0.27.4 (watching `.*`, #178), TiDB Operator v1.6.6, K8ssandra 1.33.0, valkey-operator 0.6.0 | orama-operator `helmfile.yaml`, `tier=service-operators` | `helm list -A`; each kind created, Ready, connected and deleted from the UI on 2026-09-26 (decision 47) |
| wrapper services | `oramasearch/lake-sqlite`, `lake-duckdb:0.1.0`, `lake-polars:0.1.0` (private) | their own private repos, pinned in `modules/` | `tools/e2e/services.mjs sqlite duckdb polars` exit 0 on 2026-09-26 with real queries and refused escapes (lake#207) |
| workspace Zetta | `oramasearch/zetta:dev-f84ab6f` | zetta `dev` `f84ab6f` | `Lake/prod` `spec.services.zettaImage`; the adopted workspace `prod-ws-6bb777ba498a` kept its data |
| schema | `0028_stores` | vendored from lake `9aa6141` | `PostgresSchema lake-prod-controldb-schema` Applied `sha256:28cc3b7c40b6`, guard `stores_guard` |

`Lake/prod` reports `Ready=True StoreReady=True ZettaReady=True`, and `BackupReady=False` because the
R2 backup Secret does not exist — unchanged and tracked separately.

**From `20260908c` onward every lake image reports its own source revision.** Before that, the commit
an image was built from was recorded by hand and unverifiable from the artifact. `20260908b` and
earlier remain hand-recorded.

## The host conditions that waste sessions

These are not bugs to fix in the code. They are properties of this machine that have each been
rediscovered more than once.

### FSEvents is wedged on this Mac

`fseventsd` accepts subscriptions and delivers nothing, process-wide. Proven with a standalone
`FSEventStream` program that writes a file into the directory it watches and receives no event —
no liquid code involved. It is **not** liquid, and liquid no longer fails because of it: capture
degrades to periodic reconciliation and reports `capture_status::watcher_armed = false` with an
actionable diagnostic (liquid #282, PR #316).

Repair, whenever prompt capture is wanted back — macOS relaunches it immediately:

```sh
sudo killall -9 fseventsd
```

**Discharged 2026-09-09.** The daemon was restarted (it had been pinned at 99% of a core, which
was also inflating the load everything else was measured under) and liquid's full suite run
against a healthy one: **699 / 699 serial**. The count rose from 697 because the armed-watcher
tests actually execute now, so the non-degraded branch has had its first real run.

### macFUSE is absent, and stays absent

`liquid wrap` needs a filesystem projection. macFUSE is rejected on licence grounds
([decision 39](decisions.md)), `/dev/fuse` is absent on the AKS BuildKit worker, the Linux host at
`192.168.123.175` times out on SSH, and CI dies before it gets that far. This blocks liquid #299
(Phase 2 exit), #300 (Phase 4 exit) and #302 / #304.

[Decision 41](decisions.md) removed this as a blocker for the conformance suite: liquid #301 now
calibrates against a **direct in-process backend** and passes here. #303 (macOS NFS loopback, no
kernel extension) is therefore buildable and runnable on this machine and is the obvious next FUSE
leaf.

### Host load distorts results

Timing-sensitive tests fail under contention. Six Codex workers at `-j 6` on 16 cores drove load to
97 and produced failures that were not real. **Measure the load (`uptime`) beside any failure you
report, and re-run a suspicious failure on a quiet machine before believing it.** Two false
regressions in this cycle came from skipping that, and one came from running tests inside a worktree
a worker still owned — never do that; check `pgrep -f "codex exec"` first.

**Measured on 2026-09-09, so the next person does not re-diagnose it.** liquid's suite at load ~8:

| Run | Result |
|---|---|
| `ctest -j 4` | 4 failed / 699 |
| `ctest -j 2` | 2 failed / 699, a *different* pair |
| `ctest` (serial) | **0 failed / 699** |

The offenders are `NodeStore.AbsentTreeReportsItsUnavailableStoreUrl`,
`NodeStore.LocalMetadataMountsWhenItsContentStoreIsUnavailable` and both
`Backends/StoreSimulation.SeededCrashRecovery/{Disk,Memory}`. Run in isolation they passed **5 / 5**.
They are contention-sensitive, not broken — but the failure is an `abort`, which reads exactly like a
real crash. **Reproduce serially before filing anything against them.**

### lake and liquify no longer vendor liquid

Both used to carry liquid as their own `modules/liquid` submodule while this bridge also pinned it —
three pointers at one repository, and they had drifted (lake pinned `8203911`, this bridge `aa60e87`,
nothing reporting it). Both submodules are gone
([lake#145](https://github.com/oramasearch/lake/pull/145),
[liquify#69](https://github.com/oramasearch/liquify/pull/69),
[decision 42](decisions.md)).

Each build now resolves liquid from a cache path defaulting to `../liquid`, the sibling checkout in
this bridge: `LAKE_LIQUID_SOURCE_DIR` and `LIQUIFY_LIQUID_SOURCE_DIR`. A bad path is a `FATAL_ERROR`
naming the flag.

**Consequences to know before building:**

- Building from the bridge checkout works unchanged — the default finds `../liquid`.
- **A bare clone of lake or liquify no longer configures.** Pass
  `-DLAKE_LIQUID_SOURCE_DIR=` / `-DLIQUIFY_LIQUID_SOURCE_DIR=` at a liquid checkout.
- **Bumping liquid is now two moves, not one:** the pointer here, *and* the `ref:` in each
  consumer's `.github/workflows/ci.yml`. Move them together or CI builds a different liquid than a
  developer does — the same drift, in a new place.
- CI checks out `oramasearch/liquid` directly, so `ORAMA_SUBMODULES_TOKEN` must reach it too.

**Verified 2026-09-09.** Both suites re-run against the rewired build at the merged heads —
lake 257 / 257, liquify 140 / 140, matching the counts recorded before the change. Removing the
vendored liquid altered no behaviour in either.

### The operator was down for ~12 hours on 2026-09-09, and what changed

Found by accident while checking whether the rename tracking issue was shippable — nothing paged,
because `Lake/prod` kept serving throughout. Only the control plane was down: no drift correction,
no CR changes applied, from 09:29 to 21:20.

**Cause.** The manager registers a watch for every kind unconditionally, so a kind whose CRD is
absent is not a degraded controller — the cache never syncs, the manager exits, and the pod
crash-loops with every other controller down with it. Two CRDs had silently accumulated un-applied
because **Helm applies `chart/crds` on install only, never on upgrade**, and both rollout paths pass
`--skip-crds`. `lakee2etests` first; then, once that was applied, `clerkapplications`.

**Fixed** in [operator#167](https://github.com/oramasearch/orama-operator/pull/167) (merged,
`058a7d8`), which did two things:

1. **Production reconciles no e2e kinds.** `LakeE2ETest` — the kind that crash-looped everything —
   is a test fixture production has no use for. Production runs no e2e suites; that is what a
   testing environment is for. The three e2e controllers are now gated behind
   `--enable-e2e-controllers` (**off by default**), their CRDs live in `chart/e2e-crds/` outside the
   install chart, and their RBAC renders only under `e2e.enabled`. A testing environment opts in
   with both halves: `kubectl apply -f chart/e2e-crds/` **and** `--set e2e.enabled=true`.
2. **The remaining invariant is checked, not remembered.** Three hand-maintained artifacts per kind
   cause the identical crash — the CRD in the chart, the RBAC grant, the CRD on the cluster.
   `go test ./cmd/...` covers the first two plus e2e leakage with no cluster;
   `hack/check-cluster-crds.sh` (also `make check-crds CONTEXT=…`) covers the third and is wired
   into the cutover runbook before **and** after the upgrade.

Fail-fast was kept deliberately, reasoned in
[`docs/operations/crd-rollout.md`](https://github.com/oramasearch/orama-operator/blob/main/docs/operations/crd-rollout.md):
a crash-looping pod is visible in one `kubectl get pods`, whereas a manager that started 15
controllers and quietly skipped the 16th looks healthy while its resource drifts.

**Two lessons worth keeping.** A snapshot proves nothing against a crash *loop* — the first
"recovered" call was wrong because it read a moment between crashes, and the second missing CRD was
still there. And test that a check *fails* when it should: doing that found a false pass in the new
script itself, where a quoted glob meant `--e2e` checked nothing and reported success.

### No Docker on this machine

[Decision 33](decisions.md). Images are built on the cluster's BuildKit through `buildctl` over
`kube-pod://`. The exact procedure is in `.claude/skills/liquid-dev/SKILL.md`.

## Blocked on the owner

| | What is needed | What it unblocks |
|---|---|---|
| A Linux host with `/dev/fuse` | a reachable machine, or CI that gets past checkout | liquid #299, #300, #302; the libfuse baseline owed by #301; k0s #13 |
| ~~`ORAMA_SUBMODULES_TOKEN`~~ | **Replaced for lake (2026-09-26)**: one read-only deploy key per private repository (corosio, beast2, oramacore-cpp, automerge-cpp, liquid, zetta), secrets `DEPLOY_KEY_*` on `oramasearch/lake` (lake `docs/build/ci.md`, lake#174). liquify and liquid's own CI still use the token and still fail at checkout; the same keys can be granted to them | lake CI builds and tests on Linux (284/287), then was **disabled by Steve (2026-09-26)** until the Linux-only sync bugs are fixed: `block_on` (liquid#317, open) and a lost read on epoll in the HTTP client, probably fixed by updating the `oramasearch/corosio` fork, 221 commits behind upstream (lake#176). Re-enable: `gh workflow enable ci --repo oramasearch/lake` |
| Dependabot version updates | Settings → Code security → Dependabot version updates, off for `oramasearch/k0s` | k0s mirror integrity. The sync script now *catches* a violation; the toggle prevents it |
| ~~Roll the operator onto `main`~~ | **Done 2026-09-25**: `main-83c6d90` (includes #167) rolled as release `orama-operator` revision 3 | CRDs applied first (additive only; all 70 CRD UIDs unchanged). [operator#168](https://github.com/oramasearch/orama-operator/issues/168) |
| Retire 3 e2e CRDs (~~and the former operator release~~ — **retired 2026-09-25** with `helm uninstall --keep-history`, after finding no caller of its control-plane Service; Lease and CRD UIDs unchanged) | deliberate production changes on `orama-production-cluster-01` | finishing the rename cutover ([operator#120](https://github.com/oramasearch/orama-operator/issues/120)); deleting a CRD deletes its CRs, so check for e2e resources first. [operator#168](https://github.com/oramasearch/orama-operator/issues/168) |
| ~~Enable R2 on the Cloudflare account~~ — **ignored (Steve, 2026-09-25)** | — | `CloudflareR2Bucket/v1-legacy-indexes` belongs to the Orama Cloud v1 sandbox, which will be deprecated with its customers migrated to lake, eventually; its 403 retries are expected noise until then. It is **not** the cause of `Lake/prod` `BackupReady=False`: lake's control-plane backup is simply off (`spec.postgres.backup.enabled: false`, no destination). Choosing a backup target (R2 or Azure Blob) is a separate, open step. [operator#168](https://github.com/oramasearch/orama-operator/issues/168) |
| Decisions | TAAP subjects (#1, #8), the open-source licence (#2 — decision 39 depends on it), portfolio (#9), where `lake.live` runs (#13) | phase exits and the open-source release |

## Ready to work now

No dependencies, briefs already written for several of these under
`~/dev/oramasearch/codex-work/briefs/`.

**liquid** (12 open leaves) — #310 throwing public constructors · #281 stale import gate · #264, #225
test defects · #81 hardware keys · #82 user guides
**lake** (10) — #123 drive history · #125 clipped controls · #126 review comments · plus the Phase 6
features #3, #6, #18, #25, #33, #53
**liquify** (6) — #33 navigation · #34 command palette · #35 panels · #36 first run · #39 input and
accessibility. **#66 idle CPU is closed** — shipped in [liquify#70](https://github.com/oramasearch/liquify/pull/70), open for review.
**k0s** (3) — #13 Lake CR on k0s · #16 immutable node · #17 platform surface

### The two most valuable next pieces of work

The remaining one is **liquify #33 / #34 / #39**, below. **#66 (idle CPU) is done**: the run loop waited on `SDL_PollEvent`, which never blocks, so it rebuilt and re-rendered the
whole interface forever. It now waits on `SDL_WaitEventTimeout` for a cause, and every wake still
produces a frame, so sleeping cannot swallow a state change. Measured idle, foreground, repository
open, as CPU-seconds over 30 s wall: **2.85 s (9.5 % of a core) → 0.63 s (2.1 %)**.

The trap, if this is ever revisited: `WantCaptureMouse` / `WantCaptureKeyboard` / `WantTextInput` say
where input *would be routed*, not that anything is happening, and in an editor they are true nearly
always. The first attempt treated them as activity and the number barely moved (9.5 % → 8.1 %).
`docs/ui/redraw.md` in liquify records the model and what a new async producer must do.

Not done there: per-producer dirty tracking, which would cut the residual 2.1 % further. It needs
each `poll_*` to report whether it mutated UI state, and getting that wrong means a stale window.

**liquify #33 / #34 / #39 — three real UI defects, already pinned by tests.** liquify #56's
acceptance suite reproduces each and marks them `WILL_FAIL` naming the issue, so fixing one flips its
annotation rather than requiring new coverage. It also established that **#35 (tabs not clickable) and
#31 (quarter-size Retina shell) do not reproduce** — both were fixed by the shell redesign.

## How work gets done here

`/complete-super-epic` drives Codex workers: one leaf per worker, its own worktree and branch, a PR
each. Claude triages, briefs, verifies and lands. The workflow and its hard-won rules are in
[`orchestration.md`](orchestration.md).

Three rules that were paid for in this cycle:

1. **Verify independently. Do not merge on a worker's report.** Every issue closed here was checked
   by running the proof, and several times by breaking the fix deliberately to confirm the test
   catches it. Two workers reported gates that were not real; one reported a passing suite that was
   passing for the wrong reason.
2. **A worker that stops at a gate has usually done the right thing — but check the gate is real.**
   Four stopped on failures their own briefs listed as not theirs. That is the cost of a red `main`,
   and it is why #296 and #282 were worth fixing before anything else.
3. **Say what is deployed, not what is merged.** A merged fix that has not been rolled is not fixed.

## The 2026-09-09 late session

Started as a rename sweep and turned into an incident. Everything below is merged and pushed unless
it says otherwise.

**The operator is now a top-level module of the umbrella.** `orama-cloud-v1-operator` →
`orama-operator`, moved out of `orama-cloud-v1-bridge` because it is no longer v1-specific. This
bridge no longer vendors it, nor `marketing-bridge`; both are pinned once by
[`orama-bridge`](https://github.com/oramasearch/orama-bridge) and read from
`orama-work/modules/…`. Some `orama-cloud-v1-operator` strings survive **on purpose** — the
leader-election ID, the `app.kubernetes.io/managed-by` labels, the Karpenter field owner, and every
`helm`/`kubectl` name in the operations runbooks, because production still runs that release. Do not
"clean them up"; the operator's `docs/operations/rename-cutover.md` explains each.

**lake and liquify stopped vendoring liquid** (decision 42) — merged as
[lake#145](https://github.com/oramasearch/lake/pull/145) and
[liquify#69](https://github.com/oramasearch/liquify/pull/69). They had drifted: lake pinned
`8203911` while this bridge pinned `aa60e87`, with nothing reporting it.

**liquify #66 (idle CPU) is closed**, shipped in
[liquify#70](https://github.com/oramasearch/liquify/pull/70) — open for review.

**The operator outage and its fix** are in their own section above; that is the part most worth
reading before touching the operator.

## What this cycle closed

**15 issues**, each merged and verified independently: liquid #284, #286, #288, #289, #296, #301,
#305, #314 · lake #120, #121, #127, #138 · liquify #56, #62 · k0s #12. Two decisions recorded in both
places: **41** (conformance calibration). Two defects filed rather than papered over: liquid #310,
liquify #66.

The through-line worth remembering: **four of those were tests or build noise, not features**, and
they were the highest-value work in the cycle, because every one of them had been costing sessions.
