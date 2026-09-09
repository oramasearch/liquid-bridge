# Where the work stands, and how to pick it up

Written 2026-09-09. This is the document to read first when resuming. Its live counterpart is
https://github.com/oramasearch/liquid-bridge/issues/29 — the issue carries the state, this file
carries the detail and the reproductions. It records **what is running,
what is green, what is blocked, and the host conditions that have repeatedly cost whole sessions**.

The plan is [`action-plan.md`](action-plan.md); decisions are [`decisions.md`](decisions.md); how work
is tracked is [`tracking.md`](tracking.md); the master epic is
https://github.com/oramasearch/liquid-bridge/issues/7. This file does not restate them — it says
where the moving parts are right now.

## Repository heads

| Repository | Branch | Head | Suite |
|---|---|---|---|
| liquid | `main` | `aa60e87` | **699 / 699** serial, 2026-09-09 after the fseventsd restart (was 697 — the armed-watcher tests run now) |
| liquify | `main` | `e1f49c9` | **140 / 140**, re-run after the liquid rewiring |
| lake | `main` | `3ea7ce3` | **257 / 257**, re-run after the liquid rewiring — but **112 of those are skipped**, not run: the Postgres-backed cases need `LAKE_TEST_DB_URI`, and ctest counts a skip toward the pass total |
| orama-operator | `main` | `014ae16` | `internal/...` ok, 12.1 s with envtest assets |
| k0s | `liquid` | `dc5587465` | `go build`/`vet` clean, 15 tests ok |

Both liquid and liquify are **fully green for the first time in this cycle**. That is new, and it is
the property to protect: a suite with known-failing tests trains everyone to read red as noise, which
is what cost four separate sessions before #282 was diagnosed.

## What is deployed

| | Running | Built from | Verified |
|---|---|---|---|
| lake | `oramasearch/lake:20260909a` | `98af177` | `GET /v1/server_info` returns `"revision":"98af17708fcaea0e71469ed9be1d9eb058799c92"` |
| operator | `oramasearch/orama-operator:main-014ae16` | `014ae16` | `kubectl -n orama-system get deploy orama-operator` |
| schema | `0022_session_lookup` | vendored from lake `98af177` | read from `schema_migrations` in the live database |

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

### No Docker on this machine

[Decision 33](decisions.md). Images are built on the cluster's BuildKit through `buildctl` over
`kube-pod://`. The exact procedure is in `.claude/skills/liquid-dev/SKILL.md`.

## Blocked on the owner

| | What is needed | What it unblocks |
|---|---|---|
| A Linux host with `/dev/fuse` | a reachable machine, or CI that gets past checkout | liquid #299, #300, #302; the libfuse baseline owed by #301; k0s #13 |
| `ORAMA_SUBMODULES_TOKEN` | an org secret with access to `automerge-cpp`, `corosio`, `oramacore-cpp` — **and now `liquid`**, which lake and liquify check out directly (see the rewiring above) | **all** CI — it fails at `actions/checkout` on every run, including `main`, so every test enforced locally is enforced nowhere else (lake #48) |
| Dependabot version updates | Settings → Code security → Dependabot version updates, off for `oramasearch/k0s` | k0s mirror integrity. The sync script now *catches* a violation; the toggle prevents it |
| Decisions | TAAP subjects (#1, #8), the open-source licence (#2 — decision 39 depends on it), portfolio (#9), where `lake.live` runs (#13) | phase exits and the open-source release |

## Ready to work now

No dependencies, briefs already written for several of these under
`~/dev/oramasearch/codex-work/briefs/`.

**liquid** (12 open leaves) — #310 throwing public constructors · #281 stale import gate · #264, #225
test defects · #81 hardware keys · #82 user guides
**lake** (10) — #123 drive history · #125 clipped controls · #126 review comments · plus the Phase 6
features #3, #6, #18, #25, #33, #53
**liquify** (7) — **#66 idle CPU** (see below) · #33 navigation · #34 command palette · #35 panels ·
#36 first run · #39 input and accessibility
**k0s** (3) — #13 Lake CR on k0s · #16 immutable node · #17 platform surface

### The two most valuable next pieces of work

**liquify #66 — the IDE burns 80–90% of a core while idle.** `App::run()` calls `SDL_PollEvent`,
which never blocks, and redraws the entire interface every iteration whether anything changed or not.
At ~12.5 ms of CPU per frame against a 16.7 ms budget that is three quarters of a core, forever. It
needs to wait when idle and redraw on cause. This is the most customer-visible defect open.

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

## What this cycle closed

**15 issues**, each merged and verified independently: liquid #284, #286, #288, #289, #296, #301,
#305, #314 · lake #120, #121, #127, #138 · liquify #56, #62 · k0s #12. Two decisions recorded in both
places: **41** (conformance calibration). Two defects filed rather than papered over: liquid #310,
liquify #66.

The through-line worth remembering: **four of those were tests or build noise, not features**, and
they were the highest-value work in the cycle, because every one of them had been costing sessions.
