> **DRAFT — NOT LEGAL ADVICE.** Prepared for review by [ENTITY]'s counsel. Bracketed items are
> placeholders. Nothing here is published or binding until counsel approves it and the owner
> publishes it at `https://lake.live/terms`. Refs
> https://github.com/oramasearch/liquid-bridge/issues/15.

# lake.live Terms of Service (draft)

Effective date: [DATE]. Version: draft 1, 2026-09-05.

These Terms govern use of **lake.live** (the "Service"), operated by **[ENTITY LEGAL NAME]**
("[ENTITY]", "we"), a [ENTITY TYPE] organised under the laws of [JURISDICTION], with its
registered office at [ADDRESS]. Contact: [legal@lake.live].

## 1. Definitions

| Term | Meaning |
|---|---|
| **Service** | The hosted lake at `lake.live`: repository hosting and sync for `liquid`, the web interface, the `/v1` API, the OpenAPI document and the MCP endpoint, the drive, the artifact and model surfaces, the identity provider, secrets and certificate services, the transparency log, and related pages. |
| **liquid** | The client tool that talks to the Service. Separately licensed; not part of these Terms. |
| **Customer** | The tenant: either an individual with an Account or an organisation. A Customer has one handle in a single global namespace shared by individuals and organisations. |
| **Account** | A user identity on the Service, identified by a TAAP identity and, where provided, an email address. |
| **Authorised User** | A person or workload a Customer has granted access to its resources. |
| **Content** | Everything a Customer or its Authorised Users store or transmit through the Service: repositories and their history, files, models and datasets, issues, reviews, releases, secrets, certificates, application configuration, and metadata. |
| **Application** | Software a Customer registers to use the Service's identity features for the Application's own users ("End Users"). |
| **Transparency Log** | The public, append-only log of signed attestations the Service maintains. |
| **Documentation** | The Service's published documentation, including the service-objective and operations pages [LINK]. |

## 2. The Account

2.1 **Eligibility.** You must be at least [16/18] years old and able to form a binding contract.
If you accept for an organisation, you represent that you may bind it.

2.2 **Identity and credentials.** An Account is bound to a TAAP identity (an Ed25519 key pair).
**The private key stays with you**; the Service stores only your signed identity document and
its rotation history, and verifies signatures against it. You may authenticate with a password
and a second factor, a passkey, a supported OAuth provider, or your organisation's SSO. You are
responsible for keeping credentials and devices secure and for revoking sessions and devices you
no longer control; revocation takes effect on the next request.

2.3 **Recovery.** Recovery paths are: a one-use recovery code, an email token after a 24-hour
cooling period, or approval by two administrators of your organisation. **Account recovery never
restores end-to-end encrypted repository keys.** If you encrypt Content with keys held only on
your devices and do not designate a recovery contact in advance, that Content is unrecoverable
if the devices are lost. This is by design.

2.4 **Handles.** Handles are lowercase, unique across all Customers, and may be reclaimed if an
Account is deleted or if a handle infringes a third party's rights or these Terms.

## 3. The Service

3.1 We provide the Service as described in the Documentation and may change it over time. We
will not remove a documented export path without [90 days'] notice.

3.2 **API, OpenAPI and MCP** are part of the Service and subject to these Terms. Rate and quota
limits are stated in the Documentation and on your account pages.

3.3 **No lock-in.** You may export at any time: repositories as signed portable archives (with
a Git projection where applicable), audit records as JSON lines, and Application user records.
Self-hosting the same software is a supported configuration under a separate licence.

3.4 **Early service.** The Service is new. Features marked *preview* in the Documentation may
change or be withdrawn without the notice in 3.1. Section 9 states the service levels that apply.

## 4. Acceptable use

You will not, and will not permit anyone to: (a) use the Service to store or distribute unlawful
content, malware, or material that infringes another's rights; (b) probe, scan or test the
vulnerability of the Service other than through a coordinated disclosure to [security@lake.live];
(c) circumvent quotas, authentication or access controls; (d) use the Service to send unsolicited
communications; (e) resell the Service other than through Applications as permitted in Section 10;
(f) interfere with other Customers' use. We may remove Content or suspend access to comply with
law or protect the Service, and will tell you unless the law prevents it.

## 5. Content

5.1 **Ownership.** You keep every right you have in your Content. We claim none.

5.2 **Licence to us.** You grant us the non-exclusive, worldwide, royalty-free licence needed to
host, store, deduplicate, index for your own search, transmit, display to your Authorised Users,
back up and otherwise process your Content to provide the Service and to comply with law. For
Content in a **public** repository you also grant us the right to display and serve it to anyone,
and you grant other users the right to view and fetch it through the Service. Nothing here lets us
train models on your Content or use it for any purpose other than providing the Service.

5.3 **Encrypted Content.** Content you encrypt client-side with keys we do not hold is opaque to
us; we store, deduplicate and transmit the ciphertext and cannot read, search or recover it.

5.4 **Your responsibilities.** You are responsible for your Content, for having the rights to
store and share it, and for what your Authorised Users and Applications do with the Service.

5.5 **Secrets and certificates.** Values you store in the secrets service and private keys the
certificate service generates for you are encrypted at rest with keys wrapped by a key we hold.
We use them only to perform the operations you request through the API. Do not store secrets
outside the secrets service (for example in repository files); the Service's secret scanning is
an aid, not a guarantee.

## 6. Public repositories and the Transparency Log

6.1 Content in a public repository is visible to everyone, including people without an Account,
and may be cached by intermediaries. Making a repository private again does not recall copies
already made.

6.2 **The Transparency Log is public and permanent.** Attestations you or your Applications
publish to it (build provenance, delegations, key bindings and similar signed statements) become
part of an append-only Merkle tree that anyone may read, and are replicated to third-party
witnesses and, where configured, timestamp authorities. **They cannot be edited or removed,
including on Account deletion.** Do not publish personal data or confidential information in an
attestation. The log contains signed statements and hashes; it does not contain repository
Content.

## 7. Fees

7.1 **What is metered.** Usage is recorded per Customer and UTC hour as: **unique stored bytes**
(content-addressed duplicates are counted once, across every repository you own), **inbound
transfer bytes**, **outbound transfer bytes**, and **build compute seconds** (rounded up per
build result, excluding queue time). Prices are per GiB-hour of storage, per GiB transferred in
and out, and per compute second, in [CURRENCY], as published at [PRICING URL]. Your hourly usage
and its cost are visible to you at any time through the metering page and API.

7.2 **We bill what we store, not what you upload.** Because the Service deduplicates, your bill
for storage is the unique bytes we hold for you, which may be far less than the nominal size of
your repositories.

7.3 **Quotas never degrade your data.** If you exceed a storage quota, new writes are refused or
throttled (`HTTP 429`) and metadata writes may be throttled; **every existing object remains
readable and complete**. We never replace Content with pointer files, stubs or a reduced
representation.

7.4 **Invoicing and payment.** [Monthly in arrears / prepaid credit], by [METHOD], due [30] days
from invoice. Amounts exclude taxes, which you pay where applicable. Late amounts accrue interest
at [RATE] and may lead to suspension after [30] days' notice.

7.5 **Changes.** Price changes take effect at the start of the billing period following [30
days'] notice. Metering definitions in 7.1 change only with the same notice.

7.6 **Free tier / trial.** [Describe, or delete.]

## 8. Applications (identity as a service)

8.1 A Customer may register an Application and receive an isolated user pool: hosted sign-in
pages (on the Service's host or the Application's own host), sessions, short-lived signed tokens
with a public key set, user and organisation management, and lifecycle webhooks.

8.2 **You are the controller for your End Users.** You are responsible for your Application's
own terms and privacy notice, for lawful bases, for End User support and for honouring End User
rights; we act as your processor under the
[Data Processing Addendum](data-processing-addendum.draft.md). You will not register an
Application to collect credentials for a service you do not operate.

8.3 The token issuer, public key set URL and hosted page URLs are bound to the Service's host.
We will give [90 days'] notice before changing the host or issuer; see the Documentation's
operations pages for the migration path.

## 9. Service levels, support and maintenance

9.1 **Objectives.** We run the Service against published internal objectives (availability of
the API and the web interface, latency of push and pull, page response, audit-log freshness and
integrity, backup recency) and a public status page at [https://status.lake.live]. The objectives
and how they are measured are in the Documentation.

9.2 **Service credits.** [OPTION A: No service-level agreement or credits are offered in this
plan.] [OPTION B: table of monthly availability thresholds and credits, claim process, exclusions
for planned maintenance announced on the status page, Customer-caused incidents, force majeure and
upstream provider incidents.]

9.3 **Maintenance** is announced on the status page. We will try to give [48 hours'] notice for
maintenance expected to interrupt the Service.

9.4 **Support.** [Channel, hours, response targets by severity — or "best effort via
support@lake.live".]

## 10. Security, privacy and data

10.1 We protect the Service with the measures described in the Documentation and in Annex II of
the Data Processing Addendum, including encryption in transit and at rest, per-Customer key
wrapping, hashed passwords, a signed append-only audit log of authentication, authorisation and
administrative events, and role-based access control. We are designing the Service for a SOC 2
examination; [no report exists as of this draft / a report is available under NDA].

10.2 The [Privacy Policy](privacy-policy.draft.md) describes what personal data we process about
Account holders and visitors. Where you are a controller of personal data in your Content or in
your Application's user pool, the Data Processing Addendum applies.

10.3 **Audit records.** Every API call, sign-in and administrative action on your Customer is
recorded in a signed, append-only audit log retained for **at least 400 days**; you may increase
the retention for your Customer but not reduce it below that floor. You may read, filter and
export your audit records at any time.

## 11. Suspension and termination

11.1 **By you.** You may stop using the Service and delete your Customer at any time from the
account pages or the API.

11.2 **By us.** We may suspend or terminate for material breach uncured [30] days after notice,
immediately for a breach of Section 4 that threatens the Service or others, for non-payment under
7.4, or if we discontinue the Service with [90 days'] notice and an export period.

11.3 **What happens to your data.**

| Data | On deletion of a repository | On deletion of a Customer |
|---|---|---|
| Repository content | Tombstoned; recoverable by us for **30 days**; then eligible for collection from the store when no other repository references the objects | All repositories tombstoned as above |
| Account, organisation, grants, forge records, metering, secrets, certificates, Application records | — | Deleted with the Customer (cascade) |
| Audit records | Retained | **Retained for the remainder of the 400-day floor** (or your longer setting); they are the evidence trail for you and for us and cannot be shortened |
| Transparency Log attestations | Retained, public, permanent (Section 6.2) | Retained, public, permanent |
| Backups | Roll off with the backup retention period ([30 days]) | Same |

Export before you delete: exports are not possible after the tombstone is collected.

11.4 Sections 5.1, 6.2, 7 (for amounts due), 10.3, 11.3, 12, 13 and 14 survive termination.

## 12. Disclaimers

The Service is provided "as is" and "as available". To the extent permitted by law we disclaim
all warranties, express or implied, including merchantability, fitness for a particular purpose
and non-infringement. We do not warrant that the Service will be uninterrupted or error-free, that
builds will be reproducible, or that attestations, provenance or timestamps have any particular
legal effect. [JURISDICTION-SPECIFIC CONSUMER-LAW CARVE-OUTS.]

## 13. Limitation of liability and indemnity

13.1 To the extent permitted by law, neither party is liable for indirect, incidental, special,
consequential or punitive damages, or for lost profits, revenue, data or goodwill, however
caused. [ENTITY]'s total liability under these Terms is limited to [the fees you paid in the 12
months before the claim / AMOUNT]. These limits do not apply to [liability that cannot be
limited by law; breach of confidentiality; a party's indemnity obligations; wilful misconduct].

13.2 You will defend and indemnify [ENTITY] against third-party claims arising from your Content,
your Applications or your breach of Section 4. [Mutual IP indemnity from [ENTITY], if offered.]

## 14. General

14.1 **Changes to these Terms.** We may change these Terms with [30 days'] notice by email and on
the Service; continued use after the effective date is acceptance. Changes that reduce your rights
materially let you terminate before they take effect and receive a pro-rata refund of prepaid fees.

14.2 **Governing law and venue.** [JURISDICTION]; courts of [VENUE]; [arbitration clause, if any].

14.3 **Notices.** To us: [legal@lake.live] and [ADDRESS]. To you: the email on your Account.

14.4 **Assignment, severability, entire agreement, waiver, force majeure, export control,
government users.** [Standard clauses.]

14.5 **Order of precedence.** A signed order form or enterprise agreement prevails over these
Terms; these Terms prevail over the Documentation except where the Documentation is incorporated
by reference (Sections 3, 7.1, 9.1).

---

## Grounding for counsel (not part of the Terms)

Each factual statement above comes from the system as built. Counsel should treat these as the
facts to draft against and ask engineering when a fact must change to fit the law.

| Statement | Source |
|---|---|
| One handle namespace; individual or organisation as tenant; cascade on customer deletion | lake `docs/control-plane/schema.md`, `docs/api/customers.md` |
| Private key never held by the Service; identity documents and rotation stored | lake `docs/design/phase-6.md` §Identity |
| Password with MFA, passkeys, OAuth, SSO; revocation on next request | lake `docs/api/identity.md`, `docs/api/auth.md`, `docs/api/sso.md` |
| Recovery paths and the 24-hour cooling period; no recovery of E2E keys without a designated contact | lake `docs/api/recovery.md`, `docs/design/phase-6.md` |
| Export paths | lake `docs/api/export.md`, `docs/api/audit.md` (`export_audit`), `docs/api/apps.md` (`export_application_user`) |
| Public repositories readable anonymously | lake `docs/api/repositories.md` §Public repositories |
| Transparency Log public, append-only, witnessed, timestamped, never replaced | lake `docs/api/transparency.md`, `docs/control-plane/log.md` |
| Metering fields, hourly, unique bytes, compute rounding, integer prices; quota → 429; never pointer files | lake `docs/api/metering.md`; liquid `docs/features/18-lake-service.md` §What lake must not do |
| Applications: pools, hosted pages, EdDSA JWTs, JWKS, webhooks; issuer bound to host | lake `docs/api/apps.md`; bridge `docs/operations/lake-live-host.md` |
| Objectives and status page | bridge `docs/operations/slos.md`, `docs/operations/status-page.md` |
| Audit log: one signed row per capability outcome; 400-day floor; cannot be reduced; no pruning | lake `docs/api/audit.md`, `docs/control-plane/schema.md` §Audit |
| Repository delete = 30-day tombstone, then collection when unreferenced | lake `docs/api/repositories.md` §Lifecycle |
| Backup retention default 30 days | operator `docs/lake/backups.md` |
| SOC 2 as the design target; GDPR residency out of design scope | bridge `docs/decisions.md` §13 |
| Secrets and keys encrypted under per-customer KEKs wrapped by an instance key the Service holds | lake `docs/api/secrets.md`, `docs/api/encryption.md`, `docs/design/phase-6.md` §Secrets |

Open questions for counsel: (1) whether the permanence of Transparency Log entries and the
400-day audit floor need explicit consent language for personal data that may appear in them;
(2) the SLA option in 9.2; (3) whether `.live` as the notification sender domain affects the
notice clause (liquid `docs/features/18-lake-service.md` flags deliverability); (4) age threshold.

> **DRAFT — NOT LEGAL ADVICE.** For review by [ENTITY]'s counsel.
