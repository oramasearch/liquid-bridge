#!/usr/bin/env python3
"""Build out the master epic for the liquid project.

1. Creates the gap issues (deliverables the feature docs specify that no issue covers).
2. Creates the missing repository epics (operator Lake CR, liquify, open-source release, lake.live).
3. Regenerates every phase epic's issue lists from live labels (keeps each epic's exit text).
4. Rewrites liquid-bridge #7 as the master epic that links every epic.
Idempotent: an existing issue with the same title in the same repo is reused. Output: master-epic.tsv.
"""
import json, os, subprocess, sys, time

ORG = "oramasearch"
DOCS = "https://github.com/oramasearch/liquid/blob/main/docs"
BRIDGE = "https://github.com/oramasearch/liquid-bridge/blob/main/docs"
PLAN, DECISIONS, TRACKING = f"{BRIDGE}/action-plan.md", f"{BRIDGE}/decisions.md", f"{BRIDGE}/tracking.md"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "master-epic.tsv")
MASTER = "https://github.com/oramasearch/liquid-bridge/issues/7"

FEATURES = {1:"01-object-model-and-storage.md",2:"02-version-control.md",3:"03-diff-and-merge.md",
 4:"04-build-engine.md",5:"05-caching.md",6:"06-distributed-execution.md",7:"07-dependency-resolution.md",
 8:"08-packaging-and-images.md",9:"09-artifact-service.md",10:"10-supply-chain.md",11:"11-secrets-and-encryption.md",
 12:"12-search.md",13:"13-deployment-runtime.md",14:"14-hot-update.md",15:"15-consumer-sync-and-web.md",
 16:"16-universality.md",17:"17-implementation.md",18:"18-lake-service.md",19:"19-identity.md",
 20:"20-secrets-service-and-pki.md",21:"21-liquify-ide.md",22:"22-change-capture.md",23:"23-metis-and-zetta.md",
 24:"24-multiplayer-and-agents.md",25:"25-identity-attestation-and-transparency.md"}
RESEARCH = {1:"01-version-control",2:"02-large-files-and-binary-assets",3:"03-structural-diff-and-formats",
 4:"04-build-systems",5:"05-autotools-and-configure-era",6:"06-build-and-compiler-caching",7:"07-distributed-execution",
 8:"08-incremental-compilation",9:"09-package-managers",10:"10-os-packaging",11:"11-container-images",
 12:"12-artifact-distribution",13:"13-supply-chain-security",14:"14-secrets-and-encryption",15:"15-binary-introspection",
 16:"16-monorepo-scale-and-authoring-loop",17:"17-runtime-hot-update",18:"18-implementation-cpp26",19:"19-full-text-search",
 20:"20-deployment-runtime-k8s",21:"21-consumer-sync-and-web",22:"22-forges-and-code-hosting",23:"23-secrets-service-and-pki",
 24:"24-editors-and-ide-architecture",25:"25-multiplayer-and-agent-collaboration",26:"26-transparency-logs-and-anchoring"}
PHASES = {"0":"Phase 0 — Decide","1":"Phase 1 — The store","2":"Phase 2 — The build core","3":"Phase 3 — Distribution",
 "4":"Phase 4 — The incremental engine","5":"Phase 5 — Resolution and projection","6":"Phase 6 — lake",
 "7":"Phase 7 — The runtime","8":"Phase 8 — The rest","x":"Cross-phase"}

def feat(ns): return ", ".join(f"[features/{FEATURES[n]}]({DOCS}/features/{FEATURES[n]})" for n in ns)
def res(ns): return ", ".join(f"[research/{RESEARCH[n]}]({DOCS}/research/{RESEARCH[n]}/)" for n in ns)
def header(phase, feats=(), researches=(), extra=""):
    line = f"**{phase}** · plan: [action-plan.md]({PLAN})"
    if feats: line += f" · spec: {feat(feats)}"
    if researches: line += f" · research: {res(researches)}"
    if extra: line += f" · {extra}"
    return line + "\n\n"
def done(items): return "\n## Done when\n\n" + "\n".join(f"- [ ] {i}" for i in items) + "\n"

def sh(*args, check=True, inp=None):
    r = subprocess.run(args, capture_output=True, text=True, input=inp)
    if check and r.returncode != 0:
        raise RuntimeError(f"{' '.join(args[:5])}...: {r.stderr.strip()}")
    return r.stdout.strip()

LABEL_COLOURS = {"epic":"5319e7","decision":"b60205","ops":"0e8a16","lake":"1d76db","documentation":"0075ca",
 **{f"phase-{i}": "c5def5" for i in range(9)}}
HAVE = {}
def ensure_labels(repo, names):
    if repo not in HAVE:
        HAVE[repo] = {l["name"] for l in json.loads(sh("gh","label","list","--repo",f"{ORG}/{repo}","--limit","100","--json","name"))}
    have = HAVE[repo]
    for n in names:
        if n not in have:
            sh("gh","label","create",n,"--repo",f"{ORG}/{repo}","--color",LABEL_COLOURS.get(n,"ededed"),"--force")
            have.add(n)

def all_issues(repo):
    rows = json.loads(sh("gh","issue","list","--repo",f"{ORG}/{repo}","--state","all","--limit","500",
                         "--json","number,title,url,state,labels,body"))
    for r in rows: r["labels"] = [l["name"] for l in r["labels"]]
    return rows

REPOS = ["liquid-bridge","liquid","lake","liquify","k0s","orama-operator"]
ISSUES = {r: all_issues(r) for r in REPOS}
BY_TITLE = {r: {i["title"]: i for i in ISSUES[r]} for r in REPOS}
created = []  # (repo, status, url, title)

def create(repo, title, body, labels):
    if title in BY_TITLE[repo]:
        i = BY_TITLE[repo][title]; created.append((repo,"existing",i["url"],title)); return i
    ensure_labels(repo, labels)
    url = sh("gh","issue","create","--repo",f"{ORG}/{repo}","--title",title,"--body",body,"--label",",".join(labels))
    num = int(url.rstrip("/").rsplit("/",1)[1]); time.sleep(1)
    i = {"number":num,"title":title,"url":url,"state":"OPEN","labels":labels,"body":body}
    ISSUES[repo].append(i); BY_TITLE[repo][title] = i; created.append((repo,"created",url,title))
    print(f"  + {repo}#{num} {title}", flush=True)
    return i

def edit(repo, number, body=None, title=None):
    args = ["gh","issue","edit",str(number),"--repo",f"{ORG}/{repo}"]
    if body is not None: args += ["--body-file","-"]
    if title is not None: args += ["--title",title]
    sh(*args, inp=body)
    for i in ISSUES[repo]:
        if i["number"] == number:
            if body is not None: i["body"] = body
            if title is not None: i["title"] = title

# ----------------------------------------------------------------------------------------------
# Gap issues. (repo, title, labels, phase-key, feature docs, research dirs, body, done-when, group)
# ----------------------------------------------------------------------------------------------
NEW = []
def add(repo, title, labels, phase, feats, researches, body, dones, group=None):
    NEW.append((repo, title, labels, phase, feats, researches, body, dones, group))

L, K, F, S, OP, BR = "liquid", "lake", "liquify", "k0s", "orama-operator", "liquid-bridge"

# ---------------- liquid, Phase 1 — the store ----------------
add(L, "Conflicts as first-class committable values: record, push and resolve a conflict later", ["phase-1"], "1", (2,3,24), (1,3),
 "A conflict is a committable state, not a broken working directory. When a merge — textual, structural, or the CRDT's "
 "converged-but-suspicious result — needs attention, liquid records the conflict as a value in the change graph, lets it be "
 "pushed and shared, and resolves it in a later change. Nothing is lost while a conflict stands, and \"no conflict\" is never "
 "allowed to mean \"no attention required\".",
 ["A conflict value in the object model holding both sides, the base and the region; `liquid status` shows it; a repository with an unresolved conflict can be pushed, cloned and built where the conflict does not intersect the target.",
  "Resolution is an ordinary change that references the conflict it resolves.",
  "Structural merge (Phase 5) and multiplayer (Phase 8) produce conflict values through this one path."])
add(L, "`liquid undo`: the operation log, time travel, and selective or session-scoped reversal", ["phase-1"], "1", (2,24), (1,25),
 "Every mutation of the local store is recorded in the operation log and any prior state is readable (`get_at`). `liquid undo` "
 "reverses any operation, not only the last, and reverses the user's own intent rather than the most recent remote operation. "
 "An agent's whole session is an addressable range that can be reversed atomically or selectively by file or by drip.",
 ["`liquid undo` reverses a drip, a merge, a rebase-equivalent and a lock by operation id; `liquid log --ops` lists the log.",
  "Undo of a local operation never reverts a concurrently arrived remote one (two-replica test).",
  "A session range (Phase 8 agents) reverts atomically or per file."])
add(L, "Exclusive checkout: `liquid lock` / `liquid unlock` with declared path patterns and lock authority", ["phase-1"], "1", (2,24), (1,2),
 "Unmergeable binary assets need the Perforce model: locks declared per path pattern in repository configuration, visible to "
 "everyone, refused on write. The open question is lock authority — the likely answer is advisory offline and authoritative when "
 "connected to lake, and it needs specifying here. Without locks liquid is unusable for art and hardware teams.",
 ["Path-pattern lock rules in repository configuration; `liquid lock <path>` / `unlock`; a write to a path locked by someone else is refused with the holder named.",
  "Authority model written down (offline advisory, connected authoritative) and enforced by lake in Phase 6.",
  "Locks appear in the daemon's fan-out so editors show them."])
add(L, "Git interoperability: `liquid import git`, `liquid export git`, and a Git remote for teams mid-migration", ["phase-1"], "1", (2,18), (1,22),
 "The lossless on-ramp: import a Git repository with full history and a preserved commit-identity mapping; export degrades nested "
 "repositories and change identity to subtrees and ordinary commits, and says so; serve as a Git remote so a team can move one "
 "person at a time. jj's Git backend is the reason anyone tried Jujutsu.",
 ["Import → export of a large public repository preserves every commit id and tree.",
  "`liquid export git` reports exactly what was degraded.",
  "`git clone` and `git push` against a liquid repository over the Git protocol work for a mid-migration team (the hosted side is Phase 6)."])
add(L, "Hash and signature agility: an algorithm identifier in every reference, pluggable schemes with ML-DSA in view", ["phase-1"], "1", (1,10), (13,),
 "BLAKE3 today, SHA-256 where ecosystems demand it, and an identifier in every reference so a future migration is a rollout rather "
 "than a decade. Signatures likewise: Ed25519 now, ML-DSA planned. Git's still-incomplete SHA-1 → SHA-256 migration is the "
 "cautionary tale; this is designed in before the first pack is written.",
 ["Every object, chunk and pack reference carries its algorithm tag; one repository can hold two hash algorithms side by side.",
  "A test rehashes a repository under a second algorithm and verifies both reference forms resolve.",
  "The signature scheme is a tagged field on every drip and attestation."])
add(L, "Benchmark RocksDB against LMDB for the chunk index and record the decision", ["phase-1","decision"], "1", (1,17), (2,18),
 "The billion-entry chunk index is either an LSM (write amplification, compaction) or a B+tree over mmap (simplicity, read speed). "
 "The choice is made by measurement against a realistic chunk population, not preference, and recorded in liquid `CLAUDE.md` *Decisions*.",
 ["A reproducible benchmark (insert, point lookup, range scan, cold start) at 10^8 entries on Linux and macOS, results in `docs/library/`.",
  "Decision recorded with the numbers; the index sits behind libliquid's store interface either way."])
add(L, "Pack compaction: reclaim dead chunks after collection", ["phase-1"], "1", (1,), (2,),
 "Packs accumulate dead chunks as history is collected. Compaction rewrites packs to drop them — a write-amplification versus "
 "space trade-off that GC (#8) leaves undecided. Policy and mechanism belong here: when to compact, and how to keep range-fetch "
 "offsets valid for clients holding old pack ids.",
 ["Compaction reclaims space after GC without invalidating live range fetches (old pack ids redirect or stay readable until unreferenced).",
  "A configurable threshold; `liquid gc --compact` and the daemon's background policy."])
add(L, "Symbol-level artifact identity: the object model can say \"this build supersedes that one at these symbols, with this ABI delta\"", ["phase-1"], "1", (14,7), (15,17),
 "Hot update (Phase 8) is impossible later if artifacts are opaque blobs. The object model keeps symbol-level identity for built "
 "artifacts from the start: which symbols an artifact defines, which a new build changes, and the ABI delta between them, so a "
 "hot-patched process is describable as \"artifact X plus patches Y and Z\". This issue is the design-in; extraction is #27.",
 ["Artifact nodes carry a symbol-table reference and a `supersedes` relation with an ABI delta.",
  "A unit test builds one library twice and queries the changed symbols."])
add(L, "`liquid pause`: capture is not publication, drips stay local until pushed", ["phase-1"], "1", (22,), (1,),
 "Auto-drip captures every save; nothing leaves the machine until a push. `liquid pause` stops capture for a workspace with the "
 "state visible in `status`, the daemon and the editor — never silent. Resume replays the journal from the cursor, so nothing "
 "written while paused is lost from history, only from the drip stream.",
 ["`liquid pause` / `resume` per workspace; `status` shows the paused state and how many writes are pending.",
  "Resume produces the coalesced drips for the paused interval.",
  "Push is the only operation that transmits drips; a test asserts no network traffic during capture."])
add(L, "Drip capture budget: single-digit milliseconds on the save path, signatures batched off the critical path", ["phase-1"], "1", (22,25), (1,),
 "The journal append is the only synchronous step on save. Signing sits on the save path with a single-digit-millisecond budget; "
 "batching signatures across coalesced drips is the likely answer and is unspecified. Decide and measure.",
 ["A benchmark of save → journal append → drip visible, p99 under 10 ms on a 100k-file repository on all three platforms.",
  "Signature batching design recorded; a batched signature verifies each drip independently.",
  "The overflow and cursor telemetry from #5 shows when the budget is missed."])
add(L, "Secret scanning inline on the drip path: block by default, redact for real", ["phase-1"], "1", (11,22,25), (14,),
 "The single riskiest consequence of auto-drip: a secret written to disk is captured. Scanning runs inline on the drip path, not "
 "at commit time; it blocks the drip by default; and redaction genuinely removes the content from drip history rather than adding "
 "a follow-up drip that leaves the secret in the log. Emits a `scan_result/1` attestation.",
 ["Detectors for the common secret shapes with a per-repository allow-list; a hit blocks the drip and names the path and pattern.",
  "Redacting a drip that already held a secret removes it from every replica the redaction reaches (Phase 6 for lake's copy).",
  "`scan_result/1` attached to each scanned drip."])
add(L, "Pluggable key custody for the KEK: cloud KMS, Vault Transit, age/X25519, TPM sealing, Shamir threshold shares", ["phase-1"], "1", (11,19,20), (14,),
 "Envelope encryption (#7) wraps a data key with a key-encryption key. Where the KEK lives is pluggable: a cloud KMS, lake's "
 "transit endpoint, an `age`-style X25519 identity, a TPM-sealed key, or Shamir shares for a quorum. Rotating the KEK rewraps a "
 "small key instead of re-encrypting gigabytes. Both halves of \"password protected or key protected\" come from this table.",
 ["A custody interface in libliquid with the age and passphrase providers implemented; KMS, Vault and TPM providers as separate, testable modules.",
  "KEK rotation rewraps without touching chunks; a test proves the ciphertext is unchanged.",
  "The custody matrix documented under `docs/`."])
add(L, "Structured encryption of configuration leaf values (YAML, JSON, TOML, .env): the SOPS model", ["phase-1"], "1", (11,), (14,),
 "Whole-file encryption destroys every collaboration property; it is the fallback. The default for configuration formats is "
 "leaf-value encryption with keys and structure in the clear, selected by `encrypted_regex`-style rules, so diffs, reviews and "
 "merges keep working.",
 ["Rules in repository configuration; encrypted leaves round-trip through the format codecs with structure preserved.",
  "A structural diff of two encrypted configuration versions shows which keys changed without decrypting values."])
add(L, "`liquid rotate`, and honest reporting of what rotation and revocation do and do not do", ["phase-1"], "1", (11,), (14,),
 "Rotation rewraps keys and re-keys future writes; it cannot recall what a revoked collaborator already has, and metadata stays "
 "visible. `liquid rotate` reports which revisions remain readable under which keys. The final encrypted manifest is signed so "
 "`ocicrypt` layers verify.",
 ["`liquid rotate` with a report per revision range; `liquid keys` shows who can read what.",
  "Docs state the limits plainly: past access is not recalled; names and sizes are visible.",
  "Signed encrypted manifests accepted by `ocicrypt`."])
add(L, "Offline correctness is an axiom: full function against the local store, proven by a test that cuts the network", ["phase-1"], "1", (6,18,25), (1,),
 "Everything works offline against the local store, more slowly. This is an axiom, not a fallback: lake is an accelerator and a "
 "meeting point, never a requirement. Proven, not promised.",
 ["A CI job runs the full CLI test suite with networking disabled.",
  "Every command that needs the network says so before doing anything, and only push, pull, remote execution and the remote cache are on that list."])
add(L, "Deterministic seeded simulation harness for the store, sync and reconciliation state machines", ["phase-1"], "1", (15,17), (21,18),
 "Run the reconciliation and sync state machines deterministically so a simulator can explore the state space reproducibly — "
 "Nucleus's real lesson. For a system holding people's files this matters more than throughput. One harness, reused by the "
 "drive's three-tree reconciler (Phase 6).",
 ["A seeded simulator drives the store and sync layer through randomised interleavings with crash injection; any failure reproduces from its seed.",
  "Runs in CI on every change; the seed of any failure is printed."])

# ---------------- liquid, Phase 2 — the build core ----------------
add(L, "Cached configure fact base: `AC_CHECK_*` results keyed by toolchain, sysroot and target", ["phase-2"], "2", (4,16), (5,),
 "Configure-time probing is replaced by a fact base computed once and shared globally rather than re-probed per project: "
 "`./configure` in milliseconds. It also fixes cross-compilation, because the fact base for a target is looked up rather than executed.",
 ["`liquid wrap` of an Autotools project answers its checks from the fact base on a second machine with no probe execution.",
  "Facts are content-addressed by (toolchain, sysroot, target) and shared through the remote cache.",
  "A probe with no cached fact runs once and is recorded."])
add(L, "Build observability: critical-path analysis and time attribution across analysis, execution, I/O and transfer", ["phase-2"], "2", (4,5), (4,6),
 "Beside cache-miss explanation (#15): which actions dominate the critical path, where the time goes (graph analysis, execution, "
 "I/O, transfer), and bytes transferred versus bytes avoided. Reported by the tool and queryable from the graph.",
 ["`liquid build --profile` writes a trace the daemon can serve; `liquid why-slow <target>` names the critical path.",
  "Bytes avoided by the cache are reported per build."])
add(L, "Cost-aware cache eviction and user-expressible retention with computed reachability", ["phase-2"], "2", (5,9), (6,12),
 "Eviction accounts for recomputation cost, not just recency: an artifact that took forty minutes to build should outlive one "
 "that took forty milliseconds. Retention is expressed by the user — keep every release tag forever, CI artifacts thirty days, "
 "anything referenced by a retained artifact — and liquid computes reachability.",
 ["Retention rules in configuration; the cache reports what a rule retains and why.",
  "Eviction order proven by a test with mixed-cost entries."])
add(L, "Self-host: liquid builds liquid", ["phase-2"], "2", (17,), (18,),
 "As soon as liquid can build C++ well, liquid builds liquid. It is the proof, the test suite and the forcing function at once.",
 ["`liquid build` produces the `liquid` binary and libliquid from a clean clone on Linux and macOS with correct caching across two machines.",
  "CI builds liquid with liquid and compares the outputs against the CMake build."])
add(L, "Input-verification policy: an action can require acceptable provenance on its inputs and refuse to build", ["phase-2"], "2", (10,25), (13,),
 "\"Every dependency must have provenance from an approved builder\", \"no artifact without a reproducibility attestation from "
 "two independent builders\" — enforced at build time, not discovered in an audit six months later. The policy language itself is "
 "the open question; keep it small and key it off attestation profiles.",
 ["A policy file per repository; an action whose inputs fail policy does not run and names the input and the rule.",
  "Policies reference profiles from the attestation registry."])
add(L, "SBOM generation from the build graph, with inferred SBOMs from binary composition analysis labelled distinctly", ["phase-2"], "2", (10,25), (13,15),
 "SBOMs come from the build graph, complete and correct by construction (`sbom/1`). For foreign artifacts liquid falls back to "
 "binary composition analysis and labels the difference clearly.",
 ["SPDX and CycloneDX output for any built target, derived from the graph, with a `sbom/1` attestation attached.",
  "Inferred SBOMs carry an `inferred` marker that verifiers can key policy on."])
add(L, "Attestation profile registry and profile-keyed verification policy", ["phase-2"], "2", (25,10), (26,13),
 "Profiles `org_membership/1`, `delegation/1`, `authorship/1`, `review_approval/1`, `slsa_provenance/1`, `sbom/1`, "
 "`model_provenance/1`, `abi_compatibility/1`, `scan_result/1`, `reproducibility/1`. Verifiers key policy off the profile rather "
 "than guessing, with `status_policy` freshness and `attribute_disclosure_commitments` for selective disclosure.",
 ["The registry in libliquid with a schema per profile; an unknown profile is rejected by verification, not ignored.",
  "Each profile documented under `docs/` with its verification rules."])

# ---------------- liquid, Phase 3 — distribution ----------------
add(L, "liquid's own remote-execution scheduler and worker fleet, with the CAS co-located and idempotent requeue", ["phase-3"], "3", (6,), (7,),
 "REAPI compatibility comes first (#16); liquid also ships its own scheduler and workers because owning them enables things REAPI "
 "does not express. The CAS is co-located with the workers; requeue is idempotent, because REAPI does not guarantee exactly-once execution.",
 ["A worker binary and a scheduler; a Phase 2 build runs against them with results identical to local.",
  "Killing a worker mid-action requeues once and the output is identical.",
  "Deployable through the operator (Phase 6)."])
add(L, "Delta encoding for distribution: `zstd --patch-from` and executable-aware deltas for releases and OTA updates", ["phase-3"], "3", (9,8), (12,),
 "Content-defined chunking is the baseline; delta encoding is an optimisation layered on top for the generate-once/apply-many "
 "cases — published releases and OTA-style updates — with executable-aware delta reserved for binaries.",
 ["A release update fetches a delta when one exists and falls back to chunks otherwise; measured savings recorded in docs.",
  "Deltas are attested like any other artifact."])

# ---------------- liquid, Phase 4 — the incremental engine ----------------
add(L, "Per-definition build granularity and compiler-frontend integration (Tier 3), C and C++ first", ["phase-4"], "4", (4,12,16), (8,),
 "Per translation unit today; per definition where the language and frontend permit — the Unison insight — using tree-sitter and "
 "compiler frontends to extract the units. Tier 3 is fine-grained incrementality: per-definition rebuild, compile-as-you-type, "
 "hot-update classification.",
 ["A change inside one function body re-runs only that definition's actions for a Clang-fronted C++ target.",
  "The frontend integration is a separate, replaceable module behind libliquid."])
add(L, "Compiler-derived symbols (SCIP-equivalent) as a byproduct of building, with tree-sitter syntactic fallback", ["phase-4"], "4", (12,21), (19,24),
 "Precise definitions and references are a byproduct of building, not a separate CI indexing job — fresh on every build rather "
 "than as stale as the last nightly index. Where no frontend exists, tree-sitter gives syntactic symbols and says so.",
 ["Go-to-definition and find-references answered from the graph for a built C++ target; the same query returns syntactic results for an unbuilt language and labels them.",
  "Symbols publish to the local search index (#22) and to lake (Phase 6)."])
add(L, "Cost-based query planner over BM25F, the trigram index and brute-force scan", ["phase-4"], "4", (12,17), (19,),
 "Two engines plus a scan fallback, chosen by cost: ripgrep-class scanning is genuinely fastest below a threshold, with no ingest "
 "delay and no staleness.",
 ["The planner picks scan for small working sets and the index for large ones; a test asserts the choice and the identical result set.",
  "Explain output names the plan."])

# ---------------- liquid, Phase 5 — resolution and projection ----------------
add(L, "Structural diff for source over tree-sitter syntax trees, with text fallback", ["phase-5"], "5", (3,4,12), (3,),
 "Reindentation and brace movement produce empty diffs; moving a function is a move. One parse serves diff, incremental "
 "compilation and symbol search.",
 ["`liquid diff` shows a moved function as a move and a reformat as empty for the Tier 2 languages; text diff where no grammar exists, labelled.",
  "The parse is the graph's, not a second one."])
add(L, "Structural merge over the CRDT result, surfacing converged-but-suspicious regions as conflict values", ["phase-5"], "5", (3,17,24), (3,25),
 "The CRDT guarantees no data is lost; structural merge decides whether the converged result is meaningful, and raises the result "
 "for review as a conflict value (the Phase 1 issue) when it is not. Defences 1 and 2 against agent-induced semantic inconsistency.",
 ["Two edits that converge to a syntactically broken function raise a conflict value rather than a silent merge.",
  "Merge quality measured on a corpus of real merges, results in docs."])
add(L, "Second-wave format codecs: ELF/Mach-O/PE, PDF, Jupyter, OOXML/ODF, .deb/.rpm/.apk/wheels, safetensors/pickle", ["phase-5"], "5", (3,8,12,18), (3,15),
 "Binaries by sections, symbols, relocations and disassembly so an address shift is not a total rewrite; OS packages as files plus "
 "metadata; notebooks with outputs elided and execution counts normalised; model files decomposed so \"does this checkpoint "
 "deserialise code?\" is answerable mechanically.",
 ["Each codec declares its fidelity tier and passes the registry's round-trip suite.",
  "Search inside artifacts (lake) and diff reuse the decomposition."])
add(L, "Publish declared support tiers per language and per format, reported by the tool", ["phase-5"], "5", (16,3), (3,),
 "Tiers 0–3 per language and fidelity tiers 1–3 per format are documented rather than implied; the user is told which tier they "
 "are getting, never left to infer it from behaviour.",
 ["`liquid tiers` prints the matrix; the docs table is generated from the same data.",
  "Every command that degrades by tier says so in its output."])
add(L, "tree-sitter grammar distribution for Tier 2 (~50 languages): in-tree or fetched, decided as a supply-chain question", ["phase-5","decision"], "5", (16,3), (3,13),
 "Whether grammars ship in-tree or are fetched is a supply-chain question as much as a distribution one: fetched grammars are "
 "code that runs in the parser.",
 ["Decision recorded; grammars pinned by digest either way and covered by provenance.",
  "Adding a grammar is a documented, attested step."])
add(L, "Relocation by construction: position-independent artifacts or a fixed content-addressed store path, decided before building", ["phase-5","decision"], "5", (7,), (9,),
 "Spack's RPATH rewriting is fragile — embedded paths survive in scripts, `.pc` files and hard-coded strings. liquid decides "
 "relocation before building rather than repairing after.",
 ["Decision recorded; a built package installs to a second prefix and runs without rewriting.",
  "A test greps outputs for the build prefix and fails on any hit."])
add(L, "The configuration language: small, typed, declarative, with real error messages and an ordinary-program escape hatch", ["phase-5"], "5", (7,4), (9,4),
 "Not a new lazy functional DSL — the Nix language is the most-cited reason people bounce off Nix. Typed, declarative, good "
 "errors; the escape hatch is an ordinary program rather than a language feature.",
 ["Grammar and type rules documented; a package and a build target are expressible; error messages name the line and the expected type.",
  "Escape hatch: a program that emits the declarative form, attested like any action."])
add(L, "Seed the package repository by importing from Spack, nixpkgs or conda-forge", ["phase-5"], "5", (7,), (9,),
 "A resolver with nothing to resolve is useless. Import an existing package universe as the bootstrap, translating recipes into "
 "liquid's configuration language and recording what did not translate.",
 ["500 packages imported and resolvable with variants; the import report lists the losses.",
  "Imported packages build under liquid on Linux."])
add(L, "Windows and macOS installers with platform signing: MSI/MSIX/winget with Authenticode, pkg/dmg with codesigning and notarisation", ["phase-5"], "5", (8,), (10,),
 "Notarisation is a hard gate, not polish. The open question is signing-key custody per platform — Authenticode and notarisation "
 "have incompatible trust models — which lands on the key-custody work.",
 ["A projected `.pkg`/`.dmg` passes notarisation and an `.msix` installs on a clean Windows machine with a valid signature.",
  "Key custody per platform documented; keys never in the repository."])
add(L, "Homebrew formulae and bottles, Arch PKGBUILD, Flatpak, Snap and AppImage projections", ["phase-5"], "5", (8,), (10,),
 "Tier A targets beyond the OS package formats: formulae and bottles with relocation for Homebrew; PKGBUILD; the bundled-runtime "
 "desktop formats for Linux.",
 ["One build projects to a bottle that `brew install`s, a PKGBUILD that `makepkg`s, and an AppImage that runs on two distributions.",
  "Digests pinned and attestations attached, as for #28."])
add(L, "ostree / bootc commit projection: the image-based OS target", ["phase-5"], "5", (8,13), (10,20),
 "The node OS runs a signed image identified by hash — exactly liquid's worldview — and liquid produces and signs that image "
 "itself. The closest fit to liquid's model, and the input to the immutable node model (k0s, Phase 7).",
 ["A build projects to a bootable ostree commit / bootc image with a pinned digest and attestation.",
  "k0s's immutable node boots it (Phase 7)."])
add(L, "Tier B: distro-policy-compliant source packages (`.dsc`, `debian/rules`, spec files)", ["phase-5","decision"], "5", (8,), (10,),
 "Lintian-clean, policy-conformant source packages a Debian maintainer would sponsor. Whether to emit source packages at all is "
 "open; decide, then do it properly or not at all.",
 ["Decision recorded; if yes, a source package builds in `sbuild` lintian-clean."])
add(L, "Install-time semantics: maintainer scripts generated from declarative intent, file-conflict detection, transactional upgrade with rollback", ["phase-5"], "5", (8,), (10,),
 "`preinst`/`postinst`/`prerm`/`postrm` are the top source of packaging bugs and an install-time arbitrary-code-execution vector; "
 "liquid generates them from intent — register a service, update a cache, create a user — and never passes through user shell. "
 "File conflicts between packages claiming a path are detected at projection; upgrades are transactional with rollback.",
 ["Generated scripts for the three package formats from one intent declaration; no user shell reaches a script.",
  "Two packages claiming one path fail at projection with both named.",
  "An interrupted upgrade rolls back to the previous state (kill test)."])
add(L, "Long-lived keys where wanted: hardware tokens (PIV, FIDO2), TPM sealing, and threshold signing for release approval", ["phase-5"], "5", (10,11), (13,14),
 "Keys where they are wanted: on-device custody for long-lived identity and release keys. Threshold signing is the named defence "
 "against a compromised maintainer account.",
 ["Sign a drip and a release with a FIDO2 token and with a PIV key; a 2-of-3 threshold release signature verifies.",
  "Custody options documented with their trust models."])
add(L, "User documentation: a CLI reference generated from the binary, and the guides", ["phase-5","documentation"], "5", (16,17), (),
 "Internal docs exist under `docs/`; users need a reference and guides before the first release: every command and flag generated "
 "from the binary so it cannot drift, plus the guides (wrap an existing build, first repository, keys and encryption).",
 ["`liquid docs` emits the reference; the published docs are built from it in CI.",
  "The guides exist for the Phase 2 exit scenario and are tested by running their commands."])

# ---------------- liquid, Phases 6–8 ----------------
add(L, "Complete client-side transparency-log verification: every tile verified against its parent", ["phase-6"], "6", (25,), (26,),
 "Partial verification is a bypass: `sum.golang.org`'s verifier shipped CVE-2026-56865 in August 2026 because tiles were not "
 "verified against their parents. liquid's client verifies the whole path or reports failure.",
 ["The libliquid verifier checks every tile against its parent and the checkpoint; a forged-tile test fails verification.",
  "Verification cost measured and recorded."])
add(L, "`liquid deploy`: deploy on change from the repository over the action graph, with per-change environments and rollback", ["phase-7"], "7", (13,18,21), (20,),
 "Deploy on change from the repository: environments, per-change preview environments, rollback to any prior state. No buildpacks "
 "— liquid knows what it built. In the editor a deployment is an action.",
 ["`liquid deploy` deploys a built target to a k0s cluster through the operator; `liquid deploy --to <prior state>` rolls back.",
  "A preview environment per change (orama-operator #124)."])
add(L, "Agent write flow control: token buckets per agent, document and tenant; bounded unacknowledged updates; explicit rejection", ["phase-8"], "8", (24,), (25,),
 "Silently dropping CRDT operations breaks causal dependencies, so an over-budget agent is paused or rejected explicitly, "
 "generation pauses when persistence or rendering lag crosses a watermark, and updates have a maximum size.",
 ["Limits configurable per agent, document and tenant; a runaway agent is throttled with an explicit signal and no lost operations.",
  "Watermarks visible in the daemon's status."])
add(L, "Stale-reasoning guard: an agent update carries the version it reasoned from and is re-validated if the base moved", ["phase-8"], "8", (24,), (25,),
 "Deterministic merge cannot repair decisions made from stale semantics. Every agent write names its base; if the base has moved, "
 "the write is re-validated (or re-planned) before it lands.",
 ["Writes without a base version are rejected; writes against a moved base are flagged and re-validated with the diff since the base."])
add(L, "Data-namespace isolation for agents: copy-on-write database branching", ["phase-8"], "8", (24,), (25,),
 "Git isolation does not isolate data: every worktree still points at the same `DATABASE_URL`, so one agent's migration or "
 "truncate hits everyone. Unspecified today; specify copy-on-write data branches per agent session.",
 ["Design recorded; a prototype branches a Postgres database per session and merges or discards it."])

# ---------------- lake, Phase 6 (groups drive the epic layout) ----------------
G_FOUND, G_ID, G_SEC, G_FORGE, G_REG, G_SEARCH, G_MODELS, G_DRIVE, G_OPS = (
 "Foundations", "Identity", "Secrets and PKI", "Forge", "Registry and transparency log", "Search",
 "Models and datasets", "Drive", "Platform and operations")
LAKE_GROUPS = {1:G_FOUND, 2:G_FOUND, 10:G_FOUND, 3:G_REG, 4:G_ID, 5:G_FORGE, 9:G_FORGE, 6:G_SEARCH, 7:G_MODELS, 8:G_DRIVE}

add(K, "Repository push and pull: the liquid ↔ lake wire protocol for drips and chunks", ["phase-6"], "6", (18,1,22), (1,12),
 "The daemon's fan-out (liquid #21) reaches lake through one protocol: negotiate what the other side lacks, transfer chunks with "
 "range fetch, exchange signed drips, verify on receipt. Authenticated by user tokens and workload attestation. The server side "
 "lives here; the client side is libliquid.",
 ["`liquid push` and `liquid pull` against `Lake/prod`; a clone of `steve/liquid` from lake.oramadev.net.",
  "Protocol documented under `docs/api/`; a conformance test shared with libliquid."], G_FOUND)
add(K, "Repository lifecycle from the API and pages: create, rename, transfer between customers, delete, visibility", ["phase-6"], "6", (18,), (22,),
 "The repository model and the explore pages exist; the lifecycle does not. Each step is a capability (so REST, OpenAPI and MCP "
 "get it for free) with a page on top.",
 ["Capabilities and pages for each; delete is soft with a documented retention; every step audit-logged.",
  "`docs/api/repositories.md` extended."], G_FORGE)
add(K, "End-user authentication: password with MFA, passkeys (WebAuthn) and OAuth social sign-in, each bound to a TAAP identity", ["phase-6"], "6", (19,), (23,),
 "Standard, and it has to be genuinely good or nobody reaches the interesting parts. Every method binds to a durable TAAP "
 "identity. The admin token stays an operator credential, not a user one.",
 ["Sign-up and sign-in with password + TOTP, a passkey and one OAuth provider on the production instance; sessions issued as today's `lake_session` cookie.",
  "A user row holds its TAAP identity (`taap_id`) after first sign-in.",
  "Documented under `docs/api/auth.md`."], G_ID)
add(K, "Enterprise SSO: SAML and OIDC sign-in with SCIM provisioning", ["phase-6"], "6", (19,), (23,),
 "An organisation that already runs Okta, Entra or Google Workspace signs in through it and provisions users and groups into a "
 "lake organization.",
 ["An Okta or Entra tenant signs in and provisions users and groups into an organization via SCIM.",
  "Group membership becomes team membership."], G_ID)
add(K, "Organizations: teams, roles, invitations and delegated administration, asserted as TAAP attestations", ["phase-6"], "6", (19,18), (23,),
 "Beyond the tables that exist: membership and role are TAAP attestations (`org_membership/1`), not a credential of their own; "
 "organization admins invite and delegate without lake staff.",
 ["Invite by email or handle; owner/admin/member roles per organization and per team; membership attested and verifiable offline.",
  "Pages and capabilities for each; `docs/api/organizations.md`."], G_ID)
add(K, "Sessions, per-user API tokens, device management, and revocation that takes effect", ["phase-6"], "6", (19,), (23,),
 "Long-lived static tokens are the failure mode; lake issues short-lived credentials by default and treats a static token as an "
 "explicit, audited exception. Replaces the single admin token as the API credential for users; the admin token remains the "
 "operator's break-glass.",
 ["Per-user tokens with scopes and expiry; a device list with revoke; a revoked session fails its next request.",
  "The capability registry's one auth check accepts user tokens with scopes."], G_ID)
add(K, "Audit log: authentication, authorisation decisions, and every secret and certificate issuance, access, renewal and revocation", ["phase-6"], "6", (19,20), (23,),
 "Which principal, which object, when, from where, under which policy. Certificate issuance additionally lands in the transparency log.",
 ["An append-only audit table and `/v1/audit` for organization admins.",
  "Every identity, secret and PKI capability writes to it; a test asserts the row per call."], G_ID)
add(K, "One policy engine over one object graph: repository, drive and platform permissions checked at the object, not per surface", ["phase-6"], "6", (19,15), (23,),
 "Three permission surfaces that must not become three permission systems: a path in a repository and a folder in the drive are "
 "the same object with the same ACL, viewed differently.",
 ["A single authorisation call used by every capability; permission on a repository path equals permission on the drive folder.",
  "Query-time filtering in search uses the same call."], G_ID)
add(K, "Decide auth-as-a-service for applications deployed on lake: sign-in components, user and organization management, JWT issuance and verification, lifecycle webhooks", ["phase-6","decision"], "6", (19,), (23,),
 "The way Clerk provides it. The largest scope question in the identity document: an explicit decision, not a drift. The "
 "operator's Clerk work (orama-operator #19, #65, #116) is the comparable.",
 ["Decision recorded in `decisions.md` with the scope in or out; if in, a follow-up epic."], G_ID)
add(K, "Federation: accept external identity providers, with policy naming which issuers are acceptable for which claims", ["phase-6"], "6", (19,25), (23,),
 "Federate rather than migrate. Trust is a graph, not a hierarchy: policy says which issuer may assert which claims.",
 ["An organization federates to Okta, Entra or Google Workspace and policy states which claims each issuer may assert.",
  "Documented with the trust-graph model."], G_ID)
add(K, "Offline authorisation semantics: what a cached credential permits and for how long", ["phase-6"], "6", (19,25), (23,),
 "liquid works fully offline, so authorisation cannot always be re-checked. Specify cached permission lifetimes and what "
 "revocation cannot recall.",
 ["The specification written; liquid enforces it and labels cached decisions in the CLI."], G_ID)
add(K, "Account recovery, and its interaction with end-to-end-encrypted repositories", ["phase-6"], "6", (19,25), (23,),
 "Where consumer identity systems actually fail. If lake cannot read the data, lake cannot restore access to it; TAAP open "
 "question 22.6 is the key-based version of the same problem.",
 ["A recovery flow for identity; a documented, tested statement of what is unrecoverable for encrypted repositories and the custody options that change that."], G_ID)
add(K, "Static secrets: versioned key-value with history, soft delete and metadata (the Vault KV v2 shape)", ["phase-6"], "6", (20,), (23,),
 "Still needed and supported; dynamic secrets (#4) remain the default and the UI makes them the easier choice.",
 ["KV capabilities and pages with versions, soft delete and metadata."], G_SEC)
add(K, "Encryption as a service: encrypt, decrypt, sign, verify and derive keys without the key leaving lake", ["phase-6"], "6", (20,11), (23,),
 "Vault's transit model: an application encrypts user data without ever holding the key material. Shares the envelope machinery "
 "with repository encryption; one of liquid's KEK custody providers targets it.",
 ["Transit-style capabilities; liquid's custody provider for lake works against them."], G_SEC)
add(K, "Certificate profiles: SPIFFE X.509 and JWT SVIDs, an ACME endpoint, SSH certificates, client and device certificates", ["phase-6"], "6", (20,), (23,),
 "ACME so cert-manager and the Let's Encrypt ecosystem work against lake unchanged; SSH certificates rather than distributed "
 "public keys; SVIDs for workloads.",
 ["cert-manager obtains a certificate from lake via ACME unchanged; an SSH certificate signs in to a host; SVIDs issued to workloads."], G_SEC)
add(K, "Caller authentication by attestation: Kubernetes service-account tokens, OIDC/JWT federation, cloud instance identity, workload identity", ["phase-6"], "6", (20,25), (23,),
 "\"What secret lets you fetch secrets?\" is solved by attestation rather than a first secret, because lake already knows what it deployed.",
 ["A pod authenticates to lake with its projected token and receives a dynamic secret; no bootstrap secret exists."], G_SEC)
add(K, "Break-glass, Shamir root-key recovery with a rehearsed quorum, and documented degraded-mode availability", ["phase-6"], "6", (20,), (23,),
 "Break-glass is auditable, time-boxed and loud. An untested recovery procedure is not a recovery procedure. If applications "
 "mint credentials at runtime, lake being down stops them from starting — write down what does and does not.",
 ["The unseal rehearsal runbook executed on a staging instance.",
  "Degraded-mode behaviour documented per dependent."], G_SEC)
add(K, "Decide the secrets-engine API surface (Vault-compatible or clean) and its namespacing and multi-tenancy model", ["phase-6","decision"], "6", (20,), (23,),
 "Compatibility buys immediate ecosystem access — External Secrets Operator, existing client libraries — at the cost of "
 "inheriting a large, awkward surface. A significant early decision.",
 ["Decision in `decisions.md`; if Vault-compatible, External Secrets Operator works against lake unchanged."], G_SEC)
add(K, "Forge surface beyond review: issues and discussion, releases, webhooks, branch protection", ["phase-6"], "6", (18,), (22,),
 "Listed beside review in the lake specification. Branch protection is policy over the object graph, not a separate system.",
 ["Each as capabilities plus pages; branch protection expressed through the policy engine."], G_FORGE)
add(K, "Full export: history, artifacts, issues, review discussion, permissions and deployment configuration", ["phase-6"], "6", (18,), (22,),
 "No lock-in. What is portable between forges today is only git history; everything else is hostage. lake exports the whole "
 "thing, and self-hosting is a supported configuration.",
 ["An export of a lake customer produces a self-contained archive that a self-hosted lake imports."], G_FORGE)
add(K, "GitHub migration importer, with stated fidelity for issues, pull requests and Actions", ["phase-6"], "6", (18,2), (22,),
 "History imports losslessly through liquid's Git import; issues, pull requests and Actions do not. How much fidelity is worth "
 "building is open, but the on-ramp is required.",
 ["History via liquid's Git import; issues and pull requests import with a fidelity report; Actions are analysed, not imported."], G_FORGE)
add(K, "Metering and pricing on unique stored bytes, never degrading to pointer files at a quota", ["phase-6"], "6", (18,), (22,12),
 "Charging per nominal repository size would bill customers for bytes lake does not store. Git LFS quotas — exceeding a limit "
 "silently gives you pointer files instead of your data — are the specific failure never to reproduce.",
 ["Usage per customer computed from unique chunks; a quota that is exceeded blocks new writes with a clear message and never substitutes content."], G_OPS)
add(K, "TUF-style repository roles (root, targets, snapshot, timestamp) with threshold signing and key-compromise recovery", ["phase-6"], "6", (10,9), (13,12),
 "Role separation defends against attacks signatures miss entirely: freeze attacks (a stale index so clients never see a security "
 "update), rollback, and mix-and-match. The registry serves the metadata; liquid's client enforces it.",
 ["The registry serves TUF metadata; the liquid client refuses freeze, rollback and mix-and-match in tests.",
  "A key-compromise rotation drill documented and rehearsed."], G_REG)
add(K, "Log configurations: air-gapped, witnessed (default) and anchored via OpenTimestamps-style aggregation", ["phase-6"], "6", (25,), (26,),
 "Hourly by default the log's current Merkle root is committed to a public chain. Air-gapped is a supported configuration, not "
 "a degraded one. Anchoring proves existence only — not authorship, correctness, ownership or truth.",
 ["All three configurations selectable on the `Lake` CR; anchoring hourly by default; the docs state what anchoring proves."], G_REG)
add(K, "RFC 3161 timestamping and long-term validity: renewed archive timestamps (RFC 4998 ERS)", ["phase-6"], "6", (25,), (26,),
 "The log does not provide authoritative time; a TSA does. Long-term validity requires timestamping the signature value rather "
 "than the document, renewing archive timestamps before the old protection weakens, and rehashing prior evidence before the hash "
 "algorithm breaks.",
 ["A TSA endpoint; signatures timestamped; a renewal job re-timestamps before protection weakens, with the evidence chain in the log."], G_REG)
add(K, "Transparency-log monitoring: identity scans over bulk tiles that anyone can afford", ["phase-6"], "6", (25,), (26,),
 "Monitoring cost is the real bottleneck: a Rekor v1 identity scan was measured at ~50× slower than log growth; bulk tiles "
 "improved it by two orders of magnitude. A log nobody can afford to monitor provides no security.",
 ["A monitor scans the log for a given identity at less than log-growth cost (measured); a hosted monitor for every customer."], G_REG)
add(K, "Multi-region replication of the store and the transparency log", ["phase-6"], "6", (9,), (12,26),
 "The first named open question of the artifact service: replication across regions and how the log stays consistent.",
 ["A design for the data plane (Zetta) and the log across regions with the consistency argument written down; a two-region deployment through the operator."], G_REG)
add(K, "Per-session agent key custody: short-lived keys minted per session, attested to a durable agent identity", ["phase-6"], "6", (25,24), (26,25),
 "An agent needs a key it can sign with, which is a secret it holds. Short-lived keys minted per session, attested to a durable "
 "agent identity, is the probable shape.",
 ["An agent obtains a session key from lake via attestation; drips signed with it attribute to the durable agent identity."], G_REG)
add(K, "Query-time permission filtering in every search channel, and the anonymous-public-read decision", ["phase-6"], "6", (12,9), (19,),
 "Permission filtering applies in every channel, checked at query time through the one policy engine. Whether public "
 "repositories are searchable anonymously is decided here.",
 ["Search results never include an object the caller cannot read (mixed-visibility test); anonymous public read decided and documented."], G_SEARCH)
add(K, "Search over history: hot index on branch tips, cold snapshots for releases and tags, scan for arbitrary changes", ["phase-6"], "6", (12,), (19,),
 "Hybrid, because indexing every change is prohibitive.",
 ["Query any tag's snapshot; arbitrary change search falls back to scan and says so."], G_SEARCH)
add(K, "Index inside published artifacts: .deb, wheel, jar, OCI layer", ["phase-6"], "6", (9,12), (19,12),
 "Searching the contents of published artifacts is a capability no existing code-search engine offers. Reuses the format "
 "registry's decomposition.",
 ["Search a symbol inside a published `.deb` and an OCI layer."], G_SEARCH)
add(K, "Drive web surface: browse, preview through the format registry, share, history", ["phase-6"], "6", (15,18), (21,),
 "Preview uses the format registry — the same code that decomposes a `.deb` renders a spreadsheet. Conflicts are presented as "
 "\"two versions of this file, here is what differs\".",
 ["Pages for folders and files with preview via codecs; conflict presentation as two versions with the structural difference."], G_DRIVE)
add(K, "Sharing UI designed against the documented user confusions", ["phase-6"], "6", (15,19), (21,),
 "At the moment of sharing show who can access, what they can do, whether access is inherited, and whether the recipient gets a "
 "live object, a link, or an independent copy. A share link is a continuing capability, not an attachment.",
 ["The share dialog answers all four questions before the share is made; revoking a link takes effect."], G_DRIVE)
add(K, "Linux desktop integration for the drive: pin states, hydration policy, offline behaviour and badges", ["phase-6"], "6", (15,16), (21,),
 "No standard placeholder API, no pinning bit, no cross-desktop badge protocol: Linux is real work and is budgeted as such, "
 "against the three states online-only / available offline / not synced here.",
 ["The three states on GNOME and KDE via FUSE with a file-manager extension for badges."], G_DRIVE)
add(K, "Decide the compliance scope: SOC 2, GDPR data residency, regulated scientific and clinical data", ["phase-6","decision"], "6", (19,), (23,),
 "This constrains architecture and is cheaper to design for than to retrofit.",
 ["Decision in `decisions.md`; the architectural consequences (residency, retention, audit) opened as issues."], G_OPS)
add(K, "Operational telemetry: /metrics, structured logs, health and readiness endpoints", ["ops"], "x", (18,), (),
 "`Lake/prod` runs three replicas with a readiness probe on `/` and beast2's stderr as its only log. Production needs Prometheus "
 "metrics for requests, store calls and the io thread; JSON logs; and health endpoints the Deployment and the operator can use.",
 ["`/metrics`, `/healthz`, `/readyz`; the Deployment uses them (orama-operator #122) and the cluster scrapes them (orama-operator #15).",
  "Documented under `docs/serving/`."], G_OPS)
add(K, "CI: build, tests and the amd64 image from tags", ["ops"], "x", (), (),
 "Images are built by hand today (`docs/build/container-image.md`). CI on the private repo builds with the Dockerfile's toolchain, "
 "runs the tests, and pushes `oramasearch/lake:<tag>` on a tag so the deploy runbook consumes immutable tags only.",
 ["GitHub Actions builds, runs `ctest`, and pushes the image on a tag.",
  "The deploy runbook references the workflow."], G_OPS)

# ---------------- liquify ----------------
add(F, "Stub trees: per-blob declaration subsets, content-addressed and cached like any action output", ["phase-4"], "4", (21,), (24,),
 "A stub is a compact serialised subset of a parse tree — declarations, names, modifiers, signatures — sufficient to resolve "
 "symbols from other files without fully parsing them. Cross-file resolution reads stubs; only open files need full trees.",
 ["Stubs are outputs of liquid's graph, content-addressed; opening a large repository resolves cross-file symbols without parsing closed files."])
add(F, "Interactive analysis layer over the query graph: error-tolerant parsing, source ranges and trivia, cursor-centric queries", ["phase-4"], "4", (21,4), (24,),
 "What the shared graph does not remove is the need for interactive-specific analysis: incomplete, invalid input; source ranges "
 "and trivia; recoverable trees. rust-analyzer's compiler/HIR/IDE split inside one program.",
 ["Completions and diagnostics on invalid input; cursor-centric queries answered from the graph."])
add(F, "Inline build, test and deploy from the editor against the same graph", ["phase-4"], "4", (21,13), (24,),
 "Same graph: a test result is a query, a build is visible as it runs, a deployment is an action.",
 ["Run a target's tests and see the result as a query; a build shows its critical path as it runs; deploy is wired when `liquid deploy` exists (Phase 7)."])
add(F, "Decide extension compatibility: VS Code extension API compatibility versus a clean native API", ["phase-4","decision"], "4", (21,), (24,),
 "Large, thankless, effective versus small, elegant, empty. The marketplace moat is partly legal: an extension sidesteps it, a "
 "fork inherits it. Decide before the plugin ABI (#3).",
 ["Decision recorded in `CLAUDE.md` with the argument."])
add(F, "Structural editing: AST-level refactors, structural selection, node-level edits for agents", ["phase-8"], "8", (21,24), (24,),
 "The AST already exists. Refactors, structural selection and structural diff come from the tree the build is already using; "
 "agents express edits at the node level instead of whole-file rewrites.",
 ["Rename and extract-function on the graph's tree; agents use the same node-level API."])
add(F, "Review in place: lake changes reviewed in the editor with cursor-anchored comments that survive rebase", ["phase-8"], "8", (21,18), (24,22),
 "Changes from lake are reviewed in the editor against real semantics rather than a text diff, and comments anchor to cursors "
 "that survive rebases.",
 ["Open a change from lake, comment on a cursor, rebase the change: the comment survives."])
add(F, "AI as a first-class but switch-off-able surface, fed by the real graph", ["phase-8"], "8", (21,), (24,),
 "liquid knows the real dependency graph, the real symbol table and the real build errors — dramatically better context than an "
 "editor grepping for relevant files. The ability to turn it off entirely is itself a differentiator.",
 ["A model receives graph context; one switch turns the whole surface off and nothing leaves the machine."])
add(F, "Release packaging: signed dmg/pkg, MSI/MSIX, AppImage/Flatpak, produced by liquid's projection once it exists", ["phase-5"], "5", (8,21), (10,),
 "A native IDE ships as an installer per platform. Notarised macOS and signed Windows builds; a Linux desktop format; produced "
 "by liquid's own projection targets when they land (liquid Phase 5), hand-built until then.",
 ["Notarised macOS build and signed Windows build from CI; an AppImage or Flatpak that runs on two distributions."])
add(F, "CI on the private repo: build, tests and `--smoke` on macOS, Windows and Linux", ["ops"], "x", (), (),
 "Nothing runs on push today. A matrix that builds with FetchContent'd SDL3 and ImGui, runs `ctest`, and runs `--smoke` under a "
 "virtual display on Linux and natively on macOS and Windows.",
 ["A green matrix on all three platforms; the pinned liquid submodule is built library-only in the same job."])

# ---------------- k0s ----------------
add(S, "Opinionated defaults as replaceable components with declared versions: Cilium/eBPF, Gateway API, local-path plus one distributed storage option", ["phase-7"], "7", (13,), (20,),
 "k3s is pleasant because it bundles Traefik, ServiceLB, Flannel and local-path storage — and its worst complaints come from "
 "exactly that, because bundled components shift under users at upgrade time and fight replacements.",
 ["Each bundled component has a declared version and a documented replacement path; upgrading k0s does not silently change them."])
add(S, "Cluster lifecycle: upgrades, backup and restore, node replacement, certificate rotation, observability", ["phase-7"], "7", (13,), (20,),
 "A credible new distribution is mostly a lifecycle-integration project. Running `kube-apiserver` is easy; networking, storage, "
 "certificates, upgrades, backup/restore, node replacement, observability and multi-tenancy are the work.",
 ["Runbooks and automation for each on the `liquid` branch, exercised on a three-node cluster."])
add(S, "Decide the multi-tenancy model: namespaces, vcluster, separate clusters or microVMs", ["phase-7","decision"], "7", (13,), (20,),
 "Namespaces are not a security boundary, and the alternatives have very different costs. Preview environments per change "
 "(orama-operator #124) depend on the answer.",
 ["Decision recorded with the security-boundary argument."])

# ---------------- orama-operator ----------------
add(OP, "[lake] Control-plane Postgres backups and restore for every Lake (scheduled, to R2/S3)", ["lake","p2"], "6", (18,), (),
 "`Lake/prod` holds users, organizations, customers and repositories in a 50Gi CNPG cluster with no backup. Scheduled backups "
 "of `lake-<name>-controldb` through the operator's backup work (#33), and a restore that has been run.",
 ["Scheduled CNPG backups per Lake with a tested restore into a fresh Lake; documented in `docs/lake/README.md`."])
add(OP, "[lake] Managed data services under a Lake: tested backup, restore, upgrade and failover, or labelled unmanaged", ["lake","p3"], "7", (13,), (20,),
 "Railway's standard databases are explicitly unmanaged while the product feels managed, and that gap bites users. Every data "
 "service the `Lake` CR provisions is either operated properly or labelled accurately in status and docs. No implied guarantees.",
 ["Each provisioned data service has tested procedures or an `unmanaged` marker in `Lake` status and the docs."])
add(OP, "[lake] One-way sealed secret delivery: secrets referenced from the repository, minted by lake at deploy time, decryptable only in the cluster", ["lake","p3"], "7", (13,11,20), (20,14),
 "Referenced from the repository, minted at deploy time, delivered one way in the manner of Sealed Secrets, so committing a secret "
 "does not require the author to be able to read it back.",
 ["A sealed secret committed by an author who cannot read it back decrypts only in the target cluster; keys held by the operator."])

# ---------------- liquid-bridge ----------------
add(BR, "TAAP/1 protocol feedback beyond content-addressed subjects: attenuation-only delegation with depth limits, identifier stability across rotation, the `taap:` scheme", ["decision","phase-0"], "0", (25,), (26,),
 "The remaining TAAP open questions liquid's specification answers: 22.5 delegation must be attenuation-only with depth limits "
 "(human → agent → subagent is the normal topology); 22.2 identifiers must stay stable so a drip signed in 2026 remains "
 "attributable after a 2029 key rotation; 22.10 the `taap:` scheme is worth resolving before anything ships depending on it.",
 ["Feedback delivered to the protocol owner; spec updates vendored under liquid `docs/standards/`."])
add(BR, "Decide the portfolio presentation: liquid/lake/liquify/drip and Orama/Zetta as one family or two", ["decision"], "x", (23,), (),
 "A positioning decision, not a technical one. Recorded here; the confidential material stays in `oramasearch/corporate-intelligence`.",
 ["Decision recorded in `decisions.md`."])
add(BR, "Scrub confidential references from liquid and liquify history and docs before publishing", ["ops"], "x", (23,), (),
 "Both repositories are private today and their history and docs may reference confidential material. Before either goes "
 "public: an audit of every commit and document, a rewritten history if needed, and a recorded sign-off.",
 ["Audit complete; history rewritten if required; sign-off recorded on this issue."])
add(BR, "Security review and vulnerability disclosure policy before liquid and liquify go public", ["ops"], "x", (10,11,22), (13,14),
 "The store, capture and signing paths are security surfaces. Before publishing: a threat-model review, `SECURITY.md` with a "
 "disclosure address, and fuzzing targets for the chunker and the codecs in CI.",
 ["Threat model reviewed and recorded; `SECURITY.md` in both repos; fuzzers running in CI."])
add(BR, "Metis go-to-market: the forward-deployed motion on an instrumented estate", ["phase-8"], "8", (23,), (),
 "Phase 8 item. Confidential: the plan lives in `oramasearch/corporate-intelligence`; this issue only sequences it after Phase 7.",
 ["Defined when Phase 7 is done."])
add(BR, "Decide where lake.live runs: AKS, our own k0s on rented hardware, or both, with the disaster-recovery posture", ["decision","ops"], "x", (18,13), (20,),
 "`Lake/prod` runs on the AKS sandbox cluster at lake.oramadev.net. The production home for lake.live is a decision: stay on AKS, "
 "move to our own k0s (the Phase 7 dogfood), or both, and what the recovery posture is.",
 ["Decision in `decisions.md`; the production `Lake` CR moves accordingly (#5 for DNS)."])
add(BR, "SLOs, status page and on-call runbooks for lake.live", ["ops"], "x", (18,), (),
 "A hosted service needs stated objectives, a place to read its status, and runbooks for the person paged. Builds on lake's "
 "telemetry issue and the operator's observability work (orama-operator #15).",
 ["SLOs written; a status page; runbooks for the failure modes seen so far (pod restarts, schema Job failure, DNS, Cloudflare)."])
add(BR, "Terms of service, privacy policy and data-processing terms for lake.live", ["ops"], "x", (18,19), (),
 "Customers sign up to something. The documents, and the compliance-scope decision on lake that constrains them.",
 ["Documents published on lake.live and linked from sign-up."])

# ==============================================================================================
# 1. Create the leaf issues
# ==============================================================================================
NEW_PHASE = {}
print("== leaf issues", flush=True)
for repo, title, labels, phase, feats, researches, body, dones, group in NEW:
    full = header(PHASES[phase], feats, researches) + body + "\n" + done(dones)
    i = create(repo, title, full, labels)
    NEW_PHASE[(repo, i["number"])] = phase
    if repo == K and group:
        LAKE_GROUPS[i["number"]] = group

# lake #10 (OpenAPI + MCP surface) is built and live: close it.
ten = next(i for i in ISSUES[K] if i["number"] == 10)
if ten["state"] == "OPEN":
    sh("gh","issue","close","10","--repo",f"{ORG}/lake","--comment",
       "Built (lake f0a30b4, the control surface): one capability registry exposed as REST `/v1`, `/v1/openapi.json` and "
       "`POST /mcp`, live on `Lake/prod` at https://lake.oramadev.net. Docs: `docs/api/README.md` (adding a capability), "
       "`docs/api/mcp.md`. New capabilities get all three adapters from the registry.")
    ten["state"] = "CLOSED"; print("  closed lake#10", flush=True)

# ==============================================================================================
# 2. Epics
# ==============================================================================================
def find(repo, number): return next(i for i in ISSUES[repo] if i["number"] == number)
def by_title(repo, title): return BY_TITLE[repo][title]
def line(i): return f"- [{'x' if i['state'] == 'CLOSED' else ' '}] {i['url']} — {i['title']}"
def leaves(repo, label):
    return sorted((i for i in ISSUES[repo] if label in i["labels"] and "epic" not in i["labels"]), key=lambda i: i["number"])
def section(title, items):
    return (f"\n{title}\n\n" + "\n".join(line(i) for i in items) + "\n") if items else ""
def intro_of(repo, number):
    """The epic's own text between its header line and the first '## ' section."""
    head = find(repo, number)["body"].partition("\n## ")[0].strip().split("\n")
    return "\n".join(head[1:]).strip()
def epic_header(title, feats=(), extra=""):
    return header(title, feats, (), f"master epic: {MASTER}" + (f" · {extra}" if extra else ""))

print("== phase epics", flush=True)
# liquid Phases 1, 2, 3
for num, label in ((33,"phase-1"), (34,"phase-2"), (35,"phase-3")):
    e = find(L, num)
    body = epic_header(e["title"].replace("[epic] ","")) + intro_of(L, num) + "\n" + section("## Issues", leaves(L, label))
    edit(L, num, body); print(f"  liquid#{num} regenerated", flush=True)
# Phase 4: liquid + liquify (retitled: liquify is native, not an extension)
t4 = "[epic] Phase 4 — The incremental engine and liquify on the graph"
body = epic_header(t4.replace("[epic] ","")) + intro_of(L, 36) + "\n" + section("## Issues", leaves(L, "phase-4")) \
     + section("On liquify:", leaves(F, "phase-4"))
edit(L, 36, body, t4); print("  liquid#36 regenerated + retitled", flush=True)
# Phase 5: liquid + liquify packaging
body = epic_header("Phase 5 — Resolution and projection") + intro_of(L, 37) + "\n" + section("## Issues", leaves(L, "phase-5")) \
     + section("On liquify:", leaves(F, "phase-5"))
edit(L, 37, body); print("  liquid#37 regenerated", flush=True)
# Phase 8: liquid + liquify + bridge (retitled: native liquify is decided)
t8 = "[epic] Phase 8 — Multiplayer and agents, hot update, liquify beyond the graph"
body = epic_header(t8.replace("[epic] ","")) + intro_of(L, 38) + "\n" + section("## Issues", leaves(L, "phase-8")) \
     + section("On liquify:", leaves(F, "phase-8")) + section("On liquid-bridge:", leaves(BR, "phase-8"))
edit(L, 38, body, t8); print("  liquid#38 regenerated + retitled", flush=True)

# Phase 6 — lake #11, grouped
lake_leaves = sorted((i for i in ISSUES[K] if "epic" not in i["labels"]), key=lambda i: i["number"])
groups = [G_FOUND, G_ID, G_SEC, G_FORGE, G_REG, G_SEARCH, G_MODELS, G_DRIVE, G_OPS]
body = epic_header("Phase 6 — lake") + intro_of(K, 11) + "\n\n## Issues\n"
for g in groups:
    body += section(f"### {g}", [i for i in lake_leaves if LAKE_GROUPS.get(i["number"], G_OPS) == g])
op_lake = [i for i in sorted(ISSUES[OP], key=lambda i: i["number"]) if "lake" in i["labels"]]
body += section("### On orama-operator (the `Lake` CR)", op_lake) + section("### On liquid", leaves(L, "phase-6"))
edit(K, 11, body); print("  lake#11 regenerated", flush=True)

# Phase 7 — k0s #18
op7 = [find(OP, 124)] + [i for i in ISSUES[OP] if NEW_PHASE.get((OP, i["number"])) == "7"]
body = epic_header("Phase 7 — The runtime (k0s `liquid` branch)") + intro_of(S, 18) + "\n" + section("## Issues", leaves(S, "phase-7")) \
     + section("On orama-operator:", sorted(op7, key=lambda i: i["number"])) + section("On liquid:", leaves(L, "phase-7"))
edit(S, 18, body); print("  k0s#18 regenerated", flush=True)

print("== repository epics", flush=True)
# orama-operator: the Lake CR
op_title = "[epic][lake] The Lake CR — everything the operator does for lake"
op_body = epic_header("Phase 6 — lake", (18,13), f"docs: [docs/lake/README.md](https://github.com/oramasearch/orama-operator/blob/main/docs/lake/README.md)") + (
 "`Lake` is a cluster-scoped CR on this operator (PR #118): a namespace, the lake Deployment and Service, a CloudNativePG control "
 "plane (`spec.postgres`), the schema through `PostgresSchema`, a once-minted admin token, an nginx Ingress and an owned Cloudflare "
 "record. `Lake/prod` runs on AKS at https://lake.oramadev.net. This epic collects everything the operator still owes lake, "
 "through to the on-prem install (#123) and the Zetta data plane (#125).\n") \
 + section("## Issues", [i for i in op_lake if "epic" not in i["labels"]]) \
 + section("Sub-epics:", [i for i in op_lake if "epic" in i["labels"]]) \
 + section("Operator work this depends on:", [find(OP, n) for n in (106, 126, 11, 15, 33, 93)])
op_epic = create(OP, op_title, op_body, ["epic","lake","p2"])
if op_epic.get("body") != op_body: edit(OP, op_epic["number"], op_body)

# liquify
fy_title = "[epic] liquify — the IDE"
fy_leaves = sorted((i for i in ISSUES[F] if "epic" not in i["labels"]), key=lambda i: i["number"])
fy_body = epic_header("Cross-phase", (21,)) + (
 "The native, cross-platform IDE for liquid (SDL3 + Dear ImGui, C++26), a client of libliquid. Hello world is done; the editor "
 "arrives with Phase 4 (on the graph) and grows through Phase 8 (multiplayer, agents, plugins). It never depends on Zetta and "
 "never reimplements liquid.\n") \
 + section("## Phase 4 — on the graph", [i for i in fy_leaves if "phase-4" in i["labels"]]) \
 + section("## Phase 5 — packaging", [i for i in fy_leaves if "phase-5" in i["labels"]]) \
 + section("## Phase 8 — beyond the graph", [i for i in fy_leaves if "phase-8" in i["labels"]]) \
 + section("## Operations", [i for i in fy_leaves if "ops" in i["labels"]])
fy_epic = create(F, fy_title, fy_body, ["epic"])
if fy_epic.get("body") != fy_body: edit(F, fy_epic["number"], fy_body)

# liquid-bridge: open-source release
oss_title = "[epic] Open-source release of liquid and liquify"
oss_items = [find(BR, 2), find(BR, 3),
 by_title(BR, "Scrub confidential references from liquid and liquify history and docs before publishing"),
 by_title(BR, "Security review and vulnerability disclosure policy before liquid and liquify go public"),
 find(L, 9), by_title(L, "User documentation: a CLI reference generated from the binary, and the guides"),
 by_title(F, "CI on the private repo: build, tests and `--smoke` on macOS, Windows and Linux")]
oss_body = epic_header("Cross-phase", (23,17)) + (
 "liquid and liquify are private today and open source eventually (decisions.md §5). Publishing is a sequence, not a switch: "
 "the licence, the history, the security posture, the build matrix and the user documentation. Never make either repository "
 "public before every item here is closed.\n") + section("## Issues", oss_items) + done([
 "Both repositories public under the chosen licence with `LICENSE`, `NOTICE` policy, `SECURITY.md` and contribution terms.",
 "A clean clone builds and passes on all three platforms from the public repo."])
oss_epic = create(BR, oss_title, oss_body, ["epic","ops"])
if oss_epic.get("body") != oss_body: edit(BR, oss_epic["number"], oss_body)

# liquid-bridge: lake.live
ll_title = "[epic] lake.live — the hosted service goes live"
ll_items_bridge = [find(BR, 5),
 by_title(BR, "Decide where lake.live runs: AKS, our own k0s on rented hardware, or both, with the disaster-recovery posture"),
 by_title(BR, "SLOs, status page and on-call runbooks for lake.live"),
 by_title(BR, "Terms of service, privacy policy and data-processing terms for lake.live")]
ll_items_lake = [by_title(K, t) for t in (
 "End-user authentication: password with MFA, passkeys (WebAuthn) and OAuth social sign-in, each bound to a TAAP identity",
 "Organizations: teams, roles, invitations and delegated administration, asserted as TAAP attestations",
 "Sessions, per-user API tokens, device management, and revocation that takes effect",
 "Audit log: authentication, authorisation decisions, and every secret and certificate issuance, access, renewal and revocation",
 "Repository push and pull: the liquid ↔ lake wire protocol for drips and chunks",
 "Repository lifecycle from the API and pages: create, rename, transfer between customers, delete, visibility",
 "Metering and pricing on unique stored bytes, never degrading to pointer files at a quota",
 "Decide the compliance scope: SOC 2, GDPR data residency, regulated scientific and clinical data",
 "Operational telemetry: /metrics, structured logs, health and readiness endpoints",
 "CI: build, tests and the amd64 image from tags")]
ll_items_op = [find(OP, 119), find(OP, 120), find(OP, 122),
 by_title(OP, "[lake] Control-plane Postgres backups and restore for every Lake (scheduled, to R2/S3)")]
ll_body = epic_header("Phase 6 — lake", (18,19)) + (
 "`Lake/prod` answers at https://lake.oramadev.net with an admin sign-in and the first control-plane tables. lake.live is the "
 "same service with customers on it: its own zone, accounts, tokens, billing on unique bytes, backups that restore, objectives "
 "someone is paged for, and terms. Phase 6's product surfaces (forge, registry, identity provider) land through lake #11; this "
 "epic is what makes the hosted instance a service.\n") \
 + section("## This repo", ll_items_bridge) + section("## On lake", ll_items_lake) + section("## On orama-operator", ll_items_op) + done([
 "https://lake.live serves `Lake/prod` (or its successor) with TLS through Cloudflare and the oramadev.net host retired.",
 "A stranger can sign up, create a repository, push to it from `liquid`, and be billed for the unique bytes.",
 "A restore from backup has been performed on a copy of production."])
ll_epic = create(BR, ll_title, ll_body, ["epic","ops"])
if ll_epic.get("body") != ll_body: edit(BR, ll_epic["number"], ll_body)

# ==============================================================================================
# 3. The master epic — liquid-bridge #7
# ==============================================================================================
print("== master epic", flush=True)
def row(mark, url, text): return f"- [{mark}] {url} — {text}"
phase_rows = "\n".join([
 row(" ", "Phase 0 — Decide", "no epic; the open decisions are listed below (spec change #1, licence text #2, automerge-cpp home #3, TAAP feedback)"),
 row("x", "Phase 0.5 — Hello world, every component", f"met on AKS 2026-09-02; the k0s half is {find(S,13)['url']}"),
 line(find(L,33)), line(find(L,34)), line(find(L,35)), line(find(L,36)), line(find(L,37)),
 line(find(K,11)), line(find(S,18)), line(find(L,38))])
repo_rows = "\n".join([
 f"- **liquid** — the phase epics above (Phases 1–5 and 8); libliquid's API is {find(L,39)['url']}.",
 f"- **lake** — {find(K,11)['url']} (Phase 6) and the launch epic {ll_epic['url']}.",
 f"- **liquify** — {fy_epic['url']}.",
 f"- **orama-operator** — {op_epic['url']} (the `Lake` CR), which depends on the operator's own epics "
 f"{find(OP,11)['url']}, {find(OP,33)['url']}, {find(OP,93)['url']}.",
 f"- **k0s** — {find(S,18)['url']} (Phase 7).",
 f"- **liquid-bridge** — {oss_epic['url']}, {ll_epic['url']}.",
 "- **automerge-cpp** (the org's private copy, the CRDT liquid's metadata layer sits on) — https://github.com/oramasearch/automerge-cpp/issues/13."])
decisions = [i for r in REPOS for i in sorted(ISSUES[r], key=lambda i: i["number"])
             if "decision" in i["labels"] and i["state"] == "OPEN"]
ops = [i for r in REPOS for i in sorted(ISSUES[r], key=lambda i: i["number"])
       if "ops" in i["labels"] and "epic" not in i["labels"] and i["state"] == "OPEN"] + [find(OP,119), find(OP,120)]
master = header("liquid — the master epic", (), (), f"decisions: [decisions.md]({DECISIONS}) · repositories: "
 f"[repositories.md]({BRIDGE}/repositories.md) · how work is tracked: [tracking.md]({TRACKING})") + (
 "One issue that links every epic. The project is **liquid** (version control, build, packages, artifacts and runtime in one "
 "program; open source eventually), **lake** (the hosted service at lake.live; enterprise), **liquify** (the native IDE), the "
 "**Orama operator** (deploys lake from a `Lake` CR) and our **k0s** copy (the runtime). The order is forced by dependencies: "
 "the forge, the IDE and the consumer drive are the payoff, and every one of them depends on the store, the graph and the daemon "
 "being right first. No durations; a phase is done when its exit criterion is met. Leaf issues live under the epics, in the "
 "repository that owns the work; every epic links back here.\n\n"
 "## Where things stand (2026-09-03)\n\n"
 f"- Phase 0 is decided except the spec and licence items ({find(BR,1)['url']}, {find(BR,2)['url']}). "
 "Phase 0.5 was met on AKS on 2026-09-02: `Lake/prod` runs the lake control surface (REST `/v1`, OpenAPI, MCP, the first "
 f"control-plane tables, pages) at https://lake.oramadev.net through the operator; the k0s half is {find(S,13)['url']}.\n"
 f"- In progress: Phase 1, the store, inside libliquid ({find(L,33)['url']}).\n\n"
 "## Phase epics, in dependency order\n\n" + phase_rows + "\n\n"
 "## Repository epics\n\n" + repo_rows + "\n\n"
 "## Decisions still open\n\n" + "\n".join(line(i) for i in decisions) + "\n\n"
 "## Operations and follow-ups\n\n" + "\n".join(line(i) for i in ops) + "\n\n"
 "## Done when\n\n"
 "- [ ] Every phase exit in the plan is met, Phases 1 through 8.\n"
 "- [ ] liquid and liquify are public under the chosen licence, history scrubbed, disclosure policy in place.\n"
 "- [ ] lake.live is live for customers: accounts, tokens, billing on unique bytes, backups that restore, SLOs, terms.\n"
 "- [ ] A customer installs k0s and the operator on their own hardware, applies one `Lake` CR, and has the private forge, "
 "registry and identity provider with every artifact verifying against a witnessed log and no connection to lake.live.\n")
edit(BR, 7, master, "[epic] liquid — the master epic")
print(f"  {MASTER} rewritten", flush=True)

with open(OUT, "w") as f:
    f.write("repo\tstatus\turl\ttitle\n")
    for r, s, u, t in created: f.write(f"{r}\t{s}\t{u}\t{t}\n")
n_new = sum(1 for c in created if c[1] == "created")
print(f"\n{n_new} created, {len(created) - n_new} reused; recorded in {OUT}")
