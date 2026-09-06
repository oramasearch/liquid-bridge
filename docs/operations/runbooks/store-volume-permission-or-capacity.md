# Store volume: permission, provisioning or capacity

The store volume is the PVC `lake-prod-store` (100 Gi, `managed-csi`, `ReadWriteOnce`), mounted
at `/var/lib/lake/store` as `LAKE_STORE_ROOT`. It holds **every customer's liquid store**
(`<customer id>/store`: packs, index, collector state) and the **transparency log**
(`prod/log/…`). It is production data (lake `docs/deployment/store-volume.md`, operator
`docs/lake/README.md` *Store volume*).

## Symptoms

| Symptom | Likely cause |
|---|---|
| Repository pages answer 500; API `push`/`pull`/`repository_tree` fail; lake log shows `cannot create directories: Permission denied [/var/lib/lake/store/<customer>/store/packs]` | the volume mounted root-owned and the pod lacks `fsGroup: 10001` (seen 2026-09-05, fixed by operator PR #138) |
| New lake pod `Pending` for minutes; `kubectl describe pod` shows `FailedScheduling … binding volumes` and the PVC has `ProvisioningFailed … mountVolume is not supported for access mode: MULTI_NODE_MULTI_WRITER` | the claim asks for `ReadWriteMany` on an Azure *disk* class (`managed-csi`, `default`); Azure disk is single-node only (seen 2026-09-05) |
| Rollout stuck with the new pod `Pending` and `Multi-Attach error for volume` | RWO volume still attached to the old pod on another node (single node today, so only after a second node exists), or `replicas` > 1 with RWO |
| Push fails with `500`, lake log shows `No space left on device`; `lake_store_calls_total{result!="ok"}` rising; metering `stored_bytes` near 100 GiB | volume full |
| `Lake` condition `StoreReady=False`, `kubectl get lake prod` STORE column empty | PVC unbound or missing |

## Diagnosis

```sh
kubectl get lake prod -o jsonpath='{.status.store}{"\n"}{.status.conditions}{"\n"}'
kubectl get pvc -n lake lake-prod-store -o wide
kubectl describe pvc -n lake lake-prod-store | sed -n '/Events/,$p'
kubectl get events -n lake --sort-by=.lastTimestamp | tail -20
kubectl get deploy -n lake lake-prod -o jsonpath='{.spec.template.spec.securityContext}{"\n"}'   # expect fsGroup 10001
kubectl exec -n lake deploy/lake-prod -- df -h /var/lib/lake/store                              # capacity (read-only command)
kubectl exec -n lake deploy/lake-prod -- ls -ld /var/lib/lake/store                              # owner/group; expect group 10001 or setgid dir
```

The kubelet also exports `kubelet_volume_stats_available_bytes{persistentvolumeclaim="lake-prod-store"}`
to the Azure Monitor managed Prometheus; the [`../slos.md`](../slos.md) headroom objective is 20 %.

## Fix

**Permission denied.** The operator must run the pod with `fsGroup: 10001` and
`fsGroupChangePolicy: OnRootMismatch` (operator `lake_controller.go`, PR #138). If the Deployment
lacks it, the running operator predates #138: roll the operator
([`operator-rollout-and-crd-update.md`](operator-rollout-and-crd-update.md)). Never `chown` inside
the pod as a fix; it is lost with the pod and hides the real cause.

**RWX on an Azure disk class.** The operator never mutates a created claim. Two exits:

- `replicas: 1` and a new claim with `spec.store.accessModes: [ReadWriteOnce]` — the path taken
  on 2026-09-05. Because the operator will not replace the claim, this means a **new** claim
  name via `spec.store.existingClaim` pointing at a PVC you create, or deleting the Lake's
  owned PVC while the pod is down (data loss if it held anything — it did not on 2026-09-05).
- Real RWX for multiple replicas: an Azure Files class (`azurefile-csi-premium`) as
  `spec.store.storageClassName` on a fresh claim. Not validated for libliquid's file locking;
  treat as an operator #125/#122 design item, not an on-call move.

**Capacity.** `managed-csi` allows expansion and the operator never resizes, so resize the PVC
directly (this is the one case where touching an owned object is right, because the operator
does not manage the field):

```sh
kubectl patch pvc lake-prod-store -n lake -p '{"spec":{"resources":{"requests":{"storage":"200Gi"}}}}'
kubectl get pvc -n lake lake-prod-store -w        # CAPACITY grows; Azure disk expands online for attached disks in most SKUs, otherwise after a pod restart
```

Also take a disk snapshot first if the volume is near full and the write pattern is unknown
([`disaster-recovery.md`](disaster-recovery.md)). Then: is the growth customers or garbage?
`metering_usage` per customer (`GET /v1/metering_usage?customer_id=…`) sums unique stored bytes;
tombstoned repositories are collected after their 30-day retention (lake
`docs/api/repositories.md`), so a large recent delete does not free space at once.

**Unbound / missing claim.** `kubectl get lake prod -o jsonpath='{.spec.store}'`; if
`existingClaim` names a PVC that does not exist, create it or fix the name; if the operator-created
claim is gone, the operator recreates it **empty** — stop and go to
[`disaster-recovery.md`](disaster-recovery.md) before the pod starts writing to it.

## Verification

```sh
kubectl get lake prod                                            # STORE lake-prod-store, PHASE Ready
kubectl get pvc -n lake lake-prod-store                          # Bound, expected CAPACITY
curl -sS https://<host>/v1/repository_tree?id=<public repo>&ref=<ref> | head -c 300
kubectl logs -n lake deploy/lake-prod --since=5m | grep -c 'Permission denied'    # 0
```

## Who to page

lake on-call; the operator maintainer for `fsGroup`, claim replacement or the RWX design; the
Azure subscription owner if the disk SKU refuses expansion or a snapshot is needed.
