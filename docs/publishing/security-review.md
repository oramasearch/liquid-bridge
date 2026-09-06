# Security review — threat model for liquid and liquify before publication

**For:** https://github.com/oramasearch/liquid-bridge/issues/11, under
https://github.com/oramasearch/liquid-bridge/issues/16.
**Basis:** liquid `a5659bc` and liquify `e7b47ee` (`main`, 2026-09-05), read in full for the components
below; file and line references are to those commits. Companion: [`scrub-report.md`](scrub-report.md)
(confidentiality) and [`SECURITY.md.draft`](SECURITY.md.draft) (disclosure policy). The specification
this review holds the code to is liquid's `docs/features/10-supply-chain.md`,
`11-secrets-and-encryption.md`, `22-change-capture.md`, `25-identity-attestation-and-transparency.md`
and the `docs/library/*.md` implementation notes; each invariant quoted below is from those documents.

## 1. What is being protected

liquid opens repositories it did not create, runs build tools it does not trust inside a sandbox, speaks
to remote caches and to lake over the network, signs everything with per-user keys, and encrypts
selected content with keys it custodies. liquify opens the same repositories in an editor and runs the
same graph in-process. The assets, in the order an attacker would want them:

1. **Signing keys** — the TAAP/1 Ed25519 identity key under `$LIQUID_HOME/identity/` and, later,
   agent and hardware keys. Compromise forges attribution, provenance and every "verified" result.
2. **Data keys and KEKs** — trust-domain encryption keys (`<store>/keys/*.wrapped`) and the passphrase
   or key file that wraps them. Compromise reads encrypted content, including `.env` and JSON leaves.
3. **The host** — the developer's machine or the worker node. A sandbox escape or a hostile
   repository that executes code on open is the worst outcome for a tool whose pitch is "open anything".
4. **Cache and attestation integrity** — a build result served from cache without verification, or a
   forged attestation accepted by policy, silently corrupts every downstream artifact.
5. **Repository content and metadata** — confidentiality of encrypted subtrees; integrity of history.
6. **Availability** — a malformed record, frame or file that crashes the daemon, the editor or a
   server, or makes them allocate without bound.

## 2. Trust boundaries

```
                 ┌──────────────────────── host (developer machine / worker node) ────────────────────────┐
  repository ──▶ │ B1  libliquid parsers   B2  sandbox / VFS ◀── untrusted build tool (LD_PRELOAD hook,   │
  bytes (files,  │     (CBOR, packs, LSM,      (unshare+bind mounts on Linux, sandbox-exec on macOS,       │
  names, Git,    │      JSON/.env, Git,         FUSE mount, ptrace read guard)                            │
  attestations)  │      regexes, identity)                                                                 │
                 │ B3  daemon Unix socket ◀── other local processes / other local users                    │
                 │ B5  key material on disk, $LIQUID_TOKEN in environment                                   │
                 └───────────────┬───────────────────────────────────────────────────────────────────────┘
                                 │ B4 network: sync client ↔ lake / `serve sync`; REAPI client ↔ CAS and
                                 │    execution backends; `serve reapi`; scheduler ↔ workers (own HTTP/2,
                                 │    gRPC framing, protobuf codec, TLS via Corosio + OpenSSL, bearer token)
  B6 supply chain: 5 submodules (3 private), 8 FetchContent sources, system OpenSSL/zlib/FUSE, CI runners
  B7 liquify: repository bytes → tree-sitter C/C++ (external scanner) and hand-written decoders of
     `.liquid/liquify-graph` state that lives inside the opened (untrusted) repository; future plugin ABI
     and AI surface (neither exists yet)
```

| Boundary | Trusted side | Untrusted side | Crossing |
|---|---|---|---|
| **B1** | libliquid | repository content: file bytes and names, canonical-CBOR records (drips, changes, directory documents, attestations, identity documents), pack frames and index runs on disk, Git object stores, JSON/`.env` documents, encryption path rules including user regexes, wrapped-key headers | every `open`, `read`, `import`, `verify` |
| **B2** | liquid executor, host filesystem | the build tool and everything it spawns; the wrap hook runs *inside* it | `posix_spawn` of `unshare`/`sandbox-exec`; FUSE requests; LD_PRELOAD/DYLD_INSERT_LIBRARIES |
| **B3** | the daemon (holds the graph, the capture subscription, and drives builds) | any process that can connect to the socket | framed CBOR requests over `AF_UNIX` |
| **B4** | client or server | the peer: lake, a REAPI backend, a stock Bazel, a worker | HTTP/1.1 (`oramasearch/http`), HTTP/2 + gRPC framing + protobuf (liquid's own), TLS (Corosio/OpenSSL) |
| **B5** | the user | other users on the host, child processes, backups | files under `$LIQUID_HOME`, `<store>/keys`, `.liquid/`, environment variables |
| **B6** | the build | upstream repositories, CDNs, package archives, GitHub Actions | `git submodule`, `FetchContent`, `apt`, `brew`, `choco`, `actions/*` |
| **B7** | liquify | the repository being edited; later, plugins and model providers | `liquid::repository::read`, tree-sitter, `.liquid/liquify-graph` |

## 3. Components: what each must never do, what enforces it, and where it is thin

Each section: the **invariants** (quoted from the docs — these are the promises a report is judged
against), the **controls** found in code, and the **findings** (numbered F1…, collected in §5).

### 3.1 The store (chunker, packs, LSM index, canonical CBOR, encryption at rest)

Code: `include/liquid/store.hpp`, `src/store/{chunker,pack,index,store_impl,collector,compactor,leases}.cpp`,
`src/encoding/cbor.cpp`, `src/objects/records.cpp`, `src/hash.cpp`, `src/hash/sha256.c`.

**Must never**
- return bytes whose digest was not verified: "Reading verifies each chunk's digest after decompression";
  "acknowledged ⊆ visible ⊆ correct" (`docs/library/store.md`);
- return ciphertext as content, or zeroes in place of missing data (`store.md`, `vfs.md:104-106`);
- trust an on-disk index over the packs: the index "is a cache with no write-ahead log of its own,
  always rebuildable from the packs" (`CLAUDE.md` decision 8);
- let compaction change identity: "compaction never decompresses, recompresses, or recalculates its
  identity";
- write plaintext of an encrypted object into a pack (`encryption.md`).

**Controls.** Every pack frame carries algorithm byte + 32-byte digest and is re-hashed after zstd
decompression; unknown format markers are refused with `errc::unsupported`; corrupt manifests or run
headers fall back to rebuilding from pack tables; unsealed packs recover by frame scan stopping at the
first invalid frame; range reads from remote blob sources are length-checked and hashed per chunk and
per object. Canonical CBOR rejects non-canonical encodings and checks declared lengths against the
remaining input before `reserve` (`src/encoding/cbor.cpp:238,266,269,281,284`). The deterministic crash
simulator (`tests/sim/`, `src/store/faults.cpp`, 200 seeds) runs under ASan/UBSan in CI. BLAKE3 is
FetchContent 1.8.7 built portable-only; SHA-256 (`src/hash/sha256.c`) and SHA-1 (`src/git/sha1.cpp`,
Git interop only) are in-tree implementations.

**Findings.**
- **F7 — no nesting-depth limit in the CBOR decoder.** `src/encoding/cbor.cpp` bounds lengths but has no
  depth counter; a record with deeply nested arrays or maps recurses until the stack is exhausted.
  Records arrive over sync (B4) and from repositories (B1). Add a depth cap (64 is generous for liquid's
  schemas), reject beyond it, and fuzz the decoder (§7.1).
- **F17 — decompression bounds on store and sync frames.** Delta apply caps the zstd window at 2³¹ and
  refuses unknown content size before allocating (`src/delta.cpp:34,123-127`); confirm the same two
  checks on the pack-frame reader and on `LQFRAME1` sync entries, whose raw size is a `u32` — a frame
  claiming 4 GiB raw for 1 KiB compressed must be refused before allocation, not after.
- **F20 — own hash implementations.** `sha256.c` and `sha1.cpp` are small and tested against vectors
  (`tests/test_hash.cpp`), but they are not fuzzed or sanitizer-instrumented (the sanitizer job
  instruments C++ only, F10). Compare against OpenSSL on random inputs in a test; it is already linked.

### 3.2 The sandbox, the VFS and the `liquid wrap` hook

Code: `include/liquid/build.hpp`, `src/sandbox/{linux,macos,windows}.cpp`, `src/sandbox/read_guard.c`,
`src/sandbox/wrap_hook.c`, `src/vfs/fuse_fs.cpp`, `src/build/{executor,wrap}.cpp`.

**Must never**
- let an action read outside its declared inputs and toolchain or write outside its declared outputs:
  "A write outside the declared outputs is a sandbox violation, reported with the path"; Linux = "user +
  mount + pid + net namespaces… the sandbox root bind-mounted as the only visible filesystem besides
  `/proc` and a private `/tmp`"; macOS = "`sandbox-exec` profile denying file reads outside the mount
  and the fixed toolchain path, denying network… the same guarantee with a weaker tool"
  (`build-engine.md:229-231`);
- let the environment leak in: "fixed and minimal, nothing inherited";
- serve a cached result the recorded inputs do not justify (`docs/library/build-engine.md`,
  `reapi.md`: an ActionCache hit "cannot skip candidate, manifest, signature, provenance, SBOM, or
  referenced-object validation");
- manufacture data at the mount: "The caller never receives zeroes, an empty substitute, or
  ciphertext" (`vfs.md:104-106`).

**Controls.** Linux: `posix_spawn("/usr/bin/unshare", --user --map-root-user --mount --pid --fork --net,
/bin/sh, <script>)` (`src/sandbox/linux.cpp:274-308`) with process-group kill on timeout; macOS: a
generated SBPL profile `(deny default) (deny network*)` plus subpath allows (`src/sandbox/macos.cpp:26-70`);
Windows: `errc::unsupported`, documented. Repository paths reject absolute paths and `.`/`..`
components at the repository layer (`src/repository/repository_impl.cpp:1068-1077`,
`src/crdt/schema.cpp:69-77`) and again in executor, provenance, SBOM, `why`, search and graph code; the
REAPI server rejects names containing `/`. Tests: `Build.denies_reads_outside_the_mount`,
`rejects_writes_outside_declared_outputs`, `has_fixed_environment`, `terminates_the_process_group_on_timeout`,
`BuildCache.unsigned_newest_candidate_is_never_served` (`tests/build/test_executor.cpp:734-1264`) — all
in the privileged FUSE container, **which is not part of `.github/workflows/ci.yml`**.

**Findings.**
- **F2 — the sandbox definition is generated text from repository-controlled strings.** Linux writes a
  `/bin/sh` bootstrap (`linux.cpp:83-199`) quoting each value with a single-quote escaper
  (`linux.cpp:28-37`; correct for POSIX `sh`). macOS writes an SBPL profile whose `escaped()`
  (`macos.cpp:18-24`) **escapes only `"`, not `\`**: a path or argument containing a backslash followed
  by a quote, or a newline, can terminate the string literal and inject a `(allow …)` form. Paths come
  from the action record, which comes from the repository. Fix: escape `\` before `"`, reject control
  characters and newlines in any value written into a profile or script, and prefer passing values by
  environment or a NUL-separated file read by a fixed script over generating code. Add a test with
  hostile path names on both platforms.
- **F3 — the wrap hook trusts a plan file and environment variables, and re-validates inputs with a
  64-bit non-cryptographic hash.** `wrap_hook.c` is injected via `LD_PRELOAD` / `DYLD_INSERT_LIBRARIES`
  (`src/build/wrap.cpp:2122-2130,2564-2571`); its constructor parses the plain-text plan at
  `$LIQUID_WRAP_PLAN` and, on a hit, `_exit`s with the recorded status *without running the compiler*.
  Conditional rows re-check an input by size + FNV-1a (`wrap_hook.c:44-51,152`). FNV-1a collisions are
  trivial to construct, so a repository author who controls a conditional input can make a changed file
  match a stale plan row and have a stale object served as the build of the new source — a silent
  integrity failure in the one place liquid promises correctness by construction. Fix: BLAKE3 (already
  linked; a C implementation is in tree via FetchContent) for the row fingerprint, and bind the plan to
  the run (a per-run random key in a 0600 file, HMAC over each row) so a plan cannot be planted.
  `LIQUID_WRAP_HOOK`, `LIQUID_WRAP_PLAN`, `LIQUID_WRAP_ROOT`, `LIQUID_READ_GUARD` override binary and
  plan locations (`wrap.cpp:463`, `linux.cpp:57-73`); document them as developer overrides and ignore
  them when the effective uid differs from the file owner.
- **F4 — the read guard is a hermeticity aid, not a security boundary, and should say so.**
  `read_guard.c` traces `open`/`openat`/`openat2` only (`:204-212`), prefix-matches an allow-list
  (`:198-243`), handles x86_64 and aarch64, and is applied only to `remote_eligible` actions. It does
  not see `execve`, `stat`, `readlink`, `getdents`, `mmap` of inherited descriptors, `io_uring`, or
  `openat` relative to a directory fd opened before the check. That is fine for its purpose (catching
  non-hermetic builds at the read) but the docs should state that the namespace/bind-mount layer is the
  enforcement and the guard is diagnostic.
- **F16 — Windows has no sandbox, no mount, no key-file permission check and no daemon.** All
  documented; `wrap` refuses with `errc::unsupported`. The public README must say this in the first
  screen, not in a library note.
- **F21 — `/proc` is visible inside the Linux sandbox** (`build-engine.md:229`). With `--pid` the tool
  sees only its own tree, but `/proc/self/environ`, `/proc/sys` and `/proc/net` (empty under `--net`)
  are readable; confirm nothing host-identifying leaks into a "reproducible" action, and mask
  `/proc/sys/kernel/random/boot_id` and friends if reproducibility is claimed across machines.

### 3.3 The sync protocol and the lake client and server

Code: `include/liquid/sync.hpp`, `src/sync/{codec,server,session,endpoint}.cpp`, `src/cli/{sync,serve}.cpp`.

**Must never**
- change state before every frame is validated: "the receiver parses every frame, verifies each actor
  identifier and TAAP signature, checks each change digest and referenced object… A validation failure
  rejects the selected import";
- trust the client's view of history: "The callback never trusts a client-provided fast-forward claim";
- leak the credential: "credentials never appear in the URL or output"; `LIQUID_TOKEN` is "never
  printed" (`docs/cli/README.md:102`);
- let an exception cross the coroutine boundary: "A callback task error or thrown exception refuses
  every ref with its message; no exception leaves the coroutine boundary".

**Controls.** Frame type + 4-byte length + canonical CBOR, `maximum_frame_size = 16 MiB`
(`src/sync/codec.cpp:18,200,378`), pack-entry sizes bounded to `uint32` and both raw and compressed sizes
checked (`:462-469,494`); unknown types, truncation, bytes after the end frame and missing end frames are
rejected; encrypted physical frames are never sent; TAAP signatures verified before import; fast-forward
recomputed server-side. Tests: `bad_signature_rejects_the_complete_batch`,
`ThrowingAuthorizerRefusesEveryReferenceAndKeepsObjects`, `AtomicPushRefusesEveryReferenceWhenOneIsRefused`,
`DivergentReferenceUpdateIsNotFastForward` (`tests/test_sync.cpp`).

**Findings.**
- **F6 — `liquid serve sync` ships with no authentication, and uploads land in the CAS before
  authorization.** Default bind `127.0.0.1:8080` (`src/cli/serve.cpp:311`); "Without that flag the
  command supplies no authentication policy" (`docs/library/sync.md:195`); "Object uploads happen before
  authorization and remain in the content-addressed store regardless of every outcome" (`sync.md:173`).
  Both are documented and deliberate (content-addressed objects are harmless data), but together they
  mean any peer that can reach the port can fill the disk. Before publication: refuse to bind a
  non-loopback address without an authorizer; add a per-connection and per-identity upload quota; make
  the unauthenticated-upload property explicit in the CLI help.
- **F13 — the bearer token lives in the environment.** `LIQUID_TOKEN` (`src/cli/sync.cpp:49`) is
  readable in `/proc/<pid>/environ` by the same user and is inherited by every child, including the
  daemon the CLI spawns with `environ` (`src/cli/daemon.cpp:103`). Acceptable for a first release if
  documented; plan a token file (0600) or OS keychain, and have the daemon scrub `LIQUID_TOKEN` from its
  own environment at start.
- **F22 — HTTP/1.1 lake client.** Certificate verification and redirect handling of the
  `oramasearch/http` adapter (`src/sync/endpoint.cpp`) were not reviewed here; confirm `verify_peer`
  defaults on, hostnames are checked against SAN, redirects to a different origin drop the
  `Authorization` header, and HTTP (not HTTPS) URLs are refused unless loopback.

### 3.4 REAPI, HTTP/2, gRPC framing, protobuf codec, scheduler and workers

Code: `include/liquid/{remote,reapi,workers}.hpp`, `src/reapi/*`, `src/protobuf/wire.cpp`, `src/http2/{connection,frame,hpack,grpc}.cpp`,
`src/workers/*`.

**Must never**
- speak REAPI over TLS without ALPN `h2` ("TLS connections require the peer to negotiate `h2` with ALPN
  before any REAPI request is sent", `reapi.md`);
- publish to a remote cache by default ("Publication is read-only by default");
- accept a worker completion that does not match the active lease ("rejects a completion whose
  operation, token, worker, scheduling record, or signature differs from the active lease",
  `workers.md`);
- emit credentials into HPACK's dynamic table ("Custom headers are marked sensitive for HPACK when they
  are credentials").

**Controls.** Frame length above the peer's `SETTINGS_MAX_FRAME_SIZE` rejected (`src/http2/connection.cpp:91`),
SETTINGS values validated into `[16384, 16777215]` (`:205`), padding checked (`:492`), 24-bit length and
31-bit stream id enforced (`src/http2/frame.cpp:21,25`), HPACK table-size updates above the negotiated
maximum rejected (`hpack.cpp:500`); protobuf wire decoder rejects field 0, bad wire types, over-long
varints, truncated values, unmatched groups (`tests/reapi/test_wire.cpp:65`) and keeps unknown fields
byte-for-byte; REAPI symlink nodes validated and absolute symlinks disallowed (`src/reapi/server.cpp:383-388,523`);
`tls.verify_peer` defaults true, mTLS optional. Interop against NativeLink, BuildBarn and stock Bazel is
scripted in `tools/reapi-peers/` — Docker-gated and **not in CI**.

**Findings.**
- **F18 — HTTP/2 resource limits to confirm and fuzz.** The parser bounds frames; review and test the
  remaining classic DoS vectors on `serve reapi` and the scheduler's control surface: concurrent-stream
  cap and `RST_STREAM` flood (rapid reset, CVE-2023-44487), `CONTINUATION` flood with no `END_HEADERS`,
  `SETTINGS` flood, `PING` flood, HPACK dynamic-table growth and Huffman decode of hostile literals,
  per-connection header-list size, flow-control window abuse (slow read). Each is a fuzz target and a
  unit test (§7.1).
- **F23 — `serve reapi` accepts prior-knowledge h2c and expects a TLS terminator in front** (`reapi.md`).
  Same treatment as F6: refuse non-loopback plaintext unless `--allow-plaintext` is given, and say so in
  `--help`.
- **F24 — workers execute what the scheduler hands them.** The scheduler is authenticated to workers by
  TAAP signature over the lease; confirm the worker refuses an action whose inputs are not reachable
  from the lease's signed root, that worker roots are wiped between actions, and that the size-class
  fleet cannot be steered to run a different worker's action by replaying a lease token (there is a
  bounded requeue; check the token is single-use).

### 3.5 Identity, attestations, signatures, policy

Code: `include/liquid/{identity,attestation}.hpp`, `src/identity.cpp`, `src/identity/taap.cpp`,
`src/attestation/registry.cpp`, `src/build/{provenance,policy,verify}.cpp`.

**Must never**
- accept an unregistered profile: "An unregistered profile is invalid, including when its signature is
  otherwise valid… Do not add an unregistered-profile fallback" (`attestations.md:3-6,83-85`);
- infer the algorithm from the key: TAAP §"MUST NOT infer the algorithm from key length"; unknown
  digest prefixes and signature schemes are `errc::unsupported`, ML-DSA's tag is rejected
  (`hash-agility.md`);
- trust a channel or a filename: "A Verifier MUST NOT grant any trust based on the channel a message
  arrived on" (TAAP §); policy "never trusts a filename, unsigned side table, or caller-provided claim…
  No rule passes because evidence is unavailable… a `refuse` rule fails closed" (`policy.md`);
- let one signer satisfy a quorum: "`min_count` counts distinct verified issuer identities, not records";
- reinterpret an old signature under a new form: "do not silently reinterpret existing signatures"
  (`provenance.md`);
- accept a signature after rotation: "A signature from that key at or after `declared_at` is invalid";
  the old private key is overwritten "only after the successor is signed" (`identity.md`).

**Controls.** Ed25519 and SHA-512/256 from Monocypher 4.0.3 pinned by SHA-256 in `CMakeLists.txt:148-150`;
domain separation `"TAAP/1 " + artifact_type || 0x00 || canonical_cbor(body)` with `signature_purpose`
checked against the artifact type; identifiers are full SHA-512/256 fingerprints in base32, length and
alphabet checked (`src/identity.cpp:~283`); signer wipes secret material on destruction
(`crypto_wipe`, `src/crypto/crypto.cpp:63-65`); RFC 8032 and NIST vectors in `tests/test_identity.cpp:77,84`;
policy tests include `invalid_signature_never_satisfies_a_requirement`,
`unknown_attestation_profile_is_rejected_at_configuration_time`,
`reproducibility_quorum_counts_distinct_verified_identities`, `refusal_happens_before_the_action_spawns`
(`tests/build/test_policy.cpp:196-302`).

**Findings.**
- **F19 — the protocol is a draft and the subject form is interim.** TAAP/1 is vendored as a draft;
  content-addressed subjects use an "interim result-body digest" until the spec defines the object
  form (bridge decisions §4, liquid `provenance.md:120-124`). Every verifier must key on the versioned
  profile name so the interim form can be retired without reinterpreting old signatures — the docs say
  this; the review should confirm no code path accepts a `slsa_provenance/1` body under a future
  profile name.
- **F25 — clock dependence.** Attestation `max_age` (24 h for `scan_result/1`), revocable status
  windows, rotation `declared_at`, and GC leases all use the local clock ("a clock jump can extend or
  shorten retention", `gc.md:24-28`). Document the trust in the local clock; where a verifier can, use
  the newest signed timestamp it has seen as a floor (monotonic guard) so a rolled-back clock cannot
  revive an expired attestation.
- **F26 — delegation and agent keys are not implemented yet** but are specified as "attenuation-only
  with depth limits… the confused-deputy risk is real" (`features/25:330`). When they land, they are a
  new trust boundary and need their own review; note it now so the first implementation PR carries a
  threat-model section.

### 3.6 Secrets, encryption and the CLI's handling of keys

Code: `src/crypto/crypto.cpp`, `src/encryption/leaf.cpp`, `src/formats/{json,dotenv}.cpp`, `src/scan/detectors.cpp`,
`src/identity.cpp` (keyring, providers, wrapped-key file), `src/cli/*`.

**Must never**
- write plaintext at a path declared encrypted: liquid "refuses to record plaintext at a path declared
  encrypted, and verifies stored content rather than working-tree content" (`features/11`);
  leaf mode returns `errc::unsupported` for formats other than `.json`/`.env` "instead of risking
  plaintext storage" (`leaf-encryption.md`);
- decrypt implicitly: `repository::read` "never decrypts leaf values implicitly";
- let a storage server test guesses: "Chunk ids are `blake3k` keyed digests, so a storage server cannot
  test a guessed plaintext" (`encryption.md`);
- cache unwrapped data keys: "each unwrap is consumed and wiped by the caller before the operation
  returns";
- disclose the secret it found: "Raw matched values never cross this directory's interface"
  (`src/scan/README.md`); attestations and diagnostics omit the matched value;
- replace the OS random source: "Do not replace the operating-system random source with a counter or
  deterministic input" (`src/crypto/crypto.cpp:31-60` uses `arc4random_buf` / `getrandom` /
  `BCryptGenRandom`, `#error` otherwise);
- read a world-readable key file: "the file must have mode `0600`; other modes return `unauthorized`"
  (`src/identity.cpp:1094-1099`).

**Controls.** XChaCha20-Poly1305 and Argon2i from Monocypher; BLAKE3 keyed and derive-key for chunk MACs,
chunk keys and KEK wrapping with fixed context strings (`src/identity.cpp:49`); the JSON-Pointer key
path is associated data so an envelope moved to another key fails authentication
(`tests/encryption/test_leaf.cpp:92`); strict in-tree JSON and `.env` parsers (no third-party parser);
scanner is a set of bounded matchers, not a regex engine; tests cover plaintext refusal, rotation,
wrong-KEK-changes-no-files, redaction making prior objects unreadable.

**Findings.**
- **F5 — the identity key's wrapping key is stored in cleartext beside the sealed key.**
  `$LIQUID_HOME/identity/<fp>.key` is XChaCha20-Poly1305-sealed under a random 32-byte key written to
  `$LIQUID_HOME/identity/.wrapping.key` (`src/identity.cpp:387-411`); `write_private` sets 0600 on POSIX
  and **does nothing on Windows** (`:251-271`, `#if !defined(_WIN32)` at `:265`). The sealing therefore
  protects against nothing a file read does not also defeat; it is at-rest formatting, not
  confidentiality. Before publication either (a) say so plainly in `identity.md` and the CLI help
  ("your signing key is protected by file permissions"), or (b) wrap with a passphrase-derived key or
  the OS keystore (Keychain / DPAPI / `libsecret`), which the `key_provider` interface in #170/#51
  already anticipates. Windows needs an ACL equivalent of 0600 before any key is written there.
- **F8 — Argon2 parameters are read from the wrapped-key file header.** `LQKEY\x02` carries memory,
  iterations and lanes (`src/identity.cpp:110-170`); a hostile store (cloned from a peer) can request
  gigabytes of memory or hours of hashing on open. Cap the accepted parameters (for example ≤ 1 GiB,
  ≤ 16 passes) and refuse above with `corrupt`.
- **F9 — `encrypted_regex` is `std::regex` over attacker-influenced input.** Encryption path rules
  are repository configuration; the patterns and the JSON-Pointer paths they are matched against both
  come from the repository. `std::regex` (ECMAScript) backtracks catastrophically on crafted patterns.
  Bound the pattern (length, no nested quantifiers) or switch to the in-tree glob matcher only.
- **F27 — no interactive passphrase prompt exists** (`encryption.md`: rotate/keys/revoke wiring is
  assigned to #119; `docs/cli/README.md` lists only `identity [show|rotate]`). Until it does, any
  passphrase flows through arguments or environment; make sure no code path accepts a passphrase on
  the command line (visible in `ps`), and document that key files are the supported custody for now.
- **F28 — the secret scanner is a control, not a boundary.** Blocking by default is good; its detector
  set (AWS, GitHub, Slack, Google, private keys, JWT, generic and dotenv assignments) will miss much.
  State the false-negative posture in the docs so users do not treat "scan passed" as "no secrets".

### 3.7 The daemon and its client protocol

Code: `include/liquid/daemon.hpp`, `src/daemon.cpp`, `src/daemon/fanout.cpp`, `src/cli/daemon.cpp`, `src/graph.cpp`.

**Must never**
- serve a second daemon for one checkout (advisory `flock` on `.liquid/daemon/lock`);
- let a client drive another user's checkout;
- lose or replay a fan-out cursor: "Every target persists its own journal cursor only after successful
  delivery. Replayed or duplicate cursor values are ignored" (`incremental-engine.md`);
- exceed its memory ceiling (`daemon_options::graph_memory`, 256 MiB default, `daemon.hpp:58-60`).

**Controls.** Framed requests (1-byte type, 4-byte length, canonical CBOR) reuse the sync codec's
bounds; idle shutdown; single instance by `flock`; Windows returns `errc::unsupported` until Corosio has
named pipes. Tests: `tests/test_daemon.cpp`, `BuildEvents.daemon_client_preserves_the_stream`.

**Findings.**
- **F1 — the daemon socket is at a predictable, shared-directory path with no peer check.**
  `endpoint_path()` = `temp_directory_path() / ("liquid-daemon-" + first 24 hex of BLAKE3(checkout path) + ".sock")`
  (`src/daemon.cpp:1537-1547`) — derived only from the checkout path, no per-user or random component,
  in the system temp directory shared by all users. `open_listener` (`:1011-1052`) does
  `std::filesystem::remove(endpoint)` → `bind` → `listen` → `chmod(0600)`: the socket exists with the
  umask-derived mode between `bind` and `chmod`, and the unconditional `remove` deletes whatever another
  user planted at that name. `accept_request` (`:1053-1076`) reads the first frame with **no
  `SO_PEERCRED` / `LOCAL_PEERCRED` uid check and no token**. On a multi-user host (CI runners, shared
  dev boxes, a worker node) another user who can guess the checkout path can (a) pre-create the socket
  and impersonate the daemon to the CLI, or (b) connect during the window and issue `build_*`,
  `pause_capture`, `shutdown`. Fix: create the socket inside a 0700 directory the daemon owns
  (`$XDG_RUNTIME_DIR/liquid/` on Linux, `~/Library/Application Support/liquid/` or a 0700 temp dir on
  macOS — the short-path problem is solved by hashing the path, which is already done); set
  `umask(077)` around `bind`; check the peer uid on every accepted connection and refuse others; write
  a random per-daemon token into `.liquid/daemon/` (0600) and require it in the first frame so a
  planted socket cannot be trusted by the CLI. Add a test that a connection from a different uid is
  refused (can be simulated with `SO_PEERCRED` mocking or skipped when not root).
- **F29 — the daemon inherits the CLI's full environment** (`posix_spawn(..., environ)`,
  `src/cli/daemon.cpp:103`), including `LIQUID_TOKEN` (F13) and any `LD_PRELOAD`. Pass an explicit
  minimal environment.

### 3.8 Delta delivery, Git import and export

**Must never** treat decompression success as verification: "Apply first verifies the supplied source
and patch-blob digests, reconstructs the bytes, and verifies the target digest before writing a
destination. A decompression success is not sufficient" (`distribution.md`). **Controls:** fixed 108-byte
`LQDLTA` record parsed with bounds checks (`src/delta.cpp:340-350,56-62`), zstd window capped, content
size required and bounded (`:34,123-127`), `delta/1` attestation verified with subject = expected
target before the patch is loaded (`:182-212`). Git import parses hostile `.git` directories with zlib:
every object SHA-1 verified before use, delta instructions size-checked before reconstruction, 32 MiB
index and delta caches, eight-file pack-stream cache, 1,000,000-entry memo cap (`git-interop.md`);
tests refuse corrupt loose objects (`tests/git/test_object_store.cpp:94`).

**Finding F30 — Git is the largest untrusted binary format liquid parses today**, with a long public
CVE history in every implementation (pack delta chains, index v2, `OFS_DELTA` offsets, zlib bombs,
`.gitmodules` and symlink tricks on export). It has no fuzzer here. It is the first fuzz target in §7.1
after CBOR. There are no zip or tar codecs yet (Phase 5); when they land they inherit this section
(zip-slip, symlink escape, decompression bombs, duplicate names).

### 3.9 liquify — plugins

There is **no plugin ABI, no dynamic loading and no module registration in liquify today**: no `dlopen`,
`LoadLibrary`, `system`, `popen`, `exec*` or `getenv` in `src/`, `bench/` or `tests/`. The only extension
point is liquid's in-process `query_registry`, which liquify populates with C++ lambdas
(`src/interactive_analysis.cpp:1506-1575`, `src/stub_tree.cpp:483-490`); "no query crosses the daemon
socket" (`docs/editor/interactive-analysis.md:65-69`). The plugin ABI is bridge decision 14 ("a small
stable plugin ABI over liquid's query graph… no VS Code extension API compatibility") and liquify #3
(Phase 8).

**Must never, when it exists:** load code from the repository being edited or from a path the
repository controls; run a plugin with the editor's signing identity or its file access by default;
treat a plugin's query results as more trusted than repository content. **Design requirements to
record in liquify #3 before the first line:** plugins are installed by the user from a per-user
directory, never discovered inside a repository or its `.liquid/`; each plugin is content-addressed and
its digest is pinned in user configuration; plugins run out of process (a subprocess speaking the same
framed CBOR the daemon uses) so a crash or a hang is contained and capabilities can be granted per
plugin; the ABI carries no raw pointers into the editor; the same rules apply to liquid's frontend
modules (`liquid #65`, versioned C ABI) and to Tier 2 grammars, whose in-tree-or-fetched decision
(`liquid #72`) is a supply-chain decision.

### 3.10 liquify — the AI surface

**Nothing is implemented.** No socket, HTTP client, TLS client, model provider, API key or prompt exists
in liquify's `src/`; the only outbound activity is CMake `FetchContent` at configure time and whatever
libliquid's daemon does. The surface is liquify #10 ("AI as a first-class but switch-off-able surface,
fed by the real graph… one switch turns the whole surface off and nothing leaves the machine"), the
structural edit API (bridge decision 30: public libliquid API, liquify #8), agent presence (liquify #3)
and the agent model in liquid `features/24` and #30.

**Must never, when it exists:** send repository content, symbol tables, build errors or paths to a model
provider unless the user has turned the surface on for that repository (default off; the switch is
per repository, not global, because one repository under NDA is enough); log or persist prompts or
completions inside the repository (`.liquid/` is captured and synced — an exclusion is not enough,
keep them in the per-user cache); hold a provider API key in the repository or in liquify's own
files (use libliquid's key custody or the OS keystore); apply a model-proposed edit without the same
TAAP attribution an agent gets — the edit is signed as the agent's, scoped by the same
attenuation-only delegation, and lands as drips the user can undo (`features/24`); accept
instructions embedded in repository content (comments, README, build output) as user intent —
prompt injection through the graph is the specific new risk of "fed by the real graph", and the
mitigation is that graph content is data in the prompt, never a channel for commands, with the
structural edit API rejecting edits outside the leased scope. Record these in liquify #10 as
acceptance criteria.

### 3.11 liquify — what exists today

Code: `src/app.cpp`, `editor_buffer.cpp`, `editor_graph.cpp`, `interactive_analysis.cpp`, `stub_tree.cpp`,
`repository_view.cpp`, `main.cpp`. CMake pins SDL3 `release-3.2.0`, Dear ImGui `v1.91.5` (mutable tags),
GoogleTest 1.17.0 by URL **without `URL_HASH`**, tree-sitter 0.26.13 / C 0.24.2 / C++ 0.23.4 as submodules,
liquid as a submodule pinned to a private commit.

**Must never:** execute anything from the repository it opens; write outside the repository; sign with
anything but the user's identity (it supplies none — `write(file, contents)` is unauthenticated at the
liquify layer, libliquid's identity signs; `src/editor_buffer.cpp:426`); trust the repository's names.

**Findings.**
- **F14 — repository-controlled names and bytes are used with no validation at the liquify layer.**
  Entry names are concatenated into paths with `/` (`src/app.cpp:729`) and used as `read`/`write`
  paths and ImGui ids without rejecting `..`, `/`, `\`, NUL or control characters — liquify relies
  entirely on libliquid's path validation (which exists, §3.2). Blobs are loaded whole into memory and
  laid out with no size cap or binary check (`src/editor_buffer.cpp:23-52,84-101`); go-to-definition
  auto-opens whatever path a graph result names (`src/app.cpp:560-563`); `--print-tree` prints names
  unescaped (`src/main.cpp:29-41`, terminal escape injection). Every `.c/.cc/.cpp/.h/.hpp` blob is fed
  to tree-sitter's C and C++ grammars including the C++ **external scanner** (`CMakeLists.txt:102-103`)
  — the largest native attack surface reachable from repository content, with **no fuzzing or sanitizer
  coverage in liquify's CI**. Fix: a size cap with a "binary or too large" state, name validation at the
  view layer (defence in depth), escape on `--print-tree`, and run tree-sitter under ASan in CI
  (upstream has fuzzers; reuse their corpora).
- **F15 — persisted analysis state lives inside the untrusted repository and is deserialised on
  open.** `InteractiveAnalysis::open(repository_path / ".liquid" / "liquify-graph")`
  (`src/editor_graph.cpp:86`); the hand-written little-endian decoders bounds-check lengths correctly
  but call `reserve(*count)` on attacker-controlled counts before reading elements
  (`src/stub_tree.cpp:126,142`, `src/interactive_analysis.cpp:746,754,769,778,851,955,1025`) — a
  `0xFFFFFFFF` count is an immediate `bad_alloc` — and `static_cast` enum values without range checks
  (`stub_tree.cpp:132`, `interactive_analysis.cpp:674,862,1036`). A cloned hostile repository ships this
  state. Fix: move the cache to a per-user directory keyed by repository digest (the daemon's
  `.liquid/daemon/` has the same exposure in liquid — F1's directory move covers both), or ignore state
  not written by the current user; cap counts by remaining input before `reserve`; validate enums.
- **F31 — detached threads.** `EditorGraph` detaches `std::thread`s capturing a raw `Impl*`
  (`src/editor_graph.cpp:71-79`) and waits on a counter in `~Impl` (`:48-56,156-159`). Not a security
  boundary, but a TSan run (§7.2) is the cheap way to know whether the shutdown ordering is sound.

## 4. Supply chain and build (B6)

| Item | liquid | liquify | Risk |
|---|---|---|---|
| Submodules | `capy` (public, `develop`), `corosio` (**private** patch carrier), `automerge-cpp` (**private**), `http` (public fork, `zetta-patches`), `oramacore-cpp` (**private**) — pinned by commit | `liquid` (**private**), tree-sitter ×3 (public) — pinned by commit | Private submodules block an anonymous clone; SSH URLs in both `.gitmodules` block even a public one (scrub report §3.4, §3.10) |
| FetchContent | Boost core libs 1.91.0-1 by **URL without hash**; BLAKE3 `1.8.7`, zstd `v1.5.7`, tree-sitter `v0.25.9` + grammars, googletest `v1.17.0` by **tag**; **Monocypher by URL with SHA-256** (the one done right, `CMakeLists.txt:148-150`) | SDL3 `release-3.2.0`, ImGui `v1.91.5` by tag; googletest 1.17.0 tarball **without `URL_HASH`** | A moved tag or a compromised mirror changes the build silently; pin every FetchContent by commit SHA (git) or `URL_HASH` (archives) |
| System libraries | OpenSSL 3, zlib, libfuse3 (Linux), macFUSE (optional) | OpenSSL, zlib, FUSE3 (via liquid) | Track CVEs; OpenSSL is in the TLS path |
| CI toolchain | clang-19 from `apt.llvm.org`; `brew`, `choco` unversioned | `curl https://apt.llvm.org/llvm.sh \| sudo sh` unpinned; `choco upgrade llvm` unversioned | Remote script as root; pin the LLVM version and verify the script's hash, or use the runner's image toolchain |
| GitHub Actions | `actions/checkout@v4`, `actions/cache@v4` by major tag; `persist-credentials` left default so `ORAMA_SUBMODULES_TOKEN` stays in `.git/config` for every later step | same | Pin actions by commit SHA; `persist-credentials: false`; the token goes away when submodules are public |
| Sanitizers | Linux ASan+UBSan job on `CMAKE_CXX_FLAGS` only (`ci.yml:142-144`) — **C sources uninstrumented** (`sha256.c`, `read_guard.c`, `wrap_hook.c`, BLAKE3, Monocypher, zstd, tree-sitter); no `-fno-sanitize-recover`; no TSan/MSan | none | F10 |
| Fuzzing | none; `AUTOMERGE_CPP_BUILD_FUZZ` forced `OFF` (`CMakeLists.txt:316`) although automerge-cpp ships `fuzz_leb128`, `fuzz_load`, `fuzz_change_chunk` | none | F10 |
| Hardening flags | none: no `-Wall -Wextra`, `-fstack-protector-strong`, `_FORTIFY_SOURCE`, `_GLIBCXX_ASSERTIONS`/libc++ hardening, RELRO/`-z now`, CFI; `.clang-format` yes, `.clang-tidy` no | `-Wno-deprecated-declarations`, ImGui with `-w` | F10 |
| Not in CI | privileged FUSE container suite (all sandbox tests), Docker REAPI/h2c/TLS interop, worker proof, `large`/`sim-long`/`realworld` labels, shared-library build | — | The sandbox's own tests do not run on a PR |
| Licence, NOTICE | `NOTICE` lists third parties; no `LICENSE` | neither | Bridge #2 |

**F10** and **F11** in §5 collect this table.

## 5. Findings

Severity is the reviewer's judgement of impact if published as-is; "Pub" marks what must change before
the repositories go public, the rest are the first issues to open.

| Id | Sev | Pub | Finding | Where |
|---|---|---|---|---|
| F1 | High | yes | Daemon socket at a predictable shared-tmp path; `remove`→`bind`→`chmod` ordering; no peer uid or token check | `src/daemon.cpp:1011-1076,1537-1547` |
| F2 | High | yes | Sandbox profile/script generated from repository strings; macOS escaper handles `"` only | `src/sandbox/macos.cpp:18-70`, `linux.cpp:28-199` |
| F3 | High | yes | Wrap hook re-validates inputs with FNV-1a and trusts a plan file selected by env var; can serve stale results for changed inputs | `src/sandbox/wrap_hook.c:44-51,152,158-193`, `src/build/wrap.cpp:463,2122-2130` |
| F5 | Medium | yes (document) | Identity key wrapping key stored in cleartext beside the sealed key; no permission enforcement on Windows | `src/identity.cpp:251-271,387-411` |
| F6 | Medium | yes | `serve sync` unauthenticated by default; CAS accepts uploads before authorization | `src/cli/serve.cpp:311`, `docs/library/sync.md:173,195` |
| F7 | Medium | yes | CBOR decoder has no nesting-depth limit | `src/encoding/cbor.cpp` |
| F8 | Medium | | Argon2 parameters accepted from the wrapped-key file header without caps | `src/identity.cpp:110-170` |
| F9 | Low | | `std::regex` over repository-supplied encryption rules | `src/encryption/leaf.cpp`, `repository_impl.cpp` |
| F10 | High | yes | No fuzzers; sanitizers on C++ only; no TSan/MSan; no hardening flags; automerge-cpp fuzzers disabled; sandbox tests not in CI | `.github/workflows/ci.yml:113-152`, `CMakeLists.txt:316`, `docs/build/ci.md:64-91` |
| F11 | Medium | yes | FetchContent by tag or hashless URL; actions by major tag; `persist-credentials` default; unpinned LLVM install | both `CMakeLists.txt`, both `ci.yml` |
| F12 | Medium | yes | Committed TLS private key (test fixture) | `tools/reapi-peers/nativelink-tls-key.pem` (scrub report §3.5) |
| F13 | Low | | `LIQUID_TOKEN` in environment, inherited by the daemon | `src/cli/sync.cpp:49`, `src/cli/daemon.cpp:103` |
| F14 | Medium | | liquify: unvalidated names and unbounded blobs; tree-sitter on untrusted input with no sanitizer/fuzz coverage; unescaped `--print-tree` | `src/app.cpp:560-563,729`, `src/editor_buffer.cpp:23-101`, `src/main.cpp:29-41` |
| F15 | Medium | | liquify: analysis cache inside the untrusted repository; `reserve(count)` from input; unchecked enums | `src/editor_graph.cpp:86`, `src/stub_tree.cpp:126-142`, `src/interactive_analysis.cpp:674-1036` |
| F16 | Info | yes (document) | Windows: no sandbox, mount, daemon, or key-file mode check | `src/sandbox/windows.cpp`, `src/identity.cpp:265` |
| F17 | Medium | | Confirm decompression bounds on pack and sync frames match the delta path's | `src/store/pack.cpp`, `src/sync/codec.cpp:462-494` |
| F18 | Medium | | HTTP/2 DoS vectors (rapid reset, CONTINUATION/SETTINGS/PING floods, HPACK growth, slow read) to test | `src/http2/*` |
| F19 | Info | | TAAP is a draft; interim subject form must be retired by profile version, never reinterpreted | `docs/library/provenance.md:120-124` |
| F20 | Low | | In-tree SHA-256/SHA-1 uninstrumented and unfuzzed | `src/hash/sha256.c`, `src/git/sha1.cpp` |
| F21 | Low | | `/proc` visible in the Linux sandbox; host identifiers may leak into "reproducible" actions | `docs/library/build-engine.md:229` |
| F22 | Medium | | HTTP/1.1 lake client: verify TLS hostname check, redirect credential stripping, plaintext refusal | `src/sync/endpoint.cpp` |
| F23 | Low | | `serve reapi` plaintext h2c on non-loopback without an explicit flag | `src/reapi/server.cpp`, `docs/library/reapi.md` |
| F24 | Medium | | Worker lease token single-use and input reachability from the signed root to confirm | `src/workers/*` |
| F25 | Low | | Local clock trusted for expiry, rotation, leases | `docs/library/gc.md:24-28`, registry `max_age` |
| F26 | Info | | Delegation/agent keys unimplemented; require a threat-model section on the implementing PR | `docs/features/25:330` |
| F27 | Low | | No passphrase prompt; ensure no CLI-argument passphrase path | `docs/library/encryption.md`, `docs/cli/README.md` |
| F28 | Info | yes (document) | Scanner false-negative posture | `docs/library/secret-scanning.md` |
| F29 | Low | | Daemon spawned with the CLI's full environment | `src/cli/daemon.cpp:103` |
| F30 | High | yes (fuzz) | Git object store parser unfuzzed | `src/git/object_store.cpp` |
| F31 | Low | | liquify detached threads; run TSan | `src/editor_graph.cpp:48-79,156-159` |

## 6. Known open items already tracked

| Issue | Relevance |
|---|---|
| liquid #204 `liquid secret seal` (X25519 + ChaCha20-Poly1305, CBOR) | new envelope format and key handling — review with F5/F8; the branch carries test-vector private keys (scrub report §3.5) |
| liquid #203 `liquid serve admission` | a verifying webhook is a network surface with the same policy engine (§3.5) — F6/F23 apply |
| liquid #210 RFC 3161 / RFC 4998 verification; bridge decision 32 "own strict DER reader, X.509 path validation… verify-only RSA and ECDSA… no third-party library in the trust path" | an own ASN.1/DER parser and own signature verification are exactly the code that needs fuzzing and vector suites before release; treat as a fuzz target from the first commit |
| liquid #207 tiled transparency-log verification; #83 "every tile verified against its parent" (cites CVE-2026-56865 in `sum.golang.org`); #186 TUF metadata verification | client-side verification that must fail closed; partial verification is a bypass |
| liquid #170 `key_provider` wrap/unwrap; #51 pluggable KEK custody (KMS, Vault, age, TPM, Shamir); #81 hardware tokens, TPM, threshold signing (decision 21: own CTAP2/PIV/TPM2 command layers over OS transports) | the fix path for F5; own protocol implementations over HID/PC/SC/TPM are new parsers of device-supplied data |
| liquid #76 platform signing and notarisation; liquify #11 signed installers | signing-key custody per platform; release provenance should be liquid's own attestations (dogfood) |
| liquid #72 tree-sitter grammar distribution as a supply-chain question | §3.9, F11 |
| liquid #74 the configuration language "with an ordinary-program escape hatch" | an escape hatch that executes programs must run inside the sandbox of §3.2 |
| liquid #42 exclusive checkout / lock authority; #30 multiplayer and agents, scoped authority | authority and delegation (F26) |
| liquid #54 offline correctness (waiting on the org CI secret) | disappears with public submodules (F11) |
| liquify #10 AI surface, #8 structural editing for agents, #3 plugin ABI and agent presence | §3.9, §3.10 |
| bridge #2 licence; #16 release epic; #8 TAAP feedback (attenuation-only delegation, identifier stability across rotation); #1 TAAP content-addressed subjects | F19, F26 |

No open issue mentions fuzzing, sanitizers, TSan or a threat model: the checklist below is new work.

## 7. Pre-publication review checklist

Ordered so that each item's cost is paid once. The exit criterion in issue #11 is "fuzzers running in
CI"; §7.1 defines what "fuzzers" means.

### 7.1 Fuzzing targets (libFuzzer harnesses under ASan+UBSan, seeded from existing fixtures; a short per-PR run and a nightly long run; apply to OSS-Fuzz once public)

Order is by exposure (network- or repository-reachable first).

1. **Canonical CBOR decoder** (`src/encoding/cbor.cpp`) — depth (F7), lengths, canonical-form rejection;
   seeds: `tests/fixtures/cbor/rfc8949-supported.txt`, every record in `tests/`.
2. **Record decoders** over CBOR: drips, changes, directory documents, identity documents and rotation
   chains, attestation records, `LQKEY` wrapped-key headers (F8), delta records — one harness per
   `decode_*`.
3. **Sync frame codec** (`src/sync/codec.cpp`) and the server's import path with a fixed signing key
   (structure-aware: mutate one frame in a valid stream).
4. **Git object store** (`src/git/object_store.cpp`): loose objects, packfiles with delta chains,
   `.idx` v2, refs (F30); seeds from `git fast-export` of small repositories.
5. **Protobuf wire decoder** and the REAPI message set (`src/protobuf/wire.cpp`, `src/reapi/messages.cpp`);
   seeds: `tests/reapi/fixtures/*.bin`.
6. **HTTP/2**: frame parser, HPACK decoder (with dynamic table), gRPC framing, a whole-connection
   harness that feeds a byte stream to the server state machine (F18).
7. **Pack frame and index-run readers**, LSM manifest, `objects.meta`, `remotes.meta`, leases (F17).
8. **FastCDC chunker** — property harness: deterministic boundaries, sizes within min/max, chunk
   concatenation equals input.
9. **Delta apply** (`src/delta.cpp`) with hostile patch blobs and mismatched sizes.
10. **JSON and `.env` parsers**, the leaf envelope parser (`ENC[liquid:v1:…]`), the encryption path-rule
    glob and regex matcher (F9), the secret detectors.
11. **Identity and signature decoders**, the TAAP signed-bytes construction against a known key
    (differential against a second Ed25519 implementation — OpenSSL is linked).
12. **Daemon frame reader** and each request type (`status`, `pause_capture`, `build_*`, `shutdown`).
13. **Wrap hook plan parser** (`wrap_hook.c`, C harness) and the `action_input` record.
14. **SBOM binary inference** (`src/build/sbom.cpp`, ELF/Mach-O/PE readers).
15. **In-tree SHA-256/SHA-1** differential against OpenSSL (F20).
16. **automerge-cpp**: turn `AUTOMERGE_CPP_BUILD_FUZZ` on in a CI job (`fuzz_leb128`, `fuzz_load`,
    `fuzz_change_chunk` exist).
17. **liquify**: persisted graph decoders (`stub_tree.cpp`, `interactive_analysis.cpp`) with
    `.liquid/liquify-graph` seeds; `EditorBuffer::from_text`; tree-sitter C and C++ with the upstream
    corpora (F14, F15).
18. **Later, from the first commit:** the DER/X.509/CMS reader of #210, the sealed-secret envelope of
    #204, the CTAP2/PIV/TPM2 response parsers of #81, and every Phase 5 format codec (zip, tar, HDF5,
    Parquet, SQLite).

### 7.2 Sanitizer and hardening runs

- Extend the Linux sanitizer job to `CMAKE_C_FLAGS` and add `-fno-sanitize-recover=all`,
  `-fsanitize=integer,implicit-conversion` on the hash, codec and http2 directories, and
  `ASAN_OPTIONS=detect_leaks=1:strict_string_checks=1`.
- Add **TSan** on the daemon, fan-out, executor, graph and liquify's `EditorGraph` (F31); expect
  Capy/Corosio to need suppressions — record them.
- Add **MSan** (Clang, instrumented libc++) for the parsers in §7.1 at least once before publication;
  it finds uninitialised reads the others cannot.
- Run the **privileged FUSE container suite** and the **crash simulator (`sim-long`)** under ASan in CI
  (self-hosted or a `--privileged` job); today the sandbox's own tests never run on a PR.
- Hardening flags in release builds: `-Wall -Wextra -Wconversion` (warnings as errors in CI),
  `-fstack-protector-strong`, `-D_FORTIFY_SOURCE=3`, `-D_GLIBCXX_ASSERTIONS` or
  `-D_LIBCPP_HARDENING_MODE=_LIBCPP_HARDENING_MODE_FAST`, `-fPIE -pie`, `-Wl,-z,relro,-z,now`,
  `-fcf-protection`/`-mbranch-protection=standard`; `-fsanitize=cfi` where the toolchain allows.
- `clang-tidy` with `bugprone-*`, `cert-*`, `clang-analyzer-*`, `concurrency-*`; a `.clang-tidy` in
  both repositories.
- macOS: run the test suite under `MallocScribble`/Guard Malloc once; Windows: `/analyze` and
  Application Verifier on the CLI.

### 7.3 Dependency audit of the submodules and fetched sources

For each: exact version or commit, licence and its compatibility with the licence chosen in bridge #2,
upstream delta (for the patch carriers), open CVEs, and whether liquid's usage touches the affected
code.

| Dependency | Pin today | Audit action |
|---|---|---|
| `oramasearch/corosio` (`orama-main`) | `9f8e865` | diff against `cppalliance/corosio`; the epoll hang-up fix is the only intended delta — confirm; it is in the TLS path with OpenSSL, so review the verify-peer and ALPN plumbing (F22) |
| `oramasearch/http` (`zetta-patches`) | `af0353a` | diff against `cppalliance/http`; HTTP/1.1 parser used for the lake client — fuzz upstream's parser or vendor their fuzzers |
| `oramasearch/automerge-cpp` | `06408d3` (v0.6.0+18) | a from-scratch reimplementation of the Automerge format: its own parsers (columnar chunks, LEB128, sync messages) are directly reachable from sync (B4); run its fuzzers (§7.1 item 16); confirm `nlohmann_json` vendored inside it is current |
| `oramasearch/oramacore-cpp` | `9b74ce1` | tokenizer and BM25F over repository text; licence must be compatible; fuzz the tokenizer |
| `cppalliance/capy` (`develop`) | `ce1c7d7` | public dependency in liquid's API surface; track upstream |
| BLAKE3 1.8.7, zstd 1.5.7, Monocypher 4.0.3, Boost 1.91.0, tree-sitter 0.25.9/0.26.13 + grammars, GoogleTest 1.17.0, SDL3 3.2.0, Dear ImGui 1.91.5 | tags / URL | pin by commit or `URL_HASH`; CVE check (zstd and SDL have had memory-safety advisories; ImGui is compiled with warnings off); enable Dependabot for submodules and actions, or Renovate with a lock file |
| OpenSSL 3, zlib, libfuse3, macFUSE | system | document minimum versions; zlib inflate is on the Git import path — prefer the system's patched zlib over a vendored copy |
| Generate liquid's own SBOM (`liquid sbom`) for the release and attach the `slsa_provenance/1` attestation — the project's own tooling as the release's evidence | | |

### 7.4 Repository and release settings (GitHub)

Enable before the first public push: private vulnerability reporting; secret scanning with push
protection; Dependabot alerts and security updates; CodeQL (C/C++) on PRs; branch protection with
required reviews on `main`; signed tags; `SECURITY.md` from the draft; a `CODEOWNERS`; actions pinned by
SHA with `persist-credentials: false` and a `concurrency` group; a `.gitleaksignore` for the scanner's
test vectors; `security.txt` on the project site when it exists.

### 7.5 Manual review before publishing

Read, with F-numbers in hand: `src/sandbox/*` (F2, F3, F4), `src/daemon.cpp:1000-1100,1530-1560`
(F1), `src/identity.cpp:100-420,1090-1100` (F5, F8), `src/encoding/cbor.cpp` (F7), `src/http2/*` limits
(F18), `src/sync/server.cpp` authorization ordering (F6), `src/sync/endpoint.cpp` TLS (F22),
`src/workers/*` lease handling (F24), liquify `src/editor_graph.cpp:86-134`, `stub_tree.cpp:111-179`,
`interactive_analysis.cpp:652-1045` (F14, F15). Record the outcome per finding on issue #11.

## 8. Sign-off checklist for issue #11

- [ ] F1, F2, F3, F6, F7, F12 fixed and tested; F5, F16, F28 documented in the repositories' own docs
      (`identity.md`, `README.md`, `secret-scanning.md`).
- [ ] Fuzz harnesses for §7.1 items 1–7 exist, run per PR (short) and nightly (long), and have run at
      least 24 CPU-hours each without a crash before the public push; items 8–17 tracked as issues.
- [ ] Sanitizer job instruments C and C++, TSan job exists, the FUSE container suite runs in CI.
- [ ] Every FetchContent pinned by commit or hash; actions pinned by SHA; `persist-credentials: false`;
      the submodule token retired.
- [ ] Dependency audit table (§7.3) completed with versions, licences and CVE status; `NOTICE` updated.
- [ ] `SECURITY.md` committed in both repositories with the reporting address filled; GitHub settings
      in §7.4 enabled.
- [ ] This document re-read at the publish commit and the file:line references refreshed; sign-off
      recorded on https://github.com/oramasearch/liquid-bridge/issues/11.
