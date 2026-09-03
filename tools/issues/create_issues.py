#!/usr/bin/env python3
"""Create the liquid project's GitHub issues across its repos.

Two passes: leaf issues first (URLs collected), then phase epics listing their children by full
URL, then one tracking epic in liquid-bridge. Idempotent-ish: an existing open issue with the same
title in the same repo is reused, not duplicated. Output: issues-created.tsv next to this script.
"""
import json
import os
import subprocess
import sys

ORG = "oramasearch"
DOCS = "https://github.com/oramasearch/liquid/blob/main/docs"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "issues-created.tsv")

FEATURES = {
    1: "01-object-model-and-storage.md", 2: "02-version-control.md", 3: "03-diff-and-merge.md",
    4: "04-build-engine.md", 5: "05-caching.md", 6: "06-distributed-execution.md",
    7: "07-dependency-resolution.md", 8: "08-packaging-and-images.md", 9: "09-artifact-service.md",
    10: "10-supply-chain.md", 11: "11-secrets-and-encryption.md", 12: "12-search.md",
    13: "13-deployment-runtime.md", 14: "14-hot-update.md", 15: "15-consumer-sync-and-web.md",
    16: "16-universality.md", 17: "17-implementation.md", 18: "18-lake-service.md",
    19: "19-identity.md", 20: "20-secrets-service-and-pki.md", 21: "21-liquify-ide.md",
    22: "22-change-capture.md", 23: "23-metis-and-zetta.md", 24: "24-multiplayer-and-agents.md",
    25: "25-identity-attestation-and-transparency.md",
}
RESEARCH = {
    1: "01-version-control", 2: "02-large-files-and-binary-assets", 3: "03-structural-diff-and-formats",
    4: "04-build-systems", 5: "05-autotools-and-configure-era", 6: "06-build-and-compiler-caching",
    7: "07-distributed-execution", 8: "08-incremental-compilation", 9: "09-package-managers",
    10: "10-os-packaging", 11: "11-container-images", 12: "12-artifact-distribution",
    13: "13-supply-chain-security", 14: "14-secrets-and-encryption", 15: "15-binary-introspection",
    16: "16-monorepo-scale-and-authoring-loop", 17: "17-runtime-hot-update", 18: "18-implementation-cpp26",
    19: "19-full-text-search", 20: "20-deployment-runtime-k8s", 21: "21-consumer-sync-and-web",
    22: "22-forges-and-code-hosting", 23: "23-secrets-service-and-pki", 24: "24-editors-and-ide-architecture",
    25: "25-multiplayer-and-agent-collaboration", 26: "26-transparency-logs-and-anchoring",
}
PLAN = "https://github.com/oramasearch/liquid-bridge/blob/main/docs/action-plan.md"
DECISIONS = "https://github.com/oramasearch/liquid-bridge/blob/main/docs/decisions.md"


def feat(*ns):
    return ", ".join(f"[features/{FEATURES[n]}]({DOCS}/features/{FEATURES[n]})" for n in ns)


def res(*ns):
    return ", ".join(f"[research/{RESEARCH[n]}]({DOCS}/research/{RESEARCH[n]}/)" for n in ns)


def header(phase, spec="", research=""):
    line = f"**{phase}** · plan: [action-plan.md]({PLAN})"
    if spec:
        line += f" · spec: {spec}"
    if research:
        line += f" · research: {research}"
    return line + "\n\n"


def done(items):
    return "\n## Done when\n\n" + "\n".join(f"- [ ] {i}" for i in items) + "\n"


def sh(*args, check=True):
    r = subprocess.run(args, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"{' '.join(args[:4])}...: {r.stderr.strip()}")
    return r.stdout.strip()


LABELS = {
    "epic": "5319e7", "decision": "b60205", "ops": "0e8a16", "phase-0": "c5def5", "phase-1": "c5def5",
    "phase-2": "c5def5", "phase-3": "c5def5", "phase-4": "c5def5", "phase-5": "c5def5",
    "phase-6": "c5def5", "phase-7": "c5def5", "phase-8": "c5def5", "lake": "1d76db",
}


def ensure_labels(repo, names):
    have = {l["name"] for l in json.loads(
        sh("gh", "label", "list", "--repo", f"{ORG}/{repo}", "--limit", "100", "--json", "name"))}
    for n in names:
        if n not in have:
            sh("gh", "label", "create", n, "--repo", f"{ORG}/{repo}", "--color", LABELS.get(n, "ededed"),
               "--force")


def existing(repo):
    rows = json.loads(sh("gh", "issue", "list", "--repo", f"{ORG}/{repo}", "--state", "open", "--limit", "200",
                         "--json", "number,title,url"))
    return {r["title"]: r["url"] for r in rows}


created = []  # (repo, title, url)


def create(repo, title, body, labels, cache):
    if title in cache:
        url = cache[title]
        created.append((repo, title, url, "existing"))
        return url
    url = sh("gh", "issue", "create", "--repo", f"{ORG}/{repo}", "--title", title, "--body", body,
             "--label", ",".join(labels))
    cache[title] = url
    created.append((repo, title, url, "created"))
    return url


# ----------------------------------------------------------------------------------------------
# Issue definitions. Each: (repo, title, body, labels). Epics come later and reference these.
# ----------------------------------------------------------------------------------------------
L, K, LK, OP, BR = "liquid", "lake", "lake", "orama-operator", "liquid-bridge"

leaf = []

# ---------------- Phase 0 (bridge, decisions) ----------------
leaf.append((BR, "TAAP content-addressed subjects — the spec change that unblocks attribution of objects",
    header("Phase 0 — Decide", feat(25, 19), res(26)) +
    "TAAP/1 subjects are key-derived identifiers. Documents, drips, changes and artifacts are content-addressed "
    "and cannot hold keys, so nothing can be *attested about* them today. liquid's spec marks an object-subject "
    "form as required and blocking (TAAP open question 22.3) and records a suggested shape in features/25. "
    "This is a change to the TAAP spec, which needs the protocol owner, not a liquid design choice.\n"
    + done(["The TAAP spec defines a content-addressed subject form (algorithm-tagged digest) and how Authority→Subject "
            "attestations reference it.",
            "liquid's vendored copy under `docs/standards/` is refreshed and features/25 updated.",
            "Recorded in liquid `CLAUDE.md` *Decisions* and in the bridge `decisions.md`."]),
    ["decision", "phase-0"]))

leaf.append((BR, "Choose the open-source licence for liquid and liquify",
    header("Phase 0 — Decide", feat(23), "") + f"Posture is decided ([decisions.md]({DECISIONS}) §5): liquid and liquify are open source; "
    "lake, the operator and Zetta are not. The licence text is not chosen. Constraints: liquid never depends on Zetta; "
    "automerge-cpp is MIT; the k0s copy is Apache-2.0 with NOTICE obligations on distribution; a patent grant matters "
    "for a build system that companies embed.\n"
    + done(["Licence chosen (Apache-2.0, MIT or MPL-2.0 are the candidates) with the reason recorded in `decisions.md`.",
            "`LICENSE` added to `oramasearch/liquid` (and liquify when it exists); headers or a `NOTICE` policy decided.",
            "Contribution terms (DCO or CLA) decided before the repo goes public."]),
    ["decision", "phase-0"]))

leaf.append((BR, "Canonical home for automerge-cpp (homer6 vs oramasearch), MIT preserved",
    header("Phase 0 — Decide", feat(1, 24), res(25)) +
    "`automerge-cpp` is the one open component shared by liquid (open) and Zetta (closed). Zetta vendors it as a "
    "submodule from `homer6/automerge-cpp`. Decide whether it moves under `oramasearch` (public, MIT) or stays, and "
    "how both consumers pin it.\n"
    + done(["Home decided and recorded in `decisions.md` §2 and liquid `CLAUDE.md`.",
            "liquid and Zetta both point at the same remote; pins documented in the bridge `repositories.md`."]),
    ["decision", "phase-0"]))

leaf.append((BR, "Private patch carrier for beast2 (oramasearch/beast2, orama-main): silence keep-alive EOF noise",
    header("Cross-cutting", feat(17), "") +
    "beast2's worker prints `read_header error: end of stream` to stderr for every idle keep-alive connection a client "
    "closes (`src/http_worker.cpp:64`, a raw `std::cerr`, not the logger, so it cannot be configured away). In a pod "
    "that is one line per readiness probe; Zetta's pods show the same. lake consumes `cppalliance/beast2` directly at "
    "Zetta's pin `fb0a9c8`. The org pattern for this is a private patch carrier, like `oramasearch/corosio` "
    "(`orama-main`) and `oramasearch/http` (`zetta-patches`).\n"
    + done(["`oramasearch/beast2` created as a private copy (not a fork), `main` mirrors upstream, `orama-main` carries one "
            "commit: no message when `ec == http::error::end_of_stream` (or route through `log_service` at debug).",
            "lake's `.gitmodules` points at it; Zetta's pin considered by the Zetta owners.",
            "Upstream PR opened against cppalliance/beast2 with the same change.",
            "Bridge `repositories.md` lists the carrier next to corosio and http."]),
    ["ops"]))

leaf.append((BR, "lake.live: Cloudflare zone token and moving the Lake host off oramadev.net",
    header("Phase 0.5 follow-up", feat(18), "") +
    "`Lake/hello` is public at https://lake.oramadev.net because the only Cloudflare token Secret on the cluster is "
    "scoped to the `oramadev.net` zone. The `Lake` CR's `dnsSecretRef` reads `token` and `zoneID` from a Secret in "
    "`spec.namespace`, so a `lake.live` host needs a Secret for that zone.\n"
    + done(["`lake.live` DNS is on Cloudflare and proxied.",
            "A scoped API token (DNS edit on that zone only) stored as a Secret in `lake-dev`.",
            "`Lake/hello` re-pointed to a `lake.live` host; the `oramadev.net` record removed by gating off."]),
    ["ops", "phase-0"]))

leaf.append((BR, "AKS sandbox housekeeping after Phase 0.5",
    header("Phase 0.5 follow-up") +
    "Loose ends on `orama-production-cluster-01` from the hello-world deploy.\n"
    + done(["Decide the fate of the `juan` and `nine` `OramaZettaCluster`s (Steve: they can be deleted). Deleting them "
            "removes two Zetta StatefulSets, their public peer LoadBalancers and the `juan.oramadev.net` / "
            "`zetta.oramadev.net` records; the PVCs `data-juan-zetta-0` and `data-nine-zetta-0` (5Gi each) are retained "
            "and need an explicit delete.",
            "Delete the empty `buildkit` namespace, or keep it as the documented builder home.",
            "Delete the old `oramasearch/orama-cloud-v1-operator` Docker Hub repo once nothing pulls it (holds pre-rename builds).",
            "`Lake/hello` in `lake-dev`: keep as the standing demo or remove."]),
    ["ops", "phase-0"]))

# ---------------- Phase 1 — the store (liquid) ----------------
leaf.append((L, "Content-defined chunk store: FastCDC, BLAKE3, packs with range fetch, billion-entry index",
    header("Phase 1 — The store", feat(1), res(1, 2)) +
    "The base of everything. Files are cut with FastCDC (~64 KiB target), chunks are addressed by BLAKE3, grouped into "
    "packs (~64 MiB) that support HTTP range fetch, and indexed so a repository with a billion entries stays O(log n) "
    "to look up. A 40 GB file and a 40-byte file go through the same code path.\n"
    + done(["Chunker, hasher, pack writer/reader and index are libraries with unit tests and a fuzz target.",
            "Range fetch of one chunk out of a pack works over a plain HTTP server.",
            "Dedup measured on a real repository and on a directory of large binaries; numbers in the docs.",
            "Throughput and memory on a 40 GB file recorded; no whole-file buffering anywhere."]),
    ["phase-1"]))

leaf.append((L, "Object model with repository composition: nest, split, combine",
    header("Phase 1 — The store", feat(1, 2), res(1)) +
    "Repositories embed repositories as a first-class notion (the submodule replacement), can be split out again, and "
    "combined, without rewriting history. This cannot be added later, so the object model carries it from the first "
    "commit: trees reference repositories by identity, not by path copy.\n"
    + done(["A repository nested in another clones, updates and diffs as one tree.",
            "Split a nested repository out to standalone with history intact; combine two standalone repositories into one.",
            "History of the composition itself is versioned (when what was nested where)."]),
    ["phase-1"]))

leaf.append((L, "CRDT metadata layer over the store (automerge-cpp)",
    header("Phase 1 — The store", feat(1, 24), res(25)) +
    "Refs, change metadata, review state and collaborative documents are CRDT documents on automerge-cpp so that "
    "concurrent writers (people and agents) converge without a central lock. Blob data stays content-addressed; only "
    "metadata is CRDT.\n"
    + done(["automerge-cpp vendored at a pinned commit (home per the bridge decision).",
            "Refs and change metadata modelled as Automerge documents with a compaction story (epochs).",
            "Two replicas edit concurrently and converge in a test; document size growth per operation measured."]),
    ["phase-1"]))

leaf.append((L, "TAAP identity and signed drips from the first commit",
    header("Phase 1 — The store", feat(19, 25), res(13, 26)) +
    "Every drip (one captured write) is signed by the actor who made it, person or agent, using a TAAP/1 identity. "
    "Attribution is not a later feature: the drip format carries the signature and the actor's `taap:1:` identifier "
    "from day one. Attestations about objects wait on the spec change tracked in the bridge.\n"
    + done(["Key generation, `taap:1:<alg>:<base32>` identifiers, domain-separated signing and verification implemented "
            "over the vendored spec in `docs/standards/`.",
            "Drips are signed on capture and verified on read; an unsigned or tampered drip is rejected.",
            "Agent identities and delegation (an agent acting under a person's authority) round-trip.",
            "Enabled by default, with the documented opt-out."]),
    ["phase-1"]))

leaf.append((L, "Change capture: VFS journal primary, OS watchers fallback, atomic-save detection, write attribution",
    header("Phase 1 — The store", feat(22), res(21)) +
    "Every write to disk becomes a drip. The VFS journal is the primary source; inotify/fanotify, FSEvents and the USN "
    "journal are fallbacks with their documented limits (inotify watch caps, FSEvents coalescing, fanotify needing "
    "CAP_SYS_ADMIN). Atomic saves (write temp, rename) are recognised as one drip. Writes are attributed to the action "
    "that made them so a build's outputs are not mistaken for a person's edits.\n"
    + done(["Capture on Linux, macOS and Windows with the fallback chosen automatically and reported.",
            "Editor atomic saves from VS Code, Vim and Emacs produce one drip each.",
            "Auto-drip on by default; a debounced batch never splits a single logical save.",
            "Secret scanning runs on the drip path before anything leaves the machine."]),
    ["phase-1"]))

leaf.append((L, "Lazy clone and materialisation: the virtual filesystem",
    header("Phase 1 — The store", feat(1, 15), res(2, 21)) +
    "A clone is a manifest; bytes arrive on read. Backed by CFAPI on Windows, File Provider on macOS and FUSE on Linux, "
    "with a plain checkout mode for environments without a VFS. This is what makes a 40 GB asset and a monorepo both "
    "instant to open.\n"
    + done(["Clone of a large repository completes in seconds; first read of a file fetches only its chunks.",
            "Placeholder and hydration states visible to the user; offline reads of hydrated files work.",
            "Plain-checkout fallback produces a byte-identical tree."]),
    ["phase-1"]))

leaf.append((L, "Encrypted objects in the store: key- and password-protected data",
    header("Phase 1 — The store", feat(11), res(14)) +
    "Secrets and private data live in the repository as encrypted objects (age-style recipients: TAAP keys, passphrases), "
    "with per-object keys so a repository can mix public and protected content and grant access per recipient. Chunks of "
    "encrypted objects still dedup within the same key.\n"
    + done(["Encrypt/decrypt with a TAAP key and with a passphrase; recipients can be added without re-encrypting the payload.",
            "History and diff work on encrypted objects for holders of the key and degrade honestly for others.",
            "Key rotation documented and tested."]),
    ["phase-1"]))

leaf.append((L, "Garbage collection: leased roots, epoch marking, coupled lifetimes",
    header("Phase 1 — The store", feat(1), res(1)) +
    "Space is reclaimed without corrupting a live checkout: roots are leased by checkouts, builds and caches; marking runs "
    "by epoch; lifetimes of derived data (build outputs, indexes) are coupled to their sources.\n"
    + done(["GC reclaims unreferenced chunks while a checkout and a build are live, verified by a stress test.",
            "Leases expire and are renewed; a crashed holder does not pin space forever.",
            "`liquid gc --explain` says why a chunk is retained."]),
    ["phase-1"]))

leaf.append((L, "Build and test matrix: Linux, macOS, Windows from a clean clone",
    header("Phase 1 — The store", feat(16, 17), res(18)) +
    "liquid supports all languages, platforms and operating systems, so its own build must prove the three desktop "
    "platforms from the first phase. Clang 17+ everywhere; MSVC or clang-cl on Windows to be decided in this issue.\n"
    + done(["CI builds and tests on Linux (x86_64, arm64), macOS (arm64) and Windows (x86_64) from a clean clone.",
            "The compiler auto-selection in `CMakeLists.txt` covers each platform or fails with a clear message.",
            "Sanitizer job on Linux."]),
    ["phase-1"]))

# ---------------- Phase 2 — build core (liquid) ----------------
leaf.append((L, "Sandboxed action executor with observed dependencies",
    header("Phase 2 — The build core", feat(4), res(4, 6)) +
    "Actions run in a sandbox that records what they actually read, so dependencies are observed rather than declared. "
    "Undeclared reads are caught, not guessed. The executor is the unit everything else (cache, remote execution, "
    "incremental engine) builds on.\n"
    + done(["Sandbox on Linux (namespaces + seccomp or ptrace), macOS (sandbox-exec or VFS interposition) and Windows.",
            "An action's observed inputs are recorded as a content-addressed manifest.",
            "A test action that reads an undeclared file is flagged with the path."]),
    ["phase-2"]))

leaf.append((L, "Three-tier cache: memory, disk, remote, with signed entries and read-only developer defaults",
    header("Phase 2 — The build core", feat(5), res(6)) +
    "Build cache and compiler cache out of the box. Entries are keyed by the action's observed-input digest, signed by "
    "the producer, and served from memory, local disk or a remote. Developers read from the shared cache by default and "
    "write only what CI or a trusted builder produced.\n"
    + done(["Hit on a second machine for an unchanged action; miss explained (see `liquid why`).",
            "Cache entries verify against the producer's TAAP signature; an unsigned entry is not used.",
            "Remote tier speaks the same content-addressed protocol as the store (no second wire format)."]),
    ["phase-2"]))

leaf.append((L, "`liquid wrap` for CMake, Autotools, Make and compile_commands.json",
    header("Phase 2 — The build core", feat(4), res(4, 5)) +
    "The adoption path: an existing project builds under liquid unmodified. `liquid wrap` drives the existing build "
    "inside the executor, learns its actions from observed dependencies and from `compile_commands.json`, and caches "
    "them. Autotools and the configure era are first-class, not an afterthought.\n"
    + done(["An unmodified CMake project and an unmodified Autotools project build under `liquid wrap` with correct "
            "caching across two machines.",
            "Configure-time probes are captured as actions so `./configure` results are cached and invalidated correctly.",
            "Plain Makefiles work; recursive make is handled."]),
    ["phase-2"]))

leaf.append((L, "Reproducibility by construction, verified by sampled re-execution",
    header("Phase 2 — The build core", feat(4, 10), res(13)) +
    "Timestamps, paths, locale and randomness are controlled in the sandbox so actions are reproducible by construction; "
    "a sampled fraction of cache hits is re-executed and compared so non-determinism is detected instead of assumed away.\n"
    + done(["An injected non-determinism (a timestamp in an object) is detected by sampled re-execution and reported "
            "with the action and the differing bytes.",
            "Sample rate configurable; results feed the cache's trust of that action."]),
    ["phase-2"]))

leaf.append((L, "Provenance: a TAAP attestation for every action, automatically",
    header("Phase 2 — The build core", feat(10, 25), res(13)) +
    "Every executed action emits an attestation (who ran what, on which inputs, producing which outputs) signed by the "
    "builder's TAAP identity, SLSA-shaped, attached to the outputs in the store. No opt-in, no separate tool.\n"
    + done(["Attestations produced for local and cached actions and verifiable with `liquid verify <artifact>`.",
            "Object subjects use the content-addressed form once the TAAP spec change lands; until then the interim "
            "shape is documented as such."]),
    ["phase-2"]))

leaf.append((L, "`liquid why <target>`: name the input that caused a cache miss",
    header("Phase 2 — The build core", feat(5), res(6)) +
    "A miss is explained, not shrugged at: which observed input differed, between which two builds, and what changed it.\n"
    + done(["`liquid why` prints the differing input(s) with a diff pointer for text and a digest pair for binaries.",
            "Works across machines using the remote cache's recorded manifests."]),
    ["phase-2"]))

# ---------------- Phase 3 — distribution (liquid) ----------------
leaf.append((L, "REAPI v2 compatibility: BuildBarn, BuildBuddy, NativeLink, EngFlow unchanged",
    header("Phase 3 — Distribution", feat(6), res(7)) +
    "liquid speaks the Remote Execution API v2 as a client so any stock backend works, and exposes its own store through "
    "the REAPI CAS interface so backends can pull inputs without a translation layer.\n"
    + done(["A Phase 2 build runs against at least two stock REAPI backends with the same cache-hit rate as local.",
            "Conformance covered by the upstream REAPI test suite where one exists."]),
    ["phase-3"]))

leaf.append((L, "Build without the bytes as the only mode",
    header("Phase 3 — Distribution", feat(6), res(7)) +
    "Outputs of remote actions stay remote until something reads them. There is no download-everything mode; "
    "materialisation is on read, using the store's lazy VFS.\n"
    + done(["A remote build whose outputs are never read transfers no output bytes to the client.",
            "A deliberately non-hermetic action is caught at the read, not at the remote failure."]),
    ["phase-3"]))

leaf.append((L, "Toolchain in the input tree; local/remote racing with a cost model",
    header("Phase 3 — Distribution", feat(6, 7), res(7)) +
    "Compilers and tools are inputs like any other (content-addressed, so a remote worker gets exactly the local "
    "toolchain). The scheduler races local and remote execution using a cost model (queue depth, transfer size, cache "
    "locality) rather than a fixed policy.\n"
    + done(["The toolchain is materialised on a remote worker from the store with no image baking.",
            "Racing measured on a mixed workload; the cost model's inputs are observable in `liquid why`."]),
    ["phase-3"]))

leaf.append((L, "`liquid replay <action>`: reproduce any remote failure locally",
    header("Phase 3 — Distribution", feat(6), res(7)) +
    "Any action that failed remotely can be replayed locally from its recorded inputs, toolchain and environment, "
    "producing the same failure.\n"
    + done(["Replay of a remote failure reproduces the failure locally byte-for-byte in output.",
            "Works for cached actions too (replay a hit to check it)."]),
    ["phase-3"]))

# ---------------- Phase 4 — incremental engine + liquify stage 1 (liquid) ----------------
leaf.append((L, "Demand-driven query graph: fingerprints, red-green validation, early cutoff, durability tiers",
    header("Phase 4 — The incremental engine", feat(4), res(8, 16)) +
    "The Salsa/rustc-style engine: every derived value is a memoised query with an input fingerprint; validation is "
    "red-green so unchanged results are reused; early cutoff stops propagation when an intermediate result is identical; "
    "durability tiers keep stable inputs (toolchain, dependencies) from being revalidated on every keystroke.\n"
    + done(["A comment-only edit rebuilds nothing; a one-line change recompiles one TU and relinks.",
            "Graph persistence across daemon restarts; cold-start time measured on a large C++ tree."]),
    ["phase-4"]))

leaf.append((L, "The daemon: warm graph, drips invalidate the minimum, fan-out to build/search/collaborators/lake",
    header("Phase 4 — The incremental engine", feat(22, 17), res(16)) +
    "One long-lived process per checkout keeps the graph warm. Each drip invalidates exactly the queries that depend on "
    "the changed bytes and fans out: to the build, to remote execution, to the local search index, to collaborators, and "
    "to lake when configured. Watching is on by default.\n"
    + done(["Daemon lifecycle (start on first use, idle exit, single instance per checkout) on all three platforms.",
            "Fan-out targets are pluggable and observable (`liquid status` shows what a drip triggered).",
            "Memory ceiling and eviction policy for very large graphs."]),
    ["phase-4"]))

leaf.append((L, "Local full-text search index updated on drip (oramacore-cpp)",
    header("Phase 4 — The incremental engine", feat(12), res(19)) +
    "Search over the working tree and history runs locally on oramacore-cpp (BM25F plus the positional trigram index), "
    "indexed by blob once and updated by the daemon's drip fan-out. lake's hosted search (Phase 6) reuses the same "
    "index format.\n"
    + done(["`liquid search` answers over a large repository in interactive time; the index updates within a drip's fan-out.",
            "Blobs are indexed once regardless of how many paths or commits reference them.",
            "Search inside archives and known binary formats via the format registry when it lands (Phase 5)."]),
    ["phase-4"]))

leaf.append((L, "Continuous clean-rebuild validation against incremental results",
    header("Phase 4 — The incremental engine", feat(4)) +
    "Incremental correctness is proven, not trusted: a background clean rebuild is compared against the incremental "
    "graph's outputs on a sample, and any divergence is a reported bug with the query that was wrong.\n"
    + done(["Divergence detection with the offending query and inputs; zero divergences on the reference projects."]),
    ["phase-4"]))

leaf.append((L, "liquify stage 1: VS Code extension and LSP server backed by the query graph",
    header("Phase 4 — The incremental engine", feat(21), res(24)) +
    "The IDE starts as a VS Code extension plus an LSP server that answers from the same graph the build uses: instant "
    "open of any repository at any size (lazy VFS), diagnostics before the build finishes, no second parse. Lives inside "
    "`oramasearch/liquid` until it needs its own repository.\n"
    + done(["Open a large repository instantly; diagnostics and go-to-definition served from the graph.",
            "The extension shows drip and build status and never blocks on the daemon.",
            "Decision recorded on whether stage 1 is sufficient or native liquify (Phase 8) is needed."]),
    ["phase-4"]))

# ---------------- Phase 5 — resolution & projection (liquid) ----------------
leaf.append((L, "Spack-grade constraint solver (ASP): variants, virtual providers, compilers as dependencies, unsat cores",
    header("Phase 5 — Resolution and projection", feat(7), res(9)) +
    "Dependency resolution at Spack's level: an ASP/Clingo concretiser with variants, virtual providers, compilers and "
    "target architecture as first-class dependencies, and human-readable unsat-core explanations on conflict.\n"
    + done(["A 500-package tree resolves; a conflict produces an explanation a human can act on.",
            "Reuse of already-built configurations preferred by the solver (the Spack `reuse` behaviour)."]),
    ["phase-5"]))

leaf.append((L, "Content-addressed outputs: an identical rebuild terminates the cascade",
    header("Phase 5 — Resolution and projection", feat(5, 7), res(9)) +
    "Downstream rebuilds key on the content of an upstream output, not on the fact that it was rebuilt. A glibc patch "
    "that changes no output rebuilds nothing downstream.\n"
    + done(["Cascade termination demonstrated on a real dependency chain.",
            "Output normalisation rules (stripping, ordering) documented per artifact kind."]),
    ["phase-5"]))

leaf.append((L, "ABI extraction and diffing on every built library",
    header("Phase 5 — Resolution and projection", feat(7, 8), res(15)) +
    "Every built shared library gets its ABI extracted (abidw-style) and diffed against the previous build, so an ABI "
    "break is a build event, and the solver can reason about compatibility instead of version strings.\n"
    + done(["ABI descriptor stored with the artifact; `liquid abi diff` between two builds.",
            "An incompatible change flagged before packaging."]),
    ["phase-5"]))

leaf.append((L, "Projection to OCI images, .deb, .rpm, .apk and Helm charts (Tier A, installable)",
    header("Phase 5 — Resolution and projection", feat(8), res(10, 11)) +
    "A build projects into the formats the world installs from: deterministic OCI images with computed layers, and "
    "`.deb`, `.rpm`, `.apk` packages, plus Helm charts as OCI artifacts. Pinned digests and attached attestations "
    "throughout.\n"
    + done(["One build projects to a working `.deb`, an OCI image and a Helm chart with pinned digests and attestations.",
            "Byte-identical output for identical inputs across machines.",
            "Helm chart output validated by `helm lint` and an install on k0s."]),
    ["phase-5"]))

leaf.append((L, "Format registry with the first codecs: zip, tar, HDF5, Parquet, SQLite",
    header("Phase 5 — Resolution and projection", feat(3), res(3)) +
    "Diff inside containers and known binaries: a registry of format codecs that expose structure (entries, datasets, "
    "tables) so history, diff, merge and search see inside a zip, an HDF5 file or a SQLite database. Tier 2 for HDF5 "
    "(structural, not semantic merge).\n"
    + done(["Codecs for zip, tar, HDF5, Parquet and SQLite with a shared interface and tests on real files.",
            "`liquid diff` shows an entry-level diff for two zips and a dataset-level diff for two HDF5 files.",
            "Search (Phase 4) indexes inside archives through the registry."]),
    ["phase-5"]))

# ---------------- Phase 8 items (liquid) ----------------
leaf.append((L, "Multiplayer and agents: speculative replicas, semantic leasing, epoch compaction, scoped authority",
    header("Phase 8 — The rest", feat(24), res(25)) +
    "Google-Docs-style collaboration for people and AI agents on the same repository: agents work on private speculative "
    "replicas, semantic leases prevent two actors from fighting over one symbol, epochs compact CRDT history, and every "
    "agent's authority is scoped and attributable via TAAP delegation.\n"
    + done(["Two people and one agent edit concurrently; the agent's changes are attributed and its authority scoped.",
            "Lease conflicts surface in the editor; compaction keeps document size bounded (numbers recorded)."]),
    ["phase-8"]))

leaf.append((L, "liquify native, only if stage 1 proves insufficient",
    header("Phase 8 — The rest", feat(21), res(24)) +
    "A native editor is built only if the VS Code stage cannot deliver the multiplayer, agent and history surfaces. This "
    "issue holds the decision and, if taken, the plan.\n"
    + done(["Decision recorded with the evidence from stage 1."]),
    ["phase-8"]))

leaf.append((L, "Hot update, tiers 0–2, with restart as a first-class outcome",
    header("Phase 8 — The rest", feat(14), res(17)) +
    "Live update of running programs from drips where it is safe (tier 0: data/config; tier 1: leaf functions; tier 2: "
    "types with migration), and an honest restart when it is not. Restart is a first-class, fast outcome rather than a "
    "failure.\n"
    + done(["Tiers defined with their safety rules; a demo program takes a tier-1 update without restart and a tier-3 "
            "change with a restart, both driven by drips."]),
    ["phase-8"]))

# ---------------- Phase 6 — lake ----------------
leaf.append((LK, "How lake obtains Zetta: link zetta-api as a library vs copy the pattern",
    header("Phase 6 — lake", feat(18, 23), "") +
    "lake copies Zetta's serving shape today and has no source dependency on Zetta. Everything after hello world "
    "(control plane, observed state, auth, the Clerk issuer, clustering) wants Zetta linked as a library, which means "
    "Zetta becomes a module of lake and lake's build takes Zetta's. Decide this before Phase 6 work starts; also settle "
    "the port (4900 vs Zetta's 4800).\n"
    + done(["Decision recorded in lake `CLAUDE.md` *Open decisions* and the bridge `decisions.md`.",
            "If linked: Zetta added as a submodule at a pin, `lake-api` links `zetta-api`, build green from a clean clone.",
            "Read Zetta only from the orama-work bridge, per `CLAUDE.md`."]),
    ["decision", "phase-6"]))

leaf.append((LK, "Consume liquid's store as a library: the lake ↔ liquid boundary",
    header("Phase 6 — lake", feat(18, 1), "") +
    "lake hosts liquid repositories, so it embeds liquid's store (chunks, objects, drips, TAAP verification) as a library "
    "across the licence boundary: liquid stays open and Zetta-free; lake links it. Define the library surface liquid "
    "exports for this and keep it stable.\n"
    + done(["liquid exposes a `liquid::store` library target with a documented, versioned API.",
            "lake links it and serves a liquid repository's tree and history over `/v1`."]),
    ["phase-6"]))

leaf.append((LK, "Artifact registry and transparency log: OCI distribution, ecosystem views, witnessed tiled log, debuginfod",
    header("Phase 6 — lake", feat(9, 25), res(12, 26)) +
    "First lake surface. One deduplicated store served as an OCI registry and as ecosystem views (npm, PyPI, Maven, apt, "
    "models and datasets). Every artifact lands in a tiled transparency log with a mandatory M-of-N witness quorum "
    "(the primary defence against a split view); anchoring (OpenTimestamps) is an escalation, on by default and "
    "optional. debuginfod by build-id.\n"
    + done(["`docker pull` / `push` against lake; npm and PyPI installs from lake work unchanged.",
            "Inclusion proofs verifiable offline; a split-view test is detected by witnesses.",
            "debuginfod endpoint serves symbols for a lake-built artifact."]),
    ["phase-6"]))

leaf.append((LK, "Identity, secrets and PKI: TAAP identities, OIDC issuer and attester, short-lived certs, dynamic secrets, one CA",
    header("Phase 6 — lake", feat(19, 20), res(23)) +
    "lake is the auth provider (Clerk-like), the secrets store and the PKI issuer, all on TAAP identities: it issues OIDC "
    "tokens and attestations for TAAP keys, mints short-lived certificates *to* TAAP keys from one CA, and serves "
    "dynamic secrets with leases.\n"
    + done(["Sign in to lake with a TAAP key; lake acts as OIDC issuer for a third-party app.",
            "A short-lived cert issued to an agent's TAAP key; revocation and rotation exercised.",
            "Dynamic secret leased, renewed and revoked; audit trail in the transparency log."]),
    ["phase-6"]))

leaf.append((LK, "The forge: change-based review with cursors that survive rebase, no CI YAML",
    header("Phase 6 — lake", feat(18), res(22)) +
    "Review is per change (a named aggregation of drips), comments anchor to content and survive rebase, and there is no "
    "CI configuration: the build graph already knows what to run for a change.\n"
    + done(["Open a change from a drip stream, review it, land it; comments survive a rebase.",
            "Checks come from the graph, not from a YAML file; a change page shows what was built and attested."]),
    ["phase-6"]))

leaf.append((LK, "Search: oramacore-cpp BM25F + positional trigram index, indexed by blob once, change-atomic publication",
    header("Phase 6 — lake", feat(12), res(19)) +
    "Hosted search over every repository's history and inside artifacts, on the same index format liquid uses locally. "
    "Publication is change-atomic: a change's index is visible all at once or not at all.\n"
    + done(["Code search across all hosted repositories with regex and symbol queries in interactive time.",
            "Search inside artifacts (archives, packages) via the format registry.",
            "Index cost per blob measured; blobs indexed once across repositories."]),
    ["phase-6"]))

leaf.append((LK, "Models and datasets: the Hugging Face surface with training provenance on the chunk store",
    header("Phase 6 — lake", feat(18, 9), res(2, 12)) +
    "Models and datasets are artifacts like any other: large files on the chunk store, versioned, deduplicated across "
    "revisions, with training provenance attached as attestations (data, code, run). Hub-compatible API surface where it "
    "matters for tooling.\n"
    + done(["Push and pull a multi-GB model with chunk-level dedup between revisions.",
            "Provenance chain from dataset to model verifiable with `liquid verify`.",
            "`huggingface_hub`-style client flows work against lake for the common operations."]),
    ["phase-6"]))

leaf.append((LK, "The drive: CFAPI, File Provider, FUSE; three-tree reconciler; version history as a query",
    header("Phase 6 — lake", feat(15), res(21)) +
    "The Dropbox/Google Drive surface for people who do not think in commits: a folder that syncs, on the same store, "
    "with the web view. The reconciler is the three-tree model (base, local, remote); every version is a query over "
    "history, not a separate feature.\n"
    + done(["A regular user installs the client, drops a folder, shares it, and sees history on the web.",
            "Conflicts produce two named versions, never a silent overwrite.",
            "The same folder is a repository a developer can clone with liquid."]),
    ["phase-6"]))

leaf.append((LK, "Web UI beyond hello: server-rendered pages for repositories, changes and artifacts",
    header("Phase 6 — lake", feat(18), res(22)) +
    "The self-contained, server-rendered web UI (Zetta's approach) grows from the hello page into the forge, registry "
    "and drive views. No script by default; a bundle only where interaction needs it.\n"
    + done(["Repository, change, artifact and search pages rendered from `web_ui.cpp` renderers with unit tests.",
            "Accessibility pass; pages usable without JavaScript."]),
    ["phase-6"]))

leaf.append((LK, "lake as an OpenAPI + MCP surface (`/v1/openapi.json`, `POST /mcp`) like Zetta",
    header("Phase 6 — lake", feat(18, 24), "") +
    "Zetta exposes every capability as REST under `/v1`, an OpenAPI document and an MCP endpoint so agents can use it "
    "directly. lake follows the same shape so agents are first-class users of the forge, registry and drive.\n"
    + done(["`/v1/openapi.json` generated from the capability registry; `POST /mcp` serves the same capabilities.",
            "An agent completes a review round-trip through MCP with its TAAP identity attributed."]),
    ["phase-6"]))

# ---------------- orama-operator (Phase 6.4 + Phase 7 + follow-ups) ----------------
leaf.append((OP, "[lake] Land the Lake CR (PR #118) and rebuild the sandbox image from main",
    header("Phase 0.5 follow-up", feat(18)) +
    "AKS runs the PR branch image `oramasearch/orama-operator:lake-crd-01a31d5` (helm revision 5). PR #118 "
    "(https://github.com/oramasearch/orama-operator/pull/118) carries the `Lake` CRD, controller, tests, chart RBAC, the "
    "image-repo rename and the CRD reference. Review, merge, and rebuild `v1-sandbox` from `main` so production is not "
    "on a branch.\n"
    + done(["PR #118 reviewed and merged.",
            "`build/images/build.sh --push operator` from the orama-cloud-v1-bridge produces the image from `main`; "
            "`helm upgrade` to it; pod digest verified.",
            "`Lake/hello` still Ready afterwards."]),
    ["lake", "p2"]))

leaf.append((OP, "[lake] Rename Go module path, chart name and helm release to orama-operator",
    header("Phase 0.5 follow-up") +
    "The GitHub repo and the Docker Hub repo are `orama-operator`; the Go module path, `chart/Chart.yaml` name and the "
    "helm release/Deployment name still read `orama-cloud-v1-operator`. Renaming the release means uninstall and "
    "reinstall on a production cluster, so this is a deliberate, scheduled step.\n"
    + done(["Go module path renamed with `gofmt -r`-style import rewrite; `go build ./...` green.",
            "Chart renamed; helm release migrated on AKS with the lease name preserved or a documented cutover.",
            "Bridge `repositories.md` and the operator docs updated."]),
    ["lake", "p3"]))

leaf.append((OP, "[lake] Observed state for Lake in the operator's Zetta datastore (orama_control)",
    header("Phase 6 — lake", feat(23, 18)) +
    "The operator records observed state for its CRs in Zetta (`orama_control.components`, `reconcile_events`, "
    "append-only, anti-flap). `Lake` should do the same so lake's operational state lives beside Zetta's, per the "
    "decision that lake's operator uses its own Zetta store just like the Zetta operator does.\n"
    + done(["Lake reconciles write component rows and reconcile events with the existing best-effort, retried, "
            "fingerprinted path.",
            "Covered by the datastore e2e (operator#100) or a Lake-specific case."]),
    ["lake", "p2"]))

leaf.append((OP, "[lake] Production hardening of the Lake Deployment: resources, liveness, PDB, TLS",
    header("Phase 6 — lake", feat(18)) +
    "The hello-world Deployment has a readiness probe and nothing else. Before the Lake CR reconciles a real service: "
    "resource requests/limits, a liveness probe on `/v1/server_info`, a PodDisruptionBudget for replicas > 1, TLS at the "
    "Ingress rather than only at Cloudflare, and a non-root security context matching the image.\n"
    + done(["Spec fields for resources and TLS added with defaults; probes and PDB rendered.",
            "`Lake/hello` on AKS passes a `kubectl rollout restart` with no dropped requests."]),
    ["lake", "p3"]))

leaf.append((OP, "[lake] Reconcile the whole lake service on k0s: the enterprise on-prem install path",
    header("Phase 6 — lake", feat(18, 13), res(20)) +
    "Phase 6 exit: a customer installs k0s and orama-operator on their own hardware, applies one `Lake` resource, and has "
    "a private forge + registry + identity provider whose every artifact verifies against a witnessed log, with no "
    "connection to `lake.live` required. The `Lake` CR grows from one Deployment to the service's components (lake, "
    "Zetta state, storage, ingress, witnesses).\n"
    + done(["Install runbook: k0s + operator chart + one `Lake` CR on a fresh machine.",
            "Air-gapped install verified (no `lake.live` reachability).",
            "A `LakeE2ETest` CR drives the deployed service the way `ZettaClusterE2ETest` does."]),
    ["lake", "epic", "p2"]))

leaf.append((OP, "[lake] Deploy on drip and preview environments per change",
    header("Phase 7 — The runtime", feat(13), res(20)) +
    "The operator side of the runtime: a drip in a repository produces a running preview environment through the fan-out, "
    "not a CI trigger; environments are cheap because images share chunks; teardown is tied to the change's lifecycle.\n"
    + done(["A change in a lake-hosted repository yields a preview environment with a URL in the change page.",
            "Environment image differs from the previous one by only the chunks that changed."]),
    ["lake", "p3"]))

# ---------------- k0s (Phase 7) ----------------
leaf.append((K if False else "k0s", "Upstream sync: keep `main` a pristine mirror and rebase the `liquid` branch",
    header("Ongoing", "", "") +
    "`oramasearch/k0s` is a private copy (not a fork) of `k0sproject/k0s`. `main` mirrors upstream; `liquid` carries our "
    "changes; the `upstream` remote's push URL is disabled. Define the cadence and the script so the copy never drifts "
    "silently, and keep GitHub Actions disabled on the copy.\n"
    + done(["A documented `sync.sh` fetches upstream, fast-forwards `main`, rebases or merges `liquid`, and reports conflicts.",
            "Sync run at least at each upstream release; `ORAMA-FORK.md` records the last synced tag.",
            "Licence obligations on distribution (Apache-2.0 `LICENSE`, `NOTICE`, stated changes) checked by the script."]),
    ["ops", "phase-7"]))

leaf.append(("k0s", "Run the Lake CR on k0s (the Phase 0.5 exit's second half)",
    header("Phase 0.5 → Phase 7", feat(13, 18)) +
    "Hello world was met on AKS. The same `Lake` object should reconcile on our k0s build: install the operator chart on "
    "a single-node k0s from the `liquid` branch and apply the sample.\n"
    + done(["Single-node k0s from `go build ./cmd/k0s` runs the operator chart and `Lake/hello` answers HTTP.",
            "Differences from AKS (ingress controller, storage class, LoadBalancer) recorded in the runbook."]),
    ["phase-7"]))

leaf.append(("k0s", "Chunk-aware node integration: nodes fetch only the chunks they lack, across images",
    header("Phase 7 — The runtime", feat(13, 8), res(11, 20)) +
    "The drip-aware distro's core change: the node's image store understands liquid chunks, so pulling a new image "
    "transfers only chunks the node does not already hold, regardless of which image had them. A containerd snapshotter "
    "or image-service plugin backed by the store.\n"
    + done(["A rebuilt image whose change is one file transfers only that file's chunks to a node.",
            "Works with stock OCI images (falls back to layers) and with liquid-projected images (chunk-level)."]),
    ["phase-7"]))

leaf.append(("k0s", "Attestation verification at admission: what runs is what was attested",
    header("Phase 7 — The runtime", feat(10, 13), res(13)) +
    "An admission policy verifies a workload's image against its TAAP attestations and the transparency log before it "
    "runs. An unattested or unverifiable image is refused, with the reason in the event.\n"
    + done(["Unattested image refused at admission; attested image admitted; policy configurable per namespace.",
            "Verification uses lake's log inclusion proofs and works offline with a cached checkpoint."]),
    ["phase-7"]))

leaf.append(("k0s", "Talos-style immutable node model on k0s, with a real break-glass path",
    header("Phase 7 — The runtime", feat(13), res(20)) +
    "Nodes are immutable images managed declaratively; configuration is applied, not edited; upgrades are image swaps. "
    "A documented, audited break-glass path exists because the alternative is people finding their own.\n"
    + done(["Node image built by liquid's projection; upgrade by replacing the image with rollback.",
            "Break-glass access issues a short-lived cert from lake's CA and is logged in the transparency log."]),
    ["phase-7"]))

leaf.append(("k0s", "Railway-style platform surface on the distro: deploy, logs, env, domains from one place",
    header("Phase 7 — The runtime", feat(13), res(20)) +
    "The distro exposes the platform features people use Railway for: deploy from a repository on drip, service logs, "
    "environment and secrets (from lake's secrets store), custom domains with certificates, and preview environments, "
    "all driven by the `Lake` CR and lake's web UI rather than a separate PaaS layer.\n"
    + done(["From lake's UI: deploy a repository, see logs, set an env var, attach a domain; each is a CR under the hood.",
            "Secrets come from lake's dynamic secrets, never from plain k8s Secrets typed by hand."]),
    ["phase-7"]))

# ----------------------------------------------------------------------------------------------
# Pass 1: leaves
# ----------------------------------------------------------------------------------------------
repos = sorted({r for r, *_ in leaf} | {L, LK, OP, BR, "k0s"})
caches = {}
for r in repos:
    ensure_labels(r, sorted({lab for rr, _, _, labs in leaf if rr == r for lab in labs} | {"epic"}))
    caches[r] = existing(r)

urls = {}
for r, title, body, labels in leaf:
    urls[(r, title)] = create(r, title, body, labels, caches[r])
    print(f"  {r}: {urls[(r, title)]}  {title[:70]}", flush=True)


def links(repo, phase_label):
    out = []
    for r, title, _, labels in leaf:
        if r == repo and phase_label in labels and "epic" not in labels:
            out.append(f"- [ ] {urls[(r, title)]} — {title}")
    return "\n".join(out)


# ----------------------------------------------------------------------------------------------
# Pass 2: phase epics
# ----------------------------------------------------------------------------------------------
EPICS = [
    (L, "[epic] Phase 1 — The store", "phase-1",
     "Exit: a repository can be created, written to, nested inside another, split out again, and cloned lazily; every "
     "drip is signed; a 40 GB file and a 40-byte file are handled by the same code path; GC reclaims space without "
     "corrupting a live checkout."),
    (L, "[epic] Phase 2 — The build core", "phase-2",
     "Exit: an existing CMake or Autotools project, unmodified, builds under `liquid wrap` with correct caching across "
     "two machines, and every artifact carries a verifiable attestation. Sampled re-execution detects an injected "
     "non-determinism."),
    (L, "[epic] Phase 3 — Distribution", "phase-3",
     "Exit: a Phase 2 build runs against a stock REAPI backend with the same cache hit rate as local, and a deliberately "
     "non-hermetic action is caught at the read, not at the remote failure."),
    (L, "[epic] Phase 4 — The incremental engine and liquify stage 1", "phase-4",
     "Exit: a one-line change in a large C++ project recompiles one translation unit and relinks in the time a save "
     "takes; the editor shows the diagnostic before the build finishes; a comment-only edit rebuilds nothing."),
    (L, "[epic] Phase 5 — Resolution and projection", "phase-5",
     "Exit: a dependency tree of 500 packages resolves with a human-readable explanation on conflict; a glibc patch that "
     "changes no output rebuilds nothing downstream; one build projects to a working `.deb`, OCI image and Helm chart "
     "with pinned digests and attached attestations."),
    (L, "[epic] Phase 8 — Multiplayer, native liquify, hot update", "phase-8",
     "Exit: defined per item when Phase 7 is done. Do not plan these in detail before then."),
    (LK, "[epic] Phase 6 — lake", "phase-6",
     "In order, because each surface depends on the one before: registry + transparency log; identity, secrets, PKI; "
     "the forge; the `Lake` CR reconciling the whole service on k0s (tracked on orama-operator); search; models and "
     "datasets; the drive. Exit: a customer installs k0s and orama-operator on their own hardware, applies one `Lake` "
     "resource, and has a private forge + registry + identity provider whose every artifact verifies against a "
     "witnessed log, with no connection to `lake.live` required."),
    ("k0s", "[epic] Phase 7 — The runtime (k0s `liquid` branch)", "phase-7",
     "Exit: a drip in a repository produces a running preview environment, and the environment's image differs from the "
     "previous one by only the chunks that changed; an unattested image is refused at admission."),
]
epic_urls = {}
for r, title, label, exit_text in EPICS:
    body = header(title.replace("[epic] ", "")) + exit_text + "\n\n## Issues\n\n" + links(r, label) + "\n"
    if r == LK:
        body += "\nOn orama-operator:\n" + "\n".join(
            f"- [ ] {urls[(OP, t)]} — {t}" for rr, t, _, labs in leaf if rr == OP and "phase" not in " ".join(labs)) + "\n"
    if r == "k0s":
        body += "\nOn orama-operator:\n" + "\n".join(
            f"- [ ] {urls[(OP, t)]} — {t}" for rr, t, _, labs in leaf if rr == OP and "Deploy on drip" in t) + "\n"
    epic_urls[title] = create(r, title, body, ["epic", label], caches[r])
    print(f"  {r}: {epic_urls[title]}  {title}", flush=True)

# Bridge tracking epic
phase0 = "\n".join(f"- [ ] {urls[(BR, t)]} — {t}" for r, t, _, labs in leaf if r == BR)
tracking = header("liquid — the whole plan") + (
    "One place that points at every phase epic. Order is forced by dependencies: the forge, the IDE and the consumer "
    "drive are the payoff and every one of them depends on the store, the graph and the daemon being right first. "
    "No durations; a phase is done when its exit criterion is met.\n\n"
    "Phase 0.5 (hello world, every component) was met on AKS on 2026-09-02: `Lake/hello` runs the real lake image at "
    "https://lake.oramadev.net via the operator; liquid and k0s build; PR #118 open.\n\n"
    "## Decisions and follow-ups (this repo)\n\n" + phase0 + "\n\n## Phase epics\n\n" +
    "\n".join(f"- [ ] {epic_urls[t]} — {t}" for _, t, _, _ in EPICS) + "\n")
turl = create(BR, "[epic] liquid — the plan, phase by phase", tracking, ["epic"], caches[BR])
print(f"  {BR}: {turl}  tracking epic", flush=True)

with open(OUT, "w") as f:
    f.write("repo\tstatus\turl\ttitle\n")
    for r, t, u, s in created:
        f.write(f"{r}\t{s}\t{u}\t{t}\n")
print(f"\n{len(created)} issues recorded in {OUT}")
print(f"tracking epic: {turl}")
