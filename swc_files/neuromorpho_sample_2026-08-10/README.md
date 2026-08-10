# NeuroMorpho coverage sample — 2026-08-10

This directory contains 12 publication-safe copies of standardized SWC files
downloaded from NeuroMorpho.Org. Numeric SWC fields are unchanged; comment-only
headers were sanitized to remove legacy contact addresses and absolute upstream
filesystem paths, and line endings were normalized to LF. The sample is
designed to exercise REMOD's real input
boundary: ordinary dendritic cells, dendrite-plus-axon cells, missing soma,
generic neurites, glial processes, 2D data, absent measured diameters,
incomplete reconstructions, and different species and source formats.

## Sampling

The selection used only the NeuroMorpho metadata API and direct SWC URLs, as
required by the [NeuroMorpho terms of use](https://neuromorpho.org/useterm.jsp).
It is deterministic: seed `20260810`, one draw from each of 12 ordered strata,
sorted by neuron ID. For each stratum, a 32-bit LCG selected one zero-based API
page from the reported population, with page size 1. The complete criteria,
population sizes, pages, metadata, source URLs, acquisition SHA-256 hashes, and
original download-time audit results are in [manifest.json](manifest.json). The
current post-hardening REMOD results are in
[current_remod_validation.json](current_remod_validation.json); keeping them
separate makes the behavior change auditable without rewriting source evidence.

This is a coverage-oriented stratified sample, not an unbiased estimate of the
repository-wide frequency of morphology features or data-quality problems.

## Sample outcomes

| Stratum | Record | Species / archive | REMOD outcome | Stress case |
| --- | --- | --- | --- | --- |
| global_baseline | NMO_318012 | mouse / Saminathan_Sharma | 6 glial-arbor segments | 2D type-7 microglia; generic geometry is measured, with dimensionality and radius-provenance warnings. |
| dendrites_soma_no_axon | NMO_115735 | mouse / DeFelipe | 40 dendritic segments | No measured diameter metadata; standardized-radius uncertainty is explicit without treating it as malformed geometry. |
| dendrites_soma_axon | NMO_97192 | human / Wang_Ye | 346 arbor segments (81 dendrite, 265 axon) | Mixed dendrite/axon; long axon edges are reported separately. |
| dendrites_no_soma | NMO_110695 | Toadfish / Boyle | 11 dendritic segments | Type-3 root is accepted; Sholl is unavailable, root-centered radial geometry remains available. |
| neurites_soma | NMO_247091 | rat / Lin | 2 unspecified-neurite segments | Type 6 is measured generically and identified explicitly instead of producing a misleading zero-arbor result. |
| processes_soma | NMO_199018 | mouse / Siegert | 46 glial-process segments | Type 7 is measured as glial arbor and excluded from neuron-specific dendritic claims. |
| processes_no_soma | NMO_147946 | rat / Althammer | 153 glial-process segments | Type-7 root is accepted with missing-soma, compartment, and long-edge warnings. |
| no_diameter_2d | NMO_136439 | rat / Soriano | 130 arbor segments (17 dendrite, 113 axon) | 2D, low radius variation, long soma attachments, and long axon edges are surfaced. |
| diameter_3d_no_angles | NMO_01750 | human / Lewis | 42 dendritic segments | Incomplete human dendrites; unusually long soma attachments are explicit without rejecting the tree. |
| drosophila | NMO_24621 | drosophila melanogaster / Chiang | 99 axon segments | Type-2 root is accepted as an axonal tree; dendritic growth remains unsupported. |
| human | NMO_300219 | human / Narkilahti | 52 unspecified-neurite segments | Type-6 root is accepted; generic analysis is available without inventing dendrite identity. |
| dendrites_incomplete | NMO_06053 | rat / Brunjes | 43 dendritic segments | The 23.1625-unit internal basal edge 6→7 is detected as `GEOMETRIC_DENDRITE_GAP` and retained. |

All 12 files are syntactically seven-column SWC trees with one root, unique
positive IDs, existing parents, positive radii, no detected parent cycles, and
no malformed rows. That is not enough to guarantee scientific suitability:

- All 12 files are accepted as structurally valid one-root trees. Four lack a
  soma root; soma-centered Sholl is unavailable for them, but root-independent
  topology, cable geometry, branch order, root paths, radial profiles, and
  deterministic edits remain available.
- Six contain classified dendrites. The other six are axon, unspecified-neurite,
  or glial arbors and now produce nonzero generic measurements with explicit
  compartment semantics.
- `NMO_006053` is the requested gap-like case: its topology is connected, but
  NeuroMorpho's standardization log flags the internal basal edge from sample
  6 to 7 as a 23.1625-unit length outlier and records “no action taken.”
- Long edges attached directly to the soma occur in other files. They should be
  warned about separately from internal neurite gaps because they can reflect
  the repository's three-point soma convention.
- “No Diameter” records still contain positive SWC radii after standardization.
  Those values must not be presented as experimentally measured diameters.
- SWC does not encode coordinate units. REMOD now labels measurements as native
  coordinate units rather than assuming micrometers.
- Two sampled files are 2D. Surface, volume, and 3D interpretations need an
  explicit warning even though the files parse.
- NeuroMorpho standardization logs retain warnings rather than guaranteeing
  artifact-free geometry; the sampled logs range from 1 to 7,896 warnings,
  mostly radius-related.

## Publication and provenance

The copies in this directory are clearly labeled derivatives with only comment
headers sanitized. Before and after sanitization, every file's normalized
numeric-row SHA-256 was compared and found identical. The acquisition hashes in
the manifest identify the exact raw upstream downloads; the source URLs remain
available when byte-identical originals are required. Parsing and morphology
analysis are unaffected because comments are not interpreted as SWC data.

NeuroMorpho.Org data are licensed under CC BY 4.0. Publications must cite the
original reconstruction paper(s), NeuroMorpho.Org (RRID:SCR_002145), and the
2024 Tecuatl–Ljungquist–Ascoli repository paper. Per-record DOI and PMID values
are preserved in the manifest.
