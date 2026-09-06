# Certificate or DNS failure

Traffic path: client → Cloudflare edge (TLS terminated with Cloudflare Universal SSL, proxied
record) → HTTP to the shared ingress-nginx LoadBalancer `172.212.70.79:80` → Ingress `lake-prod`
(host rule) → Service `lake-prod:80` → pod `:4900`. The DNS record is the operator-owned
`CloudflareDNSRecord lake-prod-dns`, created from `spec.host` + `spec.dnsSecretRef` once the
Ingress has an address (operator `docs/crd-reference.md`, `Lake`). There is **no TLS at the
origin** and no cert-manager; the edge certificate is Cloudflare's.

## Symptoms

| Symptom | Where the break is |
|---|---|
| `dig +short <host>` returns nothing or `NXDOMAIN` | record missing: torn down (`ingressEnabled` false or `host` changed), token invalid, or wrong zone Secret |
| `dig` returns `172.212.70.79` directly (not `104.21.x`/`172.67.x`) | record exists but is **not proxied** → no edge TLS; browsers get a certificate error or plain HTTP |
| Browser: certificate for a different name / `ERR_SSL_VERSION_OR_CIPHER_MISMATCH` | Universal SSL not (yet) issued for the zone, or the host is a second-level subdomain the wildcard does not cover (`a.b.lake.live`) |
| Cloudflare `521 Web server is down` / `522 Connection timed out` | edge cannot reach `172.212.70.79:80`: ingress-nginx down, LoadBalancer changed, NSG |
| Cloudflare `525 SSL handshake failed` / `526` | zone SSL mode set to Full/Full (strict) while the origin is HTTP-only |
| Cloudflare `502`/`504` with `server: cloudflare` and an nginx page behind | ingress up, lake Service has no ready endpoints ([`pod-crash-loop-missing-variable.md`](pod-crash-loop-missing-variable.md)) |
| Works by IP with `--resolve`, fails by name | DNS |
| `kubectl get cloudflarednsrecords -n lake` `READY false` | operator could not create/update the record: token, zone id, duplicate record |

## Diagnosis

```sh
dig +short <host>; dig +short NS <zone>                      # Cloudflare proxy IPs; Cloudflare nameservers
kubectl get cloudflarednsrecords -n lake -o wide
kubectl describe cloudflarednsrecord lake-prod-dns -n lake | sed -n '/Status/,$p'
kubectl get ingress -n lake lake-prod                         # ADDRESS 172.212.70.79
kubectl get svc -n ingress-nginx ingress-nginx-controller      # EXTERNAL-IP unchanged
kubectl get pods -n ingress-nginx
curl -sS -o /dev/null -w '%{http_code}\n' -H 'Host: <host>' http://172.212.70.79/healthz          # origin path, bypassing Cloudflare: 200
curl -sS --resolve <host>:443:104.21.41.109 https://<host>/healthz -o /dev/null -w '%{http_code}\n'    # edge path with a pinned edge IP
openssl s_client -connect <host>:443 -servername <host> </dev/null 2>/dev/null | openssl x509 -noout -subject -issuer -dates
kubectl logs -n orama-system deploy/orama-cloud-v1-operator --tail=100 | grep -i -E 'cloudflare|dns'
kubectl get secret cloudflare-api-token -n lake -o jsonpath='{.data}' | jq 'keys'                  # ["token","zoneID"] — names only
```

## Fix

- **Record missing, operator error about the token or zone**: the Secret in `lake` must hold the
  zone of `spec.host` (`oramadev.net` today; `lake.live` after the move). Fix the Secret (owner
  creates a new token; [`../lake-live-host.md`](../lake-live-host.md) §2), then the operator
  retries on its next reconcile. To force one: an annotation change on the `Lake` (`kubectl
  annotate lake prod ops/touch="$(date -u +%s)" --overwrite`).
- **Record not proxied**: the operator sets `proxied: true`; a hand edit in the dashboard turned
  it off. Turn it back on in the dashboard (the operator's update also restores it).
- **Duplicate record** (`81053`/`81057` in the operator log): a record with the same name exists
  in the zone that the operator does not own. Delete it in the dashboard; the operator creates
  its own.
- **Edge certificate wrong**: dashboard → SSL/TLS → Edge Certificates: Universal SSL status
  *Active*; if *Pending validation* the zone's nameservers are not yet Cloudflare's. Second-level
  subdomains are not covered by `*.lake.live`; use one level or an Advanced Certificate.
- **521/522**: ingress-nginx or the LoadBalancer. `kubectl rollout restart deploy
  ingress-nginx-controller -n ingress-nginx` if its pod is unhealthy; if `EXTERNAL-IP` changed,
  the operator updates the record when the Ingress status changes (it re-queues the `Lake`).
- **525/526**: the zone SSL mode is ahead of the origin. Set it back to *Flexible* until the
  Origin CA certificate and operator #122 land ([`../lake-live-host.md`](../lake-live-host.md) §3).
- **Origin healthy, edge failing, nothing else changed**: check https://www.cloudflarestatus.com;
  a Cloudflare incident is communicated on the status page as an upstream incident.

## Verification

```sh
dig +short <host>                                              # two Cloudflare proxy addresses
curl -sS https://<host>/healthz                                # {"ok":true}
curl -sSI https://<host>/ | grep -i -E '^HTTP|server: cloudflare|strict-transport'
kubectl get cloudflarednsrecords -n lake                       # READY true
```

## Who to page

lake on-call; Cloudflare account owner for zone settings and tokens; operator maintainer if the
`CloudflareDNSRecord` controller misbehaves (issues #82–#85 describe its known edges for load
balancers).
