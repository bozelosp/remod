# Mathematical contract

This document defines REMOD's data model, transformations, measurements, and
numerical conventions. It is normative: behavior not described here is outside
the scientific contract.

## 1. Morphology

A morphology is

\[
M=(V,E,x,r,c),
\]

where `(V,E)` is a finite rooted tree, `x: V → R³` assigns coordinates,
`r: V → R₊` assigns strictly positive radii, and `c: V → Z₆₄` assigns opaque
signed 64-bit SWC kind labels. One node has parent `-1`; every other node has
exactly one parent.

The parser requires seven whitespace-separated SWC fields per data row:

```text
id kind x y z radius parent
```

IDs, kinds, and parents are signed 64-bit integer tokens. IDs are positive; a
parent is either `-1` or a positive ID. Coordinates and radii are finite. IDs
are unique, all parents exist, the graph is connected and acyclic, and soma
samples (`kind = 1`) may not occur below a non-soma ancestor. Multiple proximal
soma samples are allowed. Input row order has no meaning. Direct construction
and text parsing enforce the same integer domain; both store coordinates and
radii as binary64 values.

The in-memory object is immutable. Canonical serialization emits comments and
then a deterministic parent-before-child ordering, sorts siblings by ID,
preserves IDs, and formats floating-point values with 17 significant digits.

## 2. Edges and branches

Each non-root node `v` identifies the directed edge `(p(v),v)`. Its
centerline length is

\[
L_v=\lVert x_v-x_{p(v)}\rVert_2.
\]

A neurite branch is a maximal path beginning immediately after a soma/root or a
topological branch point and ending at the next branch point or terminal. SWC
kind transitions never split a branch. The branch ID is its first distal node
ID. Branch order is one at the proximal neurite boundary and increases by one
after each topological branch point.

An analysis kind set `K` selects

\[
E_K=\{(p(v),v)\in E:c(v)\in K\}.
\]

This distal-sample convention is explicit so a mixed-kind edge is not silently
reclassified by an undocumented rule.

## 3. Geometry

Each edge is modeled as a straight centerline with radius varying linearly from
`r₀` to `r₁`. It is therefore a conical frustum. Its lateral area and volume
are

\[
A_v=\pi(r_0+r_1)\sqrt{L_v^2+(r_1-r_0)^2},
\]

\[
Q_v=\frac{\pi L_v}{3}(r_0^2+r_0r_1+r_1^2).
\]

Totals are `math.fsum` over selected edges. Unlike a distal-radius cylinder,
these formulas are invariant when an edge is subdivided at an exactly
interpolated point. Surface area excludes end caps. Zero-length edges are
allowed as topology but contribute zero centerline length and volume; their
lateral area follows the same frustum equation. Edgewise sums do not subtract
surface or volume overlap at branch junctions.

Root path length is the sum of all ancestor-edge lengths, independent of the
analysis kind filter. Units are never inferred. If the caller supplies a
coordinate unit `u`, lengths have unit `u`, areas `u²`, and volumes
`u³`.

## 4. Radial analysis

Radial analysis is computed only when the caller supplies both an origin
`o ∈ R³` and a strictly positive step `Δ`. Supplying exactly one is an
error. No soma center or default physical unit is inferred.

For radius `R=kΔ`, intersections of the closed line segment

\[
x(t)=x_0+t(x_1-x_0),\quad 0\le t\le1,
\]

with the sphere `||x(t)-o||₂=R` are the real roots of its quadratic equation.
The counting interval is `0 < t ≤ 1`: a shared node on a sphere belongs to
its proximal edge exactly once. A tangent contributes one crossing and a
secant may contribute two. Degenerate zero-length edges contribute none.

Shell lengths partition every selected edge at all sphere crossings. Each open
subsegment is assigned by its midpoint radius to shell
`[kΔ,(k+1)Δ)`. Consequently,

\[
\sum_k S_k=\sum_{v\in E_K}L_v
\]

up to floating-point summation error. At most 10,000 shells are accepted, which
bounds radial discretization for an accidentally tiny step.

An edge is tested only against its reachable contiguous shell interval.
Origin subtraction occurs in exact rational arithmetic on the stored binary64
coordinates. The minimum squared radius is therefore the exact squared
distance from the origin to the segment; the maximum is the larger exact
squared endpoint distance. Binary search compares those bounds with the exact
values of the stored binary64 shell radii. Every remaining contact is
classified from exact rational quadratic coefficients.

## 5. Pure transformations

Every operation returns a validated morphology and leaves its input unchanged.
A semantic no-op may return the identical immutable object.

### Prune

`prune(M,R)` removes the descendant closure of each requested root in `R`.
The morphology root cannot be pruned.

### Trim a terminal branch

`trim_terminal` removes either an explicit distal arclength `d` or an
explicit fraction `f` of one terminal branch. Exactly one parameter is
required. A cut inside an edge linearly interpolates both position and radius.
Full-branch removal is deliberately a prune operation, not an ambiguous trim.
An interpolation that cannot store each requested nonzero positional change
within the binary64 component bound below is rejected. The realized retained
arclength must also be within one ULP of the requested retained arclength.

### Scale edges

An edge factor is keyed by its child node. With positive factors `s_v` and a
default of one,

\[
x'_v=x'_{p(v)}+s_v(x_v-x_{p(v)}).
\]

Evaluation follows topological order. Thus an unscaled descendant is translated
using its original edge vector when an ancestor changes. Radii and topology are
unchanged. Stored coordinates use binary64 addition. The operation fails if
finite storage would collapse or reverse any requested nonzero component, or if
the realized component `δ̂` violates

\[
|\hat\delta-\delta|\le \operatorname{ulp}(\delta).
\]

The comparison is performed exactly between rational representations of the
stored binary64 values; it has no empirical tolerance multiplier.

### Scale radii

For explicitly selected nodes and positive factors `a_v`,

\[
r'_v=a_vr_v.
\]

Coordinates and topology are unchanged.

### Graft

`graft` adds explicitly specified direct children to a named parent. Each
child has a kind, a three-dimensional displacement from that parent, and a
radius. IDs are allocated monotonically from the current maximum. There is no
random direction, empirical length table, collision heuristic, or hidden seed.
An offset is rejected if finite storage would collapse or reverse a requested
nonzero component or violate the same componentwise binary64 bound.

## 6. Reproducibility and falsifiability

The implementation is required to satisfy these executable properties:

1. Parsing and analysis are independent of SWC row order.
2. Relabeling node IDs without changing the rooted geometry does not change
   aggregate measurements.
3. Translation and rotation preserve topology, length, area, and volume.
4. Uniform coordinate/radius scaling by `s` scales length, area, and volume by
   `s`, `s²`, and `s³` respectively.
5. Exact linear subdivision preserves length, lateral area, and volume.
6. Shell lengths conserve selected total length.
7. Parse → serialize → parse preserves the complete scientific object.
8. Transforms are pure, deterministic, and local according to their equations.
9. Canonical input and output digests plus exact transform parameters are
   sufficient to identify a CLI remodeling result.

Floating-point aggregation uses `math.fsum`; root paths carry a compensated
sum along the tree. Sphere-contact classification uses the exact rational
quadratic coefficients of the binary64 inputs; irrational roots use decimal
precision derived from the coefficients' bit span. Property tests verify
radial length conservation and analytic quantities at operation-scaled
binary64 tolerances rather than one global relative tolerance.

If a derived length, area, volume, path, or transformed coordinate lies outside
the finite binary64 range—or a positive result underflows to zero—the operation
fails explicitly rather than emitting infinity, NaN, or a silently collapsed
quantity.

## 7. Non-claims

SWC kinds beyond the proximal soma convention are not ontologies. Radii are not
validated against microscopy. A reconstruction may omit anatomy or encode
artifacts. Frustum geometry is a declared geometric model, not tissue truth.
Transforms express counterfactual geometry; they do not establish biological
plausibility. REMOD therefore reports only quantities determined by the stated
tree, parameters, and assumptions.
