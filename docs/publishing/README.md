# Publishing readiness — liquid and liquify

The open-source release of liquid and liquify is a sequence, not a switch
(https://github.com/oramasearch/liquid-bridge/issues/16). This folder holds the two reviews that gate
it and the disclosure policy both repositories ship with.

| Document | Issue | What it is |
|---|---|---|
| [`scrub-report.md`](scrub-report.md) | https://github.com/oramasearch/liquid-bridge/issues/10 | Every confidential reference in liquid and liquify — working tree with file and line, history with the commits that introduced it — classified remove / rephrase / keep, a worker-ready edit list, and the recommendation on history (fresh-history publish, with the trade-offs). Nothing was rewritten or edited in either repository by this report. |
| [`security-review.md`](security-review.md) | https://github.com/oramasearch/liquid-bridge/issues/11 | The threat model: trust boundaries, what each component must never do, the findings from reading the code, the open items already tracked as issues, and the checklist of fuzzing targets, sanitizer runs and dependency audits to run before publishing. |
| [`SECURITY.md.draft`](SECURITY.md.draft) | https://github.com/oramasearch/liquid-bridge/issues/11 | The vulnerability disclosure policy, ready to drop into both repositories as `SECURITY.md` once the owner fills the reporting address and PGP placeholders. |

**Status has moved on.** The October 2026 review, [`../security/review-2026-10.md`](../security/review-2026-10.md),
re-checks every finding of `security-review.md` at newer code and files them as issues; the
pre-public checklist is [`../security/pre-public-checklist.md`](../security/pre-public-checklist.md);
and the `SECURITY.md` text now lives as a draft in each repository, on pull requests into `dev`. The
documents here remain the September record: read `security-review.md` for the trust boundaries and
the per-component invariants, which the October review does not repeat.

## How to use these

1. **A worker applies the edit list** in `scrub-report.md` §9 to liquid and liquify on branches, as
   ordinary PRs. The report is the specification; the worker does not need to re-scan.
2. **The owner decides the three things only the owner can:** the submodule visibility (`corosio`,
   `automerge-cpp`, `oramacore-cpp`), the publication method (the report recommends a fresh-history
   publish and says why), and the reporting address for `SECURITY.md`.
3. **The security checklist** in `security-review.md` §7 is worked as issues under the release epic;
   the findings table in §5 names the code to change. Fuzzers running in CI is the exit criterion issue
   #11 already states.
4. **Sign-off** for #10 is the checklist at the end of `scrub-report.md`; for #11 it is the checklist at
   the end of `security-review.md`. Both are recorded on the issue with the commit that closed them.

## How to verify

Re-run the command battery in `scrub-report.md` §2 against the export tree before the public push;
the expected result is zero hits for the confidential terms outside `tests/scan/test_detectors.cpp`.
The security findings each cite file and line at liquid `a5659bc` / liquify `e7b47ee`; re-read them at
the publish commit, since the code moves daily.
