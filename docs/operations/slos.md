# lake.live service objectives — the decision and where they live

**Status: proposed 2026-10-21, awaiting Steve** (decision 66 in [`../decisions.md`](../decisions.md), https://github.com/oramasearch/liquid-bridge/issues/42). Issue:
https://github.com/oramasearch/liquid-bridge/issues/14.

The objectives, how each is measured, the error budgets and burn alerts, and the measurement gaps
are in **techops-docs**, which describes how production is run:
[`docs/lake/slos.md`](https://github.com/oramasearch/techops-docs/blob/main/docs/lake/slos.md)
(pull request https://github.com/oramasearch/techops-docs/pull/61). This page records only the
decision.

## The proposal

- **Per region.** `lake-prod` is two independent regions: `eu` (`eu.lake.live` and the apex
  `lake.live`, `orama-production-cluster-02`) and `us` (`us.lake.live`,
  `orama-production-cluster-03`), decision 64. Each objective is held per region; one region's
  outage does not spend the other's budget.
- **Two surfaces**: the API (`/v1`, `/mcp`) and the web app (the Lake Console, sign-in, the order
  sheet).
- **Objectives, rolling 30 days**: availability **99.5 %** for each surface (3 h 36 min of budget);
  API latency **95 % ≤ 0.25 s, 99 % ≤ 1 s** server-side; web app time to first byte **95 % ≤ 1.5 s**
  through Cloudflare.
- **Measured from** `lake_http_requests_total`, `lake_http_request_duration_seconds` and `/readyz`
  (lake `docs/serving/telemetry.md`), and an external probe through Cloudflare. Once both exist, the
  lower of the two decides.
- **Why 99.5 % and not 99.9 %**: each region is one lake pod rolled with `Recreate`, one Postgres
  instance and no control-plane backups, so every roll or restart is an outage of that region. It
  moves to 99.9 % with the surge rollout (decision 49, amended), two Postgres instances, backups on,
  and a month of probe data at that level.
- **Budget policy**: more than half a region's budget spent stops rolls to `lake-prod` except fixes;
  an exhausted budget needs an incident review and Steve's go-ahead. This adds to the pipeline's
  gates; it does not replace them.

**Not measurable yet**: nothing scrapes a production Lake's `/metrics`
(https://github.com/oramasearch/orama-operator/issues/15), and the external prober is the status
page's, which is not built ([`status-page.md`](status-page.md)).

The previous version of this page (2026-09-05) set objectives for the single `Lake/prod` on the
managing cluster, which is temporary and gets no new investment; it is in this file's git history.
