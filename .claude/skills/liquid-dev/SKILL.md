---
name: liquid-dev
description: Day-to-day development and deployment for the liquid family (liquid, lake, liquify, k0s liquid branch, orama-operator) without Docker on the development machine; how to build, verify, merge, and update lake and the operator on AKS
---

# /liquid-dev

The working rules for this project, and the exact procedure for updating the packages that run on AKS.
Decision 33 (`docs/decisions.md`) applies everywhere: nothing here runs `docker` on the development Mac.

## Repositories and where things live

- `modules/liquid`, `modules/lake`, `modules/liquify`, `modules/k0s` (branch `liquid`) are submodules
  of this bridge; the bridge pins them and records decisions (`docs/decisions.md`), the plan
  (`docs/action-plan.md`) and progress (issue #7). The **Orama operator** is not a module here —
  it is pinned one level up by the org umbrella; read it at `orama-work/modules/orama-operator`.
- Work happens in `codex-work/` next to the bridge: `codex-work/<repo>` is the main checkout,
  `codex-work/wt/<repo>/issue-N` the worktree per leaf, `codex-work/briefs/` the briefs, `codex-work/runs/`
  the worker logs. The `/complete-super-epic` skill drives Codex workers; this skill is the human-sized
  procedure.

## Building and verifying locally

- liquid: `cmake -S . -B build -G Ninja && cmake --build build -j 6 && ctest --test-dir build
  --output-on-failure`; the shared build adds `-DBUILD_SHARED_LIBS=ON`. Keep `-j 6`; several workers share
  the host. After merging `main`, delete the build directory if headers, submodules or CMake lists changed.
  The CLI reference is generated: after adding a verb, run `./build/liquid docs --format markdown --out
  docs/reference/cli && ./build/liquid docs --format json --out docs/reference/cli`.
- lake: configure with `-DLAKE_BUILD_TESTS=ON
  -DLAKE_ZETTA_SOURCE_DIR=/Users/stevesperandeo/dev/homer6/orama-work/modules/zetta-bridge/modules/zetta`
  (the only authorised Zetta checkout; only its client transport is compiled). Tests need a fresh database on
  the local Homebrew Postgres 17: `createdb -h 127.0.0.1 -U stevesperandeo <name>`, `psql -h 127.0.0.1 -U
  stevesperandeo -d <name> -f db/schema.sql`, then `LAKE_TEST_DB_URI=postgresql://stevesperandeo@127.0.0.1:5432/<name>
  LAKE_INSTANCE_KEK=$(openssl rand -hex 32) ctest --test-dir build --output-on-failure`. UI changes also run
  `./tools/ui/test-token-gates.sh`. Never drop a database you did not create in the same run.
- liquify: `cmake -S . -B build -G Ninja && cmake --build build && ctest --test-dir build && ./build/liquify
  version && ./build/liquify --smoke 30`.
- k0s (`liquid` branch): the Makefile wraps Docker by default; always `make DOCKER=""
  EMBEDDED_BINS_BUILDMODE=none BUILD_GO_LDFLAGS_EXTRA="" <target>` or plain `go build ./... && go test ./pkg/... -short`.
- orama-operator: `go build ./... && go vet ./... && go test ./... && helm lint chart/`.
- **No CI** (Steve, umbrella `CLAUDE.md`): never add, enable or edit a CI workflow, and never wait on
  or cite CI. Linux proofs run on the cluster BuildKit lane (`lake-linux-test/run-lake-linux-tests.sh`,
  below); where no lane exists yet, a merge records "Linux proof deferred (decision 33)" on its issue
  and `docs/action-plan.md` lists the debt.

## Steve's requests: finish first, queue the rest

Finish the work in hand (built, tested, committed, pushed, deployed, checked) before starting a new
request. File an issue for every request the moment it is made, and add it to the **bottom** of the
queue epic: [lake#571](https://github.com/oramasearch/lake/issues/571) for lake, or a queue epic of
the same shape in the repository concerned. The queue's first unchecked item is the current work.
When it ships, close its issue with a comment, tick it in the queue, and take the next one. Read the
queue first after any context reset. The full rule is in liquid-bridge `CLAUDE.md` → *Steve's
requests: finish first, queue the rest*.

## Close each issue the moment its code is on a PR

When the change for an issue is pushed to its PR and complete, **close that issue right then** with a
comment: what changed (behaviour and files), the PR or commit URL, the proof, and anything deferred (as
a new linked issue, never a silent leftover). Do not wait for the merge, the deploy or the end of the
session, and do not batch closings. A shipped issue left open is a process bug. Never use `fixes #N` /
`closes #N` auto-close keywords. An epic stays open while it has open children and gets a progress
comment instead.

## Merging

Merge with a merge commit, `gh pr merge <n> --repo oramasearch/<repo> --merge --delete-branch`, after the suites
pass on the merged tree; k0s PRs target `liquid`, operator PRs target `main` (production: PR-based only,
never fast-forwarded). The issue is already closed (above); then bump the
bridge pointer: `git -C modules/<repo> fetch origin && git -C modules/<repo> checkout origin/main`, commit
"Bump <repo> submodule (...)", push, and run `python3 tools/issues/master_epic.py`. Never add AI attribution
or session trailers to commits or PRs.

## Updating lake on AKS

**This cluster is development, not production** (the names say `production` and `prod`; there is no
production yet — umbrella `CLAUDE.md`). Rolling it is routine: do it as part of the work.

Cluster: kube context `orama-production-cluster-01`, one node. lake runs from the `Lake` CR `lake/prod`
(`lakes.orama.cloud`), reconciled by the operator release `orama-operator` in `orama-system`. The
image build runs on the cluster's BuildKit (namespace `buildkit`, deployment `aks-amd640`, rootless, unix
socket only) driven by the local `buildctl` (`brew install buildkit`) over `kube-pod://`.

1. Registry auth for the push, without Docker: write a temporary `DOCKER_CONFIG` directory holding
   `config.json` with `{"auths":{"https://index.docker.io/v1/":{"auth":"<base64 user:token>"}}}`; the token
   comes from the keychain helper once (`echo https://index.docker.io/v1/ |
   /Applications/Docker.app/Contents/Resources/bin/docker-credential-desktop get`). Delete the directory
   afterwards. Never commit or log it.
2. Build and push (from `codex-work/lake` on `main`, submodules initialised):
   ```sh
   export DOCKER_CONFIG=<tmp dir>
   POD=$(kubectl --context orama-production-cluster-01 get pods -n buildkit -o jsonpath='{.items[0].metadata.name}')
   buildctl --addr "kube-pod://$POD?context=orama-production-cluster-01&namespace=buildkit" build \
     --frontend dockerfile.v0 --local context=. --local dockerfile=. \
     --local zetta=<minimal zetta context> --local liquid=<liquid source copy> \
     --opt context:zetta_source=local:zetta --opt context:liquid_source=local:liquid \
     --opt build-arg:LAKE_BUILD_REVISION=$(git rev-parse HEAD) --opt platform=linux/amd64 \
     --output type=image,name=docker.io/oramasearch/lake:<YYYYMMDD><a|b|c>,push=true --progress plain
   ```
   The final image holds only the `lake` binary and OpenSSL; the Zetta checkout is a build-stage input. Do not
   point `--local zetta=` at the full checkout (45 GB with build trees): assemble a minimal context first
   from the commit the zetta-bridge pins, without touching the checkout (about 2.6 MB):
   `git -C <zetta> archive <pin> include src/core/connect/http_transport.cpp src/core/api/native_http_transport.cpp src/core/runtime.cpp | tar -x -C <tmp>`,
   and pass that directory. The file list is whatever lake's `CMakeLists.txt` compiles into `zetta-api`
   (`src/core/runtime.cpp` joined it with lake#380); configure fails naming any file that is missing. Keep the
   context outside `/private/tmp`, or rebuild it before each build: macOS empties old files there (a
   context emptied that way failed the 2026-10-05 build with "does not contain the required zetta-api client
   headers").

   Since lake #145 (decision 42) liquid is a second named context, `liquid_source`: add
   `--local liquid=<tmp> --opt context:liquid_source=local:liquid`. **Never pass `modules/liquid`
   directly.** liquid's own `.dockerignore` excludes everything except its Linux binaries, so BuildKit
   transfers about 200 bytes and lake's configure fails with "LAKE_LIQUID_SOURCE_DIR does not contain a
   liquid source tree: /opt/liquid" (hit on the first post-#145 image, 2026-09-25). Copy the pinned
   checkout first, about 68 MB: `rsync -a --exclude .git --exclude '/build*' --exclude .dockerignore
   --exclude .liquid-store <bridge>/modules/liquid/ <tmp>/`, after checking `git -C modules/liquid
   status` is clean and its head is the bridge pin.
3. Schema: the operator applies `internal/controller/assets/lake-schema.sql` (a byte-identical copy of lake `db/schema.sql`,
   idempotent) through the `PostgresSchema` `lake-prod-controldb-schema` Job. When lake's schema changed,
   first vendor the new file into the operator (PR, merge), rebuild the operator image (step 5), then delete
   the owned `PostgresSchema` object so the reconciler recreates it and the Job re-runs:
   `kubectl -n lake delete postgresschema lake-prod-controldb-schema`. Tables created outside the Job must be
   owned by role `lake` (`ALTER TABLE ... OWNER TO lake`).
4. Roll lake: patch the CR image and watch the rollout:
   ```sh
   kubectl --context orama-production-cluster-01 -n lake patch lake prod --type merge -p '{"spec":{"image":"oramasearch/lake:<tag>"}}'
   kubectl --context orama-production-cluster-01 -n lake rollout status deploy/lake-prod
   kubectl --context orama-production-cluster-01 -n lake get lake prod -o jsonpath='{.status.conditions}'
   ```
   The store volume (100 GiB, `managed-csi`) and the instance key Secret `lake-prod-instance-kek` are
   reused; never delete either (the key is not backed up anywhere else yet).

   **Where the helpers live.** Everything reusable is in `~/dev/oramasearch/codex-work/build/`, never in
   `/private/tmp` (macOS emptied it on 2026-10-07, taking every helper, the registry credential and the
   build contexts with it):
   - `scripts/`: `env.sh` (paths, `DOCKER_CONFIG`), `build-lake.sh <tag>` (builds `wt/lake/deploy-next`,
     rolls only on success), `build-operator.sh`, `opcall.sh`, `copyrec.sh`;
   - `contexts/`: `zetta-pin` (from the zetta-bridge pin with `git archive`) and `liquid-<sha>` (rsync of the
     pinned liquid). Refresh both when a pin moves;
   - `.dockercfg/`: the registry credential, mode 0700, from the keychain helper. Never commit it or print it;
   - `lake-linux-test/run-lake-linux-tests.sh <worktree> <label> '<gtest filter>' '<ctest regex>'`: builds
     lake's tests on Linux on the cluster BuildKit and runs them, pushing nothing. **Any change to lake,
     liquid or corosio passes its affected tests on Linux before it merges.** lake#545 passed on macOS and
     broke every connection on Linux (lake#546). Run one at a time: the BuildKit pod has a 12 GiB limit;
   - `briefs/`: the agent preamble and briefs.

   **Zetta images** (the bus `spec.zetta.image` and every workspace Zetta `spec.services.zettaImage`,
   which also sets the image of workspaces created later). Zetta's repo carries no Dockerfile; the recipe
   lives in `codex-work/build/zetta/` (`Dockerfile`, `build-zetta.sh`). It was reconstructed on 2026-10-06
   from the image history of `dev-b82a5e94` after the only copy, in `/private/tmp`, was emptied. Never keep
   build recipes or contexts in `/private/tmp`. Build from a Zetta clone on `origin/dev`:
   `build/zetta/build-zetta.sh ~/dev/oramasearch/codex-work/zetta dev-<sha8>`. Check the push answered, check an anonymous
   `curl https://hub.docker.com/v2/repositories/oramasearch/zetta/` gives 404, then patch both image fields on
   `Lake/prod` and wait for every `*-zetta-0` pod to be Ready on the new tag. Since lake#535 lake relies on
   zetta#1235 (prefix durability, `dev-5f70b306` or later); never roll a workspace Zetta back past that.
5. Operator: the Helm release is `orama-operator`; the one-time handoff from `orama-cloud-v1-operator`
   (the operator's `docs/operations/rename-cutover.md`) is done. Build the same way from `codex-work/orama-operator` on `main`
   (`--output type=image,name=docker.io/oramasearch/orama-operator:main-<sha>,push=true`, no Zetta context),
   apply CRDs first because helm does not update them, then upgrade the release with the stored values as a
   file rather than `--reuse-values` (a chart that gained a new value, such as `controlPlane.service.port`,
   fails to template under `--reuse-values` because stored values do not pick up new chart defaults):
   ```sh
   kubectl --context orama-production-cluster-01 apply -f chart/crds/
   helm --kube-context orama-production-cluster-01 get values orama-operator -n orama-system > /tmp/operator-values.yaml
   helm --kube-context orama-production-cluster-01 upgrade orama-operator chart/ -n orama-system -f /tmp/operator-values.yaml --set operator.image.tag=main-<sha>
   kubectl --context orama-production-cluster-01 -n orama-system rollout status deploy/orama-operator
   ```
6. Check: `curl -s -o /dev/null -w '%{http_code}' https://lake.oramadev.net/` returns 200 (use GET: lake routes pages for GET only, so `curl -I` answers 404), `GET /v1/server_info` reports the revision you built, and the page references the new hashed
   stylesheet; purge Cloudflare if an unhashed asset is stale (zone `a26a1f7171915e478a51f37f92838065`,
   token in the cluster Secret `cloudflare-api-token`, `POST /client/v4/zones/<zone>/purge_cache` with
   `{"purge_everything":true}`).
7. Record the deploy in `docs/action-plan.md` (deployment paragraph) and on issue #7.

## What needs Steve

Any new Linux proof lane on the cluster, secrets and tokens (Cloudflare,
registry, R2 backups), destructive database actions, and the decisions listed open on issue #7.
