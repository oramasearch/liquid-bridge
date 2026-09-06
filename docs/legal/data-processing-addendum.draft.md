> **DRAFT — NOT LEGAL ADVICE.** Prepared for review by [ENTITY]'s counsel. Bracketed items are
> placeholders. Not published or binding until counsel approves it and the owner publishes it at
> `https://lake.live/dpa`. Refs https://github.com/oramasearch/liquid-bridge/issues/15.

# lake.live Data Processing Addendum (draft)

Version: draft 1, 2026-09-05. This Addendum forms part of the
[Terms of Service](terms-of-service.draft.md) (the "Agreement") between **[ENTITY LEGAL NAME]**
("Processor", "we") and the Customer ("Controller", "you") and applies whenever we process
Personal Data on your behalf in providing the Service.

## 1. Roles

1.1 For Personal Data contained in your Content, in your organisation's membership and grants,
and in the user pools of Applications you register, **you are the Controller and we are the
Processor.**

1.2 For Personal Data we process to operate the Service itself — Account data of your users as
Account holders, security and audit records, metering, request and edge logs — **we are an
independent Controller**, as described in the [Privacy Policy](privacy-policy.draft.md). The
audit log is one record serving both purposes; Section 8.3 explains the consequence.

1.3 If you act as a processor for your own customers, you warrant that your instructions to us
are authorised by the relevant controller.

## 2. Definitions

"Personal Data", "processing", "controller", "processor", "data subject", "supervisory
authority" and "personal data breach" have the meanings in the applicable Data Protection Law
([EU/UK GDPR, CCPA/CPRA, other]). "Sub-processor" means a third party we engage to process
Personal Data under this Addendum. "Instructions" means the Agreement, this Addendum, your
configuration of the Service and the API calls you make.

## 3. Processing on instructions

3.1 We process Personal Data only on your documented Instructions, unless required by law, in
which case we tell you before processing unless the law prohibits it. **Every API call and page
action you or your Authorised Users make is an Instruction and is recorded in the audit log.**

3.2 We will inform you if we believe an Instruction infringes Data Protection Law.

3.3 We do not access your Content except as needed to perform an Instruction, to prevent or
resolve a technical problem, or as required by law; operator access is through a break-glass
credential whose every use is recorded in the audit log.

## 4. Confidentiality

Personnel authorised to process Personal Data are bound by confidentiality obligations and have
access only to what their role requires. [Named roles with production access; how access is
granted and reviewed.]

## 5. Security

We implement the technical and organisational measures in **Annex II** and will not reduce their
overall level during the term. We may change the measures as technology and threats evolve.

## 6. Sub-processors

6.1 You authorise the Sub-processors in **Annex III**. We will give [30 days'] notice of a new or
replaced Sub-processor by [email / the page at URL]; you may object on reasonable data-protection
grounds within that period, and if we cannot resolve the objection you may terminate the affected
part of the Service with a pro-rata refund.

6.2 We impose data-protection obligations on each Sub-processor no less protective than this
Addendum and remain liable for their performance.

## 7. Data subject rights and assistance

7.1 Most requests can be fulfilled by you directly: the Service lets you read, export, correct
(display name, email), and delete Account and organisation records, revoke sessions and devices,
and export repositories, audit records and Application user records.

7.2 If a data subject contacts us about your processing, we will redirect them to you without
undue delay and will not respond except on your Instructions or as required by law.

7.3 We will assist you, taking into account the nature of the processing, with data protection
impact assessments and prior consultations, and with your obligations regarding security,
breach notification and data subject rights. [Fees for assistance beyond the Service's built-in
functions.]

## 8. Deletion and return

8.1 **During the term** you may delete or export Personal Data at any time through the Service.

8.2 **At the end of the term** (deletion of your Customer or termination of the Agreement) we
delete Personal Data we process as Processor as follows: Account, credential, session, device,
organisation, grant, forge, metering, secrets, certificate and Application records are deleted
with the Customer (database cascade); repository Content is tombstoned for **30 days** and then
collected from storage when no other repository references its objects; backups of the control
database roll off after **[30] days**.

8.3 **Records we retain after the term.** (a) **Audit records** are kept for the remainder of the
**400-day** floor (or the longer period you configured) because they are the evidence of what
was done on your Customer, by whom, including our own operator actions, and because they are
part of a signed chain that cannot be edited; we process them after the term as an independent
Controller for security and accountability. (b) **Transparency Log entries** published by you or
your tooling are public, append-only and permanent by design; they contain signed statements and
public identities, not Content. [COUNSEL: confirm the treatment of (a) and (b) under Art. 28(3)(g)
GDPR and equivalents; consider pseudonymisation of principal identifiers in (a) after the term
if required.]

## 9. Personal data breach

We will notify you **without undue delay [and within X hours] after becoming aware** of a personal
data breach affecting your Personal Data, with the information Data Protection Law requires as it
becomes available, and will cooperate in your response. Our status page and the incident process
in our operations documentation govern public communication of service incidents; a breach
notice under this Section is sent to your Account administrators' email addresses.

## 10. Audits and evidence

10.1 We will make available the information necessary to demonstrate compliance with this
Addendum: this Addendum, Annexes II and III, our security documentation, [a SOC 2 report when
one exists — none exists as of this draft], and, on request, an export of the audit records
relating to your Customer, which you may verify cryptographically (`verify_audit`).

10.2 Where the above is insufficient to meet a legal requirement, you may conduct, at your cost
and no more than [once a year] on [30 days'] notice, an audit by an independent auditor bound by
confidentiality, limited to the processing under this Addendum and coordinated so as not to
disrupt the Service or other customers.

## 11. International transfers

The Service is hosted in **Microsoft Azure, East US (United States)** with backups in Cloudflare
R2 and edge processing on Cloudflare's global network. [EU/UK: Where you transfer Personal Data
to us from the EEA, UK or Switzerland, the [EU Standard Contractual Clauses (Module 2 /
Module 3) / UK Addendum / Swiss amendments] in **Annex IV** apply and are incorporated; we will
implement the supplementary measures in Annex II.] Data residency outside the United States is
not offered.

## 12. Liability and precedence

Each party's liability under this Addendum is subject to the limitations in the Agreement. In a
conflict, this Addendum prevails over the Agreement for data-protection matters; the Standard
Contractual Clauses, where applicable, prevail over both.

## 13. Term

This Addendum applies for as long as we process Personal Data on your behalf, and Section 8
survives.

---

## Annex I — Details of processing

| | |
|---|---|
| **Subject matter** | Hosting, storage, synchronisation, search, review, distribution and deployment of the Controller's repositories and files; identity and access management for the Controller's users, organisations and Applications; secrets and certificate management; metering |
| **Duration** | The term of the Agreement plus the retention in Section 8 |
| **Nature** | Storage (content-addressed and deduplicated), transmission, structuring, indexing for the Controller's own search, encryption and key wrapping, authentication and authorisation decisions, logging, backup, deletion |
| **Purpose** | Providing the Service on the Controller's Instructions |
| **Categories of data subjects** | The Controller's employees, contractors and collaborators who hold Accounts or are members of its organisations; End Users of the Controller's Applications; any individuals whose personal data the Controller includes in Content |
| **Categories of Personal Data** | Identifiers (email, display name, TAAP public identity, handles); authentication data (password hashes, encrypted TOTP seeds, passkey public keys and device names, OAuth or SSO identifiers); organisational data (roles, teams, grants, invitations); usage and security data (sessions, devices, User-Agent strings, audit events, metering); Content of the Controller's choosing (repositories, files, models, issues, reviews); Application End User profiles and status |
| **Special categories** | None intended. The Service is not designed for them; the Controller is responsible for any it stores in Content |
| **Frequency** | Continuous |
| **Retention** | Section 8 |

## Annex II — Technical and organisational measures

Grounded in the system as built (sources listed at the end); counsel should treat each line as a
fact to be kept true.

| Area | Measure |
|---|---|
| **Encryption in transit** | TLS at the Cloudflare edge for all traffic; [TLS from the edge to the origin — in progress, operator #122; **state truthfully at publication**]; TLS between the Service and its database (CloudNativePG-managed certificates) |
| **Encryption at rest** | Storage volumes encrypted by the cloud provider. Secrets, encryption keys, certificate private keys, TOTP seeds, OAuth client secrets, application signing seeds and webhook secrets encrypted with AES-256-GCM under purpose-specific data keys, wrapped by a per-Customer key-encryption key, itself wrapped by an instance key held outside the database. Customer keys can be rotated; rotation rewraps in one transaction |
| **Passwords** | Argon2id (OpenSSL `EVP_KDF`; 64 MiB, 3 iterations, 1 lane); never stored in clear or logged |
| **Authentication** | Password with TOTP MFA and one-use recovery codes; WebAuthn passkeys with origin and RP-ID verification; OAuth with PKCE; enterprise SAML/OIDC SSO with issuer-claim allow-lists; SCIM provisioning with session revocation on deactivation; five-minute, one-use challenges |
| **Authorisation** | One policy engine (`authorize(principal, object, action)`) evaluated before every capability on REST and MCP alike, over one object graph with inherited grants; list and search results filtered per candidate so no object is shown that the caller could not open |
| **Sessions** | Random secrets, hashed at rest; scoped API tokens; device management; revocation effective on the next request; HttpOnly, SameSite, Secure cookies |
| **Audit** | One signed (Ed25519), hash-chained, append-only event per capability outcome, sign-in and administrative action, including denials and failures; database triggers reject update and delete; independent verification (`verify_audit`); minimum retention 400 days, not reducible; export as JSON lines |
| **Operator access** | A break-glass bearer minted by the operator into a Kubernetes Secret; its use is recorded in the audit log; Kubernetes RBAC on the cluster; [named roles; access review cadence] |
| **Secrets handling in operations** | No credentials in logs (`admin_token_set: yes/no` only), in CR fields, in container arguments or in git; secrets delivered as Kubernetes Secrets |
| **Isolation** | One tenant per Customer in the control plane (cascade constraints); one content store per Customer on disk; Application user pools isolated by pool identifier; [future: microVMs per tenant for customer workloads, bridge decision 31] |
| **Integrity of software** | Immutable image tags; images built from source under version control; provenance attestations for builds; a public transparency log for attestations; the deployment reconciled by an operator from a declared resource |
| **Availability and backup** | Stated objectives and error budgets (bridge `docs/operations/slos.md`); scheduled control-database backups to object storage with [30]-day retention and a documented restore (operator `docs/lake/backups.md`); disk snapshots of the content store [to be enabled]; restore rehearsals [each quarter] |
| **Logging** | Application logs carry method, path, status and duration — no IP addresses, cookies or authorization headers |
| **Vulnerability and change management** | Every change reviewed through pull requests; documentation updated in the same change; dependency pins; [disclosure address security@lake.live; patch targets] |
| **Data minimisation** | Email optional; the private key never leaves the user; the "device" is a name and a User-Agent string; no analytics or advertising tracking |
| **Deletion** | Cascade on Customer deletion; 30-day tombstone for repositories then collection; irreversible destroy for secret versions (ciphertext cleared, history row kept) |

## Annex III — Sub-processors

| Sub-processor | Service | Location | Personal Data processed |
|---|---|---|---|
| Microsoft Corporation (Azure: AKS, managed disks, load balancer) | Hosting of the Service, database and content store | United States, East US | All categories, at rest and in processing |
| Cloudflare, Inc. | DNS; TLS termination and reverse proxy; caching of static assets; R2 object storage for encrypted database backups; hosting of the status page | Global edge; R2 bucket [location] | Request metadata including IP addresses; backups containing all control-plane categories |
| GitHub, Inc. (Microsoft) | Source hosting and CI for the software; OAuth sign-in **when the data subject chooses it**; repository import **when the Controller requests it** | United States | OAuth identity of users who choose GitHub sign-in; imported repositories and their metadata |
| Google LLC | OAuth sign-in **when the data subject chooses it** | United States | OAuth identity of users who choose Google sign-in |
| Docker, Inc. (Docker Hub) | Distribution of the Service's container images | United States | None — infrastructure only; listed for transparency |
| [EMAIL PROVIDER] | Delivery of recovery and notification email | [Location] | Email addresses; message content |
| [TIMESTAMP AUTHORITY] | RFC 3161 timestamps over transparency checkpoints, when configured | [Location] | Hashes only |
| [LOG WITNESSES] | Cosignatures over transparency checkpoints, when configured | [Locations] | Hashes only |

Changes to this list are announced per Section 6.1 and kept current at [URL].

## Annex IV — Standard Contractual Clauses

[Attach or incorporate by reference the applicable module(s), the UK International Data Transfer
Addendum and Swiss amendments, with Annexes I–II above as their appendices. Delete if no
EEA/UK/Swiss transfers are in scope.]

---

## Grounding for counsel (not part of the Addendum)

| Statement | Source |
|---|---|
| Every capability call recorded; policy engine before every handler; REST and MCP identical | lake `docs/api/README.md`, `docs/api/policy.md`, `docs/design/phase-6.md` |
| Encryption model (data keys, customer KEK, instance KEK); rotation | lake `docs/api/secrets.md`, `docs/api/encryption.md`, `docs/control-plane/schema.md` §Static secrets |
| Argon2id parameters; WebAuthn; PKCE; challenge lifetimes | lake `docs/design/phase-6.md` §Identity-core security decisions |
| SSO, SCIM, session revocation on deactivation, provisioning log | lake `docs/api/sso.md` |
| Audit chain, triggers, 400-day floor, export, verify | lake `docs/api/audit.md` |
| Break-glass bearer | lake `docs/api/auth.md`; operator `docs/lake/README.md` |
| No secrets in logs | lake `docs/serving/telemetry.md` |
| One store per customer; cascade | lake `docs/deployment/store-volume.md`, `docs/control-plane/schema.md` |
| Backups to R2, 30-day retention, restore procedure | operator `docs/lake/backups.md`; bridge `docs/operations/runbooks/disaster-recovery.md` |
| Hosting location | bridge `docs/operations/aks-housekeeping.md` (node `eastus`) |
| Origin TLS status | bridge `docs/operations/lake-live-host.md` §3; operator #122 |
| Tombstone and destroy semantics | lake `docs/api/repositories.md`, `docs/api/secrets.md` |
| SOC 2 as design target; no report yet | bridge `docs/decisions.md` §13 |

Open questions for counsel: (1) post-term retention of audit records and the public log under
Art. 28(3)(g) and equivalents (§8.3); (2) breach window (§9); (3) whether GitHub and Google as
optional OAuth providers belong in Annex III or in the Privacy Policy only; (4) SCC modules and
whether the Controller-to-Processor flow is the only one; (5) the facts in Annex II marked as in
progress must be true on the publication date — engineering confirms each.

> **DRAFT — NOT LEGAL ADVICE.** For review by [ENTITY]'s counsel.
