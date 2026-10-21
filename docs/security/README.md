# Security — liquid and liquify

The security record for the two repositories that are going open source. Making either public is
Steve's separate decision (https://github.com/oramasearch/liquid-bridge/issues/16); this folder is
what that decision rests on.

| Document | What it is |
|---|---|
| [`review-2026-10.md`](review-2026-10.md) | The October 2026 review at liquid `b72fc9f` and liquify `dc2a271`: the attack surface, every September finding re-checked, the new surfaces (signing and hardware keys, release approval, transparency and timestamps, hot update, installs, the services, liquify's plugins and AI assistant), 48 findings with file and line and one issue each, the controls that are sound, and the secret scan of both histories. |
| [`pre-public-checklist.md`](pre-public-checklist.md) | Everything that must be true before going public: the findings fixed, fuzzing, the history scanned and scrubbed, licences and submodules, the disclosure policy approved, repository settings, and the sign-off. Each row names who closes it. |

The September threat model, the confidentiality scrub and the first `SECURITY.md` draft are in
[`../publishing/`](../publishing/README.md). The `SECURITY.md` drafts now live in each repository, on
pull requests into `dev`.

## How to use these

- **Fixing a finding:** its issue carries the evidence, the fix and the test that proves it. When it
  is fixed, tick it in the checklist with the PR link.
- **Before publishing:** re-read the review at the publish commit, re-run the secret scan on the export
  tree (review §8), and work the checklist to the end.
- **Changing the review:** it is a dated record. Write a new dated review rather than editing the
  findings of an old one; update this index and the checklist to point at it.
