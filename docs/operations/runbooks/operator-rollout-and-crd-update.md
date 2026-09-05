# Operator rollout and CRD update

The operator is the helm release `orama-cloud-v1-operator` in `orama-system` (chart
`orama-cloud-v1-operator-0.1.0`, revision 16 on 2026-09-05), running
`oramasearch/orama-operator:lake-crd-<sha>` from branch `feat/lake-crd` until PR #118 lands
(operator #119). It reconciles `Lake/prod`, the two Zetta sandbox clusters and `OramaCloudV1/v1`.
Two facts drive this runbook: **helm never updates the CRDs in `chart/crds/`** after install, and
**the chart ClusterRole is hand-maintained** — a CR kind or owned kind the role does not grant
makes the manager CrashLoop on cache sync (operator `docs/lake/README.md` *RBAC*, bridge
`repositories.md`).

## Symptoms (when a rollout went wrong)

| Symptom | Cause |
|---|---|
| `kubectl apply` of a `Lake` with a new field is rejected `unknown field "spec.store"` / the field is silently dropped | CRD not updated; helm upgraded only the Deployment |
| Manager pod `CrashLoopBackOff`, log `failed to wait for caches to sync` / `is forbidden: … cannot list resource "scheduledbackups"` | ClusterRole missing a kind the new controller owns |
| `helm upgrade` fails `conflict with "kubectl-set"` on `spec.template.spec.containers[0].image` | server-side apply ownership from an earlier `kubectl set image`; needs `--force-conflicts`, which the owner runs |
| `Lake` status stops updating; `kubectl get lake` columns blank | manager not running or not the leader |
| Pods run an old image although the tag "changed" | mutable tag with `IfNotPresent` (operator `docs/install.md`); use immutable tags |

## Procedure (routine)

From the operator checkout on the branch to deploy (today `feat/lake-crd`):

```sh
cd /Users/stevesperandeo/dev/oramasearch/codex-work/orama-operator && git log --oneline -1
SHA=$(git rev-parse --short HEAD)

# 1. build natively on the AKS builder (see roll-lake-image.md for creating it), load, push
docker buildx build --builder aks-amd64 --platform linux/amd64 \
  -t oramasearch/orama-operator:lake-crd-$SHA --load .
docker image inspect oramasearch/orama-operator:lake-crd-$SHA --format '{{.Config.Entrypoint}} {{.Architecture}}'   # /manager amd64
docker push oramasearch/orama-operator:lake-crd-$SHA                    # the owner runs the push

# 2. CRDs first — helm will not
kubectl apply -f chart/crds/orama.cloud_lakes.yaml
kubectl apply -f chart/crds/                                            # all of them when more than the Lake changed

# 3. the release
helm upgrade orama-cloud-v1-operator ./chart -n orama-system \
  --set operator.image.repository=oramasearch/orama-operator \
  --set operator.image.tag=lake-crd-$SHA \
  --set 'operator.imagePullSecrets[0].name=oramasearch-dockerhub'
kubectl rollout status deploy/orama-cloud-v1-operator -n orama-system
```

If step 3 fails with a field-ownership conflict, the owner re-runs it with `--force-conflicts`
(the auto-mode classifier blocks that flag for the assistant).

## Diagnosis after a bad rollout

```sh
kubectl get pods -n orama-system -l app.kubernetes.io/name=orama-cloud-v1-operator
kubectl logs -n orama-system deploy/orama-cloud-v1-operator --tail=50 | grep -i -E 'forbidden|cache|error'
kubectl get crd lakes.orama.cloud -o jsonpath='{.spec.versions[0].schema.openAPIV3Schema.properties.spec.properties}' | jq 'keys'   # fields the CRD knows
helm history orama-cloud-v1-operator -n orama-system | tail -5
kubectl get clusterrole -o name | grep -i orama; kubectl describe clusterrole <name> | grep -A2 -E 'lakes|scheduledbackups|cloudflarednsrecords'
```

## Fix

- **CRD behind**: `kubectl apply -f chart/crds/orama.cloud_lakes.yaml`; the manager picks the
  schema up without a restart; re-apply the `Lake`.
- **RBAC gap**: add the kind to `chart/templates/rbac.yaml` (and `config/rbac/role.yaml`), commit,
  rebuild, `helm upgrade`; or, to stop the bleeding, `helm rollback orama-cloud-v1-operator
  <previous revision> -n orama-system` ([`rollback.md`](rollback.md)).
- **Manager down for long**: `Lake/prod` keeps serving — the Deployment, Service, Ingress and DNS
  record are already there. Nothing reconciles, so do not change the CR until the manager is
  back; the status columns are stale, not the service.

## Verification

```sh
kubectl get deploy -n orama-system orama-cloud-v1-operator -o jsonpath='{.spec.template.spec.containers[0].image}{"\n"}'
kubectl logs -n orama-system deploy/orama-cloud-v1-operator --tail=20 | grep -c '"controller":"lake"'   # reconciles are happening
kubectl get lake prod                                  # all columns populated, PHASE Ready
kubectl get lake prod -o jsonpath='{.status.conditions[*].type}{"\n"}'   # StoreReady BackupReady
```

Then update operator `docs/lake/README.md` (*Deploying* and *Current production instance*) and
lake `docs/deployment/aks.md` with the new revision and tag, in the PR that shipped the change.

## Who to page

operator maintainer; lake on-call if `Lake/prod` was affected. Operator PRs are merged by the
owner (decisions.md §7).
