# Defensive contract

REMOD is a local, standard-library Python CLI and scientific library. It has no
HTTP listener, browser UI, remote client, telemetry, accounts, database, cache,
internal worker pool, or installer/build pipeline. Security means preserving
scientific meaning and local files while bounding untrusted input and work.
This is an engineering contract, not a compliance certification.

## Threat model

An external supplier can provide SWC records, comments, and filenames that an
operator chooses to process. The boundaries are text -> validated immutable
tree -> deterministic computation -> canonical SWC or finite JSON -> local file.
The protected assets are source data, result integrity and identity, research
confidentiality, and process resources. Numeric overflow, underflow, ambiguous
serialization, partial files, and pathological geometry are concrete threats.

The invoking OS account, interpreter, checkout, and destination directory are
trusted. REMOD is not a sandbox against executable Python objects, hostile
same-account code, administrators, malicious filesystems, or an embedding
application that bypasses its file writer. Paths are explicit operator choices,
not filenames supplied by SWC data; absolute and relative paths are legitimate.
Directory ACLs and ancestors must not grant untrusted actors write access.

There is no network entry point for hostile webpages, DNS rebinding, Host/Origin
spoofing, malformed HTTP framing, remote binding, or request-concurrency attacks.
DOM XSS, URL/download handling, CSV formulas, prototype pollution, CSP and other
HTTP headers are not applicable. Neither are SaaS accounts, tenants, WAFs,
centralized SIEM, cloud infrastructure, or production deployment controls.

## Capacity policy

These are explicit operational limits, not inferred biological constraints.
Excess input is rejected, never truncated, repaired, sampled, or rescaled.

| Input/work | Limit | Purpose |
| --- | --- | --- |
| CLI inputs/outputs | One SWC input and at most one result file per call | No batch amplification |
| SWC UTF-8 bytes | 16 MiB | Bound read and parsing memory |
| SWC line | 4,096 characters; comment body at most 4,094 | Bound tokenization and diagnostics |
| Comment bodies plus canonical marker/newline allowance | 1 MiB | Bound metadata, including empty-comment streams |
| Samples, including grafted nodes | 50,000 | Bound tree, branch, and output allocation |
| Numeric token | 128 ASCII characters | Bound conversion; decimal grammar only |
| Integer fields | Signed 64-bit; positive IDs | Sparse IDs do not allocate sparse arrays |
| Geometry | Finite binary64; positive radii | Reject nonzero input underflow and unrepresentable results |
| Selected-kind/prune iterables | 50,000 entries | Bound repeated/infinite parameter iterables |
| Unit metadata | 128 characters | Bound and validate result metadata |
| Radial shells | 10,000 | Bound discretization |
| Radial work | 200,000 weighted units per call | Bound combined exact arithmetic and retained intervals |

For each selected edge, let `n` be its number of candidate shells and `b` the
largest numerator/denominator bit length of its six exact origin-relative
endpoint coordinates. Work is `sum((1+n) * max(1, ceil(b/64))**2)`. The quadratic
weight reserves more capacity for large-integer arithmetic; it is a conservative
capacity policy, not a wall-clock prediction or a scientific score. Check it
before contact solving. Every candidate generates at most two contacts, so the
work cap and sample cap also bound retained partition terms. Keep `math.fsum`
rather than weakening summation to reduce memory further.

The reviewed 14 public representative SWCs reached 7,893 samples, 274,574 bytes,
and 99 characters per line. All fit these limits with margin and retained exact
canonical/report hashes in the baseline analysis. A 50,000-deep synthetic tree
also completed without recursion. Tree construction and branch indexing are
iterative and use storage proportional to sample count, not identifier size.
Multiple processes/callers and total disk usage remain OS responsibilities.

## File and result guarantees

The POSIX CLI opens inputs without following a final symlink, rejects nonregular
files before reading, caps reads, and checks file metadata for concurrent change.
This detects ordinary mutation, not a malicious storage provider. UTF-8 decoding
is strict. Errors do not include input/output paths and terminal control
characters are escaped. Nothing is logged persistently by REMOD.

Output is written with mode `0600` to a random, exclusive temporary file in a
pinned destination directory. The directory must be owned by the invoking user
or root; group/world-writable directories require the sticky bit. The writer
flushes, fsyncs, compares the actual bytes, and reparses SWC to check the expected
canonical digest before atomic no-replacement publication. Existing files,
input/output aliases, hardlinks, symlinks, and concurrent competing writers do
not permit overwrites. There is no `--force` escape hatch or non-atomic fallback.
Filesystems without the required primitives fail explicitly.

Before publication, failures and Python-handled interruptions remove only the
operation's owned temporary file. A hard kill or power loss can leave a private
temporary file. After the atomic link succeeds, the complete output may exist
even if directory fsync or receipt delivery fails. The output and stdout receipt
are not a distributed transaction; verify a surviving file before retrying with
a new name. Filesystem crash durability depends on its fsync implementation.

Comments are scientific metadata, not automatically anonymized. Inspect them
before sharing. Digests identify canonical content (including comments), not
authenticity, biological validity, or the original input's whitespace. No
preview/apply cache or random seed state exists: transforms are pure, and the
CLI validates the exact serialized artifact against the result digest.

## Runtime, repository, and response

No direct or transitive third-party runtime dependency is required, and no
dependency lock is needed for this empty set. `.python-version` records the
verified interpreter, not a claim that upstream has no later fixes. Run only
from a trusted checkout; `python -E -S -m remod ...` avoids environment overrides
and third-party site initialization without breaking local package imports.
Keep the host interpreter maintained through its trusted distributor. Review
newly disclosed reachable vulnerabilities promptly; fix demonstrated integrity,
code-execution, disclosure, and exhaustion defects before using affected data
flows. Re-run the affected regressions when changing runtime or numerical code.
Any future justified package dependency needs exact versions and SHA-256 hashes
for the complete dependency set, verified during installation; do not add an
installer or dependency merely to implement this policy.

Keep local research, credentials, and audit outputs outside tracked source.
Ignore rules are accidental-staging protection, not a security boundary against
forced staging. Review the exact public snapshot and diff before separately
authorized publication; never include private archival refs or history. Do not
post sensitive exploit samples, research data, or credentials to public issues.
If a secret is discovered, preserve it privately without printing it, stop
sharing affected material, and have the owner separately authorize revocation
and history remediation. Preserve original input files and reproduce failures
with minimized synthetic data. No private reporting address is invented here.

## Standards considered (2026-09-05)

The mapping adapts applicable application controls to a local CLI; it does not
claim an ASVS level or formal compliance. Tests in `tests/test_security.py` and
the scientific suite supply executable evidence.

| Source/control | Disposition and evidence |
| --- | --- |
| [ASVS 5.0.0](https://github.com/OWASP/ASVS/tree/v5.0.0), 2.1.1–3, 2.2.1/3 | Applicable, remediated: documented grammar/capacity, shared model validation, numeric and tree consistency |
| ASVS 2.3.2/3, 5.2.1, 15.1.3, 15.2.2 | Applicable, remediated: bounded parsing/work and atomic result publication; stdout/crash limitations stated above |
| ASVS 15.3.5, 15.4.1/2 | Applicable, satisfied/remediated: explicit types, immutable objects, isolated Decimal context, descriptor-bound file operations |
| ASVS 16.4.1, 16.5.1/3 | Applicable, remediated: escaped path-free diagnostics, explicit rejection, no fail-open output |
| ASVS V3–4, V6–10, V12, HTTP upload/download controls | Not applicable: no web, authentication, sessions, tokens, OAuth, or network transport |
| [Top 10:2025](https://owasp.org/Top10/2025/) | Awareness only: design, supply chain, injection, integrity, and exceptional-condition risks considered; not a checklist |
| [NIST SSDF 1.1](https://csrc.nist.gov/pubs/sp/800/218/final), PO.1, PW.1/4/5/7/8, RV.1–3 | Applicable practices: documented scope, minimal dependencies, threat-based implementation/review/tests, root-cause remediation; no organization-wide conformance claim |
| [SSDF 1.2 draft](https://csrc.nist.gov/pubs/sp/800/218/r1/ipd) | Draft guidance only, not substituted for final 1.1 |
| [NIST CSF 2.0](https://www.nist.gov/cyberframework) | Govern: owner/authority; Identify: surfaces/assets; Protect: controls; Detect: rejections/tests; Respond: private owner escalation; Recover: original inputs and no-overwrite outputs |
| [CISA Secure by Design](https://www.cisa.gov/securebydesign) | Applicable: secure defaults, remove unnecessary surfaces, document failures and residual risk |
| [Python security](https://docs.python.org/3.14/library/security_warnings.html), [PyPA secure installs](https://pip.pypa.io/en/stable/topics/secure-installs/) | Applicable: trusted interpreter/imports; no packages needed; hash-verified complete sets if dependencies are introduced |
| SLSA 1.2 | Not applicable: no distributable build artifacts or build pipeline |

Accepted boundaries: trusted local OS/filesystem/interpreter, caller-controlled
parallelism and stdout, unredacted user metadata, and explicitly rejected inputs
beyond the documented capacity or numerical representation. Host maintenance and
private-reporting service configuration are owner actions, not application code.
