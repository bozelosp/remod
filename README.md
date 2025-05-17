# remod

**remod** is a small collection of Python utilities for exploring, analysing and
remodelling neuronal morphologies stored in the
[SWC format](http://www.neuronland.org/NLMorphologyConverter/MorphologyFormats/SWC/).
The tools can compute detailed morphometric statistics, apply structural changes
to dendritic trees and visualise the results.

## Features

- Parse SWC files and extract measurements such as branch counts, branch-order
  distributions, total length/area and Sholl profiles.
- Automatically store aggregated statistics in `downloads/statistics/`.
- Modify morphologies using `second_run.py` or the unified
  `run.py edit` command to remove, extend or change dendrites.
- Visualise original and edited trees with 3‑D plots.
- Additional helper scripts to merge segments and plot data. Node indices are
  renumbered automatically after relevant edits.

## Installation

The code requires **Python 3.8 or later** and depends on
[NumPy](https://numpy.org/) and [Matplotlib](https://matplotlib.org/).
Install them with:

```bash
pip install numpy matplotlib
```

Using a virtual environment is recommended but not mandatory.

## Quick start

1. **Prepare your SWC files** – place your `.swc` files in a directory. Example
   data can be found under `trash/`.

2. **Compute statistics** – run `run.py analyze` (or `first_run.py`) and provide
   the directory and a comma-separated list of file names:

   ```bash
   python run.py analyze /path/to/swc 0-2.swc
   ```

   Results such as total dendritic length, branch-order frequency and Sholl
   intersections are saved in `downloads/statistics/`.

3. **Remodel a morphology** – use `run.py edit` (or `second_run.py`) to apply structural changes.
   The example below removes 50% of all terminal dendrites from `0-2.swc` and
   writes the modified neuron to `downloads/files/0-2_new.swc`:

   ```bash
   python run.py edit \
      --directory /path/to/swc \
      --file-name 0-2.swc \
      --who who_all_terminal \
      --action remove \
      --hm-choice percent \
      --amount 50 \
      --var-choice percent \
      --diam-change 10
   ```

4. **Visualise** – run `neuron_visualization.py` or `graph.py` to generate 3‑D
   plots comparing the original and edited morphologies. Use `plot_data.py` with
   the path to `downloads/statistics/` to create summary graphs; add
   `--average` or `--compare` for group averages or comparative views.
   Figures are stored in the `downloads/` directory.

## Workflow

The individual scripts are designed to be used as a pipeline:

1. **Analyse** – start with `run.py analyze` (or `first_run.py`) to compute baseline statistics for a
   set of SWC files. It expects a directory and a comma-separated list of
   filenames. The resulting metrics are written to
   `downloads/statistics/`.
2. **Modify** – apply structural changes with `run.py edit` (or `second_run.py`).
   This script can remove, extend or shrink selected dendrites and stores edited files under `downloads/files/`.
3. **Reassign indices** – `second_run.py` (and `run.py edit`) automatically renumbers nodes after
   modifications, so no extra command is needed.
4. **Visualise and plot** – generate 3‑D views using `neuron_visualization.py`
   or `graph.py` and create summary plots with `plot_data.py` or
   `plot_individual_data.py`.
5. **Combine statistics** – use `merge_stats.py` to merge statistics from
   different runs.

## More tools

- `merge_stats.py` combines SWC segments from multiple runs.
- `plot_data.py` generates summary graphs from a statistics directory with
  optional `--average` and `--compare` flags; `plot_individual_data.py` holds
  the plotting helpers.
- `index_reassignment.py` contains the renumbering logic used internally.
- `random_sampling.py` demonstrates how to draw random dendrites.

Run any script with the `--help` flag for a description of its command-line
options.
