# Scrub report — confidential references in liquid and liquify

**For:** https://github.com/oramasearch/liquid-bridge/issues/10, under the open-source release epic
https://github.com/oramasearch/liquid-bridge/issues/16.
**Scanned on 2026-09-05** against `oramasearch/liquid` at `a5659bc` (`main`) and `oramasearch/liquify`
at `e7b47ee` (`main`), both pulled fast-forward from `origin/main` first. Read-only: no rewrite, no
push, no deletion was performed. Values of key material are never reproduced here — only location and
kind.

## 1. Summary

| | liquid | liquify |
|---|---|---|
| Commits on `main` / across all refs | 195 / 386 (141 refs: 74 remote branches, 59 of them with commits not on `main`, 0 tags) | 20 / 40 (9 remote branches, 6 with unmerged commits) |
| Tracked files | 625 | 53 |
| Working-tree hits that must be removed or rephrased | **~60 lines in 16 files** (§3) | **~20 lines in 7 files** (§5) |
| Named customers | none found | none found |
| Internal hostnames (`*.oramadev.net`), IPs, kubeconfigs | none, in tree or history | none |
| Tokens, API keys, passwords | none real. One **committed TLS private key** (localhost test fixture, `tools/reapi-peers/nativelink-tls-key.pem`) plus the secret scanner's own synthetic test vectors | none |
| Personal email | `steve.sperandeo@gmail.com` is the **author of every commit** (386/386); not present in file content | author of every commit (40/40) |
| History content hits (`git log --all -S`) | Metis 6 commits, Zetta 23, `orama-work` 2, `zetta-bridge` 1, `corporate-intelligence` 2, `/Users/stevesperandeo` 3, private key 2 | Zetta 6, `orama-work`/`zetta-bridge`/`homer6`/`/Users/` 1 |
| Commit *messages* naming Zetta / Metis | 6 / 2 | 1 (body of `4b8ea33`, three mentions) / 0 |
| History recommendation | **Fresh-history publish** (§7) | **Fresh-history publish** (§7) |

The three findings that matter most:

1. **`docs/features/23-metis-and-zetta.md` is the confidential material, not a pointer to it.** It restates
   Metis's theory (the three bands, the ten dimensions, the remediation order, the go-to-market sequence)
   and describes Zetta's architecture and its overlap with liquid. It has existed since `9549e52`
   (2026-09-01) and is linked from `README.md`, `docs/features/README.md`, `18-lake-service.md`,
   `24-multiplayer-and-agents.md` and `CLAUDE.md`. Removing the file from the tree is not enough: every
   revision of it is in history, which is the strongest argument for §7.
2. **Both `CLAUDE.md` files carry the private map**: the absolute local path
   `/Users/stevesperandeo/dev/homer6/orama-work/modules/zetta-bridge/modules/zetta`, the names
   `orama-work`, `zetta-bridge`, `corporate-intelligence`, `docs/metis/`, `docs/competitors/`, a table of
   nine private repositories, and the sentence "`oramasearch/liquid` is private". Every revision of both
   files since 2026-09-02 (liquid `2664020`, liquify `4b8ea33`) contains it.
3. **A PKCS#8 RSA private key is committed** at `tools/reapi-peers/nativelink-tls-key.pem` (added in
   `9eea816`, kept in `7fe008e`). It is self-signed for `CN=localhost`, `SAN=DNS:localhost, IP:127.0.0.1`,
   valid 2026-09-04 to 2036-09-01, and used only by `run-tls-interop.sh` for a NativeLink test peer. It is
   harmless as a credential but every downstream secret scanner (GitHub push protection, gitleaks,
   trufflehog) will flag it, and a shared test key is a habit a security-focused project should not
   publish. Generate it at run time instead (§3.10).

Everything else is rephrasing: "as Zetta does" clauses in build comments and design docs, SSH clone URLs
to private repositories, and links to the private bridge.

## 2. Method

Terms searched (case-insensitive, extended regex, whole tree excluding `modules/` submodule checkouts,
which are separate repositories):

| Group | Regex |
|---|---|
| Confidential names | `[Mm]etis`, `[Zz]etta`, `orama-work`, `zetta-bridge`, `corporate-intelligence` |
| Internal hosts, paths, handles | `oramadev`, `/Users/`, `homer6`, `\b(10\|172\|192)\.[0-9]+\.[0-9]+\.[0-9]+\b`, `kubeconfig`, `AZURE_`, `DOCKERHUB`, `R2_`, `CLOUDFLARE_` |
| Emails | `[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}`, `gmail\.com` |
| Private repository names | `oramasearch/[A-Za-z0-9_.-]+`, `orama-operator`, `orama-cloud-v1`; visibility of each checked with `gh repo view --json visibility` |
| Key material | `gh[pousr]_…`, `github_pat_…`, `AKIA[0-9A-Z]{16}`, `xox[baprs]-…`, `sk-(ant-)?…`, `-----BEGIN [A-Z ]*PRIVATE KEY`, JWT shape `eyJ….eyJ…`, `[Bb]earer …`, `(password\|secret\|token\|api[_-]?key\|private[_-]?key\|access[_-]?key)\s*[:=]\s*["'][^"']{6,}["']`; tracked `*.pem`, `*.key`, `*.hex`, `.env` paths |
| Customer names | every `[Cc]ustomer` hit read in context; capitalised names near `pilot`, `design partner`, `prospect`, `engagement`; other Orama product names (`amaro`, `clustera`, `wtm`, `blueprint`, `oramacore`) |
| Owner's name | `Steve` (classified, not confidential) |

Commands, per repository:

```sh
git pull --ff-only origin main
git grep -n -I -E -e '<regex>' -- . ':!modules'                         # working tree, every tracked file
git log --all --pickaxe-regex -S'<regex>' --name-only --format='%h %ad %s'   # history: commits that add or remove the term
git log --all --format='%h %s%n%b' | grep -i -E '<terms>'                 # commit messages (pickaxe does not see these)
git log --all --format='%an <%ae> | %cn <%ce>' | sort | uniq -c            # author and committer identities
git log --all --diff-filter=D --name-only                                 # files deleted in history
git log --all --name-only --format= | sort -u | grep -i -E 'metis|zetta|competitor|customer|\.env|\.pem|\.key|token|secret|credential|kubeconfig|id_rsa'
git rev-list --all --objects | … | git cat-file -p <blob> | grep -a -n -o -E '<key-material and email regexes>'   # every unique blob reachable from any ref (3,250 in liquid, 182 in liquify)
openssl x509 -in tools/reapi-peers/nativelink-tls-cert.pem -noout -subject -issuer -dates -ext subjectAltName
```

No dedicated secret scanner (`gitleaks`, `trufflehog`, `detect-secrets`) is installed on the scanning
host; the blob-level regex sweep above stands in for one. Before the public push, run `gitleaks detect
--source . --log-opts=--all` and `trufflehog git file://.` on the scrubbed tree as an independent check
(§8).

## 3. liquid — working tree

Classification: **remove** (delete the text or file), **rephrase** (keep the point, drop the confidential
name), **keep** (with the justification stated). Line numbers are for `a5659bc`. The consolidated
worker-ready edit list is §9.

### 3.1 Metis — 25 lines in 6 files — remove

| File:line | Content | Class |
|---|---|---|
| `docs/features/23-metis-and-zetta.md` (whole file, 142 lines) | Metis defined as "the Enterprise Intelligence OS — Orama's pivot"; its three bands and ten dimensions (lines 19–41); the GTM sequence (96–117); Zetta's architecture (13, 56–91); `docs/metis/`, `docs/competitors/`, `corporate-intelligence`, `orama-work`, the `wtm ORAMA-ZETTA` blueprint (121–131) | **remove the file** |
| `README.md:178-189` | "It is the intended go-to-market vehicle for **Metis**, the Enterprise Intelligence OS Orama is pivoting to build, whose central claim is that intelligence is bounded by *data availability*." … "while **Zetta** turns available data into running instruments." + link to 23 | **remove** paragraphs; rephrase the section (§9) |
| `docs/features/18-lake-service.md:144-146` | "— which is Zetta's stated posture too (`[23](23-metis-and-zetta.md)`) — and provenance is exactly the Band B availability dimension Metis's theory identifies as binding." | **rephrase** |
| `docs/features/24-multiplayer-and-agents.md:227` | "That is the same argument as `[23](23-metis-and-zetta.md)`, applied to the actors rather than the data." | **remove** sentence |
| `docs/features/README.md:97` | index row for 23 | **remove** row |
| `CLAUDE.md:276-286` (Confidentiality section), `:281-282`, `:310` | "**Metis material is confidential** — `docs/metis/` and `docs/competitors/` in `oramasearch/corporate-intelligence`" … | **remove** section (see 3.3) |

### 3.2 Zetta — 68 lines in 13 files

The public liquid must not describe Zetta. Two kinds of hit: descriptions of Zetta (remove) and
"the same as Zetta" comparisons in liquid's own design notes (rephrase — the point survives without the
name). A third kind — the rule "never depend on Zetta" — is rephrased to "no closed-source dependency",
because a public rule naming Zetta invites the question the rule exists to avoid.

| File:line | Content | Class |
|---|---|---|
| `docs/features/23-metis-and-zetta.md:13,15,40-41,47,51,56-91,113,128-131,136,140` | Zetta's architecture ("C++26 equal-peer CRDT-replicated store with clustering, JSONL storage plus large objects, a Postgres-SQL subset, headed and headless modes"), the four storage options, the blueprint | **remove** (file) |
| `README.md:184-189` | "while **Zetta** turns available data into running instruments" and "the overlap between liquid's storage layer and Zetta's" | **remove** |
| `CLAUDE.md:112` | liquify row: "(private for now, open source eventually; never depends on Zetta)" | **rephrase** → "(its own repository, `oramasearch/liquify`)" |
| `CLAUDE.md:243-249` | "**Read Zetta only from the umbrella bridge** — `/Users/stevesperandeo/dev/homer6/orama-work/modules/zetta-bridge/modules/zetta` … A standalone `~/dev/oramasearch/zetta` was found 1,053 commits behind and missing the whole `include/zetta/api/` HTTP layer" and the operator path | **remove** paragraph |
| `CLAUDE.md:259-266` | related-repositories rows: lake ("Zetta as data plane"), liquify ("never depends on Zetta"), orama-operator ("the Zetta operator"), corosio ("Zetta consumes it … an earlier claim that Zetta had drifted"), http ("branch `zetta-patches`") | **remove** the lake, orama-operator, k0s, orama-bridge, liquid-bridge rows; **rephrase** corosio and http rows to drop the Zetta clauses (the branch name `zetta-patches` is already public on the public `oramasearch/http` fork — keep) |
| `CLAUDE.md:307-335` (Decisions 1–6) | "Zetta is closed / enterprise source-available"; "lake uses Zetta as much as possible as its data plane"; "already has its own Zetta as observed-state store"; "already vendored by Zetta … shared open component between liquid (open) and Zetta (closed)"; "matching Zetta and oramacore-cpp"; "Zetta: source-available" | **rephrase** (§9 gives the text) |
| `CLAUDE.md:341` | "must stay free of Zetta and, where feasible, of third-party types" | **rephrase** → "must stay free of third-party types where feasible" |
| `AGENTS.md:16` | "Never take a dependency on Zetta or on `oramasearch/lake`; this repository is open source eventually." | **rephrase** |
| `CMakeLists.txt:4` | "# … the same auto-selection Zetta uses." | **rephrase** |
| `CMakeLists.txt:624` | "# Tests: GoogleTest via FetchContent + CTest, matching Zetta." | **rephrase** |
| `docs/features/17-implementation.md:103,127,134,167` | "as Zetta and oramacore-cpp already do — one async stack across the org"; "the same code Zetta already vendors as a submodule"; "The same stack Zetta and oramacore-cpp use; Zetta vendors both."; "matching Zetta and oramacore-cpp." | **rephrase** (drop the clauses) |
| `docs/features/18-lake-service.md:144` | "which is Zetta's stated posture too" | **rephrase** (with 3.1) |
| `docs/features/21-liquify-ide.md:202-206` | "(`oramasearch/liquify`, private for now, open source eventually, and it never depends on Zetta, the same rule as liquid)"; "the stack Zetta's headed mode already proves on macOS, Windows and Linux" | **rephrase** |
| `docs/library/api-map.md:11,24,28` | "keeps Zetta, Boost and the engine choices out of the API"; "Not Zetta, ever."; "(Zetta's pattern)" | **rephrase** |
| `docs/library/libliquid.md:25` | "**never a Zetta type**, and" | **remove** clause |
| `docs/features/README.md:97` | "Metis and Zetta — How liquid fits Orama's pivot…" | **remove** row |
| `.gitmodules:15` | `branch = zetta-patches` (branch of the **public** `oramasearch/http` fork) | **keep** — already public; the owner may rename the branch upstream later |

### 3.3 `orama-work`, `zetta-bridge`, `corporate-intelligence`, local paths, `homer6` — remove or keep

| File:line | Content | Class |
|---|---|---|
| `CLAUDE.md:244` | `/Users/stevesperandeo/dev/homer6/orama-work/modules/zetta-bridge/modules/zetta` — absolute local path, personal GitHub handle, two private bridge names | **remove** |
| `CLAUDE.md:248` | `orama-work/modules/orama-cloud-v1-bridge/modules/orama-cloud-v1-operator` | **remove** |
| `CLAUDE.md:278-279` | `oramasearch/corporate-intelligence`, `docs/metis/`, `docs/competitors/` | **remove** |
| `CLAUDE.md:270-274` | "Copies of public upstreams are never forks … `gh repo create oramasearch/<name> --private` … set the `upstream` remote's push URL to an invalid value so an accidental push cannot leak our changes" — internal process for private copies | **remove** |
| `CLAUDE.md:285-286` | "`oramasearch/liquid` is **private**. Never make it public, never fork it publicly. Every `oramasearch` repo is private" | **remove** (false once published) |
| `docs/features/23-metis-and-zetta.md:4,121-131` | same names | **remove** (file) |
| `docs/features/01-object-model-and-storage.md:46`, `02-version-control.md:8`, `17-implementation.md:12`, `23-metis-and-zetta.md:73` | links to `https://github.com/homer6/automerge-cpp` | **keep** — that repository is public (verified) and MIT; it is the public upstream named in bridge decision 2. Repoint to `oramasearch/automerge-cpp` if and when that copy is made public. |

### 3.4 Private repository names — 71 lines in 25 files

Visibility as of 2026-09-05 (`gh repo view --json visibility`):

| Repository | Visibility | Referenced from liquid | Class |
|---|---|---|---|
| `oramasearch/liquid` | private (to be public) | README, docs, `.gitmodules` of liquify | keep; **change SSH clone URLs to HTTPS** (`README.md:334`, `docs/library/libliquid.md:33`) |
| `oramasearch/liquify` | private (to be public) | CLAUDE.md, features 21 | keep |
| `oramasearch/http` | **public** fork of `cppalliance/http` | `.gitmodules:14`, CLAUDE.md, NOTICE | keep; `.gitmodules` URL → HTTPS |
| `oramasearch/corosio` | **private** patch carrier for `cppalliance/corosio` | `.gitmodules:7`, CLAUDE.md:265, NOTICE, 17-implementation | **publishing blocker, not a docs edit**: a public liquid cannot `--recurse-submodules` a private repository. Make it public (the Boost licence permits it) or upstream the epoll fix and pin `cppalliance/corosio`. `.gitmodules` URL → HTTPS. |
| `oramasearch/automerge-cpp` | **private** | `.gitmodules:11`, CLAUDE.md:263, NOTICE | **publishing blocker**: make public (MIT, decision 2 says "it stays open") or pin the public `homer6/automerge-cpp` at the same commit. URL → HTTPS. |
| `oramasearch/oramacore-cpp` | **private** | `.gitmodules:18`, CLAUDE.md:264, NOTICE, features 12/17, `src/search/` | **publishing blocker**: liquid's search links it. Publish it under a compatible licence, or vendor the BM25F tokenizer and scorer with attribution. URL → HTTPS. |
| `oramasearch/lake` | private (enterprise, stays private) | `CLAUDE.md:259`, `README.md:176`, `AGENTS.md:16` | **rephrase**: name the product ("lake, the hosted service at lake.live") without linking the private repository |
| `oramasearch/orama-operator` | private | `CLAUDE.md:248,261,317`, `README.md:178` | **remove** links; the operator is lake-side infrastructure the public liquid does not need to name |
| `oramasearch/k0s` | private copy of `k0sproject/k0s` | `CLAUDE.md:258,262`, `README.md:175` | **remove** links |
| `oramasearch/liquid-bridge` | private | `CLAUDE.md:252,258`, `README.md:173-179`, `AGENTS.md:17`, `docs/features/17-implementation.md` etc. (10 lines) | **rephrase**: "the action plan and cross-repository decisions are kept in the project's private planning repository" — no URL. Issue links `liquid-bridge/issues/7` → remove. |
| `oramasearch/orama-bridge` | private | `CLAUDE.md:4,268`, `AGENTS.md:7` (8 lines) | **rephrase**: "org-wide conventions apply" without the URL |
| `oramasearch/corporate-intelligence` | private | `CLAUDE.md:279`, features 23 | **remove** |
| `oramasearch/zetta` | private | `CLAUDE.md:245` (`~/dev/oramasearch/zetta`) | **remove** |

Every repository above except `oramasearch/http` is private today. `oramasearch/zetta-api` does not exist
under that name (bridge decision 19 refers to it; nothing in liquid does).

### 3.5 Key material and secret-shaped strings

| File:line | Kind | Class |
|---|---|---|
| `tools/reapi-peers/nativelink-tls-key.pem` | **RSA-2048 private key, PKCS#8** (`-----BEGIN PRIVATE KEY-----`), pairs with `nativelink-tls-cert.pem` (self-signed `CN=localhost`, SAN `localhost`/`127.0.0.1`, valid to 2036) | **remove**; generate at run time in `tools/reapi-peers/run-tls-interop.sh` (§9, item 10) |
| `tools/reapi-peers/nativelink-tls-cert.pem` | the matching certificate | **remove** with the key |
| `tests/scan/test_detectors.cpp:57,63,65` | synthetic Slack-token, OpenSSH-private-key header and JWT shapes used as the secret scanner's positive test cases | **keep** — obviously fake test vectors; add a `.gitleaksignore` (or `# gitleaks:allow` comments) so public scanners do not report them |
| `src/scan/detectors.cpp:160` | the string `-----BEGIN PGP PRIVATE KEY BLOCK-----` as a detector pattern | **keep** — it is the detector |
| `.github/workflows/ci.yml:29,120`, `docs/build/ci.md:5,53`, `docs/library/simulation.md:60` | the *name* of the org secret `ORAMA_SUBMODULES_TOKEN` (no value) | **keep until the submodules are public**, then **remove** the token step and the sentences — the token exists only to read private submodules |
| `docs/cli/README.md:102,293-294`, `docs/library/sync.md:44` | `LIQUID_TOKEN` — a product feature (bearer credential for push/pull), no value | **keep** |
| `tests/fixtures/sealed-secret/*-private.hex` | X25519 test vectors, on branch `issue-204-secret-seal` only (not on `main`) | keep on the branch; they are RFC-style vectors — confirm before merging that they are not real keys |

No GitHub, AWS, Slack, OpenAI/Anthropic, JWT or bearer credentials, no `password=`/`secret=` assignments,
no kubeconfig, no Azure/Cloudflare/R2 secret names, and no private IP addresses were found in any of the
3,250 unique blobs reachable from any liquid ref.

### 3.6 Emails — 21 lines in 12 files — keep

All are either `git@github.com:` SSH URLs (see 3.4), test identities `*@example.test`
(`tests/git/test_object_store.cpp:119,153`, `tests/test_repository.cpp:346,360,405`), or public
mailing-list archive URLs quoted verbatim in `docs/research/*/sources.md` (`gitgitgadget@gmail.com`,
`ccache@lists.samba.org`, `devel@lists.fedoraproject.org`, `…@redhat.com`, `…@secretsauce.net`,
`bugs@example.org`) and the documented `noreply@anthropic.com` / `noreply@openai.com` trailer formats in
`docs/research/25-multiplayer-and-agent-collaboration/`. No personal address appears in any tracked file
or historical blob. The personal address is in the commit metadata (§4.3).

### 3.7 Hostnames, cloud, deployment — keep

`oramadev`, `lake.oramadev.net`, `AKS`: **zero hits** in tree and history. `Cloudflare` (14 lines) and
`Azure` (80 lines) occur only in `docs/research/*/sources.md` as public-service references (R2 pricing,
Azure Key Vault, Azure DevOps) plus one line each in `docs/features/11-secrets-and-encryption.md` and two
research READMEs — public landscape, **keep**. `deploy/workers/*` names no host or registry; `tools/reapi-peers/*`
pulls public `ghcr.io/tracemachina/nativelink` and `ghcr.io/buildbarn/bb-storage` images.

### 3.8 Customers — none named

33 `customer` lines in 17 files, all generic ("the customer's own infrastructure", "regulated customers
ask for an HSM", a test store named `customer-store`). The only customer-adjacent specifics are Metis's
positioning in `23-metis-and-zetta.md` (removed with the file). No design partner, pilot or company name
appears anywhere. Other Orama product names (`amaro`, `clustera`, `wtm`): the only hit is the `wtm
ORAMA-ZETTA blueprint` reference at `23-metis-and-zetta.md:128` (removed with the file). `oramacore`
appears as the public OramaCore engine and the `oramacore-cpp` dependency (3.4).

### 3.9 The owner's name — keep

`Steve` appears in 21 lines of 15 files as decision attribution ("(Steve, 2026-09-03)") and as the
source of a design complaint in research READMEs. A first name is not confidential; the decision record
is more honest with it. Optional rephrase to "the project owner" is the owner's call.

### 3.10 What is *not* a confidentiality hit but blocks publishing (found while scrubbing)

- **Four of five liquid submodules are private** (3.4): `corosio`, `automerge-cpp`, `oramacore-cpp`; and
  `.gitmodules` uses `git@github.com:` URLs for all four org submodules, which fail for anonymous clones
  even when the repositories are public. liquify's `.gitmodules:3` pins liquid the same way.
- **No `LICENSE` file** in either repository (`NOTICE` exists in liquid). Bridge issue #2.
- **liquify's submodule pin** (`4a7306e` in the index, a different `4a99324` checked out in the local
  clone) references a commit of the *private* liquid; a public liquify must pin a commit that exists in
  the public liquid (§7.2).
- The CI checkout step depends on `ORAMA_SUBMODULES_TOKEN` (3.5).

## 4. liquid — history

Counts are commits, across **all refs** (`--all`), in which the term's occurrence count changed. Full
lists are in Appendix A.

### 4.1 Content (`git log --all --pickaxe-regex -S`)

| Term | Commits | Files touched | First introduced | On `main`? |
|---|---|---|---|---|
| `[Mm]etis` | 6 | `docs/features/23-metis-and-zetta.md`, `README.md`, `docs/features/README.md`, `18-lake-service.md`, `24-multiplayer-and-agents.md`, `CLAUDE.md` | `9549e52` 2026-09-01 | yes |
| `[Zz]etta` | 23 | `CLAUDE.md` (11 of them), `README.md`, `.gitmodules`, `AGENTS.md`, `CMakeLists.txt`, features 17/18/21/23/24/README, `docs/library/api-map.md`, `libliquid.md`, `transparency.md` (branch only) | `9549e52` | yes |
| `orama-work` | 2 | `CLAUDE.md`, `23-metis-and-zetta.md` | `9549e52`, `2664020` | yes |
| `zetta-bridge` | 1 | `CLAUDE.md` | `2664020` 2026-09-02 | yes |
| `corporate-intelligence` | 2 | `CLAUDE.md`, `23-metis-and-zetta.md` | `9549e52`, `cf93daf` | yes |
| `homer6` | 7 | `CLAUDE.md`, `README.md`, features 01/02/17/23 | `a24dc1a` 2026-09-01 | yes |
| `/Users/` | 3 | `CLAUDE.md` (`2664020`, on `main`); `tests/transparency/README.md` (`e6c72f8`, branch `issue-210-tsa-evidence-verify` only: `LAKE_ROOT=/Users/stevesperandeo/dev/oramasearch/codex-work/lake`); `docs/library/self-host.md` (`ae4dc5d`, local branch `issue-59-self-host` only: worktree paths to a `.dylib`) | — | 1 of 3 |
| `BEGIN … PRIVATE KEY` (real key) | 2 | `tools/reapi-peers/nativelink-tls-key.pem` — `9eea816` adds it, `7fe008e` (PR #161) carries it | `9eea816` 2026-09-04 | yes |
| `oramadev`, IPs, tokens, kubeconfig | 0 | — | — | — |
| `oramasearch/` | 37 | many | `409b806` 2026-09-02 | yes |
| personal email in content | 0 | — | — | — |

Blob-level sweep: 3,250 unique blobs; hits are exactly the items above plus the scanner test vectors
and public mailing-list addresses. The 219 `CLAUDE.md` blob versions containing `homer6`/`orama-work`
show how many revisions carry the map: **every `CLAUDE.md` since `2664020`**.

### 4.2 Commit messages (not visible to `-S`)

Six liquid commits name Zetta in the subject or body, two name Metis:
`f43f74f` "Record Phase 0 decisions: liquid separate from Zetta by licence, lake on Zetta, operator Zetta
state store…", `2664020` "CLAUDE.md: read Zetta and the operator only via orama-bridge", `90204a2`
"CLAUDE.md: lake's control plane is Postgres for now, Zetta the data plane", `42e7bc9` (body: "never
depends on Zetta"), `9f7016b` and `9549e52` "Add documentation … Metis and Zetta…". A rewrite would need
`--message-callback` edits as well as content edits.

### 4.3 Author identity

`Steve Sperandeo <steve.sperandeo@gmail.com>` is author and committer of 299 commits and author of the
87 GitHub-merged commits (`GitHub <noreply@github.com>` committer). **A personal address is therefore in
every commit.** Options are in §7.3.

### 4.4 Deleted files and branches

Only three files were ever deleted on any ref (`src/objects/attestation.cpp`, the `hello` trio); none
sensitive. No `docs/metis/` or `docs/competitors/` copy was ever committed to liquid. 59 remote issue
branches carry commits not on `main`, including `issue-204-secret-seal` (X25519 test vectors),
`issue-210-tsa-evidence-verify` (the `LAKE_ROOT` local path) and `issue-59-self-host` (local path,
local branch only). None of these branches should be published.

## 5. liquify — working tree

| File:line | Content | Class |
|---|---|---|
| `CLAUDE.md:51-54` | "Read Zetta only from the umbrella bridge (`/Users/stevesperandeo/dev/homer6/orama-work/modules/zetta-bridge/modules/zetta`), and only to learn its patterns (`src/gui/app.cpp` for the SDL/ImGui lifecycle). Never copy Zetta source into this repository." | **remove** bullet |
| `CLAUDE.md:31-33` | "**Never depends on Zetta** — Zetta is closed; liquify shares only its *choices* (SDL3 + Dear ImGui) and the same open libraries." | **rephrase** |
| `CLAUDE.md:34` | "Clang 17+ auto-selected the way liquid and Zetta do" | **rephrase** → "the way liquid does" |
| `CLAUDE.md:36-37` | "the stack Zetta's headed mode proves on all three desktop platforms" | **rephrase** → "a stack proven on all three desktop platforms" |
| `CLAUDE.md:69-70` | "Never depend on Zetta or on `oramasearch/lake`. liquify talks to liquid (the daemon), and through liquid to lake." | **rephrase** |
| `CLAUDE.md:71` | "Never make this repository public without the licence decision landed." | **remove** at publication (true until then) |
| `CLAUDE.md:4`, `AGENTS.md:7` | link to private `oramasearch/orama-bridge` | **rephrase** (no URL) |
| `AGENTS.md:16-18` | "Never take a dependency on Zetta or on `oramasearch/lake`…"; master-epic link into private `liquid-bridge` | **rephrase**; **remove** link |
| `CMakeLists.txt:3-4` | "# liquify is C++26 on the same coroutine stack as Zetta (Capy/Corosio/Beast2) … the same pre-project() auto-selection Zetta and liquid use." | **rephrase** |
| `CMakeLists.txt:49-51` | "# Fetched dependencies — the same window/UI stack Zetta's headed mode uses … No Zetta code is used; only its choices." | **rephrase** |
| `README.md:83-85` | "It starts from the window and UI stack Zetta's headed mode already proves on macOS, Windows and Linux (SDL3 + Dear ImGui). No Zetta code is used, only its choices; liquify never depends on Zetta." | **rephrase** |
| `README.md:40`, `.gitmodules:3` | `git@github.com:oramasearch/liquify.git`, `git@github.com:oramasearch/liquid.git` | **rephrase** → HTTPS |
| `README.md:94`, `docs/README.md:4` | links to private `liquid-bridge`; "bridge `CLAUDE.md`" | **rephrase** (no URL) |
| `docs/app-shell/README.md:16` | "**Lifecycle** (mirrors Zetta `src/gui/app.cpp`):" | **remove** the parenthetical |
| `docs/build/ci.md:7-11` | the `ORAMA_SUBMODULES_TOKEN` paragraph ("Steve creates and maintains it") | **keep until liquid is public**, then **rephrase** to "all submodules are public; no token is needed" |
| `CLAUDE.md:28,43`, `docs/app-shell/README.md:11` | "(Steve, 2026-09-02)" attributions | **keep** |

No key material, no emails other than the SSH URLs, no hostnames, no customers, no Metis.

## 6. liquify — history

| Term | Commits | Detail |
|---|---|---|
| `[Zz]etta` | 6 | `4b8ea33` (CLAUDE.md, CMakeLists.txt, README.md, src/app.cpp), `5740429` and `237f2b8` (`docs/app-shell/README.md`), `78ec751` (AGENTS.md), `7e83e48`/`5b6b85e` (src/app.cpp comment, PR #19) |
| `orama-work`, `zetta-bridge`, `homer6`, `/Users/` | 1 | `4b8ea33` 2026-09-02 (CLAUDE.md) — and **every CLAUDE.md revision since** (19 blob versions) |
| `oramasearch/` | 4 | `4b8ea33`, `9a38ee9` (`.gitmodules`), `5740429`, `78ec751` |
| commit messages | 1 | `4b8ea33` body: "as liquid and Zetta do", "stack Zetta's headed mode proves", "never on Zetta" |
| author email | 40/40 | as liquid |
| blob sweep | 182 blobs | clean apart from the above |

In addition, **every liquify commit since `9a38ee9` records a gitlink to a private liquid commit**. Those
SHAs will not exist in a fresh-history public liquid, so every historical liquify checkout would fail
`git submodule update`. That is decisive for §7.2.

## 7. Recommendation on history

### 7.1 Options

| Option | What it is | Removes history hits? | Cost |
|---|---|---|---|
| A. Publish as-is after tree edits | Flip visibility on the existing repository | **No.** Every revision of `23-metis-and-zetta.md`, both `CLAUDE.md` maps, the private key, the local paths and the commit messages become public | Unacceptable |
| B. Rewrite in place (`git filter-repo`) | `--replace-text` for the terms, `--invert-paths` for the PEM and `23-metis-and-zetta.md`, `--mailmap` for the author, `--message-callback` for the six commit messages, over all 141 refs; force-push | Yes, if every term and file is caught | Every SHA changes: liquify's submodule pin, the bridge's pointers, `Refs`/`Fixes` links in 200+ issue comments and PR bodies, the Codex worktrees under `codex-work/wt/liquid/` (14 today), and the `docs/library/*.md` "landed in `a5659bc`"-style citations all break. `--replace-text` produces incoherent old revisions (a document about Zetta with the word blanked). GitHub keeps rewritten objects reachable by SHA (PR refs, forks, caches) until Support purges them — a rewrite on the same repository does not reliably remove content from GitHub. 59 unmerged branches must be rewritten or deleted first. |
| C. **Fresh-history publish** | Create the public repository from the scrubbed tree as one initial commit (tag it; note "development history retained privately"); keep the private repository, renamed, as the archive | **Yes, completely** — nothing from the private era is in the public object store | Loses public `blame`/`bisect` over ~200 commits authored by one person in five days; issue numbers cited in docs (`liquid #21`) point into the private tracker unless issues are migrated or the citations rewritten; the private ecosystem keeps working unchanged because the private SHAs never change |

### 7.2 Recommendation: **C, fresh-history publish, for both repositories.**

The reasons, in order of weight:

1. The leak in history is **whole documents and every revision of them**, not a handful of strings. A
   rewrite cannot make `9549e52..a5659bc` coherent without Metis and Zetta; it can only blank words. A
   fresh start has nothing to blank.
2. **SHA stability for everything private.** The bridge, lake, the operator, liquify's pin, the Codex
   worktrees and every issue thread reference liquid commits by SHA. Option B breaks all of them;
   option C touches none.
3. **liquify's gitlinks.** Its history points at private liquid commits in every revision; a public
   liquify history is broken for `git submodule update` at every commit before the publish (§6).
   Rewriting gitlinks to new SHAs is possible only after liquid's rewrite completes — two coupled
   rewrites for no gain.
4. **GitHub semantics.** Rewriting in place leaves the old objects fetchable by SHA until GitHub Support
   removes them; a new repository never held them.
5. **The public history is not worth much yet.** Pre-1.0, one author, docs churn; a curated initial
   commit plus an honest note is a better first impression than 200 commits of private planning.

Concretely: rename `oramasearch/liquid` → `oramasearch/liquid-private` (keeps every link and clone
working via GitHub's redirect), create `oramasearch/liquid` public from a scrubbed export of `main` at
the publish commit (`git archive` or a clean clone with `.git` removed, after §9 is applied and the
independent scanners in §8 pass), commit as "Initial public release", tag it, and pin liquify to that
commit; same for liquify. Merge future work into the public repository directly; the private one is
frozen as the archive. If the owner prefers to keep issue numbers, GitHub's repository transfer does not
apply here (the tracker would carry private discussion); instead rewrite the `liquid #NN` citations in
docs to link the public tracker's new issues, or accept that they point at the archive.

### 7.3 The author email

With option C the initial commit's author is whatever the owner sets. Suggest an organisation address or
the GitHub noreply form `<id>+<login>@users.noreply.github.com` with "Keep my email addresses private"
enabled, so the personal Gmail never enters the public history. (If option B were chosen, `--mailmap`
does the same at the cost above.) Git author emails are conventionally public and many maintainers use a
personal address; this is a choice, not a leak, but it is free to avoid under option C.

## 8. Sign-off checklist for issue #10

- [ ] Edits in §9 applied to liquid and liquify (by a worker, on branches, PRs as usual).
- [ ] `docs/features/23-metis-and-zetta.md` removed; `docs/features/README.md` count recounted (liquid
      `CLAUDE.md` rule: "Recount, never estimate") and `README.md` feature count updated.
- [ ] Link check (liquid `CLAUDE.md` script) reports zero broken links after the removals.
- [ ] Submodule decision recorded: `corosio`, `automerge-cpp`, `oramacore-cpp` public or replaced;
      `.gitmodules` on HTTPS in both repositories; CI token step removed.
- [ ] `gitleaks detect --log-opts=--all` and `trufflehog git file://.` clean on the export tree; GitHub
      secret scanning and push protection enabled on the new repositories before the first push.
- [ ] Re-run this report's `git grep` battery on the export tree: zero hits for `metis|zetta|orama-work|
      zetta-bridge|corporate-intelligence|oramadev|/Users/|BEGIN .*PRIVATE KEY` (the scanner test file
      excepted).
- [ ] Fresh-history publish executed per §7.2; author identity per §7.3; `LICENSE` (bridge #2) and
      `SECURITY.md` (bridge #11) present in the initial commit.
- [ ] Sign-off recorded on https://github.com/oramasearch/liquid-bridge/issues/10 with the public commit
      SHA.

## 9. Worker edit list (ready to apply; nothing here was applied by this report)

Line numbers refer to liquid `a5659bc` and liquify `e7b47ee`. Where replacement text is given, use it
verbatim or better; where "delete" is given, delete the whole span and fix surrounding punctuation.

### liquid

1. **Delete `docs/features/23-metis-and-zetta.md`.** Then:
   - `docs/features/README.md:97` — delete the row.
   - `README.md:172-189` — replace the "Where this sits" section with:
     ```markdown
     ## Where this sits

     liquid is an **Orama** project. **lake** ([`docs/features/18-lake-service.md`](docs/features/18-lake-service.md))
     is its hosted service and **liquify** ([`docs/features/21-liquify-ide.md`](docs/features/21-liquify-ide.md))
     its IDE; both are clients of libliquid. The action plan and cross-repository decisions are kept in the
     project's planning repository, which is not public.
     ```
   - `docs/features/18-lake-service.md:144-146` — replace "lake runs on the customer's own infrastructure
     (`[13](13-deployment-runtime.md)`) — which is Zetta's stated posture too (`[23](23-metis-and-zetta.md)`) —
     and provenance is exactly the Band B availability dimension Metis's theory identifies as binding."
     with "lake runs on the customer's own infrastructure (`[13](13-deployment-runtime.md)`), and provenance
     is exactly what the self-hosted alternatives lack."
   - `docs/features/24-multiplayer-and-agents.md:227` — delete "That is the same argument as
     `[23](23-metis-and-zetta.md)`, applied to the actors rather than the data."
   - Recount features (`ls docs/features/*.md | grep -v README | wc -l`) and update the count in
     `README.md`; run the link check.
2. **`CLAUDE.md`**
   - `:3-6` — replace the org-bridge sentence with "Org-wide conventions apply in full; the ones most often
     hit in this repo are restated below."
   - `:112` — liquify row: replace the parenthetical with "(its own repository, `oramasearch/liquify`)".
   - `:241-249` — delete the paragraph beginning "**Read Zetta only from the umbrella bridge**".
   - `:251-254` — replace with "This repository's action plan and Phase 0 decisions are kept in the
     project's planning repository (not public); this file records the chosen options."
   - `:256-268` — keep only the rows for `automerge-cpp`, `oramacore-cpp`, `corosio`, `http`, `capy`
     (dependencies), with URLs updated to their public homes; in the `corosio` row delete "Zetta consumes
     it." and the parenthetical "(An earlier claim … stale standalone clone.)"; delete the rows for
     `liquid-bridge`, `lake`, `liquify` (keep liquify only as a plain mention), `orama-operator`, `k0s`,
     `orama-bridge`.
   - `:270-274` — delete "**Copies of public upstreams are never forks.** …" paragraph.
   - `:276-286` — delete the "## Confidentiality" section.
   - `:305-335` Decisions: **1** → "**liquid has its own store and depends on no closed-source
     component.** liquid and liquify are open source; nothing in them may depend on a component that is
     not." **2** → "**lake consumes liquid's store as a library** for repository data; its own control
     plane is its own concern." **3** → delete. **4** → "**One CRDT — `automerge-cpp`** (MIT). Its
     canonical repository is `oramasearch/automerge-cpp`." **5** → delete ", matching Zetta and
     oramacore-cpp" and "(private patch carrier)". **6** → "**Licence posture.** liquid and liquify: open
     source under `LICENSE`. lake: enterprise."
   - `:341` — "must stay free of Zetta and, where feasible, of third-party types" → "must stay free of
     third-party types where feasible".
3. **`AGENTS.md`** — `:7` drop the URL ("…the org conventions:"); `:16` → "Never take a dependency on a
   closed-source component or on lake's private code; this repository is open source."; `:17-18` → "Work
   is tracked as GitHub issues on this repository."
4. **`CMakeLists.txt:4`** → "# modern Clang before the project() call." ; **`:624`** → "# Tests:
   GoogleTest via FetchContent + CTest."
5. **`docs/features/17-implementation.md`** — `:103` delete ", as Zetta and oramacore-cpp already do —
   one async stack across the org" (keep "stdexec is not used."); `:127` delete " — the same code Zetta
   already vendors as a submodule"; `:134` delete " The same stack Zetta and oramacore-cpp use; Zetta
   vendors both."; `:167` delete ", matching Zetta and oramacore-cpp".
6. **`docs/features/21-liquify-ide.md:202-206`** — "(`oramasearch/liquify`, private for now, open source
   eventually, and it never depends on Zetta, the same rule as liquid)" → "(`oramasearch/liquify`)";
   "the stack Zetta's headed mode already proves on macOS, Windows and Linux" → "a stack proven on
   macOS, Windows and Linux".
7. **`docs/library/api-map.md`** — `:11` "keeps Zetta, Boost and the engine choices" → "keeps Boost and
   the engine choices"; `:24` delete "Not Zetta, ever. "; `:28` delete " (Zetta's pattern)".
8. **`docs/library/libliquid.md:25`** — delete "**never a Zetta type**, and ".
9. **Clone URLs** — `README.md:334`, `docs/library/libliquid.md:33`: `git@github.com:oramasearch/liquid.git`
   → `https://github.com/oramasearch/liquid.git`. `.gitmodules:7,11,14,18`: `git@github.com:oramasearch/X.git`
   → `https://github.com/oramasearch/X.git` (after the submodules are public).
10. **Test TLS key** — `git rm tools/reapi-peers/nativelink-tls-key.pem tools/reapi-peers/nativelink-tls-cert.pem`;
    in `tools/reapi-peers/run-tls-interop.sh:17-18` generate into a temporary directory before starting the
    peer: `openssl req -x509 -newkey rsa:2048 -nodes -days 1 -subj /CN=localhost -addext
    "subjectAltName=DNS:localhost,IP:127.0.0.1" -keyout "$tmp/nativelink-tls-key.pem" -out
    "$tmp/nativelink-tls-cert.pem"`, mount `$tmp` at `/certs` (the `nativelink-tls.json5:16-17` paths stay);
    `tools/reapi-peers/README.md:5-6` "with the committed self-signed certificate and private key" → "with a
    self-signed certificate and key generated for the run"; add `tools/reapi-peers/*.pem` to `.gitignore`.
11. **Scanner fixtures** — add `.gitleaksignore` entries (or `# gitleaks:allow`) for
    `tests/scan/test_detectors.cpp:57,63,65` and `src/scan/detectors.cpp:160`.
12. **CI token** — once submodules are public: delete `token:` lines `.github/workflows/ci.yml:29,120`;
    rewrite `docs/build/ci.md:5,53` and `docs/library/simulation.md:60` to drop `ORAMA_SUBMODULES_TOKEN`.
13. **`NOTICE`** — update the `corosio`, `http`, `automerge-cpp` project URLs to wherever they are public.

### liquify

1. **`CLAUDE.md`** — `:4` drop the org-bridge URL; `:31-33` → "**Open source, like liquid**, under the
   same licence. liquify depends on no closed-source component; it shares only its UI stack choices
   (SDL3 + Dear ImGui) and the same open libraries with other Orama products."; `:34` "the way liquid and
   Zetta do" → "the way liquid does"; `:36-37` "the stack Zetta's headed mode proves on all three desktop
   platforms" → "a stack proven on all three desktop platforms"; `:51-54` delete the bullet; `:69-70` →
   "Never depend on lake's private code. liquify talks to liquid (the daemon), and through liquid to
   lake."; `:71` delete at publication.
2. **`AGENTS.md`** — as liquid items `:7`, `:16-18`.
3. **`CMakeLists.txt:3-4`** → "# liquify is C++26 on the same coroutine stack as liquid (Capy/Corosio),
   which needs Clang 17+ — the same pre-project() auto-selection liquid uses."; **`:49-51`** → "# Fetched
   dependencies — SDL3 static + Dear ImGui with the SDL_Renderer backend, a proven cross-platform base."
4. **`README.md:83-85`** → "It is built on SDL3 + Dear ImGui, a window and UI stack proven on macOS,
   Windows and Linux."; `:40` SSH → HTTPS; `:94` "See the project's planning repository (not public) for
   the cross-module map and the action plan." (or delete the section).
5. **`docs/README.md:4`** — drop "(bridge `CLAUDE.md`)".
6. **`docs/app-shell/README.md:16`** — "**Lifecycle** (mirrors Zetta `src/gui/app.cpp`):" → "**Lifecycle:**".
7. **`.gitmodules:3`** — HTTPS URL to the public liquid; bump the pin to the public initial commit.
8. **`docs/build/ci.md:7-11`** and `.github/workflows/ci.yml:31` — once liquid is public, remove the token
   and rewrite the paragraph.

## Appendix A — history commit lists (liquid, all refs)

`-S'[Mm]etis'` (6): `f43f74f` 2026-09-02 Record Phase 0 decisions… (CLAUDE.md) · `cf93daf` 2026-09-01
Clarify identity and trust boundaries… (CLAUDE.md) · `60e300b` 2026-09-01 Add new topic on multiplayer…
(24) · `7d031eb` 2026-09-01 Enhance documentation for models and datasets… (18) · `9f7016b` 2026-09-01 Add
documentation on liquid's relationship with Metis and Zetta… (README.md) · `9549e52` 2026-09-01 Add
documentation for Metis and Zetta… (23, features/README).

`-S'[Zz]etta'` (23): `a93b2cf` Document TSA verification decision (branch) · `08aa677`/`77b0a31` Add
repository sync primitives and client (.gitmodules) · `b66004d` docs: libliquid is coroutine-native ·
`bb60847` docs: the libliquid API map · `7053ae5` docs: AGENTS.md · `6c4deee` docs/library: libliquid ·
`99bdbb9` libliquid: the library is the product · `42e7bc9` liquify is a native IDE · `400b718` Correct
corosio-drift claim · `2664020` CLAUDE.md: read Zetta… · `a55e372` Hello world (CMakeLists.txt) · `28ec299`
lake is a Lake CR on orama-operator · `f43f74f` Record Phase 0 decisions · `7d8db04` corosio and capy as
private patch carriers · `13e96f4`, `3436732`, `0c9e9c5` Clarify … (17-implementation, CLAUDE.md) ·
`cf93daf`, `60e300b`, `7d031eb`, `9f7016b`, `9549e52` (as above).

`-S'orama-work'` (2): `2664020`, `9549e52`. `-S'zetta-bridge'` (1): `2664020`.
`-S'corporate-intelligence'` (2): `cf93daf`, `9549e52`. `-S'homer6'` (7): `1facbff`, `2664020`, `13e96f4`,
`409b806`, `9f7016b`, `9549e52`, `a24dc1a`. `-S'/Users/'` (3): `e6c72f8` (branch), `ae4dc5d` (local
branch), `2664020`. `-S'BEGIN [A-Z ]*PRIVATE KEY'` (3): `7fe008e`, `9eea816` (the key), `7633b9d` (the
scanner). `-S'oramasearch/'` (37), `-S'Steve'` (12), `-S'[Cc]ustomer'` (13), `-S'[Aa]zure'` (6),
`-S'[Cc]loudflare'` (2), `-S'orama-operator'` (4): counted; all classified keep or covered above.

## Appendix B — history commit lists (liquify, all refs)

`-S'[Zz]etta'` (6): `5b6b85e`/`7e83e48` Add retained GPU editor surface (src/app.cpp) · `237f2b8` render a
liquid repository root tree (docs/app-shell) · `78ec751` AGENTS.md · `5740429` docs/app-shell · `4b8ea33`
Hello world (CLAUDE.md, CMakeLists.txt, README.md, src/app.cpp). `-S'orama-work'`, `-S'homer6'`,
`-S'/Users/'` (1 each): `4b8ea33`. `-S'oramasearch/'` (4): `78ec751`, `5740429`, `9a38ee9`, `4b8ea33`.
`-S'Steve'` (5): `5b6b85e`, `34c8704`, `17d726b`, `5740429`, `4b8ea33`.
