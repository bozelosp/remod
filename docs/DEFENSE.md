# Defensive contract

REMOD is a local-first Python scientific application: a loopback browser Studio,
an analysis/remodeling CLI, and a standard-library kernel. Security protects
scientific meaning, original data, confidentiality, and bounded local resources.
This is an engineering contract, not a compliance certification.

## Threat model and posture

Untrusted SWC records, comments, filenames, numeric options, and JSON cross into
validated trees, analysis, previews, and exports. Hostile webpages may attempt
to contact the listener, spoof origins, or use DNS rebinding. Local output paths
may alias inputs or encounter symlinks, competing writers, and interruptions.
Silent numeric corruption and nondeterministic preview/application are integrity
failures, not merely usability bugs.

The local OS account, browser, interpreter, checkout, and destination directories
are trusted. Same-account malware can forge HTTP headers and inspect memory;
Studio is not an authentication or sandbox boundary against it. Remote serving
is unsupported. SaaS accounts, tenants, databases, cloud infrastructure, WAFs,
centralized SIEM, production deployment, and TLS termination are out of scope.
No telemetry, remote analysis, external assets, executable SWC content, or
application subprocess execution is required.

## Local HTTP and browser boundary

`remod_ui.py` binds only `127.0.0.1`. Its constructor and CLI expose no general
host-binding option. Host must be the actual loopback authority; a supplied
Origin must match it, and Fetch Metadata must not describe cross-site access.
POST requires `X-Remod-Request: 1`, strict UTF-8 JSON, a single bounded positive
Content-Length, and a complete body. Duplicate/reserved JSON keys, excessive
nesting, non-finite/underflowing numbers, transfer/content encodings, and
unsupported methods are rejected. The header is a browser same-origin defense,
not a secret or login token. No CORS permission is granted.

Only fixed UI assets, health, two public examples, workspace analysis, cohort
summaries, and remodeling are routed. Browser requests cannot choose a server
filesystem path. The server does not save uploaded data or exports to disk.
Internal failures return generic errors without tracebacks or personal paths;
request logging is disabled. The CSP permits local code and requests only,
with no framing, external fonts, objects, or form submission. Anti-framing,
nosniff, no-referrer, and a narrow Permissions Policy accompany responses.
The server does not advertise its implementation version.

Labels, errors, and filenames use DOM text sinks. Download names reject paths
and control/format characters. CSV text that could begin a spreadsheet formula
is prefixed as text; actual negative numeric measurements remain numbers.
Only generated filename stems may be shortened to accommodate suffixes.
Source metadata and morphology samples are not silently shortened.

## Capacity policy

Limits are operational, not inferred biological constraints. Excess scientific
input or work is rejected explicitly; warning ID lists may be summarized with
an explicit total and truncation flag.

| Input/work | Limit | Purpose |
| --- | --- | --- |
| SWC UTF-8 text | 16 MiB per file | Bounded read and parsing memory |
| SWC line / total comments | 4,096 characters / 1 MiB | Bounded tokenization and metadata |
| Samples including generated geometry | 50,000 per morphology | Bounded tree and output allocation |
| Numeric token | 128 ASCII decimal characters | Bounded conversion, no nonzero-to-zero coercion |
| IDs, kinds, parents | Signed 64-bit; IDs positive | Sparse maps, not identifier-sized arrays |
| Browser integer fields and seeds | Magnitude at most 2^53 - 1 | Exact JavaScript identity |
| Coordinates, radii, results | Finite binary64; radii positive | Explicit rejection of unrepresentable geometry |
| Studio ancestor links | 1,000,000 | Bounds potentially quadratic root/descendant storage |
| Studio selected edit work | 2,000,000 sample visits | Bounds repeated subtree transformations |
| Radial shells / work | 10,000 / 200,000 weighted units per profile call | Bounded exact arithmetic and partitions |
| HTTP body / JSON depth | 24 MiB / 8 levels | Bounds framing and decoded payload |
| HTTP connections / computations | 8 / 2 | Bounds threads and concurrent scientific work |
| Connection I/O timeout | 5 seconds | Releases stalled body/header readers and writers |
| Files in browser/request | 128 | Bounds batch and cohort fan-out |
| Browser current / retained source text | 64 MiB / 128 MiB | Bounds originals, previews, and history |
| Browser retained geometry | 250,000 samples | Bounds current, preview, and undo models |
| Undo | 20 edits per file | Explicit refusal, never silent history loss |
| Cache | 12 analyses/sources, 512 statistics, 96 MiB retained Python objects | Bounded locked cache with eviction |
| Plain browser filename | 240 UTF-8 bytes | Safe names including generated suffixes |

For exact radial work, let `n` be an edge's candidate shell count and `b` the
largest numerator/denominator bit length of its six exact origin-relative
coordinates. Work is `sum((1+n) * max(1, ceil(b/64))**2)`. This conservative
capacity policy is not a wall-clock prediction. It is checked before contact
solving. Studio invokes bounded profiles for the generic arbor and eligible
dendritic regions; the number of such profiles is fixed.

Growth reserves worst-case samples from the minimum empirical step before
generating any points. Wide-tree sibling counting is linear; deeply segmented
trees may exceed the explicit ancestor budget. The kernel uses iterative,
linear-storage topology without Studio's descendant tables. The bundled examples
and representative public SWCs fit the limits. Multiple application instances,
browser overhead, transient serialization allocations, and total disk usage
remain OS responsibilities; these budgets are not a process RSS guarantee.

## Scientific and filesystem integrity

[STUDIO.md](STUDIO.md) defines the cylinder/compartment/seeded-growth model;
[ALGORITHM.md](ALGORITHM.md) defines the kernel's frustum/topological model.
Their shared radial solver, strict input tokens, and file primitives do not
erase those scientific differences. Cache keys bind source bytes, radial step,
and analysis version. Cached inputs are not mutated by edits. Preview is the
exact serialized, reparsed, reanalyzed artifact later applied; no random work is
repeated on apply. Undo restores the prior artifact. Workspace capacity checks
precede mutation, including atomic radial reanalysis.

POSIX file reads reject final symlinks and nonregular files, cap bytes, use strict
UTF-8, and check metadata for ordinary concurrent mutation. Paths in CLI commands
are explicit operator choices, not SWC-provided destinations. Ancestors and
directory ACLs must not allow untrusted writers.

The shared writer creates an exclusive mode-0600 temporary file in a pinned
destination directory, flushes/fsyncs, compares actual bytes, and reparses SWC
against its expected canonical digest before publication. Kernel commands never
replace an existing output. Studio edits require explicit `--force` to replace
a regular single-link destination; input/output aliases are rejected. Generated
Studio reports/plots atomically replace regular single-link report files when
rerun. Symlink/hardlink replacement and non-atomic fallbacks are not allowed.
Browser downloads instead use the browser's save policy.

Handled failures remove the operation's owned temporary file. A hard kill or
power loss may leave a private temporary file. After atomic publication, a
complete output can survive a directory-fsync or receipt-delivery failure.
A batch of reports/plots is not a multi-file transaction. Verify surviving
artifacts before retrying. Filesystem durability depends on its fsync semantics.

SWC comments are preserved metadata, not anonymized data. Review them before
sharing. Digests identify content, not authenticity or biological validity.
Refreshing or closing Studio discards its in-memory workspace; export first.

## Runtime, repository, and response

Studio requires NumPy; offline plotting adds Matplotlib and their transitive
dependencies. Use the complete SHA-256 lock with pip's `--require-hashes` and
`--only-binary :all:`. A successful hash check authenticates bytes against the
reviewed lock, not a compromised publisher. The kernel requires no third-party
packages. `.python-version` records the verified interpreter, not a promise of
future security status. Maintain the host interpreter through its trusted
distributor and reassess newly disclosed reachable advisories.

Preserve original inputs; reproduce failures with minimized synthetic data.
Keep credentials, research, audit artifacts, and private archival history out of
the public tree. Ignore rules prevent accidental staging, not forced disclosure.
Review the exact public diff before separately authorized publication. No secret,
private exploit sample, or research data should be sent to a public issue.
Credential revocation, history remediation, remote changes, and publication need
separate owner authorization. No private reporting address is invented here.

## Standards considered (2026-09-05)

This applicability mapping is evidence-based engineering guidance, not an ASVS
level or organization-wide compliance assertion. Executable evidence is in
`tests/test_security.py`, `tests/test_studio.py`,
`tests/test_studio_browser.js`, and the scientific suites.

| Baseline/control area | Disposition and implementation evidence |
| --- | --- |
| [ASVS 5.0.0](https://owasp.org/www-project-application-security-verification-standard/): validation, encoding, business logic | Applicable, remediated: strict parsing, text DOM sinks, CSV handling, numeric/geometry bounds, exact preview and atomic state |
| ASVS: web frontend, HTTP/API, configuration | Applicable, remediated: loopback-only server, Host/Origin/Fetch-Metadata/framing checks, fixed routes, CSP, bounded requests and concurrency |
| ASVS: file handling, data protection, errors | Applicable, satisfied/remediated: no browser-selected server paths, atomic file writer, finite serialization, safe responses, documented metadata boundary |
| ASVS: authentication, sessions, OAuth, tenants, remote TLS | Not applicable to this local no-account application; trusted local processes are an accepted boundary |
| [OWASP Top 10:2025](https://owasp.org/Top10/2025/) | Awareness only: access control, supply chain, injection, integrity, and exceptional conditions considered |
| [NIST SSDF 1.1 final](https://csrc.nist.gov/pubs/sp/800/218/final): PO.1, PW.1/4/5/7/8, RV.1–3 | Applicable: documented scope, minimal locked dependencies, threat-based fixes/review/tests, owner response; organization-wide practices not claimed |
| [SSDF 1.2](https://csrc.nist.gov/pubs/sp/800/218/r1/ipd) | Still initial public draft at lookup; guidance only, not substituted for final 1.1 |
| [NIST CSF 2.0](https://www.nist.gov/cyberframework) | Govern: owner authority; Identify: assets/surfaces; Protect: controls; Detect: rejections/regressions; Respond: private owner escalation; Recover: originals, undo, safe outputs |
| [CISA Secure by Design](https://www.cisa.gov/news-events/news/applying-secure-design-thinking-events-news) | Applicable: secure defaults that retain intended workflows, ownership of failures, transparent limits and residual risks |
| [Python security](https://docs.python.org/3.14/library/security_warnings.html), [PyPA secure installs](https://pip.pypa.io/en/stable/topics/secure-installs/) | Applicable: trusted runtime/imports, pinned complete hash-verified binary dependency set |
| SLSA 1.2 | Not applicable: no distributable build artifact or release/build pipeline |

Accepted residuals are the trusted host/filesystem/browser, process-wide resource
overhead, transient cache eviction requiring reanalysis, original metadata, and
the stated numerical/capacity limits. There is no persistent security-monitoring
service, authentication platform, telemetry, deployment gate, or scanner stack.
