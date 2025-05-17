# remod

This repository contains Python scripts for exploring and remodeling neuronal morphologies stored in the [SWC format](http://www.neuronland.org/NLMorphologyConverter/MorphologyFormats/SWC/).
The code parses morphometric information, computes statistics and can modify dendritic trees.

## Requirements

* Python 3.8 or later
* [NumPy](https://numpy.org/)
* [Matplotlib](https://matplotlib.org/)

Install the dependencies with:

```bash
pip install numpy matplotlib
```

## Workflow

1. **Prepare your SWC files**
   Place the morphology files in a directory of your choice.

2. **Extract metrics**
   Run `first_run.py` to parse the SWC data and compute statistics such as branch counts,
   length distributions and Sholl profiles. Results are written to `statistics.csv` in the
   same directory.

   ```bash
   python first_run.py /path/to/swc/ 0-2.swc
   ```

3. **Apply remodeling actions**
   Use `second_run.py` to modify the neuron. The script accepts several command line
   arguments describing which dendrites to target and what operation to perform.
   The example below removes all terminal dendrites from `0-2.swc` and stores the
   modified file in the `downloads/` subdirectory.

   ```bash
   python second_run.py \
       --directory /path/to/swc/ \
       --file-name 0-2.swc \
       --who who_all_terminal \
       --action remove \
       --hm-choice percent \
       --amount 50 \
       --var-choice percent \
       --diam-change 10
   ```

4. **Visualize the result**
   Scripts such as `neuron_visualization.py` and `graph.py` generate 3D plots
   comparing the original and remodeled morphologies.

## Additional Utilities

* `merge.py` and `smart_merge.py` combine SWC segments.
* `plot_data.py` and `plot_individual_data.py` produce graphs from computed statistics.
* `index_reassignment.py` renumbers node indices after modifications.

Each script contains inline documentation or a `--help` option that provides
further details about its usage.
