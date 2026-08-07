# REMOD

REMOD analyzes and edits neuronal morphologies represented as SWC trees. This
repository implements the measurements and end-state remodeling operations
described in the [REMOD article](https://doi.org/10.3389/fnana.2015.00156).
The exact conventions used by the code are recorded in
[docs/ALGORITHM.md](docs/ALGORITHM.md).

The maintained command-line paths provide:

- basal, apical, and combined dendritic topology;
- length, lateral surface area, volume, path length, branch order, diameter,
  taper, and geometric Sholl measurements;
- shrink, remove, extend, branch, scale, and radius operations;
- manual, regional, terminal, and seeded random segment selection;
- an interactive rotating 3D browser workspace with cohort comparison;
- deterministic JSON statistics and static SVG plots; and
- validated, parent-before-child SWC serialization after editing.

## Installation

REMOD uses Python 3.14; the tested patch release is pinned in
`.python-version`. From a fresh checkout:

```bash
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install --require-hashes -r requirements.lock
```

NumPy is required for analysis and editing. Matplotlib is used only by
`plot_statistics.py`. `requirements.txt` records the direct dependency policy;
`requirements.lock` is the reproducible, fully hashed environment and records
its regeneration command in the file header.

## Browser interface

Start the local REMOD Studio:

```bash
python remod_ui.py
```

The command opens `http://127.0.0.1:8765/` in the default browser. The interface
accepts one or many SWC files and provides:

- continuously rotating 3D morphology views with drag, zoom, and click-to-select
  segment controls;
- basal, apical, terminal, random, and multi-segment remodeling targets;
- shrink, remove, extend, branch, scale, and radius edits with preview undo;
- morphometry tables, regional Sholl charts, and SWC/JSON downloads; and
- Group A/Group B comparisons of scalar, branch-order, and Sholl measurements,
  including cohort means and population-standard-deviation error bars.

Uploaded data and generated results remain in the local browser/server process.
REMOD Studio does not transmit files or send email. Use
`python remod_ui.py --help` to change the local host or port, or to prevent
automatic browser launch.

## Input requirements

An input file must contain one connected, acyclic SWC tree with exactly seven
columns per numeric row. Sample identifiers must be positive and unique,
coordinates must be finite, radii must be positive, and every non-root parent
must exist. The single root must be a soma sample with parent `-1`.
Additional soma-contour samples must be connected through other soma samples.

Dendritic measurements include SWC types `3` (basal) and `4` (apical). Other
neurite types are preserved during editing but excluded from dendritic totals.
Coordinates and radii are interpreted as micrometers.

## Analysis

Pass a directory and a comma-separated list of file names:

```bash
python remod_cli.py analyze swc_files 0-2.CNG.swc,0-2a.CNG.swc \
  --sholl-step 20
```

The command recalculates every input and writes:

```text
swc_files/downloads/statistics/results.json
swc_files/downloads/statistics/summary.json
```

`results.json` contains measurements for each file. `summary.json` contains
means, population standard deviations, and sample counts. Missing Sholl and
count bins are treated as zero during aggregation; branch-order length bins are
averaged only over morphologies in which that order occurs. Segment-specific
maps are not aggregated across files because sample identifiers are local to
each morphology.

## Visualization

After running `analyze`, generate the aggregate plot set with:

```bash
python plot_statistics.py swc_files
```

Plot one file instead of the aggregate summary with:

```bash
python plot_statistics.py swc_files --file 0-2.CNG.swc
```

The command writes ten SVG files under
`downloads/statistics/plots/aggregate/` or a file-specific subdirectory. The
plots cover counts, total length/area/volume, branch-order distributions, and
Sholl length/branch-point/intersection measurements. Aggregate error bars are
population standard deviations.

If an analyzed file has no dendritic samples, distribution plots are still
written and state that no dendritic data are available.

## Remodeling

This example adds two daughter segments to a seeded 10% sample of all terminal
dendritic segments. Each daughter is 80% as long as its selected parent
segment:

```bash
python remod_cli.py edit \
  --directory swc_files \
  --file-name 0-2.CNG.swc \
  --who random_all \
  --random-ratio 10 \
  --action branch \
  --amount 80 \
  --extent-unit percent \
  --seed 2026 \
  --output swc_files/downloads/files/0-2.CNG_new.swc
```

`--output` selects the destination. Without it, the command writes
`swc_files/downloads/files/0-2.CNG_new.swc`. An existing destination is not
replaced unless `--force` is supplied. The exact file written is reparsed
before the command reports success.

Available selectors are:

| Selector | Selected segments |
| --- | --- |
| `all_dendrites` | All basal and apical segments |
| `all_terminal` | All terminal dendritic segments |
| `all_basal`, `all_apical` | All segments in one dendritic region |
| `basal_terminal`, `apical_terminal` | Terminal segments in one region |
| `random_all`, `random_basal`, `random_apical` | Uniform sample of eligible terminal segments |
| `manual` | IDs supplied with `--manual-dendrites` |

Segment IDs are the first sample IDs after the soma, a branch point, or a
change in SWC type. They also appear as keys in `path_length_by_dendrite`,
`median_diameter_by_dendrite`, and `diameter_taper_by_dendrite` in analysis
output.

Available actions are:

| Action | Amount semantics |
| --- | --- |
| `shrink` | Length removed from the distal end |
| `remove` | No amount; removes the segment and its distal subtree |
| `extend` | Length appended to the selected segment |
| `branch` | Length of each of two new daughter segments |
| `scale` | Percentage scale factor for coordinates and radii; `80` means `0.8` |
| `none` | No structural change; use with `--radius-change` |

For `shrink`, `extend`, and `branch`, `--extent-unit percent` is relative to
each selected segment's original length. `--extent-unit micrometers` applies
the same absolute distance to each target. Radius changes accept `percent` or
`micrometers`; a non-positive result is rejected.

Generated extension and branch steps follow a 5-degree cone around the
preceding segment direction. Every new endpoint must remain at least as far
from the root soma as its parent endpoint. If the direction cone cannot meet
that condition at a selected tip, the edit is rejected.

Sequential actions use the first output as the second input. This example
removes a seeded 17% sample of apical terminal segments, then shrinks a seeded
10% sample of the remaining apical terminal segments by 18%:

```bash
python remod_cli.py edit --directory swc_files --file-name 0-2.CNG.swc \
  --who random_apical --random-ratio 17 --action remove --seed 2026 \
  --output swc_files/downloads/files/ca3_pruned.swc
python remod_cli.py edit --directory swc_files/downloads/files \
  --file-name ca3_pruned.swc --who random_apical --random-ratio 10 \
  --action shrink --amount 18 --seed 2027 \
  --output swc_files/downloads/files/ca3_pruned_shrunk.swc
```

For example, scale only the basal arbor to 80%:

```bash
python remod_cli.py edit \
  --directory swc_files \
  --file-name 0-2.CNG.swc \
  --who all_basal \
  --action scale \
  --amount 80
```

Run either subcommand with `--help` for the complete argument list.

## Verification

Run the regression and integration suite from the repository root:

```bash
python -m unittest discover -v
python -m compileall -q .
```

The checks use analytical trees for geometry and action invariants, then
exercise the maintained CLI. The topology and aggregate geometry of both
bundled fixtures are checked against their NeuroMorpho.Org records, linked from
[swc_files/README.md](swc_files/README.md). This is a fixture-level consistency
check, not validation for every SWC reconstruction.

## Scope and limitations

REMOD produces modified end-state geometries. It does not model biological
growth dynamics, tissue mechanics, electrophysiology, or the probability of a
particular structural change.

The bundled `length_distribution.txt` is the empirical sampling table used by
extension and branching. Its derivation is not recorded in this repository, so
it should not be treated as evidence that generated geometry represents a
particular cell type, brain region, species, or condition.

The CA3 and basolateral amygdala population results reported in the article
cannot be reproduced from this repository because the complete cohorts,
selected segment sets, and random seeds are not included. Those reported
percentages are contextual results rather than regression targets.

Group comparisons describe the files assigned to each cohort and do not perform
inferential hypothesis tests. Users remain responsible for cohort construction,
independence assumptions, multiple-comparison control, and biological
interpretation.

The two bundled morphology fixtures and their attribution are documented in
[swc_files/README.md](swc_files/README.md). They are nontrivial test inputs,
not complete biological ground truth.

## License

The REMOD software is available under the [MIT License](LICENSE). The bundled
SWC morphology data are licensed separately and attributed in
[swc_files/README.md](swc_files/README.md).

## Citation

Citation metadata is provided in [CITATION.cff](CITATION.cff):

Bozelos P, Stefanou SS, Bouloukakis G, Melachrinos C, Poirazi P. “REMOD: A
Tool for Analyzing and Remodeling the Dendritic Architecture of Neural Cells.”
*Frontiers in Neuroanatomy*. 2016;9:156.
[doi:10.3389/fnana.2015.00156](https://doi.org/10.3389/fnana.2015.00156).
