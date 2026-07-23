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

- exactly one root sample, with parent `-1` and SWC type `1` (soma);
- positive, unique integer sample identifiers;
- finite coordinates and strictly positive radii;
- an existing parent for every non-root sample; and
- soma-contour samples connected only through other soma samples; and
- a connected, acyclic parent tree.

Sample identifiers do not need to be contiguous on input. Dendritic statistics
include SWC types `3` (basal) and `4` (apical). Type `2` axons and unrecognized
types are parsed but are not included in the reported dendritic totals. If an
edge crosses a type boundary, its measurement is assigned by the distal sample
type and the distal sample starts a new segment.

## Topological segments

A segment begins at the first non-soma sample after the soma, a branch point,
or a change in SWC type. It continues through samples with one neurite child
until the next branch point or terminal sample. The segment is identified by
the sample identifier of its first sample.

The geometric length of a segment includes the edge from its proximal parent
attachment to its first sample. A branch-point sample is therefore the distal
end of its incoming segment; each child starts a new outgoing segment.

A terminal segment has no downstream segment. A dendritic branch point is a
basal or apical sample with more than one non-soma child. Centrifugal branch
order is `1` before the first neurite bifurcation and increases by one at each
true bifurcation on the path away from the soma. A type boundary starts a new
reporting segment but does not change branch order. This is the one-based
convention used by the original REMOD implementation. Tools that label primary
segments as order `0`, including the NeuroMorpho.Org morphometry record for the
bundled fixture, report values one lower.

## Morphometric definitions

Coordinates and radii are interpreted in micrometers. Soma cable, surface area,
and volume are excluded from dendritic totals.

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
- **path length:** the sum of full segment lengths from a segment through its
  proximal ancestors to the soma;
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

## Sholl analysis

The Sholl origin is the coordinate of the validated root soma sample. The
radial step must be positive and may be non-integral.

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
results are calculated separately. Branch-point profiles are zero-filled over
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
segment. An amount in `micrometers` is an absolute centerline distance applied
to each target.

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
  arbors are translated to preserve connections. The soma is unchanged.
- **radius change:** applies either `radius * (1 + percentage / 100)` or
  `radius + micrometers` to selected segment samples. A result that is not
  positive is rejected.

Extension and branching divide the requested distance into steps drawn from
`length_distribution.txt`; the final step is truncated when necessary so the
requested path length is exact within floating-point tolerance. Each step is
deflected by 5 degrees from the preceding direction with a random azimuth. The
first steps of two new daughters use opposite azimuths on that cone.
Every generated endpoint must have a soma distance greater than or equal to its
parent endpoint. REMOD tries at most 128 seeded azimuths for each step. If no
candidate within the direction cone satisfies both the soma-distance and
numeric-representability conditions, the edit is rejected rather than
generating inward growth. Generation is limited to 100,000 new samples per
path. A request beyond that bound, or below the coordinate precision at the
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
by the input file; review them before publishing an edited morphology.

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
