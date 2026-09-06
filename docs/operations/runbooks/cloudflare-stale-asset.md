# Cloudflare serving a stale asset

lake serves `/style.css` with `cache-control: public, max-age=86400` (lake `docs/serving/http.md`)
and the URL never changes, so after a rollout that changes the stylesheet Cloudflare keeps serving
the old bytes for up to a day (`cf-cache-status: HIT`, `age:` climbing) while the HTML references
new classes. Seen 2026-09-05 after `20260905a` and purged by hand; the permanent fix is
content-hashed asset URLs, lake #98. Pages and `/v1` are `cache-control: no-store`
(`cf-cache-status: DYNAMIC`) and are never the problem.

## Symptoms

- Pages render unstyled or with the previous design right after an image roll; a hard refresh
  does not help; an incognito window does not help.
- `curl -sSI https://<host>/style.css | grep -i -E 'cf-cache-status|age|etag'` shows `HIT`, a
  large `age`, and an `etag` different from what the pod serves:
  `kubectl exec -n lake deploy/lake-prod -- wget -qS -O /dev/null http://127.0.0.1:4900/style.css 2>&1 | grep -i etag`
  (or compare `curl -sS http://<pod ip>:4900/style.css | sha256sum` from a debug pod).

## Diagnosis

Confirm it is the edge cache, not a half-rolled Deployment: `kubectl rollout status
deploy/lake-prod -n lake` complete and every pod on the new image (`kubectl get pods -n lake -o
jsonpath='{.items[*].spec.containers[0].image}'`). Only when all pods serve the new bytes and the
edge serves old ones is a purge right.

## Fix

Purge the one file. The zone id is the `zoneID` key of the Secret `cloudflare-api-token` in
`lake` (the `oramadev.net` zone today; `cloudflare-lake-live` after
[`../lake-live-host.md`](../lake-live-host.md)); read only that key:

```sh
ZONE=$(kubectl get secret cloudflare-api-token -n lake -o jsonpath='{.data.zoneID}' | base64 -d)
```

The **token** to call the purge API with is **not** the cluster's DNS token unless it also has
`Zone → Cache Purge → Purge`; the cluster token is scoped to DNS edit by design. Use the on-call's
purge token (a Cloudflare API token with *Cache Purge* on the zone, kept in the on-call's
password manager, never in the cluster):

```sh
curl -sS -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE/purge_cache" \
  -H "Authorization: Bearer $CF_PURGE_TOKEN" -H 'Content-Type: application/json' \
  --data '{"files":["https://lake.oramadev.net/style.css"]}'
# → {"success":true, ...}
```

Purge by URL is exact (scheme and host included); list every affected asset (`/style.css`, font
files if they are ever cached). `{"purge_everything":true}` is allowed on every plan but empties
the whole zone's cache; not needed for lake, whose only cached route is the stylesheet.

Dashboard alternative: zone → *Caching* → *Configuration* → *Purge Cache* → *Custom Purge* → URL.

## Verification

```sh
curl -sSI https://<host>/style.css | grep -i -E 'cf-cache-status|age|etag'    # MISS or EXPIRED, then HIT with age near 0 and the new etag
```

Load `/` from two networks (or `curl -H 'Accept: text/html'` and compare the `<link>`'s target
with the served CSS). Note the purge in the incident file.

## Prevention

lake #98: the stylesheet and fonts under `/style-<hash>.css` served `immutable`, HTML linking the
hashed name; no purge on rollout. Until it lands, the
[`roll-lake-image.md`](roll-lake-image.md) checklist ends with "purge `/style.css` if the
stylesheet changed".

## Who to page

lake on-call (holds the purge token); the Cloudflare account owner if the token is missing.
