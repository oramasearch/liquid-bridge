# TAAP feedback

Drafts of the feedback liquid owes the owner of the TAAP/1 protocol, written in full so they
can be sent as they stand.

## What TAAP is and why liquid owes feedback

TAAP/1, the Transport-Agnostic Authorization and Attribution Protocol, is the identity,
attestation and delegation protocol that liquid uses as its whole security model: every party
that writes to a liquid repository is a TAAP identity and every claim liquid makes about
anything is a TAAP attestation. liquid vendors the draft at
`docs/standards/taap-1-spec-draft.md` (version `1.0.0-draft.1`, dated 2026-08-05) and
describes how it uses the protocol in
`docs/features/25-identity-attestation-and-transparency.md`.

The draft is a request for comments with open questions in its Section 22, and liquid is its
first significant implementation. Implementing it produced two kinds of feedback: one change the
protocol needs before liquid's attribution of documents, drips, changes and artifacts can be
standard rather than interim, and a set of readings liquid had to make where the draft was
silent or inconsistent, plus liquid's answers to the open questions its own specification
settles.

## The documents

| Document | What it proposes | Tracking |
|---|---|---|
| [`01-content-addressed-subjects.md`](01-content-addressed-subjects.md) | A content-addressed subject form, `taap:1:content:<digest_algorithm>:<digest_base32>`, the `subject_digest` attestation field with an exactly-one rule against `subject_identifier`, Verifier obligations, a digest-algorithm registry, security and privacy considerations, and the exact text change for every affected section. Resolves Section 22.3 for objects. | https://github.com/oramasearch/liquid-bridge/issues/1 |
| [`02-protocol-feedback.md`](02-protocol-feedback.md) | Delegation chains that are attenuation-only with depth limits (22.5), identifier stability across rotation and naming the signing key (22.2, 6.7), the `taap:` scheme (22.10), how identity documents are signed and encoded (5.4), the previous-document hash (5.5), what the signature covers and what `signature_purpose` and `signed_at` are (6.6, 6.7), the key-compromise declaration (5.5, 18.7, 14.1), and liquid's answers to 22.1, 22.4, 22.6, 22.7, 22.8 and 22.9. | https://github.com/oramasearch/liquid-bridge/issues/8 |

## Who they go to

The TAAP protocol owner, meaning the editor of the draft. The draft's editor line is still
"(fill in)" and the draft refers to its owner as "the protocol owner" throughout Section 22;
these documents use the same term. Sending them is Steve's.

## Status

| Document | Status |
|---|---|
| 01 | Drafted 2026-09-06. Not sent. |
| 02 | Drafted 2026-09-06. Not sent. |

Both were written against liquid `main` at commit `0443d45` (2026-09-06), so that "what liquid
does meanwhile" in each item matches the code and the library documentation at that commit.

## What happens after the owner answers

From the done-when lists on the two issues:

1. Refresh the vendored copy under liquid `docs/standards/` and record the version or commit it
   corresponds to.
2. Update liquid `docs/features/25-identity-attestation-and-transparency.md`, whose table of
   open questions liquid answers is the source of these documents.
3. Record the outcome in liquid `CLAUDE.md` under *Decisions* and in the bridge
   [`decisions.md`](../decisions.md), item 4.
4. In liquid, introduce a new record and profile version for the protocol's subject form, keep
   verifying the interim form for records already signed, and never reinterpret an existing
   signature. That rule is already written in liquid `docs/library/provenance.md`.

## Conventions used in the drafts

- Section numbers refer to draft.1.
- Text marked *Current text* is quoted verbatim from the vendored copy.
- Requirement words follow the draft's Section 2.1.
- Every digest shown in the examples is computed over the short input named beside it, so an
  implementer can reproduce it.
- Where the draft is silent, the drafts say so instead of presenting a reading as the draft's
  intent.
