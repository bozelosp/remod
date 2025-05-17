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
- Modify morphologies using `second_run.py` (remove, extend or change the
  diameter of dendrites).
- Visualise original and edited trees with 3‑D plots.
- Additional helper scripts to merge segments, reassign indices and plot data.

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

2. **Compute statistics** – run `first_run.py` and provide the directory and a
   comma-separated list of file names:

   ```bash
   python first_run.py /path/to/swc 0-2.swc
   ```

   Results such as total dendritic length, branch-order frequency and Sholl
   intersections are saved in `downloads/statistics/`.

3. **Remodel a morphology** – use `second_run.py` to apply structural changes.
   The example below removes 50% of all terminal dendrites from `0-2.swc` and
   writes the modified neuron to `downloads/files/0-2_new.swc`:

   ```bash
   python second_run.py \
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
   plots comparing the original and edited morphologies. Figures are stored in
   the `downloads/` directory.

## Workflow

The individual scripts are designed to be used as a pipeline:

1. **Analyse** – start with `first_run.py` to compute baseline statistics for a
   set of SWC files. It expects a directory and a comma-separated list of
   filenames. The resulting metrics are written to
   `downloads/statistics/`.
2. **Modify** – apply structural changes with `second_run.py` (or the legacy
   wrapper `take_action_swc.py`). This script can remove, extend or shrink
   selected dendrites and stores edited files under `downloads/files/`.
3. **Reassign indices** – if an editing step breaks the original node numbering,
   run `index_reassignment.py` on the newly created file so that node indices are
   consecutive again.
4. **Visualise and plot** – generate 3‑D views using `neuron_visualization.py`
   or `graph.py` and create summary plots with `plot_data.py` or
   `plot_individual_data.py`.
5. **Combine statistics** – use `merge.py` or `smart_merge.py` to merge multiple
   statistics files produced from different runs.

## More tools

- `merge.py` and `smart_merge.py` combine SWC segments.
- `plot_data.py` and `plot_individual_data.py` visualise computed statistics.
- `index_reassignment.py` renumbers node indices after editing.
- `random_sampling.py` demonstrates how to draw random dendrites.

Run any script with the `--help` flag for a description of its command-line
options.
