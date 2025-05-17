# remod

**remod** provides command line tools for analysing and editing neuronal morphologies stored in the [SWC format](http://www.neuronland.org/NLMorphologyConverter/MorphologyFormats/SWC/).  The utilities compute detailed morphometric statistics, apply structural changes to dendrites and export the results for visualisation.

## Features

- Parse SWC files and compute forkpoint counts, branch order distributions,
  path and total lengths, surface areas and Sholl measurements.
- Automatically store aggregated statistics in `downloads/statistics/`.
- Remodel morphologies via `remod_cli.py edit` to remove, shrink, extend, branch or scale dendrites.  Dendrites can be chosen manually or randomly and radii can be adjusted.
- Node indices are renumbered automatically after editing.
- Visualise original and modified trees with `neuron_export.py` for individual or overlay plots.
- Generate summary graphs with `plot_statistics.py` and combine results from
  multiple runs using `merge_statistics.py`.

## Installation

The code requires **Python 3.10 or later** and depends on [NumPy](https://numpy.org/) and [Matplotlib](https://matplotlib.org/):

```bash
pip install numpy matplotlib
```

Using a virtual environment is recommended but not mandatory.

## Quick start

1. **Prepare your SWC files** – place your `.swc` files in a directory. Example data are available under `swc_files/`.
2. **Compute statistics** – run `remod_cli.py analyze` with the directory and a comma separated list of file names:

   ```bash
   python remod_cli.py analyze /path/to/swc 0-2.swc
   ```

   Results such as total dendritic length, forkpoint counts, branch order
   frequency and Sholl intersections are saved in `downloads/statistics/`.
3. **Remodel a morphology** – use `remod_cli.py edit` to apply structural changes.  The example below removes 50% of all terminal dendrites from `0-2.swc` and writes the modified neuron to `downloads/files/0-2_new.swc`:

   ```bash
   python remod_cli.py edit \
      --directory /path/to/swc \
      --file-name 0-2.swc \
      --who all_terminal \
      --action remove \
      --hm-choice percent \
      --amount 50 \
      --var-choice percent \
      --radius-change 10
   ```

   Other actions include `shrink`, `extend`, `branch` and `scale`.  Dendrites can be selected randomly using `--random-ratio` or specified explicitly with `--manual-dendrites`.
4. **Visualise** – run `neuron_export.py` to generate 3‑D plots or overlays comparing the original and edited morphologies. Use `plot_statistics.py` on `downloads/statistics/` to create summary graphs; add `--average` or `--compare` for group averages or comparative views.  Figures are stored in the `downloads/` directory.

## Workflow

The typical pipeline is:

1. **Analyse** – `remod_cli.py analyze` computes baseline statistics for a set of SWC files and writes them to `downloads/statistics/`.
2. **Modify** – `remod_cli.py edit` applies the chosen remodeling actions and saves edited files under `downloads/files/`.
3. **Reassign indices** – node indices are automatically renumbered after modifications.
4. **Visualise and plot** – generate 3‑D views and overlays with `neuron_export.py` and create summary plots with `plot_statistics.py`.
5. **Combine statistics** – use `merge_statistics.py` to merge and compare
   results from different runs. The `simple` command merges raw statistics
   whereas `smart` combines averages and generates comparison plots.

## More tools

- `swc_parser.py` also provides `index_reassign` to renumber nodes after editing.
- `core_utils.py` provides weighted dendrite sampling utilities and warning helpers once kept in `warn.py`.
- `remodeling_actions.py` implements the individual remodeling operations.
- `merge_statistics.py` combines results from separate runs and can plot comparisons.
- `plot_statistics.py` now includes the plotting helpers previously found in `plotting_helpers.py`.

Run any script with the `--help` flag for a description of its command line options.
