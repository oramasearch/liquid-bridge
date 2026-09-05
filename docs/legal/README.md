# lake.live legal documents

Drafts for the owner's lawyer, grounded in what lake actually does. **Every page is marked draft
and is not legal advice**; nothing here is published until counsel approves it and the owner
publishes it on `lake.live` and links it from sign-up (the *Done when* of
https://github.com/oramasearch/liquid-bridge/issues/15). Bracketed items — entity name,
jurisdiction, contacts, notice periods, SLA option, breach window — are for the owner and
counsel to fill.

| Document | What it is | Draft |
|---|---|---|
| [`terms-of-service.draft.md`](terms-of-service.draft.md) | Accounts and TAAP identities, the Service and its export paths, acceptable use, Content and the licence to host it, public repositories and the permanent public transparency log, metering on unique stored bytes with quotas that never degrade data, Applications (identity as a service), service levels, security and audit retention, termination and what happens to data, disclaimers, liability, general terms | 1 (2026-09-05) |
| [`privacy-policy.draft.md`](privacy-policy.draft.md) | What personal data the Service collects per category, why and for how long; sharing and sub-processors; what cannot be deleted (transparency log, the 400-day audit floor); location (Azure East US, Cloudflare); deletion and retention; security; rights | 1 (2026-09-05) |
| [`data-processing-addendum.draft.md`](data-processing-addendum.draft.md) | Roles, instructions, confidentiality, security, sub-processors with notice, data-subject assistance, deletion and return, breach notification, audits, transfers; Annex I processing details, Annex II technical and organisational measures as built, Annex III sub-processors (Microsoft Azure, Cloudflare, GitHub, Google, Docker Hub, email, timestamp authority, witnesses), Annex IV SCC placeholder | 1 (2026-09-05) |

## How these were grounded

Each draft ends with a *Grounding for counsel* table mapping every factual statement to the
lake, operator or bridge page it comes from, and a short list of open questions for counsel. The
facts that shape the documents:

- **Data per customer and where it lives**: the Postgres control plane (users, credentials,
  organisations, grants, repositories, forge records, audit, metering, secrets and keys as
  ciphertext, applications) and one liquid content store per customer on the store volume, both
  in Microsoft Azure East US; backups to Cloudflare R2; Cloudflare in front.
- **Retention and deletion**: repository deletion is a 30-day tombstone then collection; customer
  deletion cascades; the audit log has a **400-day floor** that cannot be reduced and is never
  pruned; the transparency log is public and permanent.
- **Metering**: unique stored bytes, transfer in and out, compute seconds, per UTC hour; quotas
  throttle writes (`429`) and never replace content with pointer files.
- **Compliance scope**: SOC 2 is the design target (bridge `decisions.md` §13); GDPR data
  residency is out of design scope, which the drafts flag rather than hide.
- **Sub-processors**: Microsoft Azure (hosting), Cloudflare (DNS, proxy, cache, R2, status page),
  GitHub (source and CI; OAuth and import when chosen), Google (OAuth when chosen), Docker Hub
  (images only), plus placeholders for the email provider, timestamp authority and log witnesses.

## How to change

A change to the system that touches any fact above — a new sub-processor, a retention period, a
new category of data, the hosting region, origin TLS — changes the draft in the same PR, with a
new draft number and date in the table. Publication is a separate, owner-driven step: counsel's
approved text replaces the draft banners, and the published URLs are recorded here.
