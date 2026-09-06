> **DRAFT — NOT LEGAL ADVICE.** Prepared for review by [ENTITY]'s counsel. Bracketed items are
> placeholders. Not published or binding until counsel approves it and the owner publishes it at
> `https://lake.live/privacy`. Refs https://github.com/oramasearch/liquid-bridge/issues/15.

# lake.live Privacy Policy (draft)

Effective date: [DATE]. Version: draft 1, 2026-09-05.

**Who we are.** [ENTITY LEGAL NAME] ("[ENTITY]", "we"), [ADDRESS], [JURISDICTION], operates
**lake.live** (the "Service"). Privacy contact: [privacy@lake.live]. [Data protection officer /
EU or UK representative, if required: NAME, ADDRESS.]

**Who this covers.** People who visit the Service, people who hold an Account, administrators and
members of organisations on the Service, and people whose personal data appears in Content that a
Customer stores. For **End Users of an Application** built on the Service's identity features,
the Application's operator is the controller and this policy applies to us only as their
processor; read the Application's own privacy notice.

## 1. What we collect

We collect only what the Service needs to work. The table says what, why, and how long.

| Category | Data | Why | Retention |
|---|---|---|---|
| **Account** | Email address (optional), display name, your public TAAP identity document and its rotation history (an Ed25519 public key and self-signed statements — never your private key) | To identify you, sign you in, attribute your actions | Until you delete your Account, then per §6 |
| **Credentials** | Password **hash** (Argon2id; we never store the password); TOTP seed and recovery codes (encrypted / hashed); passkey **public** key, credential id, device name and a lake-signed binding statement; the subject identifier and email returned by an OAuth provider you choose (GitHub, Google); SSO assertions mapped from your organisation's identity provider | Authentication | Until you remove the credential or delete the Account |
| **Sessions and devices** | Session identifiers (hashed), scopes, expiry, last use, revocation; named devices; the browser's `User-Agent` string recorded as the "device" of a sign-in | To keep you signed in and let you revoke access | Sessions until expiry or revocation; the sign-in record persists in the audit log (below) |
| **Organisation data** | Memberships, roles, teams, invitations (invitee email or handle), grants, and the administrator identity that made each | Authorisation | While the organisation exists |
| **Content** | Repositories and their full history, files, models and datasets, issues, reviews, releases, webhooks configuration, application configuration | To provide the Service | Until deleted: 30-day tombstone, then collection (§6) |
| **Encrypted Content** | Ciphertext you encrypt client-side | Storage and transfer only; **we cannot read it** | Same as Content |
| **Secrets and keys** | Values in the secrets service and private keys of certificates we issue, **encrypted** under a per-Customer key that is itself wrapped by a key we hold | Only to perform the operations you request | Until you destroy them or delete the Customer |
| **Audit log** | For every API call, sign-in and administrative action: time, acting identity, object, action, outcome, a request id, authentication method, device (User-Agent) where known, and details needed to interpret the event. **No secrets, credentials or private keys are ever recorded.** The log is signed and append-only. | Security, accountability, compliance evidence, your own visibility | **At least 400 days**; you may set longer for your Customer; entries are never edited or deleted before then |
| **Metering** | Per Customer and UTC hour: unique stored bytes, transfer in and out, build compute seconds; a per-build ledger | Billing and quotas | For the life of the Customer plus [accounting retention period] |
| **Recovery** | A **hash** of a one-use email recovery token, the timestamps of a recovery attempt, and the identities of approving administrators | Account recovery | Until the attempt completes or expires |
| **Provisioning (SCIM)** | User and group records your organisation's identity provider pushes to us, and an immutable log of each create, update and deactivation | Enterprise provisioning | While the organisation's SSO is configured; the provisioning log is retained |
| **Transparency Log** | Signed attestations that you or your tooling publish (provenance, key bindings, delegations), each carrying the signer's TAAP identity | Public verifiability | **Permanent and public** (§4) |
| **Request logs** | Method, path (without query string), route, status, duration, timestamp. **We do not log IP addresses, cookies or authorization headers at the application.** | Operations | [30] days |
| **Edge logs (Cloudflare)** | Cloudflare, as our network provider, sees your IP address, TLS details and request metadata and applies its own security processing | Delivery and protection of the Service | Per Cloudflare's retention |
| **Cookies and local storage** | `lake_session` (HttpOnly, SameSite=Lax, Secure): your session. `lake-theme` in the browser's localStorage: light or dark. No analytics or advertising cookies. | Sign-in; your display preference | Session: until expiry/revocation. Theme: until you clear it |
| **Support and correspondence** | What you send us | To answer you | [Period] |

We do not collect precise location, payment card numbers (payment is handled by [PAYMENT
PROVIDER], who is the controller of that data), or special categories of personal data, and the
Service is not designed for them. If your Content contains such data, you are its controller.

## 2. How we use it, and on what basis

| Purpose | Data | Basis [EU/UK GDPR, if applicable] |
|---|---|---|
| Providing the Service you asked for, including hosting, sync, search over your own Content, identity, secrets, certificates | Account, credentials, content, secrets | Performance of a contract (the Terms) |
| Billing | Metering, account | Contract; legal obligation |
| Security, fraud and abuse prevention, incident response | Audit log, sessions, request logs, edge logs | Legitimate interests (ours and other users') |
| Compliance evidence (access reviews, change management) | Audit log | Legitimate interests; legal obligation where applicable |
| Public verifiability of software provenance | Transparency Log | Legitimate interests; the publishing party's choice to publish |
| Communicating with you about the Service (incidents, changes to terms, security notices) | Email | Contract; legitimate interests |
| Product improvement | Aggregated usage counts only; **never** your Content and never model training | Legitimate interests |

We do not sell personal data, do not serve advertising, and do not use Content or personal data
to train machine-learning models.

## 3. Who we share it with

**Sub-processors and providers.** The parties below process data on our behalf. The full list,
with roles and locations, is Annex III of the
[Data Processing Addendum](data-processing-addendum.draft.md) and is kept current at [URL].

| Provider | Role | Data |
|---|---|---|
| Microsoft Azure (AKS, managed disks) | Hosting of the Service and its databases, **East US (Virginia)** | All data at rest and in processing |
| Cloudflare | DNS, TLS termination and reverse proxy, caching of static assets, object storage for database backups (R2), hosting of the status page | Traffic metadata including IP addresses; encrypted-at-rest backups |
| GitHub | Source hosting and image builds for the software (no Customer data); OAuth sign-in **when you choose it**; import of repositories **when you request it** | Your GitHub identity if you sign in with GitHub; the repositories you import |
| Google | OAuth sign-in **when you choose it** | Your Google identity |
| Docker Hub | Distribution of our container images (no Customer data) | None |
| [EMAIL PROVIDER] | Delivery of recovery and notification email | Email address, message content |
| [TIMESTAMP AUTHORITY], [LOG WITNESSES] | Independent timestamping and witnessing of Transparency Log checkpoints, **when configured** | Hashes of checkpoints only — no personal data |

**Other users.** Content in a public repository, and every Transparency Log entry, is visible to
anyone. Within an organisation, administrators can see members, grants and the organisation's
audit records.

**Legal.** We disclose data when required by law or a valid order, and we will tell you unless
prohibited. We may disclose data to protect the Service or someone's safety.

**Business transfer.** If [ENTITY] is acquired or merges, your data may transfer to the successor
under this policy; we will notify you.

## 4. The Transparency Log and other things we cannot delete

- **Transparency Log entries are public and permanent.** They are hashed into an append-only
  tree, replicated to independent witnesses and timestamp authorities, and cannot be altered or
  removed — by you or by us — without breaking the verifiability the log exists to provide. They
  contain signed statements and identities (public keys and TAAP identifiers), not repository
  Content. Do not publish personal data in an attestation.
- **Audit records** are retained for at least 400 days and cannot be deleted before then. They
  record what happened on your Customer, including sign-ins, with the acting identity and the
  device string. We regard this as necessary for security and accountability and as a legitimate
  interest that overrides erasure for that period. [COUNSEL: confirm the position under the
  applicable law; consider pseudonymisation of the identity column on Account deletion if
  required.]
- **Backups** of the control database are retained for [30] days and are not edited; deleted
  data disappears from backups as they roll off.

## 5. Where your data is

The Service runs in **Microsoft Azure, East US**. Backups are in Cloudflare R2 [bucket location /
jurisdiction hint]. Cloudflare's edge network processes requests at the location nearest to you.
Independent witnesses and timestamp authorities, when configured, are [list and locations].

[EU/UK: We transfer personal data to the United States. Transfers rely on [Standard Contractual
Clauses / the EU-US Data Privacy Framework (if the providers are certified)]. **Data residency
outside the United States is not offered.**]

## 6. Deletion and retention

| Action | Effect |
|---|---|
| Delete a repository | It is tombstoned for **30 days** (recoverable by us), then its unreferenced objects are collected from storage. Audit records of the repository remain. |
| Delete your Customer | Your Account, credentials, sessions, devices, organisation records, grants, forge data, metering, secrets, certificates and Application records are deleted (database cascade); repositories are tombstoned as above. **Audit records remain for the remainder of the 400-day floor; Transparency Log entries remain permanently.** |
| Revoke a session or device | Immediate; the next request is refused. |
| Leave an organisation | Your membership and grants are removed; the organisation's audit records of your actions remain. |

Export first: repository archives, audit JSON lines and Application user records are available
from the account pages and the API (see the Terms, Section 3.3). After the tombstone is collected
we cannot recover the data.

## 7. Security

Encryption in transit (TLS at our edge; [TLS to the origin — counsel: confirm with engineering
before publication]); encryption at rest for secrets and keys under per-Customer keys, and for
all storage volumes under the cloud provider's encryption; passwords hashed with Argon2id; MFA and
passkeys; role-based access through one policy engine checked on every request; a signed,
append-only audit log; least-privilege operator credentials; backups. Details are in Annex II of
the Data Processing Addendum. No system is perfectly secure; if we learn of a breach affecting
your personal data we will notify you [without undue delay / within X hours of confirmation] with
what we know.

## 8. Your rights

Depending on where you live you may have rights to access, correct, delete, restrict or object to
processing of, and to receive a portable copy of, your personal data, and to complain to a
supervisory authority. Most of these you can exercise yourself: your account pages show your
data, let you export it, revoke sessions and devices, and delete your Account. For anything else
write to [privacy@lake.live]; we answer within [30 days] and may ask you to prove control of the
TAAP identity in question. Section 4 explains the limits that apply to audit records and the
Transparency Log.

**California** [CCPA/CPRA notice: categories, sources, purposes, "we do not sell or share for
cross-context behavioural advertising", rights, non-discrimination.] **Other jurisdictions:**
[as required.]

## 9. Children

The Service is not directed to children under [16/18] and we do not knowingly collect their data.
If you believe a child has an Account, contact us and we will delete it.

## 10. Changes

We will post changes here with a new effective date and, for material changes, notify Account
holders by email at least [30 days] before they take effect.

## 11. Contact

[privacy@lake.live] · [ADDRESS] · [DPO / representative]

---

## Grounding for counsel (not part of the policy)

| Statement | Source |
|---|---|
| Data model: users, organisations, customers, credentials, sessions, devices, grants | lake `docs/control-plane/schema.md`, `docs/api/identity.md`, `docs/api/customers.md` |
| Argon2id; TOTP seeds encrypted; passkey public data and lake-signed binding; OAuth providers; five-minute one-use challenges | lake `docs/design/phase-6.md` §Identity-core security decisions |
| Audit event fields; no secrets in details; 400-day floor; no pruning; append-only triggers | lake `docs/api/audit.md`, `docs/control-plane/schema.md` §Audit |
| Request log fields; no authorization or cookie values logged; `admin_token_set` only as yes/no | lake `docs/serving/telemetry.md` |
| Cookies `lake_session` (HttpOnly, SameSite=Lax, Secure) and `lake-theme` localStorage | lake `docs/api/auth.md`; the served page's inline theme script (observed 2026-09-05) |
| Metering fields and hourly rows | lake `docs/api/metering.md` |
| Recovery token hash; approvals; outbox clears plaintext | lake `docs/api/recovery.md`, `docs/control-plane/schema.md` §Offline authorization and recovery |
| SCIM mapping and provisioning log | lake `docs/api/sso.md`, schema §SSO and federation |
| Transparency Log permanence, witnesses, timestamps | lake `docs/api/transparency.md`, `docs/control-plane/log.md` |
| Repository tombstone 30 days | lake `docs/api/repositories.md` |
| Hosting in Azure East US; Cloudflare proxy, R2 backups | bridge `docs/operations/aks-housekeeping.md`; operator `docs/lake/backups.md`; bridge `docs/decisions.md` §8 |
| GitHub/Google OAuth; GitHub import | lake `docs/api/identity.md`, `docs/api/github-import.md` |
| No model training, no analytics cookies | design choice; the served pages carry no third-party script (observed 2026-09-05) |
| Origin TLS not yet in place | bridge `docs/operations/lake-live-host.md` §3; operator #122 |

Open questions for counsel: (1) erasure versus the audit floor and the public log (§4);
(2) whether to geo-restrict sign-ups until GDPR terms exist, given decision 13 (bridge
`docs/decisions.md`) puts residency out of design scope; (3) the breach-notification window;
(4) whether Cloudflare's edge logging needs a specific disclosure beyond §1; (5) an engineering
check that Customer deletion is not blocked by the audit table's delete trigger (the audit table
references customers optionally; confirm the constraint behaviour).

> **DRAFT — NOT LEGAL ADVICE.** For review by [ENTITY]'s counsel.
