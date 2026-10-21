# lake.live status page — the open decision and where it lives

**Status: proposed 2026-10-21. Nothing is built. Where it runs is Steve's decision.** Issue:
https://github.com/oramasearch/liquid-bridge/issues/14.

What the page shows (API, web app and sign-in per region, the order sheet, the edge; history;
objectives; incidents), its probes, the options and the incident templates are in **techops-docs**:
[`docs/lake/status-page.md`](https://github.com/oramasearch/techops-docs/blob/main/docs/lake/status-page.md)
(pull request https://github.com/oramasearch/techops-docs/pull/61).

## What Steve decides

1. **Where it runs.** Proposed: a static page on Cloudflare Pages at `status.lake.live`, probed once
   a minute by a Cloudflare Worker (no new vendor; outside Azure and outside lake), with one check of
   the edge from outside Cloudflare. The alternative is a hosted status vendor (a new sub-processor
   and a monthly bill, but probes and subscriber notifications without building them). lake serving
   its own `/status` is rejected: it fails with the service.
2. **The host**, `status.lake.live` proposed.
3. **Who may post incidents.**
4. **The paging channel** the prober posts to, which the runbooks name.

Building the proposed option then needs a Cloudflare token scoped to Pages and Workers (not a
widened zone token) and a private repository `oramasearch/lake-status`.
