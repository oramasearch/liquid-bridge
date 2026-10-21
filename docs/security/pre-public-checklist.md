# Pre-public checklist for liquid and liquify

Everything that must be true before either repository is made public. **Making a repository public
is Steve's separate, explicit decision**; this list is what that decision rests on, not a substitute
for it. Nobody changes a repository's visibility, publishes a release publicly, or creates a public
fork because this list is complete.

**Tracks:** https://github.com/oramasearch/liquid-bridge/issues/11 (security) and the release epic
https://github.com/oramasearch/liquid-bridge/issues/16 (everything else). **State as of 2026-10-21**,
at liquid `b72fc9f` and liquify `dc2a271`. Tick an item only with a link to the commit, pull request
or issue comment that proves it.

**Owner** says who closes the item: *work* means an engineer or agent can do it; *Steve* means only
Steve can decide it.

## 1. Security review findings fixed

The review is [`review-2026-10.md`](review-2026-10.md). 48 findings, one issue each.

| | Item | Owner | State |
|---|---|---|---|
| [ ] | Every `p1` finding fixed and its test merged: liquid [L-01](review-2026-10.md#l-01) https://github.com/oramasearch/liquid/issues/383, [L-02](review-2026-10.md#l-02) https://github.com/oramasearch/liquid/issues/384, [L-03](review-2026-10.md#l-03) https://github.com/oramasearch/liquid/issues/385, [L-04](review-2026-10.md#l-04) https://github.com/oramasearch/liquid/issues/386, [L-06](review-2026-10.md#l-06) https://github.com/oramasearch/liquid/issues/388, [L-15](review-2026-10.md#l-15) https://github.com/oramasearch/liquid/issues/397, [L-19](review-2026-10.md#l-19) https://github.com/oramasearch/liquid/issues/401, [L-25](review-2026-10.md#l-25) https://github.com/oramasearch/liquid/issues/407, [L-30](review-2026-10.md#l-30) https://github.com/oramasearch/liquid/issues/412, [L-34](review-2026-10.md#l-34) https://github.com/oramasearch/liquid/issues/416; liquify [Y-01](review-2026-10.md#y-01) https://github.com/oramasearch/liquify/issues/71 | work | open |
| [ ] | Every `p2` finding fixed, or deferred by Steve in writing on its issue with the reason (each deferral is listed under *Known issues* in the first public release notes) | work, Steve for deferrals | open |
| [ ] | [L-38](review-2026-10.md#l-38) traced: no trust-controlling repository configuration arrives from a remote, or the ones that do are fixed | work | open |
| [ ] | `p3` findings are open issues that will be public; nothing in their text needs to stay private | work | open |
| [ ] | The review is re-read at the publish commit, its line numbers refreshed, and every finding's status recorded on its issue | work | open |

## 2. Fuzzing, sanitizers and hardening

Issue #11's original exit criterion was "fuzzers running in CI". The organisation has no CI, so the
criterion is restated as local and BuildKit-lane runs ([L-25](review-2026-10.md#l-25)). Steve
confirms the restatement when he signs off.

| | Item | Owner | State |
|---|---|---|---|
| [ ] | libFuzzer harnesses for the seven priority targets (CBOR, record decoders, sync codec, Git object store, protobuf, HTTP/2 and HPACK, pack and index readers) build behind a CMake option | work | none exist |
| [ ] | Each has run 24 CPU-hours without a finding under ASan and UBSan, with C sources instrumented; the runs and their commits are recorded in liquid `docs/build/` | work | open |
| [ ] | One TSan run of each repository's suite, and of liquify under ASan with tree-sitter on the upstream corpora; results recorded | work | open |
| [ ] | Release builds carry the hardening flags listed in L-25 | work | open |
| [ ] | Steve confirms that local and BuildKit-lane fuzzing replaces "in CI" for issue #11 | Steve | open |

## 3. Secrets and confidential content in history

| | Item | Owner | State |
|---|---|---|---|
| [x] | Secret scan of every ref, read-only, values redacted: liquid 24 hits, liquify 0, **no real credential** (review §8) | work | done 2026-10-21 |
| [ ] | The committed TLS fixture key removed and generated at run time; a `.gitleaksignore` lists the deliberate test vectors ([L-27](review-2026-10.md#l-27)) | work | open |
| [ ] | The confidentiality scrub's edit list applied to both repositories ([`../publishing/scrub-report.md`](../publishing/scrub-report.md) §9, https://github.com/oramasearch/liquid-bridge/issues/10) | work | open |
| [ ] | How history is published: a fresh-history export (the scrub report recommends it, §7) or the existing history rewritten | **Steve** | open |
| [ ] | On the export tree that will actually be pushed: `gitleaks git --redact=100 --log-opts="--all"` and `gitleaks dir --redact=100` report zero findings outside the ignore file, and the scrub report's §2 grep battery reports zero confidential terms | work | open |

## 4. Licences and dependencies

| | Item | Owner | State |
|---|---|---|---|
| [ ] | The open-source licence for liquid and liquify chosen (https://github.com/oramasearch/liquid-bridge/issues/2; bridge decision 5) | **Steve** | open |
| [ ] | A `LICENSE` file in both repositories; `NOTICE` complete in liquid and added to liquify | work, after the choice | liquid has `NOTICE` and no `LICENSE`; liquify has neither |
| [ ] | Contribution terms decided (DCO sign-off, a CLA, or neither) and written in a `CONTRIBUTING.md` | **Steve** | open |
| [ ] | Every submodule is public with a compatible licence, or is removed. Today: liquid's `capy` (public, BSL-1.0), `http` (public, BSL-1.0), `corosio` (**private**, BSL-1.0), `automerge-cpp` (**private**, MIT), `oramacore-cpp` (**private, no licence file**); liquify's tree-sitter submodules (public, MIT) and `corosio`, `http` | **Steve** for each private one | three private, one unlicensed |
| [ ] | Both `.gitmodules` use `https://` URLs, not `git@github.com:` | work | SSH URLs today |
| [ ] | Every FetchContent pinned by commit or `URL_HASH` ([L-26](review-2026-10.md#l-26)) | work | Boost, BLAKE3, zstd, googletest open |
| [ ] | Dependency audit: version, licence and open CVEs for each submodule and fetched source, as in the September review §7.3 | work | open |

## 5. The disclosure policy

Drafts are up for review: https://github.com/oramasearch/liquid/pull/421 (liquid `SECURITY.md`) and
https://github.com/oramasearch/liquify/pull/81 (liquify `SECURITY.md`).

| | Item | Owner | State |
|---|---|---|---|
| [ ] | The reporting address (and a PGP key, or the PGP sentence deleted) | **Steve** | placeholder |
| [ ] | The response times: acknowledge, assess, update interval, fix targets per severity, disclosure window | **Steve** | placeholders, with the September proposal quoted |
| [ ] | The safe-harbour wording approved as written, replaced with a standard text, or narrowed; counsel consulted if Steve wants | **Steve** | proposed text, marked not in force |
| [ ] | The supported-versions policy | **Steve** | proposed |
| [ ] | Lake's own security policy URL exists, or the out-of-scope line is reworded | **Steve** | placeholder |
| [ ] | The drafts merged into `dev` with every placeholder and question removed | work, after the above | PRs open |

## 6. Repository settings at the moment of publishing

| | Item | Owner | State |
|---|---|---|---|
| [ ] | Private vulnerability reporting turned on in both repositories | work, on Steve's go | off (private repositories) |
| [ ] | Secret scanning with push protection, and Dependabot alerts, turned on | work, on Steve's go | open |
| [ ] | Branch protection with required review on `main` and `dev` | Steve | open |
| [ ] | liquify's enabled `CI` and `Release` workflows: keep, or turn off before publishing. The organisation's rule is no CI; agents do not change them. If `Release` stays, a tag push must not publish ad-hoc or self-signed installers ([Y-07](review-2026-10.md#y-07)) | **Steve** | both enabled |
| [ ] | The READMEs state the known limits on the first screen (Windows, read guard, scanner, `liquid install`; [L-37](review-2026-10.md#l-37)) | work | open |

## 7. Sign-off

| | Item | Owner | State |
|---|---|---|---|
| [ ] | Every row above ticked with its proof | work | open |
| [ ] | Sign-off recorded on https://github.com/oramasearch/liquid-bridge/issues/11 with the publish commits of both repositories | Steve | open |
| [ ] | **The decision to make liquid and liquify public** | **Steve alone** | not taken |
