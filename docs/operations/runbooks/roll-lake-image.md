# Rolling lake to a new image

Ship a new `oramasearch/lake:<tag>` to `Lake/prod`. Two build paths: the intended one is the
GitHub Actions `image` workflow on a pushed Git tag (lake `docs/build/container-image.md`,
`docs/build/ci.md`), blocked on the org secrets as of 2026-09-05; the working one is a native
amd64 build on the AKS builder, which is what every 2026-09-05 roll used. Emulated builds on Apple
Silicon are far too slow and hit `Illegal instruction`; never push one.

## Before you start

- [`../slos.md`](../slos.md) budget: more than half spent this month → fixes only.
- The image is on lake `main` (or the PR is merged) and its CI is green.
- The schema: if the image needs migrations the database lacks, the operator's vendored copy
  must land first (`PostgresSchema` `VERSION` == the migration set the image expects;
  [techops-docs `schema-job-failure.md`](https://github.com/oramasearch/techops-docs/blob/main/docs/lake/runbooks/schema-job-failure.md)). lake reports missing
  tables as 500s, not at startup.
- New required variables in the image → add them to `spec.env` in the same CR apply
  ([techops-docs `lake-pod-restarts.md`](https://github.com/oramasearch/techops-docs/blob/main/docs/lake/runbooks/lake-pod-restarts.md)).
- Note the current image for rollback: `kubectl get lake prod -o jsonpath='{.spec.image}'`.

## Build on the `aks-amd64` builder

```sh
cd /Users/stevesperandeo/dev/oramasearch/codex-work/lake && git checkout main && git pull --ff-only
TAG=$(date -u +%Y%m%d)a          # immutable, date-based, letter-suffixed: 20260905a, 20260905b

# create the builder if it is not there (it lives in namespace buildkit; remove it after — 2 CPU / 4 GiB while idle)
docker buildx inspect aks-amd64 >/dev/null 2>&1 || docker buildx create --name aks-amd64 \
  --driver kubernetes --platform linux/amd64 --bootstrap \
  --driver-opt namespace=buildkit,replicas=1,rootless=true,requests.cpu=2,requests.memory=4Gi,limits.cpu=6,limits.memory=12Gi

docker buildx build --builder aks-amd64 --platform linux/amd64 -t oramasearch/lake:$TAG --load .
docker image inspect oramasearch/lake:$TAG --format '{{.Config.Entrypoint}} {{.Config.Cmd}} {{.Architecture}} {{.Config.User}}'
# expect: [lake] [--listen 0.0.0.0:4900] amd64 10001:10001   — a wrong entrypoint shipped once (2026-09-02, operator tag carrying lake's binary)
docker push oramasearch/lake:$TAG               # the owner runs the push
docker buildx rm aks-amd64                       # frees the node reservation
```

Build contexts are absolute paths (bridge `CLAUDE.md`, *Deploy hygiene*).

## Apply the CR

Take the current CR as JSON, change only `spec.image`, apply. Keep the manifest file: it is the
rollback artefact.

```sh
kubectl get lake prod -o json | jq 'del(.status, .metadata.resourceVersion, .metadata.uid, .metadata.generation, .metadata.creationTimestamp, .metadata.managedFields)' > lake-prod-cr.json
jq --arg img "oramasearch/lake:$TAG" '.spec.image = $img' lake-prod-cr.json > lake-prod-cr.new.json
kubectl apply -f lake-prod-cr.new.json
kubectl rollout status deploy/lake-prod -n lake
```

With `replicas: 1` the Deployment's `RollingUpdate` (`maxSurge 25%`, `maxUnavailable 25%`) starts
the new pod before stopping the old one; the readiness probe on `GET /` gates the switch. The
store PVC is RWO on one node, so both pods can mount it — a second node would make this a
`Multi-Attach` wait ([`store-volume-permission-or-capacity.md`](store-volume-permission-or-capacity.md)).

## Verification

```sh
kubectl get pods -n lake -l app.kubernetes.io/name=lake -o jsonpath='{.items[*].spec.containers[0].image}{"\n"}'
kubectl logs -n lake deploy/lake-prod | head -1                           # startup JSON: version, store postgres, log_mode
curl -sS https://<host>/v1/server_info | jq '.value.version, .value.store'
curl -sS https://<host>/v1/identity | jq .ok                              # true: KEK and identity intact
curl -sS -o /dev/null -w '%{http_code}\n' https://<host>/repositories       # 200 or 303
curl -sSI https://<host>/style.css | grep -i cf-cache-status              # if the stylesheet changed: see techops-docs docs/lake/runbooks/cloudflare-edge.md, case F
kubectl get lake prod                                                       # READY 1, PHASE Ready
```

Then a signed-in page load and, when the synthetic client exists, one push and pull. Record the
tag, the date and the operator revision in lake `docs/deployment/aks.md` (*What exists*) in the
PR that shipped the change.

## If it goes wrong

[`rollback.md`](rollback.md): re-apply `lake-prod-cr.json` (the previous image).

## Who to page

lake on-call performs the roll; the owner runs `docker push`. A roll is announced on the status
page as maintenance only if it needs a restart that drops requests (it should not with the surge
pod, but the single replica makes a readiness-probe failure a full outage).
