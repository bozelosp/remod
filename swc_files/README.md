# Bundled SWC Fixtures

This directory contains two source morphologies used for parser, measurement,
and remodeling checks. Their numeric SWC records are retained as distributed;
the comment headers have been normalized to remove email addresses and local or
server file paths.

| File | NeuroMorpho.Org record | Archive | Recorded content |
| --- | --- | --- | --- |
| `0-2.CNG.swc` | [NMO_01999](https://neuromorpho.org/api/neuron/id/1999) | Smith | Rat prelimbic layer 5 pyramidal cell; soma and dendrites; no axon; dendrites incomplete |
| `0-2a.CNG.swc` | [NMO_02000](https://neuromorpho.org/api/neuron/id/2000) | Smith | Rat prelimbic layer 5 pyramidal cell; soma and dendrites; no axon; dendrites incomplete |

The source headers attribute SWC conversion and standardization work to Sridevi
Polavaram, R. Scorcioni, and Duncan Donohue, using L-Measure and StdSwc 1.31.

## Data attribution

The [NeuroMorpho.Org terms of
use](https://neuromorpho.org/useterm.jsp) state that material found on or
downloaded from NeuroMorpho.Org is provided under the [Creative Commons
Attribution 4.0 International
license](https://creativecommons.org/licenses/by/4.0/) and require users to
cite all of the following:

1. Bergstrom HC, McDonald CG, French HT, Smith RF. “Continuous nicotine
   administration produces selective, age-dependent structural alteration of
   pyramidal neurons from prelimbic cortex.” *Synapse*. 2008;62(1):31–39.
   [doi:10.1002/syn.20467](https://doi.org/10.1002/syn.20467).
2. NeuroMorpho.Org (RRID:SCR_002145).
3. Tecuatl C, Ljungquist B, Ascoli GA. “Accelerating the continuous community
   sharing of digital neuromorphology data.” *FASEB BioAdvances*.
   2024;6(7):207–221.
   [doi:10.1096/fba.2024-00048](https://doi.org/10.1096/fba.2024-00048).

This CC BY 4.0 notice applies to the bundled morphology data. The REMOD
software is licensed separately under the [MIT License](../LICENSE).

## Use as fixtures

The files provide nontrivial branched trees for structural and numerical
regression tests. Passing those tests establishes consistency with the stated
SWC and measurement conventions; it does not establish that the
reconstructions are complete biological ground truth. NeuroMorpho.Org records
both dendritic reconstructions as incomplete.
