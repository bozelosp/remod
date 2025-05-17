# Remod

**Remod** offers a friendly collection of command line tools for analysing and tweaking neuronal morphologies stored in the [SWC format](http://www.neuronland.org/NLMorphologyConverter/MorphologyFormats/SWC/). Whether you want detailed statistics or structural edits, Remod helps you measure, modify and visualise your neurons.

## Features

- Parse SWC files to compute branch point counts, branch order distributions, lengths, surface areas and Sholl measurements.
- Automatically save all aggregated statistics in `downloads/statistics/`.
- Remodel morphologies with `remod_cli.py edit` by removing, shrinking, extending, branching or scaling dendrites. Pick dendrites manually or randomly and adjust radii as needed.
- Node indices are renumbered automatically after editing.
- Visualise original and edited trees using the export helpers in `file_io.py` for individual plots or overlays.
- Summarise multiple runs with `plot_statistics.py` using the `simple` or `smart` commands.

## Installation

Requires **Python 3.10 or later** with [NumPy](https://numpy.org/) and [Matplotlib](https://matplotlib.org/):

```bash
pip install numpy matplotlib
```

Using a virtual environment is recommended but not required.

## Quick start

1. **Prepare SWC files** – place your `.swc` files in a directory (see examples under `swc_files/`).
2. **Compute statistics** – run `remod_cli.py analyze` on the directory with a comma separated list of file names:

   ```bash
   python remod_cli.py analyze /path/to/swc 0-2.swc
   ```

   Results such as total dendritic length, branch point counts and Sholl intersections are written to `downloads/statistics/`.

   To get the statistics in a single JSON file without intermediate text files, use `json_stats.py`:

   ```bash
   python json_stats.py /path/to/swc 0-2.swc
   ```
3. **Edit morphologies** – `remod_cli.py edit` applies structural changes. The following removes 50% of all terminal dendrites from `0-2.swc` and writes the result to `downloads/files/0-2_new.swc`:

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

   Other actions include `shrink`, `extend`, `branch` and `scale`. Choose dendrites randomly via `--random-ratio` or specify them with `--manual-dendrites`.
4. **Visualise** – use the helpers in `file_io.py` to generate 3‑D plots or overlays. `plot_statistics.py` builds summary graphs from `downloads/statistics/`; add `--average` or `--compare` for group averages or comparisons. Figures are saved in the `downloads/` directory.

## Workflow

A typical pipeline looks like this:

1. **Analyse** – `remod_cli.py analyze` records baseline statistics in `downloads/statistics/`.
2. **Modify** – `remod_cli.py edit` performs the chosen remodeling operations and saves results in `downloads/files/`.
3. **Reassign indices** – node indices are automatically renumbered after modifications.
4. **Visualise and plot** – generate 3‑D views and overlays with `file_io.py` and produce summary plots via `plot_statistics.py`.
5. **Combine statistics** – use `plot_statistics.py` with `simple` or `smart` to merge and compare runs.

## More tools

- `swc_parser.py` also provides `index_reassign` to renumber nodes after editing.
- `core_utils.py` offers weighted dendrite sampling utilities and warning helpers.
- `remodeling_actions.py` implements the remodeling operations.
- Plotting and merging functionality resides in `plot_statistics.py`.
- `swc_parser.py` exposes an `SWCParser` class wrapping the original `parse_swc_file` function.
- `logger_utils.py` contains a small `MarkdownLogger` for logs.
- `core_utils.py` collects CLI parsers in the `CLIParsers` class.
- Common file helpers live under `FileIO` in `file_io.py`.
- Morphometric functions are grouped in `MorphologyStats`.
- `json_stats.py` exports a `StatisticsComputer` for JSON output.
- Plotting helpers are accessible via the `StatisticsPlotter` class.
- The main entry points reside in `RemodCLI` within `remod_cli.py`.
- Remodeling actions are available through the `RemodelActions` class.

Run any script with the `--help` flag to see its command line options.
