# TAAP/1 proposal: content-addressed subjects

**To:** the TAAP/1 protocol owner
**From:** the liquid project (first significant implementer of TAAP/1)
**Against:** TAAP/1 `1.0.0-draft.1`, dated 2026-08-05, as vendored at liquid
`docs/standards/taap-1-spec-draft.md`
**Resolves:** Section 22.3, in the part that concerns objects
**Status:** draft, not yet sent (bridge issue
https://github.com/oramasearch/liquid-bridge/issues/1)

Section numbers below refer to draft.1. Every quotation marked *Current text* is verbatim
from the vendored copy. Requirement words are used as Section 2.1 defines them.

## 1. Summary

TAAP/1 identifies every Subject by a key. Section 5.1 defines an identity as a key-derived
identifier, and Section 10.2 names the Subject of an attestation with `subject_identifier`,
which holds one of those identifiers. That is right for people, organisations, devices and
agents, all of which can hold a key.

It leaves out everything that is identified by what it is rather than by who controls it: a
document, a file, a build artifact, a container image, a version-control change, a model
checkpoint, or a signed TAAP artifact itself. These objects are content-addressed. They have
no key, cannot sign, cannot consent, and cannot hold status. Today nothing can be attested
*about* them.

This proposal adds one thing to the protocol: a **content-addressed subject**, an identifier
of the form

```
taap:1:content:<digest_algorithm>:<digest_base32>
```

that names an object by an algorithm-tagged digest of its bytes, together with the rule for
how an attestation references it (`subject_digest`, present exactly when `subject_identifier`
is absent), the Verifier obligations that follow, a digest-algorithm registry, and the text
change for every section the addition touches. Nothing else in the protocol changes. The
change is additive, and implementations that predate it fail closed when they meet it.

## 2. Motivation: liquid's concrete cases

liquid is a version-control and build system in which TAAP/1 is the whole security model, not
one component of it. Every claim liquid makes about anything is a TAAP attestation, and every
party that makes a claim is a TAAP identity. The parties are covered by Section 5.1. The
things the claims are about mostly are not.

liquid's registered attestation profiles, with the kind of subject each one needs:

| Profile | Authority | Subject | Subject holds a key? |
|---|---|---|---|
| `org_membership/1` | lake (the hosted service) | a person | yes |
| `delegation/1` | a principal | an agent | yes |
| `authorship/1` | the author | a drip (one recorded edit) | no |
| `review_approval/1` | a reviewer | a change | no |
| `scan_result/1` | the secret scanner | a drip | no |
| `slsa_provenance/1` | the build worker | a build result | no |
| `sbom/1` | the build graph | a build artifact | no |
| `reproducibility/1` | an independent verifier | a cached build result | no |
| `abi_compatibility/1` | liquid | a shared library blob | no |
| `delta/1` | the publisher | a delivered artifact | no |
| `hot_update/1` | the incremental engine | a rebuilt result | no |
| `image_provenance/1` | the projection tool | an OCI image (by its SHA-256 digest) | no |
| `projection/1` | the projection tool | a package, image manifest or chart | no |
| `model_provenance/1` | a training run | a model checkpoint | no |

Twelve of fourteen profiles have a subject that cannot hold a key. Two concrete situations
show why a key-derived subject cannot be substituted:

**A review approval.** A reviewer approves a change. The statement liquid needs is
"Authority R asserts that change X is approved". The change is a record in a content-addressed
store; its identity is the digest of its canonical bytes. Attesting about the change's *author*
instead would say something different and weaker: the author may have many changes, the
approval must bind to exactly one, and the approval must survive the author's key rotation,
the author leaving the organisation, and the change being copied to another repository.

**Build provenance.** A build worker records that it produced result Y from these inputs with
this command. Verifiers downstream (deployment admission, a customer receiving a package) hold
the bytes of Y and need to find and check every statement about exactly those bytes. There is
no party that "is" the result. liquid's current provenance profile therefore carries a
non-standard `subject_kind: "artifact"` field and a digest of the result body, documented as
an interim form that will be replaced by the protocol form once one exists, with old
signatures retained and never reinterpreted. That interim form is the reason this proposal is
written.

Giving objects keys is not an answer. A key per object would mean a private key per file,
held by nobody, or by whoever created the object, which collapses back to attesting about the
creator. Objects are correctly identified by digest, exactly as `evidence_references` already
identifies evidence by `evidence_digest_base64` (Section 10.2) and as identity documents chain
by `previous_document_hash_base64` (Section 5.4). The protocol already relies on
content addressing at its edges; this proposal lets it name a content-addressed thing as a
Subject.

## 3. The subject form

### 3.1. Grammar

A content-addressed subject is a string:

```
content_subject   = "taap:1:content:" digest_algorithm ":" digest_base32
digest_algorithm  = 1*( %x61-7A / DIGIT / "-" )      ; a registered identifier, Section 23.6
digest_base32     = 1*( %x41-5A / %x32-37 )          ; unpadded uppercase RFC 4648 base32
```

Example, the SHA-512/256 digest of the ASCII bytes `example liquid change record`:

```
taap:1:content:sha512-256:DZAVAWNH3YPDXVGJTGS6WD3CPBOOADTB3ILFTVJCITLWWHEXQABA
```

Segment by segment:

- `taap:1:` is the same scheme and protocol major version as Section 5.1.
- `content` is a reserved literal. It occupies the position Section 5.1 gives to the signature
  algorithm, and Section 23.1 reserves the word so that no signature algorithm can ever be named
  `content`. A parser that reads the third segment learns from that one token which grammar it
  is reading. The two identifier spaces are disjoint by construction.
- `digest_algorithm` is a digest algorithm identifier registered in the new Section 23.6. It is
  lowercase and is compared exactly.
- `digest_base32` is the complete digest output, encoded as unpadded uppercase RFC 4648 base32,
  the same encoding Section 5.1 uses for key fingerprints and for the same reason: it survives
  print, QR codes, OCR and being read aloud. A 256-bit digest is exactly 52 characters.

### 3.2. Canonicalisation of the identifier text

1. Implementations MUST emit `digest_base32` in uppercase and MUST NOT emit padding.
2. On input, implementations MAY accept lowercase base32 and MUST compare the base32 segment
   case-insensitively; every other segment is compared exactly.
3. A Verifier MUST decode `digest_base32` and MUST reject the identifier if the decoded length
   differs from the registered output length of `digest_algorithm`.
4. Section 5.2 applies unchanged: a content-addressed subject MUST NOT be truncated, displayed
   as truncated without marking, or used for a security decision in abbreviated form.
5. There is no whitespace, no trailing separator and no optional segment.

Section 5.1 does not state a comparison rule for key-derived identifiers. Rule 2 is proposed for
Section 5.1 as well, so both forms behave alike.

### 3.3. What is digested: the subject content rule

TAAP/1 does not define what a document, a build result or a change is, and should not. What it
must define is *which bytes* the digest covers, because otherwise two implementations will
compute different identifiers for the same object. The proposal fixes this with a **subject
content rule**, named by the attestation profile (Section 23.3), from these options:

- **`bytes`.** The digest is over the object's bytes exactly as stored or transmitted. This is
  the rule for files, chunks, blobs, image layers, and any object that is already a byte string.
- **`taap_artifact`.** The object is itself a TAAP artifact: an identity document, an attestation,
  an access grant, an access token or a revocation list. The digest is over the artifact's
  complete canonical bytes in its declared encoding, `signatures` field included, exactly as
  stored. An attestation about a TAAP artifact is therefore a statement about that artifact *as
  signed*, which is what a countersignature, an endorsement or a transparency-log inclusion
  needs. This is the same computation liquid uses for `previous_document_hash_base64` (see
  Section 7 below and document 02, item 5).
- **Profile-defined.** A profile MAY define its own rule when the object is a structured record
  whose canonical form the application controls. The rule MUST be a deterministic function of
  the object alone, MUST be stated in the profile registration, and MUST NOT include any field
  whose value depends on the attestation being issued. liquid's build result is the motivating
  case: the result record stores the digest of its own provenance attestation, so the provenance
  profile digests the result body with that one field omitted, which avoids a content-addressed
  cycle.

The content rule is deliberately not encoded in the identifier. The identifier is a pure digest,
so the same bytes have one identifier under every profile and can be compared across profiles,
systems and stores. Interpretation lives where the draft already puts interpretation: in the
profile, which Section 10.3 says Verifiers key their policy off.

### 3.4. Registered digest algorithms (new Section 23.6)

| Identifier | Algorithm | Output | Status |
|---|---|---|---|
| `sha512-256` | SHA-512/256 (FIPS 180-4) | 32 bytes | REQUIRED |
| `sha256` | SHA-256 (FIPS 180-4) | 32 bytes | RECOMMENDED |
| `blake3` | BLAKE3, default 256-bit output, unkeyed | 32 bytes | RECOMMENDED |
| `sha3-256` | SHA3-256 (FIPS 202) | 32 bytes | OPTIONAL |

`sha512-256` is REQUIRED because it is already the draft's hash (Sections 5.1, 10.4, 18.9), so
every implementation has it. `sha256` is RECOMMENDED because the ecosystems liquid must
interoperate with (OCI images, SLSA and in-toto statements, SPDX and CycloneDX documents) address
content by SHA-256. `blake3` is RECOMMENDED because it is the default object identifier in
liquid's store; liquid keeps BLAKE3 and SHA-256 identifiers side by side and does not rewrite
existing references, so it needs both registered.

Registration rules: an algorithm MUST have at least 256 bits of output and no practical
collision attack. MD5 and SHA-1 MUST NOT be registered. Keyed or salted constructions (a MAC, a
keyed BLAKE3) are not content addresses, because the identifier would depend on a secret, and
MUST NOT be registered.

Note that three of the four entries produce 32 bytes. The digest length identifies nothing;
the tag is load-bearing. See Section 8.2 below.

### 3.5. Interaction with key-derived subjects

A content-addressed subject is not a party. It has no keys, no identity document, no status,
no consent to give and nothing to revoke. The proposal makes this explicit:

- It MUST NOT appear in `identifier` or `controller` (Section 5.4), `sender_identifier` or
  `recipient_identifier` (Section 7), `verifier_identifier` or `requested_subject_identifier`
  (Section 9), `authority_identifier` or `status_authority_identifier` (Section 10),
  `client_identifier`, `grant_authority_identifier`, `resource_holder_identifier`,
  `intended_resource_holder_identifier` or `bound_client_key_identifier` (Sections 11 to 13),
  `issuing_authority_identifier` (Section 14), `signing_key_identifier` (Section 6.7), or the
  `subject_identifier` of an access grant or access token. Delegation is on behalf of a party
  that consented (Section 11.3); an object cannot consent.
- It appears in exactly one protocol field: `subject_digest` on an attestation (Section 4
  below).
- It MAY appear as a *value* inside `asserted_attributes` or `evidence_references` where a
  profile says so (liquid's `abi_compatibility/1` names the earlier library blob in
  `compatible_with`; `delta/1` names `source` and `target`). There it is application data, not
  a protocol identifier, and the protocol attaches no semantics to it.
- An implementation of draft.1 that meets a `taap:1:content:` string in any identifier field
  will, under Section 6.8, find `content` absent from its signature-algorithm accept-list and
  reject. That is the desired failure.

## 4. The attestation reference rule

### 4.1. `subject_digest`

The attestation object (Section 10.2) gains one field:

| Field | Type | Meaning |
|---|---|---|
| `subject_digest` | string, Section 3.1 grammar | The content-addressed object this attestation is about. |

Exactly one of `subject_identifier` and `subject_digest` MUST be present. An attestation with
both, or with neither, is malformed and MUST be rejected with `subject_reference_invalid`.

The field is a separate field rather than a second value space for `subject_identifier`, for
three reasons. First, Section 3.1's goal G2 asks for field names that say what they hold, and
`subject_identifier` is used throughout the draft for a party that can be authenticated
(Section 9), can consent (Sections 10.5 and 11.3) and can request suppression (Section 14.2);
none of that applies to an object. Second, the "exactly one" rule is checkable by structure
rather than by parsing a string. Third, an implementation of draft.1 that receives an
attestation with `subject_digest` and no `subject_identifier` sees a required field missing
and rejects, instead of parsing a digest as an identifier and looking up a key that does not
exist.

The field is a string in the identifier grammar rather than a structured object with
`digest_algorithm` and `digest_base32` members, because that keeps it interchangeable with
`subject_identifier` everywhere an identifier is logged, displayed, printed, or placed in an
`evidence_locator`, and because the tag inside the string cannot be separated from the digest
it qualifies.

### 4.2. Verifier obligations for content-addressed subjects (new Section 10.6)

A Verifier that receives an attestation carrying `subject_digest` MUST, in order:

1. Verify the Authority signature and the structure of the attestation as for any attestation.
2. Parse `subject_digest` under Section 3.1, and reject a malformed value with
   `subject_reference_invalid`.
3. Check `digest_algorithm` against its configured `acceptable_digest_algorithms`
   (Section 15.4), and reject with `digest_algorithm_not_accepted` otherwise. The Verifier
   MUST NOT infer the algorithm from the digest length.
4. Check that the decoded digest length equals the registered output length.
5. Confirm that the registered profile accepts a content-addressed subject, and read the
   profile's subject content rule.
6. If the Verifier holds the object, recompute the digest under that rule and compare. A
   mismatch means "this attestation is not about this object" and MUST be reported as
   `subject_content_mismatch`; it is not a signature failure and MUST NOT be reported as one.
7. If the Verifier does not hold the object, the attestation is a verified statement about an
   object the Verifier has not seen. The Verifier MUST NOT conclude from the attestation alone
   that the object exists, that it has the attested property, or that any object it later
   receives is the attested one, until step 6 has been performed on those bytes.

Step 7 is the offline case Section 3.1's goal G5 asks for: signature and structure verify with
no other party, and the content match is a local computation whenever the bytes arrive.

### 4.3. Presentation, consent, status and revocation

- **Presentation.** Any party holding the attestation MAY present it (`attestation_presentation`,
  Section 8). The Subject cannot present, sign or consent. A profile SHOULD say who is expected
  to hold attestations issued under it.
- **Consent.** Section 10.5 applies to party Subjects. An Authority issuing an attestation about
  an object SHOULD record in `evidence_references` how it obtained the object, which is the
  audit trail Section 10.3 already gives that field.
- **Selective disclosure.** Section 10.4 applies unchanged; the commitments are over attributes,
  not over the subject.
- **Status.** `status_policy` remains the Authority's statement about the validity of the
  attestation itself. The object has no status of its own.
- **Revocation.** The attestation is revocable by its Authority under Section 14 exactly as
  today. The object is never a revocation target. Section 14.2's "Subject MAY request
  suppression" applies to party Subjects only.
- **Domain separation.** Unchanged. The artifact type is `attestation` and the domain separator
  is `TAAP/1 attestation`.
- **Tokens.** `attested_attribute_summary` (Section 12.2) is unchanged. A token is issued on
  behalf of a party; the party may have presented attestations about objects, and the summary
  records them like any other.

## 5. Examples

The digests in this section are real. Each is computed over the short ASCII string named next
to it, so an implementer can reproduce every value. In liquid the object would be the canonical
CBOR of a change or result record; the short strings stand in for those bytes.

### 5.1. A review approval about a change

Object: the ASCII bytes `example liquid change record`.
SHA-512/256: `1e415059a7de1e3bd4c999a5eb0f62785ce00e61da1659d52244d76b1c978002`.

```json
{
  "artifact_type": "attestation",
  "protocol_version": "TAAP/1",
  "attestation_identifier": "01K4HB6ZQ3S8M2N7P0R5T9V1X4",
  "authority_identifier": "taap:1:ed25519:REVIEWERKEY...",
  "authority_display_name": "Repository reviewer",
  "subject_digest": "taap:1:content:sha512-256:DZAVAWNH3YPDXVGJTGS6WD3CPBOOADTB3ILFTVJCITLWWHEXQABA",
  "attestation_profile": "review_approval/1",
  "asserted_attributes": {
    "reviewer": "taap:1:ed25519:REVIEWERKEY...",
    "approved": true,
    "comment": "Parser change reviewed against the grammar tests."
  },
  "evidence_references": [
    {
      "evidence_type": "repository_change",
      "evidence_locator": "liquid:change:sha512-256:DZAVAWNH3YPDXVGJTGS6WD3CPBOOADTB3ILFTVJCITLWWHEXQABA",
      "evidence_digest_base64": "HkFQWafeHjvUyZml6w9ieFzgDmHaFlnVIkTXaxyXgAI="
    }
  ],
  "issued_at": "2026-09-06T14:02:11Z",
  "valid_from": "2026-09-06T14:02:11Z",
  "expires_at": null,
  "status_policy": {
    "status_check_recommended": false,
    "status_authority_identifier": "taap:1:ed25519:REVIEWERKEY...",
    "maximum_status_age_seconds": 0
  },
  "signatures": [
    {
      "signature_algorithm": "ed25519",
      "signing_key_identifier": "taap:1:ed25519:REVIEWERKEY...",
      "signing_key_label": "reviewer-laptop-2026",
      "signature_purpose": "attestation",
      "signed_at": "2026-09-06T14:02:11Z",
      "signature_bytes_base64": "..."
    }
  ]
}
```

`evidence_digest_base64` carries the same 32 bytes as `subject_digest`, in the base64 encoding
that field already uses. The two encodings name one object.

### 5.2. Build provenance about a result

Object: the ASCII bytes `example liquid build result body`.
SHA-512/256: `f8ac40954f0e6ffc488e9c46d93853c4d014cc88b115a4142f758aaf7fd04063`.

```json
{
  "artifact_type": "attestation",
  "protocol_version": "TAAP/1",
  "attestation_identifier": "01K4HB7C2D4F6G8H0J1K3M5N7P",
  "authority_identifier": "taap:1:ed25519:BUILDERKEY...",
  "authority_display_name": "liquid build worker",
  "subject_digest": "taap:1:content:sha512-256:7CWEBFKPBZX7YSEOTRDNSOCTYTIBJTEIWEK2IFBPOWFK676QIBRQ",
  "attestation_profile": "slsa_provenance/1",
  "asserted_attributes": {
    "buildDefinition": {
      "buildType": "https://github.com/oramasearch/liquid/blob/main/docs/library/provenance.md#liquid-action-v1",
      "externalParameters": { "command": ["cc", "-c", "parser.c"], "cwd": "src" }
    },
    "runDetails": {
      "builder": { "id": "taap:1:ed25519:BUILDERKEY..." },
      "metadata": { "startedOn": "2026-09-06T14:00:00Z", "finishedOn": "2026-09-06T14:00:02Z" }
    }
  },
  "evidence_references": [],
  "issued_at": "2026-09-06T14:00:02Z",
  "valid_from": "2026-09-06T14:00:02Z",
  "expires_at": null,
  "status_policy": {
    "status_check_recommended": false,
    "status_authority_identifier": "taap:1:ed25519:BUILDERKEY...",
    "maximum_status_age_seconds": 0
  },
  "signatures": [ { "...": "builder signature, signature_purpose attestation" } ]
}
```

The profile registration for `slsa_provenance/1` states its subject content rule: the canonical
CBOR of the result record with the `provenance` field omitted (Section 3.3, profile-defined).
Under the `bytes` rule with the same object the identifier would be different, which is why the
rule is part of the registration and a Verifier reads it in step 5.

### 5.3. The same subject with a SHA-256 digest

Object: the ASCII bytes `example liquid drip record`.
SHA-256: `bcd359d824f57bed82ac10a227dc821f02221890105dc1199c23fde860be3606`.

```
taap:1:content:sha256:XTJVTWBE6V563AVMCCRCPXECD4BCEGEQCBO4CGM4EP66QYF6GYDA
```

A liquid store writes this object's identifier as `sha256:bcd359d8...3606` (lowercase hex with
the same algorithm tag). The TAAP form encodes the same 32 bytes in base32. Conversion is
mechanical in both directions and loses nothing.

### 5.4. Canonical bytes

Three fields of the Section 5.1 attestation, in both canonical encodings.

Canonical JSON (Section 6.2; keys sorted by code point):

```
{"attestation_profile":"review_approval/1","protocol_version":"TAAP/1","subject_digest":"taap:1:content:sha512-256:DZAVAWNH3YPDXVGJTGS6WD3CPBOOADTB3ILFTVJCITLWWHEXQABA"}
```

Canonical CBOR (Section 6.3; keys sorted by their encoded bytes, so shorter keys sort first),
158 bytes:

```
a3                                              map(3)
  6e 7375626a6563745f646967657374               "subject_digest"
  78 4e 746161703a313a636f6e74656e743a          text(78) "taap:1:content:
        7368613531322d3235363a                             sha512-256:
        445a415641574e48335950445856474a               DZAVAWNH3YPDXVGJ
        544753365744334350424f4f41445442               TGS6WD3CPBOOADTB
        33494c4654564a4349544c575748455851             3ILFTVJCITLWWHEXQ
        414241                                             ABA"
  70 70726f746f636f6c5f76657273696f6e           "protocol_version"
  66 544141502f31                               "TAAP/1"
  73 6174746573746174696f6e5f70726f66696c65     "attestation_profile"
  71 7265766965775f617070726f76616c2f31         "review_approval/1"
```

As one hex string:

```
a36e7375626a6563745f646967657374784e746161703a313a636f6e74656e743a7368613531322d3235363a445a415641574e48335950445856474a544753365744334350424f4f4144544233494c4654564a4349544c5757484558514142417070726f746f636f6c5f76657273696f6e66544141502f31736174746573746174696f6e5f70726f66696c65717265766965775f617070726f76616c2f31
```

The signing input for the full attestation is, per Section 6.6, the ASCII bytes
`TAAP/1 attestation` (`544141502f31206174746573746174696f6e`), one `00` byte, then the
canonical bytes of the attestation without its `signatures` field. `subject_digest` is inside
those bytes, so the subject is covered by the Authority signature exactly as
`subject_identifier` is today.

### 5.5. An identity document as a content-addressed subject

Object: the ASCII bytes `example identity document bytes`, standing in for the complete
canonical CBOR of a stored identity document, signatures included (the `taap_artifact` rule).
SHA-512/256: `6a7e3ed7e94922700b65e3f5398b36f48be1744a76c00338b46b47fdd8a8020b`.

| Where the digest appears | Value |
|---|---|
| `previous_document_hash_base64` in the successor document (Section 5.4) | `an4+1+lJInALZeP1OYs29IvhdEp2wAM4tGtH/dioAgs=` |
| `subject_digest` of an attestation about the document | `taap:1:content:sha512-256:NJ7D5V7JJERHAC3F4P2TTCZW6SF6C5CKO3AAGOFUNND73WFIAIFQ` |

One digest, two encodings, so a transparency log can attest "this identity document was
included at sequence N" with a subject that a Verifier can match against the chain link it
already holds.

## 6. Security considerations (new Section 18.11)

### 6.1. Collision and second-preimage resistance

An attestation about an object is a statement about the bytes the Authority digested. If the
object's author can later produce a second object with the same digest, the Authority's
statement transfers to bytes it never saw. Section 23.6 therefore admits only algorithms with
no practical collision attack and at least 256 bits of output. The author of an object is often
the party with the strongest motive to find a collision, and the Authority cannot defend
against it except by the choice of algorithm.

### 6.2. Algorithm confusion

`sha256`, `sha512-256` and `blake3` all produce 32 bytes. A Verifier that inferred the
algorithm from the length would accept a digest under an algorithm it has not chosen to trust,
which is the failure Section 6.8 forbids for signatures. Verifiers MUST use only the tag, and
only if it is on their accept-list. Two identifiers with different algorithms MUST NOT be
treated as naming the same object unless the Verifier holds bytes that reproduce both.

### 6.3. Name versus bytes

An attestation is about bytes, never about a name. A Verifier that resolves a path, a tag, a
URL or a store key to bytes MUST digest the bytes it received and compare against
`subject_digest`. Trusting the name is trusting the resolver, which is the transport-derived
trust Section 7.4 rules out.

### 6.4. Cross-profile and cross-type reuse

`attestation_profile` and the domain separator are both inside the signed bytes. An attestation
about object X under profile P cannot be presented as a statement under profile Q, and cannot be
relabelled as a message or another artifact type. Two attestations with the same
`subject_digest` under different profiles are different statements and MUST be evaluated under
their own profiles.

### 6.5. Attestations about TAAP artifacts

Under the `taap_artifact` rule the digested bytes include the inner artifact's signatures. An
outer attestation therefore endorses the inner artifact as signed, but it does not launder it:
a Verifier MUST still verify the inner artifact on its own terms, including revocation and,
under Section 18.7, compromise of the inner signing key. An endorsement of a later-revoked
artifact remains a true statement about what was endorsed and confers nothing.

### 6.6. Self-reference

A profile's content rule MUST NOT include any field whose value depends on the attestation
being issued. Such a digest cannot be computed, and an implementation that tries will either
loop or, worse, digest a placeholder. liquid's provenance profile omits the result's
`provenance` field for this reason.

### 6.7. What does not change

Objects cannot be revoked; the attestation about them can, under Section 14. Section 5.2's ban
on truncation applies to content-addressed subjects. Section 18.7 applies to the Authority's
key. Nothing in this proposal alters the envelope, the signing procedure, the authentication
flow, grants or tokens.

## 7. Privacy considerations (new Section 19.5)

- **A digest is a commitment.** It reveals nothing about a high-entropy object, and it confirms a
  guess about a low-entropy one. This is the same property that makes Section 10.4 require
  salts for attribute commitments. Where an object is both guessable and confidential, the
  profile SHOULD define its content rule over a salted commitment to the object rather than the
  raw bytes, and deliver the salt with the object, mirroring Section 10.4. No new protocol field
  is needed; the rule belongs to the profile.
- **Objects can be about people.** A document has an author; a change may contain a name. An
  attestation about such an object is personal data by proxy, and Sections 19.3 and 19.4 apply
  to it.
- **Correlation.** A content-addressed subject is globally stable and correlatable across
  Verifiers by construction. Unlike a key-derived identifier, it cannot be varied per
  relationship (Section 19.1). This is a stated limitation: an object has one set of bytes.

## 8. Compatibility and versioning

1. **Additive.** Every existing attestation remains valid and unchanged. `subject_identifier`
   keeps its meaning. `protocol_version` remains `TAAP/1`; the document version becomes
   `1.0.0-draft.2` or whatever the owner's next draft number is.
2. **Fail closed on old implementations.** A draft.1 Verifier meeting `subject_digest` either
   rejects for a missing `subject_identifier` or, if it parses the value as an identifier,
   rejects `content` as an unregistered signature algorithm under Section 6.8. Neither path
   accepts anything. The draft does not currently say what a Verifier does with a field it does
   not know; this proposal adds, for attestations, that a Verifier MUST reject an attestation
   that carries neither subject form it understands.
3. **Registries.** New Section 23.6 (digest algorithms); `content` reserved in Section 23.1;
   Section 23.3 profile registrations extended with the accepted subject forms and the subject
   content rule.
4. **Error codes.** `subject_reference_invalid`, `digest_algorithm_not_accepted`,
   `subject_content_mismatch` added to Section 17.
5. **Trust policy.** `acceptable_digest_algorithms` added to Section 15.4.
6. **Reserved names.** `subject_digest` added to Appendix B.
7. **liquid's migration.** liquid's records today carry a `subject_kind` and a digest in
   liquid's own record layout, documented as interim. When this proposal is adopted liquid
   introduces a new record and profile version carrying `subject_digest`, keeps verifying the
   interim form for records already signed, and never reinterprets an existing signature.
   liquid's `blake3:<hex>` and `sha256:<hex>` object identifiers convert to and from the TAAP
   form by re-encoding the same bytes.

## 9. Proposed text changes, section by section

### Section 2.2, the Subject row

*Current text*

```
| Subject | S | The party an attestation is about, or on whose behalf access is delegated. Usually a human or an organization. |
```

*Proposed text*

```
| Subject | S | The party an attestation is about, or on whose behalf access is delegated. Usually a human or an organization. For attestations only, the Subject MAY instead be a content-addressed object (Section 5.6), which can be attested about and can act in no role. |
```

### Section 2.3, Other Terms

*Current text*: the list has three entries, `Artifact`, `Fingerprint` and `Canonical form`.

*Proposed text*: append one entry.

```
- **Content-addressed subject**: an object identified by an algorithm-tagged digest of its
  bytes rather than by a key (Section 5.6). It can be the Subject of an attestation and
  nothing else.
```

### Section 5.1, Identifiers

*Current text*

```
- `algorithm` is a registered signature algorithm identifier (Section 23.1).
- `fingerprint_base32` is the unpadded uppercase RFC 4648 base32 encoding of
  `SHA-512/256(canonical_public_key_object)`.
```

*Proposed text*

```
- `algorithm` is a registered signature algorithm identifier (Section 23.1). The literal
  `content` is reserved in this position and never names a signature algorithm: an identifier
  whose third segment is `content` is a content-addressed subject (Section 5.6), not a
  key-derived identifier, and MUST NOT be accepted where a key-derived identifier is required.
- `fingerprint_base32` is the unpadded uppercase RFC 4648 base32 encoding of
  `SHA-512/256(canonical_public_key_object)`.

Implementations MUST emit `fingerprint_base32` in uppercase without padding, MAY accept
lowercase on input, and MUST compare the base32 segment case-insensitively and every other
segment exactly.
```

### Section 5.5, Key Rotation, item 1

*Current text*

```
1. references the previous document by hash,
```

*Proposed text*

```
1. references the previous document in `previous_document_hash_base64`: the RFC 4648 base64
   encoding of the SHA-512/256 digest of the previous document under the `taap_artifact`
   content rule of Section 5.6, that is, its complete canonical bytes as stored, signatures
   included. The same 32 bytes, base32-encoded, form the previous document's content-addressed
   subject `taap:1:content:sha512-256:...`,
```

Document 02, item 5, proposes the same definition on its own; it is repeated here because it
depends on Section 5.6.

### New Section 5.6, Content-Addressed Subjects

*Current text*: none.

*Proposed text*

```
### 5.6. Content-Addressed Subjects

Some things an Authority needs to make statements about hold no key: a document, a file, a
build artifact, a container image, a version-control change, a model checkpoint, or a signed
TAAP/1 artifact. Such an object is identified by a digest of its bytes:

    taap:1:content:<digest_algorithm>:<digest_base32>

Example:

    taap:1:content:sha512-256:DZAVAWNH3YPDXVGJTGS6WD3CPBOOADTB3ILFTVJCITLWWHEXQABA

Where:

- `content` is a reserved literal (Section 23.1). It occupies the position a signature
  algorithm occupies in Section 5.1, so the two identifier forms cannot be confused.
- `digest_algorithm` is a registered digest algorithm identifier (Section 23.6), lowercase,
  compared exactly.
- `digest_base32` is the complete digest output as unpadded uppercase RFC 4648 base32.
  Implementations MAY accept lowercase on input and MUST compare case-insensitively. A Verifier
  MUST decode it and MUST reject the identifier if the decoded length differs from the
  algorithm's registered output length. Section 5.2 applies.

**What is digested.** The bytes covered by the digest are fixed by the attestation profile's
subject content rule (Section 23.3), one of:

- `bytes`: the object's bytes exactly as stored or transmitted.
- `taap_artifact`: for an object that is itself a TAAP/1 artifact (identity document,
  attestation, access grant, access token, revocation list), its complete canonical bytes in
  its declared encoding, `signatures` included, exactly as stored.
- a profile-defined rule: a deterministic function of the object alone, stated in the profile
  registration, which MUST NOT include any field whose value depends on the attestation being
  issued.

The rule is not encoded in the identifier. The identifier is a pure digest, so the same bytes
have one identifier under every profile.

**A content-addressed subject is not a party.** It has no keys, no identity document, no
status, cannot sign, cannot consent, and cannot be revoked. It MUST NOT appear in any field
that names a sender, recipient, Authority, Grant Authority, Client, Resource Holder, Verifier,
signing key, controller, or the Subject of an access grant or access token. It MAY appear only
in `subject_digest` of an attestation (Section 10.2) and, as application data, inside
`asserted_attributes` and `evidence_references` where a profile says so.

**Reasoning (why a digest, not a key per object):** An object has no controller who could hold
a key on its behalf without the statement collapsing into a statement about that controller.
Content addressing is already how this protocol names evidence (`evidence_digest_base64`) and
chains identity documents (`previous_document_hash_base64`); this section lets the same kind of
name be a Subject.

**Reasoning (why the algorithm is in the identifier):** SHA-256, SHA-512/256 and BLAKE3 all
produce 32 bytes. A Verifier cannot recover the algorithm from the digest, and Section 6.8
forbids guessing. The tag makes the identifier self-describing and lets a Verifier's accept-list
be authoritative.

**Reasoning (why base32):** The same reason as Section 5.1. These identifiers are printed,
placed in QR codes and read aloud, and one encoding for both identifier forms is one fewer
thing to get wrong.
```

### Section 6.8, Algorithm Agility

*Current text*

```
Every signed object carries its algorithm. Verifiers **MUST** reject algorithms not in their
configured accept-list, and **MUST NOT** infer the algorithm from key length or from the
signature itself.
```

*Proposed text*

```
Every signed object carries its algorithm. Verifiers **MUST** reject algorithms not in their
configured accept-list, and **MUST NOT** infer the algorithm from key length or from the
signature itself.

The same rule applies to digests. A content-addressed subject (Section 5.6) carries its digest
algorithm; Verifiers **MUST** reject digest algorithms not in their configured accept-list
(`acceptable_digest_algorithms`, Section 15.4) and **MUST NOT** infer the digest algorithm
from the digest length.
```

### Section 7.1, Field Semantics, the sender and recipient rows

*Current text*

```
| `sender_identifier` | yes | TAAP identifier of the sender. |
| `recipient_identifier` | no | Omitted for broadcast or when the recipient is unknown. |
```

*Proposed text*

```
| `sender_identifier` | yes | Key-derived TAAP identifier (Section 5.1) of the sender. A content-addressed subject (Section 5.6) is never valid here. |
| `recipient_identifier` | no | Key-derived TAAP identifier of the recipient. Omitted for broadcast or when the recipient is unknown. A content-addressed subject is never valid here. |
```

### Section 10.1, Purpose

*Current text*

```
An attestation is a signed statement: *Authority A asserts that Subject S has attributes X
as of time T*. This is the "signed attribution" requirement.
```

*Proposed text*

```
An attestation is a signed statement: *Authority A asserts that Subject S has attributes X
as of time T*. This is the "signed attribution" requirement.

S is either a party, named by a key-derived identifier (Section 5.1) in `subject_identifier`,
or an object, named by a content-addressed subject (Section 5.6) in `subject_digest`. In the
second case the statement is about the object's bytes and nothing else.
```

### Section 10.2, Attestation Object

*Current text*: the example object contains the line

```
  "subject_identifier": "taap:1:ed25519:JBSWY3DP...",
```

and no `subject_digest`.

*Proposed text*: keep the example as it is and add, immediately after it:

```
`subject_identifier` names a party. An attestation about an object carries `subject_digest`
instead, and the rest of the object is unchanged:

    {
      "artifact_type": "attestation",
      "protocol_version": "TAAP/1",
      "attestation_identifier": "01K4HB6ZQ3S8M2N7P0R5T9V1X4",
      "authority_identifier": "taap:1:ed25519:REVIEWERKEY...",
      "authority_display_name": "Repository reviewer",
      "subject_digest": "taap:1:content:sha512-256:DZAVAWNH3YPDXVGJTGS6WD3CPBOOADTB3ILFTVJCITLWWHEXQABA",
      "attestation_profile": "review_approval/1",
      "asserted_attributes": { "reviewer": "taap:1:ed25519:REVIEWERKEY...", "approved": true },
      "evidence_references": [],
      "issued_at": "2026-09-06T14:02:11Z",
      "valid_from": "2026-09-06T14:02:11Z",
      "expires_at": null,
      "status_policy": { "status_check_recommended": false, "status_authority_identifier": "taap:1:ed25519:REVIEWERKEY...", "maximum_status_age_seconds": 0 },
      "signatures": [ { "...": "authority signature" } ]
    }

Exactly one of `subject_identifier` and `subject_digest` **MUST** be present. An attestation
with both, or with neither, **MUST** be rejected with `subject_reference_invalid`.
```

### Section 10.3, Field Reasoning

*Current text*: no entry for the subject fields.

*Proposed text*: add, before the `attestation_profile` entry:

```
**`subject_identifier` or `subject_digest`** exactly one present. The first names a party
(Section 5.1); the second names an object by digest (Section 5.6).
*Reasoning:* Two fields rather than two value spaces for one field: the name says which kind of
Subject it holds, the exactly-one rule is checkable by structure, and an implementation that
predates `subject_digest` rejects a missing `subject_identifier` instead of looking up a key
for a digest.
```

### Section 10.5, Subject Consent to Attestation

*Current text*

```
An Authority **SHOULD NOT** issue an attestation about a Subject without either an
`attestation_request` signed by that Subject or a documented lawful basis recorded in
`evidence_references`.
```

*Proposed text*

```
An Authority **SHOULD NOT** issue an attestation about a party Subject without either an
`attestation_request` signed by that Subject or a documented lawful basis recorded in
`evidence_references`.

A content-addressed subject cannot sign a request. An Authority issuing an attestation about an
object **SHOULD** record in `evidence_references` how it obtained the object, and **SHOULD**
consider whether the object is about a person (Section 19.5).
```

### New Section 10.6, Verifying Attestations About Content-Addressed Subjects

*Current text*: none.

*Proposed text*: the numbered list in Section 4.2 of this proposal, introduced by "A Verifier
that receives an attestation carrying `subject_digest` **MUST**, in order:" and followed by:

```
**Reasoning (step 7):** Goal G5 asks for offline verification. Signature and structure verify
with no other party; the content match is a local computation whenever the object's bytes
arrive. What a Verifier must not do is treat a statement about unseen bytes as a statement
about whatever bytes it happens to receive next.
```

### Section 14.2, Who May Revoke, the attestation row

*Current text*

```
| `attestation` | Issuing Authority; Subject MAY request suppression |
```

*Proposed text*

```
| `attestation` | Issuing Authority; a party Subject MAY request suppression. An attestation about a content-addressed subject has no party who can request suppression, and the object itself is never a revocation target. |
```

### Section 15.4, Trust Policy Object

*Current text*: the example contains the line

```
  "acceptable_signature_algorithms": ["ed25519", "p256"],
```

*Proposed text*: add, immediately after it:

```
  "acceptable_digest_algorithms": ["sha512-256", "sha256", "blake3"],
```

and, after the reasoning paragraph:

```
**Reasoning (`acceptable_digest_algorithms`):** The same rule as `acceptable_signature_algorithms`,
for the digest algorithm of a content-addressed subject (Sections 5.6 and 6.8).
```

### Section 17, Error Handling

*Current text*: the registered-codes list ends

```
`rate_limited`, `internal_error`.
```

*Proposed text*

```
`rate_limited`, `internal_error`, `subject_reference_invalid`, `digest_algorithm_not_accepted`,
`subject_content_mismatch`.
```

with, after the list:

```
**Reasoning (`subject_content_mismatch` distinct from `signature_invalid`):** A valid
attestation about different bytes is a different situation from a forged one. Collapsing them
would make an honest mismatch (the wrong file was presented) look like an attack, and would hide
a real attack behind a common operational error.
```

### New Section 18.11, Content-Addressed Subjects

*Current text*: none.

*Proposed text*: Section 6 of this proposal, subsections 6.1 to 6.6, under the heading
`### 18.11. Content-Addressed Subjects`.

### New Section 19.5, Content-Addressed Subjects

*Current text*: none.

*Proposed text*: Section 7 of this proposal under the heading
`### 19.5. Content-Addressed Subjects`.

### Section 20, Design Rationale

*Current text*: the table has no row for subjects.

*Proposed text*: append one row.

```
| Content-addressed subjects by algorithm-tagged digest | A key per object; a party as a stand-in for the object; an untagged digest | Objects hold no key; a stand-in changes the statement; three registered algorithms share one output length, so the tag is what makes the digest self-describing. |
```

### Section 22.3

*Current text*

```
**22.3. Attestations about organizations and machines.** Should the Subject of an attestation
be allowed to be a non-human (a device, a build artifact, a corporate entity)? Supporting this
well probably means additional profiles and possibly delegation chains.
```

*Proposed text*

```
**22.3. Attestations about organizations and machines.** Resolved for objects: a build
artifact, a document, a change or any other content-addressed thing is a Subject through
Section 5.6 and `subject_digest`. A device or a corporate entity holds a key and is a party
under Section 5.1 with a `controller`; whether those need additional profiles is a registry
question (Section 23.3), not a protocol one. Delegation chains are Section 22.5.
```

### Section 23.1, Signature Algorithm Identifiers

*Current text*: the table ends with the row

```
| `slh-dsa-sha2-128s` | SLH-DSA | RESERVED |
```

*Proposed text*: append one row.

```
| `content` | Not an algorithm. Reserved so that an identifier whose third segment is `content` is unambiguously a content-addressed subject (Section 5.6). | RESERVED |
```

### Section 23.3, Attestation Profiles

*Current text*

```
Each profile registration **MUST** specify attribute names, value types and formats, required
versus optional attributes, and expected volatility to guide `status_policy`.
```

*Proposed text*

```
Each profile registration **MUST** specify attribute names, value types and formats, required
versus optional attributes, expected volatility to guide `status_policy`, which subject forms
the profile accepts (key-derived, content-addressed, or both), and, when it accepts a
content-addressed subject, the subject content rule of Section 5.6 that fixes the bytes
digested and, where useful, who is expected to hold attestations issued under the profile.
```

### New Section 23.6, Digest Algorithm Identifiers

*Current text*: none.

*Proposed text*: the table and registration rules in Section 3.4 of this proposal under the
heading `### 23.6. Digest Algorithm Identifiers`.

### Section 25, Appendix B, the Attestation line

*Current text*

```
Attestation: `attestation_identifier`, `authority_identifier`, `authority_display_name`,
`subject_identifier`, `attestation_profile`, `asserted_attributes`, `evidence_references`,
`issued_at`, `valid_from`, `expires_at`, `status_policy`,
`attribute_disclosure_commitments`.
```

*Proposed text*

```
Attestation: `attestation_identifier`, `authority_identifier`, `authority_display_name`,
`subject_identifier`, `subject_digest`, `attestation_profile`, `asserted_attributes`,
`evidence_references`, `issued_at`, `valid_from`, `expires_at`, `status_policy`,
`attribute_disclosure_commitments`.

Trust policy: `acceptable_digest_algorithms` joins the existing trust policy fields.
```

## 10. Questions for the owner

1. **Names.** `subject_digest` and the reserved literal `content` are proposals. If the owner
   prefers `subject_content_identifier`, or `object` in place of `content`, liquid has no
   objection; what liquid needs is the disjointness of the two identifier grammars and the
   exactly-one rule.
2. **One digest per attestation.** in-toto statements let a subject carry several digests of
   the same bytes under different algorithms. This proposal allows one. liquid does not need
   more: its store resolves each identifier to bytes, and verification recomputes. If the owner
   wants a multi-digest form, liquid asks that a single-digest attestation remain valid.
3. **BLAKE3 status.** liquid needs `blake3` registered; RECOMMENDED versus OPTIONAL is the
   owner's call.
4. **Signatures inside the `taap_artifact` rule.** liquid includes them, so that an endorsement
   is of the artifact as signed and so that `previous_document_hash_base64` and the
   content-addressed subject of an identity document are one computation. If the owner would
   rather digest the unsigned body, liquid asks that the choice be written down in Section 5.5
   as well, since liquid has shipped the signatures-included reading there.
