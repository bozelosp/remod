"""Regressions for reachable local-input, file, and scientific-integrity risks."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stderr
from decimal import localcontext
from fractions import Fraction
from io import StringIO
from itertools import repeat
import json
import os
from pathlib import Path
import stat
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from remod import Morphology, Node, analyze, graft, parse_swc, scale_radii, to_swc
from remod import cli, metrics, model

CHAIN = "1 1 0 0 0 1 -1\n2 3 4 0 0 1 1\n"


class InputIntegrityTests(unittest.TestCase):
    def test_numeric_tokens_reject_underflow_and_nondecimal_grammar(self):
        for token in ("1e-999", "-1e-999", "nan", "inf", "1_000", "١", "1" * 129):
            with self.subTest(token=token), self.assertRaises(ValueError):
                parse_swc(f"1 1 {token} 0 0 1 -1\n")
        for token, expected in (("0e-999", 0.0), ("5e-324", 5e-324), ("+.25", .25)):
            self.assertEqual(parse_swc(f"1 1 {token} 0 0 1 -1\n").root.point[0], expected)

    def test_cli_numeric_sinks_share_strict_parser(self):
        morphology = parse_swc(CHAIN)
        for operation in (
            lambda: cli._origin("1e-999,0,0", morphology),
            lambda: cli._children(["3,1e-999,0,0,1"]),
            lambda: cli._factors(["2=1e-999"]),
        ):
            with self.assertRaises(ValueError):
                operation()
        with redirect_stderr(StringIO()), self.assertRaises(SystemExit) as caught:
            cli.main(["analyze", "unused.swc", "--radial-step", "1e-999"])
        self.assertEqual(caught.exception.code, 2)

    def test_comment_marker_is_removed_once_and_identity_is_stable(self):
        source = parse_swc("### metadata\n" + CHAIN)
        self.assertEqual(source.comments, ("## metadata",))
        result = scale_radii(source, {2: 2})
        self.assertEqual(result.comments, source.comments)
        for _ in range(3):
            reparsed = parse_swc(to_swc(result))
            self.assertEqual(reparsed, result)
            self.assertEqual(reparsed.digest, result.digest)
            result = reparsed

    def test_comment_and_source_control_characters_cannot_inject_rows(self):
        for separator in ("\n", "\r", "\v", "\f", "\x85", "\u2028", "\u2029", "\x1b", "\u202e", "\ud800"):
            with self.subTest(separator=repr(separator)), self.assertRaises(ValueError):
                Morphology(parse_swc(CHAIN).nodes, ("label" + separator + "3 3 5 0 0 1 2",))
            if separator not in ("\n", "\r"):
                with self.assertRaises(ValueError):
                    parse_swc("# label" + separator + CHAIN)
        self.assertEqual(parse_swc(CHAIN.replace("\n", "\r\n")), parse_swc(CHAIN))

    def test_byte_line_comment_and_sample_limits_reject_not_truncate(self):
        with patch.object(model, "MAX_SWC_BYTES", len(CHAIN.encode()) - 1):
            with self.assertRaisesRegex(ValueError, "bytes"):
                parse_swc(CHAIN)
        with self.assertRaisesRegex(ValueError, "line"):
            parse_swc(" " * (model.MAX_LINE_CHARS + 1) + "\n" + CHAIN)
        with patch.object(model, "MAX_COMMENT_BYTES", 8):
            with self.assertRaisesRegex(ValueError, "comments"):
                parse_swc("# abc\n# def\n" + CHAIN)
            with self.assertRaisesRegex(ValueError, "comments"):
                Morphology(parse_swc(CHAIN).nodes, repeat(""))
        with patch.object(model, "MAX_NODES", 1):
            with self.assertRaisesRegex(ValueError, "sample count"):
                parse_swc(CHAIN)
            with self.assertRaisesRegex(ValueError, "sample count"):
                Morphology(repeat(Node(1, 1, (0., 0., 0.), 1., -1)))

    def test_generation_and_parameter_iterables_are_bounded(self):
        source = parse_swc(CHAIN)
        with patch("remod.transforms.MAX_NODES", 2), self.assertRaisesRegex(ValueError, "samples"):
            graft(source, 1, ((3, (1., 0., 0.), 1.),))
        with patch.object(metrics, "MAX_NODES", 4), self.assertRaisesRegex(ValueError, "selected kinds"):
            analyze(source, kinds=repeat(3))
        with self.assertRaisesRegex(ValueError, "origin"):
            analyze(source, origin=repeat(0.), radial_step=1.)
        with self.assertRaisesRegex(ValueError, "unit"):
            analyze(source, unit="x" * 129)


class NumericSecurityTests(unittest.TestCase):
    def test_unselected_ancestor_overflow_is_rejected(self):
        source = parse_swc("1 1 0 0 0 1 -1\n2 2 1e308 0 0 1 1\n3 2 0 0 0 1 2\n4 3 1 0 0 1 3\n")
        with self.assertRaisesRegex(ValueError, "root path"):
            analyze(source)

    def test_collapsed_secant_contacts_fail_before_silent_shell_loss(self):
        y, z = 1 - 2**-53, 2**-26 - 2**-79
        source = Morphology((Node(1, 1, (-4096., y, z), 1., -1), Node(2, 3, (4096., y, z), 1., 1)))
        with self.assertRaisesRegex(ValueError, "contacts"):
            analyze(source, origin=(0., 0., 0.), radial_step=1.)

    def test_contact_endpoint_rounding_and_positive_length_underflow_fail(self):
        source = parse_swc("1 1 -5e-324 0 0 1 -1\n2 3 2 0 0 1 1\n")
        with self.assertRaisesRegex(ValueError, "contacts"):
            analyze(source, origin=(-1., 0., 0.), radial_step=1.)
        source = parse_swc("1 1 0 0 0 1 -1\n2 3 5e-324 0 0 1 1\n")
        with patch.object(metrics, "_sphere_parameters", return_value=(.5,)), self.assertRaises(ValueError):
            metrics._radial_profile(source, [{"parent_id": 1, "child_id": 2, "length": 5e-324}], (0., 0., 0.), 5e-324)

    def test_decimal_context_and_parallel_callers_do_not_change_results(self):
        source = parse_swc("1 1 -2 .5 0 1 -1\n2 3 2 .5 0 1 1\n")
        expected = analyze(source, origin=(0., 0., 0.), radial_step=1.)
        def restricted(_):
            with localcontext() as context:
                context.Emax = context.Emin = 0
                for signal in context.traps:
                    context.traps[signal] = False
                return analyze(source, origin=(0., 0., 0.), radial_step=1.)
        with ThreadPoolExecutor(max_workers=2) as executor:
            for result in executor.map(restricted, range(4)):
                self.assertEqual(result, expected)
                json.dumps(result, allow_nan=False)

    def test_combined_radial_work_is_rejected_before_contact_solving(self):
        nodes = [Node(1, 1, (0., 0., 0.), 1., -1)]
        nodes.extend(Node(i, 3, (10000., 0., 0.), 1., 1) for i in range(2, 23))
        with patch.object(metrics, "_sphere_parameters", side_effect=AssertionError("contact evaluated")):
            with self.assertRaisesRegex(ValueError, "work units"):
                analyze(Morphology(tuple(nodes)), origin=(0., 0., 0.), radial_step=1.)

    def test_underflowed_library_origin_and_offset_are_rejected(self):
        source = parse_swc(CHAIN)
        tiny = Fraction(1, 10**400)
        with self.assertRaisesRegex(ValueError, "underflow"):
            analyze(source, origin=(tiny, 0., 0.), radial_step=1.)
        with self.assertRaisesRegex(ValueError, "underflow"):
            graft(source, 1, ((3, (tiny, 0., 0.), 1.),))


class FileSecurityTests(unittest.TestCase):
    def test_unprotected_shared_output_directory_is_rejected(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            root.chmod(0o777)
            with self.assertRaisesRegex(ValueError, "directory"):
                cli._write_new(root / "new.swc", CHAIN)
            self.assertEqual(list(root.iterdir()), [])
            root.chmod(0o1777)
            cli._write_new(root / "new.swc", CHAIN)
            self.assertEqual((root / "new.swc").read_text(), CHAIN)

    def test_regular_bounded_utf8_input_and_safe_errors(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.swc"
            source.write_text(CHAIN)
            self.assertEqual(cli._read(source), parse_swc(CHAIN))
            link = root / "link.swc"
            link.symlink_to(source)
            fifo = root / "pipe.swc"
            os.mkfifo(fifo)
            for path in (link, fifo, root):
                with self.subTest(path=path.name), self.assertRaises(ValueError):
                    cli._read(path)
            with patch.object(cli, "MAX_SWC_BYTES", 2), self.assertRaisesRegex(ValueError, "bytes"):
                cli._read(source)
            source.write_bytes(b"\xff")
            with self.assertRaisesRegex(ValueError, "UTF-8"):
                cli._read(source)
            errors = StringIO()
            with redirect_stderr(errors):
                self.assertEqual(cli.main(["analyze", str(root / "\x1b[2J.swc")]), 2)
            self.assertNotIn("\x1b", errors.getvalue())
            self.assertNotIn(directory, errors.getvalue())

    def test_existing_file_input_alias_and_leaf_links_are_never_overwritten(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.swc"
            source.write_text(CHAIN)
            for name, operation in (("hard", os.link), ("soft", os.symlink)):
                operation(source, root / name)
            os.symlink(root / "missing", root / "dangling")
            for path in (source, root / "hard", root / "soft", root / "dangling"):
                with self.assertRaisesRegex(ValueError, "already exists"):
                    cli._write_new(path, "replacement")
            self.assertEqual(source.read_text(), CHAIN)
            self.assertEqual(list(root.glob(".remod-*")), [])

    def test_output_is_private_reparsed_and_readback_verified(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "new.swc"
            source = parse_swc("### label\n" + CHAIN)
            with self.assertRaisesRegex(ValueError, "morphology"):
                cli._write_new(path, to_swc(source), swc_digest="incorrect")
            self.assertFalse(path.exists())
            cli._write_new(path, to_swc(source), swc_digest=source.digest)
            self.assertEqual(parse_swc(path.read_text()).digest, source.digest)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            self.assertEqual(list(path.parent.glob(".remod-*")), [])

    def test_failed_write_and_interruption_leave_no_final_or_temporary_file(self):
        for error in (OSError(28, "No space left on device"), KeyboardInterrupt()):
            with self.subTest(error=type(error).__name__), TemporaryDirectory() as directory:
                path = Path(directory) / "new.swc"
                with patch.object(cli.os, "fsync", side_effect=error):
                    with self.assertRaises((ValueError, KeyboardInterrupt)):
                        cli._write_new(path, CHAIN)
                self.assertEqual(list(path.parent.iterdir()), [])

    def test_partial_write_and_corrupt_readback_are_never_published(self):
        real_fdopen = os.fdopen
        for fault in ("partial", "readback"):
            with self.subTest(fault=fault), TemporaryDirectory() as directory:
                path = Path(directory) / "new.swc"
                class FaultyFile:
                    def __init__(self, descriptor, mode):
                        self.handle = real_fdopen(descriptor, mode)
                    def __enter__(self):
                        return self
                    def __exit__(self, *args):
                        self.handle.close()
                    def __getattr__(self, name):
                        return getattr(self.handle, name)
                    def write(self, data):
                        if fault == "partial":
                            self.handle.write(data[:5])
                            raise OSError(28, "No space left on device")
                        return self.handle.write(data)
                    def read(self, size):
                        return b"corrupt"
                with patch.object(cli.os, "fdopen", side_effect=FaultyFile):
                    with self.assertRaises(ValueError):
                        cli._write_new(path, CHAIN)
                self.assertEqual(list(path.parent.iterdir()), [])

    def test_input_mutation_during_read_is_rejected(self):
        with TemporaryDirectory() as directory:
            source = Path(directory) / "source.swc"
            source.write_text(CHAIN)
            real_fstat = os.fstat
            calls = 0
            def mutate(descriptor):
                nonlocal calls
                calls += 1
                if calls == 2:
                    source.write_text(CHAIN + "# changed\n")
                return real_fstat(descriptor)
            with patch.object(cli.os, "fstat", side_effect=mutate):
                with self.assertRaisesRegex(ValueError, "changed"):
                    cli._read(source)

    def test_temporary_name_collision_preserves_unowned_file(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            existing = root / ".remod-fixed.tmp"
            existing.write_text("keep")
            with patch.object(cli.secrets, "token_hex", return_value="fixed"):
                with self.assertRaises(ValueError):
                    cli._write_new(root / "new.swc", CHAIN)
            self.assertEqual(existing.read_text(), "keep")

    def test_concurrent_publish_has_exactly_one_winner(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "new.swc"
            def publish(text):
                try:
                    cli._write_new(path, text)
                    return True
                except ValueError:
                    return False
            with ThreadPoolExecutor(max_workers=2) as executor:
                self.assertEqual(sum(executor.map(publish, ("first", "second"))), 1)
            self.assertIn(path.read_text(), ("first", "second"))
            self.assertEqual(list(path.parent.glob(".remod-*")), [])

    def test_output_parent_is_pinned_against_path_replacement(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            parent = root / "parent"
            parent.mkdir()
            moved = root / "moved"
            real_link = os.link
            def swap_then_link(*args, **kwargs):
                parent.rename(moved)
                parent.mkdir()
                return real_link(*args, **kwargs)
            with patch.object(cli.os, "link", side_effect=swap_then_link):
                cli._write_new(parent / "new.swc", CHAIN)
            self.assertFalse((parent / "new.swc").exists())
            self.assertEqual((moved / "new.swc").read_text(), CHAIN)


if __name__ == "__main__":
    unittest.main()
