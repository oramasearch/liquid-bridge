# Moving the Lake host from lake.oramadev.net to lake.live

**What.** The plan to serve `Lake/prod` at `lake.live`: the Cloudflare zone token and its scope,
the Secret, the certificate path, the `Lake` CR change, redirects, what breaks and in what order
to change it. Two changes are **one-way doors** and are marked. Refs
https://github.com/oramasearch/liquid-bridge/issues/5; epic
https://github.com/oramasearch/liquid-bridge/issues/17.

**Why.** `Lake/prod` is public at https://lake.oramadev.net only because the one Cloudflare token
Secret on the cluster is scoped to the `oramadev.net` zone. The `Lake` CR's `dnsSecretRef` reads
`token` and `zoneID` from a Secret in `spec.namespace` and the Secret must hold the zone of
`spec.host` (operator `docs/crd-reference.md`, `Lake`). The product host is `lake.live`, and
several identity features bind to the host permanently, so the move should happen **before the
first customer registers a passkey or an application**.

## Where things stand (2026-09-05)

| | |
|---|---|
| `Lake/prod` | `spec.host: lake.oramadev.net`, `spec.dnsSecretRef: cloudflare-api-token`, `spec.env: LAKE_PUBLIC_HOST=lake.oramadev.net`, `ingressEnabled: true` |
| `lake.oramadev.net` | `CloudflareDNSRecord lake-prod-dns` → `172.212.70.79` (the shared ingress-nginx LoadBalancer), proxied |
| TLS | Cloudflare Universal SSL at the edge; the Ingress has **no `tls:`** — origin is HTTP on port 80 |
| `lake.live` | Already on Cloudflare: NS `jonah.ns.cloudflare.com`, `martha.ns.cloudflare.com`; the apex resolves to Cloudflare proxy addresses (`104.21.41.109`, `172.67.164.111`), so **a proxied record already exists at the apex**. Which account owns the zone and what that record serves are for the owner to confirm. |
| Identity binding | WebAuthn RP ID and the allowed origin are `LAKE_PUBLIC_HOST` (lake `docs/api/identity.md`); OAuth callbacks are `https://<LAKE_PUBLIC_HOST>/v1/oauth/<provider>/callback`; application JWTs carry `iss` and are verified against `https://<host>/v1/apps/<id>/.well-known/jwks.json` (lake `docs/api/apps.md`) |
| Customers | Seed data only (customer `steve`, repository `steve/liquid`); no passkeys or applications registered by anyone else, so the one-way doors are still open |

## 1. Decide the host

Two candidates. Pick one before creating anything.

| Host | For | Against |
|---|---|---|
| **`lake.live` (apex)** | The product is the domain, as `github.com` is. The WebAuthn RP ID becomes `lake.live`, which is a valid RP ID for any future origin under it (`app.lake.live`, `status.lake.live` is not affected). Shortest OIDC issuer. | The apex record exists already and serves something; it must be repointed. Everything else on the zone (marketing, status page) lives on subdomains. HSTS `includeSubDomains` is already sent by lake and will apply to every `*.lake.live` — fine, since they are all proxied. |
| `app.lake.live` | Leaves the apex for a marketing site. | The RP ID and issuer become `app.lake.live`; moving pages to the apex later would then be a second one-way door. lake's code sets the RP ID *equal to* `LAKE_PUBLIC_HOST`, so the RP ID cannot be `lake.live` while pages are served elsewhere without a lake change. |

**Recommendation: the apex, `lake.live`**, with the status page at `status.lake.live` and any
marketing under the `oramasearch` web properties. If the owner wants pages on a subdomain, file a
lake issue first to split `LAKE_RP_ID` from `LAKE_PUBLIC_HOST` so the RP ID can still be
`lake.live`; do not move the host until that lands.

## 2. Token and Secret (owner creates; never through a prompt)

Cloudflare dashboard → *My Profile* → *API Tokens* → *Create Custom Token*:

| Field | Value |
|---|---|
| Permissions | **Zone → DNS → Edit** (the operator creates, updates and deletes A records). Nothing else. Read is implied by Edit. |
| Zone Resources | **Include → Specific zone → `lake.live`** only |
| Client IP filtering | optional: the AKS egress address |
| TTL | none (rotate on a schedule instead; the operator reads the Secret on every reconcile, so rotation is a Secret update) |

Cache purge is a *different* permission (**Zone → Cache Purge → Purge**). Keep it on a separate
token held by the on-call, not in the cluster; the cluster token should only be able to do what
the operator does ([`runbooks/cloudflare-stale-asset.md`](runbooks/cloudflare-stale-asset.md)).

Zone ID: dashboard → `lake.live` → *Overview* → *API* panel, or
`GET https://api.cloudflare.com/client/v4/zones?name=lake.live` with the new token.

Create the Secret **with a new name** so the CR change is explicit and the `oramadev.net` copy
is untouched until the end:

```sh
kubectl create secret generic cloudflare-lake-live -n lake \
  --from-literal=token='<token>' --from-literal=zoneID='<zone id>'
```

Verify without printing the value: `kubectl get secret cloudflare-lake-live -n lake -o
jsonpath='{.data.zoneID}' | base64 -d` shows the 32-hex zone id; `DATA` is 2.

## 3. Certificate path

Nothing to issue for the edge: **Cloudflare Universal SSL** covers `lake.live` and `*.lake.live`
once the zone is active and the record is proxied, and renews itself. The Ingress stays HTTP on
port 80, so the zone's *SSL/TLS encryption mode* must be **Flexible** for the move to work as
`oramadev.net` does today. That leaves the Cloudflare → AKS hop in plaintext (finding 4 in
[`aks-housekeeping.md`](aks-housekeeping.md)).

Hardening, after the move and independent of it:

1. Issue a **Cloudflare Origin CA certificate** for `lake.live` (dashboard → SSL/TLS → Origin
   Server; 15-year lifetime; trusted only by Cloudflare) and store it as a `kubernetes.io/tls`
   Secret in `lake`.
2. Operator #122 adds `spec.tls.secretName` to the `Lake` and renders the Ingress `tls:` block.
3. Switch the zone to **Full (strict)**. Verify with `curl --resolve lake.live:443:172.212.70.79
   https://lake.live/healthz -k` (origin answers TLS) and then without `--resolve`.

cert-manager is not installed and is not needed for this path.

## 4. The `Lake` CR change

One `kubectl apply` changes three fields together — the host, the zone Secret, and the public
host lake binds identity to. Splitting them leaves a window where passkeys or OAuth are bound to
the wrong host.

```json
{
  "spec": {
    "host": "lake.live",
    "dnsSecretRef": { "name": "cloudflare-lake-live" },
    "env": [
      { "name": "LAKE_LOG_MODE", "value": "air-gapped" },
      { "name": "LAKE_PUBLIC_HOST", "value": "lake.live" }
    ]
  }
}
```

Apply the full CR manifest with these values (the scratchpad manifests from the 2026-09-05
deploys are the template; `kubectl apply -f <cr.json>` is the permitted form). What the operator
does: updates the Ingress host, updates the owned `CloudflareDNSRecord lake-prod-dns` to
`lake.live` in the new zone, and rolls the Deployment because `LAKE_PUBLIC_HOST` changed.

**Watch for a leaked record.** The `CloudflareDNSRecord` controller updates the record it owns;
when the zone Secret changes underneath it, it may create `lake.live` in the new zone without
deleting `lake.oramadev.net` in the old one. After the apply, `dig +short lake.oramadev.net`
should stop returning Cloudflare addresses once its TTL passes; if it does not, delete the record
in the `oramadev.net` dashboard by hand and note it on the operator issue.

**The existing apex record.** If a record for `lake.live` already exists in the zone, the
operator's create fails with a Cloudflare `81053`/`81057` duplicate error and the
`CloudflareDNSRecord` stays not-Ready. Delete or rename the existing record first (owner, in the
dashboard), or point it at `172.212.70.79` proxied so the operator adopts it — check the
controller's adoption behaviour (operator issue #82 notes name-only adoption for load balancers)
before relying on that.

## 5. Redirects

After the cutover, `lake.oramadev.net` should answer `301` to `https://lake.live/<same path>` for
a season so bookmarks, the seed repository's URLs and any pasted API examples keep working, then
disappear. The operator tears the record down when `spec.host` changes, so the redirect is a
Cloudflare-side object in the `oramadev.net` zone, created by hand:

1. A proxied `A lake.oramadev.net → 192.0.2.1` placeholder record (any address; Cloudflare never
   connects to it for a redirect).
2. A **Single Redirect** rule: when `http.host eq "lake.oramadev.net"`, `301` to
   `concat("https://lake.live", http.request.uri.path)` preserving the query string.

API clients get the `301`; `liquid` remotes must be re-pointed (see below) because a sync client
should not follow redirects on POST. Remove the placeholder and rule when the audit stream shows
no requests with the old host for a month (the request log carries `path` not host, so this is
read from Cloudflare analytics for the `oramadev.net` zone).

## 6. What breaks, and in what order to change it

| What | Bound to the host how | Break on move | Fix | Door |
|---|---|---|---|---|
| **Passkeys (WebAuthn)** | RP ID = `LAKE_PUBLIC_HOST`; every stored credential and its lake-signed `passkey_binding/1` attestation carry the RP ID; assertions verify the RP ID hash and origin | Every passkey registered under `lake.oramadev.net` **stops working** at `lake.live`; there is no migration — browsers scope credentials by RP ID | Users re-register a passkey after signing in another way. Today only seed accounts exist. | **One-way.** Once customers hold passkeys under an RP ID, changing it means every one of them re-enrols. Choose the RP ID now and never move it. |
| **OIDC issuer for auth-as-a-service** | Application JWTs carry `iss`; relying applications pin `issuer` and the JWKS URL `https://<host>/v1/apps/<id>/.well-known/jwks.json`; hosted pages `/apps/<id>/…` and custom-host selection by `Host` | Every relying application's verification config is wrong; tokens in flight fail `iss`; webhooks keep working (they are outbound) | Application owners update `issuer` and the JWKS URL; lake keeps retired keys so old tokens verify once the URL is fixed | **One-way.** After the first external application registers, changing the issuer is a coordinated migration with every one of them. Set it once. |
| OAuth social sign-in (GitHub, Google) | Callback `https://<LAKE_PUBLIC_HOST>/v1/oauth/<provider>/callback` registered at each provider | Sign-in with GitHub/Google fails with a redirect-URI mismatch | Add the new callback at each provider *before* the cutover, remove the old one after | Reversible |
| Browser sessions | `lake_session` cookie is set for the serving host | Everyone is signed out at the new host | Sign in again; bearer API tokens are not host-bound | Reversible |
| API tokens and MCP clients | Not host-bound; the client's configured URL is | Clients pointed at the old host get `301` (GET) or fail (POST) | Re-point clients and `liquid` remotes; the redirect covers browsers and GETs | Reversible |
| `liquid` remotes | Repository sync URL `https://<host>/v1/repositories/<id>/sync/*` | POST bodies are not replayed through a redirect | `liquid remote set-url` (or the client's equivalent) to `lake.live` | Reversible |
| Enterprise SSO (SAML/OIDC) and SCIM | ACS URLs, entity IDs, redirect URIs and the `/scim/v2` base are configured at the customer's IdP | Each configured IdP breaks until updated | Customer-side change per organization; none exist today | Reversible but per-customer |
| Application custom hosts | Route their own host to lake; selected by `Host` | Unaffected by lake's host change | — | — |
| Customer ACME and PKI | Directory URL `https://<host>/v1/acme_*`; SPIFFE trust domains are per customer, not the host | ACME clients need the new directory URL | Re-point clients | Reversible |
| `HSTS includeSubDomains` | Sent by lake on every response | Now applies to all of `*.lake.live` | Every subdomain must serve HTTPS — true for proxied records | — |
| Transparency log, audit stream | Keyed by instance name `prod` and lake's TAAP identity, not the host | Unaffected | — | — |

**Order of operations**

1. Owner: confirm the `lake.live` zone account, what the apex record serves today, and the host
   decision (§1). Record the decision in `decisions.md`.
2. Owner: create the scoped token and the `cloudflare-lake-live` Secret (§2). Set the zone's
   SSL mode to Flexible for now (§3).
3. Owner: register the new OAuth callback URLs at GitHub and Google alongside the old ones.
4. Clear or repoint the existing apex record (§4).
5. Apply the `Lake` CR with the three fields changed (§4). Watch
   `kubectl get lake prod -w` (Ready, DNS record Ready) and `kubectl rollout status deploy/lake-prod -n lake`.
6. Verify (below). Re-register the seed account's passkey if one exists.
7. Create the redirect in the `oramadev.net` zone (§5). Confirm the old record was torn down or
   remove it by hand.
8. Update every URL in docs that names `lake.oramadev.net`: lake `docs/deployment/aks.md` and
   `docs/api/*.md` examples, operator `docs/lake/README.md`, this repository's
   `action-plan.md`, `repositories.md`, [`slos.md`](slos.md), [`status-page.md`](status-page.md)
   and the runbooks — in the PR that records the move.
9. After the redirect has served a month with no traffic: delete the placeholder record and the
   rule, delete the `oramadev.net` token copy from `lake` (housekeeping item 6), remove the old
   OAuth callbacks at the providers.
10. Then the hardening in §3 (Origin CA certificate, operator #122, Full (strict)).

## How to verify

```sh
dig +short lake.live                          # Cloudflare proxy addresses
kubectl get cloudflarednsrecords -n lake      # lake-prod-dns  lake.live  172.212.70.79  true
curl -sS https://lake.live/v1/server_info     # ok:true, store postgres
curl -sS https://lake.live/v1/identity        # same taap_id as before the move
curl -sSI https://lake.live/ | grep -i strict-transport-security
curl -sS -o /dev/null -w '%{http_code} %{redirect_url}\n' https://lake.oramadev.net/repositories   # 301 https://lake.live/repositories
openssl s_client -connect lake.live:443 -servername lake.live </dev/null 2>/dev/null | openssl x509 -noout -subject -dates
kubectl logs -n lake deploy/lake-prod | head -1 | grep -o '"log_mode":"[^"]*"'        # air-gapped, unchanged
```

Then a full sign-in on the new host, a passkey registration, and a `liquid` push to the seed
repository against `https://lake.live`.

## How to change

This page is the plan; when the move happens, its *Where things stand* table becomes the record
of what changed and when, and issue #5 closes with a link here. A future host change is a new
page, because the one-way doors above mean it is a migration, not a rename.
