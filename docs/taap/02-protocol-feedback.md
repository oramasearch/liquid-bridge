# TAAP/1 protocol feedback beyond content-addressed subjects

**To:** the TAAP/1 protocol owner
**From:** the liquid project (first significant implementer of TAAP/1)
**Against:** TAAP/1 `1.0.0-draft.1`, dated 2026-08-05, as vendored at liquid
`docs/standards/taap-1-spec-draft.md`
**Companion:** [`01-content-addressed-subjects.md`](01-content-addressed-subjects.md), which
resolves Section 22.3 for objects and is referenced below as document 01
**Status:** draft, not yet sent (bridge issue
https://github.com/oramasearch/liquid-bridge/issues/8)

liquid has implemented signed identities, signed drips and changes, identity rotation with
compromise declarations, a registered attestation profile set, and scoped delegation to agents
against draft.1. Where the draft was silent or inconsistent, liquid had to choose, and each
choice is recorded in liquid's library documentation. This document sends those choices back
as feedback, together with liquid's answers to the open questions in Section 22 that its own
specification settles.

Each item has four parts: the problem in the draft, liquid's requirement with the scenario that
produces it, the proposed spec text, and what liquid does in the meantime. Section numbers
refer to draft.1; every *Current text* is verbatim from the vendored copy.

## Item 1. Section 22.5: delegation chains, attenuation-only, with depth limits

### The problem

Section 11 defines one shape of delegation: a Grant Authority issues an access grant to a
Client on behalf of a consenting Subject. Section 22.5 asks whether a Client may sub-delegate
and names the two rules any answer needs:

*Current text*

```
**22.5. Delegation chains.** Should a Client be able to sub-delegate to another Client
(A grants to B, B grants a subset to C)? This is powerful and a common source of confused
deputy bugs; it needs explicit depth limits and attenuation-only rules if included.
```

There is no text for a chain: no field that links a child artifact to its parent, no rule for
who may issue a child, no definition of "subset", no depth counter, no verification order for a
chain, and no statement of how revocation travels down it.

### liquid's requirement and scenario

Yes, chains are needed, and the normal case is not Client to Client. It is **human to agent to
subagent**. A developer dispatches a coding agent; the agent dispatches subagents for parts of
the task. Each hop must carry strictly less authority than the hop above it, and a Verifier
must be able to check that from the artifacts alone.

The scenario liquid implements today:

1. A developer (the principal) starts an agent session with authority over `src/**`, the right
   to publish to the shared repository, the right to take semantic leases on files and symbols,
   and permission to delegate one level further.
2. The agent dispatches a subagent for `src/parser/**` with no publish right and no further
   delegation.
3. The subagent edits files. Every edit it records (a drip) is signed by the subagent's own key
   and carries the digest of the delegation it acted under, so the edit is attributable to the
   subagent, to the agent that dispatched it, and to the developer at the root.
4. A drip outside `src/parser/**`, or an attempt by the subagent to publish, is rejected at the
   session boundary before any lease or base check runs.
5. If the developer revokes the root delegation, every session below it loses authority at the
   next status check, which liquid bounds to one hour for delegations.
6. A leaf must never be able to widen itself, and a party holding two chains must not be able to
   combine them into authority neither chain grants.

Delegation in liquid is an attestation (profile `delegation/1`): the principal is the Authority
and the agent is the Subject. A chain is therefore a chain of attestations in which each child's
Authority is the parent's Subject. The proposed text below covers both that shape and the
Client-to-Client shape Section 22.5 describes, with one set of rules.

### Proposed spec text

New Section 11.5.

```
### 11.5. Delegation Chains

A delegation chain is an ordered sequence of artifacts, root first, in which each artifact
after the root is issued by the party that received the one before it and confers no more than
it. Two artifact types may form chains: access grants (Section 11.4), where the receiving party
is the `client_identifier`, and attestations under a profile registered as a delegation
profile (Section 23.3), where the receiving party is the `subject_identifier`.

A chained artifact carries three additional fields:

    "parent_artifact_type": "attestation",
    "parent_artifact_identifier": "01J9ZB4KQ7Y8X2M5N0P3R6T9V1",
    "parent_artifact_digest_base64": "7f3a...",
    "delegation_depth_remaining": 0

- `parent_artifact_type` and `parent_artifact_identifier` name the parent. `parent_artifact_digest_base64`
  is the SHA-512/256 digest of the parent's complete canonical bytes, signatures included, so
  that the child binds to one exact parent (the same pattern as `consent_response_digest_base64`).
  A root carries none of the three parent fields.
- `delegation_depth_remaining` is a non-negative integer. A root sets it. A child's value MUST
  be strictly less than its parent's. An artifact whose value is 0 MUST NOT be a parent. An
  absent field means 0: sub-delegation is off unless the issuer turns it on.

Rules for a valid chain:

1. **Issuer continuity.** The issuer of each child (`grant_authority_identifier` for a grant,
   `authority_identifier` for an attestation) MUST equal the receiving party of its parent. The
   receiving party of every link MUST be a key-derived identifier (Section 5.1); a
   content-addressed subject (Section 5.6) cannot receive a delegation.
2. **Root authority.** The root of a grant chain MUST be issued by a Grant Authority the
   Verifier trusts after Subject consent (Section 11.3). The root of an attestation chain MUST be
   issued by an Authority the Verifier trusts for the delegation profile (Section 15.4).
3. **Attenuation only.** Each child MUST confer a subset of its parent. For grants:
   `approved_scopes` of the child is a subset of the parent's, `resource_holder_identifier` is
   equal, `subject_identifier` is equal, `expires_at` is not later than the parent's, and
   `maximum_token_lifetime_seconds` is not greater. For a delegation profile, the registration
   MUST define containment for every attribute that carries authority: a set attribute is
   contained when it is a subset, a boolean permission is contained when a parent `false` stays
   `false`, a numeric limit is contained when the child's value is not greater, and a path or
   scope pattern is contained when every value it matches is matched by the parent's. An
   attribute with no defined containment MUST be equal in child and parent.
4. **Depth.** Rule on `delegation_depth_remaining` above, and the chain length MUST NOT exceed
   the Verifier's configured `maximum_delegation_depth` (Section 15.4; default 2, which admits
   principal, delegate and one sub-delegate).
5. **Whole chain.** A Verifier MUST verify every link, root first: signature, validity window,
   revocation freshness per Section 14.5, and rules 1 to 4, and MUST reject the leaf if any
   link fails. A leaf MUST NOT be accepted without its chain unless the Verifier has previously
   verified and retained that chain.
6. **Effective authority.** The authority conferred by a chain is that of its leaf, which by
   rule 3 is contained in every ancestor. A party holding more than one chain MUST act under
   exactly one per request and a Verifier MUST NOT combine chains.
7. **Revocation.** `revoke_derived_artifacts` (Section 14.3) applied to any link revokes every
   descendant. The issuer of any link MAY revoke that link and, through the cascade, everything
   below it. The root issuer MAY revoke the whole chain.

**Reasoning (attestation chains as well as grant chains):** The agent case is a principal
conferring authority directly, with no Grant Authority in between. That is an attestation by
the principal about the agent. Making the chain rules apply to both shapes gives one set of
checks for "who authorised this, through whom, and with what limits."

**Reasoning (depth default 2):** The common topology is a person, an agent and a subagent.
Deeper chains are not forbidden, but a Verifier should have to choose them.

**Reasoning (absent means 0):** A field an issuer forgot to set must not become permission to
re-delegate.
```

Section 13.2, add after step 3:

```
3a. If the token's grant is a chained artifact (Section 11.5), verify the chain.
```

Section 14.3: after the list of cascade values, add:

```
For a chained artifact (Section 11.5), "derived" includes every descendant in the chain.
```

Section 15.4: add `"maximum_delegation_depth": 2` to the trust policy example.

Section 17: add `delegation_chain_invalid`, `delegation_depth_exceeded`,
`delegation_not_attenuated`.

Section 22.5: replace with "Resolved by Section 11.5: chains are permitted, attenuation-only,
with an explicit depth counter and a Verifier-configured maximum."

Section 25: add `parent_artifact_type`, `parent_artifact_identifier`,
`parent_artifact_digest_base64`, `delegation_depth_remaining`.

### What liquid does meanwhile

`delegation/1` is a registered attestation profile whose Authority is the principal and whose
Subject is the agent actor. Its required attributes are `scopes` (repository-relative path
globs), `may_publish` and `may_lease` (independent capabilities), `depth_remaining` and
`dispatcher`; `model` is optional. `validate_delegation(child, parent)` enforces attenuation:
every child scope must be contained by a parent scope, a denied capability cannot become
allowed, and remaining depth must strictly decrease. Session creation also verifies the
signature, current revocation evidence no older than one hour, and that the local principal
issued the delegation. Scope and capability checks run before lease and base validation.
Version-3 signed drips record the delegation digest and the agent actor; older drip versions
remain decodable. Drips are signed by the acting identity directly; the chain lives on the
session, not on each drip.

## Item 2. Section 22.2 and Section 6.7: identifier stability across rotation, and naming the key that signed

### The problem

Section 5.5 keeps the identifier stable across rotation and flags the choice:

*Current text*

```
**Note:** The identifier is derived from a key, so rotation raises the question of whether
the identifier changes. TAAP/1 keeps the **original** identifier stable and treats the
document chain as the authority on the current key set. This is flagged in
**[OPEN QUESTION 22.2]** because it trades self-certification for stability.
```

Two consequences of that choice are unstated. First, the signature object (Section 6.7) names
the signer with `signing_key_identifier`, which is the identity's identifier, not a key. After
a rotation the identity has had more than one key, and a Verifier reading a signature cannot
tell from the signature which key to check against. `signing_key_label` is free text and the
draft does not make labels unique. Second, Section 5.5 does not say whether a signature made by
a key that was later rotated out in an orderly way (not compromised) remains valid. Section
18.7 covers only compromised keys.

### liquid's requirement and scenario

Stability, without qualification. A drip signed in 2026 must remain attributable to the same
identity, and verifiable, after that identity rotates its key in 2029. liquid is a
version-control system; every stored record names its actor by identifier, and those records
are immutable and content-addressed. An identifier that changed on rotation would break every
stored reference and could not be fixed by rewriting, because rewriting would change every
digest above it.

A Verifier holding a 2026 drip and the 2029 identity chain must be able to find the 2026 key in
the chain, check that it was current when the drip says it was signed, and accept the signature.
It must also be able to do this offline, from the chain alone.

### Proposed spec text

Section 5.5, replace the Note with normative text:

```
The identifier is fixed by the first identity document and never changes. Rotation adds keys
to the document chain and retires others; the chain, not any one document, is the authority on
which keys were valid when.

A signature made by a key that a later document retires in an orderly rotation remains valid
for the period in which the key was current. A Verifier that holds the chain **MUST** accept
such a signature if the key was in the current key set at the time of signing, and **MUST NOT**
require the signature to be re-made with a current key. A key declared compromised is governed
by Section 18.7 instead.

The time of signing is established by the Verifier's time evidence: inclusion in a transparency
log, an RFC 3161 timestamp, or, absent both, the signature's `signed_at`, which is the signer's
own claim and is not covered by the signature (Section 6.6).
```

Section 6.7, add a field to the signature object and the field table:

```
  "signing_key_fingerprint_base32": "JBSWY3DPEHPK3PXPJBSWY3DPEHPK3PXPJBSWY3DPEHPK3PXPJBSW",
```

```
`signing_key_fingerprint_base32` is the fingerprint of the exact public key object used, computed
as in Section 5.1. It **MUST** be present when the signing identity's chain lists, or has ever
listed, more than one key, and **SHOULD** be present otherwise. A Verifier selects the key by
fingerprint from the chain and **MUST** reject a signature whose fingerprint names a key the
chain does not contain.

**Reasoning:** `signing_key_identifier` names an identity, which after rotation has several
keys. Trying each key is cheap but is guessing, which Section 6.8 forbids for algorithms and
which should not be the rule for keys either.
```

Section 22.2: replace with "Resolved: the identifier is stable. Section 5.5 states the
consequences for signatures made by retired keys, and Section 6.7 names the signing key by
fingerprint."

### What liquid does meanwhile

liquid's `actor` carries the stable `taap_id` and the identity fingerprint, and beside them the
current `public_key` and its `key_fingerprint`. A drip embeds the actor with its public key, so
verification of a stored drip needs no chain lookup; `verify(actor, ...)` resolves a
non-current key through the locally retained chain, and `verify_chain` returns the current key
set. Documents are retained as canonical CBOR under
`identity/<identity-fingerprint>/documents/NNN.cbor`. `signer::rotate` keeps the subject
identifier and identifier fingerprint of the first document and changes only `key_fingerprint`.

## Item 3. Section 22.10: the `taap:` identifier scheme

### The problem

*Current text*

```
**22.10. Naming.** "TAAP" is a placeholder.
```

The section goes on to ask that the `taap:1:...` identifier scheme be confirmed, and notes that
reusing `did:` would gain ecosystem tooling but would inherit DID method governance.

The identifier text is persisted. If the scheme changes after implementations have stored
identifiers, every stored record either needs rewriting or every parser needs to accept both
forms forever.

### liquid's requirement and scenario

liquid stores the identifier text in every drip, every change, every attestation and every
identity document, and those records are immutable. It also derives the CRDT actor identifier
for collaborative editing from the TAAP identifier text and the device identifier by a fixed
BLAKE3 derivation, so a change to the text would change every actor identifier in every
collaborative document. liquid needs the identifier grammar frozen before its repositories
carry data that will outlive the draft, whatever the protocol ends up being called.

On `did:`: liquid works offline and air-gapped, and relies on Section 15.1's rule that direct
presentation is always sufficient. A DID method reintroduces exactly the resolution and
governance layer the draft's own reasoning in Section 15.1 avoids, and Section 22.10 already
says the governance cost is real. liquid's answer is no.

### Proposed spec text

Section 5.1, add after the identifier grammar:

```
The identifier grammar is versioned by its second segment and is independent of this
protocol's name. Identifiers minted under TAAP/1 keep the `taap:1:` prefix regardless of any
later renaming of the protocol. If a later version changes the grammar, it **MUST** define an
exact, byte-preserving, one-to-one mapping from `taap:1:` identifiers, so that a stored
identifier remains resolvable without re-signing anything.
```

Section 22.10: replace the second sentence with "Resolved: the `taap:1:` scheme is confirmed
and is stable regardless of the protocol's eventual name; `did:` is not adopted."

### What liquid does meanwhile

liquid stores identifiers as text with the `taap:1:` prefix. Its parser rejects an unrecognised
prefix. A rename that is not byte-preserving would be a re-encoding step for every liquid
repository and would change CRDT actor identity, which is why this item is worth settling
before the draft stabilises.

## Item 4. Section 5.4: how an identity document is signed and encoded

### The problem

*Current text*

```
Identity documents are **self-signed** by a key they contain (Section 7).
```

Section 7 is the message envelope. An identity document is an artifact, not a message: it is
stored, presented in-band under Section 15.1, and hashed by its successor. Three things a
second implementer must know are unstated: the domain separator type used in Section 6.6, where
the signatures live on the document, and which canonical encoding the stored bytes are in.
Section 2.3 also defines *Artifact* as an attestation, a grant or a token, so the identity
document is not formally an artifact at all.

### liquid's requirement and scenario

liquid had to ship signed drips with identities before any of this was settled. Two liquid
installations, or liquid and lake, must produce byte-identical identity documents for the same
inputs and verify each other's, and a successor document must hash exactly the bytes its
predecessor stored.

### Proposed spec text

Section 2.3, the *Artifact* entry: extend the list to "an identity document, an attestation,
an access grant, an access token, or a revocation list".

Section 5.4, replace the sentence above with:

```
An identity document is an artifact. It is signed under Section 6.6 with `artifact_type`
`identity_document` as the domain separator, and carries its signatures in a `signatures`
array of Section 6.7 objects whose `signature_purpose` is `identity_document`. It is
**self-signed**: every signature is by a key the document's `keys` array contains, except as
Section 5.5 permits for a retired key.

An artifact stored or presented outside an envelope carries an `encoding` field with the same
values and meaning as the envelope's (Section 7.1). It is **REQUIRED** on an identity document,
so that a Verifier never has to guess which canonical form the document's stored bytes, and
therefore its hash under Section 5.5, are in.
```

### What liquid does meanwhile

Identity documents are canonical CBOR with `artifact_type = "identity_document"`,
`encoding = "ccbor"`, and a `signatures` array of Section 6.7 objects. The signed bytes are
`ASCII("TAAP/1 identity_document") || 0x00 || canonical_cbor(body without signatures)`.
`encode_identity_document` emits the complete canonical record; `decode_identity_document`
rejects malformed or non-canonical input. Both the initial document and every rotation
successor use this one record type.

## Item 5. Section 5.5: the algorithm and input of `previous_document_hash_base64`

### The problem

*Current text*

```
1. references the previous document by hash,
```

Neither Section 5.4 nor Section 5.5 names the hash algorithm or says which bytes are hashed:
the previous document's signed body, or its complete stored bytes including signatures. The two
readings give different hashes, and a chain produced under one cannot be verified under the
other.

### liquid's requirement and scenario

Rotation is implemented (liquid #111). A verifier holding the stored bytes of document N must be
able to check document N+1's link with no other information. Including the signatures in the
hashed bytes means the link binds to the predecessor *as signed*, so a predecessor whose
signatures were stripped or replaced does not match.

### Proposed spec text

Replace item 1 of Section 5.5 with:

```
1. references the previous document in `previous_document_hash_base64`: the RFC 4648 base64
   encoding of the SHA-512/256 digest of the previous document's complete canonical bytes in
   its declared encoding, `signatures` included, exactly as stored,
```

Document 01 phrases the same rule through its `taap_artifact` content rule, so that the
previous-document hash and the document's content-addressed subject are one computation. Either
wording is acceptable to liquid; the bytes and the algorithm are what matter.

### What liquid does meanwhile

SHA-512/256 over the predecessor's stored canonical CBOR bytes, signatures included, base64
encoded. `verify_chain` checks the stored-byte links.

## Item 6. Sections 6.6 and 6.7: what the signature covers, and what `signature_purpose` and `signed_at` are

### The problem

Section 6.6 excludes the signature object from the signed bytes:

*Current text*

```
1. Construct `B` **without** any `signatures` field.
```

Section 6.7 then describes `signature_purpose` as signed:

*Current text*

```
**Reasoning (`signature_purpose`):** It states intent in the signed material itself, so a
signature made for authentication cannot be repurposed as a signature of consent. This is
the same motivation as the domain separator, applied at a finer granularity.
```

Under Section 6.6 as written, nothing in the signature object is signed: not
`signature_purpose`, not `signing_key_identifier`, not `signed_at`. Two consequences follow.
First, `signature_purpose` cannot itself prevent repurposing; the domain separator does that,
and the field is a label unless a Verifier is told to check it against the separator. Second,
`signed_at` is an unverified claim, yet Section 18.7 turns on "the declared compromise time"
versus the time a signature was made. An attacker holding a compromised key can write any
`signed_at` it likes.

### liquid's requirement and scenario

One unambiguous rule so that liquid and any other implementation compute the same signing
input, and a defined check for `signature_purpose` so that a signature stored with a drip cannot
be moved to a change or an identity document. liquid also needs the draft to be honest about
`signed_at`, because its rotation code must decide whether a signature by a compromised key
was made before or after the declaration, and the only trustworthy time it has is external
(transparency-log inclusion or an RFC 3161 token; liquid implements verification of both).

### Proposed spec text

Option A, which is liquid's reading and what liquid has shipped. Add to Section 6.7:

```
The fields of the signature object are not covered by the signature (Section 6.6, step 1).
`signature_purpose` **MUST** equal the `artifact_type` or `message_type` used as the domain
separator in Section 6.6, and a Verifier **MUST** fail the signature if it does not. The field
is a readable statement of the separator that was used, so that a stored signature can be
checked against the object it accompanies without recomputing anything else first.

`signed_at` is the signer's claim of when it signed and is not verified by the signature. A
Verifier **MUST NOT** rely on `signed_at` alone where the time of signing has security
consequences (Section 18.7); it **SHOULD** use external time evidence such as transparency-log
inclusion or an RFC 3161 timestamp over the signature, and **MAY** fall back to `signed_at`
only under an explicit policy.
```

and replace the reasoning paragraph's first sentence with: "It states the domain separator in
readable form beside the signature, and the Verifier's equality check is what prevents a
signature made for authentication from being presented as a signature of consent."

Option B, if the owner would rather protect the signature metadata: change Section 6.6 step 3
to

```
signing_input = domain_separator || 0x00
             || canonical_bytes(signature object without signature_bytes_base64) || 0x00
             || canonical_bytes(B)
```

This signs `signature_purpose`, `signing_key_identifier` and `signed_at`, at the cost of
changing every signature ever made under draft.1. `signed_at` would then be a signed claim, but
still the signer's claim, so the Section 18.7 caveat stands either way. liquid can implement
either option; it asks for A unless the owner has a reason for B, and asks that whichever is
chosen be written into Section 6.6 rather than left to the reasoning paragraph.

### What liquid does meanwhile

Option A. The signed bytes are the body without `signatures`, domain-separated by the artifact
type; the signature object's own fields are not signed; `signature_purpose` must equal the
artifact type or verification fails. The artifact types liquid uses are `drip`, `change`,
`identity_document`, `attestation` and `result`.

## Item 7. Sections 5.5, 18.7, 14.1 and 23.5: declaring a key compromised

### The problem

Section 5.5 permits a successor without the old key's signature when the old key is declared
compromised:

*Current text*

```
2. is signed by **both** an old key and a new key (dual signature), unless the old key is
   declared compromised, and
```

Section 18.7 gives the declaration consequences:

*Current text*

```
An identity document declaring `key_compromised` **MUST** cause Verifiers to reject
signatures made by that key after the declared compromise time, and **SHOULD** trigger review
of artifacts signed before it. Attestations signed by a compromised Authority key **SHOULD**
be treated as suspect pending re-issuance.
```

Nothing defines the declaration: `key_compromised` appears in Section 23.5 as a revocation
reason code and nowhere as a field, no field carries a compromise time, and there is no way to
identify *which* key, because public key objects (Section 5.3) have labels but no identifier of
their own. Section 14.1 has the same gap: `revocation_target_type` may be `identity_key`, but
`revocation_target_identifier` for a key has no defined form:

*Current text*

```
`revocation_target_type` is one of `access_token`, `access_grant`, `attestation`, or
`identity_key`.
```

A further gap: Section 5.5's reasoning says an attacker with only the old key cannot redirect
the identity "without also signing with it, which is detectable". An attacker who holds a
compromised old key can sign with it, so a dual-signed successor by the attacker and a
compromise successor by the owner can both exist. The draft has no rule for a fork in the chain.

### liquid's requirement and scenario

A developer's key is exposed. The developer still controls it but so does someone else. The
developer must be able to publish a successor signed with a new key only, name the exposed key
and the time from which it is untrusted, and have every verifier reject signatures by that key
made from that time on while keeping the signatures made before it, flagged for review. lake
must be able to record the same event as a revocation with the key identified unambiguously.

### Proposed spec text

Section 5.3, add after the key object examples:

```
Every public key object has a **key fingerprint**: the unpadded uppercase RFC 4648 base32
encoding of `SHA-512/256(canonical_public_key_object)`, the same computation as Section 5.1.
It identifies one key wherever a key must be named: in `signing_key_fingerprint_base32`, in
`compromised_keys`, and as the `revocation_target_identifier` of an `identity_key` revocation.
```

Section 5.4, add an optional field to the identity document, part of the signed body:

```
  "compromised_keys": [
    {
      "key_fingerprint_base32": "JBSWY3DPEHPK3PXPJBSWY3DPEHPK3PXPJBSWY3DPEHPK3PXPJBSW",
      "declared_at": "2026-09-01T08:00:00Z",
      "reason": "laptop stolen"
    }
  ],
```

```
`compromised_keys` lists keys the controller declares compromised. Each entry names the key by
fingerprint, gives the time from which the key is untrusted (`declared_at`, Section 6.5), and
MAY give a free-text reason. The array is inside the signed body. Entries are never removed
from later documents in the chain.
```

Section 5.5, replace item 2 with:

```
2. is signed by **both** a key of the previous document and a new key (dual signature), unless
   the new document's `compromised_keys` names the previous document's key, in which case the
   new key's signature alone suffices, and
```

and add after the list:

```
A Verifier presented with two successors of one document treats the fork as compromise of that
document's keys, whatever the successors declare, and MUST NOT accept signatures made after the
earlier of the two successors' `updated_at` by any key of the forked document until its policy
resolves the fork. A transparency log (Section 15.1) that fixes the order of documents is the
recommended way to resolve it.
```

Section 18.7, replace with:

```
An identity document whose `compromised_keys` names a key **MUST** cause Verifiers to reject
signatures made by that key at or after the entry's `declared_at`, and **SHOULD** trigger review
of artifacts signed by it before that time; those earlier signatures remain valid and a
Verifier **SHOULD** report that the signing key was later declared compromised. Attestations
signed by a compromised Authority key **SHOULD** be treated as suspect pending re-issuance.
Because `signed_at` is not verified (Section 6.7), the comparison with `declared_at` **SHOULD**
use external time evidence where the outcome matters.
```

Section 14.1, add after the list of target types: "For `identity_key`,
`revocation_target_identifier` is the key fingerprint (Section 5.3)."

Section 25: add `compromised_keys`, `key_fingerprint_base32`, `declared_at`, `reason`.

### What liquid does meanwhile

`compromised_keys` is an optional array on the identity document, inside the signed body, of
`{ key_fingerprint_base32, declared_at, reason? }`. The fingerprint is SHA-512/256 of the key's
canonical public key object as unpadded uppercase base32; `declared_at` is RFC 3339 UTC. A
successor may omit the old-key signature only when its own `compromised_keys` names the
predecessor key. A signature by that key at or after `declared_at` is invalid; one made before
it is valid and `verified_identity` reports compromised history. A compromise successor proves
that the new key signed the declaration; it cannot prove continuity of control through the
omitted old-key signature, and liquid leaves that to verifier policy, which is why the fork
rule above is proposed.

## Item 8. The remaining open questions liquid's specification answers

These are answers rather than problems. Each gives liquid's position, the reason, and the text
change, if any.

### 22.1. Primary environment

Enterprise services plus offline and air-gapped, in that combination. liquid signs on a laptop
on a plane and verifies in a hosted forge. `cjson` should stay non-optional: the auditability of
the signed material matters more to liquid than density, and the visual binding already
mandates `ccbor` where density matters (Section 16.4). No text change beyond recording the
answer in Section 22.1.

### 22.6. Recovery

It matters commercially for the hosted service and is, as the draft says, the most common
real-world failure of key-based identity. liquid's answer is that recovery is a *re-binding*
performed by an Authority: the hosted service, having verified the person by whatever means its
policy allows, issues an attestation that binds the old identifier to the new one under a
registered profile, and Verifiers that trust that Authority for that profile follow it. This
keeps recovery out of the identity document chain, which stays self-certifying, and puts it
where trust decisions already live (Section 15.4). liquid notes that recovery interacts badly
with end-to-end encryption: a service that cannot read the data cannot restore access to it, and
the draft should say that recovery of identity does not imply recovery of encrypted content.
Proposed text: a new profile `identity_rebinding/1` in Section 23.3 with attributes
`previous_identifier` and `successor_identifier`, and a sentence in Section 22.6 recording the
approach.

### 22.7. Attestation portability

liquid's specification does not answer this directly; the answer follows from Item 2. With a
stable identifier, attestations follow rotation with nothing to do. With recovery as a
re-binding attestation (22.6 above), portability across *replacement* is a policy decision per
Verifier about whether to honour the re-binding, which is where Section 15.4 already puts such
decisions. No text change beyond noting the dependency.

### 22.8. Ledger dependency

Optional, and liquid supplies one. liquid's hosted service runs a tiled, witnessed
transparency log of identity documents and attestations, and the protocol should keep treating
that as an optional resolution method under Section 15.1. The protocol must keep working with
purely local trust stores: liquid's air-gapped configuration is signing and hash chaining with
no network, and it is a supported configuration, not a degraded one. No text change.

### 22.9. Bearer mode

liquid does not need it. Every liquid client, including build workers and agents, holds a key.
liquid's answer is to remove bearer mode.

*Current text*

```
Bearer tokens (`binding_type: "bearer"`) are **NOT RECOMMENDED** and, if supported, **MUST**
have a lifetime of at most 300 seconds.
```

*Proposed text*

```
Bearer tokens are not defined by this protocol. `binding_type` is `client_key_proof_required`.
A gateway that must produce a bearer credential for a legacy system does so outside TAAP/1
under Section 21.1 and logs the downgrade.
```

with the corresponding removal in Section 18.8 and the second row of Section 20.

### 22.4. Advanced privacy

liquid takes no position. Its attribute commitments follow Section 10.4 as written and do not
prove predicates; nothing in liquid's specification needs them to.

## Summary of sections touched

| Item | Sections |
|---|---|
| 1. Delegation chains | new 11.5; 13.2; 14.3; 15.4; 17; 22.5; 25 |
| 2. Identifier stability, signing key | 5.5; 6.7; 22.2 |
| 3. The `taap:` scheme | 5.1; 22.10 |
| 4. Identity document signing and encoding | 2.3; 5.4 |
| 5. Previous document hash | 5.5 |
| 6. Signed bytes, `signature_purpose`, `signed_at` | 6.6; 6.7 |
| 7. Compromise declaration | 5.3; 5.4; 5.5; 14.1; 18.7; 25 |
| 8. Remaining open questions | 12.3; 18.8; 20; 22.1; 22.6; 22.7; 22.8; 22.9; 23.3 |

Document 01 covers 22.3 and the sections it lists. Items 2, 5 and 7 here and document 01
share the fingerprint and digest computations, so they are best read together.
