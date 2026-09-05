"""Restored Studio boundaries and compatibility with the scientific kernel."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stderr
from dataclasses import replace
import http.client
from io import StringIO
import json
import os
from pathlib import Path
import socket
from tempfile import TemporaryDirectory
from threading import Thread
import unittest
from unittest.mock import patch

from file_io import write_swc
from core_utils import parse_edit_args
from remod import parse_swc
from remod import cli, metrics
from remod_engine import AnalysisCache, RemodelRequest, analyze_text, remodel_text
import remod_ui as ui
from remodeling_actions import translate_descendants
from swc_parser import MAX_LINE_CHARS, parse_swc_text, segment_roots

CELL = "# public analytic fixture\n1 1 0 0 0 1 -1\n2 3 4 0 0 1 1\n3 3 5 1 0 1 2\n4 3 5 -1 0 1 2\n"


class StudioIntegrityTests(unittest.TestCase):
    def test_wide_tree_sibling_work_is_linear_and_edit_metadata_is_complete(self):
        class CountedChildren(list):
            visits = 0

            def __iter__(self):
                for child in super().__iter__():
                    type(self).visits += 1
                    yield child

        samples = {1: [1, 1, 0, 0, 0, 1, -1]}
        samples.update({i: [i, 3, i, 0, 0, 1, 1] for i in range(2, 1102)})
        children = {i: CountedChildren() for i in samples}
        children[1] = CountedChildren(range(2, 1102))
        self.assertEqual(len(segment_roots(samples, children)), 1100)
        self.assertEqual(CountedChildren.visits, 1100)
        source = "\n".join(" ".join(map(str, row)) for row in samples.values()) + "\n"
        result = remodel_text(source, RemodelRequest("cell.swc", "all_terminal", "none", radius_change=10))
        self.assertEqual(len(result.parsed.samples), 1101)
        metadata = [line for line in result.content.splitlines() if line.startswith("# segment_ids:")]
        self.assertGreater(len(metadata), 1)
        self.assertTrue(all(len(line) <= MAX_LINE_CHARS for line in metadata))
        ids = [int(token) for line in metadata for token in line.partition(": ")[2].split(",")]
        self.assertEqual(ids, list(range(2, 1102)))

    def test_edit_work_limit_and_positive_geometry_underflow_are_explicit(self):
        with patch("remodeling_actions.MAX_EDIT_WORK", 1):
            with self.assertRaisesRegex(ValueError, "sample visits"):
                remodel_text(CELL, RemodelRequest("cell.swc", "all_terminal", "scale", amount=90))
        source = "1 1 0 0 0 1 -1\n2 3 1 0 0 1 1\n3 3 2 0 0 1e-200 2\n"
        with self.assertRaisesRegex(ValueError, "underflows"):
            parse_swc_text(source)

    def test_generated_names_are_bounded_without_altering_source_metadata(self):
        for name in ("a" * 236 + ".swc", "é" * 118 + ".swc"):
            output = ui._remodeled_name(name)
            self.assertLessEqual(len(output.encode("utf-8")), 240)
            self.assertTrue(output.endswith("_remodeled.swc"))
            result = remodel_text(CELL, RemodelRequest(name, "all_terminal", "none", radius_change=10))
            self.assertIn("# source_file: " + name + "\n", result.content)

    def test_numeric_options_validate_original_decimal_seed(self):
        for value in ("1.0000000000000001", ui._decimal_token("1.0000000000000001"), "9007199254740992"):
            with self.assertRaisesRegex(ValueError, "whole number"):
                ui._optional_number(value, integer=True)
        self.assertEqual(ui._optional_number("12.0", integer=True), 12)
        with self.assertRaisesRegex(ValueError, "underflows"):
            ui._optional_number("1e-999")
        with redirect_stderr(StringIO()), self.assertRaises(SystemExit):
            parse_edit_args(["--directory", str(Path(__file__).resolve().parents[1] / "swc_files"), "--file-name", "0-2.CNG.swc", "--who", "all_terminal", "--action", "none", "--radius-change", "1e-999"])

    def test_source_tokens_and_comment_separators_share_kernel_rejection(self):
        for source in (CELL.replace("4 0 0", "1e-999 0 0"),
                       CELL.replace("1 1 0", "١ 1 0"),
                       "# label\u2028999 3 6 0 0 1 1\n" + CELL):
            for parser in (parse_swc_text, parse_swc):
                with self.subTest(parser=parser.__module__), self.assertRaises(ValueError):
                    parser(source)

    def test_filename_cannot_inject_a_sample_into_preview(self):
        request = RemodelRequest("cell.swc", "all_terminal", "shrink", amount=10)
        for name in ("cell\n999 3 6 0 0 1 1\n# x.swc", "../cell.swc", "C:\\cell.swc", "x\u2028y.swc"):
            with self.subTest(name=repr(name)), self.assertRaises(ValueError):
                remodel_text(CELL, replace(request, file_name=name))
        result = remodel_text(CELL, request)
        self.assertEqual(len(parse_swc(result.content).nodes), 4)
        self.assertEqual(result.parsed.samples, parse_swc_text(result.content).samples)

    def test_preview_is_seeded_exact_and_does_not_mutate_cached_input(self):
        cache = AnalysisCache()
        before, _ = cache.get_or_analyze(CELL, 1)
        original = json.dumps(before.morphology, sort_keys=True)
        request = RemodelRequest("cell.swc", "random_all", "extend", random_ratio=50, amount=10, seed=17)
        first = remodel_text(CELL, request, parsed=before.parsed)
        second = remodel_text(CELL, request, parsed=before.parsed)
        self.assertEqual(first.content, second.content)
        self.assertEqual(json.dumps(before.morphology, sort_keys=True), original)
        self.assertEqual(before.parsed.samples, parse_swc_text(CELL).samples)

    def test_javascript_unsafe_ids_fail_without_restricting_kernel(self):
        source = CELL.replace("1 1 0 0 0 1 -1", "9007199254740993 1 0 0 0 1 -1").replace("4 0 0 1 1", "4 0 0 1 9007199254740993")
        self.assertEqual(parse_swc(source).root.id, 9007199254740993)
        with self.assertRaisesRegex(ValueError, "JavaScript"):
            analyze_text(source)

    def test_topology_growth_and_exact_radial_work_fail_before_expensive_work(self):
        with patch("swc_parser.MAX_TOPOLOGY_LINKS", 2):
            with self.assertRaisesRegex(ValueError, "ancestor links"):
                parse_swc_text(CELL)
        with patch("remodeling_actions.MAX_NODES", 5), patch("remodeling_actions.create_points", side_effect=AssertionError("generated")):
            with self.assertRaisesRegex(ValueError, "generation budget"):
                remodel_text(CELL, RemodelRequest("cell.swc", "all_terminal", "extend", amount=100))
        with patch.object(metrics, "_MAX_RADIAL_WORK", 1), patch.object(metrics, "_sphere_parameters", side_effect=AssertionError("solved")):
            with self.assertRaisesRegex(ValueError, "work units"):
                analyze_text(CELL, 1)

    def test_collapsed_radial_contacts_rejected_by_both_interfaces(self):
        y, z = 1 - 2**-53, 2**-26 - 2**-79
        source = f"1 1 0 0 0 1 -1\n2 3 -4096 {y:.17g} {z:.17g} 1 1\n3 3 4096 {y:.17g} {z:.17g} 1 2\n"
        with self.assertRaisesRegex(ValueError, "contacts"):
            analyze_text(source, 1)

    def test_descendant_translation_cannot_silently_collapse(self):
        segments = {2: [[2, 3, 1e16, 0., 0., 1., 1]]}
        with self.assertRaisesRegex(ValueError, "collapses"):
            translate_descendants((1., 0., 0.), 1, {1: [2]}, segments)

    def test_cache_is_byte_bounded_and_separated_by_source_and_step(self):
        cache = AnalysisCache(max_entries=1, max_bytes=30_000)
        a, _ = cache.get_or_analyze(CELL, 1)
        b, _ = cache.get_or_analyze(CELL, 2)
        c, _ = cache.get_or_analyze(CELL.replace("5 1", "6 1"), 1)
        self.assertEqual(len({a.analysis_id, b.analysis_id, c.analysis_id}), 3)
        self.assertLessEqual(cache.info()["bytes"], cache.max_bytes)
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: cache.get_or_analyze(CELL, 1)[0].statistics, range(4)))
        self.assertTrue(all(result == results[0] for result in results))

    def test_export_reuses_atomic_writer_and_safe_force(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "result.swc"
            write_swc(path, CELL.splitlines())
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            with self.assertRaises(ValueError):
                write_swc(path, CELL.splitlines())
            with patch.object(cli.os, "replace", side_effect=OSError("interrupted")):
                with self.assertRaises(ValueError):
                    write_swc(path, CELL.replace("5 1", "6 1").splitlines(), overwrite=True)
            self.assertEqual(path.read_text(), CELL)
            self.assertEqual(list(Path(directory).iterdir()), [path])
            link = Path(directory) / "link.swc"
            link.symlink_to(path)
            with self.assertRaises(ValueError):
                write_swc(link, CELL.splitlines(), overwrite=True)
            link.unlink()
            os.link(path, link)
            with self.assertRaises(ValueError):
                write_swc(link, CELL.splitlines(), overwrite=True)


class LocalHTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ui.RemodServer(0)
        cls.thread = Thread(target=cls.server.serve_forever, kwargs={"poll_interval": .01}, daemon=True)
        cls.thread.start()
        cls.host = f"127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(2)

    def request(self, method="GET", path="/api/health", body=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=2)
        request_headers = {"Host": self.host}
        if body is not None:
            body = json.dumps(body)
            request_headers.update({"Content-Type": "application/json", "X-Remod-Request": "1"})
        request_headers.update(headers or {})
        try:
            connection.request(method, path, body, request_headers)
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            connection.close()

    def raw(self, headers, body=b"", method="POST"):
        data = f"{method} /api/workspace HTTP/1.1\r\nHost: {self.host}\r\n{headers}\r\n\r\n".encode() + body
        with socket.create_connection(("127.0.0.1", self.server.server_port), timeout=2) as peer:
            peer.sendall(data)
            peer.shutdown(socket.SHUT_WR)
            return peer.recv(4096)

    def test_loopback_only_and_security_headers_with_real_assets(self):
        self.assertEqual(self.server.server_address[0], "127.0.0.1")
        with redirect_stderr(StringIO()), self.assertRaises(SystemExit):
            ui._parser().parse_args(["--host", "0.0.0.0"])
        for path in ("/", "/app.js", "/styles.css"):
            status, headers, body = self.request(path=path)
            self.assertEqual(status, 200)
            self.assertTrue(body)
            self.assertEqual(headers["Content-Security-Policy"], ui.CSP)
            self.assertEqual(headers["X-Frame-Options"], "DENY")
            self.assertNotIn("Server", headers)

    def test_host_origin_metadata_and_method_boundary(self):
        for headers in ({"Host": "evil.invalid"}, {"Origin": "https://evil.invalid"}, {"Origin": "null"}, {"Sec-Fetch-Site": "cross-site"}):
            self.assertEqual(self.request(headers=headers)[0], 403)
        self.assertEqual(self.request(headers={"Origin": "http://" + self.host, "Sec-Fetch-Site": "same-origin"})[0], 200)
        for method in ("OPTIONS", "PUT", "DELETE", "HEAD", "TRACE"):
            self.assertEqual(self.request(method=method)[0], 405)
        self.assertEqual(self.request(path="/api/examples/../README.md")[0], 404)
        self.assertEqual(self.request(path="/api/examples/%2e%2e%2fREADME.md")[0], 404)

    def test_framing_encoding_and_property_rejections(self):
        common = "Content-Type: application/json\r\nX-Remod-Request: 1\r\n"
        for header, body in (("Content-Length: -1", b""), ("Content-Length: 999999999", b""), ("Content-Length: 20", b"{}"), ("Transfer-Encoding: chunked", b""), ("Content-Length: 2\r\nContent-Length: 2", b"{}"), ("", b"")):
            with self.subTest(header=header):
                self.assertIn(b" 400 ", self.raw(common + header, body).split(b"\r\n")[0])
        for body in (b'{"a":1,"a":2}', b'{"__proto__":{}}', b'{"a":NaN}', b'{"a":1e-999}', b'{"a":"\xff"}', b'[' * 100 + b']' * 100):
            self.assertIn(b" 400 ", self.raw(common + f"Content-Length: {len(body)}", body).split(b"\r\n")[0])
        for headers in ({"Content-Type": "text/plain"}, {"Content-Type": "application/json;charset=latin1"}, {"X-Remod-Request": ""}):
            self.assertEqual(self.request("POST", "/api/workspace", {"files": []}, headers)[0], 400)

    def test_request_timeout_and_concurrency_bound(self):
        with patch.object(ui, "REQUEST_TIMEOUT", .1):
            with socket.create_connection(("127.0.0.1", self.server.server_port), timeout=2) as peer:
                peer.sendall(f"POST /api/workspace HTTP/1.1\r\nHost: {self.host}\r\nContent-Type: application/json\r\nX-Remod-Request: 1\r\nContent-Length: 99\r\n\r\n{{".encode())
                self.assertIn(b" 408 ", peer.recv(4096).split(b"\r\n")[0])
        self.server.computations.acquire()
        self.server.computations.acquire()
        try:
            self.assertEqual(self.request("POST", "/api/workspace", {"files": [{"name": "cell.swc", "content": CELL}]})[0], 503)
        finally:
            self.server.computations.release()
            self.server.computations.release()

    def test_workspace_preview_cohorts_and_safe_failure(self):
        status, _, body = self.request("POST", "/api/workspace", {"files": [{"name": "cell.swc", "content": CELL}], "sholl_step": 1})
        self.assertEqual(status, 200)
        analysis = json.loads(body)["files"][0]
        groups = {"files": [{"name": "cell.swc", "analysis_id": analysis["analysis_id"], "group": "A"}]}
        self.assertEqual(self.request("POST", "/api/groups", groups)[0], 200)
        preview = {"name": "cell.swc", "content": CELL, "sholl_step": 1, "options": {"action": "shrink", "amount": 10, "seed": 17}}
        status, _, body = self.request("POST", "/api/remodel", preview)
        self.assertEqual(status, 200)
        result = json.loads(body)
        self.assertEqual(len(parse_swc(result["content"]).nodes), 4)
        with patch.object(ui.ANALYSIS_CACHE, "get_or_analyze", side_effect=OSError("/private/research/secret.swc")):
            status, _, body = self.request("POST", "/api/workspace", {"files": [{"name": "cell.swc", "content": CELL}]})
        self.assertEqual(status, 500)
        self.assertNotIn(b"secret", body)
        self.assertNotIn(b"/private", body)

    def test_exact_json_fractional_seed_is_not_rounded_into_an_integer(self):
        body = json.dumps({"name": "cell.swc", "content": CELL, "options": {"action": "none", "radius_change": 10, "seed": "EXACT_SEED"}}).replace('"EXACT_SEED"', "1.0000000000000001").encode()
        with socket.create_connection(("127.0.0.1", self.server.server_port), timeout=2) as peer:
            peer.sendall(f"POST /api/remodel HTTP/1.1\r\nHost: {self.host}\r\nContent-Type: application/json\r\nX-Remod-Request: 1\r\nContent-Length: {len(body)}\r\n\r\n".encode() + body)
            self.assertIn(b" 400 ", peer.recv(4096).split(b"\r\n")[0])


if __name__ == "__main__":
    unittest.main()
