# lake.live status page

**What.** Where the status of lake.live is read, what it shows, where it runs, how it learns the
truth, and the template used to communicate an incident. Refs
https://github.com/oramasearch/liquid-bridge/issues/14. Objectives it reports against:
[`slos.md`](slos.md).

**Why.** The status page is the one place a customer, and the on-call, look when something is
wrong. It must therefore live outside lake's own failure domain and be fed by a probe that sees
the service the way a customer does: through Cloudflare, from outside Azure.

## What it shows

| Section | Content | Source |
|---|---|---|
| Components | One row each: **API** (`/v1`), **Web UI**, **Push and pull**, **Sign-in** (identity pages and the OAuth callback), **Control database**, **Backups**, **Edge (Cloudflare, DNS, certificate)**. State: Operational, Degraded, Outage, Maintenance. | The prober's last result per component; Backups from the `Lake` status (see below). |
| History | 90 daily bars per component; a bar is the worst state seen that day. | Prober results in KV. |
| Incidents | Open incidents first, then resolved, each with its timeline of updates. | Markdown files in the status repository. |
| Maintenance | Scheduled windows (AKS node upgrades, image rolls that need a restart). | Same files, `kind: maintenance`. |
| Objectives | This month's attainment for each SLO in [`slos.md`](slos.md) with the budget remaining. | Computed from prober results; server-side SLIs are added when `/metrics` is scraped. |
| Subscribe | Atom feed of incident updates. | Generated at build. |

The page states plainly what it cannot see: server-side latency until `/metrics` is scraped, and
backup age until backups are enabled.

## Where it runs

**Decision proposed: a static page on Cloudflare Pages at `status.lake.live`, fed by a Cloudflare
Worker probe on a Cron Trigger.** Rejected alternatives and why:

| Option | Why not as the primary |
|---|---|
| lake renders `/status` from its own `/readyz` | Inside the failure domain: a dead pod, a broken ingress or a wrong DNS record makes the status page vanish with the service. Worth adding later as a *detail* page (lake issue) that the static page links to when the service is up. |
| A hosted status vendor | A new sub-processor and a monthly bill for a page a Worker can render; revisit if the incident volume justifies the tooling. |
| A page inside this bridge repository | Private repository, and a GitHub outage would take the page. |

**Shape.**

- Repository `oramasearch/lake-status` (private source, public site): `site/` (one HTML template,
  one stylesheet compiled from the same Orama design tokens lake uses, no framework),
  `incidents/*.md` (front matter: `id`, `title`, `kind: incident|maintenance`, `status`,
  `impact`, `components`, `started`, `resolved`, then dated updates as sections), `worker/`
  (the prober), `probes.json` (the table below).
- **Prober**: a Worker on a one-minute Cron Trigger runs every probe in `probes.json`, writes
  `{component, state, latency_ms, checked_at}` to Workers KV, and on a *state change* posts to
  the paging webhook named in [`runbooks/README.md`](runbooks/README.md). Three consecutive
  failures flip a component; one success flips it back. KV keeps 90 days of daily rollups.
- **Site**: Cloudflare Pages builds `site/` on push; a Pages Function reads KV for the live
  component states and the history bars, and the build embeds the incidents. Custom domain
  `status.lake.live` in the `lake.live` zone, proxied.
- **Backups component**: the prober cannot read the cluster. A tiny CronJob in the `lake`
  namespace (operator-rendered later) posts `Lake.status.lastBackupTime` and `backupReady` to the
  Worker's ingest endpoint with a shared secret; stale ingest (no post in 2 h) shows the
  component as *Unknown*, never *Operational*.
- **Cloudflare is a shared dependency**: the proxy in front of lake and Pages/Workers behind
  the status page are different products but one vendor. If Cloudflare is wholly down, the
  fallback channel is the `oramasearch/lake-status` repository README on GitHub and email to
  affected customers (template below).

**Probes** (`probes.json`), all `GET`, 10 s timeout, from the Worker's own edge location plus one
scheduled run through a second region:

| Component | URL | Expect |
|---|---|---|
| API | `https://lake.live/v1/server_info` | `200`, JSON `ok:true`, `value.store == "postgres"` |
| API | `https://lake.live/readyz` | `200`, `ok:true` |
| Web UI | `https://lake.live/` | `200`, body contains `<title>lake` (GET, not HEAD) |
| Web UI | `https://lake.live/repositories` | `200` or `303` |
| Sign-in | `https://lake.live/sign-in` | `200` |
| Sign-in | `https://lake.live/v1/identity` | `200`, `value.taap_id` starts `taap:1:` |
| Push and pull | `https://lake.live/v1/refs?repository_id=<public seed repository>` | `200` (anonymous read of a public repository); the full synthetic client is the [`slos.md`](slos.md) gap |
| Control database | derived: `readyz` `503` with `store_unavailable` flips this component, not API | — |
| Edge | TLS handshake succeeds; certificate `notAfter` ≥ 14 days; `server: cloudflare` header present | — |

Until the host moves ([`lake-live-host.md`](lake-live-host.md)) the URLs read `lake.oramadev.net`.

## Incident communication

Post the first update within the fast-burn alert's acknowledgement; update at the cadence stated
in the post, in UTC, with what is known and what is being done — never with a cause that has not
been confirmed. Resolved incidents get a review within the week.

### Incident post (one file, appended over time)

```markdown
---
id: 2026-09-05-style-css-stale
title: Pages rendered with an outdated stylesheet
kind: incident
status: resolved            # investigating | identified | monitoring | resolved
impact: degraded            # none | degraded | outage
components: [web-ui]
started: 2026-09-05T20:10Z
resolved: 2026-09-05T21:05Z
---

## Investigating — 2026-09-05T20:20Z
Pages on lake.oramadev.net render with the previous design after the 20260905a rollout.
The API is unaffected. Next update by 20:50Z.

## Identified — 2026-09-05T20:35Z
Cloudflare is serving `/style.css` from its cache (`max-age=86400`) while the HTML
references classes that exist only in the new stylesheet. Purging the file at the edge.

## Resolved — 2026-09-05T21:05Z
`/style.css` purged; pages verified from two locations. Permanent fix: content-hashed
asset URLs (lake #98). Review: <link>.
```

### Post-incident review (merged into the same file under `## Review`)

| Heading | Content |
|---|---|
| Summary | Two sentences: what customers saw, for how long. |
| Impact | Duration; requests failed or degraded (from counters or probe results); customers affected (from the audit stream, `GET /v1/audit?from=…&to=…`); SLO budget consumed. |
| Timeline | UTC, from the change or trigger through detection, mitigation and resolution. |
| Cause | The mechanism, not the person. |
| Detection | What noticed it, and what should have. |
| What went well / badly | Plain lists. |
| Actions | Each with an owner and an issue link; a runbook change is an action. |

### Customer email (fallback channel, and for incidents touching their data)

```
Subject: [lake.live] <component> incident, <date>

Between <start> and <end> UTC, <what happened, in one sentence>. <Who was affected and how>.
<What we did>. <What we are changing>. Your data <was / was not> affected: <specifics>.
Details and updates: https://status.lake.live/incidents/<id>. Questions: <contact>.
```

## How to verify

Open `https://status.lake.live` and compare every component with the manual probes in
[`slos.md`](slos.md) *How to verify*. Flip one probe's expectation in `probes.json` on a branch
deploy and confirm the component turns *Outage* after three runs and the paging webhook fires.
Post a test incident file and confirm the feed updates.

## How to change

Probe URLs and expectations live in `probes.json`; thresholds mirror [`slos.md`](slos.md) and
change with it. Adding a component means a probe, a row here, and a component key in the
templates. The host change in [`lake-live-host.md`](lake-live-host.md) is a one-line change per
probe.
