# Rollback

Two rollbacks exist, and they are independent: **lake** (the image in the `Lake` CR) and **the
operator** (the helm release). The control-plane schema does **not** roll back — migrations are
additive and idempotent, and lake images tolerate extra tables, so the rule is "roll the image
back, leave the schema".

## Lake image

**Symptoms that call for it.** After a roll: crash loop the CR cannot fix in one apply
([`pod-crash-loop-missing-variable.md`](pod-crash-loop-missing-variable.md)), 500s on routes that
worked, a broken sign-in, or the SLO fast-burn alert.

**Fix.** Re-apply the previous CR manifest — the file saved before the roll — or set the previous
tag:

```sh
kubectl apply -f lake-prod-cr.json                      # the pre-roll manifest, or:
kubectl get lake prod -o json | jq 'del(.status, .metadata.resourceVersion, .metadata.uid, .metadata.generation, .metadata.creationTimestamp, .metadata.managedFields) | .spec.image = "oramasearch/lake:<previous tag>"' | kubectl apply -f -
kubectl rollout status deploy/lake-prod -n lake
```

The previous tag is in the Deployment's ReplicaSet history when the manifest is lost:
`kubectl get rs -n lake -l app.kubernetes.io/name=lake --sort-by=.metadata.creationTimestamp -o
jsonpath='{range .items[*]}{.metadata.creationTimestamp} {.spec.template.spec.containers[0].image}{"\n"}{end}'`.
Do not `kubectl rollout undo deploy/lake-prod`: the operator re-applies the CR's image on its
next reconcile and undoes the undo.

**Data written by the newer image** stays: rows in new tables are ignored by the older image;
store-volume content is liquid's format, versioned by liquid, and older lake images read what
they wrote. A newer image that *changed* a liquid store format would say so in its release
notes; check before rolling back across such a change.

**Verification.** As in [`roll-lake-image.md`](roll-lake-image.md): image on the pods, startup
JSON, `server_info` version, `/v1/identity` `ok:true`, `kubectl get lake prod` Ready. Then the
incident file gets the reason.

## Operator

**Symptoms.** Manager CrashLoop after `helm upgrade`, `Lake` status frozen, reconcile errors in
the manager log ([`operator-rollout-and-crd-update.md`](operator-rollout-and-crd-update.md)).

**Fix.**

```sh
helm history orama-cloud-v1-operator -n orama-system | tail -5
helm rollback orama-cloud-v1-operator <previous good revision> -n orama-system
kubectl rollout status deploy/orama-cloud-v1-operator -n orama-system
```

Done on 2026-09-02 (revision 10 = rollback to 8, after revisions 9 pointed at a mis-built image).
CRDs are **not** rolled back by helm and should not be: a newer CRD schema is a superset the
older manager ignores. If the older manager cannot list a kind the newer CRD added as owned, that
is the RBAC case in the operator runbook, not a CRD problem.

**Verification.** Manager image is the previous tag; `kubectl get lake prod` columns update again;
`Lake/prod` pods untouched (a manager rollback does not restart lake unless the Deployment
template differs between manager versions — check `kubectl get rs -n lake` for a new ReplicaSet
and be ready to roll lake back too).

## What cannot be rolled back

| Change | Why | What to do instead |
|---|---|---|
| Schema migrations | additive, idempotent, never reverted | leave them; roll the image |
| `LAKE_PUBLIC_HOST` after passkeys or applications exist | RP ID and issuer are one-way ([`../lake-live-host.md`](../lake-live-host.md)) | do not change it in a rollback |
| Deleting `lake-prod-instance-kek` or letting the operator re-mint it | every wrapped key becomes unreadable | [`disaster-recovery.md`](disaster-recovery.md) |
| `spec.postgres.enabled: false` | deletes the CNPG cluster **and its data** | never as a rollback step |
| A purge, a DNS record deletion | already propagated | re-create forward |

## Who to page

lake on-call (lake image); operator maintainer (helm rollback). Both write the review.
