import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import numpy as np

from file_io import write_json
from json_stats import compute_statistics, main as json_main
from swc_parser import parse_swc_file, paths_to_soma


class PathsToSomaTests(unittest.TestCase):
    def test_path_contains_only_dendrite_roots(self):
        samples = {
            1: [1, 1, 0, 0, 0, 1, -1],
            2: [2, 3, 0, 1, 0, 1, 1],
            3: [3, 3, 0, 2, 0, 1, 2],
            4: [4, 3, 0, 3, 0, 1, 3],
        }
        self.assertEqual(paths_to_soma([2, 4], samples, {}, [samples[1]]), {2: [2], 4: [4, 2]})

    def test_missing_parent_has_clear_error(self):
        samples = {2: [2, 3, 0, 1, 0, 1, 99]}
        with self.assertRaisesRegex(ValueError, "sample 2 refers to missing parent 99"):
            paths_to_soma([2], samples, {}, [])

    def test_cycle_has_clear_error(self):
        samples = {
            2: [2, 3, 0, 1, 0, 1, 3],
            3: [3, 3, 0, 2, 0, 1, 2],
        }
        with self.assertRaisesRegex(ValueError, "cycle detected"):
            paths_to_soma([2], samples, {}, [])

    def test_bundled_valid_morphology_parses(self):
        result = parse_swc_file("swc_files/0-2.CNG.swc")
        self.assertTrue(result[10])
        self.assertTrue(result[23])

    def test_statistics_are_json_serializable(self):
        import json

        json.dumps(compute_statistics(Path("swc_files/0-2.CNG.swc")))

    def test_json_cli_writes_json_to_stdout(self):
        import json

        output = StringIO()
        with redirect_stdout(output):
            json_main(["swc_files", "0-2.CNG.swc"])
        self.assertIn("0-2.CNG.swc", json.loads(output.getvalue()))

    def test_file_json_writer_normalizes_numpy_scalars(self):
        import json
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "statistics.json"
            write_json(path, {np.int64(20): np.float64(1.5)})
            self.assertEqual(json.loads(path.read_text()), {"20": 1.5})


if __name__ == "__main__":
    unittest.main()
