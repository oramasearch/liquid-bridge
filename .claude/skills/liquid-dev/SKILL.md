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
- Linux proofs run off this machine (hosted CI once `ORAMA_SUBMODULES_TOKEN` exists); until then a merge
  records "Linux proof deferred (decision 33)" on its issue and `docs/action-plan.md` lists the debt.

## Merging

Squash-merge with `gh pr merge <n> --repo oramasearch/<repo> --squash --delete-branch` after the suites
pass on the merged tree; k0s PRs target `liquid`, operator PRs target `main` (production: PR-based only,
never fast-forwarded). Close the issue with what was done, the proof, and what was deferred; then bump the
bridge pointer: `git -C modules/<repo> fetch origin && git -C modules/<repo> checkout origin/main`, commit
"Bump <repo> submodule (...)", push, and run `python3 tools/issues/master_epic.py`. Never add AI attribution
or session trailers to commits or PRs.

## Updating lake on AKS

Cluster: kube context `orama-production-cluster-01`, one node. lake runs from the `Lake` CR `lake/prod`
(`lakes.orama.cloud`), reconciled by the operator release `orama-cloud-v1-operator` in `orama-system`. The
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
   point `--local zetta=` at the full checkout (45 GB with build trees): assemble a minimal context first,
   `rsync -a --exclude .git <zetta>/include/ <tmp>/include/` plus `src/core/connect/http_transport.cpp` and
   `src/core/api/native_http_transport.cpp` under the same paths (about 2 MB), and pass that directory.

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
5. Operator: since orama-operator #148 (2026-09-06) the chart, module and release are named `orama-operator`,
   while production still runs the Helm release `orama-cloud-v1-operator` from before the rename. The next
   operator deploy must first run the one-time handoff in the operator's `docs/operations/rename-cutover.md`
   (both releases briefly installed, the leader-election lease preserved, the former release retired; it
   records values, CRD UIDs and the lease UID before touching anything). After that, replace the release
   name below with `orama-operator`. Build the same way from `codex-work/orama-operator` on `main`
   (`--output type=image,name=docker.io/oramasearch/orama-operator:main-<sha>,push=true`, no Zetta context),
   apply CRDs first because helm does not update them, then upgrade the release with the stored values as a
   file rather than `--reuse-values` (a chart that gained a new value, such as `controlPlane.service.port`,
   fails to template under `--reuse-values` because stored values do not pick up new chart defaults):
   ```sh
   kubectl --context orama-production-cluster-01 apply -f chart/crds/
   helm --kube-context orama-production-cluster-01 get values orama-cloud-v1-operator -n orama-system > /tmp/operator-values.yaml
   helm --kube-context orama-production-cluster-01 upgrade orama-cloud-v1-operator chart/ -n orama-system -f /tmp/operator-values.yaml --set operator.image.tag=main-<sha>
   kubectl --context orama-production-cluster-01 -n orama-system rollout status deploy/orama-cloud-v1-operator
   ```
6. Check: `curl -s -o /dev/null -w '%{http_code}' https://lake.oramadev.net/` returns 200 (use GET: lake routes pages for GET only, so `curl -I` answers 404), `GET /v1/server_info` reports the revision you built, and the page references the new hashed
   stylesheet; purge Cloudflare if an unhashed asset is stale (zone `a26a1f7171915e478a51f37f92838065`,
   token in the cluster Secret `cloudflare-api-token`, `POST /client/v4/zones/<zone>/purge_cache` with
   `{"purge_everything":true}`).
7. Record the deploy in `docs/action-plan.md` (deployment paragraph) and on issue #7.

## What needs Steve

`ORAMA_SUBMODULES_TOKEN` for hosted CI, any Linux proof lane on the cluster, secrets and tokens (Cloudflare,
registry, R2 backups), destructive database actions, and the decisions listed open on issue #7.
