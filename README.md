# REMOD

REMOD is a small, deterministic kernel for measuring and transforming rooted
[SWC](https://openneuroscience.org/Standards/SWC) morphologies. Its complete
workflow is parse → analyze or transform → canonical export.

The scientific object is deliberately narrow: a finite rooted tree whose nodes
have an integer label, a three-dimensional position, and a positive radius.
REMOD does not infer units, biological validity, or generative mechanisms that
are absent from that object.

## Structure

| Module | Purpose |
| --- | --- |
| `remod.model` | Immutable tree, strict SWC parsing, canonical serialization |
| `remod.metrics` | Topology, path, length, frustum geometry, optional radial analysis |
| `remod.transforms` | Pure prune, trim, edge-scale, radius-scale, and explicit graft operations |
| `remod.cli` | Thin command-line interface with machine-readable results and receipts |

The implementation uses only the Python standard library. The repository pins
Python 3.14.6 in `.python-version`.

## Use

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

Outputs are never overwritten. Transformations are deterministic and contain
no random sampling.

The library API is intentionally small:

```python
from pathlib import Path

from remod import analyze, parse_swc, scale_edges, to_swc

morphology = parse_swc(Path("cell.swc").read_text(encoding="utf-8"))
report = analyze(morphology, kinds=(3, 4), unit="micrometre")
shorter = scale_edges(morphology, {41: 0.8})
Path("shorter.swc").write_text(to_swc(shorter), encoding="utf-8")
```

## Scientific contract

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

The complete definitions and falsifiable invariants are in
[`docs/ALGORITHM.md`](docs/ALGORITHM.md).

## Verification

```console
python -m unittest discover -s tests -v
```

The compact suite uses analytic trees and two attributed real SWC fixtures. It
tests row/ID-order independence, rigid-motion and scale covariance, exact
frustum subdivision, radial intersection conventions, shell conservation,
serialization, and transform locality.

## Scope and citation

REMOD does not claim that an edited morphology is biologically plausible. It
does not estimate missing anatomy, compare heterogeneous cohorts, or generate
branches from an undocumented probability distribution.

If you use REMOD, cite Bozelos et al., “REMOD: A Tool for Analyzing and
Remodeling the Dendritic Architecture of Neural Cells,” *Frontiers in
Neuroanatomy* 9:156, [doi:10.3389/fnana.2015.00156](https://doi.org/10.3389/fnana.2015.00156).
The bundled fixture provenance and separate data license are documented in
[`swc_files/README.md`](swc_files/README.md).
