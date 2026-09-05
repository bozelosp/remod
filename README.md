# REMOD

REMOD is a local-first application for inspecting, measuring, comparing, and
remodeling [SWC](https://openneuroscience.org/Standards/SWC) morphologies.
REMOD Studio provides the interactive browser workspace. The `remod` package
also provides a small, deterministic scientific kernel and CLI.

The scientific object is deliberately narrow: a finite rooted tree whose nodes
have an integer label, a three-dimensional position, and a positive radius.
REMOD does not infer units, biological validity, or generative mechanisms that
are absent from that object.

## Start Studio

Use Python 3.14 (the verified patch version is in `.python-version`):

```console
python3.14 -m venv .venv
.venv/bin/python -m pip install --require-hashes --only-binary :all: -r requirements.lock
.venv/bin/python remod_ui.py
```

With the environment already installed, only the last command is needed.
Studio opens at **http://127.0.0.1:8765/**. Use `--no-open` to skip opening a
browser or `--port 8766` to choose another loopback port. Remote serving is not
supported. Stop the server with Ctrl-C.

Studio includes the original full workspace:

- local SWC import and two bundled examples;
- interactive 3D morphology inspection, segment selection, and compartment visibility;
- scalar measurements, radial/Sholl profiles, and branch-order plots;
- two-cohort descriptive comparison with eligibility counts and missingness handling;
- shrink, remove, scale, radius, seeded extension, and branching operations;
- exact preview → apply → undo, plus SWC, JSON, and CSV downloads.

Files stay between your browser and the local Python process. There is no
telemetry, cloud upload, external font, CDN, or persistent browser workspace.
Export work before refreshing or closing the tab. Input comments are preserved;
review them before sharing an exported file.

The same Studio measurements and operations are available from
`remod_cli.py analyze` and `remod_cli.py edit`; use each subcommand's `--help`.
`plot_statistics.py` produces local plots from exported statistics. NumPy is
used by Studio analysis; Matplotlib is used for offline plots. The complete
dependency set is pinned and hash-verified in `requirements.lock`;
`requirements.txt` declares the two direct dependencies, not a reproducible install.

## Minimal kernel

| Module | Purpose |
| --- | --- |
| `remod.model` | Immutable tree, strict SWC parsing, canonical serialization |
| `remod.metrics` | Topology, path, length, frustum geometry, optional radial analysis |
| `remod.transforms` | Pure prune, trim, edge-scale, radius-scale, and explicit graft operations |
| `remod.cli` | Thin command-line interface with machine-readable results and receipts |

The `remod` package uses only the Python standard library; its CLI does not
require Studio's dependencies. Run from a trusted checkout;
`python -E -S -m remod ...` also ignores Python environment overrides and
third-party site packages.

### Kernel use

Analyze dendritic samples (SWC kinds 3 and 4):

```console
python -m remod analyze swc_files/0-2.CNG.swc --unit micrometre
```

Radial analysis has no hidden origin or bin size. Both must be requested:

```console
python -m remod analyze swc_files/0-2.CNG.swc \
  --unit micrometre --origin root --radial-step 20
```

`--origin root` means the coordinates of the unique SWC root, not an inferred
soma centroid. An explicit `x,y,z` origin is also accepted.

Every remodeling command writes a new SWC file and prints a JSON receipt with
the exact parameters and canonical input/output SHA-256 digests:

```console
python -m remod prune input.swc output.swc --roots 41,57
python -m remod trim input.swc output.swc --branch 41 --length 12.5
python -m remod scale-edges input.swc output.swc --factor 41=0.8 --factor 42=1.1
python -m remod scale-radii input.swc output.swc --factor 41=1.2
python -m remod graft input.swc output.swc --parent 41 --child 3,4,0,0,0.7
```

Kernel CLI outputs are never overwritten: a private, verified temporary file is
published atomically at a new path. Inputs must be regular UTF-8 files, not
symlinks. Transformations are deterministic and contain no random sampling.

The library API is intentionally small:

```python
from pathlib import Path

from remod import analyze, parse_swc, scale_edges, to_swc

morphology = parse_swc(Path("cell.swc").read_text(encoding="utf-8"))
report = analyze(morphology, kinds=(3, 4), unit="micrometre")
shorter = scale_edges(morphology, {41: 0.8})
serialized = to_swc(shorter)
assert parse_swc(serialized).digest == shorter.digest
```

Library callers own file I/O. Use the CLI for the verified, no-overwrite file
workflow; shell redirection does not inherit that guarantee.

## Scientific contracts

These interfaces intentionally expose different scientific models. A Studio
report must not be silently substituted with a kernel report:

| Convention | Studio (`remod_ui.py`, `remod_cli.py`) | Kernel (`python -m remod`) |
| --- | --- | --- |
| Area / volume | Distal-radius open cylinders | Linearly tapered conical frusta |
| Reporting segments | Split at topology and compartment changes | Maximal topological branches |
| Edited sample IDs | Deterministically renumbered | Preserved |
| Generated geometry | Explicit seeded empirical dendritic growth | Caller-supplied grafts only |
| Radial analysis | Labeled soma/root origin, default step 20 native units | Explicit origin and step required |

Both use strict bounded SWC validation, the same exact-contact radial solver,
finite results, 17-digit SWC serialization, and verified atomic CLI file writes.
Studio's full operational definitions and biological limitations are in
[`docs/STUDIO.md`](docs/STUDIO.md). Kernel invariants are:

- Parsing rejects malformed, non-finite, disconnected, cyclic, or
  non-positive-radius data.
- Sample IDs and SWC kinds are preserved. Kinds are opaque labels except that
  kind 1 identifies the proximal soma region.
- Branches are maximal topological paths. A change of SWC kind does not create
  an artificial branch boundary.
- Centerlines and radii vary linearly along each edge. Surface area and volume
  therefore use conical-frustum formulas, which are invariant to exact linear
  subdivision of an edge.
- A kind filter selects an edge by its distal sample. The selected kinds and
  unit are recorded in every report; radial origin and step are recorded
  when radial analysis is requested.
- Summation uses `math.fsum`; serialization uses 17 significant digits;
  transforms return validated trees without mutating inputs and reject
  unrepresentable vectors rather than silently collapsing them.
- Undefined or unrequested quantities are omitted rather than replaced by
  invented defaults.

The complete kernel definitions and falsifiable invariants are in
[`docs/ALGORITHM.md`](docs/ALGORITHM.md).
The local threat model, supported input limits, file guarantees, and residual
risks are in [`docs/DEFENSE.md`](docs/DEFENSE.md).

## Verification

```console
.venv/bin/python -m unittest discover -v
node --test tests/test_studio_browser.js
```

The suites cover both scientific contracts, attributed SWC fixtures, local HTTP
boundaries, safe file publication, bounded work, preview identity, undo, and
failure-atomic UI state. The JavaScript checks use Node's built-in test runner;
Node is not needed to run Studio.

## Scope and citation

Neither interface claims that an edited morphology is biologically plausible
or estimates missing anatomy. Studio's cohort comparisons are descriptive,
not inferential statistics; its documented empirical growth distribution is
not a validated model for every cell type or experimental condition.

If you use REMOD, cite Bozelos et al., “REMOD: A Tool for Analyzing and
Remodeling the Dendritic Architecture of Neural Cells,” *Frontiers in
Neuroanatomy* 9:156, [doi:10.3389/fnana.2015.00156](https://doi.org/10.3389/fnana.2015.00156).
The bundled fixture provenance and separate data license are documented in
[`swc_files/README.md`](swc_files/README.md).
