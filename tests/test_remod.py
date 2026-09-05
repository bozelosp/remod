from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from dataclasses import FrozenInstanceError
from io import StringIO
import json
from math import fsum, pi, sqrt, ulp
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import remod
from remod import (
    Morphology,
    Node,
    analyze,
    graft,
    parse_swc,
    prune,
    scale_edges,
    scale_radii,
    to_swc,
    trim_terminal,
)
from remod.cli import main


ROOT = Path(__file__).resolve().parents[1]
Y_TREE = """\
# synthetic Y
5 3 3 -1 0 0.5 3
3 4 2 0 0 0.8 2
1 1 0 0 0 1 -1
4 3 3 1 0 0.5 3
2 3 1 0 0 0.9 1
"""
CHAIN = """\
1 1 0 0 0 3 -1
2 3 4 0 0 2 1
3 3 10 0 0 1 2
"""


def close(test: unittest.TestCase, actual: float, expected: float, ulps: int = 64) -> None:
    tolerance = ulps * max(ulp(actual), ulp(expected))
    test.assertAlmostEqual(actual, expected, delta=tolerance)


class ModelTests(unittest.TestCase):
    def test_parse_is_row_order_independent_and_round_trips(self) -> None:
        morphology = parse_swc(Y_TREE)
        self.assertEqual([node.id for node in morphology.nodes], [1, 2, 3, 4, 5])
        self.assertEqual(morphology.comments, ("synthetic Y",))
        self.assertEqual(parse_swc(to_swc(morphology)), morphology)
        data_rows = [line for line in Y_TREE.splitlines() if line and not line.startswith("#")]
        reordered = parse_swc("# synthetic Y\n" + "\n".join(reversed(data_rows)) + "\n")
        self.assertEqual(reordered, morphology)
        self.assertEqual(reordered.digest, morphology.digest)
        self.assertEqual(
            parse_swc("1 1 -0 +0 0.0 1 -1\n").digest,
            parse_swc("1 1 0 0 0 1 -1\n").digest,
        )

    def test_model_is_deeply_immutable(self) -> None:
        morphology = parse_swc(CHAIN)
        with self.assertRaises(FrozenInstanceError):
            morphology.nodes = ()
        with self.assertRaises(FrozenInstanceError):
            morphology.root.radius = 2
        self.assertIsInstance(morphology.children(1), tuple)

    def test_strict_validation_rejects_invalid_scientific_objects(self) -> None:
        invalid = {
            "empty": "",
            "field count": "1 1 0 0 0 1\n",
            "non-integer id token": "1.0 1 0 0 0 1 -1\n",
            "duplicate id": "1 1 0 0 0 1 -1\n1 3 1 0 0 1 1\n",
            "missing parent": "1 1 0 0 0 1 -1\n2 3 1 0 0 1 8\n",
            "multiple roots": "1 1 0 0 0 1 -1\n2 3 1 0 0 1 -1\n",
            "disconnected cycle": (
                "1 1 0 0 0 1 -1\n2 3 1 0 0 1 3\n3 3 2 0 0 1 2\n"
            ),
            "nonfinite": "1 1 nan 0 0 1 -1\n",
            "zero radius": "1 1 0 0 0 0 -1\n",
            "nonpositive id": "0 1 0 0 0 1 -1\n",
            "invalid parent sentinel": "1 1 0 0 0 1 0\n",
            "distal soma": "1 1 0 0 0 1 -1\n2 3 1 0 0 1 1\n3 1 2 0 0 1 2\n",
        }
        for label, text in invalid.items():
            with self.subTest(label=label), self.assertRaises((TypeError, ValueError)):
                parse_swc(text)

    def test_integer_domain_is_shared_by_objects_and_text(self) -> None:
        largest = (1 << 63) - 1
        boundary = Morphology((Node(largest, -(1 << 63), (0.0, 0.0, 0.0), 1.0, -1),))
        self.assertEqual(parse_swc(to_swc(boundary)), boundary)

        outside = 1 << 63
        with self.assertRaisesRegex(ValueError, "signed 64-bit"):
            Morphology((Node(outside, 1, (0.0, 0.0, 0.0), 1.0, -1),))
        with self.assertRaisesRegex(ValueError, "signed 64-bit"):
            parse_swc(f"1 {outside} 0 0 0 1 -1\n")
        with self.assertRaises(ValueError):
            Morphology((Node(10**5000, 1, (0.0, 0.0, 0.0), 1.0, -1),))
        with self.assertRaises(ValueError):
            parse_swc("9" * 5000 + " 1 0 0 0 1 -1\n")

    def test_direct_numeric_values_are_normalized_to_binary64(self) -> None:
        morphology = Morphology(
            (Node(1, 1, (10**16 + 1, 2, 3), 4, -1),)
        )
        self.assertEqual(morphology.root.point, (1e16, 2.0, 3.0))
        self.assertTrue(all(type(value) is float for value in morphology.root.point))
        self.assertIs(type(morphology.root.radius), float)
        self.assertEqual(parse_swc(to_swc(morphology)), morphology)

    def test_branch_decomposition_is_topological_not_type_based(self) -> None:
        morphology = parse_swc(Y_TREE)
        self.assertEqual(
            [
                (branch.id, branch.proximal, branch.node_ids)
                for branch in morphology.branches
            ],
            [(2, 1, (2, 3)), (4, 3, (4,)), (5, 3, (5,))],
        )


class MetricTests(unittest.TestCase):
    def test_frustum_geometry_has_an_analytic_value(self) -> None:
        morphology = parse_swc("1 1 0 0 0 2 -1\n2 3 4 0 0 1 1\n")
        geometry = analyze(morphology)["geometry"]
        self.assertEqual(geometry["total_length"], 4.0)
        close(self, geometry["total_lateral_area"], 3 * pi * sqrt(17))
        close(self, geometry["total_volume"], 28 * pi / 3)

    def test_linear_subdivision_preserves_all_geometry(self) -> None:
        coarse = parse_swc("1 1 0 0 0 2 -1\n3 3 4 0 0 1 1\n")
        refined = parse_swc(
            "1 1 0 0 0 2 -1\n2 3 1 0 0 1.75 1\n3 3 4 0 0 1 2\n"
        )
        a = analyze(coarse)["geometry"]
        b = analyze(refined)["geometry"]
        for key in ("total_length", "total_lateral_area", "total_volume"):
            close(self, a[key], b[key])

    def test_aggregate_metrics_ignore_ids_and_input_rows(self) -> None:
        source = parse_swc(Y_TREE)
        mapping = {1: 80, 2: 7, 3: 42, 4: 3, 5: 101}
        relabeled = Morphology(
            tuple(
                Node(
                    mapping[node.id],
                    node.kind,
                    node.point,
                    node.radius,
                    -1 if node.parent == -1 else mapping[node.parent],
                )
                for node in reversed(source.nodes)
            ),
            source.comments,
        )
        first = analyze(source)
        second = analyze(relabeled)
        for key in ("total_length", "total_lateral_area", "total_volume"):
            self.assertEqual(first["geometry"][key], second["geometry"][key])
        self.assertEqual(
            len(first["topology"]["branches"]),
            len(second["topology"]["branches"]),
        )

    def test_rigid_motion_and_uniform_scale_have_expected_covariance(self) -> None:
        source = parse_swc(Y_TREE)

        def mapped(point: tuple[float, float, float]) -> tuple[float, float, float]:
            x, y, z = point
            return (11 - y, -7 + x, 5 + z)

        rigid = Morphology(
            tuple(
                Node(node.id, node.kind, mapped(node.point), node.radius, node.parent)
                for node in source.nodes
            )
        )
        scaled = Morphology(
            tuple(
                Node(
                    node.id,
                    node.kind,
                    tuple(3 * value for value in node.point),
                    3 * node.radius,
                    node.parent,
                )
                for node in source.nodes
            )
        )
        base_geometry = analyze(source)["geometry"]
        rigid_geometry = analyze(rigid)["geometry"]
        scaled_geometry = analyze(scaled)["geometry"]
        for key in ("total_length", "total_lateral_area", "total_volume"):
            close(self, rigid_geometry[key], base_geometry[key])
        close(self, scaled_geometry["total_length"], 3 * base_geometry["total_length"])
        close(
            self,
            scaled_geometry["total_lateral_area"],
            9 * base_geometry["total_lateral_area"],
        )
        close(self, scaled_geometry["total_volume"], 27 * base_geometry["total_volume"])

    def test_fsum_preserves_small_terms_in_a_large_total(self) -> None:
        morphology = Morphology(
            (
                Node(1, 1, (0.0, 0.0, 0.0), 1.0, -1),
                Node(2, 3, (1e16, 0.0, 0.0), 1.0, 1),
                Node(3, 3, (1.0, 0.0, 0.0), 1.0, 1),
                Node(4, 3, (0.0, 1.0, 0.0), 1.0, 1),
            )
        )
        self.assertEqual(
            analyze(morphology)["geometry"]["total_length"],
            fsum((1e16, 1.0, 1.0)),
        )

    def test_unrepresentable_derived_geometry_fails_explicitly(self) -> None:
        morphology = Morphology(
            (
                Node(1, 1, (0.0, 0.0, 0.0), 5e-324, -1),
                Node(2, 3, (1.0, 0.0, 0.0), 5e-324, 1),
            )
        )
        with self.assertRaisesRegex(ValueError, "numeric resolution"):
            analyze(morphology)

    def test_root_paths_include_unselected_ancestor_edges(self) -> None:
        morphology = parse_swc(
            "1 1 0 0 0 1 -1\n2 2 2 0 0 1 1\n3 3 5 0 0 1 2\n"
        )
        report = analyze(morphology, kinds=(3,))
        self.assertEqual(report["geometry"]["total_length"], 3.0)
        self.assertEqual(report["edges"][0]["root_path_length"], 5.0)
        self.assertEqual(
            report["geometry"]["terminal_root_path_lengths"],
            [{"terminal_id": 3, "root_path_length": 5.0}],
        )

    def test_root_paths_retain_recoverable_low_order_terms(self) -> None:
        morphology = Morphology(
            (
                Node(1, 1, (0.0, 0.0, 0.0), 1.0, -1),
                Node(2, 3, (1e16, 0.0, 0.0), 1.0, 1),
                Node(3, 3, (1e16, 1.0, 0.0), 1.0, 2),
                Node(4, 3, (1e16, 2.0, 0.0), 1.0, 3),
            )
        )
        report = analyze(morphology)
        self.assertEqual(
            report["geometry"]["terminal_root_path_lengths"][0]["root_path_length"],
            fsum((1e16, 1.0, 1.0)),
        )

    def test_radial_specification_is_all_or_nothing_and_typed(self) -> None:
        morphology = parse_swc(CHAIN)
        for arguments in (
            {"origin": (0.0, 0.0, 0.0)},
            {"radial_step": 1.0},
            {"origin": ("0", 0, 0), "radial_step": 1.0},
            {"origin": (0, 0, 0), "radial_step": "1"},
        ):
            with self.subTest(arguments=arguments), self.assertRaises(
                (TypeError, ValueError)
            ):
                analyze(morphology, **arguments)

    def test_secant_radial_profile_and_shell_conservation(self) -> None:
        morphology = parse_swc("1 1 -2 0 0 1 -1\n2 3 2 0 0 1 1\n")
        report = analyze(morphology, origin=(0.0, 0.0, 0.0), radial_step=1.0)
        shells = report["radial"]["shells"]
        self.assertEqual(
            [(shell["cable_length"], shell["intersection_count"]) for shell in shells],
            [(2.0, 2), (2.0, 1)],
        )
        self.assertEqual(
            fsum(shell["cable_length"] for shell in shells),
            report["geometry"]["total_length"],
        )

    def test_shared_endpoint_is_counted_once_and_tangent_once(self) -> None:
        chain = parse_swc(
            "1 1 0 0 0 1 -1\n2 3 1 0 0 1 1\n3 3 2 0 0 1 2\n"
        )
        chain_shells = analyze(
            chain, origin=(0.0, 0.0, 0.0), radial_step=1.0
        )["radial"]["shells"]
        self.assertEqual([shell["intersection_count"] for shell in chain_shells], [1, 1])

        tangent = parse_swc("1 1 -1 1 0 1 -1\n2 3 1 1 0 1 1\n")
        tangent_shells = analyze(
            tangent, origin=(0.0, 0.0, 0.0), radial_step=1.0
        )["radial"]["shells"]
        self.assertEqual(tangent_shells[0]["intersection_count"], 1)

        oblique_tangent = parse_swc("1 1 -3 -1 0 1 -1\n2 3 1 2 0 1 1\n")
        oblique_shells = analyze(
            oblique_tangent, origin=(0.0, 0.0, 0.0), radial_step=1.0
        )["radial"]["shells"]
        self.assertEqual(oblique_shells[0]["intersection_count"], 1)

    def test_radial_work_is_bounded(self) -> None:
        morphology = parse_swc("1 1 0 0 0 1 -1\n2 3 2 0 0 1 1\n")
        with self.assertRaises(ValueError):
            analyze(morphology, origin=(0, 0, 0), radial_step=1e-5)

    def test_far_short_edge_preserves_radial_contacts_and_partition(self) -> None:
        morphology = parse_swc(
            "1 1 9990 0 0 1 -1\n2 3 10000 0 0 1 1\n"
        )
        shells = analyze(
            morphology, origin=(0.0, 0.0, 0.0), radial_step=1.0
        )["radial"]["shells"]
        self.assertEqual(len(shells), 10_000)
        self.assertEqual(
            sum(shell["intersection_count"] for shell in shells), 10
        )
        self.assertEqual(fsum(shell["cable_length"] for shell in shells), 10.0)
        self.assertEqual(shells[9989]["intersection_count"], 0)
        close(self, shells[9990]["cable_length"], 1.0)
        self.assertEqual(shells[9990]["intersection_count"], 1)
        close(self, shells[-1]["cable_length"], 1.0)
        self.assertEqual(shells[-1]["intersection_count"], 1)

    def test_radial_origin_subtraction_is_exact(self) -> None:
        morphology = parse_swc(
            "1 1 2 0 0 1 -1\n2 3 1 0 0 1 1\n"
        )
        shells = analyze(
            morphology,
            origin=(1e16, 0.0, 0.0),
            radial_step=1e16,
        )["radial"]["shells"]
        self.assertEqual(len(shells), 1)
        self.assertEqual(shells[0]["intersection_count"], 0)
        self.assertEqual(shells[0]["cable_length"], 1.0)

    def test_real_fixture_has_stable_tree_and_centerline_length(self) -> None:
        first = parse_swc(
            (ROOT / "swc_files/0-2.CNG.swc").read_text(encoding="utf-8")
        )
        second = parse_swc(
            (ROOT / "swc_files/0-2a.CNG.swc").read_text(encoding="utf-8")
        )
        self.assertEqual((len(first.nodes), len(first.branches)), (485, 39))
        self.assertEqual((len(second.nodes), len(second.branches)), (457, 30))
        close(
            self,
            analyze(first)["geometry"]["total_length"],
            2605.5130433646286,
            ulps=128,
        )

    def test_branch_order_is_independent_of_recursion_limits_and_ids(self) -> None:
        depth = 1100
        root_id = depth + 2
        nodes = [Node(root_id, 1, (0.0, 0.0, 0.0), 1.0, -1)]
        parent = root_id
        for index in range(depth):
            continuation = depth + 1 - index
            leaf = 10_000 + index
            nodes.append(
                Node(continuation, 3, (float(index + 1), 0.0, 0.0), 1.0, parent)
            )
            nodes.append(Node(leaf, 3, (float(index), 1.0, 0.0), 1.0, parent))
            parent = continuation
        report = analyze(Morphology(tuple(nodes)))
        self.assertEqual(
            max(branch["order"] for branch in report["topology"]["branches"]),
            depth,
        )


class TransformTests(unittest.TestCase):
    def test_prune_removes_exact_descendants_without_mutation(self) -> None:
        source = parse_swc(Y_TREE)
        before = to_swc(source)
        result = prune(source, (3,))
        self.assertEqual([node.id for node in result.nodes], [1, 2])
        self.assertEqual(to_swc(source), before)
        with self.assertRaises(ValueError):
            prune(source, (1,))
        with self.assertRaises(ValueError):
            prune(source, (999,))

    def test_terminal_trim_interpolates_position_and_radius(self) -> None:
        source = parse_swc(CHAIN)
        result = trim_terminal(source, 2, length=3.0)
        self.assertEqual(result.node(3).point, (7.0, 0.0, 0.0))
        self.assertEqual(result.node(3).radius, 1.5)
        self.assertEqual(result, trim_terminal(source, 2, fraction=0.3))

        at_node = trim_terminal(source, 2, length=6.0)
        self.assertEqual([node.id for node in at_node.nodes], [1, 2])
        self.assertEqual(at_node.node(2).point, (4.0, 0.0, 0.0))

    def test_terminal_trim_rejects_nonterminal_or_complete_removal(self) -> None:
        with self.assertRaises(ValueError):
            trim_terminal(parse_swc(Y_TREE), 2, length=0.1)
        with self.assertRaises(ValueError):
            trim_terminal(parse_swc(CHAIN), 2, length=10.0)

    def test_terminal_trim_rejects_arclength_beyond_one_ulp(self) -> None:
        source = parse_swc(
            "1 1 26.7322212663845 -85.8743173829511 -90.35765119452013 1 -1\n"
            "2 3 107.07007216122284 -5.2407416955284845 -46.3875620033612 1 1\n"
        )
        with self.assertRaisesRegex(ValueError, "arclength.*one ULP"):
            trim_terminal(source, 2, fraction=0.5244191777208187)

    def test_terminal_trim_preserves_small_residual_across_large_scales(self) -> None:
        source = Morphology(
            (
                Node(1, 1, (0.0, 0.0, 0.0), 1.0, -1),
                Node(2, 3, (1e16, 0.0, 0.0), 1.0, 1),
                Node(3, 3, (1e16, 1.0, 0.0), 1.0, 2),
            )
        )
        retained = trim_terminal(source, 2, length=1e16)
        self.assertEqual([node.id for node in retained.nodes], [1, 2])
        self.assertEqual(retained.node(2).point, (1.0, 0.0, 0.0))

        distal = trim_terminal(source, 2, length=1.0)
        self.assertEqual([node.id for node in distal.nodes], [1, 2])
        self.assertEqual(distal.node(2).point, (1e16, 0.0, 0.0))

    def test_edge_scaling_obeys_recursive_vector_equation(self) -> None:
        source = parse_swc(CHAIN)
        one = scale_edges(source, {2: 2.0})
        self.assertEqual(one.node(2).point, (8.0, 0.0, 0.0))
        self.assertEqual(one.node(3).point, (14.0, 0.0, 0.0))
        two = scale_edges(source, {2: 2.0, 3: 0.5})
        self.assertEqual(two.node(3).point, (11.0, 0.0, 0.0))
        self.assertEqual(source.node(3).point, (10.0, 0.0, 0.0))

    def test_radius_scaling_is_local(self) -> None:
        source = parse_swc(CHAIN)
        result = scale_radii(source, {3: 2.0})
        self.assertEqual(result.node(3).radius, 2.0)
        self.assertEqual(result.node(2), source.node(2))
        with self.assertRaises(ValueError):
            scale_radii(source, {3: 0.0})

    def test_graft_is_explicit_and_allocates_monotonic_ids(self) -> None:
        source = parse_swc(CHAIN)
        result = graft(
            source,
            3,
            ((3, (1.0, 2.0, 0.0), 0.5), (4, (-1.0, 0.0, 0.0), 0.4)),
        )
        self.assertEqual(result.node(4), Node(4, 3, (11.0, 2.0, 0.0), 0.5, 3))
        self.assertEqual(result.node(5), Node(5, 4, (9.0, 0.0, 0.0), 0.4, 3))
        with self.assertRaises(ValueError):
            graft(source, 3, ())

    def test_invalid_edge_targets_and_factors_are_rejected(self) -> None:
        source = parse_swc(CHAIN)
        for factors in ({1: 2.0}, {999: 2.0}, {2: 0.0}):
            with self.subTest(factors=factors), self.assertRaises(ValueError):
                scale_edges(source, factors)

    def test_unrepresentable_transform_vectors_are_rejected(self) -> None:
        chain = parse_swc(
            "1 1 0 0 0 1 -1\n2 3 1 0 0 1 1\n3 3 2 0 0 1 2\n"
        )
        with self.assertRaises(ValueError):
            scale_edges(chain, {2: 1e16})

        distant = parse_swc("1 1 10000000000000000 0 0 1 -1\n")
        with self.assertRaises(ValueError):
            graft(distant, 1, ((3, (1.0, 0.0, 0.0), 1.0),))
        ordinary = parse_swc("1 1 1 0 0 1 -1\n")
        with self.assertRaises(ValueError):
            graft(ordinary, 1, ((3, (5e-324, 0.0, 0.0), 1.0),))

    def test_material_transform_vector_distortion_is_rejected(self) -> None:
        distant = parse_swc("1 1 10000000000000000 0 0 1 -1\n")
        with self.assertRaisesRegex(ValueError, "one ULP"):
            graft(distant, 1, ((3, (3.0, 0.0, 0.0), 1.0),))

        translated_chain = parse_swc(
            "1 1 0 0 0 1 -1\n2 3 1 0 0 1 1\n3 3 4 0 0 1 2\n"
        )
        with self.assertRaisesRegex(ValueError, "one ULP"):
            scale_edges(translated_chain, {2: 1e16})

        coarse = parse_swc(
            "1 1 10000000000000000 0 0 1 -1\n"
            "2 3 10000000000000004 0 0 1 1\n"
        )
        with self.assertRaisesRegex(ValueError, "one ULP"):
            trim_terminal(coarse, 2, length=1.5)


class CliTests(unittest.TestCase):
    def test_analysis_stdout_and_transform_receipt(self) -> None:
        with TemporaryDirectory() as directory:
            source_path = Path(directory) / "input.swc"
            output_path = Path(directory) / "output.swc"
            source_path.write_text(Y_TREE, encoding="utf-8")

            analysis_stdout = StringIO()
            with redirect_stdout(analysis_stdout):
                self.assertEqual(main(["analyze", str(source_path)]), 0)
            self.assertEqual(
                json.loads(analysis_stdout.getvalue())["schema"], "remod.metrics.v1"
            )

            receipt_stdout = StringIO()
            with redirect_stdout(receipt_stdout):
                self.assertEqual(
                    main(
                        [
                            "prune",
                            str(source_path),
                            str(output_path),
                            "--roots",
                            "4",
                        ]
                    ),
                    0,
                )
            receipt = json.loads(receipt_stdout.getvalue())
            result = parse_swc(output_path.read_text(encoding="utf-8"))
            self.assertEqual(receipt["schema"], "remod.transform.v1")
            self.assertEqual(receipt["input_sha256"], parse_swc(Y_TREE).digest)
            self.assertEqual(receipt["output_sha256"], result.digest)
            self.assertNotIn(4, {node.id for node in result.nodes})

            errors = StringIO()
            with redirect_stderr(errors):
                self.assertEqual(
                    main(
                        [
                            "prune",
                            str(source_path),
                            str(output_path),
                            "--roots",
                            "5",
                        ]
                    ),
                    2,
                )
            self.assertIn("already exists", errors.getvalue())

    def test_each_transform_command_routes_exact_parameters(self) -> None:
        with TemporaryDirectory() as directory:
            source = Path(directory) / "input.swc"
            source.write_text(CHAIN, encoding="utf-8")
            commands = (
                ("trim", ["--branch", "2", "--length", "1"], "trim_terminal"),
                ("scale-edges", ["--factor", "2=0.5"], "scale_edges"),
                ("scale-radii", ["--factor", "3=2"], "scale_radii"),
                (
                    "graft",
                    ["--parent", "3", "--child", "3,1,0,0,0.5"],
                    "graft",
                ),
            )
            for index, (command, arguments, operation) in enumerate(commands):
                with self.subTest(command=command):
                    output = Path(directory) / f"output-{index}.swc"
                    stdout = StringIO()
                    with redirect_stdout(stdout):
                        code = main(
                            [command, str(source), str(output), *arguments]
                        )
                    self.assertEqual(code, 0)
                    self.assertEqual(
                        json.loads(stdout.getvalue())["operation"]["name"],
                        operation,
                    )
                    parse_swc(output.read_text(encoding="utf-8"))

    def test_public_api_is_deliberately_small(self) -> None:
        self.assertEqual(
            set(remod.__all__),
            {
                "Morphology",
                "Node",
                "analyze",
                "graft",
                "parse_swc",
                "prune",
                "scale_edges",
                "scale_radii",
                "to_swc",
                "trim_terminal",
            },
        )


if __name__ == "__main__":
    unittest.main()
