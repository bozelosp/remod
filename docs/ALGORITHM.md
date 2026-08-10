# Algorithm and Measurement Conventions

This document records the conventions implemented by REMOD. The scientific
scope follows the [REMOD article](https://doi.org/10.3389/fnana.2015.00156),
but the definitions below are the operational contract for the current code.

## Input model

REMOD accepts the seven-column SWC representation:

```text
sample_id type x y z radius parent_id
```

Parsing requires:

- exactly one graph-root sample with parent `-1` (any integer SWC type);
- positive, unique integer sample identifiers;
- finite coordinates and strictly positive radii;
- an existing parent for every non-root sample; and
- soma-contour samples, when present, connected proximally through soma samples;
- no soma sample hanging below a non-soma process; and
- a connected, acyclic parent tree.

Sample identifiers do not need to be contiguous on input. The graph root is an
attachment anchor. If it is not type `1`, REMOD reports `NO_SOMA_ROOT` but keeps
root-independent analysis available. A missing soma therefore does not turn a
valid tree into malformed data.

Compartment types follow the NeuroMorpho SWC convention without pretending the
convention is enforced by the file format:

| Type | Interpretation | REMOD treatment |
| --- | --- | --- |
| `0` | undefined | generic arbor only; explicit warning |
| `1` | soma | root/origin when proximal |
| `2` | axon | axon and generic-arbor measurements |
| `3` | basal dendrite | dendritic and generic-arbor measurements |
| `4` | apical dendrite | dendritic and generic-arbor measurements |
| `5` | custom | generic arbor only; explicit warning |
| `6` | unspecified neurite | unspecified-neurite and generic-arbor measurements |
| `7` | glial process | glial-process and generic-arbor measurements |
| other integer | non-standard | preserved and measured generically; explicit warning |

If an edge crosses a type boundary, its measurement is assigned by the distal
sample type and the distal sample starts a new segment.

## Topological segments

A segment begins at the first non-soma sample after the graph-root anchor, a
soma sample, a branch point, or a change in SWC type. It continues through
samples with one non-soma child until the next branch point or terminal sample.
The graph-root sample itself is not a segment because it has no incoming edge.
The segment is identified by the sample identifier of its first sample.

The geometric length of a segment includes the edge from its proximal parent
attachment to its first sample. A branch-point sample is therefore the distal
end of its incoming segment; each child starts a new outgoing segment.

A terminal segment has no downstream segment. A dendritic branch point is a
basal or apical sample with more than one non-soma child. Centrifugal branch
order is `1` before the first arbor bifurcation and increases by one at each
true bifurcation on the path away from the graph root. A type boundary starts a new
reporting segment but does not change branch order. This is the one-based
convention used by the original REMOD implementation. Tools that label primary
segments as order `0`, including the NeuroMorpho.Org morphometry record for the
bundled fixture, report values one lower.

## Morphometric definitions

SWC carries no machine-readable coordinate unit. REMOD reports native
`units`, `units²`, and `units³` and emits `COORDINATE_UNIT_UNSPECIFIED`; it does
not silently infer micrometers. Files recorded in pixels or another unit must
be calibrated before physical quantities are interpreted. The sixth SWC column
is radius. Soma cable, surface area, and volume are excluded from arbor totals.

For an edge with Euclidean centerline length `L` and distal sample radius `r`,
REMOD uses:

```text
centerline length = L
lateral area      = 2 * pi * r * L
volume            = pi * r^2 * L
```

The area and volume formulas model each edge as an open cylinder whose radius
is recorded by its distal SWC sample. This is the explicit convention of the
current implementation. The article identifies these measurements but does not
specify the compartment formula. For the bundled NMO_01999 fixture, the
resulting centerline length, lateral area, and volume reproduce the values in
its [NeuroMorpho.Org morphometry
record](https://neuromorpho.org/api/morphometry/id/1999). That agreement is a
fixture-level consistency check, not proof of publication-era provenance or
validation for every SWC file. The soma radius is not used for a
soma-to-neurite edge. A zero-length edge contributes zero length, area, and
volume.

Other reported measurements use these definitions:

- **total length, area, and volume:** sums over the selected segments;
- **root-path length:** the sum of full segment lengths from a segment through
  its proximal ancestors to the graph-root anchor;
- **median segment diameter:** twice the median sample radius within a segment;
- **fractional diameter taper:** `(proximal diameter - distal diameter) /
  proximal diameter`;
- **diameter taper per length:** `(proximal diameter - distal diameter) /
  segment length`; and
- **branch-order summaries:** segment count and unweighted mean segment or path
  length within each centrifugal order.

The proximal and distal diameters used for taper are those of the first and
last samples in the segment. A positive taper value denotes narrowing toward
the distal end; a negative value denotes widening.

## Radial and Sholl analysis

Classical `sholl_*` results require a validated soma root and classified type-3
or type-4 dendrites. If either is absent, those maps are empty rather than
misleading zero-valued results. REMOD also reports `radial_all_arbor_*` for all
non-soma compartments. Its origin is the soma when present and otherwise the
explicitly labeled reconstruction root. A root-centered profile is useful
geometry, but it is not presented as soma-centered Sholl analysis. The radial
step must be positive and may be non-integral.

Aggregate statistics apply the same capability boundary: morphologies for which
a dendrite-specific, Sholl, or radial measurement is unavailable are excluded
from that metric's mean and sample count, not inserted as zeros. This permits
mixed real-world cohorts without silently depressing soma-dependent results.

For each requested sphere radius, intersection counts are calculated from the
exact intersections between a straight SWC edge and the sphere. A contact at
an edge's distal endpoint is assigned to that edge; the proximal endpoint is
excluded so a shared sample is not counted twice. Tangencies count as one
intersection.

Cable length is split geometrically among radial shells. The bin labeled `r`
contains length in the shell from `r - step` through `r`. A point on a shell
boundary has zero cable length, so the open or closed boundary choice does not
change the length sum. The shell lengths sum to the dendritic centerline length
within floating-point tolerance.

Branch points are assigned to the smallest shell whose outer radius is greater
than or equal to their radial distance. Basal, apical, and combined dendritic
Sholl results are calculated separately, alongside a generic all-arbor radial
profile. Branch-point profiles are zero-filled over
the same radial extent as the corresponding cable-length profile, including
for an unbranched arbor.

A request that would require more than 10,000 radial bins is rejected before
allocation. Increase the Sholl step for a morphology with a larger radial
extent.

## Remodeling operations

Operations act on segment identifiers. Fixed selectors address all or regional
segments; terminal selectors address terminal segments only. Random selectors
sample terminal segments uniformly without replacement. The requested count
is the nearest integer to `number of eligible segments * ratio`, with half
values rounded upward. A seed makes random selection and generated geometry
repeatable.

An action amount in `percent` is relative to the original length of each target
segment. An amount in `units` is an absolute centerline distance in native SWC
coordinates applied to each target.

- **shrink:** removes the requested length from the distal end. The remaining
  segment must have positive length. Any downstream arbor is translated by the
  tip displacement so its internal geometry and attachment are preserved.
- **remove:** removes each selected segment and its complete distal subtree.
- **extend:** appends the requested centerline length. For a nonterminal target,
  the downstream arbor is translated and reattached to the new tip.
- **branch:** adds exactly two daughter segments to each selected tip. Each
  daughter has the requested centerline length; existing downstream segments,
  if present, remain attached.
- **scale:** interprets the amount as a scale percentage (`80` means a factor of
  `0.8`). Selected segment coordinates are scaled about their proximal
  attachment and their radii are multiplied by the same factor. Downstream
  arbors are translated to preserve connections. The root anchor is unchanged.
- **radius change:** applies either `radius * (1 + percentage / 100)` or
  `radius + units` to selected segment samples. A result that is not
  positive is rejected. When combined with branching, the radius edit occurs
  first so both daughters inherit the edited attachment radius.

The browser interface previews the exact serialized and reanalyzed result
without mutating the active morphology. Applying promotes that same artifact;
it does not repeat random selection or geometry generation. Studio supplies an
explicit seed for stochastic requests that do not already have one.

Extension and branching divide the requested distance into steps drawn from
`length_distribution.txt`; the final step is truncated when necessary so the
requested path length is exact within floating-point tolerance. Each step is
deflected by 5 degrees from the preceding direction with a random azimuth. The
first steps of two new daughters use opposite azimuths on that cone. With a
soma root, every generated endpoint must have a soma distance greater than or
equal to its parent endpoint. Without a soma, no soma-radial claim is possible,
so growth follows local forward direction and retains the `NO_SOMA_ROOT`
warning. A 2D reconstruction uses the two in-plane directions and generated
points retain the constant coordinate. Growth is rejected for a 0D/1D input
because a meaningful deflection plane is absent.

`extend` and `branch` accept only type-3/type-4 targets. Their empirical length
table and biological interpretation are dendritic, so applying them to an axon,
unspecified neurite, glial process, custom type, or unknown type would be an
unsupported scientific assumption. Those compartments remain eligible for
deterministic `shrink`, `remove`, `scale`, and radius changes.

REMOD tries at most 128 seeded directions for each step. If no candidate within
the direction cone satisfies the applicable orientation and numeric
representability conditions, the edit is rejected. Generation is limited to
100,000 new samples per path. A request beyond that bound, or below the coordinate precision at the
selected tip, is rejected without writing an output file.

## Serialization

Samples are validated and renumbered contiguously in deterministic
parent-before-child order before serialization. The exact written file is
reparsed before the command reports success. Floating-point fields use 17
significant digits so finite binary64 values survive a write-read round trip.
`--output` selects an explicit destination; otherwise REMOD uses
`downloads/files/<stem>_new.swc`. Input and output must differ. An existing
destination is rejected unless `--force` is supplied.

Output headers record the source file name, selector, segment identifiers,
action, amounts, and seed without adding local paths or timestamps. Existing
source comments are preserved unchanged.

Those comments can contain paths, email addresses, or other metadata supplied
by the input file. Comment text is never interpreted as SWC geometry and cannot
affect parsing or analysis. Review or sanitize it separately before publishing
or redistributing a file; morphology rows need not be modified.

## Diagnostics and decision boundary

REMOD distinguishes three classes of input condition:

- **malformed data (hard error):** malformed rows, duplicate/non-positive IDs,
  missing parents, no or multiple graph roots, cycles, non-finite values, or
  non-positive radii. Continuing would make topology or geometry undefined.
- **unusual but structurally valid data (warning):** a non-soma root, effective
  2D/1D coordinates, coincident endpoints, very long internal edges, or
  soma/root-attachment outliers. The parent graph is retained. Measurements
  include the recorded edge and name the affected interpretation.
- **incomplete or uncertain semantics (information/warning):** types `0`, `5`,
  `6`, `7`, non-standard types, unknown units, or nearly uniform radii. Generic
  measurements remain available; biological labels and radius-derived claims
  are limited to what the file actually establishes.

Long-edge diagnostics use conservative robust file-level thresholds. Every
flagged edge must exceed four times the median positive arbor-edge length.
Soma/root attachments, axons, and generic arbors must also exceed the median
plus six scaled median absolute deviations. An internal dendritic edge must
exceed the stricter median-plus-ten-scaled-MAD threshold before it is described
as a possible geometric discontinuity. The edge classes receive distinct codes.
These warnings do not repair, interpolate, delete, or disconnect samples.
Length, path, radial, and remodeling results explicitly include the recorded
connected edge.

## Verification boundary and limitations

The implementation can be checked against analytical synthetic trees and the
structural invariants of the bundled SWC fixtures. These checks cover topology,
length conservation, compartment formulas, Sholl partitioning, exact edit
extents, connectivity, deterministic seeds, and valid SWC serialization.

The population-level CA3 and basolateral amygdala examples reported in the
REMOD article cannot be reproduced from this repository. The complete source
cohorts, exact sampled segment sets, and random seeds used for those examples
are not bundled. Their reported percentage changes are therefore contextual
results, not regression targets for this implementation.

REMOD produces edited end-state geometries. It does not model biological growth
dynamics, tissue mechanics, electrophysiology, or the probability that a
particular remodeling operation occurs. The bundled empirical length
distribution does not establish that generated branches are representative of
another cell type, brain region, species, or experimental condition. Users
should evaluate those assumptions for each analysis.

The article identifies diameter taper as a measurement but does not specify the
formula used for every reported taper value. The fractional and per-length
definitions above are therefore explicit implementation conventions, tested on
analytical fixtures rather than reconstructed from population results.
